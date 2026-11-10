# Zotero Web API implementation notes

The runtime uses Python's standard library and `https://api.zotero.org`, with
`Zotero-API-Version: 3`.

## API documentation

- [Read requests, filters, exports and pagination](https://www.zotero.org/support/dev/web_api/v3/basics)
- [Write requests, versions and multi-object responses](https://www.zotero.org/support/dev/web_api/v3/write_requests)
- [Attachment upload protocol](https://www.zotero.org/support/dev/web_api/v3/file_upload)
- [Synced full-text content](https://www.zotero.org/support/dev/web_api/v3/fulltext_content)
- [Incremental syncing](https://www.zotero.org/support/dev/web_api/v3/syncing)
- [Official new-item templates](https://api.zotero.org/items/new?itemType=journalArticle)
- [Official annotation template](https://api.zotero.org/items/new?itemType=annotation&annotationType=highlight)

## Routes and invariants

`P` is `/users/<userID>` or `/groups/<groupID>`. Numeric IDs and uppercase
eight-character item/collection keys are distinct. A client is bound to one P.

Configuration resolves the library ID from command-line arguments, then the
environment. If neither provides an ID and the type is `user`, it requests
`GET /keys/<key>` and uses the returned numeric `userID` as the personal library
ID. This lookup uses the existing transport, API version, backoff and error
handling; missing or malformed `userID` values produce `invalid_response`.
Explicit IDs skip discovery, and `group` libraries always require an explicit
ID. The key's permissions still govern subsequent reads and writes.

| Operation | Official request |
| --- | --- |
| Items / top-level / trash | `GET P/items`, `P/items/top`, `P/items/trash` |
| Item / children | `GET P/items/KEY`, `P/items/KEY/children` |
| Item create / import | `POST P/items` with an array, at most 50 objects per batch |
| Item patch / permanent delete | `PATCH` / `DELETE P/items/KEY`, guarded by the fetched item version |
| Trash an item | `PATCH P/items/KEY` with `deleted: 1` |
| Collections | `GET P/collections`; create with `POST P/collections` |
| Update / delete collection | `PUT` / `DELETE P/collections/KEY` (collection update is not item PATCH) |
| Membership | Update an item's `collections` array in one item PATCH |
| Tags | `GET P/tags`, `P/items/KEY/tags`, `P/collections/KEY/tags` |
| Notes / annotations | Ordinary item records with `itemType=note` / `annotation` |
| Related items | An item's `relations` object; bidirectional links require two writes |
| Full-text read / supplied text write | `GET` / `PUT P/items/ATTACHMENT_KEY/fulltext` |
| Full-text versions | `GET P/fulltext?since=VERSION` |
| Export | Item/collection reads with `format=bibtex`, `csljson`, `ris`, `bib` etc. |
| Saved searches | `GET P/searches[/KEY]`; `POST P/searches` for creates/versioned updates |
| Saved-search deletion | `DELETE P/searches?searchKey=KEY` with the current library version |
| Changed objects | `GET P/items`, `collections`, `searches` with `format=versions&since=VERSION` |
| Deleted objects | `GET P/deleted?since=VERSION` |
| Key permissions / group libraries | `GET /keys/<key>`; `GET /users/<userID>/groups` |
| Schemas | `GET /itemTypes`, `/itemFields`, `/itemTypeFields`, `/itemTypeCreatorTypes`, `/creatorFields` |

`qmode=titleCreatorYear` is the normal keyword search. `qmode=everything` includes
server-indexed full text. Results depend on what has synced; there is no local
index, embedding model or PDF extraction fallback.

Full-text retrieval preserves `indexedPages/totalPages` or
`indexedChars/totalChars`. A 404 is reported as unavailable, not as a paper with
empty content. Uploading full text requires supplying the correct counters;
the script does not extract the content itself.

Read pagination uses `Total-Results`, a page size of at most 100, and offsets.
Normal listings expose `next_start`; `--all` follows every page. Text/CSL JSON
collection exports also follow pages. CSL bibliography format (`bib`) is
limited by Zotero to 150 items per response; larger requests can be rejected by
the service. Explicit-key exports accept at most 50 keys per invocation.

The default write path is immediate execution. `--dry-run` suppresses every
remote mutation. There are no confirmation prompts, plan tokens, or mandatory
preview/approve steps. Reads for templates and version preconditions still occur.

Update/delete operations use `If-Unmodified-Since-Version`. Unversioned creates
send a random `Zotero-Write-Token`. HTTP 200 is not sufficient: every per-object
`successful`, `unchanged`, and `failed` result must be accounted for. Partial
failure includes completed records, so callers can reconcile rather than replay
the whole batch. A 412 conflict is not automatically retried. Reads can retry a
429/503 with bounded `Retry-After`; successful-request `Backoff` is also honored.

## Attachment storage

1. Get the `attachment` template with `linkMode=imported_file`, and create the
   metadata item via `POST P/items`.
2. Authorize with `POST P/items/KEY/file`, form fields `md5`, `filename`,
   `filesize`, `mtime` (milliseconds), and `If-None-Match: *`.
3. If the response is `exists: 1`, the bytes are already associated. Otherwise
   upload `prefix + file bytes + suffix` to the HTTPS signed URL supplied by
   Zotero, using its supplied content type, and require HTTP 201.
4. Register via `POST P/items/KEY/file` with `upload=<uploadKey>` and the same
   precondition. Re-fetch metadata and verify MD5.

The signed storage request and cross-origin file redirects never receive the
Zotero API key. Credentials are used only on the Zotero API origin. An interrupted
upload reports the created attachment key for reconciliation; it is not silently
deleted or claimed complete. Repeated uploads to the same parent with the same
MD5 reuse the attachment.

Download `GET P/items/KEY/file`. Verify a supplied MD5, sanitize the remote
filename, and cache under `$ZOTERO_CACHE_DIR/<user-or-group>-<id>/files/KEY/<hash>/`.
Default cache root is `~/.cache/zotero-library`. Linked local files, linked URLs,
unsynced bytes and WebDAV-only bytes are not available from Zotero Storage.
`attach --url` creates only linked-URL metadata and never fetches the URL.

## Annotation positions

The official annotation template provides fields for the selected
`annotationType`. Pass an explicit `annotationPosition` object matching the
attachment, e.g. `{"pageIndex":0,"rects":[[x1,y1,x2,y2]]}` for a PDF highlight.
Coordinates are Zotero/PDF coordinates, not normalized rectangles or guessed
text offsets. `pageIndex` is zero-based; labels shown to humans can differ.
Use `annotationSortIndex` when known. This implementation creates/updates synced
native annotation records; it does not calculate positions or edit PDF bytes.

## Capabilities and limitations

| Capability | Implementation or limitation |
| --- | --- |
| Keyword, tag, recent, collection search | Native API reads and filters |
| Advanced search | Explicit local metadata predicates over paged official records |
| Metadata, BibTeX and other exports | Native API item reads and export formats |
| Full text | Native synced full-text endpoint; no PDF fallback |
| Notes and annotations | Native item CRUD; caller supplies annotation position |
| Item, collection, tag, relation maintenance | Native writes and client compositions |
| Batch updates, duplicate detection/merge | Client-side plans over official metadata and versioned item writes |
| Attachment import | Explicit file upload or linked-URL metadata; no inferred bibliography |
| Citation-key lookup | Synced `citationKey`/`Extra` only; no desktop Better BibTeX call |
| Annotation synthesis | Source digest grouped by paper; explanation remains agent work |
| Personal/group libraries | Native groups listing and per-command ID/type overrides |
| Sync administration | Native object/full-text version maps and deletion logs |
| Semantic search | Not implemented |
| PDF outlines, page images/layout, automatic highlight placement | Excluded; not native Web API operations |
| DOI/ISBN/URL metadata enrichment, OA discovery, OpenAlex, Scite | Excluded; require external providers |
| Desktop RSS, reader UI, local write authorization | Excluded; desktop/local features |

Duplicate merge is not a server-side transaction. It retains the keeper's
conflicting values, fills missing fields, unions tags/collections/relations,
moves duplicate children, records `dc:replaces`, and trashes duplicate parents.
Conflicting alternatives remain in the trashed source items and in the report.
There is no automatic merge-all or two-call confirmation protocol.

Saved-search results are not exposed by the Web API. `saved-searches` manages
definitions only. `changes` reports a potential checkpoint only when all read
endpoints agree on a library version; callers must still fetch changed objects
and apply deletions before persisting that checkpoint.
