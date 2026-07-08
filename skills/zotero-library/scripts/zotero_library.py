#!/usr/bin/env python3
"""Small pyzotero CLI for safe Zotero library automation."""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LibraryConfig:
    library_id: str
    library_type: str
    api_key: str | None = None
    local: bool = False

    @classmethod
    def from_env(cls) -> "LibraryConfig":
        library_id = os.environ.get("ZOTERO_LIBRARY_ID")
        library_type = os.environ.get("ZOTERO_LIBRARY_TYPE", "user")
        api_key = os.environ.get("ZOTERO_API_KEY")
        local = os.environ.get("ZOTERO_LOCAL", "").lower() in {"1", "true", "yes"}

        if not library_id:
            raise SystemExit("Missing ZOTERO_LIBRARY_ID")
        if library_type not in {"user", "group"}:
            raise SystemExit("ZOTERO_LIBRARY_TYPE must be 'user' or 'group'")
        if library_type == "user" and not api_key and not local:
            raise SystemExit("Missing ZOTERO_API_KEY for user library access")
        return cls(library_id=library_id, library_type=library_type, api_key=api_key, local=local)


def build_zotero(config: LibraryConfig) -> Any:
    try:
        from pyzotero import Zotero
    except ImportError as exc:
        raise SystemExit("Install pyzotero first: uv add pyzotero or run with uv run --with pyzotero") from exc

    if config.local:
        return Zotero(config.library_id, config.library_type, config.api_key, local=True)
    return Zotero(config.library_id, config.library_type, config.api_key)


def load_json(value: str) -> Any:
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text(encoding="utf-8"))
    return json.loads(value)


def emit_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def apply_fields(target: dict[str, Any], fields: dict[str, Any]) -> dict[str, Any]:
    for key, value in fields.items():
        target[key] = value
    return target


