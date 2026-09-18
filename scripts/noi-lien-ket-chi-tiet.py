#!/usr/bin/env python3
"""Tăng độ ưu tiên crawl cho các trang chi tiết căn hộ.

Script chạy SAU sinh-trang-can.py và các generator lưới. Nó làm 4 việc:

1. Bọc tiêu đề mọi thẻ căn tĩnh bằng liên kết thật /can-ho/{slug}/. Phạm vi
   gồm các trang danh mục/tòa (section.luoi) VÀ khối 16 căn dựng sẵn trên
   trang chủ (#listingGrid). JavaScript vốn đã có link này; bước này làm HTML
   thô mà Googlebot đọc được cũng có đúng liên kết như trình duyệt.

2. Giữ /can-ho/ làm crawl hub chỉ trỏ tới các căn ĐANG hoạt động. Các URL đã
   có khách vẫn giữ 200 + noindex,follow để không gãy backlink, nhưng không
   còn nằm trong danh sách hub khiến bot tốn lượt crawl vào trang noindex.

3. Lấy danh sách căn ĐANG hoạt động trực tiếp từ sitemap-can-ho.xml để lọc
   /can-ho/ hub. Script này KHÔNG còn ghi lastmod hay crawl-state. Quyền sở hữu
   freshness thuộc duy nhất scripts/cap-nhat-sitemap.mjs, tránh hai workflow
   tính fingerprint ở hai thời điểm khác nhau rồi tự ghi đè state của nhau.

Không tạo URL mới, không dùng Indexing API, không fake <priority>. Google vẫn
quyết định crawl/index; mục tiêu ở đây là làm discovery/internal links sạch,
deterministic và không tạo commit giả.

Chạy:  python3 scripts/noi-lien-ket-chi-tiet.py [--thu]
"""

import argparse
import html
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_CAN_HO = os.path.join(GOC, "can-ho")
DUONG_DANH_SACH_TRANG = os.path.join(THU_MUC_CAN_HO, "danh-sach-trang.json")
DUONG_HUB = os.path.join(THU_MUC_CAN_HO, "index.html")
DUONG_SITEMAP_CAN_HO = os.path.join(GOC, "sitemap-can-ho.xml")
TEN_MIEN = "https://timthuesmartcity.com"

BO_QUA_THU_MUC = {".git", ".github", "node_modules", "images", "scripts",
                  "anh-can-ho", "can-ho"}

# Neo vào data-ma-noi-bo để bắt đúng từng thẻ căn, không neo vào khoảng trắng.
RE_THE = re.compile(
    r'<article class="the[^"]*"[^>]*\bdata-ma-noi-bo="([^"]*)"[^>]*>.*?</article>',
    re.S)
RE_TEN = re.compile(r'(<h3 class="ten">)(.*?)(</h3>)', re.S)

# Sitemap-can-ho.xml hiện được sinh một <url> trên một dòng nhưng regex vẫn
# chịu được xuống dòng để không phụ thuộc cách format sau này.
RE_KHOI_URL = re.compile(r'<url>[\s\S]*?</url>')
RE_LOC = re.compile(r'<loc>([^<]+)</loc>')
# Khối lịch sử đã có khách trên /can-ho/. Chỉ gỡ khỏi HUB; bản thân URL vẫn
# tồn tại 200 + noindex,follow và vẫn gợi ý sang căn còn trống.
RE_KHOI_DA_CO_KHACH = re.compile(
    r'\n\s*<h2 style="font-size:19px">Đã có khách</h2>\s*'
    r'<ul class="ds-can-ho">[\s\S]*?</ul>',
    re.S)
RE_JSON_LD = re.compile(r'(<script type="application/ld\+json">)([\s\S]*?)(</script>)')


def esc(v):
    return html.escape("" if v is None else str(v), quote=True)


def ngay_hom_nay():
    return (datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=7)).date().isoformat()


def ngay_hien_thi(iso):
    try:
        return datetime.date.fromisoformat(iso).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return ""


def ngay_iso_hop_le(v):
    try:
        datetime.date.fromisoformat(str(v))
        return True
    except (TypeError, ValueError):
        return False


def doc_bang_tra():
    """can-ho/danh-sach-trang.json: slug -> {ma, ...} — đảo thành ma -> slug."""
    with open(DUONG_DANH_SACH_TRANG, encoding="utf-8") as f:
        ds = json.load(f)
    bang = {}
    for slug, thong_tin in ds.items():
        ma = str((thong_tin or {}).get("ma", "")).strip()
        if ma:
            bang[ma] = slug
    return bang, ds


def tim_trang_can_xu_ly():
    """Quét mọi lưới căn tĩnh, gồm danh mục/tòa và 16 card ở trang chủ."""
    ra = []
    for thu_muc, cac_thu_muc, cac_file in os.walk(GOC):
        cac_thu_muc[:] = [d for d in cac_thu_muc
                          if d not in BO_QUA_THU_MUC and not d.startswith(".")]
        for ten in cac_file:
            if ten != "index.html":
                continue
            duong = os.path.join(thu_muc, ten)
            with open(duong, encoding="utf-8") as f:
                noi_dung = f.read()
            if 'class="luoi"' in noi_dung or 'id="listingGrid"' in noi_dung:
                ra.append(duong)
    return sorted(ra)


