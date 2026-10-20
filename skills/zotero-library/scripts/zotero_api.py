"""Zotero Web API v3 transport. No MCP or desktop Zotero dependency."""

from __future__ import annotations

import copy
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class ZoteroError(Exception):
    def __init__(self, message: str, code: str = "operation_failed", *, details: Any = None):
        super().__init__(message)
        self.code, self.details = code, details


def cache_root() -> Path:
    configured = os.environ.get("ZOTERO_CACHE_DIR")
    return Path(configured).expanduser() if configured else Path.home() / ".cache" / "zotero-library"


@dataclass(frozen=True)
class LibraryConfig:
    library_id: str
    library_type: str = "user"
    api_key: str | None = field(default=None, repr=False)
    api_base: str = "https://api.zotero.org"

    @classmethod
    def from_env(cls, library_id: str | None = None, library_type: str | None = None):
        ident = library_id or os.environ.get("ZOTERO_LIBRARY_ID")
        kind = library_type or os.environ.get("ZOTERO_LIBRARY_TYPE", "user")
        api_key = os.environ.get("ZOTERO_API_KEY")
        if kind not in {"user", "group"}:
            raise ZoteroError("ZOTERO_LIBRARY_TYPE must be user or group.", "configuration")
        if not ident:
            if kind == "group":
                raise ZoteroError("Set --library-id or ZOTERO_LIBRARY_ID for a group library; "
                                  "API key discovery only selects the owner's personal library.", "configuration")
            if not api_key:
                raise ZoteroError("Set ZOTERO_API_KEY to discover your personal library ID, "
                                  "or provide --library-id / ZOTERO_LIBRARY_ID.", "configuration")
            # Key metadata is unscoped: no library ID is needed for this absolute request.
            info = WebAPI(cls("", "user", api_key)).request("GET", "/keys/" + api_key, absolute=True)
            ident = info.get("userID") if isinstance(info, dict) else None
            if (not ident or not str(ident).isascii() or not str(ident).isdigit()
                    or int(ident) <= 0):
                raise ZoteroError("Zotero key information did not include a valid numeric userID.",
                                  "invalid_response")
        if not str(ident).isdigit():
            raise ZoteroError("Set ZOTERO_LIBRARY_ID to the numeric user/group library ID.", "configuration")
        # ZOTERO_LOCAL is deliberately ignored: this skill always uses the Web API.
        return cls(str(ident), kind, api_key)

    @property
    def prefix(self) -> str:
        return f"/{'users' if self.library_type == 'user' else 'groups'}/{self.library_id}"

    @property
    def scope(self) -> str:
        return f"{self.library_type}-{self.library_id}"

    @property
    def cache_dir(self) -> Path:
        return cache_root() / self.scope


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes

    def json(self):
        try:
            return json.loads(self.body.decode("utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise ZoteroError("The server returned invalid JSON.", "invalid_response") from exc


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Transport:
    """Bounded HTTP requests; credentials never follow cross-origin redirects."""

    def __init__(self, timeout: float = 45):
        self.timeout = timeout
        self.opener = build_opener(_NoRedirect())

    def request(self, method: str, url: str, *, headers=None, body: bytes | None = None) -> Response:
        headers = dict(headers or {})
        for _ in range(6):
            if urlsplit(url).scheme not in {"https", "http"}:
                raise ZoteroError("HTTP(S) URLs are required.", "bad_url")
            req = Request(url, data=body, headers=headers, method=method)
            try:
                with self.opener.open(req, timeout=self.timeout) as res:
                    return Response(res.status, {k.lower(): v for k, v in res.headers.items()}, res.read())
            except HTTPError as exc:
                hdr = {k.lower(): v for k, v in exc.headers.items()}
                payload = exc.read()
                if exc.code in {301, 302, 303, 307, 308} and "location" in hdr:
                    target = urljoin(url, hdr["location"])
                    if urlsplit(url).scheme == "https" and urlsplit(target).scheme != "https":
                        raise ZoteroError("Refusing an HTTPS downgrade redirect.", "bad_redirect")
                    if urlsplit(target).netloc != urlsplit(url).netloc:
                        headers = {k: v for k, v in headers.items() if k.lower() not in {
                            "authorization", "zotero-api-key", "cookie", "zotero-write-token"}}
                    if exc.code == 303 or (exc.code in {301, 302} and method == "POST"):
                        method, body = "GET", None
                        headers = {k: v for k, v in headers.items() if k.lower() != "content-type"}
                    url = target
                    continue
                return Response(exc.code, hdr, payload)
            except (URLError, TimeoutError, OSError) as exc:
                raise ZoteroError(f"Network request failed: {type(exc).__name__}", "network_error") from exc
        raise ZoteroError("Too many HTTP redirects.", "bad_redirect")


class WebAPI:
    def __init__(self, config: LibraryConfig, transport=None):
        self.config, self.transport = config, transport or Transport()
        self.last_headers: dict[str, str] = {}
        self._templates: dict[tuple, dict] = {}
        self._not_before = 0.0

    def request(self, method: str, path: str, *, params=None, data=None, headers=None,
                absolute=False, raw=False) -> Any:
        if method != "GET" and not self.config.api_key:
            raise ZoteroError("ZOTERO_API_KEY with write permission is required.", "authentication")
        url = self.config.api_base.rstrip("/") + (path if absolute else self.config.prefix + path)
        if params:
            url += "?" + urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
        hdr = {"Zotero-API-Version": "3", "User-Agent": "zotero-library-skill/2.0"}
        if self.config.api_key:
            hdr["Zotero-API-Key"] = self.config.api_key
        hdr.update(headers or {})
        payload = None
        if data is not None:
            if isinstance(data, bytes):
                payload = data
            else:
                payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
                hdr.setdefault("Content-Type", "application/json")
        if method == "POST" and path in {"/items", "/collections", "/searches"} and not (
                isinstance(data, list) and any("version" in d for d in data)):
            hdr.setdefault("Zotero-Write-Token", uuid.uuid4().hex)
        # Respect Backoff on all requests, including the request following a successful one.
        for attempt in range(3):
            delay = self._not_before - time.monotonic()
            if delay > 120:
                raise ZoteroError("Zotero requested a long backoff; retry later.", "rate_limited",
                                  details={"retry_after": round(delay)})
            if delay > 0:
                time.sleep(delay)
            res = self.transport.request(method, url, headers=hdr, body=payload)
            self.last_headers = res.headers
            backoff = self._delay(res.headers.get("backoff", "0"))
            if backoff:
                self._not_before = time.monotonic() + backoff
            if res.status in {429, 503} and method == "GET" and attempt < 2:
                self._not_before = time.monotonic() + max(backoff, self._delay(
                    res.headers.get("retry-after", str(2 ** attempt))))
                continue
            break
        if not 200 <= res.status < 300:
            code = {401: "authentication", 403: "permission_denied", 404: "not_found",
                    409: "library_locked", 412: "version_conflict", 413: "quota_exceeded",
                    429: "rate_limited"}.get(res.status, "api_error")
            message = res.body.decode("utf-8", errors="replace")[:1500]
            if self.config.api_key:
                message = message.replace(self.config.api_key, "[redacted]")
            raise ZoteroError(f"Zotero HTTP {res.status}: {message}", code,
                              details={"status": res.status})
        if raw:
            return res
        return res.json() if res.body else {"success": True}

    @staticmethod
    def _delay(value: str) -> float:
        try:
            return max(0, float(value))
        except ValueError:
            try:
                return max(0, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError):
                return 0

    def get(self, path: str, **params):
        return self.request("GET", path, params=params)

    def page(self, path="/items", *, limit=25, start=0, **params):
        if not 1 <= limit <= 100 or start < 0:
            raise ZoteroError("limit must be 1..100 and start must be nonnegative.", "bad_arguments")
        items = self.get(path, limit=limit, start=start, **params)
        if not isinstance(items, list):
            raise ZoteroError("Expected an array from the listing endpoint.", "invalid_response")
        total = int(self.last_headers.get("total-results", len(items)))
        return {"items": items, "count": len(items), "total": total,
                "start": start, "next_start": start + len(items) if start + len(items) < total else None}

    def all(self, path="/items", **params):
        start, result = 0, []
        params = {k: v for k, v in params.items() if k not in {"start", "limit"}}
        while True:
            page = self.page(path, limit=100, start=start, **params)
            result.extend(page["items"])
            if page["next_start"] is None:
                return result
            if not page["items"]:
                raise ZoteroError("Pagination stopped before the advertised total.", "incomplete_response")
            start = page["next_start"]

    def item(self, key: str):
        return self.get(f"/items/{key}")

    def children(self, key: str):
        return self.all(f"/items/{key}/children")

    def template(self, kind: str, **params):
        cache_key = (kind, tuple(sorted(params.items())))
        if cache_key not in self._templates:
            value = self.request("GET", "/items/new", absolute=True, params={"itemType": kind, **params})
            if not isinstance(value, dict):
                raise ZoteroError("Expected an object from the template endpoint.", "invalid_response")
            self._templates[cache_key] = value
        return copy.deepcopy(self._templates[cache_key])

    def create(self, records: list[dict], path="/items") -> list[dict]:
        created = []
        for offset in range(0, len(records), 50):
            batch = records[offset:offset + 50]
            try:
                res = self.request("POST", path, data=batch)
            except ZoteroError as exc:
                exc.details = {"completed": created, "cause": exc.details, "batch_start": offset}
                raise
            if not isinstance(res, dict):
                raise ZoteroError("Expected a multi-object write response.", "invalid_response",
                                  details={"completed": created, "batch_start": offset})
            successful = res.get("successful", {})
            success_keys = res.get("success", {})
            for i in range(len(batch)):
                key = str(i)
                if key in successful:
                    created.append(successful[key])
                elif key in success_keys:
                    created.append(self.get(f"{path}/{success_keys[key]}"))
                elif key in res.get("unchanged", {}):
                    val = res["unchanged"][key]
                    created.append(val if isinstance(val, dict) else self.get(f"{path}/{val}"))
            if res.get("failed"):
                raise ZoteroError("Some records were rejected; successful records were retained.", "partial_write",
                                  details={"completed": created, "failed": res["failed"], "batch_start": offset})
            if len(created) != offset + len(batch):
                raise ZoteroError("The write response did not account for every record.", "invalid_response",
                                  details={"completed": created, "response": res})
        return created

    def patch(self, record: dict, fields: dict, path="/items"):
        key = record.get("key") or record.get("data", {}).get("key")
        version = record.get("version", record.get("data", {}).get("version"))
        if not key or version is None:
            raise ZoteroError("A key and version are required for an update.", "missing_version")
        if path == "/collections":
            payload = copy.deepcopy(record.get("data", record))
            payload.update(fields)
            payload.update({"key": key, "version": version})
            self.request("PUT", f"{path}/{key}", data=payload,
                         headers={"If-Unmodified-Since-Version": str(version)})
        else:
            self.request("PATCH", f"{path}/{key}", data=fields,
                         headers={"If-Unmodified-Since-Version": str(version)})
        try:
            return self.get(f"{path}/{key}")
        except ZoteroError as exc:
            raise ZoteroError("Update was acknowledged but could not be read back: " + str(exc),
                              "verification_failed", details={"write_acknowledged": True, "key": key,
                                                             "cause": exc.code}) from exc

    def delete(self, record: dict, path="/items"):
        key = record.get("key") or record.get("data", {}).get("key")
        version = record.get("version", record.get("data", {}).get("version"))
        if not key or version is None:
            raise ZoteroError("A key and version are required for deletion.", "missing_version")
        self.request("DELETE", f"{path}/{key}", headers={"If-Unmodified-Since-Version": str(version)})
        return {"key": key, "deleted": True}
