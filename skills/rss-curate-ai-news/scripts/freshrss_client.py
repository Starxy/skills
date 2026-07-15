#!/usr/bin/env python3
"""Minimal FreshRSS Google Reader API client for rss-curate-ai-news."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import unicodedata
from hashlib import sha256
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlencode, urlsplit, urlunsplit
from urllib.request import ProxyHandler, Request, build_opener


TODAY_FEED_PATTERN = re.compile(r"(?:-|－)\s*今天看啥$")
DIGEST_FEED_TITLE = "橘鸦AI早报"
DIRECT_SOURCE = "direct_article"
DIGEST_SOURCE = "daily_digest"
SELECTED_LABEL = "AI例会/已选"
SELECTED_STORY_PREFIX = "AI例会/已选新闻/"
STORY_CONCEPT_PREFIX = "AI例会/新闻概念/"
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
        self.link_details: list[dict[str, Any]] = []
        self._skip_depth = 0
        self._active_link: dict[str, Any] | None = None

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
                self._active_link = {
                    "url": href,
                    "text_parts": [],
                    "context_before": " ".join("".join(self.parts)[-240:].split()),
                }

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag == "a" and self._active_link:
            detail = {
                "ordinal": len(self.link_details) + 1,
                "url": str(self._active_link["url"]),
                "anchor_text": " ".join("".join(self._active_link["text_parts"]).split()),
                "context_before": str(self._active_link["context_before"]),
            }
            self.link_details.append(detail)
            self._active_link = None
        if not self._skip_depth and tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)
            if self._active_link:
                self._active_link["text_parts"].append(data)


def html_to_text_and_links(value: str) -> tuple[str, list[str]]:
    text, links, _ = html_to_text_links_and_details(value)
    return text, links


def html_to_text_links_and_details(value: str) -> tuple[str, list[str], list[dict[str, Any]]]:
    parser = _ArticleHTMLParser()
    parser.feed(value or "")
    lines = [" ".join(line.split()) for line in "".join(parser.parts).splitlines()]
    text = "\n".join(line for line in lines if line)
    links = list(dict.fromkeys(parser.links))
    return text, links, parser.link_details


def normalize_subscription_title(title: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", html.unescape(title)).split())


def subscription_source_kind(title: str) -> str | None:
    normalized = normalize_subscription_title(title)
    if normalized == DIGEST_FEED_TITLE:
        return DIGEST_SOURCE
    if TODAY_FEED_PATTERN.search(normalized):
        return DIRECT_SOURCE
    return None


def _richest_item_content(item: dict[str, Any]) -> tuple[str, str]:
    candidates: list[tuple[str, str]] = []
    for key in ("content", "summary"):
        value = item.get(key) or {}
        raw = value.get("content", "") if isinstance(value, dict) else str(value)
        if raw:
            candidates.append((key, raw))
    if not candidates:
        return "unavailable", ""
    return max(candidates, key=lambda candidate: len(candidate[1]))


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
    source_kind: str = DIRECT_SOURCE,
    feed_id: str | None = None,
) -> dict[str, Any]:
    chosen_time, basis = choose_article_time(item, now_utc)
    content_source, raw_content = _richest_item_content(item)
    content, embedded_links, link_details = html_to_text_links_and_details(raw_content)
    labels = _extract_labels(item.get("categories") or [])
    crawl_time = _parse_epoch(item.get("crawlTimeMsec"), milliseconds=True)
    article_url = _first_href(item, "canonical") or _first_href(item, "alternate")
    in_primary = bool(chosen_time and primary_start <= chosen_time <= now_utc)
    in_fallback = bool(chosen_time and fallback_start <= chosen_time <= now_utc)
    return {
        "item_id": str(item.get("id", "")),
        "title": html.unescape(str(item.get("title", "")).strip()),
        "feed": feed_title,
        "feed_id": feed_id,
        "source_kind": source_kind,
        "requires_story_expansion": source_kind == DIGEST_SOURCE,
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
        "link_occurrences": link_details,
        "content_source": content_source,
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


def _target_subscriptions(client: FreshRSSClient) -> list[dict[str, str]]:
    data = client.get_json("/reader/api/0/subscription/list", {"output": "json"})
    matches: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for subscription in data.get("subscriptions") or []:
        display_title = html.unescape(str(subscription.get("title", ""))).strip()
        normalized_title = normalize_subscription_title(display_title)
        feed_id = str(subscription.get("id", ""))
        source_kind = subscription_source_kind(normalized_title)
        if not source_kind or not feed_id or feed_id in seen_ids:
            continue
        seen_ids.add(feed_id)
        matches.append({
            "title": display_title,
            "normalized_title": normalized_title,
            "feed_id": feed_id,
            "source_kind": source_kind,
        })

    if not any(match["source_kind"] == DIRECT_SOURCE for match in matches):
        raise FreshRSSError("No subscriptions end with '-今天看啥' (optional spaces are allowed)")
    if not any(match["source_kind"] == DIGEST_SOURCE for match in matches):
        raise FreshRSSError(f"Missing target subscription: {DIGEST_FEED_TITLE}")
    return sorted(
        matches,
        key=lambda match: (
            match["source_kind"] == DIGEST_SOURCE,
            match["normalized_title"],
            match["feed_id"],
        ),
    )


def _user_labels(client: FreshRSSClient) -> list[str]:
    data = client.get_json("/reader/api/0/tag/list", {"output": "json"})
    return _extract_labels(tag.get("id", "") for tag in data.get("tags") or [])


def _selected_story_keys(labels: Iterable[str]) -> list[str]:
    return sorted({
        label[len(SELECTED_STORY_PREFIX):]
        for label in labels
        if label.startswith(SELECTED_STORY_PREFIX)
    })


def _story_concepts(labels: Iterable[str]) -> dict[str, list[str]]:
    labels = list(labels)
    selected_keys = set(_selected_story_keys(labels))
    result: dict[str, list[str]] = {}
    for label in labels:
        if not label.startswith(STORY_CONCEPT_PREFIX):
            continue
        remainder = label[len(STORY_CONCEPT_PREFIX):]
        if "/" not in remainder:
            continue
        story_key, concept = remainder.split("/", 1)
        if story_key in selected_keys and concept:
            result.setdefault(story_key, []).append(concept)
    return {key: list(dict.fromkeys(values)) for key, values in sorted(result.items())}


def _stream_items(
    client: FreshRSSClient,
    path: str,
    api_fetch_start: datetime,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    continuation: str | None = None
    seen_continuations: set[str] = set()
    while True:
        params: dict[str, Any] = {
            "output": "json",
            "n": 1000,
            "ot": int(api_fetch_start.timestamp()),
        }
        if continuation:
            params["c"] = continuation
        data = client.get_json(path, params)
        items.extend(item for item in data.get("items") or [] if isinstance(item, dict))
        next_continuation = str(data.get("continuation") or "").strip()
        if not next_continuation:
            return items
        if next_continuation in seen_continuations:
            raise FreshRSSError(f"FreshRSS repeated a continuation token for {path}")
        seen_continuations.add(next_continuation)
        continuation = next_continuation


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
    subscriptions = _target_subscriptions(client)
    user_labels = _user_labels(client)
    articles: list[dict[str, Any]] = []
    counts: list[dict[str, Any]] = []

    for subscription in subscriptions:
        title = subscription["title"]
        feed_id = subscription["feed_id"]
        source_kind = subscription["source_kind"]
        path = "/reader/api/0/stream/contents/" + quote(feed_id, safe="/")
        feed_articles = []
        seen_in_feed: set[str] = set()
        for item in _stream_items(client, path, api_fetch_start):
            article = article_from_item(
                item,
                title,
                now_utc,
                primary_start,
                fallback_start,
                source_kind=source_kind,
                feed_id=feed_id,
            )
            if not article["item_id"] or article["item_id"] in seen_in_feed:
                continue
            seen_in_feed.add(article["item_id"])
            if article["in_fallback_pool"]:
                feed_articles.append(article)
                articles.append(article)
        counts.append({
            "title": title,
            "feed_id": feed_id,
            "source_kind": source_kind,
            "primary_feed_items": sum(
                1 for article in feed_articles if article["in_primary_window"]
            ),
            "fallback_feed_items": len(feed_articles),
        })

    articles.sort(key=lambda article: article["published_at"] or "", reverse=True)
    return {
        "generated_at": now_utc.astimezone(SHANGHAI).isoformat(),
        "timezone": "Asia/Shanghai",
        "primary_window": {
            "start": primary_start.astimezone(SHANGHAI).isoformat(),
            "end": now_utc.astimezone(SHANGHAI).isoformat(),
        },
        "fallback_start": fallback_start.astimezone(SHANGHAI).isoformat(),
        "source_selection": {
            "direct_feed_title_suffix": "-今天看啥",
            "digest_feed_title": DIGEST_FEED_TITLE,
        },
        "target_subscriptions": subscriptions,
        "target_feeds": [subscription["title"] for subscription in subscriptions],
        "known_concept_labels": [label for label in user_labels if label.startswith(CONCEPT_PREFIX)],
        "selected_story_keys": _selected_story_keys(user_labels),
        "story_concepts": _story_concepts(user_labels),
        "selected_label_exists": SELECTED_LABEL in user_labels,
        "counts": counts,
        "feed_items": articles,
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


def story_key_from_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise FreshRSSError("Story URL must begin with http:// or https:// and include a host")
    host = parsed.hostname.lower()
    port = parsed.port
    if port and not ((parsed.scheme == "http" and port == 80) or (parsed.scheme == "https" and port == 443)):
        host = f"{host}:{port}"
    path = parsed.path or "/"
    normalized = urlunsplit((parsed.scheme.lower(), host, path, parsed.query, ""))
    return sha256(normalized.encode("utf-8")).hexdigest()[:16]


def labels_for_selection(
    concepts: Iterable[str],
    *,
    story_url: str | None = None,
    digest_component: bool = False,
) -> list[str]:
    concepts = _normalise_concepts(concepts)
    if digest_component and not story_url:
        raise FreshRSSError("Digest components require --story-url for component-level history")
    labels = [f"{CONCEPT_PREFIX}{concept}" for concept in concepts]
    if story_url:
        story_key = story_key_from_url(story_url)
        labels.extend(
            f"{STORY_CONCEPT_PREFIX}{story_key}/{concept}" for concept in concepts
        )
        labels.append(f"{SELECTED_STORY_PREFIX}{story_key}")
    else:
        labels.append(SELECTED_LABEL)
    return labels


def apply_labels(
    client: FreshRSSClient,
    item_id: str,
    concepts: Iterable[str],
    *,
    story_url: str | None = None,
    digest_component: bool = False,
) -> list[str]:
    labels = labels_for_selection(
        concepts,
        story_url=story_url,
        digest_component=digest_component,
    )
    token = client.get_text("/reader/api/0/token").strip()
    if not token:
        raise FreshRSSError("FreshRSS did not return a mutation token")
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
        primary = sum(
            1 for item in value.get("feed_items", []) if item.get("in_primary_window")
        )
        print(json.dumps({"output": str(path.resolve()), "primary_feed_items": primary}, ensure_ascii=False))
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

    subparsers.add_parser("probe", help="Authenticate and resolve today's feeds plus the daily digest")

    fetch = subparsers.add_parser("fetch", help="Fetch the primary window and seven-day fallback pool")
    fetch.add_argument("--output", help="Write UTF-8 JSON to this path instead of stdout")
    fetch.add_argument("--now", help="Override current time with an ISO-8601 timestamp (testing only)")

    story_key = subparsers.add_parser("story-key", help="Compute stable keys for canonical story URLs")
    story_key.add_argument("--url", action="append", required=True)

    tag = subparsers.add_parser("tag", help="Add concept labels and a story-level commit marker")
    tag.add_argument("--item-id", required=True)
    tag.add_argument("--concept", action="append", default=[])
    tag.add_argument(
        "--story-url",
        required=True,
        help="Canonical original URL used for story-level history",
    )
    tag.add_argument(
        "--digest-component",
        action="store_true",
        help="Tag one story inside a digest without marking the entire digest as selected",
    )
    tag.add_argument("--apply", action="store_true", help="Actually modify FreshRSS")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "story-key":
            print(json.dumps({
                "stories": [
                    {"url": url, "story_key": story_key_from_url(url)} for url in args.url
                ]
            }, ensure_ascii=False, indent=2))
            return 0
        client = FreshRSSClient.from_env()
        if args.command == "probe":
            subscriptions = _target_subscriptions(client)
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
            planned = labels_for_selection(
                args.concept,
                story_url=args.story_url,
                digest_component=args.digest_component,
            )
            if not args.apply:
                print(json.dumps({"dry_run": True, "item_id": args.item_id, "labels": planned}, ensure_ascii=False))
            else:
                applied = apply_labels(
                    client,
                    args.item_id,
                    args.concept,
                    story_url=args.story_url,
                    digest_component=args.digest_component,
                )
                print(json.dumps({"item_id": args.item_id, "applied": applied}, ensure_ascii=False))
        return 0
    except (FreshRSSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
