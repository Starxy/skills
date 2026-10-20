#!/usr/bin/env python3
"""Zotero Web API CLI. Python 3.10+, standard library only; JSON on stdout."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path

from zotero_api import LibraryConfig, WebAPI, ZoteroError
from zotero_core import Library, data, item_key, norm
from zotero_files import Files


CAPABILITIES = {
    "backend": "Zotero Web API v3", "base_url": "https://api.zotero.org", "writes_execute_by_default": True,
    "dry_run": "optional --dry-run; no separate confirmation or --execute gate",
    "api_capabilities": ["item/collection/tag/note/annotation reads and writes", "keyword/full-text keyword search",
                         "synced attachment full text", "Zotero Storage uploads/downloads", "linked URL attachments",
                         "BibTeX/CSL JSON/RIS/CSL bibliography export", "personal/group library selection",
                         "item relations", "saved-search metadata", "incremental changes and deletion logs",
                         "item templates and field/creator schemas"],
    "client_compositions": ["advanced metadata filters", "citation-key lookup in synced metadata/Extra",
                            "bulk edits", "duplicate detection/merge through metadata and item writes",
                            "per-paper note/annotation digest"],
    "excluded": ["semantic search/embeddings", "local Zotero database/API/UI", "PDF rendering/layout/text extraction",
                 "automatic annotation positioning", "third-party metadata lookup or citation intelligence",
                 "desktop-only RSS feeds", "execution of desktop saved searches", "Better BibTeX desktop RPC"],
}


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ZoteroError(message, "bad_arguments")


def load_json(value):
    if value == "-":
        return json.load(sys.stdin)
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text(encoding="utf-8-sig"))
    return json.loads(value)


def note_source(args):
    if args.file:
        return Path(args.file).read_text(encoding="utf-8-sig")
    return sys.stdin.read() if args.text == "-" else args.text or ""


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--library-id", default=argparse.SUPPRESS,
                        help="Numeric user/group ID; overrides the environment. Defaults to the API key owner's ID for user libraries.")
    common.add_argument("--library-type", choices=["user", "group"], default=argparse.SUPPRESS)
    common.add_argument("--dry-run", action="store_true", default=argparse.SUPPRESS, help="Preview remote writes without executing.")
    common.add_argument("--execute", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="Output is always JSON (accepted for compatibility).")
    parser = Parser(description=__doc__, parents=[common])
    sub = parser.add_subparsers(dest="command", required=True)

    def command(name, help_text, aliases=()):
        p = sub.add_parser(name, aliases=list(aliases), help=help_text, parents=[common])
        p.set_defaults(operation=name)
        return p

    def page_flags(p):
        p.add_argument("--limit", type=int, default=25, help="Page size, 1..100.")
        p.add_argument("--start", "--offset", type=int, default=0, dest="start")
        p.add_argument("--all", action="store_true", help="Follow every API page.")

    def read_flags(p):
        page_flags(p)
        p.add_argument("--sort")
        p.add_argument("--direction", choices=["asc", "desc"])
        p.add_argument("--detail", choices=["keys_only", "summary", "full"], default="summary")

    def search_flags(p):
        read_flags(p)
        p.add_argument("--collection")
        p.add_argument("--tag", action="append")
        p.add_argument("--item-type")
        p.add_argument("--qmode", choices=["titleCreatorYear", "everything"], default="titleCreatorYear")
        p.add_argument("--all-libraries", action="store_true")

    command("capabilities", "Report supported API operations and scope.")
    command("config", "Show configuration without revealing credentials.")
    command("key-info", "Read this API key's permissions (key value is omitted).")
    p = command("libraries", "List personal/group libraries accessible to the key.")
    p.add_argument("--user-id")
    command("library-info", "Read active library item counts and version.")

    p = command("items", "List or search library items.")
    search_flags(p)
    p.add_argument("--q")
    p.add_argument("--trash", action="store_true")
    p = command("search", "Search by keywords, tags, metadata, notes, annotations or citation key.")
    search_flags(p)
    p.add_argument("query", nargs="?", default="")
    p.add_argument("--mode", choices=["items", "tag", "advanced", "citekey", "notes", "annotations", "fulltext"], default="items")
    p.add_argument("--conditions", help="JSON array or @file.json for advanced metadata filters.")
    p.add_argument("--join", choices=["all", "any"], default="all")
    for name in ("top", "recent"):
        p = command(name, "List top-level items." if name == "top" else "List recently added items.")
        read_flags(p)
    p = command("advanced-search", "Filter all fetched metadata with explicit conditions.")
    p.add_argument("--conditions", required=True)
    p.add_argument("--join", choices=["all", "any"], default="all")
    p.add_argument("--collection")
    read_flags(p)
    p = command("item", "Get complete item metadata, or a server-generated export.", aliases=["metadata", "fetch"])
    p.add_argument("key")
    p.add_argument("--format", choices=["json", "bibtex", "csljson", "ris"], default="json")
    p = command("children", "Read every child item for one or more parent keys.")
    p.add_argument("keys", nargs="+")
    p = command("fulltext", "Read synced attachment full-text content, with completeness statistics.")
    p.add_argument("key")
    p = command("set-fulltext", "Upload supplied attachment full-text content and indexing statistics.")
    p.add_argument("key")
    p.add_argument("--fields", required=True)
    p = command("fulltext-changes", "List full-text versions changed since a library version.")
    p.add_argument("--since", required=True, type=int)

    p = command("collections", "List or search collections.")
    p.add_argument("--query")
    p = command("collection-items", "List items in a collection key/name/path.")
    p.add_argument("collection")
    read_flags(p)
    p = command("item-collections", "Resolve one item's collection memberships.")
    p.add_argument("key")
    p = command("tags", "List tags (optionally by collection/item or name query).")
    p.add_argument("--collection")
    p.add_argument("--item")
    p.add_argument("--query")
    page_flags(p)
    p = command("item-template", "Get an official Zotero new-item template.")
    p.add_argument("item_type")
    p.add_argument("--link-mode", choices=["imported_file", "imported_url", "linked_file", "linked_url"])
    p.add_argument("--annotation-type")
    p = command("schema", "Read item types, item fields, or creator types from Zotero.")
    p.add_argument("kind", choices=["itemTypes", "itemFields", "itemTypeFields", "itemTypeCreatorTypes", "creatorFields"])
    p.add_argument("--item-type")

    p = command("create-item", "Create from a template and explicit JSON fields; executes by default.")
    p.add_argument("item_type")
    p.add_argument("--fields", required=True)
    p.add_argument("--parent-id")
    p = command("import-items", "Create new items from a Zotero JSON array (no external metadata lookup).")
    p.add_argument("--data", required=True, help="JSON array, @file.json, or - for stdin.")
    p = command("update-item", "Patch a versioned item, then read the result.")
    p.add_argument("key")
    p.add_argument("--fields", required=True)
    p = command("delete-item", "Move items to trash, or permanently delete with --permanent.")
    p.add_argument("keys", nargs="+")
    p.add_argument("--permanent", action="store_true")
    p = command("set-parent", "Change an attachment/note/annotation parent, or make it top-level.")
    p.add_argument("key")
    p.add_argument("--parent", help="Omit to clear the parent.")
    p = command("create-collection", "Create a collection.")
    p.add_argument("name")
    p.add_argument("--parent")
    p = command("update-collection", "Rename a collection or change its parent.")
    p.add_argument("key")
    p.add_argument("--fields", required=True)
    p = command("delete-collection", "Delete a collection; its items remain in the library.")
    p.add_argument("key")
    for name in ("add-to-collection", "move-to-collection", "remove-from-collection"):
        p = command(name, "Change collection membership with one versioned item update.")
        p.add_argument("collection_key")
        p.add_argument("item_key")
        if name == "move-to-collection":
            p.add_argument("--from-collection")
    for name in ("add-tags", "remove-tags"):
        p = command(name, "Update tags while preserving tag types.")
        p.add_argument("key")
        p.add_argument("tags", nargs="+")
    p = command("rename-tag", "Rename a tag across every matching item.")
    p.add_argument("old_tag")
    p.add_argument("new_tag")
    p = command("batch-update", "Apply fields/tag changes to explicit item keys.")
    p.add_argument("keys", nargs="+")
    p.add_argument("--fields", default="{}")
    p.add_argument("--add-tag", action="append")
    p.add_argument("--remove-tag", action="append")

    for name in ("notes", "annotations"):
        p = command(name, "Read/search synced " + name + ".")
        p.add_argument("--parent")
        p.add_argument("--query")
    for name in ("create-note", "update-note"):
        p = command(name, "Create/update a note using plain text or explicit HTML.")
        p.add_argument("parent_key" if name == "create-note" else "key", nargs="?" if name == "create-note" else None)
        source = p.add_mutually_exclusive_group(required=True)
        source.add_argument("--text", help="Plain text; - reads stdin.")
        source.add_argument("--html", help="Already formatted note HTML.")
        source.add_argument("--file", help="Read plain text from a UTF-8 file.")
        if name == "create-note":
            p.add_argument("--heading")
            p.add_argument("--tag", action="append")
        else:
            p.add_argument("--append", action="store_true")
    for name in ("delete-note", "delete-annotation"):
        p = command(name, "Permanently delete a typed child item.")
        p.add_argument("key")
    p = command("create-annotation", "Create a native annotation from explicit Zotero position JSON.")
    p.add_argument("attachment_key")
    p.add_argument("--type", required=True, dest="annotation_type")
    p.add_argument("--position", required=True, help="JSON object or @file; supply existing Zotero coordinates.")
    p.add_argument("--text", default="")
    p.add_argument("--comment", default="")
    p.add_argument("--color", default="#ffd400")
    p.add_argument("--page-label")
    p.add_argument("--sort-index")
    p.add_argument("--tag", action="append")
    p = command("update-annotation", "Update explicit native annotation fields.")
    p.add_argument("key")
    p.add_argument("--fields", required=True)
    p = command("synthesize", "Group source notes/annotations per paper; no model or external service.")
    p.add_argument("--keys", nargs="+")
    p.add_argument("--collection")
    p.add_argument("--tag")

    p = command("attach", "Upload a file to Zotero Storage, or create a linked URL attachment.")
    p.add_argument("--parent")
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--file")
    source.add_argument("--url")
    p.add_argument("--title")
    p = command("download", "Download a stored attachment using its key.")
    p.add_argument("key")
    p.add_argument("--out")
    p = command("export", "Export through Zotero's bibliography/translation formats.")
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--keys", nargs="+")
    source.add_argument("--collection")
    p.add_argument("--format", default="bibtex", choices=["bibtex", "biblatex", "csljson", "ris", "bib", "refer"])
    p.add_argument("--style", default="apa")
    p.add_argument("--locale", default="en-US")
    p.add_argument("--out")
    p = command("related", "Read stored item relations.")
    p.add_argument("key")
    for name in ("add-relation", "remove-relation"):
        p = command(name, "Update a bidirectional stored item relation.")
        p.add_argument("first")
        p.add_argument("second")
        p.add_argument("--predicate", default="dc:relation")
    p = command("find-duplicates", "Compare library metadata by DOI or similar title (client-side).")
    p.add_argument("--threshold", type=float, default=0.93)
    page_flags(p)
    p = command("merge-duplicates", "Merge metadata/children via item writes and trash duplicate parents.")
    p.add_argument("keep")
    p.add_argument("duplicates", nargs="+")

    p = command("saved-searches", "Manage saved-search definitions; does not execute desktop searches.")
    p.add_argument("action", choices=["list", "get", "create", "update", "delete"], nargs="?", default="list")
    p.add_argument("--key")
    p.add_argument("--name")
    p.add_argument("--conditions")
    p.add_argument("--fields")
    p = command("changes", "Read changed object versions and deletion logs.", aliases=["sync"])
    p.add_argument("--since", type=int, required=True)
    return parser


def dispatch(args, api=None):
    op = args.operation
    if op == "capabilities":
        return CAPABILITIES
    config = LibraryConfig.from_env(getattr(args, "library_id", None), getattr(args, "library_type", None))
    api = api or WebAPI(config)
    lib = Library(api, dry_run=getattr(args, "dry_run", False))
    if op == "config":
        return {"library_id": config.library_id, "library_type": config.library_type,
                "api_key_configured": bool(config.api_key), "api_base": config.api_base,
                "cache_dir": str(config.cache_dir), "writes_execute_by_default": True}
    if op == "key-info":
        if not config.api_key:
            raise ZoteroError("Set ZOTERO_API_KEY to inspect its permissions.", "authentication")
        info = api.request("GET", "/keys/" + config.api_key, absolute=True)
        return {k: v for k, v in info.items() if k not in {"key", "secret"}}
    if op == "libraries":
        return lib.libraries(args.user_id)
    if op == "library-info":
        page = api.page(limit=1)
        return {"library_id": config.library_id, "library_type": config.library_type,
                "item_count": page["total"], "version": api.last_headers.get("last-modified-version")}
    if op in {"items", "search"}:
        if args.all_libraries:
            if args.collection:
                raise ZoteroError("A collection is scoped to one library; omit --all-libraries.", "bad_arguments")
            results, failures = [], []
            for target in lib.libraries()["libraries"]:
                clone = argparse.Namespace(**vars(args))
                clone.all_libraries = False
                clone.library_id, clone.library_type = target["id"], target["type"]
                try:
                    results.append({"library": target, "data": dispatch(clone, WebAPI(
                        LibraryConfig(target["id"], target["type"], config.api_key), api.transport))})
                except ZoteroError as exc:
                    failures.append({"library": target, "code": exc.code, "message": str(exc)})
            return {"libraries": results, "failures": failures, "complete": not failures}
        if op == "search":
            if args.mode == "advanced":
                if not args.conditions:
                    raise ZoteroError("Advanced search needs --conditions.", "bad_arguments")
                return lib.advanced_search(load_json(args.conditions), join=args.join, collection=args.collection,
                                           limit=None if args.all else args.limit, start=args.start, detail=args.detail,
                                           sort=args.sort, direction=args.direction, tags=args.tag, item_type=args.item_type)
            if args.mode in {"citekey", "notes", "annotations"}:
                if args.collection or args.tag or args.item_type:
                    raise ZoteroError("This search mode does not accept collection/tag/item-type filters. "
                                      "Use notes/annotations --parent for a parent scope.", "bad_arguments")
                raw = (lib.citation_key_search(args.query) if args.mode == "citekey" else
                       lib.notes(query=args.query) if args.mode == "notes" else lib.annotations(query=args.query))
                return paginate_records(raw["items"], args)
        return lib.list_items(collection=args.collection, query=args.query if op == "search" and args.mode != "tag"
                              else args.q if op == "items" else None,
                              tags=(args.tag or []) + (args.query.split(",") if op == "search" and args.mode == "tag" and args.query else []),
                              item_type=args.item_type, limit=args.limit, start=args.start, all_items=args.all,
                              sort=args.sort, direction=args.direction, detail=args.detail,
                              trash=getattr(args, "trash", False),
                              qmode="everything" if op == "search" and args.mode == "fulltext" else args.qmode)
    if op in {"top", "recent", "collection-items"}:
        return lib.list_items(collection=getattr(args, "collection", None), limit=args.limit, start=args.start,
                              all_items=args.all, top=op == "top", detail=args.detail,
                              sort="dateAdded" if op == "recent" else args.sort,
                              direction="desc" if op == "recent" else args.direction)
    if op == "advanced-search":
        return lib.advanced_search(load_json(args.conditions), join=args.join, collection=args.collection,
                                   limit=None if args.all else args.limit, start=args.start, detail=args.detail,
                                   sort=args.sort, direction=args.direction)
    if op == "item":
        return api.item(item_key(args.key)) if args.format == "json" else lib.export(keys=[args.key], fmt=args.format)
    if op == "children":
        return {"parents": [{"key": k, "children": api.children(item_key(k))} for k in args.keys]}
    if op == "fulltext":
        return lib.fulltext(args.key)
    if op == "set-fulltext":
        return lib.set_fulltext(args.key, load_json(args.fields))
    if op == "fulltext-changes":
        if args.since < 0:
            raise ZoteroError("since must be nonnegative.", "bad_arguments")
        return {"versions": api.get("/fulltext", since=args.since)}
    if op == "collections":
        return lib.collections(args.query)
    if op == "item-collections":
        return lib.item_collections(args.key)
    if op == "tags":
        if args.item and args.collection:
            raise ZoteroError("Choose an item or a collection, not both.", "bad_arguments")
        path = f"/items/{item_key(args.item)}/tags" if args.item else f"/collections/{lib.resolve_collection(args.collection)}/tags" if args.collection else "/tags"
        if args.all:
            values = api.all(path, q=args.query)
            return {"items": values, "count": len(values), "next_start": None}
        return api.page(path, q=args.query, limit=args.limit, start=args.start)
    if op == "item-template":
        extra = {k: v for k, v in {"linkMode": args.link_mode, "annotationType": args.annotation_type}.items() if v}
        return api.template(args.item_type, **extra)
    if op == "schema":
        if args.kind.startswith("itemType") and args.kind != "itemTypes" and not args.item_type:
            raise ZoteroError("This schema endpoint needs --item-type.", "bad_arguments")
        return api.request("GET", "/" + args.kind, params={"itemType": args.item_type}, absolute=True)
    if op == "create-item":
        return lib.create_item(args.item_type, load_json(args.fields), args.parent_id)
    if op == "import-items":
        return lib.import_items(load_json(args.data))
    if op == "update-item":
        return lib.update_item(args.key, load_json(args.fields))
    if op == "delete-item":
        return lib.delete_items(args.keys, args.permanent)
    if op == "set-parent":
        return lib.set_parent(args.key, args.parent)
    if op == "create-collection":
        return lib.create_collection(args.name, args.parent)
    if op == "update-collection":
        return lib.update_collection(args.key, load_json(args.fields))
    if op == "delete-collection":
        return lib.delete_collection(args.key)
    if op in {"add-to-collection", "move-to-collection", "remove-from-collection"}:
        return lib.membership([args.item_key], add=[] if op == "remove-from-collection" else [args.collection_key],
                              remove=[args.collection_key] if op == "remove-from-collection" else [],
                              move=op == "move-to-collection", source=getattr(args, "from_collection", None))
    if op in {"add-tags", "remove-tags"}:
        return lib.change_tags([args.key], add=args.tags if op == "add-tags" else None,
                               remove=args.tags if op == "remove-tags" else None)
    if op == "rename-tag":
        return lib.rename_tag(args.old_tag, args.new_tag)
    if op == "batch-update":
        return lib.batch_update(args.keys, fields=load_json(args.fields), add_tags=args.add_tag, remove_tags=args.remove_tag)
    if op == "notes":
        return lib.notes(args.parent, args.query)
    if op == "annotations":
        return lib.annotations(args.parent, args.query)
    if op == "create-note":
        return lib.create_note(args.parent_key, text=note_source(args), note_html=args.html, heading=args.heading, tags=args.tag)
    if op == "update-note":
        return lib.update_note(args.key, text=note_source(args), note_html=args.html, append=args.append)
    if op in {"delete-note", "delete-annotation"}:
        return lib.delete_typed(args.key, "note" if op == "delete-note" else "annotation")
    if op == "create-annotation":
        return lib.create_annotation(args.attachment_key, args.annotation_type, load_json(args.position), text=args.text,
                                     comment=args.comment, color=args.color, page_label=args.page_label,
                                     sort_index=args.sort_index, tags=args.tag)
    if op == "update-annotation":
        return lib.update_annotation(args.key, load_json(args.fields))
    if op == "synthesize":
        return lib.synthesize(args.keys, args.collection, args.tag)
    if op == "attach":
        return Files(lib).attach(args.parent, args.file, args.url, args.title)
    if op == "download":
        return Files(lib).download(args.key, args.out)
    if op == "export":
        result = lib.export(keys=args.keys, collection=args.collection, fmt=args.format, style=args.style, locale=args.locale)
        if args.out:
            path = Path(args.out).expanduser().resolve()
            content = result.get("text") or json.dumps(result.get("items"), ensure_ascii=False, indent=2)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return {"format": args.format, "path": str(path), "bytes": path.stat().st_size}
        return result
    if op == "related":
        return lib.related(args.key)
    if op in {"add-relation", "remove-relation"}:
        return lib.relation(args.first, args.second, remove=op == "remove-relation", predicate=args.predicate)
    if op == "find-duplicates":
        return lib.find_duplicates(threshold=args.threshold, limit=None if args.all else args.limit, start=args.start)
    if op == "merge-duplicates":
        return lib.merge_duplicates(args.keep, args.duplicates)
    if op == "saved-searches":
        return lib.saved_searches(args.action, args.key, args.name, load_json(args.conditions) if args.conditions else None,
                                  load_json(args.fields) if args.fields else None)
    if op == "changes":
        return lib.changes(args.since)
    raise ZoteroError("Unsupported command.", "bad_arguments")


def paginate_records(records, args):
    if not 1 <= args.limit <= 100 or args.start < 0:
        raise ZoteroError("limit must be 1..100 and start must be nonnegative.", "bad_arguments")
    if args.sort:
        records.sort(key=lambda r: norm(data(r).get(args.sort, "")), reverse=args.direction == "desc")
    selected = records[args.start:] if args.all else records[args.start:args.start + args.limit]
    return {"items": selected, "count": len(selected), "total": len(records),
            "next_start": args.start + args.limit if not args.all and args.start + args.limit < len(records) else None}


def main(argv=None):
    command = None
    try:
        args = build_parser().parse_args(argv)
        command = args.operation
        with contextlib.redirect_stdout(sys.stderr):
            result = dispatch(args)
        output, status = {"ok": True, "command": command, "schema": 1, "data": result}, 0
    except ZoteroError as exc:
        output = {"ok": False, "command": command, "schema": 1,
                  "error": {"code": exc.code, "message": str(exc), "details": exc.details}}
        status = 1
    except (ValueError, OSError, UnicodeError) as exc:
        output = {"ok": False, "command": command, "schema": 1,
                  "error": {"code": "invalid_input", "message": str(exc)}}
        status = 1
    rendered = json.dumps(output, ensure_ascii=False, indent=2)
    secret = os.environ.get("ZOTERO_API_KEY")
    if secret:
        rendered = rendered.replace(secret, "[redacted]")
    # Windows terminals can use a legacy code page even when the JSON contains Unicode.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(rendered)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
