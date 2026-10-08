#!/usr/bin/env python3
"""Quét thư mục ảnh công khai mỗi lượt đồng bộ, kể cả link không đổi.

Nguồn thư mục ảnh là 7 tab của Sheet CTV mới. Chỉ đọc ID CĂN (cột C)
và LINK ẢNH (cột J); không đọc ghi chú, hoa hồng hay dữ liệu liên hệ.
Drive public HTML không phải API ổn định: kiểm tra đủ cấu trúc/phân trang,
giữ snapshot gần nhất khi nguồn lỗi, và dừng nếu lỗi diện rộng.
"""
import hashlib
import json
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from media_anh import ROOT, MANIFEST, drive_id, source_key

SHEET = "1Gnh6ILQT1mV1bQFw5OLVSXMIvqcrO-M36vjlinMiH0w"
SHEETS = ("Stu", "1N", "1n+", "2n1", "2n2", "2n+", "3n")
APARTMENT_ID = re.compile(r"^CT\.[A-Za-z0-9+]+\.\d+$")
ID = re.compile(r"^[A-Za-z0-9_-]{10,}$")


def get_text(url):
    for attempt in range(2):
        try:
            with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as response:
                return response.read(8_000_001).decode("utf-8")
        except (OSError, UnicodeError):
            if attempt:
                raise


def parse_folder(text, folder_id):
    if len(text) > 8_000_000:
        raise ValueError("Drive response quá lớn")
    match = re.search(r"window\['_DRIVE_ivd'\]\s*=\s*'((?:\\.|[^'\\])*)'", text)
    if not match:
        raise ValueError("Không đọc được dữ liệu thư mục công khai")
    escaped = re.sub(r"\\x([0-9a-fA-F]{2})", r"\\u00\1", match.group(1)).replace("\\'", "'")
    data = json.loads(json.loads('"' + escaped + '"'))
    if (not isinstance(data, list) or len(data) != 6 or data[5] != 1
            or not isinstance(data[0], list) or any(data[1:4])
            or folder_id not in json.dumps(data[4]) or len(data[0]) >= 100):
        raise ValueError("Cấu trúc Drive thay đổi hoặc thư mục chưa tải đủ")
    result = []
    for row in data[0]:
        if (not isinstance(row, list) or len(row) < 14 or not isinstance(row[0], str)
                or not ID.fullmatch(row[0]) or not isinstance(row[1], list)
                or folder_id not in row[1] or not isinstance(row[3], str)):
            raise ValueError("Bản ghi Drive không hợp lệ")
        if row[3] == "application/vnd.google-apps.folder":
            raise ValueError("Có thư mục con; cần quét đầy đủ trước khi cập nhật")
        if row[3].startswith(("image/", "video/")):
            result.append({"id": row[0], "name": str(row[2]), "modified": row[9], "size": row[13],
                           "kind": "video" if row[3].startswith("video/") else "image"})
    return result


def fetch_folder_with_retry(folder, *, fetch_text=None, sleep=None, attempts=4):
    """Retry both network errors and Drive HTML that lacks folder metadata.

    Drive may respond with a consent/login/challenge page while returning HTTP
    200. Retrying only urlopen() errors cannot recover from that transient case.
    Never interpret an unreadable page as an empty folder.
    """
    fetch_text = fetch_text or get_text
    sleep = sleep or time.sleep
    if attempts < 1:
        raise ValueError("attempts phải >= 1")
    last_error = None
    for attempt in range(attempts):
        try:
            return parse_folder(
                fetch_text("https://drive.google.com/drive/folders/" + folder), folder
            )
        except (OSError, UnicodeError, ValueError) as error:
            last_error = error
            if attempt + 1 < attempts:
                # Stagger concurrent retries instead of hammering Drive again.
                sleep(min(4.0, 0.7 * (2 ** attempt)) + random.uniform(0, 0.4))
    raise ValueError(
        f"Đã thử {attempts} lần nhưng không quét được Drive: {last_error}"
    ) from last_error


def read_folders():
    result = {}
    total_rows = 0
    for sheet in SHEETS:
        query = urlencode({"tqx": "out:json", "sheet": sheet, "headers": "1",
                           "tq": "select C,J limit 1001"})
        text = get_text(f"https://docs.google.com/spreadsheets/d/{SHEET}/gviz/tq?{query}")
        data = json.loads(text[text.index("{"):text.rindex("}") + 1])
        if data.get("status") != "ok" or len(data["table"]["cols"]) != 2:
            raise ValueError("Không đọc được ID/LINK ẢNH ở tab " + sheet)
        rows = data["table"]["rows"]
        total_rows += len(rows)
        for row in rows:
            values = [(cell or {}).get("v", "") for cell in row["c"]]
            if len(values) != 2:
                raise ValueError("Tab " + sheet + " trả thiếu cột")
            code, link = [str(v or "").strip() for v in values]
            if not APARTMENT_ID.fullmatch(code):
                continue
            match = re.search(
                r"https://drive\.google\.com/(?:drive/(?:u/\d+/)?folders/|open\?id=)([A-Za-z0-9_-]+)",
                link)
            if not match:
                continue
            value = {"folderId": match.group(1), "Ảnh đại diện": "", "Danh sách ảnh": ""}
            if code in result and result[code] != value:
                raise ValueError("Mã căn trùng thư mục khác nhau: " + code)
            result[code] = value
    if not 250 <= total_rows <= 500:
        raise ValueError("Sheet CTV rỗng/bất thường: %d dòng" % total_rows)
    if len(result) < 100:
        raise ValueError("Quá ít thư mục ảnh hợp lệ trong CTV: %d" % len(result))
    return result

