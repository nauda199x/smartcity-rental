#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sinh 2 landing nhu cầu từ data thật: vào ở ngay và full nội thất.

Hai trang được dựng lại sau khi sinh-trang-can.py hoàn tất để link thẳng tới
URL chi tiết từng căn. Không tạo trang theo thuộc tính không có trong data.
"""
import argparse, datetime, html, json, os, re

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA=os.path.join(ROOT,"data.json")
REG=os.path.join(ROOT,"can-ho","danh-sach-trang.json")
DOMAIN="https://timthuesmartcity.com"
MAX_CARDS=80

def clean(v): return str("" if v is None else v).strip()
def visible(r): return clean(r.get("Hiển thị trên Web")).lower()=="có"
def price(v):
    if isinstance(v,(int,float)): return int(v)
    return int(re.sub(r"[^0-9]","",clean(v)) or 0)
def fmt(p):
    x=p/1_000_000
    return (("%g"%x).replace(".",","))+" triệu"
def today_vn():
    return (datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=7)).date()
def date_passed(s,today):
    m=re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$",clean(s))
    if not m: return False
    try: d=datetime.date(int(m.group(3)),int(m.group(2)),int(m.group(1)))
    except ValueError: return False
    return d<=today
def ready_now(r,today):
    s=clean(r.get("Ngày vào ở")).lower()
    return (not s) or s in ("luôn","ở ngay","o ngay","ngay") or date_passed(s,today)

def read_registry():
    try:
        with open(REG,encoding="utf-8") as f: raw=json.load(f)
    except Exception: return {}
    return {clean(v.get("ma")):slug for slug,v in raw.items() if isinstance(v,dict) and clean(v.get("ma"))}

def cards(rows,reg):
    out=[]
    for r in rows[:MAX_CARDS]:
        ma=clean(r.get("Mã nội bộ")); slug=reg.get(ma)
        href=("/can-ho/%s/"%slug) if slug else "/"
        out.append('<article class="the" style="padding:16px"><h3 style="margin:0 0 8px"><a href="%s">%s · %s · %sm²</a></h3><p style="margin:0 0 6px"><strong>%s/tháng</strong> · %s · %s</p><small>Mã %s</small></article>'%(
            html.escape(href,quote=True),html.escape(clean(r.get("Loại"))),html.escape(clean(r.get("Tòa"))),
            html.escape(clean(r.get("Diện tích"))),html.escape(fmt(price(r.get("Giá thuê")))),
            html.escape(clean(r.get("Nội thất"))),html.escape(clean(r.get("Ngày vào ở")) or "Vào ngay"),html.escape(ma)))
    return "\n".join(out)

def page(path,title,desc,h1,intro,rows,reg,faq):
    url=DOMAIN+"/"+path
    body=cards(rows,reg)
    faq_html="".join('<details class="faq"><summary>%s</summary><p>%s</p></details>'%(html.escape(q),html.escape(a)) for q,a in faq)
    schema=json.dumps({"@context":"https://schema.org","@type":"CollectionPage","name":title,"url":url,
                       "description":desc,"isPartOf":{"@type":"WebSite","name":"Tìm Thuê Smart City","url":DOMAIN+"/"}},
                      ensure_ascii=False)
    return f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc,quote=True)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Tìm Thuê Smart City"><meta property="og:title" content="{html.escape(title,quote=True)}"><meta property="og:description" content="{html.escape(desc,quote=True)}"><meta property="og:image" content="{DOMAIN}/og-smartcity.jpg">
<script type="application/ld+json">{schema}</script><link rel="stylesheet" href="/assets/v3.css?v=20260830-8"></head><body>
<header class="top"><div class="khung"><a class="hieu" href="/">Tìm Thuê Smart City<small>Quỹ căn thực tế · cập nhật mỗi ngày</small></a><nav><a href="/">Tất cả căn</a><a href="/bang-gia-thue-vinhomes-smart-city.html">Bảng giá</a></nav></div></header>
<main class="khung" style="padding-top:28px;padding-bottom:48px"><p class="bc"><a href="/">Trang chủ</a> › {html.escape(h1)}</p><h1>{html.escape(h1)}</h1><p class="tt">{html.escape(intro)}</p>
<div class="sl"><div class="o"><b>{len(rows)}</b><span>căn khớp dữ liệu hiện tại</span></div><div class="o"><b>{min((price(r.get("Giá thuê")) for r in rows),default=0)//1_000_000} tr</b><span>giá thấp nhất</span></div></div>
<section class="luoi">{body}</section>
<section class="bai"><h2>Cách dùng danh sách này</h2><p>Trang được sinh trực tiếp từ data.json. Khi căn ngừng hiển thị, nó tự rời danh sách; URL chi tiết cũ vẫn được hệ thống giữ để tránh 404 và chuyển khách sang căn tương tự.</p><h2>Câu hỏi thường gặp</h2>{faq_html}
<a class="cta-home duoi" href="/">Mở bộ lọc toàn bộ quỹ căn<small>Lọc tiếp theo phân khu, loại căn, giá và nội thất</small></a></section></main>
<footer class="chan"><div class="khung"><p>© Tìm Thuê Smart City · <a href="/gioi-thieu-lien-he.html">Giới thiệu & Liên hệ</a></p></div></footer><script src="/assets/app-shell.js?v=20260901-1" defer></script></body></html>'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--thu",action="store_true"); args=ap.parse_args()
    with open(DATA,encoding="utf-8") as f: raw=json.load(f)
    reg=read_registry(); today=today_vn()
    base=[r for r in raw if visible(r) and price(r.get("Giá thuê"))>0 and clean(r.get("Tòa")) and clean(r.get("Loại"))]
    ready=sorted([r for r in base if ready_now(r,today)],key=lambda r:(price(r.get("Giá thuê")),clean(r.get("Tòa"))))
    full=sorted([r for r in base if clean(r.get("Nội thất")).lower()=="full nội thất"],key=lambda r:(price(r.get("Giá thuê")),clean(r.get("Tòa"))))
    pages=[
      ("can-ho-vao-o-ngay-vinhomes-smart-city.html","Căn hộ Vinhomes Smart City vào ở ngay | Cập nhật quỹ căn",
       "Danh sách căn hộ Vinhomes Smart City có thể vào ở ngay theo dữ liệu quỹ căn hiện tại, kèm giá thuê, nội thất và URL chi tiết.",
       "Căn hộ Vinhomes Smart City vào ở ngay","Danh sách ưu tiên những căn có ngày vào ở trống, ghi “luôn/ở ngay”, hoặc ngày sẵn sàng đã đến.",ready,
       [("“Vào ở ngay” được xác định thế nào?","Dựa trực tiếp vào trường Ngày vào ở trong dữ liệu: để trống, ghi ở ngay/luôn, hoặc ngày sẵn sàng đã đến."),
        ("Danh sách có tự cập nhật không?","Có. Trang được dựng lại từ quỹ căn trong workflow cập nhật website.")]),
      ("can-ho-full-noi-that-vinhomes-smart-city.html","Căn hộ Vinhomes Smart City full nội thất | Quỹ căn thực tế",
       "Danh sách căn hộ Vinhomes Smart City full nội thất đang chào thuê, cập nhật từ quỹ căn thực tế theo giá, tòa và loại căn.",
       "Căn hộ Vinhomes Smart City full nội thất","Tổng hợp toàn bộ căn đang hiển thị có trường Nội thất = Full nội thất; phù hợp người muốn hạn chế mua sắm thêm khi chuyển vào.",full,
       [("Full nội thất có nghĩa mọi căn giống nhau không?","Không. Mức trang bị thực tế khác nhau theo từng căn; cần xem ảnh và xác nhận danh mục bàn giao trước khi cọc."),
        ("Có thể lọc thêm theo ngân sách không?","Có. Từ trang chủ có thể kết hợp loại căn, phân khu, giá và nội thất.")])
    ]
    for path,title,desc,h1,intro,rows,faq in pages:
        print(path,len(rows))
        if not args.thu:
            with open(os.path.join(ROOT,path),"w",encoding="utf-8",newline="") as f: f.write(page(path,title,desc,h1,intro,rows,reg,faq))
    return 0
if __name__=="__main__": raise SystemExit(main())
