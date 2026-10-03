#!/usr/bin/env python3
"""Quét thư mục ảnh công khai của quỹ căn Lumi Hanoi.

Chỉ đọc data-lumi.json đã được lọc sạch. Không đọc/ghi tên chủ nhà, số điện
thoại, pass cửa hay nguồn nội bộ. Khi Drive lỗi, giữ nguyên album gần nhất.
"""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data-lumi.json"
DRIVE_ID = re.compile(r"^[A-Za-z0-9_-]{10,}$")


def text(v):
    return str(v or "").strip()


def folder_id(url):
    m = re.search(
        r"https://drive\.google\.com/(?:drive/(?:u/\d+/)?folders/|open\?id=)([A-Za-z0-9_-]+)",
        text(url),
    )
    return m.group(1) if m else ""


def get_text(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=25) as response:
        return response.read(8_000_001).decode("utf-8")


def parse_folder(html, fid):
    if len(html) > 8_000_000:
        raise ValueError("Drive response quá lớn")
    match = re.search(r"window\['_DRIVE_ivd'\]\s*=\s*'((?:\\.|[^'\\])*)'", html)
    if not match:
        raise ValueError("Không đọc được dữ liệu thư mục công khai")
    escaped = re.sub(r"\\x([0-9a-fA-F]{2})", r"\\u00\1", match.group(1)).replace("\\'", "'")
    data = json.loads(json.loads('"' + escaped + '"'))
    if (not isinstance(data, list) or len(data) != 6 or data[5] != 1
            or not isinstance(data[0], list) or fid not in json.dumps(data[4])):
        raise ValueError("Cấu trúc Drive thay đổi")
    if len(data[0]) >= 100:
        raise ValueError("Thư mục có thể bị phân trang; dừng để không mất ảnh")
    out = []
    for row in data[0]:
        if not isinstance(row, list) or len(row) < 4:
            continue
        ident = row[0] if isinstance(row[0], str) else ""
        mime = row[3] if isinstance(row[3], str) else ""
        if not DRIVE_ID.fullmatch(ident):
            continue
        if mime == "application/vnd.google-apps.folder":
            raise ValueError("Có thư mục con; chưa quét đệ quy")
        if mime.startswith("image/"):
            out.append(ident)
    return list(dict.fromkeys(out))


def thumb(ident):
    return "https://drive.google.com/thumbnail?id=%s&sz=w1000" % ident


def main():
    rows = json.loads(DATA.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("data-lumi.json không phải mảng")

    work = {}
    for i, row in enumerate(rows):
        if text(row.get("Hiển thị trên Web")).lower() != "có":
            continue
        fid = folder_id(row.get("Ảnh thư mục"))
        if fid:
            work.setdefault(fid, []).append(i)

    if not work:
        print("Chưa có thư mục ảnh Lumi công khai; giữ nguyên data-lumi.json.")
        return 0
    if len(work) > 200:
        raise ValueError("Số thư mục Lumi bất thường: %d" % len(work))

    results, errors = {}, {}
    with ThreadPoolExecutor(max_workers=min(8, len(work))) as pool:
        pending = {
            pool.submit(parse_folder, get_text("https://drive.google.com/drive/folders/" + fid), fid): fid
            for fid in work
        }
        for future in as_completed(pending):
            fid = pending[future]
            try:
                results[fid] = future.result()
            except Exception as error:
                errors[fid] = str(error)
                print("::warning::Giữ album Lumi cũ cho %s: %s" % (fid, error), flush=True)

    if len(errors) > max(2, int(len(work) * .4)):
        raise ValueError("Drive lỗi diện rộng: %d/%d thư mục" % (len(errors), len(work)))

    changed = 0
    for fid, indices in work.items():
        if fid not in results:
            continue
        ids = results[fid]
        cover = thumb(ids[0]) if ids else ""
        gallery = "\n".join(thumb(x) for x in ids)
        for i in indices:
            row = rows[i]
            if text(row.get("Ảnh đại diện")) != cover or text(row.get("Danh sách ảnh")) != gallery:
                row["Ảnh đại diện"] = cover
                row["Danh sách ảnh"] = gallery
                changed += 1

    if changed:
        tmp = DATA.with_suffix(".tmp")
        tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(DATA)
        print("Đã cập nhật ảnh cho %d bản ghi Lumi từ %d thư mục." % (changed, len(results)))
    else:
        print("Ảnh Lumi không đổi; đã kiểm tra %d/%d thư mục." % (len(results), len(work)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("::error::%s" % error, file=sys.stderr)
        sys.exit(1)