def xu_ly_mot_trang(duong, bang_tra, thong_ke):
    """Bọc <a> quanh h3.ten của mọi thẻ khớp bảng tra."""
    with open(duong, encoding="utf-8") as f:
        goc = f.read()

    def mot_the(m):
        ma = m.group(1)
        khoi = m.group(0)
        thong_ke["the_quet"] += 1

        slug = bang_tra.get(ma)
        if not slug:
            return khoi
        thong_ke["the_khop"] += 1
        thong_ke["slug_duoc_tro"].add(slug)

        def mot_ten(m2):
            mo, noi_dung, dong = m2.group(1), m2.group(2), m2.group(3)
            if "<a" in noi_dung:
                thong_ke["bo_qua_da_co"] += 1
                return m2.group(0)
            thong_ke["lien_ket_chen"] += 1
            return (mo + '<a href="/can-ho/%s/">' % esc(slug)
                    + noi_dung + "</a>" + dong)

        return RE_TEN.sub(mot_ten, khoi, count=1)

    moi = RE_THE.sub(mot_the, goc)
    return moi, moi != goc


def slug_tu_loc(loc):
    tien_to = TEN_MIEN + "/can-ho/"
    if not loc.startswith(tien_to) or loc == tien_to:
        return None
    duoi = loc[len(tien_to):].strip("/")
    if not duoi or "/" in duoi:
        return None
    return duoi


def doc_active_slugs_sitemap():
    """Đọc đúng các URL căn active mà sitemap-can-ho.xml đang publish.

    lastmod được quản lý ở cap-nhat-sitemap.mjs. Hàm này chỉ đọc sitemap để
    /can-ho/ hub không giữ link tới các trang đã noindex/hết hàng.
    """
    if not os.path.exists(DUONG_SITEMAP_CAN_HO):
        return set()

    with open(DUONG_SITEMAP_CAN_HO, encoding="utf-8") as f:
        noi_dung = f.read()

    active = set()
    for khoi in RE_KHOI_URL.findall(noi_dung):
        mloc = RE_LOC.search(khoi)
        if not mloc:
            continue
        slug = slug_tu_loc(mloc.group(1).strip())
        if slug:
            active.add(slug)
    return active

def toi_uu_hub(active_slugs, chi_thu):
    """Gỡ link tới URL noindex khỏi /can-ho/ và lọc ItemList về căn active."""
    if not os.path.exists(DUONG_HUB):
        return False, 0
    with open(DUONG_HUB, encoding="utf-8") as f:
        goc = f.read()

    moi, so_khoi = RE_KHOI_DA_CO_KHACH.subn("", goc, count=1)

    def sua_json_ld(m):
        try:
            d = json.loads(m.group(2))
        except (ValueError, TypeError):
            return m.group(0)
        if not isinstance(d, dict) or d.get("@type") != "ItemList":
            return m.group(0)
        ds_moi = []
        for item in d.get("itemListElement", []):
            if not isinstance(item, dict):
                continue
            slug = slug_tu_loc(str(item.get("url", "")))
            if slug in active_slugs:
                item = dict(item)
                item["position"] = len(ds_moi) + 1
                ds_moi.append(item)
        d["numberOfItems"] = len(ds_moi)
        d["itemListElement"] = ds_moi
        return m.group(1) + json.dumps(
            d, ensure_ascii=False, separators=(",", ":")) + m.group(3)

    moi = RE_JSON_LD.sub(sua_json_ld, moi)
    co_doi = moi != goc
    if co_doi and not chi_thu:
        with open(DUONG_HUB, "w", encoding="utf-8", newline="") as f:
            f.write(moi)
    return co_doi, so_khoi


def main():
    bo_phan_tich = argparse.ArgumentParser(
        description="Tăng internal links và tín hiệu crawl cho trang căn hộ.")
    bo_phan_tich.add_argument("--thu", action="store_true",
                              help="chỉ in bảng nghiệm thu, không ghi file")
    tham_so = bo_phan_tich.parse_args()

    bang_tra, ds_trang = doc_bang_tra()
    print("can-ho/danh-sach-trang.json: %d mục, %d mã hợp lệ." % (
        len(ds_trang), len(bang_tra)))

    cac_trang = tim_trang_can_xu_ly()
    thong_ke = {
        "the_quet": 0,
        "the_khop": 0,
        "lien_ket_chen": 0,
        "bo_qua_da_co": 0,
        "slug_duoc_tro": set(),
    }

    da_doi = 0
    for duong in cac_trang:
        moi, co_doi = xu_ly_mot_trang(duong, bang_tra, thong_ke)
        if co_doi:
            da_doi += 1
            if not tham_so.thu:
                with open(duong, "w", encoding="utf-8", newline="") as f:
                    f.write(moi)

    active_slugs = doc_active_slugs_sitemap()
    hub_doi, hub_khoi = toi_uu_hub(active_slugs, tham_so.thu)

    print()
    print("Trang lưới xử lý:    %d" % len(cac_trang))
    print("Thẻ quét:            %d" % thong_ke["the_quet"])
    print("Thẻ khớp trang CT:   %d" % thong_ke["the_khop"])
    print("Liên kết đã chèn:    %d" % thong_ke["lien_ket_chen"])
    print("Bỏ qua (đã có link): %d" % thong_ke["bo_qua_da_co"])
    print("Trang chi tiết được lưới trỏ tới: %d/%d" % (
        len(thong_ke["slug_duoc_tro"]), len(bang_tra)))
    print()
    print("Sitemap căn active:  %d URL" % len(active_slugs))
    print("Lastmod/crawl-state:  do cap-nhat-sitemap.mjs quản lý (script này chỉ đọc)")
    print("Hub gỡ khối đã thuê: %s" % ("có" if hub_khoi else "không"))

    if tham_so.thu:
        print("\n(--thu: chưa ghi file nào; %d trang lưới sẽ đổi, hub=%s)" % (
            da_doi, "đổi" if hub_doi else "không đổi"))
    else:
        print("\nĐã tối ưu crawl graph cho trang căn hộ.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
