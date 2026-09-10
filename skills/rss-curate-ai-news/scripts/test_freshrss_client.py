from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stderr
from datetime import datetime, timedelta, timezone
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from freshrss_client import (  # noqa: E402
    DIGEST_SOURCE,
    DIRECT_SOURCE,
    SELECTED_LABEL,
    SELECTED_STORY_PREFIX,
    STORY_CONCEPT_PREFIX,
    FreshRSSError,
    _eligible_subscriptions,
    _resolve_fetch_window,
    _story_concepts,
    _target_subscriptions,
    apply_labels,
    article_from_item,
    build_parser,
    choose_article_time,
    fetch_articles,
    html_to_text_and_links,
    html_to_text_links_and_details,
    labels_for_selection,
    story_key_from_url,
    subscription_source_kind,
)


class FakeClient:
    def __init__(self) -> None:
        self.posts = []

    def get_text(self, path, params=None):
        self.token_path = path
        return "token-123\n"

    def post_text(self, path, params):
        self.posts.append((path, params))
        return "OK"


class FakeSubscriptionClient:
    def __init__(self, subscriptions):
        self.subscriptions = subscriptions

    def get_json(self, path, params=None):
        self.path = path
        return {"subscriptions": self.subscriptions}


class FakeFetchClient:
    def __init__(self, now):
        self.now = now

    def get_json(self, path, params=None):
        if path.endswith("/subscription/list"):
            return {"subscriptions": [
                {"id": "feed/2", "title": "机器之心SOTA模型 - 今天看啥"},
                {"id": "feed/3", "title": "橘鸦AI早报"},
            ]}
        if path.endswith("/tag/list"):
            return {"tags": [
                {"id": "user/-/label/AI%E4%BE%8B%E4%BC%9A/%E5%B7%B2%E9%80%89%E6%96%B0%E9%97%BB/abc123"},
                {"id": "user/-/label/AI例会/新闻概念/abc123/智能体"},
            ]}
        source = "早报正文" if path.endswith("feed/3") else "SOTA 正文"
        return {"items": [{
            "id": "shared-item-id",
            "published": int((self.now - timedelta(hours=1)).timestamp()),
            "canonical": [{"href": f"https://example.com/{path[-1]}"}],
            "summary": {"content": f"<p>{source}</p>"},
        }]}


class FakePaginatedClient(FakeFetchClient):
    def __init__(self, now):
        super().__init__(now)
        self.direct_page_params = []

    def get_json(self, path, params=None):
        if not path.endswith("feed/2"):
            return super().get_json(path, params)
        self.direct_page_params.append(dict(params or {}))
        page = 2 if (params or {}).get("c") == "next-page" else 1
        result = {"items": [{
            "id": f"direct-page-{page}",
            "published": int((self.now - timedelta(hours=page)).timestamp()),
            "canonical": [{"href": f"https://example.com/direct/{page}"}],
            "summary": {"content": f"<p>第 {page} 页</p>"},
        }]}
        if page == 1:
            result["continuation"] = "next-page"
        return result


