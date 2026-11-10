# Command reference

Run Python 3.10+ with the absolute path to `scripts/zotero_library.py`. No package
installation is needed. `$Z` below denotes that path. Every invocation returns
one JSON envelope; errors exit 1. Run `python $Z COMMAND --help` for exact flags.

## Shared options

- `--library-id ID --library-type user|group`: override environment selection for
  this invocation, without a persistent switch or a daemon.
- `--dry-run`: optional remote-write preview, accepted before/after the command.
  Without it, writes execute immediately. No second confirmation is required.
- `--json`: accepted for compatibility; output is always JSON.
- Legacy `--execute`: accepted as a no-op; omitting it also executes writes.
- JSON arguments accept inline JSON, `'@file.json'`, or `-` for stdin. Files use
  UTF-8 (a BOM is accepted). Quote the `@file` argument in PowerShell.
- Read lists use `--limit 25` (1..100), `--start 0` / `--offset 0`, and `--all`.
  Follow `data.next_start` until null; do not interpret the first page as the
  entire library. Metadata listings also accept `--detail keys_only|summary|full`.

Environment: `ZOTERO_API_KEY`, optional `ZOTERO_LIBRARY_ID`, optional
`ZOTERO_LIBRARY_TYPE` (default `user`), and optional `ZOTERO_CACHE_DIR` for file
downloads. Selection order is `--library-id`, then `ZOTERO_LIBRARY_ID`, then the
API key owner's `userID` from `GET /keys/<key>`. This last step applies only to
personal libraries; group libraries require an explicit ID. With only the key
configured, `python $Z config` discovers and shows the personal library ID.
Public-library reads may omit the key when an ID is supplied. Discovery does
not grant library access; permission and storage-quota failures come from Zotero.

## Discovery, search and reads

| Command | Parameters / behavior |
| --- | --- |
| `capabilities` | No credentials needed; lists scope and omissions |
| `config` | Selected ID/type, key-present boolean, cache root; never the key |
| `key-info` | Key owner/permissions, excluding the key value |
| `libraries` | `--user-id ID` optional; lists personal and group libraries |
| `library-info` | Item count and active library version |
| `search [QUERY]` | `--mode items|tag|advanced|citekey|notes|annotations|fulltext` |
| `items` | `--q QUERY`, `--trash`, same metadata filters as normal search |
| `top`, `recent` | Top-level items or items ordered by newest `dateAdded` |
| `advanced-search` | `--conditions JSON --join all|any [--collection SPEC]` |
| `item KEY` | Complete raw JSON; aliases `metadata`, `fetch`; `--format bibtex|csljson|ris` for exports |
| `children KEY...` | All child records for each supplied parent |
| `collections` | Optional `--query NAME` |
| `collection-items SPEC` | A collection key, exact name, or `parent/child` path |
| `item-collections KEY` | Current collection keys and names |
| `tags` | Optional `--item KEY` or `--collection SPEC`, `--query TEXT`, pagination |
| `item-template TYPE` | Official template; attachment needs `--link-mode`; annotation needs `--annotation-type` |
| `schema KIND` | `itemTypes`, `itemFields`, `itemTypeFields`, `itemTypeCreatorTypes`, `creatorFields`; type-specific routes need `--item-type TYPE` |

Normal search accepts `--collection SPEC`, repeated `--tag TAG`, `--item-type TYPE`,
`--qmode titleCreatorYear|everything`, `--sort FIELD`, `--direction asc|desc`,
and `--all-libraries`. Tag parameters form an intersection; Zotero also accepts
its own OR-expression syntax in an individual tag value. `--mode fulltext` sets
`qmode=everything`; it uses the official server index, not semantic search.

Citation-key lookup checks a synced `citationKey` or `Citation Key:` line in
`extra`. It does not invent Better BibTeX keys or call a local plugin.

Advanced conditions are evaluated over fetched official metadata. Example:

```json
[
  {"field": "title", "operation": "contains", "value": "attention"},
  {"field": "year", "operation": "isAfter", "value": "2020"},
  {"field": "tags", "operation": "is", "value": "reviewed"}
]
```

