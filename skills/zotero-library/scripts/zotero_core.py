"""Library operations shared by the CLI, PDF, import and index workflows."""

from __future__ import annotations

import copy
import html
import json
import re
import unicodedata
from difflib import SequenceMatcher
from html.parser import HTMLParser
from typing import Any

from zotero_api import WebAPI, ZoteroError


def item_key(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z0-9]{8}", value):
        raise ZoteroError(f"Invalid Zotero key: {value!r}; expected eight uppercase letters/digits.", "bad_key")
    return value


def data(record: dict) -> dict:
    return record.get("data", record)


def norm(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFKD", str(value)).casefold().split())


def normalize_doi(value: str) -> str:
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value.strip(), flags=re.I).lower()


def merge_tags(*groups) -> list[dict]:
    result: dict[str, dict] = {}
    for group in groups:
        for tag in group:
            tag = {"tag": tag} if isinstance(tag, str) else copy.deepcopy(tag)
            name = tag.get("tag", "")
            if name and (name not in result or tag.get("type", 0) == 0):
                result[name] = tag
    return list(result.values())


class _PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, text):
        self.parts.append(text)


def plain_text(text: str) -> str:
    parser = _PlainText()
    parser.feed(text)
    return " ".join(parser.parts)


def note_text_to_html(text: str, heading: str | None = None) -> str:
    """Escape plain text and retain basic headings, paragraphs and bullet lists."""
    parts, pending = [], []

    def flush():
        if pending:
            parts.append("<ul>" + "".join(pending) + "</ul>")
            pending.clear()

    for line in text.splitlines():
        if line.strip().startswith("- "):
            pending.append("<li>" + html.escape(line.strip()[2:]) + "</li>")
        else:
            flush()
            if match := re.match(r"^(#{1,6})\s+(.+)$", line):
                level = len(match[1])
                parts.append(f"<h{level}>{html.escape(match[2])}</h{level}>")
            elif line.strip():
                parts.append("<p>" + html.escape(line) + "</p>")
    flush()
    body = "\n".join(parts) or "<p></p>"
    return (f"<h2>{html.escape(heading)}</h2>\n" if heading else "") + body


def project(record: dict, detail="summary") -> dict:
    d, key = data(record), record.get("key", data(record).get("key"))
    if detail == "full":
        return record
    if detail == "keys_only":
        return {"key": key, "title": d.get("title", ""), "itemType": d.get("itemType")}
    return {"key": key, **{k: d[k] for k in ("itemType", "title", "creators", "date", "DOI", "url",
                                             "abstractNote", "tags", "collections") if k in d}}