class FreshRSSClientTests(unittest.TestCase):
    def test_html_extraction_skips_active_content_and_keeps_links(self):
        text, links = html_to_text_and_links(
            '<h1>标题</h1><script>ignore()</script><p>正文 <a href="https://example.com/x">来源</a></p>'
        )
        self.assertEqual("标题\n正文 来源", text)
        self.assertEqual(["https://example.com/x"], links)

    def test_link_occurrences_keep_order_anchor_and_repeated_urls(self):
        _, links, occurrences = html_to_text_links_and_details(
            '<h2>新闻一</h2><a href="https://example.com/x">原文甲</a>'
            '<h2>新闻二</h2><a href="https://example.com/x">原文乙</a>'
        )
        self.assertEqual(["https://example.com/x"], links)
        self.assertEqual([1, 2], [value["ordinal"] for value in occurrences])
        self.assertEqual(["原文甲", "原文乙"], [value["anchor_text"] for value in occurrences])
        self.assertIn("新闻二", occurrences[1]["context_before"])

    def test_subscription_title_rules_are_dynamic_and_whitespace_tolerant(self):
        self.assertEqual(DIRECT_SOURCE, subscription_source_kind("机器之心-今天看啥"))
        self.assertEqual(DIRECT_SOURCE, subscription_source_kind("机器之心SOTA模型 － 今天看啥 "))
        self.assertEqual(DIGEST_SOURCE, subscription_source_kind(" 橘鸦AI早报 "))
        self.assertIsNone(subscription_source_kind("机器之心"))
        self.assertIsNone(subscription_source_kind("今天看啥-备份"))

    def test_eligible_subscriptions_include_all_matching_ids_and_exclude_old_feeds(self):
        client = FakeSubscriptionClient([
            {"id": "feed/1", "title": "新智元"},
            {"id": "feed/2", "title": "新智元 - 今天看啥"},
            {"id": "feed/3", "title": "机器之心SOTA模型-今天看啥"},
            {"id": "feed/4", "title": "量子位 - 今天看啥"},
            {"id": "feed/5", "title": "橘鸦AI早报"},
            {"id": "feed/6", "title": "量子位 - 今天看啥"},
        ])
        matches = _eligible_subscriptions(client)
        self.assertEqual(["feed/2", "feed/3", "feed/4", "feed/6", "feed/5"], [m["feed_id"] for m in matches])
        self.assertEqual(4, sum(m["source_kind"] == DIRECT_SOURCE for m in matches))
        self.assertEqual(DIGEST_SOURCE, matches[-1]["source_kind"])

    def test_target_subscriptions_honor_manual_channel_scope(self):
        client = FakeSubscriptionClient([
            {"id": "feed/2", "title": "新智元 - 今天看啥"},
            {"id": "feed/4", "title": "量子位 - 今天看啥"},
            {"id": "feed/5", "title": "橘鸦AI早报"},
            {"id": "feed/6", "title": "量子位 - 今天看啥"},
        ])
        matches = _target_subscriptions(client, [" 量子位 - 今天看啥 "])
        self.assertEqual(["feed/4", "feed/6"], [match["feed_id"] for match in matches])
        digest_only = _target_subscriptions(client, ["橘鸦AI早报"])
        self.assertEqual(["feed/5"], [match["feed_id"] for match in digest_only])

    def test_target_subscriptions_require_explicit_valid_scope(self):
        client = FakeSubscriptionClient([
            {"id": "feed/2", "title": "新智元 - 今天看啥"},
            {"id": "feed/5", "title": "橘鸦AI早报"},
        ])
        with self.assertRaises(FreshRSSError):
            _target_subscriptions(client)
        with self.assertRaises(FreshRSSError):
            _target_subscriptions(client, ["不存在的频道"])
        self.assertEqual(2, len(_target_subscriptions(client, all_eligible=True)))

    def test_fetch_contract_preserves_same_item_id_from_different_feeds(self):
        now = datetime(2026, 7, 14, 2, tzinfo=timezone.utc)
        result = fetch_articles(
            FakeFetchClient(now),
            window_start=now - timedelta(hours=24),
            window_end=now,
            top_k=4,
            all_eligible=True,
            now_utc=now,
        )
        self.assertEqual(2, len(result["feed_items"]))
        self.assertEqual({"feed/2", "feed/3"}, {item["feed_id"] for item in result["feed_items"]})
        self.assertEqual({DIRECT_SOURCE, DIGEST_SOURCE}, {item["source_kind"] for item in result["feed_items"]})
        self.assertEqual(["abc123"], result["selected_story_keys"])
        self.assertEqual({"abc123": ["智能体"]}, result["story_concepts"])
        self.assertEqual(2, len(result["counts"]))
        self.assertEqual(4, result["selection"]["top_k"])
        self.assertEqual("all_eligible", result["selection"]["channel_mode"])
        self.assertNotIn("fallback_start", result)

    def test_fetch_follows_stream_continuation_until_exhausted(self):
        now = datetime(2026, 7, 14, 2, tzinfo=timezone.utc)
        client = FakePaginatedClient(now)
        result = fetch_articles(
            client,
            window_start=now - timedelta(hours=4),
            window_end=now,
            top_k=2,
            feed_titles=["机器之心SOTA模型 - 今天看啥"],
            now_utc=now,
        )
        direct_items = [item for item in result["feed_items"] if item["feed_id"] == "feed/2"]
        self.assertEqual(["direct-page-1", "direct-page-2"], [item["item_id"] for item in direct_items])
        self.assertEqual(2, len(client.direct_page_params))
        self.assertNotIn("c", client.direct_page_params[0])
        self.assertEqual("next-page", client.direct_page_params[1]["c"])
        self.assertTrue(all("ot" in params for params in client.direct_page_params))

    def test_timestamp_prefers_valid_publication(self):
        now = datetime(2026, 7, 14, 2, tzinfo=timezone.utc)
        published = int((now - timedelta(hours=2)).timestamp())
        crawled = int((now - timedelta(hours=1)).timestamp() * 1000)
        chosen, basis = choose_article_time({"published": published, "crawlTimeMsec": crawled}, now)
        self.assertEqual(datetime.fromtimestamp(published, tz=timezone.utc), chosen)
        self.assertEqual("published", basis)

    def test_timestamp_falls_back_when_publication_is_invalid(self):
        now = datetime(2026, 7, 14, 2, tzinfo=timezone.utc)
        crawled = int((now - timedelta(hours=1)).timestamp() * 1000)
        chosen, basis = choose_article_time({"published": 1, "crawlTimeMsec": crawled}, now)
        self.assertEqual(datetime.fromtimestamp(crawled / 1000, tz=timezone.utc), chosen)
        self.assertEqual("crawl_fallback", basis)

    def test_article_marks_window_and_existing_cognition_labels(self):
        now = datetime(2026, 7, 14, 2, tzinfo=timezone.utc)
        item = {
            "id": "item-1",
            "published": int((now - timedelta(hours=4)).timestamp()),
            "crawlTimeMsec": int((now - timedelta(hours=3)).timestamp() * 1000),
            "title": "测试",
            "canonical": [{"href": "https://example.com/article"}],
            "categories": [
                "user/-/label/AI%E4%BE%8B%E4%BC%9A/%E5%B7%B2%E9%80%89",
                "user/-/label/AI%E6%A6%82%E5%BF%B5/%E6%99%BA%E8%83%BD%E4%BD%93",
            ],
            "summary": {"content": "<p>正文</p>"},
        }
        article = article_from_item(
            item,
            "机器之心",
            now,
            now - timedelta(hours=24),
            now,
        )
        self.assertTrue(article["in_selected_window"])
        self.assertTrue(article["already_selected"])
        self.assertEqual(["AI概念/智能体"], article["concept_labels"])

    def test_article_url_rejects_non_http_canonical(self):
        now = datetime(2026, 7, 14, 2, tzinfo=timezone.utc)
        item = {
            "id": "item-2",
            "published": int((now - timedelta(hours=1)).timestamp()),
            "canonical": [{"href": "javascript:alert(1)"}],
            "alternate": [{"href": "https://example.com/safe"}],
            "summary": {"content": "正文"},
        }
        article = article_from_item(
            item,
            "量子位",
            now,
            now - timedelta(hours=24),
            now,
        )
        self.assertEqual("https://example.com/safe", article["article_url"])

    def test_fetch_excludes_items_outside_selected_window(self):
        now = datetime(2026, 7, 14, 2, tzinfo=timezone.utc)
        result = fetch_articles(
            FakeFetchClient(now),
            window_start=now - timedelta(minutes=30),
            window_end=now,
            top_k=1,
            all_eligible=True,
            now_utc=now,
        )
        self.assertEqual([], result["feed_items"])
        self.assertTrue(all(count["selected_window_feed_items"] == 0 for count in result["counts"]))

    def test_resolve_fetch_window_supports_relative_hours(self):
        now = datetime(2026, 7, 14, 2, tzinfo=timezone.utc)
        args = build_parser().parse_args([
            "fetch", "--feed-title", "量子位 - 今天看啥", "--hours", "36", "--top-k", "5",
        ])
        start, end = _resolve_fetch_window(args, now)
        self.assertEqual(now - timedelta(hours=36), start)
        self.assertEqual(now, end)
        self.assertEqual(5, args.top_k)

    def test_resolve_fetch_window_supports_explicit_range(self):
        args = build_parser().parse_args([
            "fetch", "--all-eligible-feeds", "--start", "2026-07-12T08:00:00+08:00",
            "--end", "2026-07-14T08:00:00+08:00", "--top-k", "3",
        ])
        start, end = _resolve_fetch_window(args, datetime(2026, 7, 14, 2, tzinfo=timezone.utc))
        self.assertEqual(datetime(2026, 7, 12, 0, tzinfo=timezone.utc), start)
        self.assertEqual(datetime(2026, 7, 14, 0, tzinfo=timezone.utc), end)

    def test_fetch_cli_requires_channel_time_and_top_k(self):
        parser = build_parser()
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(["fetch", "--hours", "24", "--top-k", "2"])
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(["fetch", "--all-eligible-feeds", "--hours", "24"])
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(["fetch", "--all-eligible-feeds", "--top-k", "2"])
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(["fetch", "--all-eligible-feeds", "--hours", "24", "--top-k", "0"])
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(["fetch", "--all-eligible-feeds", "--hours", "0", "--top-k", "2"])

    def test_resolve_fetch_window_rejects_mixed_or_incomplete_ranges(self):
        parser = build_parser()
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args([
                "fetch", "--all-eligible-feeds", "--hours", "24", "--start",
                "2026-07-12T08:00:00+08:00", "--end", "2026-07-14T08:00:00+08:00",
                "--top-k", "2",
            ])
        incomplete = parser.parse_args([
            "fetch", "--all-eligible-feeds", "--start", "2026-07-12T08:00:00+08:00",
            "--top-k", "2",
        ])
        with self.assertRaises(FreshRSSError):
            _resolve_fetch_window(incomplete, datetime(2026, 7, 14, 2, tzinfo=timezone.utc))

    def test_legacy_item_selected_label_is_applied_last_as_commit_marker(self):
        client = FakeClient()
        applied = apply_labels(client, "item-1", ["持续学习", "智能体"])
        self.assertEqual(["AI概念/持续学习", "AI概念/智能体", SELECTED_LABEL], applied)
        labels = [post[1]["a"].split("/label/", 1)[1] for post in client.posts]
        self.assertEqual(applied, labels)
        self.assertTrue(all(post[1]["T"] == "token-123" for post in client.posts))

    def test_digest_component_uses_story_marker_without_parent_selected_label(self):
        story_url = "https://Example.com/news/1#section"
        labels = labels_for_selection(
            ["智能体"],
            story_url=story_url,
            digest_component=True,
        )
        self.assertEqual("AI概念/智能体", labels[0])
        self.assertEqual(
            f"{STORY_CONCEPT_PREFIX}{story_key_from_url(story_url)}/智能体",
            labels[1],
        )
        self.assertEqual(
            f"{SELECTED_STORY_PREFIX}{story_key_from_url(story_url)}",
            labels[-1],
        )
        self.assertNotIn(SELECTED_LABEL, labels)

    def test_documented_direct_path_commits_with_story_marker_last(self):
        client = FakeClient()
        story_url = "https://example.com/news/2"
        applied = apply_labels(client, "item-2", ["大语言模型"], story_url=story_url)
        self.assertEqual(f"AI概念/大语言模型", applied[0])
        self.assertEqual(
            f"{STORY_CONCEPT_PREFIX}{story_key_from_url(story_url)}/大语言模型",
            applied[1],
        )
        self.assertEqual(
            f"{SELECTED_STORY_PREFIX}{story_key_from_url(story_url)}",
            applied[-1],
        )
        self.assertNotIn(SELECTED_LABEL, applied)
        self.assertEqual(applied, [post[1]["a"].split("/label/", 1)[1] for post in client.posts])

    def test_story_concepts_remain_associated_for_two_stories_on_one_parent(self):
        first_url = "https://example.com/story/one"
        second_url = "https://example.com/story/two"
        labels = labels_for_selection(["智能体"], story_url=first_url, digest_component=True)
        labels += labels_for_selection(["世界模型"], story_url=second_url, digest_component=True)
        self.assertEqual({
            story_key_from_url(first_url): ["智能体"],
            story_key_from_url(second_url): ["世界模型"],
        }, _story_concepts(labels))

    def test_orphan_story_concepts_are_hidden_until_commit_marker_exists(self):
        labels = labels_for_selection(
            ["智能体"],
            story_url="https://example.com/story/incomplete",
            digest_component=True,
        )
        self.assertEqual({}, _story_concepts(labels[:-1]))

    def test_digest_component_requires_story_url(self):
        with self.assertRaises(FreshRSSError):
            labels_for_selection(["智能体"], digest_component=True)

    def test_tag_cli_requires_story_url_for_new_writes(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            build_parser().parse_args(["tag", "--item-id", "item-1", "--concept", "智能体"])

    def test_story_key_normalizes_fragment_and_default_port_but_preserves_path(self):
        self.assertEqual(
            story_key_from_url("https://EXAMPLE.com:443/news/1/#part"),
            story_key_from_url("https://example.com/news/1/"),
        )
        self.assertNotEqual(
            story_key_from_url("https://example.com/news/1/"),
            story_key_from_url("https://example.com/news/1"),
        )


if __name__ == "__main__":
    unittest.main()
