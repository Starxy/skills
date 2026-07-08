import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


SCRIPT = Path(__file__).with_name("zotero_library.py")


def load_module():
    spec = importlib.util.spec_from_file_location("zotero_library", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["zotero_library"] = module
    spec.loader.exec_module(module)
    return module


class ZoteroLibraryTests(unittest.TestCase):
    def setUp(self):
        sys.modules.pop("zotero_library", None)

    def test_build_zotero_uses_environment_credentials(self):
        fake_zotero = MagicMock()
        fake_module = types.SimpleNamespace(Zotero=fake_zotero)

        with patch.dict(sys.modules, {"pyzotero": fake_module}):
            module = load_module()
            with patch.dict(
                os.environ,
                {
                    "ZOTERO_LIBRARY_ID": "12345",
                    "ZOTERO_LIBRARY_TYPE": "group",
                    "ZOTERO_API_KEY": "secret",
                },
                clear=True,
            ):
                config = module.LibraryConfig.from_env()
                module.build_zotero(config)

        fake_zotero.assert_called_once_with("12345", "group", "secret")

    def test_write_operations_are_dry_run_by_default(self):
        module = load_module()
        zot = MagicMock()
        zot.item_template.return_value = {
            "itemType": "journalArticle",
            "title": "",
            "creators": [],
            "tags": [],
        }
        zot.check_items.side_effect = lambda items: items

        result = module.create_item(
            zot,
            "journalArticle",
            {"title": "A reproducible paper"},
            execute=False,
        )

        zot.create_items.assert_not_called()
        self.assertEqual(result["status"], "dry-run")
        self.assertEqual(result["items"][0]["title"], "A reproducible paper")

    def test_create_item_checks_template_before_execute(self):
        module = load_module()
        zot = MagicMock()
        zot.item_template.return_value = {
            "itemType": "book",
            "title": "",
            "creators": [],
            "tags": [],
        }
        zot.check_items.side_effect = lambda items: items
        zot.create_items.return_value = {"success": {"0": "ABC123"}, "failed": {}, "unchanged": {}}

        result = module.create_item(zot, "book", {"title": "Checked First"}, execute=True)

        zot.item_template.assert_called_once_with("book")
        zot.check_items.assert_called_once()
        zot.create_items.assert_called_once()
        self.assertEqual(result["success"]["0"], "ABC123")

    def test_delete_item_fetches_versioned_item_before_execute(self):
        module = load_module()
        zot = MagicMock()
        zot.item.return_value = {"key": "ABC123", "version": 42, "data": {"title": "Delete me"}}
        zot.delete_item.return_value = True

        result = module.delete_item(zot, ["ABC123"], execute=True)

        zot.item.assert_called_once_with("ABC123")
        zot.delete_item.assert_called_once_with([zot.item.return_value])
        self.assertTrue(result)

    def test_update_collection_patches_retrieved_collection_data(self):
        module = load_module()
        zot = MagicMock()
        zot.collection.return_value = {
            "key": "COLL123",
            "data": {"key": "COLL123", "name": "Old"},
            "version": 9,
        }

        result = module.update_collection(zot, "COLL123", {"name": "New"}, execute=False)

        zot.update_collection.assert_not_called()
        self.assertEqual(result["collection"]["data"]["name"], "New")

    def test_create_note_formats_text_as_zotero_note_html(self):
        module = load_module()
        zot = MagicMock()
        zot.item_template.return_value = {"itemType": "note", "note": ""}
        zot.check_items.side_effect = lambda items: items

        result = module.create_note(
            zot,
            "ITEM123",
            heading="阅读笔记",
            text="重点\n- 方法有效\n- 需要复现",
            execute=False,
        )

        note_html = result["items"][0]["note"]
        self.assertIn("<h2>阅读笔记</h2>", note_html)
        self.assertIn("<ul>", note_html)
        self.assertIn("<li>方法有效</li>", note_html)
        zot.create_items.assert_not_called()

    def test_move_item_to_collection_removes_existing_collections_and_adds_target(self):
        module = load_module()
        zot = MagicMock()
        item = {"key": "ITEM123", "data": {"collections": ["OLD1", "OLD2"]}, "version": 3}
        zot.item.return_value = item

        result = module.move_item_to_collection(zot, "ITEM123", "NEW1", execute=True)

        zot.addto_collection.assert_called_once_with("NEW1", item)
        zot.deletefrom_collection.assert_any_call("OLD1", item)
        zot.deletefrom_collection.assert_any_call("OLD2", item)
        self.assertEqual(result["removed_collections"], ["OLD1", "OLD2"])

    def test_rename_tag_fetches_old_tag_items_and_replaces_tag(self):
        module = load_module()
        zot = MagicMock()
        item = {
            "key": "ITEM123",
            "data": {"tags": [{"tag": "old"}, {"tag": "keep"}]},
            "version": 8,
        }
        zot.items.return_value = [item]
        zot.everything.side_effect = lambda page: page

        result = module.rename_tag(zot, "old", "new", execute=True)

        zot.items.assert_called_once_with(tag="old")
        zot.update_items.assert_called_once()
        self.assertEqual(item["data"]["tags"], [{"tag": "keep"}, {"tag": "new"}])
        self.assertEqual(result["updated_count"], 1)

    def test_item_collections_returns_keys_and_names(self):
        module = load_module()
        zot = MagicMock()
        zot.item.return_value = {"key": "ITEM123", "data": {"collections": ["C1", "C2"]}}
        zot.collection.side_effect = [
            {"key": "C1", "data": {"name": "Inbox"}},
            {"key": "C2", "data": {"name": "Reviewed"}},
        ]

        result = module.item_collections(zot, "ITEM123")

        self.assertEqual(
            result["collections"],
            [{"key": "C1", "name": "Inbox"}, {"key": "C2", "name": "Reviewed"}],
        )


if __name__ == "__main__":
    unittest.main()
