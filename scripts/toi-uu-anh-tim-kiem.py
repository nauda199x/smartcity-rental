#!/usr/bin/env python3
"""Khai báo ảnh ưu tiên để Google có đủ tín hiệu dựng thumbnail kết quả tìm kiếm.

Google tự quyết định có hiển thị ảnh cạnh kết quả hay không. Phần website có
thể làm là:
  1. cho phép ảnh xem trước cỡ lớn bằng ``max-image-preview:large``;
  2. chỉ rõ ảnh đại diện của từng URL bằng ``WebPage.primaryImageOfPage``;
  3. giữ ảnh đó đồng nhất với ``og:image`` đã được từng trang lựa chọn.

Repo có nhiều generator dựng lại HTML từ data.json mỗi ngày, vì vậy đây là
bước hậu xử lý cuối workflow thay vì sửa tay hàng trăm trang. Script bỏ qua
mọi trang ``noindex`` và có marker riêng để chạy lặp lại không sinh bản trùng.

Chạy:
  python3 scripts/toi-uu-anh-tim-kiem.py          # cập nhật HTML
  python3 scripts/toi-uu-anh-tim-kiem.py --thu    # xem trước, không ghi
  python3 scripts/toi-uu-anh-tim-kiem.py --kiem-tra
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse


GOC = Path(__file__).resolve().parent.parent
TEN_MIEN = "https://timthuesmartcity.com"
ANH_MAC_DINH = f"{TEN_MIEN}/og-smartcity.jpg"

MOC_BAT_DAU = "<!-- GOOGLE-IMAGE-PREVIEW:BAT-DAU -->"
MOC_KET_THUC = "<!-- GOOGLE-IMAGE-PREVIEW:KET-THUC -->"
RE_KHOI = re.compile(
    re.escape(MOC_BAT_DAU) + r"[\s\S]*?" + re.escape(MOC_KET_THUC), re.I
)
RE_HEAD_DONG = re.compile(r"</head\s*>", re.I)
RE_META = re.compile(r"<meta\b[^>]*>", re.I)
RE_LINK = re.compile(r"<link\b[^>]*>", re.I)
RE_TITLE = re.compile(r"<title\b[^>]*>([\s\S]*?)</title\s*>", re.I)
RE_ATTR = re.compile(
    r"(?P<ten>[\w:-]+)\s*=\s*(?P<quote>[\"'])(?P<gia_tri>[\s\S]*?)(?P=quote)",
    re.I,
)


def thuoc_tinh(the: str, ten: str) -> str | None:
    """Lấy một thuộc tính HTML không phụ thuộc thứ tự hoặc kiểu dấu nháy."""
    ten = ten.lower()
    for khop in RE_ATTR.finditer(the):
        if khop.group("ten").lower() == ten:
            return html.unescape(khop.group("gia_tri").strip())
    return None


def tim_meta(noi_dung: str, *, name: str | None = None,
             property_name: str | None = None) -> tuple[re.Match[str], str] | None:
    for khop in RE_META.finditer(noi_dung):
        the = khop.group(0)
        if name is not None and (thuoc_tinh(the, "name") or "").lower() != name.lower():
            continue
        if (property_name is not None
                and (thuoc_tinh(the, "property") or "").lower() != property_name.lower()):
            continue
        return khop, the
    return None


def tim_canonical(noi_dung: str) -> str | None:
    for khop in RE_LINK.finditer(noi_dung):
        the = khop.group(0)
        rel = (thuoc_tinh(the, "rel") or "").lower().split()
        if "canonical" in rel:
            return thuoc_tinh(the, "href")
    return None


def la_noindex(noi_dung: str) -> bool:
    """Chỉ đọc directive robots/googlebot, không bắt nhầm chữ trong nội dung."""
    for khop in RE_META.finditer(noi_dung):
        the = khop.group(0)
        ten = (thuoc_tinh(the, "name") or "").lower()
        if ten not in {"robots", "googlebot"}:
            continue
        chi_thi = (thuoc_tinh(the, "content") or "").lower()
        cac_lenh = {x.strip() for x in chi_thi.split(",")}
        if "noindex" in cac_lenh or "none" in cac_lenh:
            return True
    return False


def thanh_url_tuyet_doi(url: str | None) -> str | None:
    if not url:
        return None
    url = html.unescape(url.strip())
    if url.startswith("data:") or url.startswith("blob:"):
        return None
    tuyet_doi = urljoin(TEN_MIEN + "/", url)
    parsed = urlparse(tuyet_doi)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return tuyet_doi


def tim_anh_uu_tien(noi_dung: str) -> str:
    """og:image là nguồn lựa chọn có chủ đích hiện tại của từng trang."""
    ket_qua = tim_meta(noi_dung, property_name="og:image")
    if ket_qua:
        anh = thanh_url_tuyet_doi(thuoc_tinh(ket_qua[1], "content"))
        if anh:
            return anh
    return ANH_MAC_DINH


def tim_tieu_de(noi_dung: str) -> str:
    khop = RE_TITLE.search(noi_dung)
    if not khop:
        return "Tìm Thuê Smart City"
    # Title của site không chứa markup, nhưng gỡ tag để script vẫn an toàn nếu
    # một generator sau này vô tình chèn thẻ nhấn mạnh vào đây.
    tieu_de = re.sub(r"<[^>]+>", " ", khop.group(1))
    return re.sub(r"\s+", " ", html.unescape(tieu_de)).strip() or "Tìm Thuê Smart City"


def them_quyen_xem_truoc(noi_dung: str) -> tuple[str, bool]:
    """Thêm/nâng max-image-preview vào thẻ robots hiện có hoặc tạo thẻ mới."""
    ket_qua = tim_meta(noi_dung, name="robots")
    if not ket_qua:
        khop_head = RE_HEAD_DONG.search(noi_dung)
        if not khop_head:
            return noi_dung, False
        the_moi = '<meta name="robots" content="max-image-preview:large">\n'
        return noi_dung[:khop_head.start()] + the_moi + noi_dung[khop_head.start():], True

    khop, the = ket_qua
    content = thuoc_tinh(the, "content") or ""
    lenh = [x.strip() for x in content.split(",") if x.strip()]
    moi = []
    da_co = False
    for muc in lenh:
        if muc.lower().startswith("max-image-preview:"):
            da_co = True
            moi.append("max-image-preview:large")
        else:
            moi.append(muc)
    if not da_co:
        moi.append("max-image-preview:large")
    content_moi = ", ".join(moi)
    if content_moi == content:
        return noi_dung, False

    def thay_content(khop_attr: re.Match[str]) -> str:
        quote = khop_attr.group("quote")
        return f'content={quote}{html.escape(content_moi, quote=True)}{quote}'

    re_content = re.compile(
        r"content\s*=\s*(?P<quote>[\"'])(?P<gia_tri>[\s\S]*?)(?P=quote)", re.I
    )
    if re_content.search(the):
        the_moi = re_content.sub(thay_content, the, count=1)
    else:
        the_moi = the[:-1] + f' content="{html.escape(content_moi, quote=True)}">'
    return noi_dung[:khop.start()] + the_moi + noi_dung[khop.end():], True


def dung_khoi_schema(canonical: str, anh: str, tieu_de: str) -> str:
    du_lieu = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": canonical + "#webpage",
        "url": canonical,
        "name": tieu_de,
        "primaryImageOfPage": {
            "@type": "ImageObject",
            "@id": anh + "#primaryimage",
            "url": anh,
            "contentUrl": anh,
            "caption": tieu_de,
            "representativeOfPage": True,
        },
        "thumbnailUrl": anh,
    }
    json_ld = json.dumps(du_lieu, ensure_ascii=False, separators=(",", ":"))
    # Không cho một title bất thường đóng thẻ script sớm.
    json_ld = json_ld.replace("</", "<\\/")
    return (
        f'{MOC_BAT_DAU}\n'
        f'<script type="application/ld+json" id="google-image-preview-data">'
        f'{json_ld}</script>\n'
        f'{MOC_KET_THUC}'
    )


def toi_uu_mot_trang(noi_dung: str) -> tuple[str, str]:
    if not RE_HEAD_DONG.search(noi_dung):
        return noi_dung, "khong-head"
    if la_noindex(noi_dung):
        return noi_dung, "noindex"

    canonical = thanh_url_tuyet_doi(tim_canonical(noi_dung))
    if not canonical:
        return noi_dung, "khong-canonical"

    anh = tim_anh_uu_tien(noi_dung)
    tieu_de = tim_tieu_de(noi_dung)
    moi, _ = them_quyen_xem_truoc(noi_dung)
    khoi = dung_khoi_schema(canonical, anh, tieu_de)

    if RE_KHOI.search(moi):
        moi = RE_KHOI.sub(lambda _: khoi, moi, count=1)
    else:
        khop_head = RE_HEAD_DONG.search(moi)
        moi = moi[:khop_head.start()] + khoi + "\n" + moi[khop_head.start():]

    return moi, "doi" if moi != noi_dung else "dung"


def loi_kiem_tra(noi_dung: str) -> list[str]:
    if la_noindex(noi_dung):
        return []
    loi = []
    robots = tim_meta(noi_dung, name="robots")
    chi_thi = (thuoc_tinh(robots[1], "content") or "").lower() if robots else ""
    if "max-image-preview:large" not in chi_thi.replace(" ", ""):
        loi.append("thiếu max-image-preview:large")
    if len(RE_KHOI.findall(noi_dung)) != 1:
        loi.append("khối primaryImageOfPage thiếu hoặc bị lặp")
    if 'id="google-image-preview-data"' not in noi_dung:
        loi.append("thiếu JSON-LD ảnh ưu tiên")
    else:
        khop = re.search(
            r'<script[^>]*id="google-image-preview-data"[^>]*>([\s\S]*?)</script>',
            noi_dung,
            re.I,
        )
        try:
            du_lieu = json.loads(khop.group(1)) if khop else {}
        except json.JSONDecodeError:
            du_lieu = {}
        anh = du_lieu.get("primaryImageOfPage", {}) if isinstance(du_lieu, dict) else {}
        if not isinstance(anh, dict) or not anh.get("contentUrl"):
            loi.append("JSON-LD primaryImageOfPage không hợp lệ")
    return loi


def main() -> int:
    parser = argparse.ArgumentParser(description="Tối ưu ảnh thumbnail Google cho HTML.")
    parser.add_argument("--thu", action="store_true", help="Chỉ xem trước, không ghi file.")
    parser.add_argument("--kiem-tra", action="store_true", help="Chỉ kiểm tra trạng thái hiện tại.")
    args = parser.parse_args()

    cac_file = sorted(GOC.rglob("*.html"))
    da_doi = 0
    bo_qua_noindex = 0
    canh_bao: list[str] = []

    if args.kiem_tra:
        for duong in cac_file:
            noi_dung = duong.read_text(encoding="utf-8")
            for loi in loi_kiem_tra(noi_dung):
                canh_bao.append(f"{duong.relative_to(GOC)}: {loi}")
        if canh_bao:
            print("LỖI kiểm tra ảnh tìm kiếm:")
            for dong in canh_bao:
                print(" -", dong)
            return 1
        print(f"OK: mọi trang indexable trong {len(cac_file)} file HTML đều có ảnh ưu tiên.")
        return 0

    for duong in cac_file:
        noi_dung = duong.read_text(encoding="utf-8")
        moi, trang_thai = toi_uu_mot_trang(noi_dung)
        if trang_thai == "noindex":
            bo_qua_noindex += 1
            continue
        if trang_thai in {"khong-head", "khong-canonical"}:
            canh_bao.append(f"{duong.relative_to(GOC)}: {trang_thai}")
            continue
        if moi != noi_dung:
            da_doi += 1
            if not args.thu:
                duong.write_text(moi, encoding="utf-8", newline="")

    che_do = "Sẽ cập nhật" if args.thu else "Đã cập nhật"
    print(f"{che_do} {da_doi} trang; bỏ qua {bo_qua_noindex} trang noindex.")
    if canh_bao:
        print("CẢNH BÁO:")
        for dong in canh_bao:
            print(" -", dong)
    return 0 if not canh_bao else 1


if __name__ == "__main__":
    sys.exit(main())
