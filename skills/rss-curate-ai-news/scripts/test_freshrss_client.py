from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from freshrss_client import (  # noqa: E402
    SELECTED_LABEL,
    apply_labels,
    article_from_item,
    choose_article_time,
    html_to_text_and_links,
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


class FreshRSSClientTests(unittest.TestCase):
    def test_html_extraction_skips_active_content_and_keeps_links(self):
        text, links = html_to_text_and_links(
            '<h1>标题</h1><script>ignore()</script><p>正文 <a href="https://example.com/x">来源</a></p>'
        )
        self.assertEqual("标题\n正文 来源", text)
        self.assertEqual(["https://example.com/x"], links)

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
            now - timedelta(days=7),
        )
        self.assertTrue(article["in_primary_window"])
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
            now - timedelta(days=7),
        )
        self.assertEqual("https://example.com/safe", article["article_url"])

    def test_selected_label_is_applied_last_as_commit_marker(self):
        client = FakeClient()
        applied = apply_labels(client, "item-1", ["持续学习", "智能体"])
        self.assertEqual(["AI概念/持续学习", "AI概念/智能体", SELECTED_LABEL], applied)
        labels = [post[1]["a"].split("/label/", 1)[1] for post in client.posts]
        self.assertEqual(applied, labels)
        self.assertTrue(all(post[1]["T"] == "token-123" for post in client.posts))


if __name__ == "__main__":
    unittest.main()