Supported operations: `contains`, `notContains`, `is`, `isNot`, `beginsWith`,
`isBefore`, `isAfter`, `exists`. Creator aliases `creator`/`author` inspect all
creator names; `year` uses the first four characters of `date`. Date comparisons
are lexical, so prefer ISO-formatted dates. Unsupported operations are errors.

```powershell
python $Z search 'attention mechanisms' --limit 10 --detail keys_only
python $Z search 'training data' --mode fulltext --all
python $Z search --tag reviewed --tag important
python $Z search 'author2026' --mode citekey
python $Z advanced-search --conditions '@conditions.json' --join all
python $Z item PAPER001
python $Z children PAPER001 PAPER002
```

## Item, collection and tag writes

| Command | Parameters / behavior |
| --- | --- |
| `create-item TYPE` | `--fields JSON [--parent-id KEY]`; official template plus supplied fields |
| `import-items` | `--data JSON_ARRAY`; new Zotero JSON, no existing key/version; batches of 50 |
| `update-item KEY` | `--fields JSON`; fetch version, patch fields, read back |
| `delete-item KEY...` | Trash by default; `--permanent` physically deletes |
| `set-parent KEY` | `--parent KEY`, or omit to clear parent where Zotero allows it |
| `create-collection NAME` | Optional `--parent SPEC` |
| `update-collection SPEC` | `--fields JSON` containing `name` and/or `parentCollection` |
| `delete-collection SPEC` | Delete collection, not its library items |
| `add-to-collection SPEC KEY` | Append a membership |
| `move-to-collection SPEC KEY` | Replace memberships; `--from-collection SPEC` removes only that source |
| `remove-from-collection SPEC KEY` | Remove only this membership |
| `add-tags KEY TAG...`, `remove-tags KEY TAG...` | Preserve untouched tags and their types |
| `rename-tag OLD NEW` | Fetch every old-tag item; replace/deduplicate tags while preserving type |
| `batch-update KEY...` | `--fields JSON`, repeated `--add-tag TAG` and `--remove-tag TAG` |

No metadata lookup occurs from a bare DOI/URL/ISBN. Supply the known Zotero fields
or new Zotero JSON records. `create-item` never claims an automatically fetched
title, author list or abstract.

Example `fields.json`:

```json
{
  "title": "A reproducible paper",
  "DOI": "10.1000/example",
  "creators": [{"creatorType": "author", "firstName": "Ada", "lastName": "Lovelace"}],
  "tags": [{"tag": "to-read", "type": 0}]
}
```

```powershell
python $Z create-item journalArticle --fields '@fields.json'
python $Z update-item PAPER001 --fields '@corrections.json'
python $Z move-to-collection 'Research/Reviewed' PAPER001
python $Z batch-update PAPER001 PAPER002 --add-tag screened
python $Z rename-tag old-tag new-tag
python $Z delete-item PAPER001 --dry-run  # Only when a preview is requested
```

## Notes, annotations and full text

| Command | Parameters / behavior |
| --- | --- |
| `notes`, `annotations` | `--parent KEY` optional; `--query TEXT` searches synced text |
| `create-note [PARENT_KEY]` | Exactly one `--text TEXT`, `--file PATH`, or `--html HTML`; optional `--heading`, repeated `--tag` |
| `update-note KEY` | Same text/HTML/file sources; `--append` retains previous HTML |
| `delete-note KEY` | Permanently delete a note, after checking its type |
| `create-annotation ATTACHMENT_KEY` | `--type TYPE --position JSON`; optional `--text`, `--comment`, `--color '#RRGGBB'`, `--page-label`, `--sort-index`, repeated `--tag` |
| `update-annotation KEY` | `--fields JSON`; annotation fields/tags only |
| `delete-annotation KEY` | Permanently delete a native annotation |
| `fulltext KEY` | Attachment key or bibliographic parent; returns all matching synced text with index statistics |
| `set-fulltext ATTACHMENT_KEY` | `--fields JSON`; supplied text plus appropriate counters |
| `fulltext-changes` | `--since VERSION`; full-text version map |
| `synthesize` | `--keys KEY...`, `--collection SPEC`, or `--tag TAG`; source digest grouped by paper |

Plain note text supports escaped paragraphs, `#` headings and `- ` bullet lists.
Use `--html` for richer Zotero note formatting or read/edit/write HTML preservation.