def chunked(values: list[Any], size: int) -> list[list[Any]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def note_text_to_html(text: str, heading: str | None = None) -> str:
    parts: list[str] = []
    list_items: list[str] = []

    if heading:
        parts.append(f"<h2>{html.escape(heading)}</h2>")

    def close_list() -> None:
        if list_items:
            parts.append("<ul>" + "".join(list_items) + "</ul>")
            list_items.clear()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            close_list()
            continue
        if line.startswith("- "):
            list_items.append(f"<li>{html.escape(line[2:].strip())}</li>")
            continue
        close_list()
        parts.append(f"<p>{html.escape(line)}</p>")

    close_list()
    return "\n".join(parts) if parts else "<p></p>"


def create_note(
    zot: Any,
    parent_key: str,
    *,
    text: str | None = None,
    note_html: str | None = None,
    heading: str | None = None,
    execute: bool,
) -> Any:
    if note_html is None:
        note_html = note_text_to_html(text or "", heading)
    note = zot.item_template("note")
    note["note"] = note_html
    checked = zot.check_items([note])
    if not execute:
        return {"operation": "create-note", "status": "dry-run", "parent": parent_key, "items": checked}
    return zot.create_items(checked, parentid=parent_key)


def create_item(
    zot: Any,
    item_type: str,
    fields: dict[str, Any],
    *,
    execute: bool,
    parent_id: str | None = None,
    last_modified: int | str | None = None,
) -> Any:
    item = zot.item_template(item_type)
    apply_fields(item, fields)
    checked = zot.check_items([item])
    if not execute:
        return {"operation": "create-item", "status": "dry-run", "items": checked}
    return zot.create_items(checked, parentid=parent_id, last_modified=last_modified)


def update_item(zot: Any, key: str, fields: dict[str, Any], *, execute: bool) -> Any:
    item = zot.item(key)
    data = item.setdefault("data", {})
    apply_fields(data, fields)
    if not execute:
        return {"operation": "update-item", "status": "dry-run", "item": item}
    return zot.update_item(item)


def delete_item(zot: Any, keys: list[str], *, execute: bool) -> Any:
    items = [zot.item(key) for key in keys]
    if not execute:
        return {"operation": "delete-item", "status": "dry-run", "items": items}
    return zot.delete_item(items)


def update_collection(zot: Any, key: str, fields: dict[str, Any], *, execute: bool) -> Any:
    collection = zot.collection(key)
    target = collection.get("data", collection)
    apply_fields(target, fields)
    if not execute:
        return {"operation": "update-collection", "status": "dry-run", "collection": collection}
    return zot.update_collection(collection)


def item_collections(zot: Any, item_key: str) -> dict[str, Any]:
    item = zot.item(item_key)
    collection_keys = item.get("data", {}).get("collections", [])
    collections = []
    for key in collection_keys:
        collection = zot.collection(key)
        data = collection.get("data", collection)
        collections.append({"key": key, "name": data.get("name", "")})
    return {"item": item_key, "collections": collections}


def move_item_to_collection(
    zot: Any,
    item_key: str,
    target_collection: str,
    *,
    execute: bool,
    source_collection: str | None = None,
) -> Any:
    item = zot.item(item_key)
    current = item.get("data", {}).get("collections", [])
    if source_collection:
        remove_keys = [source_collection] if source_collection in current else []
    else:
        remove_keys = [key for key in current if key != target_collection]

    plan = {
        "operation": "move-item-to-collection",
        "status": "dry-run" if not execute else "executed",
        "item": item,
        "target_collection": target_collection,
        "removed_collections": remove_keys,
    }
    if not execute:
        return plan

    if target_collection not in current:
        zot.addto_collection(target_collection, item)
    for collection_key in remove_keys:
        zot.deletefrom_collection(collection_key, item)
    return plan


def replace_tag(tags: list[dict[str, Any]], old_tag: str, new_tag: str) -> list[dict[str, Any]]:
    replacement = {"tag": new_tag}
    result = [tag for tag in tags if tag.get("tag") != old_tag]
    if not any(tag.get("tag") == new_tag for tag in result):
        result.append(replacement)
    return result


def rename_tag(zot: Any, old_tag: str, new_tag: str, *, execute: bool) -> Any:
    page = zot.items(tag=old_tag)
    items = zot.everything(page) if hasattr(zot, "everything") else page
    updated = []
    for item in items:
        data = item.setdefault("data", {})
        tags = data.get("tags", [])
        if any(tag.get("tag") == old_tag for tag in tags):
            data["tags"] = replace_tag(tags, old_tag, new_tag)
            updated.append(item)

    plan = {
        "operation": "rename-tag",
        "status": "dry-run" if not execute else "executed",
        "old_tag": old_tag,
        "new_tag": new_tag,
        "updated_count": len(updated),
        "items": updated,
    }
    if not execute:
        return plan

    for batch in chunked(updated, 50):
        zot.update_items(batch)
    return plan


def list_items(zot: Any, args: argparse.Namespace) -> Any:
    params = {
        "limit": args.limit,
        "start": args.start,
        "sort": args.sort,
        "direction": args.direction,
    }
    params = {key: value for key, value in params.items() if value is not None}
    if args.q:
        params["q"] = args.q
    if args.qmode:
        params["qmode"] = args.qmode
    if args.tag:
        params["tag"] = args.tag
    if args.item_type:
        params["itemType"] = args.item_type
    return zot.items(**params)


def collection_payload(name: str, parent: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": name}
    if parent:
        payload["parentCollection"] = parent
    return payload


def dispatch(args: argparse.Namespace) -> Any:
    zot = build_zotero(LibraryConfig.from_env())

    if args.command == "items":
        return list_items(zot, args)
    if args.command == "top":
        return zot.top(limit=args.limit)
    if args.command == "item":
        return zot.item(args.key)
    if args.command == "item-collections":
        return item_collections(zot, args.key)
    if args.command == "children":
        return zot.children(args.key)
    if args.command == "collections":
        return zot.collections()
    if args.command == "collection-items":
        return zot.collection_items(args.collection)
    if args.command == "tags":
        return zot.tags()
    if args.command == "item-template":
        return zot.item_template(args.item_type)
    if args.command == "create-item":
        return create_item(
            zot,
            args.item_type,
            load_json(args.fields),
            execute=args.execute,
            parent_id=args.parent_id,
            last_modified=args.last_modified,
        )
    if args.command == "create-note":
        note_text = args.text
        if args.file:
            note_text = Path(args.file).read_text(encoding="utf-8")
        return create_note(
            zot,
            args.parent_key,
            text=note_text,
            note_html=args.html,
            heading=args.heading,
            execute=args.execute,
        )
    if args.command == "update-item":
        return update_item(zot, args.key, load_json(args.fields), execute=args.execute)
    if args.command == "delete-item":
        return delete_item(zot, args.keys, execute=args.execute)
    if args.command == "create-collection":
        payload = collection_payload(args.name, args.parent)
        if not args.execute:
            return {"operation": "create-collection", "status": "dry-run", "collections": [payload]}
        return zot.create_collections([payload], last_modified=args.last_modified)
    if args.command == "delete-collection":
        collection = zot.collection(args.key)
        if not args.execute:
            return {"operation": "delete-collection", "status": "dry-run", "collection": collection}
        return zot.delete_collection(collection, last_modified=args.last_modified)
    if args.command == "update-collection":
        return update_collection(zot, args.key, load_json(args.fields), execute=args.execute)
    if args.command == "add-to-collection":
        item = zot.item(args.item_key)
        if not args.execute:
            return {
                "operation": "add-to-collection",
                "status": "dry-run",
                "collection": args.collection_key,
                "item": item,
            }
        return zot.addto_collection(args.collection_key, item)
    if args.command == "move-to-collection":
        return move_item_to_collection(
            zot,
            args.item_key,
            args.collection_key,
            execute=args.execute,
            source_collection=args.from_collection,
        )
    if args.command == "remove-from-collection":
        item = zot.item(args.item_key)
        if not args.execute:
            return {
                "operation": "remove-from-collection",
                "status": "dry-run",
                "collection": args.collection_key,
                "item": item,
            }
        return zot.deletefrom_collection(args.collection_key, item)
    if args.command == "add-tags":
        item = zot.item(args.key)
        if not args.execute:
            return {"operation": "add-tags", "status": "dry-run", "item": item, "tags": args.tags}
        return zot.add_tags(item, *args.tags)
    if args.command == "rename-tag":
        return rename_tag(zot, args.old_tag, args.new_tag, execute=args.execute)
    raise SystemExit(f"Unsupported command: {args.command}")


def add_common_read_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--limit", type=int)
    parser.add_argument("--start", type=int)
    parser.add_argument("--sort")
    parser.add_argument("--direction", choices=["asc", "desc"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe pyzotero helper for Zotero library CRUD.")
    sub = parser.add_subparsers(dest="command", required=True)

    items = sub.add_parser("items", help="Search or list library items.")
    add_common_read_flags(items)
    items.add_argument("--q")
    items.add_argument("--qmode", choices=["titleCreatorYear", "everything"])
    items.add_argument("--tag", action="append")
    items.add_argument("--item-type")

    top = sub.add_parser("top", help="List top-level items.")
    top.add_argument("--limit", type=int, default=10)

    item = sub.add_parser("item", help="Read one item by key.")
    item.add_argument("key")

    item_collections_parser = sub.add_parser("item-collections", help="Read one item's collection keys and names.")
    item_collections_parser.add_argument("key")

    children = sub.add_parser("children", help="Read child items for one item key.")
    children.add_argument("key")

    sub.add_parser("collections", help="List collections.")

    collection_items = sub.add_parser("collection-items", help="List items in a collection.")
    collection_items.add_argument("collection")

    sub.add_parser("tags", help="List tags.")

    template = sub.add_parser("item-template", help="Print a Zotero item template.")
    template.add_argument("item_type")

    create = sub.add_parser("create-item", help="Create an item from a Zotero template.")
    create.add_argument("item_type")
    create.add_argument("--fields", required=True, help="JSON object or @path.json")
    create.add_argument("--parent-id")
    create.add_argument("--last-modified")
    create.add_argument("--execute", action="store_true")

    create_note_parser = sub.add_parser("create-note", help="Create a child note with Zotero-readable HTML.")
    create_note_parser.add_argument("parent_key")
    note_source = create_note_parser.add_mutually_exclusive_group(required=True)
    note_source.add_argument("--text")
    note_source.add_argument("--html")
    note_source.add_argument("--file")
    create_note_parser.add_argument("--heading")
    create_note_parser.add_argument("--execute", action="store_true")

    update = sub.add_parser("update-item", help="Fetch then update an item.")
    update.add_argument("key")
    update.add_argument("--fields", required=True, help="JSON object or @path.json")
    update.add_argument("--execute", action="store_true")

    delete = sub.add_parser("delete-item", help="Fetch versioned item(s), then delete.")
    delete.add_argument("keys", nargs="+")
    delete.add_argument("--execute", action="store_true")

    create_collection = sub.add_parser("create-collection", help="Create a collection.")
    create_collection.add_argument("name")
    create_collection.add_argument("--parent")
    create_collection.add_argument("--last-modified")
    create_collection.add_argument("--execute", action="store_true")

    delete_collection = sub.add_parser("delete-collection", help="Fetch then delete a collection.")
    delete_collection.add_argument("key")
    delete_collection.add_argument("--last-modified")
    delete_collection.add_argument("--execute", action="store_true")

    update_collection_parser = sub.add_parser("update-collection", help="Fetch then update a collection.")
    update_collection_parser.add_argument("key")
    update_collection_parser.add_argument("--fields", required=True, help="JSON object or @path.json")
    update_collection_parser.add_argument("--execute", action="store_true")

    add_to_collection = sub.add_parser("add-to-collection", help="Fetch an item, then add it to a collection.")
    add_to_collection.add_argument("collection_key")
    add_to_collection.add_argument("item_key")
    add_to_collection.add_argument("--execute", action="store_true")

    move_to_collection = sub.add_parser(
        "move-to-collection",
        help="Move an item to a target collection, removing existing collection memberships by default.",
    )
    move_to_collection.add_argument("collection_key")
    move_to_collection.add_argument("item_key")
    move_to_collection.add_argument("--from-collection")
    move_to_collection.add_argument("--execute", action="store_true")

    remove_from_collection = sub.add_parser(
        "remove-from-collection",
        help="Fetch an item, then remove it from a collection.",
    )
    remove_from_collection.add_argument("collection_key")
    remove_from_collection.add_argument("item_key")
    remove_from_collection.add_argument("--execute", action="store_true")

    add_tags = sub.add_parser("add-tags", help="Fetch an item, then add tags.")
    add_tags.add_argument("key")
    add_tags.add_argument("tags", nargs="+")
    add_tags.add_argument("--execute", action="store_true")

    rename_tag_parser = sub.add_parser("rename-tag", help="Rename one tag across the whole library.")
    rename_tag_parser.add_argument("old_tag")
    rename_tag_parser.add_argument("new_tag")
    rename_tag_parser.add_argument("--execute", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    emit_json(dispatch(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
