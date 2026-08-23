#!/usr/bin/env python3
"""Tải ảnh căn hộ từ Google Drive về repo dưới dạng WebP.

Google Drive chặn crawler nên không ảnh nào được Google Images index. Script
này tải ảnh đại diện lẫn ảnh gallery của scripts/danh-sach-anh.json về thư
mục anh-can-ho/, chuyển sang WebP rồi sinh ra:

  - anh-can-ho/anh-map.json  : drive_id -> đường dẫn ảnh 800px trong repo,
                                gộp chung cả ảnh bìa lẫn ảnh gallery.
  - sitemap-images.xml       : Google Image Sitemap.

Ảnh bìa (loai_anh="bia") tải hai bề rộng — 800px cho desktop, 400px cho khung
ảnh nhỏ trên mobile (hậu tố -400 trước phần mở rộng). Ảnh gallery
(loai_anh="gallery") chỉ tải bản 800px: gallery trên trang căn hiển thị khổ
lớn, bản nhỏ chỉ phình repo mà không dùng tới.

Ảnh nào đã có đủ file cần thiết thì được bỏ qua, nên chạy lại script chỉ tải
phần còn thiếu.

Đầu vào là scripts/danh-sach-anh.json. Script KHÔNG đụng vào data.json.

Chạy:  python3 scripts/tai-anh-can-ho.py [--gioi-han N] [--gia-lap]

Môi trường phát triển của Claude Code chặn drive.google.com, nên script này
được thiết kế để chạy trong GitHub Actions (.github/workflows/tai-anh-can-ho.yml).
Chế độ --gia-lap sinh ảnh WebP một màu đúng kích thước thay vì gọi Drive, để
kiểm chứng được toàn bộ pipeline khi không có mạng — TỪ CHỐI chạy nếu
GITHUB_ACTIONS=true, không bao giờ để ảnh giả lọt lên production.
"""

import argparse
import hashlib
import io
import json
import os
import random
import sys
import time
from xml.sax.saxutils import escape

import requests
from PIL import Image

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DANH_SACH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "danh-sach-anh.json")
THU_MUC_ANH = os.path.join(GOC, "anh-can-ho")
DUONG_MAP = os.path.join(THU_MUC_ANH, "anh-map.json")
DUONG_SITEMAP_ANH = os.path.join(GOC, "sitemap-images.xml")

# danh-sach-anh.json rỗng hoặc gần rỗng gần như luôn là lỗi sinh dữ liệu chứ
# không phải hết ảnh. Dưới ngưỡng này thì dừng, không ghi đè anh-map.json hay
# sitemap-images.xml.
NGUONG_TOI_THIEU = 150

TEN_MIEN = "https://timthuesmartcity.com"
RONG_TOI_DA = 800
# Khung ảnh trên thẻ chỉ rộng ~166 CSS px ở màn ≤640px, tức ~332px thật với
# DPR 2. Bản 800px thừa hơn hai lần, nên mỗi ảnh có thêm một bản 400px cho
# mobile; srcset trên thẻ tự chọn bản phù hợp.
RONG_NHO = 400
CHAT_LUONG = 82
SO_LAN_THU = 3

# Ảnh đại diện của một căn xuất hiện trên trang chủ (liệt kê mọi căn, không
# lọc) và trên hai trang danh mục: theo loại căn và theo phân khu. Cả ba đều
# đã dùng ảnh repo nên đều được khai báo trong sitemap-images.xml.
TRANG_CHU = "/"
TRANG_THEO_LOAI = {
    "Studio": "/studio/",
    "1 Ngủ": "/1pn/",
    "1 Ngủ +": "/1pn-plus/",
    "2 Ngủ": "/2pn/",
    "2 Ngủ +": "/2pn-plus/",
    "3 Ngủ": "/3pn/",
}
TRANG_THEO_PHAN_KHU = {
    "Masteri": "/masteri/",
    "Sakura": "/sakura/",
    "Sapphire": "/sapphire/",
    "Imperia": "/imperia/",
    "Miami": "/miami/",
    "Canopy": "/canopy/",
    "Tonkin": "/tonkin/",
    "Lumiere": "/lumiere/",
}

