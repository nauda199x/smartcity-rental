#!/usr/bin/env python3
"""Thay URL Google Drive trong HTML bằng ảnh WebP nằm trong repo.

Ngoài src của thẻ <img>, script còn đồng bộ ảnh social của trang chi tiết căn:
  - og:image
  - twitter:image
  - primaryImageOfPage / thumbnailUrl nếu khối google-image-preview-data đã có

Lý do: trang căn có thể được sinh trước khi workflow tải ảnh mới từ Drive.
Khi đó gallery vẫn có ảnh thật nhưng og:image phải rơi về og-smartcity.jpg.
Ngay sau khi ảnh đã tải xong, script này lấy ảnh local đầu tiên trong gallery
và sửa social preview mà KHÔNG sinh lại toàn bộ trang, tránh ghi đè các bước
SEO/internal-link đã chạy sau sinh-trang-can.py.

Chỉ thay khi ID vừa có trong map vừa có file WebP thật trên đĩa. ID nào chưa
tải được ảnh thì giữ nguyên URL Drive để trang không vỡ ảnh — chạy lại workflow
tai-anh-can-ho là lần sau sẽ thay được.

Chạy lần hai trên repo đã sửa phải cho 0 thay đổi.

Chạy:  python3 scripts/thay-anh-trong-html.py [--thu]
"""

import argparse
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_ANH = os.path.join(GOC, "anh-can-ho")
DUONG_MAP = os.path.join(THU_MUC_ANH, "anh-map.json")
TEN_MIEN = "https://timthuesmartcity.com"

# Thư mục không chứa HTML của trang, hoặc chứa bản nháp/thư viện không được
# đụng tới. 404.html do GitHub Pages phục vụ riêng, không có thẻ ảnh căn hộ.
THU_MUC_BO_QUA = {".git", "anh-can-ho", "_design:", "assets", "images",
                  "scripts", ".github"}
FILE_BO_QUA = {"404.html"}

# Bắt src của thẻ <img>. Dấu & trong HTML tĩnh phần lớn là thực thể &amp;,
# nhưng vẫn có chỗ viết & thuần nên phải nhận cả hai.
MAU_SRC = re.compile(
    r'(src\s*=\s*")'
    r'https://drive\.google\.com/thumbnail\?id=([A-Za-z0-9_-]+)(?:&amp;|&)sz=w1000'
    r'(")'
)
MAU_IMG = re.compile(r'<img\b[^>]*>', re.IGNORECASE)

# Chỉ lấy ảnh social từ gallery của trang căn. Không lấy logo, ảnh phân khu hay
# ảnh tĩnh khác ở header/footer. Sau thay_trong_html(), ảnh local có dạng
# /anh-can-ho/*.webp.
MAU_GALLERY = re.compile(
    r'<section\b[^>]*class="[^"]*\bgallery\b[^"]*"[^>]*>(.*?)</section>',
    re.IGNORECASE | re.DOTALL,
)
MAU_IMG_SRC_BAT_KY = re.compile(
    r'<img\b[^>]*\bsrc\s*=\s*"([^"]+)"', re.IGNORECASE
)
MAU_OG_IMAGE = re.compile(
    r'(<meta\s+property="og:image"\s+content=")([^"]*)("[^>]*>)',
    re.IGNORECASE,
)
MAU_TWITTER_IMAGE = re.compile(
    r'(<meta\s+name="twitter:image"\s+content=")([^"]*)("[^>]*>)',
    re.IGNORECASE,
)
MAU_GOOGLE_IMAGE_DATA = re.compile(
    r'(<script\s+type="application/ld\+json"\s+id="google-image-preview-data">)'
    r'(.*?)'
    r'(</script>)',
    re.IGNORECASE | re.DOTALL,
)


def cac_file_html():
    """Duyệt repo, trả về đường dẫn tương đối của mọi file HTML trong phạm vi."""
    ket_qua = []
    for thu_muc, cac_con, cac_file in os.walk(GOC):
        # Cắt nhánh ngay tại đây để không phải duyệt vào trong cho tốn thời gian.
        cac_con[:] = [c for c in cac_con
                      if os.path.relpath(os.path.join(thu_muc, c), GOC)
                      not in THU_MUC_BO_QUA]
        for ten in cac_file:
            if ten.endswith(".html") and ten not in FILE_BO_QUA:
                ket_qua.append(
                    os.path.relpath(os.path.join(thu_muc, ten), GOC))
    return sorted(ket_qua)


