#!/usr/bin/env python3
"""Minimal FreshRSS Google Reader API client for rss-curate-ai-news."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlencode, urlsplit
from urllib.request import ProxyHandler, Request, build_opener


TARGET_FEEDS = ("机器之心", "新智元", "量子位")
SELECTED_LABEL = "AI例会/已选"
CONCEPT_PREFIX = "AI概念/"
SHANGHAI = timezone(timedelta(hours=8), name="Asia/Shanghai")
EARLIEST_VALID_PUBLICATION = datetime(2000, 1, 1, tzinfo=timezone.utc)


class FreshRSSError(RuntimeError):
    """Expected configuration, transport, or API failure."""


class _ArticleHTMLParser(HTMLParser):
    BLOCK_TAGS = {
        "address", "article", "aside", "blockquote", "br", "div", "figcaption",
        "figure", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header",
        "hr", "li", "main", "nav", "ol", "p", "pre", "section", "table",
        "td", "th", "tr", "ul",
    }
    SKIP_TAGS = {"script", "style", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "a":
            href = dict(attrs).get("href")
            if href and urlsplit(href).scheme in {"http", "https"}:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if not self._skip_depth and tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)


def html_to_text_and_links(value: str) -> tuple[str, list[str]]:
    parser = _ArticleHTMLParser()
    parser.feed(value or "")
    lines = [" ".join(line.split()) for line in "".join(parser.parts).splitlines()]
    text = "\n".join(line for line in lines if line)
    links = list(dict.fromkeys(parser.links))
    return text, links


def _parse_epoch(value: Any, *, milliseconds: bool = False) -> datetime | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if milliseconds:
        number /= 1000
    try:
        return datetime.fromtimestamp(number, tz=timezone.utc)
    except (OSError, OverflowError, ValueError):
        return None


def choose_article_time(item: dict[str, Any], now_utc: datetime) -> tuple[datetime | None, str]:
    published = _parse_epoch(item.get("published"))
    latest_valid = now_utc + timedelta(minutes=5)
    if published and EARLIEST_VALID_PUBLICATION <= published <= latest_valid:
        return published, "published"
    crawled = _parse_epoch(item.get("crawlTimeMsec"), milliseconds=True)
    if crawled:
        return crawled, "crawl_fallback"
    return None, "unavailable"


def _first_href(item: dict[str, Any], key: str) -> str | None:
    values = item.get(key) or []
    if isinstance(values, list):
        for value in values:
            if isinstance(value, dict) and value.get("href"):
                href = str(value["href"]).strip()
                if urlsplit(href).scheme in {"http", "https"}:
                    return href
    return None


def _extract_labels(categories: Iterable[Any]) -> list[str]:
    labels: list[str] = []
    marker = "/label/"
    for category in categories:
        category = str(category)
        if marker in category:
            labels.append(unquote(category.split(marker, 1)[1]))
    return list(dict.fromkeys(labels))


def article_from_item(
    item: dict[str, Any],
    feed_title: str,
    now_utc: datetime,
    primary_start: datetime,
    fallback_start: datetime,
) -> dict[str, Any]:
    chosen_time, basis = choose_article_time(item, now_utc)
    summary = item.get("summary") or item.get("content") or {}
    raw_content = summary.get("content", "") if isinstance(summary, dict) else str(summary)
    content, embedded_links = html_to_text_and_links(raw_content)
    labels = _extract_labels(item.get("categories") or [])
    crawl_time = _parse_epoch(item.get("crawlTimeMsec"), milliseconds=True)
    article_url = _first_href(item, "canonical") or _first_href(item, "alternate")
    in_primary = bool(chosen_time and primary_start <= chosen_time <= now_utc)
    in_fallback = bool(chosen_time and fallback_start <= chosen_time <= now_utc)
    return {
        "item_id": str(item.get("id", "")),
        "title": html.unescape(str(item.get("title", "")).strip()),
        "feed": feed_title,
        "article_url": article_url,
        "published_at": chosen_time.astimezone(SHANGHAI).isoformat() if chosen_time else None,
        "crawl_at": crawl_time.astimezone(SHANGHAI).isoformat() if crawl_time else None,
        "timestamp_basis": basis,
        "in_primary_window": in_primary,
        "in_fallback_pool": in_fallback,
        "labels": labels,
        "already_selected": SELECTED_LABEL in labels,
        "concept_labels": [label for label in labels if label.startswith(CONCEPT_PREFIX)],
        "embedded_links": embedded_links,
        "content": content,
    }


@dataclass
class FreshRSSClient:
    base_url: str
    username: str
    password: str
    timeout: int = 30
    auth_token: str | None = None

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        if urlsplit(self.base_url).scheme not in {"http", "https"}:
            raise FreshRSSError("FRESHRSS_URL must begin with http:// or https://")
        self.api_base = f"{self.base_url}/api/greader.php"

    @classmethod
    def from_env(cls) -> "FreshRSSClient":
        names = ("FRESHRSS_URL", "FRESHRSS_USERNAME", "FRESHRSS_API_PASSWORD")
        missing = [name for name in names if not os.environ.get(name)]
        if missing:
            raise FreshRSSError("Missing environment variables: " + ", ".join(missing))
        return cls(
            os.environ["FRESHRSS_URL"],
            os.environ["FRESHRSS_USERNAME"],
            os.environ["FRESHRSS_API_PASSWORD"],
        )

    def _request(
        self,
        path: str,
        *,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        method: str = "GET",
        authenticated: bool = True,
    ) -> str:
        url = f"{self.api_base}{path}"
        data = None
        if params:
            encoded = urlencode(params, doseq=True)
            if method == "GET":
                url = f"{url}?{encoded}"
            else:
                data = encoded.encode("utf-8")
        headers = {"User-Agent": "rss-curate-ai-news/1"}
        if authenticated:
            if not self.auth_token:
                self.login()
            headers["Authorization"] = f"GoogleLogin auth={self.auth_token}"
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with build_opener(ProxyHandler({})).open(request, timeout=self.timeout) as response:
                return response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:300]
            raise FreshRSSError(f"FreshRSS HTTP {exc.code} for {path}: {body}") from exc
        except URLError as exc:
            raise FreshRSSError(f"FreshRSS connection failed for {path}: {exc.reason}") from exc

    def login(self) -> None:
        body = self._request(
            "/accounts/ClientLogin",
            params={"Email": self.username, "Passwd": self.password},
            method="POST",
            authenticated=False,
        )
        match = re.search(r"(?m)^Auth=(.+)$", body)
        if not match:
            raise FreshRSSError("FreshRSS API authentication failed")
        self.auth_token = match.group(1).strip()

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        body = self._request(path, params=params)
        try:
            value = json.loads(body)
        except json.JSONDecodeError as exc:
            raise FreshRSSError(f"FreshRSS returned invalid JSON for {path}") from exc
        if not isinstance(value, dict):
            raise FreshRSSError(f"FreshRSS returned unexpected JSON for {path}")
        return value

    def get_text(self, path: str, params: dict[str, Any] | None = None) -> str:
        return self._request(path, params=params)

    def post_text(self, path: str, params: dict[str, Any]) -> str:
        return self._request(path, params=params, method="POST")


def _subscription_map(client: FreshRSSClient) -> dict[str, str]:
    data = client.get_json("/reader/api/0/subscription/list", {"output": "json"})
    matches: dict[str, list[str]] = {title: [] for title in TARGET_FEEDS}
    for subscription in data.get("subscriptions") or []:
        title = str(subscription.get("title", ""))
        if title in matches:
            matches[title].append(str(subscription.get("id", "")))
    missing = [title for title, ids in matches.items() if not ids]
    duplicates = [title for title, ids in matches.items() if len(ids) > 1]
    if missing:
        raise FreshRSSError("Missing target subscriptions: " + ", ".join(missing))
    if duplicates:
        raise FreshRSSError("Duplicate target subscription titles: " + ", ".join(duplicates))
    return {title: ids[0] for title, ids in matches.items()}


def _user_labels(client: FreshRSSClient) -> list[str]:
    data = client.get_json("/reader/api/0/tag/list", {"output": "json"})
    return _extract_labels(tag.get("id", "") for tag in data.get("tags") or [])


def fetch_articles(
    client: FreshRSSClient,
    *,
    now_utc: datetime | None = None,
    primary_hours: int = 24,
    fallback_days: int = 7,
) -> dict[str, Any]:
    now_utc = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    primary_start = now_utc - timedelta(hours=primary_hours)
    fallback_start = now_utc - timedelta(days=fallback_days)
    api_fetch_start = now_utc - timedelta(days=fallback_days + 1)
    subscriptions = _subscription_map(client)
    user_labels = _user_labels(client)
    articles: list[dict[str, Any]] = []
    seen: set[str] = set()
    counts: dict[str, dict[str, int]] = {}

    for title in TARGET_FEEDS:
        feed_id = subscriptions[title]
        path = "/reader/api/0/stream/contents/" + quote(feed_id, safe="/")
        data = client.get_json(
            path,
            {
                "output": "json",
                "n": 1000,
                "ot": int(api_fetch_start.timestamp()),
            },
        )
        feed_articles = []
        for item in data.get("items") or []:
            article = article_from_item(item, title, now_utc, primary_start, fallback_start)
            if not article["item_id"] or article["item_id"] in seen:
                continue
            seen.add(article["item_id"])
            if article["in_fallback_pool"]:
                feed_articles.append(article)
                articles.append(article)
        counts[title] = {
            "primary": sum(1 for article in feed_articles if article["in_primary_window"]),
            "fallback_pool": len(feed_articles),
        }

    articles.sort(key=lambda article: article["published_at"] or "", reverse=True)
    return {
        "generated_at": now_utc.astimezone(SHANGHAI).isoformat(),
        "timezone": "Asia/Shanghai",
        "primary_window": {
            "start": primary_start.astimezone(SHANGHAI).isoformat(),
            "end": now_utc.astimezone(SHANGHAI).isoformat(),
        },
        "fallback_start": fallback_start.astimezone(SHANGHAI).isoformat(),
        "target_feeds": list(TARGET_FEEDS),
        "known_concept_labels": [label for label in user_labels if label.startswith(CONCEPT_PREFIX)],
        "selected_label_exists": SELECTED_LABEL in user_labels,
        "counts": counts,
        "articles": articles,
    }


def _normalise_concepts(values: Iterable[str]) -> list[str]:
    concepts: list[str] = []
    for value in values:
        value = value.strip()
        if value.startswith(CONCEPT_PREFIX):
            value = value[len(CONCEPT_PREFIX):]
        if not value or len(value) > 64 or "/" in value or "\n" in value or "\r" in value:
            raise FreshRSSError(f"Invalid concept label: {value!r}")
        if value not in concepts:
            concepts.append(value)
    if not 1 <= len(concepts) <= 3:
        raise FreshRSSError("Each selected article requires one to three unique concepts")
    return concepts


def apply_labels(client: FreshRSSClient, item_id: str, concepts: Iterable[str]) -> list[str]:
    concepts = _normalise_concepts(concepts)
    token = client.get_text("/reader/api/0/token").strip()
    if not token:
        raise FreshRSSError("FreshRSS did not return a mutation token")
    labels = [f"{CONCEPT_PREFIX}{concept}" for concept in concepts] + [SELECTED_LABEL]
    applied: list[str] = []
    for label in labels:
        response = client.post_text(
            "/reader/api/0/edit-tag",
            {
                "i": item_id,
                "a": f"user/-/label/{label}",
                "ac": "edit",
                "T": token,
            },
        ).strip()
        if response != "OK":
            raise FreshRSSError(
                f"FreshRSS rejected label {label!r}; already applied: {', '.join(applied) or 'none'}"
            )
        applied.append(label)
    return applied


def _write_json(value: dict[str, Any], output: str | None) -> None:
    content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if output:
        path = Path(output)
        path.write_text(content, encoding="utf-8")
        primary = sum(1 for article in value.get("articles", []) if article.get("in_primary_window"))
        print(json.dumps({"output": str(path.resolve()), "primary_articles": primary}, ensure_ascii=False))
    else:
        print(content, end="")


def _parse_now(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise FreshRSSError("--now must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("probe", help="Authenticate and verify the three target subscriptions")

    fetch = subparsers.add_parser("fetch", help="Fetch the primary window and seven-day fallback pool")
    fetch.add_argument("--output", help="Write UTF-8 JSON to this path instead of stdout")
    fetch.add_argument("--now", help="Override current time with an ISO-8601 timestamp (testing only)")

    tag = subparsers.add_parser("tag", help="Add concept labels and the selected commit label")
    tag.add_argument("--item-id", required=True)
    tag.add_argument("--concept", action="append", default=[])
    tag.add_argument("--apply", action="store_true", help="Actually modify FreshRSS")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        client = FreshRSSClient.from_env()
        if args.command == "probe":
            subscriptions = _subscription_map(client)
            labels = _user_labels(client)
            result = {
                "base_url": client.base_url,
                "username": client.username,
                "target_subscriptions": subscriptions,
                "user_labels": len(labels),
                "known_concept_labels": [label for label in labels if label.startswith(CONCEPT_PREFIX)],
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "fetch":
            result = fetch_articles(client, now_utc=_parse_now(args.now))
            _write_json(result, args.output)
        elif args.command == "tag":
            concepts = _normalise_concepts(args.concept)
            planned = [f"{CONCEPT_PREFIX}{concept}" for concept in concepts] + [SELECTED_LABEL]
            if not args.apply:
                print(json.dumps({"dry_run": True, "item_id": args.item_id, "labels": planned}, ensure_ascii=False))
            else:
                applied = apply_labels(client, args.item_id, concepts)
                print(json.dumps({"item_id": args.item_id, "applied": applied}, ensure_ascii=False))
        return 0
    except (FreshRSSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