# Ảnh minh hoạ cho các trang nội dung tĩnh (không phải ảnh căn hộ tải từ
# Drive). ghi_sitemap_anh() ghi đè toàn bộ sitemap-images.xml mỗi lần chạy,
# nên khai báo thủ công tại đây thay vì sửa tay file XML — sửa tay sẽ mất
# ngay lần workflow tai-anh-can-ho chạy lại.
TRANG_TINH = [
    ("/mau-hop-dong-thue-nha-vinhomes-smart-city.html", [
        ("/images/hop-dong/mau-hop-dong-thue-can-ho-vinhomes-smart-city.webp",
         "Mẫu hợp đồng thuê căn hộ Vinhomes Smart City gồm hợp đồng chính và phụ lục bàn giao nội thất"),
        ("/images/hop-dong/hop-dong-thue-nha-dieu-khoan-gia-va-dat-coc.webp",
         "Điều khoản giá thuê, phương thức thanh toán và đặt cọc trong hợp đồng thuê căn hộ chung cư"),
        ("/images/hop-dong/phu-luc-ban-giao-noi-that-va-chi-so-cong-to.webp",
         "Phụ lục bàn giao căn hộ cho thuê với bảng danh sách nội thất và chỉ số công tơ điện nước"),
        ("/images/hop-dong/ghi-chi-so-cong-to-dien-nuoc-khi-nhan-nha.webp",
         "Khối ghi chỉ số công tơ điện và đồng hồ nước tại thời điểm bàn giao căn hộ"),
    ]),
]

PHIEN = requests.Session()
PHIEN.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
})


def cac_url(ban_ghi):
    """URL thumbnail trước, nếu lỗi thì tới URL tải trực tiếp."""
    ma_drive = ban_ghi["drive_id"]
    goc = ban_ghi.get("url_goc") or (
        "https://drive.google.com/thumbnail?id=%s&sz=w1000" % ma_drive
    )
    return [goc, "https://drive.google.com/uc?export=download&id=%s" % ma_drive]


def tai_mot_url(url):
    """Trả về bytes ảnh, hoặc None kèm lý do lỗi."""
    r = PHIEN.get(url, timeout=45)
    if r.status_code != 200:
        return None, "HTTP %d" % r.status_code
    noi_dung = r.content
    if not noi_dung:
        return None, "phản hồi rỗng"
    # Drive trả về trang HTML (hỏi xác nhận virus, hoặc file không công khai)
    # với status 200 — phải bắt bằng nội dung chứ không tin status code.
    dau = noi_dung.lstrip()[:15].lower()
    if dau.startswith(b"<!doctype") or dau.startswith(b"<html"):
        return None, "Drive trả về HTML (ảnh có thể không công khai)"
    return noi_dung, ""


def duong_ban_nho(duong):
    """Đường dẫn bản nhỏ: chèn hậu tố -400 trước phần mở rộng.

    anh.webp -> anh-400.webp. anh-map.json vẫn chỉ ghi bản 800px; phía trang
    suy ra đường dẫn bản nhỏ bằng đúng quy tắc này."""
    goc, duoi = os.path.splitext(duong)
    return "%s-%d%s" % (goc, RONG_NHO, duoi)


def da_du_hai_ban(duong_ra):
    """Có đủ cả bản 800px lẫn bản 400px thì lần chạy sau khỏi tải lại."""
    return os.path.exists(duong_ra) and os.path.exists(duong_ban_nho(duong_ra))


def da_du_mot_ban(duong_ra):
    """Ảnh gallery chỉ cần đúng một bản 800px."""
    return os.path.exists(duong_ra)


def anh_gia_lap(drive_id):
    """Ảnh WebP một màu, kích thước hợp lý, KHÔNG gọi mạng — dùng cho --gia-lap
    để kiểm chứng toàn bộ pipeline khi không truy cập được Drive."""
    mau = tuple(hashlib.md5(drive_id.encode()).digest()[:3])
    im = Image.new("RGB", (1200, 900), mau)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return buf.getvalue()


