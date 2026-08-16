#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kiem-tra-lien-ket.py — kiểm tra sức khoẻ liên kết nội bộ.

BỐN VIỆC SCRIPT LÀM
-------------------
1. Đếm inbound internal link cho TỪNG URL trong repo.
2. Phát hiện orphan page (0 link vào, không tính chính nó).
3. Cảnh báo page có inbound thấp bất thường SO VỚI NHÓM CÙNG LOẠI.
4. Bắt link gãy (href trỏ tới file không tồn tại).

NGUYÊN TẮC ĐO
-------------
Script KHÔNG yêu cầu mọi page có số inbound bằng nhau. Số link bằng nhau
không phải mục tiêu SEO — một trang phụ (chính sách quyền riêng tư) tự nhiên
sẽ có nhiều link sitewide, còn một trang ngách (/1pn/) tự nhiên ít hơn.

Cách đo: chia page thành các NHÓM có vai trò tương đương, rồi so mỗi page với
TRUNG VỊ (median) của nhóm mình. Trung vị chống nhiễu tốt hơn trung bình khi
nhóm có vài giá trị cực đoan. Chỉ cảnh báo khi inbound < NGUONG_TY_LE × trung
vị nhóm — tức là lệch hẳn khỏi mặt bằng chung của các page cùng vai trò, chứ
không phải chỉ vì thấp hơn page khác.

WARN không làm script fail. Chỉ FAIL khi: link gãy, orphan page, hoặc vi phạm
ngưỡng cứng đã chốt trong NGUONG_VAO/NGUONG_RA.

