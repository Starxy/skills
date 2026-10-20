"""Attachment transfer using only the official Zotero Storage upload/download flow."""

from __future__ import annotations

import hashlib
import mimetypes
import tempfile
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from zotero_api import ZoteroError
from zotero_core import data, item_key


def safe_filename(name: str) -> str:
    import re
    leaf = name.replace("\\", "/").rsplit("/", 1)[-1]
    leaf = re.sub(r'[^\w.\- ()]', "_", leaf).strip(". ")[:180] or "attachment.bin"
    if re.fullmatch(r"CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9]", leaf.split(".")[0], re.I):
        leaf = "_" + leaf
    return leaf


def file_hash(path: Path) -> str:
    digest = hashlib.md5()  # Required by Zotero's official file storage protocol.
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Files:
    def __init__(self, library):
        self.lib, self.api = library, library.api

    def download(self, key: str, out: str | None = None):
        record = self.api.item(item_key(key))
        d = data(record)
        if d.get("itemType") != "attachment":
            raise ZoteroError("Download needs an attachment key; use children to find it.", "wrong_item_type")
        if d.get("linkMode") in {"linked_file", "linked_url"}:
            raise ZoteroError("Linked files/URLs have no stored file in Zotero Storage.", "file_not_stored",
                              details={"linkMode": d.get("linkMode"), "url": d.get("url")})
        filename = safe_filename(d.get("filename") or (key + ".bin"))
        fingerprint = d.get("md5") or str(record.get("version", "current"))
        target = self.api.config.cache_dir / "files" / key / str(fingerprint) / filename
        if not target.exists() or (d.get("md5") and file_hash(target) != d["md5"]):
            try:
                response = self.api.request("GET", f"/items/{key}/file", raw=True)
            except ZoteroError as exc:
                if exc.code == "not_found":
                    raise ZoteroError("Attachment metadata exists, but the file is not available in Zotero Storage "
                                      "(it may be unsynced or stored only in WebDAV).", "file_not_synced") from exc
                raise
            if d.get("md5") and hashlib.md5(response.body).hexdigest() != d["md5"]:
                raise ZoteroError("Downloaded bytes do not match the attachment MD5; refresh metadata and retry.",
                                  "file_version_conflict")
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                stream.write(response.body)
                temporary = Path(stream.name)
            temporary.replace(target)
        if out:
            import shutil
            dest = Path(out).expanduser().resolve()
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest != target.resolve():
                shutil.copyfile(target, dest)
            target = dest
        return {"key": key, "path": str(target.resolve()), "filename": filename,
                "bytes": target.stat().st_size, "source": "zotero-storage/cache"}

    def attach(self, parent: str | None, file: str | None = None, url: str | None = None, title=None):
        if bool(file) == bool(url):
            raise ZoteroError("Choose exactly one of file or url.", "bad_arguments")
        if parent:
            parent_record = self.api.item(item_key(parent))
            if data(parent_record).get("itemType") in {"attachment", "annotation", "note"}:
                raise ZoteroError("Attachments need a bibliographic parent or no parent.", "wrong_item_type")
        if url:
            if urlsplit(url).scheme not in {"https", "http"}:
                raise ZoteroError("Attachment URL must use HTTP(S).", "bad_url")
            payload = self.api.template("attachment", linkMode="linked_url")
            payload.update({"title": title or url, "url": url, "linkMode": "linked_url"})
            if parent:
                payload["parentItem"] = parent
            for child in self.api.children(parent) if parent else []:
                if data(child).get("itemType") == "attachment" and data(child).get("url") == url:
                    return {"status": "unchanged", "attachment": child}
            return self.lib._write("attach-url", [payload], lambda: self.api.create([payload]))
        path = Path(file).expanduser().resolve()
        if not path.is_file():
            raise ZoteroError("Attachment file does not exist.", "file_not_found")
        digest = file_hash(path)
        for child in self.api.children(parent) if parent else []:
            if data(child).get("itemType") == "attachment" and data(child).get("md5") == digest:
                return {"status": "unchanged", "attachment": child}
        payload = self.api.template("attachment", linkMode="imported_file")
        payload.update({"linkMode": "imported_file", "title": title or path.name,
                        "contentType": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                        "filename": path.name})
        if parent:
            payload["parentItem"] = parent
        plan = {"attachment": payload, "file": str(path), "md5": digest, "bytes": path.stat().st_size}

        def upload():
            created = self.api.create([payload])[0]
            key = created["key"]
            uploaded = False
            try:
                form = {"md5": digest, "filename": path.name, "filesize": path.stat().st_size,
                        "mtime": int(path.stat().st_mtime * 1000)}
                headers = {"Content-Type": "application/x-www-form-urlencoded", "If-None-Match": "*"}
                auth = self.api.request("POST", f"/items/{key}/file", data=urlencode(form).encode(), headers=headers)
                if not auth.get("exists"):
                    if urlsplit(auth["url"]).scheme != "https":
                        raise ZoteroError("Zotero Storage upload URL must use HTTPS.", "invalid_response")
                    content = auth["prefix"].encode("utf-8") + path.read_bytes() + auth["suffix"].encode("utf-8")
                    # This signed URL comes from Zotero's upload authorization, and gets no Zotero credentials.
                    res = self.api.transport.request("POST", auth["url"], body=content,
                                                     headers={"Content-Type": auth["contentType"]})
                    if res.status != 201:
                        raise ZoteroError(f"Zotero Storage returned HTTP {res.status}.", "storage_upload_failed")
                    uploaded = True
                    self.api.request("POST", f"/items/{key}/file",
                                     data=urlencode({"upload": auth["uploadKey"]}).encode(), headers=headers)
                result = self.api.item(key)
                if data(result).get("md5") != digest:
                    raise ZoteroError("Upload completed but its MD5 could not be verified.", "verification_failed")
                return result
            except (ZoteroError, OSError, KeyError, TypeError, ValueError) as exc:
                raise ZoteroError(str(exc), "partial_write", details={"attachment_key": key,
                                  "storage_bytes_uploaded": uploaded, "cause": getattr(exc, "code", "upload_failed"),
                                  "details": getattr(exc, "details", None)}) from exc
        return self.lib._write("attach-file", plan, upload)
