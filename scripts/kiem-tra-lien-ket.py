#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit sức khoẻ internal-link cho timthuesmartcity.com.

Bản P6 sửa các false-positive của audit cũ:
- đọc <a href> với cả dấu nháy đơn và nháy kép;
- không đếm URL nằm trong script/style/noscript;
- chuẩn hoá absolute/relative URL theo đúng hostname;
- orphan chỉ FAIL với page thực sự indexable/self-canonical;
- tách căn active trong sitemap khỏi căn lưu trữ và khỏi landing phân khu;
- link gãy chỉ xét anchor nội bộ thật, không xét canonical/CSS/JS asset.

Mã thoát: 0 = graph sạch; 1 = còn orphan/link gãy/ngưỡng cứng thật.
"""

import collections
import html as html_lib
import os
import re
import statistics
import sys
from urllib.parse import urlsplit

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEN_MIEN = "https://timthuesmartcity.com"
HOSTS = {"timthuesmartcity.com", "www.timthuesmartcity.com"}
BO_QUA = {'.git', '.github', 'node_modules'}

NGUONG_TY_LE = 0.40
TOI_THIEU_MAU = 4

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

MIEN_ORPHAN = {
    '404.html',
    'bang-gia-thue-smart-city-thang-7-2026.html',
}
BO_QUA_NGUON = {'404.html'}

RE_SCHEME_BO_QUA = re.compile(r'^(mailto|tel|javascript|data|blob|sms|zalomsg|ftp|file):', re.I)
RE_SCRIPT_STYLE = re.compile(r'<(script|style|noscript)\b[\s\S]*?</\1>', re.I)
RE_A_HREF = re.compile(r'<a\b[^>]*\bhref\s*=\s*(["\'])(.*?)\1', re.I | re.S)
RE_META_ROBOTS = re.compile(
    r'<meta\b(?=[^>]*\bname\s*=\s*["\']robots["\'])(?=[^>]*\bcontent\s*=\s*["\']([^"\']*)["\'])[^>]*>',
    re.I,
)
RE_CANONICAL = re.compile(
    r'<link\b(?=[^>]*\brel\s*=\s*["\']canonical["\'])(?=[^>]*\bhref\s*=\s*["\']([^"\']+)["\'])[^>]*>',
    re.I,
)
RE_SITEMAP_LOC = re.compile(r'<loc>\s*([^<]+?)\s*</loc>', re.I)


def nap_trang():
    pages = {}
    for root, dirs, fs in os.walk(GOC):
        dirs[:] = [d for d in dirs if d not in BO_QUA]
        for f in fs:
            if not f.endswith('.html'):
                continue
            p = os.path.relpath(os.path.join(root, f), GOC).replace(os.sep, '/')
            with open(os.path.join(root, f), encoding='utf-8', errors='replace') as fh:
                pages[p] = fh.read()
    return pages


def nap_can_active():
    path = os.path.join(GOC, 'sitemap-can-ho.xml')
    active = set()
    if not os.path.exists(path):
        return active
    raw = open(path, encoding='utf-8', errors='replace').read()
    for loc in RE_SITEMAP_LOC.findall(raw):
        loc = html_lib.unescape(loc.strip())
        if not loc.startswith(TEN_MIEN + '/can-ho/') or loc == TEN_MIEN + '/can-ho/':
            continue
        parsed = urlsplit(loc)
        rel = parsed.path.lstrip('/')
        if rel.endswith('/'):
            rel += 'index.html'
        active.add(rel)
    return active


def page_path_from_file(p):
    if p == 'index.html':
        return '/'
    if p.endswith('/index.html'):
        return '/' + p[:-len('index.html')]
    return '/' + p


def canon(href, src):
    """Chuẩn hoá một anchor href nội bộ về file HTML trong repo."""
    h = html_lib.unescape(href.strip())
    if not h or h.startswith('#') or RE_SCHEME_BO_QUA.match(h):
        return None

    parsed = urlsplit(h)
    if parsed.scheme in ('http', 'https'):
        host = (parsed.hostname or '').lower()
        if host not in HOSTS:
            return None
        h = parsed.path or '/'
    elif h.startswith('//'):
        parsed = urlsplit('https:' + h)
        host = (parsed.hostname or '').lower()
        if host not in HOSTS:
            return None
        h = parsed.path or '/'
    else:
        h = h.split('#', 1)[0].split('?', 1)[0]
        if not h:
            return None

    if not h.startswith('/'):
        keep_slash = h.endswith('/')
        h = os.path.normpath(os.path.join(os.path.dirname(src), h)).replace(os.sep, '/')
        h = '/' + h.lstrip('./')
        if keep_slash and not h.endswith('/'):
            h += '/'

    if h in ('', '/'):
        return 'index.html'
    h = h.lstrip('/')
    return h + 'index.html' if h.endswith('/') else h


def anchor_links(raw, src):
    sach = RE_SCRIPT_STYLE.sub('', raw)
    out = set()
    for _, href in RE_A_HREF.findall(sach):
        target = canon(href, src)
        if target:
            out.add(target)
    return out


def meta_noindex(raw):
    vals = [html_lib.unescape(x).lower() for x in RE_META_ROBOTS.findall(raw)]
    return any(
        'noindex' in x or re.search(r'(^|[,\s])none([,\s]|$)', x)
        for x in vals
    )


def canonical_file(raw, src):
    vals = [html_lib.unescape(x).strip() for x in RE_CANONICAL.findall(raw)]
    if len(vals) != 1:
        return src if not vals else None
    return canon(vals[0], src)


def la_indexable(raw, src):
    if meta_noindex(raw):
        return False
    c = canonical_file(raw, src)
    return c in (None, src) if c is None else c == src


def phan_nhom(p, active_can):
    if p == 'index.html':
        return 'trang-chu'
    if p in ('404.html', 'chinh-sach-quyen-rieng-tu.html'):
        return 'phu-tro'
    if p.startswith('can-ho/') and p.endswith('/index.html'):
        return 'can-ho-active' if p in active_can else 'can-ho-luu-tru'
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
        if re.match(r'^(a\d+-lumiere|west-[a-d]-masteri|gs\d+-the-miami|sa\d+-the-sakura|tc\d+-canopy|tk\d+-tonkin|i\d+-imperia)', thu_muc):
            return 'trang-toa'
        if thu_muc.startswith('cho-thue-'):
            return 'giao-thoa'
        return 'danh-muc-phan-khu'
    return 'bai-viet'


def main():
    pages = nap_trang()
    active_can = nap_can_active()
    indexable = {p for p, raw in pages.items() if la_indexable(raw, p)}

    inb = collections.Counter()
    outb = {}
    nguon = collections.defaultdict(set)

    for p, raw in pages.items():
        if p in BO_QUA_NGUON:
            outb[p] = 0
            continue
        links = {t for t in anchor_links(raw, p) if t in pages and t != p}
        outb[p] = len(links)
        for t in links:
            inb[t] += 1
            nguon[t].add(p)

    for p in pages:
        inb.setdefault(p, 0)

    loi = 0
    canh_bao = 0

    print('=' * 76)
    print('AUDIT INTERNAL-LINK — timthuesmartcity.com')
    print('=' * 76)
    print(f'Tổng HTML: {len(pages)} · indexable/self-canonical: {len(indexable)}')
    print(f'Căn active trong sitemap: {len(active_can)}')

    print('\n' + '=' * 76)
    print('1. INBOUND THEO NHÓM INDEXABLE')
    print('=' * 76)
    nhom = collections.defaultdict(list)
    for p in sorted(indexable):
        nhom[phan_nhom(p, active_can)].append(p)

    trung_vi = {}
    for g, ps in sorted(nhom.items()):
        vals = sorted(inb[p] for p in ps)
        tv = statistics.median(vals) if vals else 0
        trung_vi[g] = tv
        print(f'[{g}] {len(ps)} page · min={min(vals) if vals else 0} · median={tv:g} · max={max(vals) if vals else 0}')

    print('\n' + '=' * 76)
    print('2. ORPHAN INDEXABLE THẬT')
    print('=' * 76)
    orphan = [p for p in sorted(indexable) if inb[p] == 0 and p not in MIEN_ORPHAN]
    if orphan:
        for p in orphan:
            print('FAIL orphan:', p)
            loi += 1
    else:
        print('PASS — không có orphan indexable.')

    print('\n' + '=' * 76)
    print(f'3. INBOUND THẤP (< {NGUONG_TY_LE:.0%} median nhóm)')
    print('=' * 76)
    for g, ps in sorted(nhom.items()):
        if len(ps) < TOI_THIEU_MAU:
            continue
        threshold = trung_vi[g] * NGUONG_TY_LE
        for p in sorted(ps, key=lambda x: inb[x]):
            if inb[p] == 0 or inb[p] >= threshold:
                continue
            print(f'WARN {p}: {inb[p]} link vào — median [{g}]={trung_vi[g]:g}, ngưỡng={threshold:.1f}')
            srcs = sorted(nguon[p])[:5]
            if srcs:
                print('     nguồn:', ', '.join(srcs) + (' …' if len(nguon[p]) > 5 else ''))
            canh_bao += 1
    if canh_bao == 0:
        print('PASS — không có page thấp bất thường.')

    print('\n' + '=' * 76)
    print('4. NGƯỠNG CỨNG & LINK GÃY')
    print('=' * 76)
    for p, n in sorted(NGUONG_VAO.items()):
        actual = inb[p]
        ok = actual >= n
        print(('PASS' if ok else 'FAIL'), f'link vào {p}: {actual} (cần >= {n})')
        if not ok:
            loi += 1
    for p, n in sorted(NGUONG_RA.items()):
        actual = outb.get(p, 0)
        ok = actual >= n
        print(('PASS' if ok else 'FAIL'), f'link ra {p}: {actual} (cần >= {n})')
        if not ok:
            loi += 1

    gay = []
    for p, raw in pages.items():
        for t in anchor_links(raw, p):
            if t in pages:
                continue
            disk = os.path.join(GOC, t.replace('/', os.sep))
            if os.path.exists(disk):
                continue
            # Chỉ coi là broken page-link khi href đích có dạng HTML/page.
            if t.endswith('.html') or t.endswith('/index.html'):
                gay.append((p, t))
    if gay:
        for p, t in gay[:120]:
            print(f'FAIL link gãy: {p} -> {t}')
            loi += 1
        if len(gay) > 120:
            print(f'... và {len(gay) - 120} link gãy nữa')
            loi += len(gay) - 120
    else:
        print('PASS — không có internal page-link gãy.')

    print('\n' + '=' * 76)
    print(f'KẾT QUẢ: {"PASS" if loi == 0 else f"{loi} lỗi"} · {canh_bao} cảnh báo')
    print('=' * 76)
    return 1 if loi else 0


if __name__ == '__main__':
    sys.exit(main())