def thu_nho(im, rong_dich):
    """Thu ảnh về đúng rong_dich px chiều rộng, giữ nguyên tỉ lệ.

    Ảnh vốn đã hẹp hơn thì trả về nguyên trạng — phóng to chỉ làm file nặng
    thêm mà không thêm chi tiết nào."""
    rong, cao = im.size
    if rong <= rong_dich:
        return im
    cao_moi = max(1, round(cao * rong_dich / rong))
    return im.resize((rong_dich, cao_moi), Image.LANCZOS)


def chuyen_webp(noi_dung, duong_ra, ca_hai_ban=True):
    """Ghi bytes ảnh ra WebP: luôn có RONG_TOI_DA, thêm RONG_NHO nếu
    `ca_hai_ban` (ảnh bìa). Ảnh gallery chỉ cần bản RONG_TOI_DA."""
    with Image.open(io.BytesIO(noi_dung)) as im:
        im.load()
        # WebP không lưu được ảnh chỉ mục/CMYK — chuyển hết về RGB. Ảnh đại
        # diện luôn hiển thị trên nền thẻ nên không cần giữ kênh alpha.
        if im.mode != "RGB":
            im = im.convert("RGB")
        lon = thu_nho(im, RONG_TOI_DA)
        lon.save(duong_ra, "WEBP", quality=CHAT_LUONG, method=6)
        if not ca_hai_ban:
            return lon.size, None
        # Bản nhỏ thu thẳng từ ảnh gốc chứ không thu lại từ bản 800px, để
        # không chồng thêm nhiễu của một lần nén nữa.
        nho = thu_nho(im, RONG_NHO)
        nho.save(duong_ban_nho(duong_ra), "WEBP", quality=CHAT_LUONG, method=6)
        return lon.size, nho.size


def tai_mot_anh(ban_ghi, ca_hai_ban=True, gia_lap=False):
    """Tải + chuyển đổi một bản ghi. Trả về (thành công, mô tả)."""
    duong_ra = os.path.join(THU_MUC_ANH, ban_ghi["ten_file"])
    duong_phu = [duong_ban_nho(duong_ra)] if ca_hai_ban else []
    loi = []

    if gia_lap:
        try:
            co_lon, co_nho = chuyen_webp(
                anh_gia_lap(ban_ghi["drive_id"]), duong_ra, ca_hai_ban)
        except Exception as e:
            for duong in [duong_ra] + duong_phu:
                if os.path.exists(duong):
                    os.remove(duong)
            return False, "%s: %s" % (type(e).__name__, e)
        if ca_hai_ban:
            return True, "%dx%d (giả lập) + %dx%d (giả lập)" % (
                co_lon[0], co_lon[1], co_nho[0], co_nho[1])
        return True, "%dx%d (giả lập)" % (co_lon[0], co_lon[1])

    for url in cac_url(ban_ghi):
        for lan in range(1, SO_LAN_THU + 1):
            try:
                noi_dung, ly_do = tai_mot_url(url)
                if noi_dung is None:
                    loi.append(ly_do)
                    break  # lỗi từ phía Drive, đổi URL chứ thử lại vô ích
                co_lon, co_nho = chuyen_webp(noi_dung, duong_ra, ca_hai_ban)
                if ca_hai_ban:
                    return True, "%dx%d %.0f KB + %dx%d %.0f KB" % (
                        co_lon[0], co_lon[1],
                        os.path.getsize(duong_ra) / 1024,
                        co_nho[0], co_nho[1],
                        os.path.getsize(duong_ban_nho(duong_ra)) / 1024,
                    )
                return True, "%dx%d %.0f KB" % (
                    co_lon[0], co_lon[1], os.path.getsize(duong_ra) / 1024)
            except requests.RequestException as e:
                loi.append("%s (lần %d)" % (type(e).__name__, lan))
                if lan < SO_LAN_THU:
                    time.sleep(2 ** lan)
            except Exception as e:  # ảnh hỏng, Pillow không mở được
                loi.append("%s: %s" % (type(e).__name__, e))
                break
    # Không để lại file dở dang: xoá mọi bản, nếu không lần chạy sau sẽ thấy
    # file còn sót và tưởng ảnh này đã xong.
    for duong in [duong_ra] + duong_phu:
        if os.path.exists(duong):
            os.remove(duong)
    return False, "; ".join(loi[:3]) or "không rõ nguyên nhân"


