# kiem-tra-lien-ket.py
import re, os, collections

pages = {}
for root, d, fs in os.walk('.'):
    if '.git' in root: continue
    for f in fs:
        if f.endswith('.html'):
            p = os.path.join(root, f).replace('./', '')
            pages[p] = open(p, encoding='utf-8').read()

def canon(h, src):
    h = h.split('#')[0].split('?')[0]
    if h.startswith('http'):
        if 'timthuesmartcity.com' not in h: return None
        h = re.sub(r'https?://(www\.)?timthuesmartcity\.com', '', h)
    elif h.startswith(('mailto', 'tel', 'javascript')): return None
    elif not h.startswith('/'):
        h = '/' + os.path.normpath(os.path.join(os.path.dirname(src), h))
    if h in ('', '/'): return 'index.html'
    h = h.lstrip('/')
    return h + 'index.html' if h.endswith('/') else h

inb = collections.Counter(); outb = {}
for p, html in pages.items():
    links = {t for m in re.findall(r'href="([^"]+)"', html)
             if (t := canon(m, p)) and t in pages and t != p}
    outb[p] = len(links)
    for t in links: inb[t] += 1

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

loi = 0
for p, n in NGUONG_VAO.items():
    ok = inb[p] >= n
    print(('PASS' if ok else 'FAIL'), f'link vào {p}: {inb[p]} (cần >= {n})')
    loi += not ok
for p, n in NGUONG_RA.items():
    ok = outb.get(p, 0) >= n
    print(('PASS' if ok else 'FAIL'), f'link ra  {p}: {outb.get(p,0)} (cần >= {n})')
    loi += not ok

# Không được sinh link gãy
for p, html in pages.items():
    for m in re.findall(r'href="(/[^"]*)"', html):
        t = canon(m, p)
        if t and not t.startswith('http') and t not in pages and not os.path.exists(t):
            print('FAIL link gãy:', p, '->', m); loi += 1

print('\n=== KẾT QUẢ:', 'PASS' if loi == 0 else f'{loi} lỗi ===')