class Library:
    def __init__(self, api: WebAPI, dry_run: bool = False):
        self.api, self.dry_run = api, dry_run
        self._catalog = None

    def _write(self, operation: str, plan: Any, fn):
        if self.dry_run:
            return {"operation": operation, "status": "dry-run", "changes": plan}
        return {"operation": operation, "status": "executed", "result": fn()}

    def catalog(self):
        if self._catalog is None:
            self._catalog = self.api.all("/items/top")
        return self._catalog

    def list_items(self, *, collection=None, query=None, tags=None, item_type=None,
                   limit=25, start=0, all_items=False, top=False, sort=None, direction=None,
                   detail="summary", trash=False, qmode=None):
        path = "/items/trash" if trash else "/items/top" if top else "/items"
        if collection:
            path = f"/collections/{self.resolve_collection(collection)}/items"
        params = {"q": query, "tag": tags, "itemType": item_type, "sort": sort, "direction": direction,
                  "qmode": qmode}
        if all_items:
            records = self.api.all(path, **params)
            page = {"items": records, "count": len(records), "total": len(records), "next_start": None}
        else:
            page = self.api.page(path, limit=limit, start=start, **params)
        page["items"] = [project(r, detail) for r in page["items"]]
        return page

    def advanced_search(self, conditions: list[dict], *, join="all", collection=None,
                        limit=25, start=0, detail="summary", sort=None, direction=None, tags=None, item_type=None):
        if start < 0 or (limit is not None and not 1 <= limit <= 100):
            raise ZoteroError("limit must be 1..100 and start must be nonnegative.", "bad_arguments")
        if not isinstance(conditions, list) or not conditions:
            raise ZoteroError("conditions must be a nonempty JSON array.", "bad_conditions")
        supported = {"contains", "notContains", "is", "isNot", "beginsWith", "isBefore", "isAfter", "exists"}
        for c in conditions:
            if (not isinstance(c, dict) or not c.get("field") or c.get("operation", "contains") not in supported
                    or (c.get("operation") != "exists" and "value" not in c)):
                raise ZoteroError("Each condition needs field, operation and value.", "bad_conditions")

        def matches(record, condition):
            d, field = data(record), condition["field"]
            value = d.get(field, "")
            if field in {"creator", "creators", "author"}:
                value = " ".join(" ".join(str(v) for k, v in person.items() if k != "creatorType")
                                 for person in d.get("creators", []))
            elif field in {"tag", "tags"}:
                value = [t["tag"] for t in d.get("tags", [])]
            elif field == "year":
                value = str(d.get("date", ""))[:4]
            values = [norm(v) for v in value] if isinstance(value, list) else [norm(value)]
            target, op = norm(condition.get("value", "")), condition.get("operation", "contains")
            if op == "exists":
                return any(values)
            if op == "is":
                return target in values
            if op == "isNot":
                return target not in values
            if op == "contains":
                return any(target in v for v in values)
            if op == "notContains":
                return all(target not in v for v in values)
            if op == "beginsWith":
                return any(v.startswith(target) for v in values)
            return any(v < target if op == "isBefore" else v > target for v in values)

        path = f"/collections/{self.resolve_collection(collection)}/items" if collection else "/items"
        records = self.api.all(path, tag=tags, itemType=item_type)
        combine = all if join == "all" else any
        found = [r for r in records if combine(matches(r, c) for c in conditions)]
        if sort:
            found.sort(key=lambda r: norm(data(r).get(sort, "")), reverse=direction == "desc")
        selected = found[start:] if limit is None else found[start:start + limit]
        return {"items": [project(r, detail) for r in selected], "count": len(selected),
                "total": len(found), "scanned": len(records),
                "next_start": start + limit if limit and start + limit < len(found) else None}

    def citation_key_search(self, citekey: str):
        found = []
        for record in self.catalog():
            d = data(record)
            if d.get("citationKey") == citekey or re.search(
                    r"^Citation Key:\s*" + re.escape(citekey) + r"\s*$", d.get("extra", ""), re.M):
                found.append(record)
        return {"items": found, "count": len(found), "source": "synced citationKey/Extra; no desktop BBT RPC"}

    def create_item(self, kind: str, fields: dict, parent=None):
        if not isinstance(fields, dict) or set(fields) & {"key", "version"}:
            raise ZoteroError("New-item fields must be a JSON object without key/version.", "bad_arguments")
        payload = self.api.template(kind)
        payload.update(copy.deepcopy(fields))
        payload["itemType"] = kind
        if parent:
            self.api.item(item_key(parent))
            payload["parentItem"] = parent
        return self._write("create-item", [payload], lambda: self.api.create([payload]))

    def import_items(self, records):
        if not isinstance(records, list) or not records or any(not isinstance(r, dict) or
                not r.get("itemType") or "version" in r or "key" in r for r in records):
            raise ZoteroError("Import needs an array of new Zotero JSON records with itemType and no key/version.",
                              "bad_arguments")
        return self._write("import-items", records, lambda: self.api.create(records))

    def update_item(self, key: str, fields: dict):
        if not isinstance(fields, dict) or set(fields) & {"key", "version", "itemType"}:
            raise ZoteroError("fields must be an object without key/version/itemType.", "bad_arguments")
        record = self.api.item(item_key(key))
        return self._write("update-item", {"key": key, "version": record.get("version"), "fields": fields},
                           lambda: self.api.patch(record, fields))

    def delete_items(self, keys: list[str], permanent=False):
        records = [self.api.item(item_key(k)) for k in keys]
        return self._write("delete-item", {"keys": keys, "permanent": permanent},
                           lambda: self._apply_records(records, lambda r: self.api.delete(r) if permanent
                                                      else self.api.patch(r, {"deleted": 1})))

    @staticmethod
    def _apply_records(records, fn):
        done = []
        for record in records:
            try:
                done.append(fn(record))
            except ZoteroError as exc:
                raise ZoteroError(str(exc), "partial_write" if done else exc.code,
                                  details={"completed": done, "failed_key": record.get("key"),
                                           "cause": exc.code, "details": exc.details}) from exc
        return done

    def collections(self, query=None):
        records = self.api.all("/collections")
        if query:
            records = [r for r in records if norm(query) in norm(data(r).get("name", ""))]
        return {"collections": records, "count": len(records)}

    def resolve_collection(self, spec: str) -> str:
        records = self.api.all("/collections")
        by_key = {r["key"]: r for r in records}
        if spec in by_key:
            return spec

        def path(key, seen=None):
            seen = set(seen or ())
            if key in seen or key not in by_key:
                return ""
            seen.add(key)
            d = data(by_key[key])
            parent = d.get("parentCollection")
            return (path(parent, seen) + "/" if parent else "") + d.get("name", "")

        found = [r["key"] for r in records if (path(r["key"]) if "/" in spec
                                              else data(r).get("name")) == spec.strip("/")]
        if len(found) != 1:
            raise ZoteroError(f"Collection {spec!r} is {'ambiguous' if found else 'not found'}.",
                              "ambiguous_collection" if found else "collection_not_found", details={"matches": found})
        return found[0]

    def create_collection(self, name: str, parent=None):
        if not name.strip():
            raise ZoteroError("Collection name cannot be empty.", "bad_arguments")
        payload = {"name": name, "parentCollection": self.resolve_collection(parent) if parent else False}
        return self._write("create-collection", [payload], lambda: self.api.create([payload], "/collections"))

    def update_collection(self, spec: str, fields: dict):
        if not isinstance(fields, dict) or set(fields) - {"name", "parentCollection"}:
            raise ZoteroError("Collection fields are name and parentCollection.", "bad_arguments")
        key = self.resolve_collection(spec)
        record = self.api.get(f"/collections/{key}")
        fields = copy.deepcopy(fields)
        if fields.get("parentCollection"):
            fields["parentCollection"] = self.resolve_collection(fields["parentCollection"])
            if fields["parentCollection"] == key:
                raise ZoteroError("A collection cannot be its own parent.", "bad_arguments")
        return self._write("update-collection", {"key": key, "fields": fields},
                           lambda: self.api.patch(record, fields, "/collections"))

    def delete_collection(self, spec: str):
        record = self.api.get(f"/collections/{self.resolve_collection(spec)}")
        return self._write("delete-collection", record, lambda: self.api.delete(record, "/collections"))

    def item_collections(self, key: str):
        record = self.api.item(item_key(key))
        return {"item": key, "collections": [self.api.get(f"/collections/{c}")
                                               for c in data(record).get("collections", [])]}

    def membership(self, keys: list[str], *, add=None, remove=None, move=False, source=None):
        adds = [self.resolve_collection(c) for c in (add or [])]
        removes = [self.resolve_collection(c) for c in (remove or [])]
        if source:
            removes.append(self.resolve_collection(source))
        records = [self.api.item(item_key(k)) for k in keys]
        plans = []
        for r in records:
            current = data(r).get("collections", [])
            kept = [] if move and not source else [c for c in current if c not in removes]
            plans.append({"key": r["key"], "collections": list(dict.fromkeys(kept + adds))})
        return self._write("manage-collections", plans,
                           lambda: self._apply_records(records, lambda r: self.api.patch(
                               r, {"collections": next(p["collections"] for p in plans if p["key"] == r["key"])})))

    def change_tags(self, keys: list[str], *, add=None, remove=None):
        records = [self.api.item(item_key(k)) for k in keys]
        plans = [{"key": r["key"], "tags": merge_tags(
            [t for t in data(r).get("tags", []) if t["tag"] not in (remove or [])], add or [])} for r in records]
        return self._write("tags", plans, lambda: self._apply_records(records, lambda r: self.api.patch(
            r, {"tags": next(p["tags"] for p in plans if p["key"] == r["key"])})))

    def rename_tag(self, old: str, new: str):
        if not new.strip():
            raise ZoteroError("New tag must not be empty.", "bad_arguments")
        records = [r for r in self.api.all("/items", tag=old)
                   if any(t["tag"] == old for t in data(r).get("tags", []))]
        plans = []
        for r in records:
            tags = [dict(t, tag=new) if t["tag"] == old else t for t in data(r).get("tags", [])]
            plans.append({"key": r["key"], "tags": merge_tags(tags)})
        return self._write("rename-tag", plans, lambda: self._apply_records(records, lambda r: self.api.patch(
            r, {"tags": next(p["tags"] for p in plans if p["key"] == r["key"])})))

    def notes(self, parent=None, query=None, annotations=False):
        records = self.api.children(item_key(parent)) if parent else self.api.all(
            "/items", itemType="annotation" if annotations else "note")
        kind = "annotation" if annotations else "note"
        records = [r for r in records if data(r).get("itemType") == kind]
        if query:
            records = [r for r in records if norm(query) in norm(plain_text(" ".join(
                str(data(r).get(k, "")) for k in ("note", "annotationText", "annotationComment"))))]
        return {"items": records, "count": len(records)}

    def annotations(self, parent=None, query=None):
        if not parent:
            return self.notes(query=query, annotations=True)
        record = self.api.item(item_key(parent))
        parents = [record] if data(record).get("itemType") == "attachment" else [
            c for c in self.api.children(parent) if data(c).get("itemType") == "attachment"]
        records = [a for p in parents for a in self.notes(p["key"], query=query, annotations=True)["items"]]
        return {"items": records, "count": len(records)}

    def create_annotation(self, parent, kind, position, *, text="", comment="", color="#ffd400",
                          page_label=None, sort_index=None, tags=None):
        attachment = self.api.item(item_key(parent))
        if data(attachment).get("itemType") != "attachment":
            raise ZoteroError("Annotations require an attachment parent.", "wrong_item_type")
        if not isinstance(position, dict) or not position:
            raise ZoteroError("position must be a Zotero annotationPosition JSON object.", "bad_arguments")
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            raise ZoteroError("Annotation color must use #RRGGBB.", "bad_arguments")
        payload = self.api.template("annotation", annotationType=kind)
        payload.update({"parentItem": parent, "annotationType": kind, "annotationPosition": position,
                        "annotationComment": comment, "annotationColor": color, "tags": merge_tags(tags or [])})
        if "annotationText" in payload:
            payload["annotationText"] = text
        if page_label is not None:
            payload["annotationPageLabel"] = str(page_label)
        elif isinstance(position.get("pageIndex"), int):
            payload["annotationPageLabel"] = str(position["pageIndex"] + 1)
        if sort_index:
            payload["annotationSortIndex"] = sort_index
        elif isinstance(position.get("pageIndex"), int):
            payload["annotationSortIndex"] = f"{position['pageIndex']:05d}|000000|00000"
        return self._write("create-annotation", [payload], lambda: self.api.create([payload]))

    def update_annotation(self, key, fields):
        record = self.api.item(item_key(key))
        if data(record).get("itemType") != "annotation":
            raise ZoteroError("The target is not an annotation.", "wrong_item_type")
        allowed = {"annotationText", "annotationComment", "annotationColor", "annotationPageLabel",
                   "annotationSortIndex", "annotationPosition", "tags"}
        if not isinstance(fields, dict) or set(fields) - allowed:
            raise ZoteroError("Provide only annotation fields or tags.", "bad_arguments")
        return self._write("update-annotation", {"key": key, "fields": fields},
                           lambda: self.api.patch(record, fields))

    def delete_typed(self, key, kind):
        record = self.api.item(item_key(key))
        if data(record).get("itemType") != kind:
            raise ZoteroError(f"The target is not a {kind}.", "wrong_item_type")
        return self._write("delete-" + kind, {"key": key, "permanent": True}, lambda: self.api.delete(record))

    def fulltext(self, key):
        record = self.api.item(item_key(key))
        if data(record).get("itemType") == "attachment":
            attachments = [record]
        else:
            attachments = [r for r in self.api.children(key) if data(r).get("itemType") == "attachment"]
        result = []
        for attachment in attachments:
            akey = attachment["key"]
            try:
                content = self.api.get(f"/items/{akey}/fulltext")
                complete = ((content.get("indexedPages", 0) >= content["totalPages"]) if content.get("totalPages")
                            else (content.get("indexedChars", 0) >= content["totalChars"]) if content.get("totalChars") else None)
                result.append({"key": akey, "available": True, "complete": complete,
                               "fulltext_version": self.api.last_headers.get("last-modified-version"), **content})
            except ZoteroError as exc:
                if exc.code != "not_found":
                    raise
                result.append({"key": akey, "available": False, "reason": "no synced full-text content"})
        return {"key": key, "attachments": result, "count": len(result), "source": "zotero-web-api"}

    def set_fulltext(self, key, content):
        record = self.api.item(item_key(key))
        if data(record).get("itemType") != "attachment":
            raise ZoteroError("Full-text content belongs to an attachment.", "wrong_item_type")
        if not isinstance(content, dict) or not isinstance(content.get("content"), str):
            raise ZoteroError("Full-text JSON needs a string content field and indexing statistics.", "bad_arguments")
        pair = ("indexedPages", "totalPages") if data(record).get("contentType") == "application/pdf" else (
            "indexedChars", "totalChars")
        if any(not isinstance(content.get(k), int) or content[k] < 0 for k in pair) or content[pair[0]] > content[pair[1]]:
            raise ZoteroError("Provide valid " + ", ".join(pair) + " statistics.", "bad_arguments")

        def update():
            self.api.request("PUT", f"/items/{key}/fulltext", data=content)
            return self.fulltext(key)
        return self._write("set-fulltext", {"key": key, "content": content}, update)

    def changes(self, since: int):
        if since < 0:
            raise ZoteroError("since must be nonnegative.", "bad_arguments")
        result, versions = {}, {}
        for name in ("items", "collections", "searches"):
            result[name] = self.api.get("/" + name, format="versions", since=since)
            versions[name] = self.api.last_headers.get("last-modified-version")
        for name in ("deleted", "fulltext"):
            result[name] = self.api.get("/" + name, since=since)
            versions[name] = self.api.last_headers.get("last-modified-version")
        values = set(versions.values())
        stable = len(values) == 1 and None not in values
        return {"since": since, "changes": result, "endpoint_versions": versions,
                "consistent": stable, "checkpoint": int(next(iter(values))) if stable else None,
                "note": "Advance a sync checkpoint only after fetching changed objects and applying deletions; "
                        "rerun if endpoint versions differ."}

    def saved_searches(self, action="list", key=None, name=None, conditions=None, fields=None):
        if action == "list":
            return {"searches": self.api.all("/searches")}
        if action == "get":
            return self.api.get(f"/searches/{item_key(key)}")
        if action == "create":
            if not name or not isinstance(conditions, list):
                raise ZoteroError("A saved search needs a name and conditions array.", "bad_arguments")
            payload = {"name": name, "conditions": conditions}
            return self._write("create-search", [payload], lambda: self.api.create([payload], "/searches"))
        if action == "update":
            record = self.api.get(f"/searches/{item_key(key)}")
            if not isinstance(fields, dict) or set(fields) - {"name", "conditions"}:
                raise ZoteroError("Search update fields are name and conditions.", "bad_arguments")
            payload = {"key": record["key"], "version": record["version"], **fields}
            return self._write("update-search", payload, lambda: self.api.create([payload], "/searches"))
        if action == "delete":
            key = item_key(key)
            self.api.get(f"/searches/{key}")
            self.api.get("/searches", format="versions")
            version = self.api.last_headers.get("last-modified-version")
            if not version:
                raise ZoteroError("Cannot delete a saved search without the library version.", "missing_version")
            return self._write("delete-search", {"key": key, "library_version": version}, lambda: self.api.request(
                "DELETE", "/searches", params={"searchKey": key}, headers={"If-Unmodified-Since-Version": version}))
        raise ZoteroError("Unsupported saved-search action.", "bad_arguments")

    def create_note(self, parent=None, text="", note_html=None, heading=None, tags=None):
        payload = {"note": note_html if note_html is not None else note_text_to_html(text, heading),
                   "tags": merge_tags(tags or [])}
        return self.create_item("note", payload, parent)

    def update_note(self, key, text=None, note_html=None, append=False):
        record = self.api.item(item_key(key))
        if data(record).get("itemType") != "note":
            raise ZoteroError("The target is not a note.", "wrong_item_type")
        content = note_html if note_html is not None else note_text_to_html(text or "")
        if append:
            content = data(record).get("note", "") + "\n" + content
        return self._write("update-note", {"key": key, "note": content},
                           lambda: self.api.patch(record, {"note": content}))

    def set_parent(self, key, parent):
        record = self.api.item(item_key(key))
        if data(record).get("itemType") not in {"attachment", "note", "annotation"}:
            raise ZoteroError("Only attachments, notes and annotations can have parents.", "wrong_item_type")
        if parent:
            if parent == key:
                raise ZoteroError("An item cannot parent itself.", "bad_arguments")
            self.api.item(item_key(parent))
        return self._write("set-parent", {"key": key, "parentItem": parent or False},
                           lambda: self.api.patch(record, {"parentItem": parent or False}))

    def uri(self, key):
        return "http://zotero.org" + self.api.config.prefix + "/items/" + item_key(key)

    def related(self, key):
        record = self.api.item(item_key(key))
        relations = data(record).get("relations", {})
        return {"key": key, "relations": relations}

    def relation(self, first, second, *, remove=False, predicate="dc:relation"):
        if first == second:
            raise ZoteroError("Choose two distinct items.", "bad_arguments")
        a, b = self.api.item(item_key(first)), self.api.item(item_key(second))
        plans = []
        for record, other in [(a, second), (b, first)]:
            relations = copy.deepcopy(data(record).get("relations", {}))
            values = relations.get(predicate, [])
            values = [values] if isinstance(values, str) else values
            uri = self.uri(other)
            values = [v for v in values if v != uri] if remove else list(dict.fromkeys(values + [uri]))
            if values:
                relations[predicate] = values
            else:
                relations.pop(predicate, None)
            plans.append({"key": record["key"], "relations": relations})
        return self._write("remove-relation" if remove else "add-relation", plans,
                           lambda: self._apply_records([a, b], lambda r: self.api.patch(
                               r, {"relations": next(p["relations"] for p in plans if p["key"] == r["key"])})))

    def find_duplicates(self, *, threshold=0.93, limit=25, start=0):
        if not 0 <= threshold <= 1 or start < 0 or (limit is not None and not 1 <= limit <= 100):
            raise ZoteroError("Use threshold 0..1, limit 1..100 and a nonnegative start.", "bad_arguments")
        records = [r for r in self.catalog() if data(r).get("itemType") not in {"attachment", "note", "annotation"}]
        groups, assigned = [], set()
        for i, a in enumerate(records):
            if a["key"] in assigned:
                continue
            da = data(a)
            doi = normalize_doi(da.get("DOI", ""))
            members, reasons = [a], []
            for b in records[i + 1:]:
                if b["key"] in assigned:
                    continue
                db = data(b)
                exact = bool(doi and doi == normalize_doi(db.get("DOI", "")))
                ta, tb = norm(da.get("title", "")), norm(db.get("title", ""))
                title_match = (len(ta) >= 12 and len(tb) >= 12 and da.get("itemType") == db.get("itemType")
                               and SequenceMatcher(None, ta, tb).ratio() >= threshold)
                if exact or title_match:
                    members.append(b)
                    reasons.append("same_doi" if exact else "similar_title")
            if len(members) > 1:
                assigned.update(r["key"] for r in members)
                groups.append({"items": [project(r) for r in members], "reason": sorted(set(reasons)),
                               "high_confidence": all(r == "same_doi" for r in reasons)})
        return {"groups": groups[start:] if limit is None else groups[start:start + limit], "total": len(groups),
                "next_start": start + limit if limit and start + limit < len(groups) else None}

    def merge_duplicates(self, keep: str, duplicates: list[str]):
        keys = list(dict.fromkeys([item_key(keep)] + [item_key(k) for k in duplicates]))
        if len(keys) < 2:
            raise ZoteroError("Provide a keeper and at least one distinct duplicate.", "bad_arguments")
        records = [self.api.item(k) for k in keys]
        kinds = {data(r).get("itemType") for r in records}
        if len(kinds) != 1 or kinds & {"attachment", "annotation", "note"}:
            raise ZoteroError("Merge requires bibliographic items of the same type.", "wrong_item_type")
        keeper = records[0]
        merged, conflicts = copy.deepcopy(data(keeper)), {}
        for record in records[1:]:
            for key, value in data(record).items():
                if key in {"key", "version", "itemType", "dateAdded", "dateModified", "deleted"}:
                    continue
                if key == "tags":
                    merged[key] = merge_tags(merged.get(key, []), value)
                elif key == "collections":
                    merged[key] = list(dict.fromkeys(merged.get(key, []) + value))
                elif key == "relations":
                    relations = merged.setdefault("relations", {})
                    for pred, uris in value.items():
                        prev = relations.get(pred, [])
                        prev = [prev] if isinstance(prev, str) else prev
                        uris = [uris] if isinstance(uris, str) else uris
                        relations[pred] = list(dict.fromkeys(prev + uris))
                elif not merged.get(key):
                    merged[key] = value
                elif value and merged[key] != value:
                    conflicts.setdefault(key, []).append({"key": record["key"], "value": value})
        for pred, values in list(merged.get("relations", {}).items()):
            values = [values] if isinstance(values, str) else values
            merged["relations"][pred] = [v for v in values if v not in {self.uri(k) for k in keys}]
        replaces = merged.setdefault("relations", {}).get("dc:replaces", [])
        replaces = [replaces] if isinstance(replaces, str) else replaces
        merged["relations"]["dc:replaces"] = list(dict.fromkeys(replaces + [self.uri(k) for k in keys[1:]]))
        fields = {k: v for k, v in merged.items() if k not in {
            "key", "version", "itemType", "dateAdded", "dateModified", "deleted"}}
        children = [c for r in records[1:] for c in self.api.children(r["key"])]
        plan = {"keep": keep, "duplicates": keys[1:], "children": [c["key"] for c in children],
                "fields": fields, "preserved_conflicts": conflicts}

        def execute():
            done = []
            try:
                result = self.api.patch(keeper, fields)
                done.append({"updated": keep})
                for child in children:
                    self.api.patch(child, {"parentItem": keep})
                    done.append({"reparented": child["key"]})
                for record in records[1:]:
                    self.api.patch(record, {"deleted": 1})
                    done.append({"trashed": record["key"]})
            except ZoteroError as exc:
                raise ZoteroError(str(exc), "partial_write", details={"completed": done, "cause": exc.code}) from exc
            return {"item": result, "actions": done, "preserved_conflicts": conflicts}
        return self._write("merge-duplicates", plan, execute)

    def batch_update(self, keys, *, fields=None, add_tags=None, remove_tags=None):
        fields = {} if fields is None else fields
        if not isinstance(fields, dict) or set(fields) & {"key", "version", "itemType"}:
            raise ZoteroError("Cannot batch change key/version/itemType.", "bad_arguments")
        if not fields and not add_tags and not remove_tags:
            raise ZoteroError("Provide fields or tags to change.", "bad_arguments")
        records = [self.api.item(item_key(k)) for k in list(dict.fromkeys(keys))]
        plans = []
        for r in records:
            patch = copy.deepcopy(fields)
            if add_tags or remove_tags:
                patch["tags"] = merge_tags([t for t in data(r).get("tags", [])
                                            if t["tag"] not in (remove_tags or [])], add_tags or [])
            plans.append({"key": r["key"], "fields": patch})
        return self._write("batch-update", plans, lambda: self._apply_records(records, lambda r: self.api.patch(
            r, next(p["fields"] for p in plans if p["key"] == r["key"]))))

    def export(self, *, keys=None, collection=None, fmt="bibtex", style="apa", locale="en-US"):
        params = {"format": fmt, "style": style, "locale": locale}
        if keys:
            if len(keys) > 50:
                raise ZoteroError("Export at most 50 explicit keys per call; use a collection for larger exports.",
                                  "bad_arguments")
            params["itemKey"] = ",".join(item_key(k) for k in keys)
        path = f"/collections/{self.resolve_collection(collection)}/items/top" if collection else "/items/top"
        if not keys and not collection:
            raise ZoteroError("Choose item keys or a collection to export.", "bad_arguments")
        texts, objects, start = [], [], 0
        while True:
            res = self.api.request("GET", path, params={**params, "limit": 100, "start": start}, raw=True)
            text = res.body.decode("utf-8")
            if fmt in {"csljson", "json"}:
                page = json.loads(text)
                if not isinstance(page, list):
                    raise ZoteroError("Expected an array in the JSON export.", "invalid_response")
                objects.extend(page)
            else:
                texts.append(text)
            total = int(res.headers.get("total-results", "0"))
            if fmt == "bib" or start + 100 >= total:
                break
            start += 100
        return {"format": fmt, "items": objects} if fmt in {"csljson", "json"} else {
            "format": fmt, "text": "\n".join(texts)}

    def libraries(self, user_id=None):
        cfg = self.api.config
        if not user_id and cfg.library_type == "user":
            user_id = cfg.library_id
        if not user_id and cfg.api_key:
            info = self.api.request("GET", "/keys/" + cfg.api_key, absolute=True)
            user_id = str(info["userID"])
        if not user_id:
            raise ZoteroError("Provide --user-id to list a user's group libraries.", "bad_arguments")
        if not str(user_id).isdigit():
            raise ZoteroError("user-id must be numeric.", "bad_arguments")
        groups = self.api.request("GET", f"/users/{user_id}/groups", absolute=True)
        return {"active": {"id": cfg.library_id, "type": cfg.library_type}, "libraries": [
            {"id": str(user_id), "type": "user"}, *[
                {"id": str(g["id"]), "type": "group", "name": data(g).get("name", "")} for g in groups]]}

    def synthesize(self, keys=None, collection=None, tag=None):
        records = ([self.api.item(item_key(k)) for k in keys] if keys else
                   self.list_items(collection=collection, tags=[tag] if tag else None,
                                   top=True, all_items=True, detail="full")["items"])
        groups = []
        for record in records:
            if data(record).get("itemType") in {"attachment", "note", "annotation"}:
                continue
            children = self.api.children(record["key"])
            notes = [r for r in children if data(r).get("itemType") == "note"]
            annotations = []
            for attachment in children:
                if data(attachment).get("itemType") == "attachment":
                    annotations.extend(self.notes(attachment["key"], annotations=True)["items"])
            groups.append({"item": project(record), "notes": notes, "annotations": annotations})
        return {"papers": groups, "count": len(groups), "kind": "source_digest; interpret findings in the agent"}