def thay_trong_html(noi_dung, co_the_thay, bo_qua):
    """Thay src Drive trong từng thẻ <img>. Trả về (nội dung mới, số lượt thay).

    Chỉ đụng phần văn bản nằm trong thẻ <img>, nên URL Drive ở <a href>,
    <video src>, thuộc tính data-*, khối <script> hay bình luận HTML đều không
    bị ảnh hưởng."""
    dem = [0]

    def thay_mot_img(khop_img):
        the = khop_img.group(0)

        def thay_mot_src(khop):
            ma_drive = khop.group(2)
            duong_dan = co_the_thay.get(ma_drive)
            if not duong_dan:
                bo_qua.append(ma_drive)
                return khop.group(0)
            dem[0] += 1
            return khop.group(1) + duong_dan + khop.group(3)

        return MAU_SRC.sub(thay_mot_src, the)

    return MAU_IMG.sub(thay_mot_img, noi_dung), dem[0]


def la_trang_can(duong_dan):
    duong = duong_dan.replace(os.sep, "/")
    return duong.startswith("can-ho/") and duong.endswith("/index.html")


def anh_local_dau_gallery(noi_dung):
    """Trả URL tuyệt đối của ảnh căn local đầu tiên trong gallery, hoặc None.

    Nếu ảnh số 1 chưa tải được nhưng ảnh số 2 đã có local thì dùng ảnh số 2 —
    vẫn tốt hơn fallback ảnh dự án. Chỉ nhận /anh-can-ho/ để bảo đảm crawler
    không phải đi qua Google Drive hay host ngoài."""
    khop_gallery = MAU_GALLERY.search(noi_dung)
    if not khop_gallery:
        return None

    for khop in MAU_IMG_SRC_BAT_KY.finditer(khop_gallery.group(1)):
        src = khop.group(1).strip()
        if src.startswith("/anh-can-ho/"):
            return TEN_MIEN + src
        if src.startswith(TEN_MIEN + "/anh-can-ho/"):
            return src
    return None


def cap_nhat_google_image_data(noi_dung, anh_social):
    """Đồng bộ khối JSON-LD ưu tiên ảnh nếu khối đó đã tồn tại.

    Không tự chèn khối mới ở đây: scripts/toi-uu-anh-tim-kiem.py là nguồn duy
    nhất chịu trách nhiệm tạo/xóa marker này. Script này chỉ sửa URL ảnh để hai
    pipeline không giẫm trách nhiệm lên nhau."""
    dem = [0]

    def thay(khop):
        try:
            du_lieu = json.loads(khop.group(2))
        except (TypeError, ValueError, json.JSONDecodeError):
            return khop.group(0)

        anh = du_lieu.get("primaryImageOfPage")
        if not isinstance(anh, dict):
            anh = {"@type": "ImageObject"}
            du_lieu["primaryImageOfPage"] = anh

        truoc = (
            anh.get("@id"), anh.get("url"), anh.get("contentUrl"),
            du_lieu.get("thumbnailUrl"),
        )
        anh["@id"] = anh_social + "#primaryimage"
        anh["url"] = anh_social
        anh["contentUrl"] = anh_social
        du_lieu["thumbnailUrl"] = anh_social
        sau = (
            anh.get("@id"), anh.get("url"), anh.get("contentUrl"),
            du_lieu.get("thumbnailUrl"),
        )
        if truoc == sau:
            return khop.group(0)

        dem[0] += 1
        return (khop.group(1)
                + json.dumps(du_lieu, ensure_ascii=False,
                             separators=(",", ":"))
                + khop.group(3))

    return MAU_GOOGLE_IMAGE_DATA.sub(thay, noi_dung), dem[0]