def ghi_sitemap_anh(ban_ghi_ok):
    """Sinh Google Image Sitemap: nhóm ảnh theo trang hiển thị nó.

    Ảnh bìa (loai_anh="bia") giữ nguyên cách khai cũ: trang chủ liệt kê mọi
    căn, hai trang danh mục chỉ nhận ảnh của loại căn / phân khu tương ứng.
    Ảnh gallery (loai_anh="gallery") CHỈ khai dưới đúng trang căn của nó
    (bg["trang"]) — không lên trang chủ, không lên trang danh mục, vì ảnh đó
    chỉ thực sự xuất hiện trên một trang duy nhất."""
    theo_trang = {TRANG_CHU: []}
    for bg in ban_ghi_ok:
        if bg.get("loai_anh", "bia") == "gallery":
            trang = bg.get("trang")
            if trang:
                theo_trang.setdefault(trang, []).append(bg)
            continue
        theo_trang[TRANG_CHU].append(bg)
        for bang, khoa in ((TRANG_THEO_LOAI, "loai"),
                           (TRANG_THEO_PHAN_KHU, "phan_khu")):
            trang = bang.get(bg[khoa])
            if trang:
                theo_trang.setdefault(trang, []).append(bg)

    dong = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
            '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for trang in sorted(theo_trang):
        dong.append("  <url><loc>%s%s</loc>" % (TEN_MIEN, trang))
        for bg in sorted(theo_trang[trang], key=lambda x: x["ten_file"]):
            tieu_de = "Cho thuê căn hộ %s %s %sm2 Vinhomes Smart City - %s" % (
                bg["loai"], bg["phan_khu"], bg["dien_tich"], bg["ma"])
            dong.append(
                "    <image:image><image:loc>%s/anh-can-ho/%s</image:loc>"
                "<image:title>%s</image:title></image:image>"
                % (TEN_MIEN, bg["ten_file"], escape(tieu_de)))
        dong.append("  </url>")
    for trang, anh in TRANG_TINH:
        dong.append("  <url><loc>%s%s</loc>" % (TEN_MIEN, trang))
        for duong, tieu_de in anh:
            dong.append(
                "    <image:image><image:loc>%s%s</image:loc>"
                "<image:title>%s</image:title></image:image>"
                % (TEN_MIEN, duong, escape(tieu_de)))
        dong.append("  </url>")
    dong.append("</urlset>")
    dong.append("")

    with open(DUONG_SITEMAP_ANH, "w", encoding="utf-8") as f:
        f.write("\n".join(dong))
    return len(theo_trang)


