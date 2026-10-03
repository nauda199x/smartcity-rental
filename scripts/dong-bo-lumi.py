#!/usr/bin/env python3
"""Đồng bộ quỹ căn Lumi từ Google Sheet qua XLSX export.

Lý do dùng XLSX thay GViz:
- giữ đủ cả các hàng đang ẩn/lọc trong Sheet;
- giữ hyperlink thật của ô "ảnh";
- chỉ xuất ra data-lumi.json các trường public, không ghi PII/nội bộ.
"""
import io
import json
import re
import sys
import unicodedata
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data-lumi.json"
SHEET_ID = "1Buw_vjB_2x8KExje34lqmJKEFzCUM79LOmcvCVWw-yQ"
EXPORT_URL = "https://docs.google.com/spreadsheets/d/%s/export?format=xlsx" % SHEET_ID
DRY = "--thu" in sys.argv or "--dry-run" in sys.argv

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

TABS = {
    "THUÊ 1PN": {"type": "1 Ngủ", "code": "1N", "special": False},
    "THUÊ 2PN": {"type": "2 Ngủ", "code": "2N", "special": False},
    "THUÊ 3PN": {"type": "3 Ngủ", "code": "3N", "special": False},
    "THUÊ DUPLEX": {"type": "Duplex", "code": "DUPLEX", "special": True},
    "THUÊ PENTHOUSE": {"type": "Penthouse", "code": "PENTHOUSE", "special": True},
    "THUÊ SHOP": {"type": "Shop", "code": "SHOP", "special": True},
}


def txt(v):
    return str(v if v is not None else "").strip()


def key(v):
    return txt(v).lower()


def deaccent(v):
    s = unicodedata.normalize("NFD", txt(v))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


def money(v):
    if isinstance(v, (int, float)):
        return int(round(v))
    s = re.sub(r"[^\d]", "", txt(v))
    return int(s or 0)


def area(v):
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d.]", "", txt(v).replace(",", "."))
    try:
        return float(s)
    except ValueError:
        return 0.0


def pad_area(v):
    n = area(v)
    if n.is_integer():
        return str(int(n))
    return ("%g" % n).replace(".", "_")


def today_vn():
    d = datetime.now(timezone.utc) + timedelta(hours=7)
    return d.strftime("%d/%m/%Y")


def excel_date(v):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return txt(v)
    if n < 20000 or n > 100000:
        return txt(v)
    d = datetime(1899, 12, 30) + timedelta(days=n)
    return d.strftime("%d/%m/%Y")