def cap_nhat_anh_social(noi_dung, duong_dan):
    """Đồng bộ ảnh thật cho OG/Twitter/Google preview của trang căn."""
    if not la_trang_can(duong_dan):
        return noi_dung, 0

    anh_social = anh_local_dau_gallery(noi_dung)
    if not anh_social:
        return noi_dung, 0

    dem = 0

    def thay_meta(mau, chuoi):
        nonlocal dem

        def thay(khop):
            nonlocal dem
            if khop.group(2) == anh_social:
                return khop.group(0)
            dem += 1
            return khop.group(1) + anh_social + khop.group(3)

        return mau.sub(thay, chuoi, count=1)

    moi = thay_meta(MAU_OG_IMAGE, noi_dung)
    moi = thay_meta(MAU_TWITTER_IMAGE, moi)
    moi, so_json = cap_nhat_google_image_data(moi, anh_social)
    dem += so_json
    return moi, dem


def main():
    bo_phan_tich = argparse.ArgumentParser()
    bo_phan_tich.add_argument("--thu", action="store_true",
                              help="chỉ in kết quả dự kiến, không ghi file")
    tham_so = bo_phan_tich.parse_args()

    if not os.path.exists(DUONG_MAP):
        print("Không tìm thấy %s — chạy tai-anh-can-ho.py trước." % DUONG_MAP)
        return 1

    with open(DUONG_MAP, encoding="utf-8") as f:
        anh_map = json.load(f)

    # Map có thể còn dòng của ảnh đã bị xoá khỏi đĩa. Thay bằng đường dẫn không
    # tồn tại thì trang vỡ ảnh, tệ hơn cả để nguyên URL Drive.
    co_the_thay = {}
    thieu_file = 0
    for ma_drive, duong_dan in anh_map.items():
        if os.path.exists(os.path.join(GOC, duong_dan.lstrip("/"))):
            co_the_thay[ma_drive] = duong_dan
        else:
            thieu_file += 1

    print("anh-map.json: %d ảnh, %d ảnh có file trên đĩa%s\n"
          % (len(anh_map), len(co_the_thay),
             ", %d dòng thiếu file" % thieu_file if thieu_file else ""))

    tong_thay = tong_social = tong_bo_qua = 0
    bo_qua_tat_ca = []
    print("%-46s %8s %8s %8s" % ("File", "Đã thay", "Social", "Bỏ qua"))
    print("-" * 74)
    for duong_dan in cac_file_html():
        with open(os.path.join(GOC, duong_dan), encoding="utf-8") as f:
            noi_dung = f.read()

        bo_qua = []
        moi, so_thay = thay_trong_html(noi_dung, co_the_thay, bo_qua)
        moi, so_social = cap_nhat_anh_social(moi, duong_dan)
        if not so_thay and not so_social and not bo_qua:
            continue

        print("%-46s %8d %8d %8d"
              % (duong_dan, so_thay, so_social, len(bo_qua)))
        tong_thay += so_thay
        tong_social += so_social
        tong_bo_qua += len(bo_qua)
        bo_qua_tat_ca.extend(bo_qua)

        if (so_thay or so_social) and not tham_so.thu:
            # newline="" để không đụng vào ký tự xuống dòng sẵn có của file.
            with open(os.path.join(GOC, duong_dan), "w",
                      encoding="utf-8", newline="") as f:
                f.write(moi)

    print("-" * 74)
    print("%-46s %8d %8d %8d"
          % ("TỔNG", tong_thay, tong_social, tong_bo_qua))

    if bo_qua_tat_ca:
        rieng = sorted(set(bo_qua_tat_ca))
        print("\n%d lượt bỏ qua, thuộc %d Drive ID chưa có ảnh trong repo."
              % (tong_bo_qua, len(rieng)))
        print("Chạy workflow tai-anh-can-ho để tải về, sau đó chạy lại script này.")
        for ma_drive in rieng[:20]:
            print("  - %s" % ma_drive)
        if len(rieng) > 20:
            print("  ... còn %d ID nữa" % (len(rieng) - 20))

    if tham_so.thu:
        print("\n(--thu) Không ghi file nào.")
    elif tong_thay or tong_social:
        print("\nĐã sửa xong. Chạy lại script này phải cho 0 lượt thay/social.")
    else:
        print("\nKhông có gì để thay.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