def main():
    bo_phan_tich = argparse.ArgumentParser()
    bo_phan_tich.add_argument("--gioi-han", type=int, default=0,
                              help="chỉ tải N ảnh đầu (để thử nhanh)")
    bo_phan_tich.add_argument("--gia-lap", action="store_true",
                              help="sinh ảnh WebP một màu thay vì gọi Drive, "
                                   "để kiểm chứng pipeline khi không có mạng")
    tham_so = bo_phan_tich.parse_args()

    if tham_so.gia_lap and os.environ.get("GITHUB_ACTIONS") == "true":
        print("DỪNG: --gia-lap không được phép chạy khi GITHUB_ACTIONS=true "
              "— không bao giờ để ảnh giả lọt lên production.")
        return 1

    with open(DANH_SACH, encoding="utf-8") as f:
        danh_sach = json.load(f)

    if len(danh_sach) < NGUONG_TOI_THIEU:
        print("DỪNG: scripts/danh-sach-anh.json chỉ có %d bản ghi, dưới "
              "ngưỡng %d — nhiều khả năng đang lỗi. Không ghi đè "
              "anh-map.json, không ghi đè sitemap-images.xml."
              % (len(danh_sach), NGUONG_TOI_THIEU))
        return 1

    if tham_so.gioi_han:
        danh_sach = danh_sach[:tham_so.gioi_han]

    os.makedirs(THU_MUC_ANH, exist_ok=True)
    print("Bắt đầu tải %d ảnh về %s%s\n" % (
        len(danh_sach), "anh-can-ho/", " (--gia-lap: không gọi Drive)"
        if tham_so.gia_lap else ""))

    ok, that_bai, bo_qua = [], [], []
    for i, bg in enumerate(danh_sach, 1):
        ca_hai_ban = bg.get("loai_anh", "bia") == "bia"
        duong_ra = os.path.join(THU_MUC_ANH, bg["ten_file"])
        # Đã có đủ file cần thiết thì không gọi Drive nữa: chạy lại script
        # nhiều lần chỉ tải phần còn thiếu. Ảnh vẫn vào anh-map.json và sitemap.
        da_du = da_du_hai_ban(duong_ra) if ca_hai_ban else da_du_mot_ban(duong_ra)
        if da_du:
            ok.append(bg)
            bo_qua.append(bg)
            print("[%3d/%d] BỎ QUA %-12s %s (đã có sẵn)"
                  % (i, len(danh_sach), bg["ma"], bg["ten_file"]))
            sys.stdout.flush()
            continue

        thanh_cong, mo_ta = tai_mot_anh(bg, ca_hai_ban, tham_so.gia_lap)
        if thanh_cong:
            ok.append(bg)
            print("[%3d/%d] OK   %-12s %s (%s)" % (i, len(danh_sach), bg["ma"],
                                                   bg["ten_file"], mo_ta))
        else:
            that_bai.append((bg, mo_ta))
            print("[%3d/%d] LỖI  %-12s %s" % (i, len(danh_sach), bg["ma"], mo_ta))
        sys.stdout.flush()
        # Chỉ nghỉ giữa hai lần thật sự gọi Drive; ảnh bỏ qua/giả lập không
        # chạm mạng.
        if i < len(danh_sach) and not tham_so.gia_lap:
            time.sleep(random.uniform(0.3, 0.5))

    tong_byte = 0
    for bg in ok:
        duong_ra = os.path.join(THU_MUC_ANH, bg["ten_file"])
        cac_duong = [duong_ra]
        if bg.get("loai_anh", "bia") == "bia":
            cac_duong.append(duong_ban_nho(duong_ra))
        for duong in cac_duong:
            if os.path.exists(duong):
                tong_byte += os.path.getsize(duong)
    print("\n=== KẾT QUẢ ===")
    print("Thành công : %d/%d (trong đó bỏ qua vì đã có sẵn: %d)"
          % (len(ok), len(danh_sach), len(bo_qua)))
    print("Thất bại   : %d" % len(that_bai))
    print("Dung lượng : %.1f MB" % (tong_byte / 1024 / 1024))
    if that_bai:
        print("\nMã nội bộ lỗi:")
        for bg, ly_do in that_bai:
            print("  - %s (%s): %s" % (bg["ma"], bg["drive_id"], ly_do))

    # Quá nửa số ảnh lỗi thì dữ liệu không dùng được — dừng hẳn, không ghi map
    # để không ai lỡ mở PR với ảnh thiếu.
    if len(ok) * 2 <= len(danh_sach):
        print("\nDỪNG: quá nửa số ảnh tải lỗi, không ghi anh-map.json.")
        return 1

    with open(DUONG_MAP, "w", encoding="utf-8") as f:
        json.dump({bg["drive_id"]: "/anh-can-ho/" + bg["ten_file"]
                   for bg in sorted(ok, key=lambda x: x["ten_file"])},
                  f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("\nĐã ghi anh-can-ho/anh-map.json (%d ảnh)." % len(ok))

    so_trang = ghi_sitemap_anh(ok)
    print("Đã ghi sitemap-images.xml (%d trang)." % so_trang)
    return 0


if __name__ == "__main__":
    sys.exit(main())