Annotation position example (PDF coordinates supplied by the caller):

```json
{"pageIndex": 0, "rects": [[72, 650, 300, 670]]}
```

This is not a normalized box and it is not automatically located in a PDF.
Full-text uploads for a PDF need `content`, `indexedPages`, `totalPages`; other
text attachments need `content`, `indexedChars`, `totalChars`.

```powershell
python $Z create-note PAPER001 --heading '阅读笔记' --file ./notes.txt
python $Z update-note NOTE0001 --append --text 'Additional evidence'
python $Z annotations --parent PAPER001
python $Z create-annotation ATTACH01 --type highlight --position '@position.json' --text 'Exact words'
python $Z fulltext ATTACH01
python $Z synthesize --keys PAPER001 PAPER002
```

## Files, exports, relations and duplicates

| Command | Parameters / behavior |
| --- | --- |
| `attach` | Exactly one `--file PATH` or `--url URL`; optional `--parent KEY`, `--title` |
| `download ATTACHMENT_KEY` | Optional `--out PATH`; otherwise uses the library-scoped cache |
| `export` | Exactly one `--keys KEY...` or `--collection SPEC`; `--format bibtex|biblatex|csljson|ris|bib|refer`, `--style apa`, `--locale en-US`, optional `--out PATH` |
| `related KEY` | Stored relation object, not a research-discovery query |
| `add-relation FIRST SECOND`, `remove-relation FIRST SECOND` | Bidirectional; optional `--predicate dc:relation` |
| `find-duplicates` | DOI equality or title similarity; `--threshold 0.93`, pagination |
| `merge-duplicates KEEP OTHER...` | Keep conflicting keeper values, union other metadata, move children, trash duplicate parents |

An uploaded file is deduplicated by MD5 within its parent. A linked URL only
creates Zotero metadata. Files are never downloaded from that linked website.
There is no PDF metadata inference, OA downloader, or page-rendering step.

```powershell
python $Z attach --parent PAPER001 --file ./paper.pdf
python $Z attach --parent PAPER001 --url 'https://example.org/paper.pdf'
python $Z download ATTACH01 --out ./downloaded.pdf
python $Z export --collection 'Research' --format bibtex --out ./references.bib
python $Z export --keys PAPER001 PAPER002 --format bib --style apa
python $Z add-relation PAPER001 PAPER002
python $Z find-duplicates
python $Z merge-duplicates PAPER001 PAPER002
```

## Saved searches and syncing

`saved-searches list|get|create|update|delete` manages definitions. `get`,
`update`, `delete` take `--key KEY`; `create` takes `--name NAME --conditions
JSON`; `update` takes `--fields JSON` with `name` and/or `conditions`.
Saved-search conditions use Zotero's native `condition/operator/value` schema,
which differs from `advanced-search`'s local `field/operation/value` schema.
The Web API does not execute a desktop saved search.

`changes --since VERSION` (alias `sync`) returns object version maps, deleted
object keys/tags, full-text versions, per-endpoint library versions and a
potential consistent checkpoint. Fetch changed objects and apply deletions
before persisting the next checkpoint. A changing library returns
`consistent: false` and no checkpoint.

## Error handling

| Code | Meaning |
| --- | --- |
| `authentication`, `permission_denied` | Missing/insufficient API credentials |
| `version_conflict`, `library_locked` | Concurrent edit/locked library; reconcile before another write |
| `partial_write` | Inspect `error.details.completed` or the reported attachment key; earlier writes may have succeeded |
| `verification_failed` | Server acknowledged a write, but readback did not confirm it |
| `rate_limited` | Zotero backoff/retry budget; retry later |
| `quota_exceeded` | Zotero Storage quota or file size constraint |
| `ambiguous_collection`, `collection_not_found` | Resolve an exact key/path before writing |
| `file_not_stored`, `file_not_synced` | Official storage cannot supply these bytes |
| `file_version_conflict` | Downloaded bytes disagree with the remote MD5 |
| `bad_arguments`, `bad_key`, `invalid_input` | Fix the supplied keys/options/JSON |

Tests (offline, standard library only):

```powershell
python -B -m unittest discover -s skills/zotero-library/scripts -p 'test_*.py'
```
