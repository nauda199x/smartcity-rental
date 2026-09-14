"""Ảnh đã quét trực tiếp từ thư mục Drive, không ghi đè data.json của Sheet."""
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "anh-can-ho/nguon-anh.json"


def drive_id(url):
    match = re.search(r"(?:[?&]id=|/file/d/)([A-Za-z0-9_-]+)", str(url or ""))
    return match.group(1) if match else str(url or "").strip()


def source_key(row):
    return "|".join([drive_id(row.get("Ảnh đại diện"))] + [
        drive_id(x) for x in str(row.get("Danh sách ảnh") or "").splitlines() if x.strip()
    ])


@lru_cache(maxsize=1)
def photo_manifest():
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if data.get("version") == 1 and isinstance(data.get("items"), dict):
            return data
    except (OSError, ValueError, AttributeError):
        pass
    return {"version": 1, "items": {}, "revisions": {}}


def ap_dung_anh(row):
    item = photo_manifest()["items"].get(str(row.get("Mã nội bộ", "")).strip())
    # Sheet vừa đổi ảnh: dùng dữ liệu mới, không ép snapshot Drive cũ lên đó.
    if not isinstance(item, dict) or item.get("source") != source_key(row):
        return row
    photos = item.get("photos")
    if not isinstance(photos, list) or any(
        not isinstance(x, str) or not re.fullmatch(r"[A-Za-z0-9_-]{10,}", x) for x in photos
    ) or item.get("cover", "") != (photos[0] if photos else item.get("poster", "")):
        return row
    if item.get("cover") and not re.fullmatch(r"[A-Za-z0-9_-]{10,}", item["cover"]):
        return row
    url = lambda ident: "https://drive.google.com/thumbnail?id=" + ident + "&sz=w1000" if ident else ""
    return {**row, "Ảnh đại diện": url(item["cover"]), "Danh sách ảnh": "\n".join(map(url, photos))}


def ten_file_co_phien_ban(filename, ident):
    revision = photo_manifest().get("revisions", {}).get(ident, {}).get("revision", "")
    if not re.fullmatch(r"[a-f0-9]{12}", revision):
        return filename
    return re.sub(r"(?:-v[a-f0-9]{12})?\.webp$", "-v" + revision + ".webp", filename)