def build_item(row, source, files, previous):
    current = {f["id"] for f in files if f.get("kind", "image") == "image"}
    videos = {f["id"] for f in files if f.get("kind") == "video"}
    # Ưu tiên ảnh bìa do Sheet chọn nếu nó vẫn nằm trong thư mục hiện tại.
    preferred = [drive_id(source.get("Ảnh đại diện"))]
    if previous and previous.get("folderId") == source["folderId"]:
        preferred += previous.get("photos", [])
    preferred += [drive_id(x) for x in str(source.get("Danh sách ảnh") or "").splitlines()]
    preferred += [f["id"] for f in sorted(files, key=lambda f: (f["name"], f["id"]))]
    photos = list(dict.fromkeys(x for x in preferred if x in current))
    # Ảnh thumbnail lấy từ video vẫn là bìa hợp lệ của căn chỉ có video.
    poster = drive_id(source.get("Ảnh đại diện"))
    poster = poster if not photos and poster in videos else ""
    return {"folderId": source["folderId"], "source": source_key(row),
            "cover": photos[0] if photos else poster, "photos": photos, "poster": poster}


def scan(rows, sources, old, fetch_folder):
    work = {str(r.get("Mã nội bộ", "")).strip(): r for r in rows
            if str(r.get("Hiển thị trên Web", "")).strip().lower() in ("có", "co", "yes", "true", "1")
            and str(r.get("Mã nội bộ", "")).strip() in sources}
    if not 1 <= len(work) <= 400:
        raise ValueError("Số thư mục cần quét bất thường: " + str(len(work)))
    items = {k: v for k, v in old.get("items", {}).items() if k in work}
    revisions = dict(old.get("revisions", {}))
    errors = []
    folders = {sources[code]["folderId"] for code in work}
    results = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = {pool.submit(fetch_folder, folder): folder for folder in folders}
        for future in as_completed(pending):
            folder = pending[future]
            try:
                results[folder] = future.result()
            except Exception as error:
                errors.append(folder)
                print(f"::warning::Giữ ảnh cũ cho thư mục {folder}: {error}", flush=True)
            if (len(results) + len(errors)) % 50 == 0:
                print(f"Tiến độ: {len(results) + len(errors)}/{len(folders)} thư mục", flush=True)
    if len(errors) > max(3, len(folders) * .2):
        raise ValueError(f"Drive lỗi diện rộng: {len(errors)}/{len(folders)}; không ghi snapshot")
    for code, row in sorted(work.items()):
        source = sources[code]
        previous = items.get(code)
        if source["folderId"] not in results:
            # Không áp dụng ảnh của thư mục cũ cho căn vừa đổi thư mục.
            if previous and previous.get("folderId") != source["folderId"]:
                items.pop(code, None)
            continue
        files = results[source["folderId"]]
        item = build_item(row, source, files, previous)
        old_ids = set(previous["photos"]) if previous else set(source_key(row).split("|")) - {"", item["poster"]}
        new_ids = set(item["photos"])
        if old_ids != new_ids:
            print(f"{code}: {len(old_ids)} → {len(new_ids)} ảnh (+{len(new_ids-old_ids)}, -{len(old_ids-new_ids)})", flush=True)
        items[code] = item
        for f in files:
            observed = {"modified": f["modified"], "size": f["size"]}
            before = revisions.get(f["id"])
            revision = before.get("revision", "") if before else ""
            if before and any(before.get(k) != v for k, v in observed.items()):
                revision = hashlib.sha256(json.dumps(observed, sort_keys=True).encode()).hexdigest()[:12]
            revisions[f["id"]] = {**observed, "revision": revision}
    used = {ident for item in items.values() for ident in item["photos"] + [item["cover"]] if ident}
    print(f"Đã quét {len(folders)-len(errors)}/{len(folders)} thư mục; giữ ảnh cũ cho {len(errors)} thư mục lỗi.")
    return {"version": 1, "items": items, "revisions": {k: v for k, v in revisions.items() if k in used}}


def main():
    rows = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
    old = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"version": 1, "items": {}, "revisions": {}}
    sources = read_folders()
    result = scan(rows, sources, old, fetch_folder_with_retry)
    if result == old:
        print("Danh sách và phiên bản ảnh không đổi.")
        return
    temporary = MANIFEST.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary.replace(MANIFEST)
    print("Đã cập nhật anh-can-ho/nguon-anh.json; không sửa data.json.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)