Chạy:  python3 scripts/kiem-tra-lien-ket.py
Mã thoát: 0 = pass, 1 = có lỗi.
"""

import collections
import os
import re
import statistics
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BO_QUA = {'.git', '.github', 'node_modules'}

# Page có inbound < tỷ lệ này so với trung vị nhóm thì cảnh báo.
NGUONG_TY_LE = 0.40
# Nhóm ít hơn số page này thì không đủ mẫu để tính trung vị -> bỏ qua cảnh báo.
TOI_THIEU_MAU = 4

# Ngưỡng cứng đã chốt từ trước — giữ nguyên, đây là FAIL gate.
NGUONG_VAO = {
    'so-sanh-gia-thue-cac-phan-khu-smart-city.html': 10,
    'cho-thue-can-ho-masteri-west-heights-smart-city.html': 2,
    'gia-thue-studio-smart-city.html': 5,
    'kinh-nghiem-thue-chung-cu-smart-city.html': 9,
    'tien-ich-vinhomes-smart-city.html': 10,
    'luu-y-do-xe-thu-cung-phi-dich-vu-smart-city.html': 10,
    'bang-gia-thue-vinhomes-smart-city.html': 15,
    'chinh-sach-quyen-rieng-tu.html': 30,
}
NGUONG_RA = {p: 5 for p in NGUONG_VAO if p != 'chinh-sach-quyen-rieng-tu.html'}

# Page không cần link vào — orphan ở đây là CÓ CHỦ Ý, không phải lỗi:
#   404.html: trang lỗi, không ai link tới là đúng.
#   bang-gia-thue-smart-city-thang-7-2026.html: bản cũ đã canonical trỏ về
#     bang-gia-thue-vinhomes-smart-city.html; gỡ link nội bộ là chủ động.
MIEN_ORPHAN = {
    '404.html',
    'bang-gia-thue-smart-city-thang-7-2026.html',
}

# Không tính là nguồn truyền liên kết: 404 không nằm trong luồng duyệt thật.
BO_QUA_NGUON = {'404.html'}


def nap_trang():
    pages = {}
    for root, dirs, fs in os.walk(GOC):
        dirs[:] = [d for d in dirs if d not in BO_QUA]
        for f in fs:
            if not f.endswith('.html'):
                continue
            p = os.path.relpath(os.path.join(root, f), GOC)
            pages[p] = open(os.path.join(root, f), encoding='utf-8',
                            errors='replace').read()
    return pages


# Scheme không phải liên kết trang — bỏ qua hoàn toàn.
RE_SCHEME_BO_QUA = re.compile(
    r'^(mailto|tel|javascript|data|blob|sms|zalomsg|ftp|file):', re.I)


def canon(h, src):
    """Chuẩn hoá href về đường dẫn file tương đối so với gốc repo.

    Nhận được cả bốn dạng viết link nội bộ:
        https://timthuesmartcity.com/abc/   (tuyệt đối, có domain)
        /abc/                               (tuyệt đối từ gốc site)
        abc/                                (tương đối so với trang hiện tại)
        ../abc/                             (tương đối, lùi thư mục)

    Trả None nếu không phải link nội bộ tới một trang (neo #, mailto:, tel:,
    data: base64, link ngoại...). Trước đây `data:image/...;base64,...` lọt
    xuống nhánh tương đối và sinh ra đường dẫn rác.
    """
    h = h.strip()
    if not h or h.startswith('#'):
        return None
    if RE_SCHEME_BO_QUA.match(h):
        return None
    h = h.split('#')[0].split('?')[0]
    if not h:
        return None
    if h.startswith('//'):          # protocol-relative -> coi là ngoại
        return None
    if h.startswith('http'):
        if 'timthuesmartcity.com' not in h:
            return None
        h = re.sub(r'https?://(www\.)?timthuesmartcity\.com', '', h)
    elif not h.startswith('/'):
        # 'abc/', './abc/', '../abc/' — giải tương đối theo thư mục của src.
        ket_thuc_slash = h.endswith('/')
        h = os.path.normpath(os.path.join(os.path.dirname(src), h))
        h = '/' + h.replace(os.sep, '/').lstrip('./')
        if ket_thuc_slash and not h.endswith('/'):
            h += '/'
    if h in ('', '/'):
        return 'index.html'
    h = h.lstrip('/')
    if h in ('', '.'):
        return 'index.html'
    return h + 'index.html' if h.endswith('/') else h


def phan_nhom(p):
    """Chia page theo VAI TRÒ, không theo số lượng link.

    Các page cùng nhóm mới đáng so với nhau. So /1pn/ với trang chính sách
    quyền riêng tư là vô nghĩa vì vai trò khác hẳn.
    """
    if p == 'index.html':
        return 'trang-chu'
    if p in ('404.html', 'chinh-sach-quyen-rieng-tu.html'):
        return 'phu-tro'
    if p.endswith('/index.html'):
        thu_muc = p.rsplit('/', 1)[0]
        if re.match(r'^(studio|\dpn)(-plus)?$', thu_muc):
            return 'danh-muc-loai-can'
        if re.search(r'(trieu|full-do)$', thu_muc):
            return 'danh-muc-gia-noi-that'
        if thu_muc == 'gui-thue':
            return 'phu-tro'
        if re.match(r'^[a-z0-9]+-\d+-vinhomes', thu_muc):
            return 'trang-toa'
        return 'danh-muc-phan-khu'
    return 'bai-viet'


def main():
    pages = nap_trang()
    inb = collections.Counter()
    outb = {}
    nguon = collections.defaultdict(set)

    for p, html in pages.items():
        # Bỏ <script> để không đếm URL nằm trong JS.
        sach = re.sub(r'<script.*?</script>', '', html, flags=re.S)
        links = set()
        if p in BO_QUA_NGUON:
            outb[p] = 0
            continue
        for m in re.findall(r'href="([^"]+)"', sach):
            t = canon(m, p)
            if t and t in pages and t != p:
                links.add(t)
        outb[p] = len(links)
        for t in links:
            inb[t] += 1
            nguon[t].add(p)

    for p in pages:
        inb.setdefault(p, 0)

    loi = 0
    canh_bao = 0

    # ---- 1. Bảng inbound cho từng URL ----
    print('=' * 72)
    print('1. INBOUND INTERNAL LINK THEO TỪNG URL')
    print('=' * 72)
    nhom = collections.defaultdict(list)
    for p in pages:
        nhom[phan_nhom(p)].append(p)

    trung_vi = {}
    for g, ps in sorted(nhom.items()):
        vals = sorted(inb[p] for p in ps)
        tv = statistics.median(vals) if vals else 0
        trung_vi[g] = tv
        print(f'\n[{g}]  {len(ps)} page · trung vị inbound = {tv:g}')
        for p in sorted(ps, key=lambda x: inb[x]):
            print(f'    {inb[p]:>4}  vào  {p}   (ra: {outb.get(p, 0)})')

    # ---- 2. Orphan page ----
    print('\n' + '=' * 72)
    print('2. ORPHAN PAGE (không có link nội bộ nào trỏ tới)')
    print('=' * 72)
    orphan = [p for p in sorted(pages) if inb[p] == 0 and p not in MIEN_ORPHAN]
    if orphan:
        for p in orphan:
            print('FAIL orphan:', p)
            loi += 1
    else:
        print('PASS — không có orphan page.')

    # ---- 3. Inbound thấp bất thường so với nhóm ----
    print('\n' + '=' * 72)
    print(f'3. INBOUND THẤP BẤT THƯỜNG (< {NGUONG_TY_LE:.0%} trung vị nhóm)')
    print('=' * 72)
    for g, ps in sorted(nhom.items()):
        if len(ps) < TOI_THIEU_MAU:
            continue
        nguong = trung_vi[g] * NGUONG_TY_LE
        for p in sorted(ps, key=lambda x: inb[x]):
            if inb[p] == 0 or inb[p] >= nguong:
                continue
            print(f'WARN  {p}: {inb[p]} link vào — trung vị nhóm '
                  f'[{g}] là {trung_vi[g]:g}, ngưỡng {nguong:.1f}')
            print(f'      nguồn hiện có: {", ".join(sorted(nguon[p])[:5])}'
                  + (' …' if len(nguon[p]) > 5 else ''))
            canh_bao += 1
    if canh_bao == 0:
        print('Không có page nào lệch dưới ngưỡng.')

    # ---- 4. Ngưỡng cứng + link gãy ----
    print('\n' + '=' * 72)
    print('4. NGƯỠNG CỨNG & LINK GÃY')
    print('=' * 72)
    for p, n in sorted(NGUONG_VAO.items()):
        ok = inb[p] >= n
        print(('PASS' if ok else 'FAIL'),
              f'link vào {p}: {inb[p]} (cần >= {n})')
        loi += not ok
    for p, n in sorted(NGUONG_RA.items()):
        ok = outb.get(p, 0) >= n
        print(('PASS' if ok else 'FAIL'),
              f'link ra  {p}: {outb.get(p, 0)} (cần >= {n})')
        loi += not ok

    # Bắt link gãy ở CẢ BỐN dạng viết, không chỉ dạng bắt đầu bằng '/'.
    gay = 0
    for p, html in pages.items():
        sach = re.sub(r'<script.*?</script>', '', html, flags=re.S)
        for m in re.findall(r'href="([^"]*)"', sach):
            t = canon(m, p)
            if t and t not in pages and not os.path.exists(
                    os.path.join(GOC, t)):
                print(f'FAIL link gãy: {p} -> {m}   (giải thành: {t})')
                loi += 1
                gay += 1
    if gay == 0:
        print('PASS không có link gãy.')

    print('\n' + '=' * 72)
    print(f'KẾT QUẢ: {"PASS" if loi == 0 else f"{loi} lỗi"} '
          f'· {canh_bao} cảnh báo (cảnh báo không làm fail)')
    print('=' * 72)
    return 1 if loi else 0


if __name__ == '__main__':
    sys.exit(main())
