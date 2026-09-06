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

3. Sửa sitemap-can-ho.xml để <lastmod> phản ánh thay đổi THẬT của từng trang.
   sinh-trang-can.py phải dựng lại file mỗi lần chạy nên trước đây mọi URL đều
   bị gắn ngày hôm nay dù nội dung không đổi. Script lưu fingerprint của HTML
   (bỏ qua đúng ngày footer tự thay mỗi ngày); trang không đổi giữ lastmod cũ,
   trang đổi nội dung mới nhận ngày hiện tại.

4. Đồng bộ ngày ở footer trang chi tiết với lastmod thật. Nhờ vậy lần chạy tự
   động ngày hôm sau không tạo diff cho hàng trăm trang chỉ vì một con số ngày.

Không tạo URL mới, không dùng Indexing API, không fake <priority>. Google vẫn
quyết định crawl/index; mục tiêu ở đây là làm tín hiệu discovery, internal
links và freshness đáng tin hơn.

Chạy:  python3 scripts/noi-lien-ket-chi-tiet.py [--thu]
"""

import argparse
import datetime
import hashlib
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
DUONG_TRANG_THAI_CRAWL = os.path.join(THU_MUC_CAN_HO, "crawl-state.json")
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
RE_LASTMOD = re.compile(r'(<lastmod>)(\d{4}-\d{2}-\d{2})(</lastmod>)')

# Ngày duy nhất thay tự động mỗi lần chạy trên trang chi tiết là ngày trong
# footer. Bỏ nó khỏi fingerprint để một trang không đổi không giả vờ "mới".
RE_NGAY_FOOTER = re.compile(
    r'(<p>Cập nhật )(\d{2}/\d{2}/\d{4})( · <a href="/">Tìm căn hộ</a>)')

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


def doc_trang_thai_crawl():
    if not os.path.exists(DUONG_TRANG_THAI_CRAWL):
        return {"version": 1, "items": {}}
    try:
        with open(DUONG_TRANG_THAI_CRAWL, encoding="utf-8") as f:
            d = json.load(f)
        if d.get("version") == 1 and isinstance(d.get("items"), dict):
            return d
    except (OSError, ValueError, TypeError):
        pass
    return {"version": 1, "items": {}}


def fingerprint_trang(slug):
    """Hash HTML thật của trang, bỏ duy nhất ngày footer tự nhảy hàng ngày."""
    duong = os.path.join(THU_MUC_CAN_HO, slug, "index.html")
    if not os.path.exists(duong):
        return None
    with open(duong, encoding="utf-8") as f:
        noi_dung = f.read()
    chuan = RE_NGAY_FOOTER.sub(r'\1__LASTMOD__\3', noi_dung)
    return hashlib.sha256(chuan.encode("utf-8")).hexdigest()


def dong_bo_footer_lastmod(slug, lastmod, chi_thu):
    duong = os.path.join(THU_MUC_CAN_HO, slug, "index.html")
    if not os.path.exists(duong):
        return False
    hien_thi = ngay_hien_thi(lastmod)
    if not hien_thi:
        return False
    with open(duong, encoding="utf-8") as f:
        goc = f.read()
    moi = RE_NGAY_FOOTER.sub(lambda m: m.group(1) + hien_thi + m.group(3), goc, count=1)
    if moi == goc:
        return False
    if not chi_thu:
        with open(duong, "w", encoding="utf-8", newline="") as f:
            f.write(moi)
    return True


def toi_uu_sitemap_can_ho(chi_thu):
    """Giữ lastmod ổn định nếu HTML không đổi; đổi ngày khi fingerprint đổi."""
    if not os.path.exists(DUONG_SITEMAP_CAN_HO):
        return {"url": 0, "doi_lastmod": 0, "footer": 0, "state": False,
                "active_slugs": set()}

    with open(DUONG_SITEMAP_CAN_HO, encoding="utf-8") as f:
        goc = f.read()

    trang_thai_cu = doc_trang_thai_crawl()
    cu = trang_thai_cu.get("items", {})
    hom_nay = ngay_hom_nay()
    moi_state = {}
    doi_lastmod = 0
    doi_footer = 0
    active_slugs = set()

    def mot_khoi(m):
        nonlocal doi_lastmod, doi_footer
        khoi = m.group(0)
        mloc = RE_LOC.search(khoi)
        if not mloc:
            return khoi
        slug = slug_tu_loc(mloc.group(1).strip())
        if not slug:
            return khoi
        active_slugs.add(slug)

        fp = fingerprint_trang(slug)
        mlast = RE_LASTMOD.search(khoi)
        lastmod_hien_tai = mlast.group(2) if mlast else hom_nay
        ban_cu = cu.get(slug, {}) if isinstance(cu.get(slug, {}), dict) else {}
        fp_cu = ban_cu.get("hash")
        lm_cu = ban_cu.get("lastmod")

        if fp and fp_cu == fp and ngay_iso_hop_le(lm_cu):
            lastmod = lm_cu
        elif fp_cu is not None and fp and fp_cu != fp:
            lastmod = hom_nay
        elif ngay_iso_hop_le(lastmod_hien_tai):
            # Lần đầu cài state: giữ ngày sitemap hiện có thay vì giả vờ toàn
            # bộ URL vừa mới thay đổi chỉ vì vừa cài bộ tối ưu này.
            lastmod = lastmod_hien_tai
        else:
            lastmod = hom_nay

        if fp:
            moi_state[slug] = {"hash": fp, "lastmod": lastmod}

        if mlast and mlast.group(2) != lastmod:
            doi_lastmod += 1
            khoi = RE_LASTMOD.sub(
                lambda mm: mm.group(1) + lastmod + mm.group(3), khoi, count=1)

        if dong_bo_footer_lastmod(slug, lastmod, chi_thu):
            doi_footer += 1
        return khoi

    moi = RE_KHOI_URL.sub(mot_khoi, goc)
    state_moi = {"version": 1, "items": dict(sorted(moi_state.items()))}
    state_text = json.dumps(state_moi, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    state_cu_text = ""
    if os.path.exists(DUONG_TRANG_THAI_CRAWL):
        with open(DUONG_TRANG_THAI_CRAWL, encoding="utf-8") as f:
            state_cu_text = f.read()
    state_doi = state_text != state_cu_text

    if not chi_thu:
        if moi != goc:
            with open(DUONG_SITEMAP_CAN_HO, "w", encoding="utf-8", newline="") as f:
                f.write(moi)
        if state_doi:
            with open(DUONG_TRANG_THAI_CRAWL, "w", encoding="utf-8", newline="") as f:
                f.write(state_text)

    return {"url": len(active_slugs), "doi_lastmod": doi_lastmod,
            "footer": doi_footer, "state": state_doi,
            "active_slugs": active_slugs}


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

    crawl = toi_uu_sitemap_can_ho(tham_so.thu)
    hub_doi, hub_khoi = toi_uu_hub(crawl["active_slugs"], tham_so.thu)

    print()
    print("Trang lưới xử lý:    %d" % len(cac_trang))
    print("Thẻ quét:            %d" % thong_ke["the_quet"])
    print("Thẻ khớp trang CT:   %d" % thong_ke["the_khop"])
    print("Liên kết đã chèn:    %d" % thong_ke["lien_ket_chen"])
    print("Bỏ qua (đã có link): %d" % thong_ke["bo_qua_da_co"])
    print("Trang chi tiết được lưới trỏ tới: %d/%d" % (
        len(thong_ke["slug_duoc_tro"]), len(bang_tra)))
    print()
    print("Sitemap căn active:  %d URL" % crawl["url"])
    print("Lastmod đổi thật:     %d URL" % crawl["doi_lastmod"])
    print("Footer đồng bộ:       %d trang" % crawl["footer"])
    print("Crawl state thay đổi: %s" % ("có" if crawl["state"] else "không"))
    print("Hub gỡ khối đã thuê:  %s" % ("có" if hub_khoi else "không"))

    if tham_so.thu:
        print("\n(--thu: chưa ghi file nào; %d trang lưới sẽ đổi, hub=%s)" % (
            da_doi, "đổi" if hub_doi else "không đổi"))
    else:
        print("\nĐã tối ưu crawl graph cho trang căn hộ.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
