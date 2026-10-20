"""Offline API-contract and workflow tests. Never contact or mutate a real library."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import zotero_library as cli
from zotero_api import LibraryConfig, Response, Transport, WebAPI, ZoteroError
from zotero_core import Library, data, note_text_to_html
from zotero_files import Files


def record(key, kind="journalArticle", **fields):
    return {"key": key, "version": 1, "data": {"key": key, "version": 1,
            "itemType": kind, "title": key, "tags": [], "collections": [], "relations": {}, **fields}}


class FakeZotero:
    """An in-memory implementation of the documented HTTP contract, not pyzotero mocks."""

    def __init__(self):
        self.version, self.counter, self.calls = 10, 0, []
        self.items = {
            "PAPER001": record("PAPER001", title="Attention mechanisms for reproducible research", DOI="10.1000/example",
                               tags=[{"tag": "old", "type": 1}], collections=["COLL0001"]),
            "PAPER002": record("PAPER002", title="A different paper", DOI="10.1000/other", collections=["COLL0002"]),
            "ATTACH01": record("ATTACH01", "attachment", parentItem="PAPER001", contentType="application/pdf",
                               linkMode="imported_file", filename="paper.pdf"),
            "NOTE0001": record("NOTE0001", "note", parentItem="PAPER001", note="<p>A useful insight</p>"),
            "ANNOT001": record("ANNOT001", "annotation", parentItem="ATTACH01", annotationType="highlight",
                               annotationText="Exact words", annotationComment="Important", annotationPosition={
                                   "pageIndex": 0, "rects": [[10, 20, 200, 40]]})}
        self.collections = {"COLL0001": {"key": "COLL0001", "version": 1,
                "data": {"key": "COLL0001", "version": 1, "name": "Inbox", "parentCollection": False}},
            "COLL0002": {"key": "COLL0002", "version": 1,
                "data": {"key": "COLL0002", "version": 1, "name": "Reviewed", "parentCollection": False}}}
        self.searches = {}
        self.fulltexts = {"ATTACH01": {"content": "Synced full text with attention mechanisms.",
                                      "indexedPages": 3, "totalPages": 5}}
        self.files = {"ATTACH01": b"%PDF-fake-stored-bytes"}
        self.items["ATTACH01"]["data"]["md5"] = hashlib.md5(self.files["ATTACH01"]).hexdigest()
        self.pending, self.overrides = {}, {}
        self.storage_status, self.exists_response = 201, False
        self.key_info_response = self.response({"key": "test-secret", "userID": 12345,
                                               "access": {"user": {"library": True, "write": True}}})

    def response(self, body=None, status=200, headers=None):
        body = b"" if body is None else body if isinstance(body, bytes) else json.dumps(body).encode()
        return Response(status, {"last-modified-version": str(self.version), **(headers or {})}, body)

    def store(self, source, fields):
        self.version += 1
        source["data"].update(copy.deepcopy(fields))
        source["version"] = self.version
        source["data"]["version"] = self.version
        return copy.deepcopy(source)

    def request(self, method, url, *, headers=None, body=None):
        parts, headers = urlsplit(url), dict(headers or {})
        path, params = parts.path, parse_qs(parts.query)
        self.calls.append({"method": method, "url": url, "path": path, "headers": headers, "body": body, "params": params})
        if parts.netloc == "storage.zotero.test":
            return self.response(status=self.storage_status)
        if path == "/keys/test-secret":
            return self.key_info_response
        if path == "/users/12345/groups":
            return self.response([{"id": 54321, "data": {"name": "Lab"}}])
        if path == "/items/new":
            kind = params["itemType"][0]
            template = {"itemType": kind, "title": "", "creators": [], "tags": [], "collections": [], "extra": ""}
            if kind == "note":
                template = {"itemType": "note", "note": "", "tags": [], "collections": []}
            if kind == "attachment":
                template = {"itemType": "attachment", "linkMode": params["linkMode"][0], "filename": "", "title": "",
                            "contentType": "", "md5": None, "mtime": None, "tags": []}
            if kind == "annotation":
                template = {"itemType": "annotation", "parentItem": "", "annotationType": params["annotationType"][0],
                            "annotationText": "", "annotationComment": "", "annotationColor": "", "annotationPageLabel": "",
                            "annotationSortIndex": "00000|000000|00000", "annotationPosition": {}, "tags": []}
            return self.response(template)
        if path in {"/itemTypes", "/itemFields", "/itemTypeFields", "/itemTypeCreatorTypes", "/creatorFields"}:
            return self.response([{"field": "title"}])
        bits = path.strip("/").split("/")
        if bits[0] not in {"users", "groups"}:
            return self.response("Unexpected endpoint", 404)
        path = "/" + "/".join(bits[2:])
        override = self.overrides.get((method, path))
        if override:
            return override(self.calls[-1]) if callable(override) else override
        resource = path.strip("/").split("/")[0]
        pool = {"items": self.items, "collections": self.collections, "searches": self.searches}.get(resource)
        if path == "/deleted":
            return self.response({"items": [], "collections": [], "searches": [], "tags": []})
        if path == "/fulltext":
            return self.response({k: self.version for k in self.fulltexts})
        if path.endswith("/fulltext"):
            key = path.split("/")[2]
            if method == "GET":
                return self.response(self.fulltexts[key]) if key in self.fulltexts else self.response("Not found", 404)
            self.fulltexts[key] = json.loads(body)
            self.version += 1
            return self.response(status=204)
        if path.endswith("/file"):
            key = path.split("/")[2]
            if method == "GET":
                return self.response(self.files[key]) if key in self.files else self.response("File not found", 404)
            form = parse_qs(body.decode())
            if "upload" in form:
                self.store(self.items[key], {"md5": self.pending[key]["md5"][0]})
                return self.response(status=204)
            self.pending[key] = form
            if self.exists_response:
                self.store(self.items[key], {"md5": form["md5"][0]})
                return self.response({"exists": 1})
            return self.response({"url": "https://storage.zotero.test/upload", "prefix": "PREFIX", "suffix": "SUFFIX",
                                  "contentType": "multipart/form-data; boundary=123", "uploadKey": "upload-key"})
        if method == "POST" and pool is not None:
            values = json.loads(body)
            if len(values) > 50:
                return self.response("Too many records", 400)
            success, failed = {}, {}
            for i, value in enumerate(values):
                if value.get("title") == "reject":
                    failed[str(i)] = {"code": 400, "message": "Bad field"}
                    continue
                key = value.get("key")
                if key and key in pool:
                    if value.get("version") != pool[key]["version"]:
                        failed[str(i)] = {"code": 412, "message": "Version conflict"}
                        continue
                    success[str(i)] = self.store(pool[key], value)
                else:
                    self.counter += 1
                    key = f"NEW{self.counter:05d}"
                    self.version += 1
                    pool[key] = {"key": key, "version": self.version, "data": {"key": key, "version": self.version, **value}}
                    success[str(i)] = copy.deepcopy(pool[key])
            return self.response({"successful": success, "failed": failed, "unchanged": {}})
        bits = path.strip("/").split("/")
        if method in {"PATCH", "PUT", "DELETE"} and pool is not None and len(bits) == 2:
            key = bits[1]
            if key not in pool:
                return self.response("Not found", 404)
            if headers.get("If-Unmodified-Since-Version") != str(pool[key]["version"]):
                return self.response("Stale version", 412)
            if resource == "collections" and method == "PATCH":
                return self.response("PATCH not documented for collections", 405)
            if method == "DELETE":
                del pool[key]
                self.version += 1
            else:
                self.store(pool[key], json.loads(body))
            return self.response(status=204)
        if path == "/searches" and method == "DELETE":
            if headers.get("If-Unmodified-Since-Version") != str(self.version):
                return self.response("Stale library", 412)
            del self.searches[params["searchKey"][0]]
            self.version += 1
            return self.response(status=204)
        if method != "GET":
            return self.response("Unexpected method", 405)
        if pool is not None and len(bits) == 2 and bits[1] not in {"top", "trash"}:
            return self.response(pool[bits[1]]) if bits[1] in pool else self.response("Not found", 404)
        values = list(pool.values()) if pool is not None else []
        if resource == "items":
            values = [r for r in values if bool(data(r).get("deleted")) == (path == "/items/trash")]
            if path == "/items/top":
                values = [r for r in values if not data(r).get("parentItem")]
            if len(bits) == 3 and bits[-1] == "children":
                values = [r for r in self.items.values() if data(r).get("parentItem") == bits[1] and not data(r).get("deleted")]
        if resource == "collections" and len(bits) >= 3 and bits[2] == "items":
            values = [r for r in self.items.values() if bits[1] in data(r).get("collections", []) and not data(r).get("deleted")]
        if path == "/tags":
            names = sorted({t["tag"] for r in self.items.values() for t in data(r).get("tags", [])})
            values = [{"tag": n, "type": 0} for n in names]
        if params.get("q"):
            query = params["q"][0].lower()
            values = [r for r in values if query in json.dumps(r, ensure_ascii=False).lower()]
        if params.get("tag"):
            values = [r for r in values if set(params["tag"]) <= {t["tag"] for t in data(r).get("tags", [])}]
        if params.get("itemType"):
            values = [r for r in values if data(r).get("itemType") == params["itemType"][0]]
        if params.get("itemKey"):
            keys = params["itemKey"][0].split(",")
            values = [r for r in values if r["key"] in keys]
        fmt = params.get("format", ["json"])[0]
        if fmt == "versions":
            return self.response({r["key"]: r["version"] for r in values})
        total = len(values)
        start, limit = int(params.get("start", [0])[0]), int(params.get("limit", [25])[0])
        values = values[start:start + limit]
        headers = {"total-results": str(total)}
        if fmt == "csljson":
            return self.response([{"id": r["key"], "title": data(r).get("title")} for r in values], headers=headers)
        if fmt in {"bibtex", "ris", "bib", "biblatex", "refer"}:
            return self.response("\n".join("@article{" + r["key"] + ",title={" + data(r).get("title", "") + "}}" for r in values).encode(), headers=headers)
        return self.response(copy.deepcopy(values), headers=headers)

    def writes(self):
        return [r for r in self.calls if r["method"] not in {"GET", "HEAD"}]


class ConfigTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {"ZOTERO_API_KEY": "test-secret",
                                             "ZOTERO_CACHE_DIR": tempfile.gettempdir()}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        self.server = FakeZotero()
        transport = patch("zotero_api.Transport", return_value=self.server)
        transport.start()
        self.addCleanup(transport.stop)

    def run_command(self, *args):
        return cli.dispatch(cli.build_parser().parse_args(args))

    def test_key_alone_discovers_personal_library_id(self):
        for user_id in (12345, "12345"):
            with self.subTest(user_id=user_id):
                self.server.key_info_response = self.server.response({"userID": user_id})
                config = LibraryConfig.from_env()
                self.assertEqual(config.library_id, "12345")
                self.assertEqual(config.prefix, "/users/12345")
                self.assertNotIn("test-secret", repr(config))
        call = self.server.calls[0]
        self.assertEqual((call["method"], call["path"]), ("GET", "/keys/test-secret"))
        self.assertEqual(call["headers"]["Zotero-API-Key"], "test-secret")

    def test_explicit_and_environment_ids_skip_discovery(self):
        os.environ["ZOTERO_LIBRARY_ID"] = "23456"
        self.assertEqual(LibraryConfig.from_env("54321").library_id, "54321")
        self.assertEqual(LibraryConfig.from_env().library_id, "23456")
        self.assertEqual(LibraryConfig.from_env("54321", "group").prefix, "/groups/54321")
        self.assertFalse(self.server.calls)

    def test_public_library_with_explicit_id_needs_no_key(self):
        os.environ.pop("ZOTERO_API_KEY")
        config = LibraryConfig.from_env("12345")
        self.assertEqual(config.library_id, "12345")
        self.assertIsNone(config.api_key)
        self.assertFalse(self.server.calls)

    def test_empty_environment_id_allows_discovery(self):
        os.environ["ZOTERO_LIBRARY_ID"] = ""
        self.assertEqual(LibraryConfig.from_env().library_id, "12345")

    def test_group_without_id_does_not_select_personal_library(self):
        for origin in ("argument", "environment"):
            with self.subTest(origin=origin):
                os.environ["ZOTERO_LIBRARY_TYPE"] = "group" if origin == "environment" else "user"
                with self.assertRaises(ZoteroError) as error:
                    LibraryConfig.from_env(library_type="group" if origin == "argument" else None)
                self.assertEqual(error.exception.code, "configuration")
        self.assertFalse(self.server.calls)

    def test_invalid_explicit_selection_does_not_fall_back_to_discovery(self):
        for options in ({"library_id": "not-numeric"}, {"library_type": "unknown"}):
            with self.subTest(options=options), self.assertRaises(ZoteroError) as error:
                LibraryConfig.from_env(**options)
            self.assertEqual(error.exception.code, "configuration")
        os.environ["ZOTERO_LIBRARY_ID"] = "not-numeric"
        with self.assertRaises(ZoteroError) as error:
            LibraryConfig.from_env()
        self.assertEqual(error.exception.code, "configuration")
        self.assertFalse(self.server.calls)

    def test_missing_key_and_id_reports_configuration_error(self):
        os.environ.pop("ZOTERO_API_KEY")
        with self.assertRaises(ZoteroError) as error:
            LibraryConfig.from_env()
        self.assertEqual(error.exception.code, "configuration")
        self.assertIn("ZOTERO_API_KEY", str(error.exception))
        self.assertFalse(self.server.calls)

    def test_discovery_rejects_missing_or_invalid_user_id(self):
        payloads = [None, [], {}, {"userID": None}, {"userID": "bad"}, {"userID": -1},
                    {"userID": True}, {"userID": 0}, {"userID": "１２３"}, b"not JSON"]
        for payload in payloads:
            with self.subTest(payload=payload):
                self.server.key_info_response = self.server.response(payload)
                with self.assertRaises(ZoteroError) as error:
                    LibraryConfig.from_env()
                self.assertEqual(error.exception.code, "invalid_response")
        self.assertFalse(self.server.writes())

    def test_discovery_http_errors_are_structured_and_redact_key(self):
        for status, code in ((401, "authentication"), (403, "permission_denied"), (500, "api_error")):
            with self.subTest(status=status):
                self.server.key_info_response = self.server.response("test-secret denied", status)
                output = io.StringIO()
                with patch("sys.stdout", output):
                    result = cli.main(["config"])
                self.assertEqual(result, 1)
                self.assertEqual(json.loads(output.getvalue())["error"]["code"], code)
                self.assertNotIn("test-secret", output.getvalue())

    def test_discovery_network_error_is_preserved(self):
        with (patch.object(self.server, "request", side_effect=ZoteroError("Offline", "network_error")),
              self.assertRaises(ZoteroError) as error):
            LibraryConfig.from_env()
        self.assertEqual(error.exception.code, "network_error")

    def test_key_only_commands_configure_read_and_write_personal_library(self):
        config = self.run_command("config")
        self.assertEqual((config["library_id"], config["library_type"]), ("12345", "user"))
        self.assertTrue(config["api_key_configured"])
        self.assertNotIn("test-secret", json.dumps(config))
        self.assertEqual(self.run_command("search", "attention")["count"], 1)
        created = self.run_command("create-item", "book", "--fields", '{"title":"Key-only workflow"}')
        key = created["result"][0]["key"]
        self.run_command("add-to-collection", "Reviewed", key)
        self.run_command("add-tags", key, "automated")
        item = data(self.server.items[key])
        self.assertEqual(item["collections"], ["COLL0002"])
        self.assertIn("automated", {tag["tag"] for tag in item["tags"]})
        self.assertTrue(all(call["path"].startswith("/users/12345/") for call in self.server.writes()))

    def test_key_info_works_without_library_id_and_omits_key(self):
        info = self.run_command("key-info")
        self.assertEqual(info["userID"], 12345)
        self.assertNotIn("key", info)


class LibraryFixture:
    def setUp(self):
        self.environment = patch.dict(os.environ, {"ZOTERO_LIBRARY_ID": "12345", "ZOTERO_LIBRARY_TYPE": "user",
                                                   "ZOTERO_API_KEY": "test-secret"}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.server = FakeZotero()
        self.api = WebAPI(LibraryConfig.from_env(), self.server)
        self.lib = Library(self.api)

    def run_command(self, *args):
        return cli.dispatch(cli.build_parser().parse_args(args), self.api)


class LibraryTests(LibraryFixture, unittest.TestCase):
    def test_environment_selects_web_even_when_old_local_flag_is_set(self):
        os.environ["ZOTERO_LOCAL"] = "true"
        config = LibraryConfig.from_env("54321", "group")
        self.assertEqual(config.prefix, "/groups/54321")
        self.assertEqual(config.api_base, "https://api.zotero.org")
        self.assertNotIn("test-secret", repr(config))

    def test_create_executes_without_execute_or_confirmation(self):
        result = self.run_command("create-item", "book", "--fields", '{"title":"New book"}')
        self.assertEqual(result["status"], "executed")
        self.assertEqual(len(self.server.writes()), 1)
        call = self.server.writes()[0]
        self.assertEqual(len(call["headers"]["Zotero-Write-Token"]), 32)
        self.assertEqual(data(result["result"][0])["title"], "New book")

    def test_dry_run_before_and_after_subcommand_prevents_writes(self):
        for argv in [("--dry-run", "create-note", "PAPER001", "--text", "Preview"),
                     ("create-note", "PAPER001", "--text", "Preview", "--dry-run")]:
            self.assertEqual(self.run_command(*argv)["status"], "dry-run")
        self.assertFalse(self.server.writes())

    def test_every_remote_mutator_respects_optional_dry_run(self):
        cases = [
            ["create-item", "book", "--fields", '{"title":"T"}'],
            ["import-items", "--data", '[{"itemType":"book","title":"T"}]'],
            ["update-item", "PAPER001", "--fields", '{"title":"Changed"}'],
            ["delete-item", "PAPER001"], ["delete-item", "PAPER001", "--permanent"],
            ["create-collection", "New"], ["update-collection", "COLL0001", "--fields", '{"name":"New"}'],
            ["delete-collection", "COLL0001"], ["add-to-collection", "COLL0002", "PAPER001"],
            ["move-to-collection", "COLL0002", "PAPER001"], ["remove-from-collection", "COLL0001", "PAPER001"],
            ["add-tags", "PAPER001", "new"], ["remove-tags", "PAPER001", "old"], ["rename-tag", "old", "new"],
            ["batch-update", "PAPER001", "--add-tag", "new"],
            ["create-note", "PAPER001", "--text", "Note"], ["update-note", "NOTE0001", "--text", "Changed"],
            ["delete-note", "NOTE0001"], ["delete-annotation", "ANNOT001"],
            ["create-annotation", "ATTACH01", "--type", "highlight", "--position", '{"pageIndex":0,"rects":[[1,2,3,4]]}'],
            ["update-annotation", "ANNOT001", "--fields", '{"annotationComment":"New"}'],
            ["set-parent", "NOTE0001", "--parent", "PAPER002"],
            ["set-fulltext", "ATTACH01", "--fields", '{"content":"X","indexedPages":1,"totalPages":1}'],
            ["attach", "--parent", "PAPER001", "--url", "https://example.org/paper.pdf"],
            ["add-relation", "PAPER001", "PAPER002"], ["remove-relation", "PAPER001", "PAPER002"],
            ["merge-duplicates", "PAPER001", "PAPER002"],
            ["saved-searches", "create", "--name", "Search", "--conditions", "[]"]]
        before = copy.deepcopy((self.server.items, self.server.collections, self.server.fulltexts))
        for case in cases:
            with self.subTest(command=case[0]):
                self.run_command(*case, "--dry-run")
        self.assertFalse(self.server.writes())
        self.assertEqual(before, (self.server.items, self.server.collections, self.server.fulltexts))

    def test_legacy_execute_is_optional_compatibility_only(self):
        self.run_command("update-item", "PAPER001", "--fields", '{"title":"New"}', "--execute")
        self.assertEqual(data(self.server.items["PAPER001"])["title"], "New")

    def test_pagination_fetches_every_item_beyond_100(self):
        for i in range(205):
            self.server.items[f"B{i:07d}"] = record(f"B{i:07d}")
        result = self.lib.list_items(all_items=True)
        self.assertEqual(result["count"], 210)
        self.assertEqual([c["params"].get("start") for c in self.server.calls], [["0"], ["100"], ["200"]])

    def test_fulltext_search_uses_official_qmode_not_a_local_index(self):
        self.run_command("search", "attention", "--mode", "fulltext")
        self.assertEqual(self.server.calls[-1]["params"]["qmode"], ["everything"])

    def test_tag_search_preserves_unicode_and_spaces_in_query(self):
        data(self.server.items["PAPER001"])["tags"].append({"tag": "待读 review", "type": 0})
        result = self.run_command("search", "--mode", "tag", "待读 review")
        self.assertEqual(result["count"], 1)
        self.assertEqual(self.server.calls[-1]["params"]["tag"], ["待读 review"])

    def test_tag_mode_with_flag_does_not_add_an_empty_tag_filter(self):
        result = self.run_command("search", "--mode", "tag", "--tag", "old")
        self.assertEqual(result["count"], 1)
        self.assertEqual(self.server.calls[-1]["params"]["tag"], ["old"])

    def test_advanced_search_preserves_native_tag_filter(self):
        result = self.run_command("search", "--mode", "advanced", "--conditions",
                                  '[{"field":"title","operation":"exists"}]', "--tag", "old")
        self.assertEqual([r["key"] for r in result["items"]], ["PAPER001"])

    def test_advanced_search_combines_metadata_conditions(self):
        result = self.lib.advanced_search([
            {"field": "title", "operation": "contains", "value": "attention"},
            {"field": "tags", "operation": "is", "value": "old"}], join="all")
        self.assertEqual([r["key"] for r in result["items"]], ["PAPER001"])

    def test_invalid_condition_does_not_silently_return_no_results(self):
        with self.assertRaises(ZoteroError) as error:
            self.lib.advanced_search([{"field": "title", "operation": "typo", "value": "X"}])
        self.assertEqual(error.exception.code, "bad_conditions")

    def test_citation_key_falls_back_to_synced_extra(self):
        data(self.server.items["PAPER001"])["extra"] = "Citation Key: author2026\n"
        self.assertEqual(self.lib.citation_key_search("author2026")["items"][0]["key"], "PAPER001")

    def test_update_sends_version_guard_and_reads_back(self):
        result = self.lib.update_item("PAPER001", {"title": "New"})
        call = self.server.writes()[0]
        self.assertEqual(call["headers"]["If-Unmodified-Since-Version"], "1")
        self.assertGreater(result["result"]["version"], 1)

    def test_readback_failure_distinguishes_an_acknowledged_update(self):
        reads = 0

        def read(call):
            nonlocal reads
            reads += 1
            return (self.server.response(self.server.items["PAPER001"]) if reads == 1 else
                    self.server.response("Readback temporarily unavailable", 500))

        self.server.overrides[("GET", "/items/PAPER001")] = read
        with self.assertRaises(ZoteroError) as error:
            self.lib.update_item("PAPER001", {"title": "Actually saved"})
        self.assertEqual(error.exception.code, "verification_failed")
        self.assertTrue(error.exception.details["write_acknowledged"])
        self.assertEqual(data(self.server.items["PAPER001"])["title"], "Actually saved")

    def test_create_rejects_accidental_existing_key_version_payload(self):
        with self.assertRaises(ZoteroError):
            self.lib.create_item("book", {"key": "PAPER001", "version": 1})
        self.assertFalse(self.server.writes())

    def test_stale_version_is_reported_without_retrying_write(self):
        self.server.overrides[("PATCH", "/items/PAPER001")] = self.server.response("Conflict", 412)
        with self.assertRaises(ZoteroError) as error:
            self.lib.update_item("PAPER001", {"title": "New"})
        self.assertEqual(error.exception.code, "version_conflict")
        self.assertEqual(len(self.server.writes()), 1)

    def test_http_200_with_partial_create_failure_is_an_error(self):
        with self.assertRaises(ZoteroError) as error:
            self.lib.import_items([{"itemType": "book", "title": "Good"}, {"itemType": "book", "title": "reject"}])
        self.assertEqual(error.exception.code, "partial_write")
        self.assertEqual(len(error.exception.details["completed"]), 1)
        self.assertEqual(len([r for r in self.server.items.values() if data(r).get("title") == "Good"]), 1)

    def test_large_create_splits_at_api_limit(self):
        results = self.api.create([{"itemType": "book", "title": str(i)} for i in range(55)])
        self.assertEqual(len(results), 55)
        self.assertEqual([len(json.loads(c["body"])) for c in self.server.writes()], [50, 5])

    def test_batch_failure_reports_earlier_successes(self):
        self.server.overrides[("PATCH", "/items/PAPER002")] = self.server.response("Conflict", 412)
        with self.assertRaises(ZoteroError) as error:
            self.lib.batch_update(["PAPER001", "PAPER002"], fields={"title": "New"})
        self.assertEqual(error.exception.code, "partial_write")
        self.assertEqual(error.exception.details["failed_key"], "PAPER002")
        self.assertEqual(len(error.exception.details["completed"]), 1)

    def test_collection_update_uses_put_not_item_patch(self):
        self.lib.update_collection("COLL0001", {"name": "New"})
        call = self.server.writes()[0]
        self.assertEqual(call["method"], "PUT")
        self.assertEqual(json.loads(call["body"])["parentCollection"], False)

    def test_move_collection_is_one_atomic_membership_patch(self):
        self.lib.membership(["PAPER001"], add=["Reviewed"], move=True)
        self.assertEqual(len(self.server.writes()), 1)
        self.assertEqual(data(self.server.items["PAPER001"])["collections"], ["COLL0002"])

    def test_ambiguous_collection_is_rejected_before_writing(self):
        self.server.collections["COLL0003"] = {"key": "COLL0003", "version": 1,
            "data": {"name": "Inbox", "parentCollection": False}}
        with self.assertRaises(ZoteroError) as error:
            self.lib.membership(["PAPER001"], add=["Inbox"])
        self.assertEqual(error.exception.code, "ambiguous_collection")
        self.assertFalse(self.server.writes())

    def test_collection_path_resolves_nested_name(self):
        data(self.server.collections["COLL0002"])["parentCollection"] = "COLL0001"
        self.assertEqual(self.lib.resolve_collection("Inbox/Reviewed"), "COLL0002")

    def test_rename_tag_preserves_automatic_type(self):
        self.lib.rename_tag("old", "renamed")
        self.assertEqual(data(self.server.items["PAPER001"])["tags"], [{"tag": "renamed", "type": 1}])

    def test_plain_note_text_escapes_markup_and_formats_lists(self):
        body = note_text_to_html("<script>bad</script>\n- 方法\n- 结果", "阅读笔记")
        self.assertIn("&lt;script&gt;", body)
        self.assertIn("<li>方法</li>", body)
        self.lib.create_note("PAPER001", text="Hello")
        self.assertEqual(data(next(r for r in self.server.items.values() if r["key"].startswith("NEW")))["parentItem"], "PAPER001")

    def test_note_append_keeps_previous_html(self):
        self.lib.update_note("NOTE0001", text="More", append=True)
        self.assertIn("A useful insight", data(self.server.items["NOTE0001"])["note"])
        self.assertIn("More", data(self.server.items["NOTE0001"])["note"])

    def test_annotations_traverse_paper_attachments(self):
        result = self.lib.annotations("PAPER001", "Exact")
        self.assertEqual([r["key"] for r in result["items"]], ["ANNOT001"])

    def test_annotation_uses_explicit_position_json_and_official_template(self):
        position = {"pageIndex": 2, "rects": [[10, 20, 100, 50]]}
        result = self.lib.create_annotation("ATTACH01", "highlight", position, text="Quoted words")
        annotation = data(result["result"][0])
        self.assertEqual(annotation["annotationPosition"], position)
        self.assertEqual(annotation["annotationPageLabel"], "3")
        self.assertEqual(annotation["annotationSortIndex"], "00002|000000|00000")
        self.assertTrue(any(c["params"].get("annotationType") == ["highlight"] for c in self.server.calls))

    def test_wrong_typed_delete_cannot_delete_a_parent_paper(self):
        with self.assertRaises(ZoteroError):
            self.lib.delete_typed("PAPER001", "note")
        self.assertFalse(self.server.writes())

    def test_fulltext_preserves_partial_index_statistics(self):
        result = self.lib.fulltext("PAPER001")
        self.assertFalse(result["attachments"][0]["complete"])
        self.assertEqual(result["attachments"][0]["content"], self.server.fulltexts["ATTACH01"]["content"])

    def test_missing_synced_fulltext_is_explicit(self):
        self.server.fulltexts.clear()
        self.assertFalse(self.lib.fulltext("ATTACH01")["attachments"][0]["available"])

    def test_upload_fulltext_verifies_supplied_statistics_and_reads_back(self):
        result = self.lib.set_fulltext("ATTACH01", {"content": "All", "indexedPages": 1, "totalPages": 1})
        self.assertTrue(result["result"]["attachments"][0]["complete"])
        with self.assertRaises(ZoteroError):
            self.lib.set_fulltext("ATTACH01", {"content": "Bad", "indexedPages": 2, "totalPages": 1})

    def test_duplicate_merge_moves_children_and_keeps_metadata(self):
        self.server.items["CHILD002"] = record("CHILD002", "attachment", parentItem="PAPER002")
        data(self.server.items["PAPER002"])["tags"] = [{"tag": "other", "type": 0}]
        data(self.server.items["PAPER002"])["abstractNote"] = "Preserved abstract"
        result = self.lib.merge_duplicates("PAPER001", ["PAPER002"])
        kept = data(self.server.items["PAPER001"])
        self.assertEqual(data(self.server.items["CHILD002"])["parentItem"], "PAPER001")
        self.assertEqual(kept["abstractNote"], "Preserved abstract")
        self.assertEqual(set(kept["collections"]), {"COLL0001", "COLL0002"})
        self.assertEqual(data(self.server.items["PAPER002"])["deleted"], 1)
        self.assertIn("title", result["result"]["preserved_conflicts"])
        self.assertTrue(all(c["method"] != "DELETE" for c in self.server.writes()))

    def test_find_duplicates_distinguishes_same_doi(self):
        data(self.server.items["PAPER002"])["DOI"] = "https://doi.org/10.1000/EXAMPLE"
        result = self.lib.find_duplicates()
        self.assertTrue(result["groups"][0]["high_confidence"])

    def test_bidirectional_relation_is_saved_on_both_items(self):
        self.lib.relation("PAPER001", "PAPER002")
        self.assertIn("http://zotero.org/users/12345/items/PAPER002", data(self.server.items["PAPER001"])["relations"]["dc:relation"])
        self.assertIn("http://zotero.org/users/12345/items/PAPER001", data(self.server.items["PAPER002"])["relations"]["dc:relation"])

    def test_trash_and_permanent_deletion_have_distinct_effects(self):
        self.lib.delete_items(["PAPER001"])
        self.assertIn("PAPER001", self.server.items)
        self.assertEqual(data(self.server.items["PAPER001"])["deleted"], 1)
        self.lib.delete_items(["PAPER002"], permanent=True)
        self.assertNotIn("PAPER002", self.server.items)

    def test_synthesis_contains_real_notes_and_annotations(self):
        result = self.lib.synthesize(keys=["PAPER001"])
        self.assertEqual(result["papers"][0]["notes"][0]["key"], "NOTE0001")
        self.assertEqual(result["papers"][0]["annotations"][0]["key"], "ANNOT001")

    def test_group_listing_and_cross_library_search_use_scoped_clients(self):
        result = self.run_command("search", "attention", "--all-libraries")
        self.assertEqual(len(result["libraries"]), 2)
        self.assertTrue(any(c["path"].startswith("/groups/54321/items") for c in self.server.calls))

    def test_collection_export_follows_all_pages(self):
        for i in range(205):
            self.server.items[f"B{i:07d}"] = record(f"B{i:07d}", collections=["COLL0001"])
        result = self.lib.export(collection="COLL0001", fmt="csljson")
        self.assertEqual(len(result["items"]), 206)

    def test_saved_search_update_is_versioned_post_and_delete_uses_library_version(self):
        created = self.lib.saved_searches("create", name="My search", conditions=[])["result"][0]
        key = created["key"]
        self.lib.saved_searches("update", key=key, fields={"name": "Renamed"})
        update = self.server.writes()[-1]
        self.assertNotIn("Zotero-Write-Token", update["headers"])
        self.assertIn("version", json.loads(update["body"])[0])
        self.lib.saved_searches("delete", key=key)
        self.assertNotIn(key, self.server.searches)

    def test_incremental_changes_only_propose_a_consistent_checkpoint(self):
        result = self.lib.changes(0)
        self.assertEqual(result["checkpoint"], 10)
        self.server.overrides[("GET", "/fulltext")] = self.server.response({}, headers={"last-modified-version": "11"})
        result = self.lib.changes(0)
        self.assertFalse(result["consistent"])
        self.assertIsNone(result["checkpoint"])

    def test_cli_errors_are_structured_and_do_not_leak_key(self):
        self.server.overrides[("PATCH", "/items/PAPER001")] = self.server.response("test-secret denied", 403)
        output = io.StringIO()
        with patch.object(cli, "WebAPI", return_value=self.api), patch("sys.stdout", output):
            status = cli.main(["update-item", "PAPER001", "--fields", '{"title":"T"}'])
        self.assertEqual(status, 1)
        self.assertNotIn("test-secret", output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["error"]["code"], "permission_denied")

    def test_invalid_arguments_are_json_errors(self):
        output = io.StringIO()
        with patch("sys.stdout", output):
            status = cli.main(["search", "x", "--mode", "semantic"])
        self.assertEqual(status, 1)
        self.assertEqual(json.loads(output.getvalue())["error"]["code"], "bad_arguments")

    def test_root_library_override_is_not_reset_by_subparser(self):
        args = cli.build_parser().parse_args(["--library-id", "54321", "--library-type", "group", "search", "x"])
        self.assertEqual(args.library_id, "54321")
        self.assertEqual(args.library_type, "group")

    def test_note_search_honors_pagination(self):
        self.server.items["NOTE0002"] = record("NOTE0002", "note", note="Second note")
        result = self.run_command("search", "", "--mode", "notes", "--limit", "1")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["next_start"], 1)

    def test_note_search_does_not_silently_ignore_collection_filter(self):
        with self.assertRaises(ZoteroError):
            self.run_command("search", "insight", "--mode", "notes", "--collection", "Inbox")

    def test_advanced_all_and_sort_return_all_matches(self):
        for i in range(30):
            self.server.items[f"B{i:07d}"] = record(f"B{i:07d}", title=f"Book {i:02d}")
        result = self.run_command("advanced-search", "--conditions", '[{"field":"title","operation":"contains","value":"Book"}]',
                                  "--all", "--sort", "title", "--direction", "desc")
        self.assertEqual(result["count"], 30)
        self.assertEqual(result["items"][0]["title"], "Book 29")

    def test_key_info_omits_key_value(self):
        result = self.run_command("key-info")
        self.assertNotIn("key", result)
        self.assertEqual(result["userID"], 12345)


class FileTests(LibraryFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        os.environ["ZOTERO_CACHE_DIR"] = self.temp.name
        self.file = Path(self.temp.name) / "本地 paper.pdf"
        self.file.write_bytes(b"%PDF-my-upload-data")

    def test_file_upload_uses_authorize_storage_register_without_leaking_key(self):
        result = Files(self.lib).attach("PAPER001", file=str(self.file))
        self.assertEqual(result["status"], "executed")
        storage = next(c for c in self.server.calls if urlsplit(c["url"]).netloc == "storage.zotero.test")
        self.assertNotIn("Zotero-API-Key", storage["headers"])
        self.assertEqual(storage["body"], b"PREFIX" + self.file.read_bytes() + b"SUFFIX")
        self.assertEqual(data(result["result"])["md5"], hashlib.md5(self.file.read_bytes()).hexdigest())

    def test_file_preview_performs_no_remote_writes(self):
        result = Files(Library(self.api, dry_run=True)).attach("PAPER001", file=str(self.file))
        self.assertEqual(result["status"], "dry-run")
        self.assertFalse(self.server.writes())

    def test_upload_existing_blob_skips_storage_post(self):
        self.server.exists_response = True
        Files(self.lib).attach("PAPER001", file=str(self.file))
        self.assertFalse(any(urlsplit(c["url"]).netloc == "storage.zotero.test" for c in self.server.calls))

    def test_upload_failure_reports_created_attachment_for_recovery(self):
        self.server.storage_status = 500
        with self.assertRaises(ZoteroError) as error:
            Files(self.lib).attach("PAPER001", file=str(self.file))
        self.assertEqual(error.exception.code, "partial_write")
        self.assertIn(error.exception.details["attachment_key"], self.server.items)

    def test_matching_file_md5_is_idempotent(self):
        self.file.write_bytes(self.server.files["ATTACH01"])
        result = Files(self.lib).attach("PAPER001", file=str(self.file))
        self.assertEqual(result["status"], "unchanged")
        self.assertFalse(self.server.writes())

    def test_download_sanitizes_filename_and_reuses_cache(self):
        data(self.server.items["ATTACH01"])["filename"] = "../../escape.pdf"
        output = Files(self.lib).download("ATTACH01")
        path = Path(output["path"])
        self.assertTrue(path.is_relative_to(self.temp.name))
        self.assertEqual(path.name, "escape.pdf")
        before = len([c for c in self.server.calls if c["path"].endswith("/file")])
        Files(self.lib).download("ATTACH01")
        after = len([c for c in self.server.calls if c["path"].endswith("/file")])
        self.assertEqual(before, after)

    def test_download_checksum_mismatch_is_not_cached_as_success(self):
        self.server.files["ATTACH01"] = b"different data"
        with self.assertRaises(ZoteroError) as error:
            Files(self.lib).download("ATTACH01")
        self.assertEqual(error.exception.code, "file_version_conflict")

    def test_download_refreshes_a_corrupt_cache_entry(self):
        path = Path(Files(self.lib).download("ATTACH01")["path"])
        path.write_bytes(b"corrupted cache")
        Files(self.lib).download("ATTACH01")
        self.assertEqual(path.read_bytes(), self.server.files["ATTACH01"])

    def test_linked_url_creates_metadata_without_fetching_external_url(self):
        Files(self.lib).attach("PAPER001", url="https://example.org/paper.pdf")
        self.assertTrue(all(urlsplit(c["url"]).hostname == "api.zotero.org" for c in self.server.calls))

    def test_linked_file_download_is_explicitly_unavailable(self):
        data(self.server.items["ATTACH01"])["linkMode"] = "linked_file"
        with self.assertRaises(ZoteroError) as error:
            Files(self.lib).download("ATTACH01")
        self.assertEqual(error.exception.code, "file_not_stored")


class TransportTests(unittest.TestCase):
    def test_cross_origin_file_redirect_drops_credentials(self):
        seen = []

        class Destination(BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append(dict(self.headers))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"download bytes")

            def log_message(self, *args):
                pass

        destination = ThreadingHTTPServer(("127.0.0.1", 0), Destination)
        target = f"http://127.0.0.1:{destination.server_port}/file"

        class Origin(Destination):
            def do_GET(self):
                self.send_response(302)
                self.send_header("Location", target)
                self.end_headers()

        origin = ThreadingHTTPServer(("127.0.0.1", 0), Origin)
        for server in (origin, destination):
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
        response = Transport().request("GET", f"http://127.0.0.1:{origin.server_port}/download",
                                       headers={"Zotero-API-Key": "secret", "Authorization": "Bearer secret"})
        self.assertEqual(response.body, b"download bytes")
        self.assertFalse({k.lower() for k in seen[0]} & {"zotero-api-key", "authorization"})

    def test_backoff_and_retry_after_are_observed_only_for_reads(self):
        server = FakeZotero()
        replies = iter([Response(429, {"retry-after": "1"}, b"rate limited"), server.response([])])
        server.overrides[("GET", "/items")] = lambda call: next(replies)
        api = WebAPI(LibraryConfig("12345", api_key="test-secret"), server)
        with patch("zotero_api.time.sleep") as sleep:
            api.get("/items")
        sleep.assert_called_once()
        server.overrides[("POST", "/items")] = Response(429, {"retry-after": "1"}, b"rate limited")
        with self.assertRaises(ZoteroError):
            api.create([{"itemType": "book"}])
        self.assertEqual(len(server.writes()), 1)


if __name__ == "__main__":
    unittest.main()