def normalize_date(v):
    s = txt(v)
    if not s:
        return ""
    if re.fullmatch(r"\d+(?:\.\d+)?", s):
        return excel_date(s)
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", s)
    if m:
        return "%02d/%02d/%04d" % (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(r"\b(\d{1,2})/(\d{1,2})\b", s)
    if m:
        y = (datetime.now(timezone.utc) + timedelta(hours=7)).year
        return "%02d/%02d/%04d" % (int(m.group(1)), int(m.group(2)), y)
    return s


def inactive(note):
    s = re.sub(r"\s+", " ", deaccent(note))
    return bool(re.search(r"cho thue roi|da cho thue|da thue|da coc|chot thue|khong cho thue|dung thue", s))


def public_move(move, note):
    direct = txt(move)
    if direct:
        return normalize_date(direct)
    raw = txt(note)
    s = deaccent(raw)
    if re.search(r"vao o dc luon|vao o duoc luon|vao luon|cho thue luon|nha trong.*vao luon", s):
        return ""
    m = re.search(r"\b\d{1,2}\s*[-–]\s*\d{1,2}/\d{1,2}\b", raw)
    if m:
        return m.group(0)
    m = re.search(r"\b\d{1,2}/\d{1,2}(?:/\d{4})?\b", raw)
    if m and re.search(r"nhan nha|vao|trong", s):
        return normalize_date(m.group(0))
    m = re.search(r"tháng\s+\d{1,2}", raw, re.I)
    if m and re.search(r"nhan nha|vao", s):
        return m.group(0)
    return "Chưa xác nhận"


def col_index(ref):
    letters = re.match(r"([A-Z]+)", ref or "")
    if not letters:
        return 0
    n = 0
    for c in letters.group(1):
        n = n * 26 + (ord(c) - 64)
    return n


def cell_text(cell, shared):
    t = cell.get("t")
    if t == "inlineStr":
        return "".join(x.text or "" for x in cell.findall(".//{%s}t" % NS_MAIN))
    v = cell.find("{%s}v" % NS_MAIN)
    raw = "" if v is None else (v.text or "")
    if t == "s":
        try:
            return shared[int(raw)]
        except Exception:
            return ""
    if t == "str":
        return raw
    return raw


def read_shared(z):
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    out = []
    for si in root.findall("{%s}si" % NS_MAIN):
        out.append("".join(x.text or "" for x in si.findall(".//{%s}t" % NS_MAIN)))
    return out


def rel_map(z, path):
    if path not in z.namelist():
        return {}
    root = ET.fromstring(z.read(path))
    out = {}
    for rel in root.findall("{%s}Relationship" % NS_PKG_REL):
        out[rel.get("Id")] = rel.get("Target", "")
    return out


def workbook_sheets(z):
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = rel_map(z, "xl/_rels/workbook.xml.rels")
    out = {}
    for sh in wb.findall(".//{%s}sheet" % NS_MAIN):
        name = sh.get("name", "")
        rid = sh.get("{%s}id" % NS_REL)
        target = rels.get(rid, "")
        if target.startswith("/"):
            path = target.lstrip("/")
        else:
            path = "xl/" + target.lstrip("/")
        out[name] = path
    return out


def sheet_rows(z, path, shared):
    root = ET.fromstring(z.read(path))
    rel_path = str(Path(path).parent / "_rels" / (Path(path).name + ".rels")).replace("\\", "/")
    rels = rel_map(z, rel_path)
    hyperlinks = {}
    for node in root.findall(".//{%s}hyperlink" % NS_MAIN):
        ref = node.get("ref", "")
        rid = node.get("{%s}id" % NS_REL)
        target = rels.get(rid, "")
        if target:
            hyperlinks[ref] = target

    rows = {}
    for row in root.findall(".//{%s}row" % NS_MAIN):
        rn = int(row.get("r", "0") or 0)
        values = {}
        for cell in row.findall("{%s}c" % NS_MAIN):
            ref = cell.get("r", "")
            ci = col_index(ref)
            values[ci] = cell_text(cell, shared)
        rows[rn] = values
    return rows, hyperlinks


def internal_id(spec, code, area_value):
    return "LH.%s.%s.%s" % (
        spec["code"],
        re.sub(r"\s+", "", txt(code)),
        pad_area(area_value),
    )


def source_from_sheet(name, spec, rows, hyperlinks):
    out = []
    for rn in sorted(rows):
        if rn <= 5:
            continue
        c = rows[rn]
        tower = txt(c.get(4))
        code = txt(c.get(5))
        direction = txt(c.get(6))
        ar = area(c.get(7))
        if spec["special"]:
            price = money(c.get(9))
            interior = txt(c.get(10))
            updated = normalize_date(c.get(12))
            note = txt(c.get(14))
            move = txt(c.get(16))
            image_col = "M"
        else:
            price = money(c.get(8))
            interior = txt(c.get(9))
            updated = normalize_date(c.get(11))
            note = txt(c.get(13))
            move = txt(c.get(15))
            image_col = "L"

        if not tower and not code and not ar and not price:
            continue
        if deaccent(code) == "ma can" or deaccent(tower) == "toa":
            continue
        if not code:
            continue

        href = hyperlinks.get("%s%d" % (image_col, rn), "")
        ident = internal_id(spec, code, ar)
        complete = bool(tower and code and ar > 0 and price > 0)
        show = complete and not inactive(note)
        out.append({
            "id": ident, "code": code, "tower": tower, "type": spec["type"],
            "area": ar, "price": price, "interior": interior, "direction": direction,
            "updated": updated, "move": public_move(move, note), "folder": href,
            "show": show,
        })
    return out


def load_source():
    req = Request(EXPORT_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=40) as response:
        body = response.read(30_000_001)
    if len(body) > 30_000_000:
        raise ValueError("XLSX Lumi quá lớn; dừng an toàn")

    z = zipfile.ZipFile(io.BytesIO(body))
    shared = read_shared(z)
    sheets = workbook_sheets(z)
    all_rows = []
    tab_stat = {}

    for name, spec in TABS.items():
        path = sheets.get(name)
        if not path:
            raise ValueError("Không tìm thấy tab XLSX: " + name)
        rows, hyperlinks = sheet_rows(z, path, shared)
        parsed = source_from_sheet(name, spec, rows, hyperlinks)
        all_rows.extend(parsed)
        tab_stat[name] = {
            "rows": len(parsed),
            "active": sum(1 for x in parsed if x["show"]),
            "folders": sum(1 for x in parsed if x["folder"]),
        }

    ids = [x["id"] for x in all_rows]
    dup = sorted({x for x in ids if ids.count(x) > 1})
    if dup:
        raise ValueError("ID Lumi trùng trong nguồn XLSX: " + ", ".join(dup))
    if len(all_rows) < 10 or len(all_rows) > 300:
        raise ValueError("Số dòng Lumi bất thường: %d" % len(all_rows))

    return all_rows, tab_stat


def sync(old, source):
    # Dọn đúng dòng header rác lịch sử; căn cũ hợp lệ vẫn được giữ để URL không chết.
    next_rows = [dict(r) for r in old if deaccent(r.get("Mã căn")) != "ma can"]
    by_id = {txt(r.get("Mã nội bộ")): i for i, r in enumerate(next_rows)}
    touched = set()
    stat = {"updated": 0, "added": 0, "on": 0, "off": 0, "missing": 0}

    for src in source:
        pos = by_id.get(src["id"])
        if pos is None:
            # Migration fallback nếu ID lịch sử khác nhưng cùng loại+mã+diện tích.
            for i, r in enumerate(next_rows):
                if (txt(r.get("Mã căn")) == src["code"] and
                        key(r.get("Loại")) == key(src["type"]) and
                        abs(area(r.get("Diện tích")) - src["area"]) < .01):
                    pos = i
                    break

        payload = {
            "Mã nội bộ": src["id"], "Mã căn": src["code"], "Tòa": src["tower"],
            "Loại": src["type"], "Diện tích": src["area"], "Nội thất": src["interior"],
            "Giá thuê": src["price"], "Hướng ban công": src["direction"],
            "Ngày vào ở": src["move"], "Ngày cập nhật": src["updated"],
            "Hiển thị trên Web": "Có" if src["show"] else "Không",
        }

        if pos is None:
            row = dict(payload)
            row["Ngày thêm vào hệ thống"] = src["updated"] or today_vn()
            row["Ảnh thư mục"] = src["folder"]
            row["Ảnh đại diện"] = ""
            row["Danh sách ảnh"] = ""
            next_rows.append(row)
            pos = len(next_rows) - 1
            by_id[src["id"]] = pos
            stat["added"] += 1
            stat["on" if src["show"] else "off"] += 1
        else:
            row = next_rows[pos]
            was = key(row.get("Hiển thị trên Web")) == "có"
            row.update(payload)
            if not txt(row.get("Ngày thêm vào hệ thống")):
                row["Ngày thêm vào hệ thống"] = src["updated"] or today_vn()
            # XLSX hyperlink là nguồn sự thật; nếu ô không còn link thì xóa folder.
            row["Ảnh thư mục"] = src["folder"]
            row.setdefault("Ảnh đại diện", "")
            row.setdefault("Danh sách ảnh", "")
            stat["updated"] += 1
            if not was and src["show"]:
                stat["on"] += 1
            if was and not src["show"]:
                stat["off"] += 1

        touched.add(pos)

    for i, row in enumerate(next_rows):
        if i in touched:
            continue
        if not txt(row.get("Mã nội bộ")).startswith("LH."):
            continue
        if key(row.get("Hiển thị trên Web")) == "có":
            row["Hiển thị trên Web"] = "Không"
            stat["missing"] += 1

    return next_rows, stat


def main():
    old = json.loads(DATA.read_text(encoding="utf-8"))
    if not isinstance(old, list):
        raise ValueError("data-lumi.json không phải mảng")

    source, tabs = load_source()
    result, stat = sync(old, source)
    active_count = sum(1 for x in source if x["show"])
    folder_count = sum(1 for x in source if x["folder"])

    print("Lumi XLSX: %d dòng nguồn, %d căn active, %d folder ảnh." %
          (len(source), active_count, folder_count))
    for name, st in tabs.items():
        print("  %s: %d dòng, %d active, %d folder" %
              (name, st["rows"], st["active"], st["folders"]))
    print("Đối chiếu: cập nhật %(updated)d, thêm %(added)d, bật %(on)d, "
          "tắt %(off)d, tắt vì rời nguồn %(missing)d." % stat)

    after = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    before = DATA.read_text(encoding="utf-8")
    if before == after:
        print("data-lumi.json đã khớp Google Sheet XLSX.")
        return
    if not DRY:
        DATA.write_text(after, encoding="utf-8")
    print("Chế độ --thu: không ghi file." if DRY else
          "Đã ghi data-lumi.json (%d dòng)." % len(result))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("::error::%s" % error, file=sys.stderr)
        sys.exit(1)
