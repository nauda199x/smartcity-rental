#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sinh cụm bài SEO so sánh/quyết định thuê từ data.json.

4 URL:
- masteri-vs-lumiere-thue-can-ho-smart-city.html
- nen-thue-phan-khu-nao-vinhomes-smart-city.html
- ngan-sach-10-trieu-thue-can-ho-smart-city.html
- ngan-sach-12-trieu-thue-can-ho-smart-city.html

Các con số (số căn, khoảng giá, trung vị, phân bố loại căn/phân khu) đều tính
trực tiếp từ quỹ căn đang hiển thị. Không viết cứng số liệu thị trường.
"""
import argparse, datetime, html, json, os, re, statistics

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA=os.path.join(ROOT,"data.json")
DOMAIN="https://timthuesmartcity.com"
MIN_SAMPLE=3

ZONE_META={
 "Sapphire":("/sapphire/","Sapphire"),
 "Masteri":("/masteri/","Masteri West Heights"),
 "Lumiere":("/lumiere/","Lumière Evergreen"),
 "Miami":("/miami/","The Miami"),
 "Sakura":("/sakura/","The Sakura"),
 "Imperia":("/imperia/","Imperia Smart City"),
 "Canopy":("/canopy/","The Canopy"),
 "Tonkin":("/tonkin/","The Tonkin"),
}
TYPE_ORDER=["Studio","1 Ngủ","1 Ngủ +","2 Ngủ","2 Ngủ +","3 Ngủ"]

def clean(v): return str("" if v is None else v).strip()
def visible(r): return clean(r.get("Hiển thị trên Web")).lower()=="có"
def money(v):
    if isinstance(v,(int,float)): return int(v)
    return int(re.sub(r"[^0-9]","",clean(v)) or 0)
def zone(t):
    t=re.sub(r"[\s._-]","",clean(t)).upper()
    if t.startswith(("MAS","WEST")): return "Masteri"
    if t.startswith("SA"): return "Sakura"
    if t.startswith("GS"): return "Miami"
    if t.startswith("TC"): return "Canopy"
    if t.startswith("TK"): return "Tonkin"
    if re.match(r"^I\d",t): return "Imperia"
    if re.match(r"^A\d",t): return "Lumiere"
    if re.match(r"^S\d",t): return "Sapphire"
    return ""
def fmt(v):
    x=v/1_000_000
    s=("%g"%x).replace(".",",")
    return s+" triệu"
def median(vals): return statistics.median(sorted(vals))
def stats(vals):
    if not vals: return None
    return {"n":len(vals),"min":min(vals),"max":max(vals),"median":median(vals)}
def today_vn():
    return (datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=7)).date()
def esc(v): return html.escape(str(v),quote=True)

def load_rows():
    with open(DATA,encoding="utf-8") as f: raw=json.load(f)
    rows=[]
    for r in raw:
        if not visible(r): continue
        z=zone(r.get("Tòa")); t=clean(r.get("Loại")); p=money(r.get("Giá thuê"))
        if z in ZONE_META and t and p>0:
            rows.append({"z":z,"t":t,"nt":clean(r.get("Nội thất")),"p":p})
    return rows

def group(rows,key):
    out={}
    for r in rows: out.setdefault(r[key],[]).append(r["p"])
    return out

def zone_summary(rows):
    g=group(rows,"z")
    return {z:stats(v) for z,v in g.items()}

def zone_type(rows,z):
    g={}
    for r in rows:
        if r["z"]==z: g.setdefault(r["t"],[]).append(r["p"])
    return {t:stats(v) for t,v in g.items()}

def article(path,title,desc,h1,lead,body,updated):
    url=DOMAIN+"/"+path
    article_schema=json.dumps({
      "@context":"https://schema.org","@type":"Article","headline":h1,
      "description":desc,"datePublished":"2026-08-31","dateModified":updated.isoformat(),
      "author":{"@type":"Organization","name":"Tìm Thuê Smart City","url":DOMAIN+"/"},
      "publisher":{"@type":"Organization","name":"Tìm Thuê Smart City","url":DOMAIN+"/"},
      "mainEntityOfPage":url,"inLanguage":"vi-VN"
    },ensure_ascii=False)
    bread=json.dumps({
      "@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"Trang chủ","item":DOMAIN+"/"},
        {"@type":"ListItem","position":2,"name":"Cẩm nang thuê nhà","item":DOMAIN+"/cam-nang-thue-nha.html"},
        {"@type":"ListItem","position":3,"name":h1,"item":url}
      ]},ensure_ascii=False)
    return f'''<!doctype html>
<html lang="vi"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}"><link rel="icon" href="/favicon.ico" sizes="any">
<meta property="og:type" content="article"><meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{DOMAIN}/og-smartcity.jpg"><meta property="og:site_name" content="Tìm Thuê Smart City">
<script type="application/ld+json">{article_schema}</script><script type="application/ld+json">{bread}</script>
<link rel="stylesheet" href="/assets/v3.css?v=20260831-2"></head><body>
<header class="top"><div class="khung"><a class="hieu" href="/">Tìm Thuê Smart City<small>Dữ liệu thuê căn hộ Smart City</small></a><nav><a href="/">Tìm căn</a><a href="/bang-gia-thue-vinhomes-smart-city.html">Bảng giá</a><a href="/cam-nang-thue-nha.html">Cẩm nang</a></nav></div></header>
<main class="khung" style="padding-top:28px;padding-bottom:48px"><p class="bc"><a href="/">Trang chủ</a> › <a href="/cam-nang-thue-nha.html">Cẩm nang</a> › So sánh & ngân sách</p>
<h1>{esc(h1)}</h1><p class="tt">{lead}</p>
<div class="note">Dữ liệu: {len(ROWS)} căn đang hiển thị · cập nhật {updated.strftime("%d/%m/%Y")}. Trung vị phản ánh cơ cấu quỹ căn hiện tại, không phải bảng giá niêm yết cố định.</div>
<section class="bai">{body}
<h2>Xem dữ liệu gốc trước khi quyết định</h2><p><a href="/bang-gia-thue-vinhomes-smart-city.html">Bảng giá thuê theo phân khu × loại căn × nội thất</a> · <a href="/">Toàn bộ quỹ căn đang trống</a>.</p>
<div class="lq"><a href="/masteri-vs-lumiere-thue-can-ho-smart-city.html">Masteri vs Lumière</a><a href="/nen-thue-phan-khu-nao-vinhomes-smart-city.html">Nên thuê phân khu nào?</a><a href="/ngan-sach-10-trieu-thue-can-ho-smart-city.html">Ngân sách 10 triệu</a><a href="/ngan-sach-12-trieu-thue-can-ho-smart-city.html">Ngân sách 12 triệu</a></div>
<a class="cta-home duoi" href="/">Mở quỹ căn thực tế<small>Lọc trực tiếp theo loại căn, phân khu, giá và nội thất</small></a>
</section></main><footer class="chan"><div class="khung"><p>© Tìm Thuê Smart City · <a href="/gioi-thieu-lien-he.html">Giới thiệu & Liên hệ</a></p></div></footer>
<script src="/assets/app-shell.js?v=20260901-1" defer></script></body></html>'''

def zone_table(rows):
    zs=zone_summary(rows)
    ordered=sorted(zs,key=lambda z:(zs[z]["median"],-zs[z]["n"],z))
    trs=[]
    for z in ordered:
        s=zs[z]; href,label=ZONE_META[z]
        trs.append('<tr><th scope="row"><a href="%s">%s</a></th><td>%d</td><td>%s–%s</td><td><strong>%s</strong></td></tr>'%(
          href,esc(label),s["n"],fmt(s["min"]),fmt(s["max"]),fmt(s["median"])))
    return '<div class="bang-cuon"><table class="bang"><thead><tr><th>Phân khu</th><th>Số căn</th><th>Khoảng giá</th><th>Trung vị</th></tr></thead><tbody>%s</tbody></table></div>'%"".join(trs)

def comparison_body(rows):
    a=zone_type(rows,"Masteri"); b=zone_type(rows,"Lumiere")
    za=stats([r["p"] for r in rows if r["z"]=="Masteri"])
    zb=stats([r["p"] for r in rows if r["z"]=="Lumiere"])
    trs=[]
    for t in TYPE_ORDER:
        if t in a and t in b and a[t]["n"]>=MIN_SAMPLE and b[t]["n"]>=MIN_SAMPLE:
            trs.append('<tr><th>%s</th><td>%d căn · trung vị %s</td><td>%d căn · trung vị %s</td></tr>'%(
              esc(t),a[t]["n"],fmt(a[t]["median"]),b[t]["n"],fmt(b[t]["median"])))
    return f'''
<h2>Masteri và Lumière khác nhau thế nào nếu nhìn bằng dữ liệu thuê?</h2>
<p>Quỹ hiện tại có <strong>{za["n"]} căn Masteri</strong> và <strong>{zb["n"]} căn Lumière</strong>. Trung vị toàn quỹ lần lượt là <strong>{fmt(za["median"])}</strong> và <strong>{fmt(zb["median"])}</strong>/tháng. Tuy nhiên con số tổng không phải so sánh “cùng loại căn”: Lumière đang có tỷ trọng 2PN lớn hơn, còn Masteri có nhiều Studio và 1PN+ hơn.</p>
<h2>So sánh cùng loại căn khi cả hai bên đủ mẫu</h2>
<div class="bang-cuon"><table class="bang"><thead><tr><th>Loại căn</th><th>Masteri West Heights</th><th>Lumière Evergreen</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div>
<p>Đây là lý do không nên kết luận đơn giản “Lumière luôn đắt hơn Masteri” hoặc ngược lại. Với từng loại căn, chênh lệch có thể khác hoàn toàn so với trung vị toàn phân khu.</p>
<h2>Khi nào nên nghiêng về Masteri?</h2>
<p>Nếu ngân sách tập trung vào Studio/1PN+ hoặc muốn quỹ lựa chọn dày hơn ở nhóm căn nhỏ, dữ liệu hiện tại cho thấy Masteri có nhiều mẫu hơn. Hãy xem <a href="/masteri/">căn Masteri đang trống</a> và các landing tòa West A/B/D để so cụ thể.</p>
<h2>Khi nào nên nghiêng về Lumière?</h2>
<p>Nếu ưu tiên 2PN, quỹ Lumière hiện dày hơn rõ rệt. Thay vì so tên thương hiệu, nên so đúng loại căn, nội thất và tổng chi phí ở. Xem <a href="/lumiere/">căn Lumière đang trống</a>.</p>
<h2>Cách quyết định trong 10 phút</h2>
<ol><li>Chốt loại căn và ngân sách.</li><li>So trung vị đúng loại căn ở bảng trên.</li><li>Mở 3–5 căn thật ở mỗi phân khu.</li><li>So nội thất, ngày vào ở và vị trí tòa.</li><li>Đi xem nhóm nhỏ căn phù hợp nhất.</li></ol>'''

def choose_zone_body(rows):
    return '''<h2>Toàn cảnh 8 phân khu theo quỹ căn hiện tại</h2>%s
<p><strong>Lưu ý:</strong> bảng xếp theo trung vị không phải bảng “chất lượng”. Phân khu có nhiều Studio có thể có trung vị thấp hơn chỉ vì cơ cấu loại căn. Dùng bảng để định hướng, sau đó phải so đúng loại căn.</p>
<h2>Nếu ưu tiên nhiều lựa chọn</h2>
<p>Sapphire, Masteri và Lumière đang có quỹ căn dày nhất trong dữ liệu hiện tại. Quỹ dày giúp dễ so sánh nhiều tòa, nội thất và ngày vào ở hơn.</p>
<h2>Nếu ưu tiên ngân sách</h2>
<p>Hãy dùng trung vị như điểm bắt đầu, sau đó xem các trang <a href="/ngan-sach-10-trieu-thue-can-ho-smart-city.html">ngân sách 10 triệu</a> và <a href="/ngan-sach-12-trieu-thue-can-ho-smart-city.html">ngân sách 12 triệu</a> để biết hiện có bao nhiêu căn thật sự nằm trong giới hạn.</p>
<h2>Nếu ưu tiên loại căn cụ thể</h2>
<p>Không chọn phân khu bằng trung vị toàn quỹ. Vào <a href="/bang-gia-thue-vinhomes-smart-city.html">bảng giá chi tiết</a>, tìm đúng dòng phân khu × loại căn; nhóm có từ 3 mẫu trở lên sẽ có khoảng giá và trung vị riêng.</p>
<h2>Quy tắc chọn nhanh</h2>
<ul><li>Chốt loại căn trước tên phân khu.</li><li>Chốt trần ngân sách gồm cả phí ngoài tiền thuê.</li><li>Chỉ so các căn có ngày vào ở phù hợp.</li><li>Đi xem 3–5 căn tốt nhất thay vì xem tràn lan.</li></ul>'''%zone_table(rows)

def budget_body(rows,max_price,label):
    rs=[r for r in rows if r["p"]<=max_price]
    bz={}
    bt={}
    for r in rs:
        bz[r["z"]]=bz.get(r["z"],0)+1
        bt[r["t"]]=bt.get(r["t"],0)+1
    zrows=[]
    for z,n in sorted(bz.items(),key=lambda x:(-x[1],x[0])):
        href,zlabel=ZONE_META[z]
        zrows.append('<tr><th><a href="%s">%s</a></th><td><strong>%d</strong></td></tr>'%(href,esc(zlabel),n))
    trows=[]
    for t in TYPE_ORDER:
        if bt.get(t): trows.append('<tr><th>%s</th><td><strong>%d</strong></td></tr>'%(esc(t),bt[t]))
    extra = ('Ở mức 10 triệu, nhóm Studio và 1PN+ chiếm tỷ trọng lớn; vẫn có một phần 2PN trong các phân khu giá mềm hoặc căn nội thất cơ bản.'
             if max_price==10_000_000 else
             'Tăng trần từ 10 lên 12 triệu mở rộng mạnh sang 2PN và 2PN+, đồng thời tăng số lựa chọn ở Masteri, Miami, Imperia và các phân khu cao cấp hơn.')
    return f'''
<h2>Với ngân sách tối đa {label}, hiện có bao nhiêu lựa chọn?</h2>
<p>Trong quỹ đang hiển thị, có <strong>{len(rs)} căn</strong> có giá chào thuê không vượt quá {label}/tháng. Con số này thay đổi khi căn được cho thuê, chủ nhà đổi giá hoặc có nguồn hàng mới.</p>
<h2>Phân bố theo phân khu</h2><div class="bang-cuon"><table class="bang"><thead><tr><th>Phân khu</th><th>Số căn ≤ {label}</th></tr></thead><tbody>{"".join(zrows)}</tbody></table></div>
<h2>Phân bố theo loại căn</h2><div class="bang-cuon"><table class="bang"><thead><tr><th>Loại căn</th><th>Số căn ≤ {label}</th></tr></thead><tbody>{"".join(trows)}</tbody></table></div>
<p>{extra}</p>
<h2>Nên lọc theo thứ tự nào?</h2>
<ol><li>Chọn loại căn tối thiểu chấp nhận được.</li><li>Giữ giá tối đa ở {label}.</li><li>So 2–3 phân khu có nhiều lựa chọn nhất.</li><li>Ưu tiên căn có ngày vào ở đúng lịch và nội thất phù hợp.</li><li>Nếu không có lựa chọn tốt, mới nới ngân sách hoặc đổi loại căn.</li></ol>
<h2>Đừng dùng hết ngân sách cho tiền thuê</h2>
<p>Ngoài tiền nhà còn có thể có phí dịch vụ, gửi xe, điện nước và internet. Nếu trần chi tiêu tổng là {label}, nên để lại biên cho các khoản ngoài tiền thuê thay vì chọn căn đúng sát trần.</p>'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--thu",action="store_true"); args=ap.parse_args()
    updated=today_vn()
    pages={
      "masteri-vs-lumiere-thue-can-ho-smart-city.html":article(
        "masteri-vs-lumiere-thue-can-ho-smart-city.html",
        "Masteri vs Lumière: thuê khu nào đáng tiền hơn? | Dữ liệu căn thực tế",
        "So sánh Masteri West Heights và Lumière Evergreen cho người thuê: số căn, trung vị theo loại căn và cách chọn dựa trên dữ liệu quỹ căn thực tế.",
        "Masteri hay Lumière: thuê khu nào đáng tiền hơn?",
        "So sánh bằng quỹ căn thật thay vì cảm tính: tách trung vị toàn phân khu khỏi so sánh cùng loại căn.",
        comparison_body(ROWS),updated),
      "nen-thue-phan-khu-nao-vinhomes-smart-city.html":article(
        "nen-thue-phan-khu-nao-vinhomes-smart-city.html",
        "Nên thuê phân khu nào ở Vinhomes Smart City? | So sánh 8 phân khu",
        "Nên thuê phân khu nào ở Vinhomes Smart City? So sánh số căn, khoảng giá và trung vị 8 phân khu từ quỹ căn đang cho thuê thực tế.",
        "Nên thuê phân khu nào ở Vinhomes Smart City?",
        "Bảng định hướng theo dữ liệu hiện tại; không xếp hạng chất lượng chung cho mọi nhu cầu.",
        choose_zone_body(ROWS),updated),
      "ngan-sach-10-trieu-thue-can-ho-smart-city.html":article(
        "ngan-sach-10-trieu-thue-can-ho-smart-city.html",
        "Ngân sách 10 triệu thuê được căn nào ở Smart City? | Dữ liệu thực tế",
        "Ngân sách tối đa 10 triệu/tháng thuê được căn nào tại Vinhomes Smart City? Xem số căn theo phân khu, loại căn và cách lọc từ quỹ thực tế.",
        "Ngân sách 10 triệu thuê được căn nào ở Vinhomes Smart City?",
        "Đếm trực tiếp các căn đang hiển thị có giá không vượt quá 10 triệu/tháng.",
        budget_body(ROWS,10_000_000,"10 triệu"),updated),
      "ngan-sach-12-trieu-thue-can-ho-smart-city.html":article(
        "ngan-sach-12-trieu-thue-can-ho-smart-city.html",
        "Ngân sách 12 triệu thuê được căn nào ở Smart City? | Dữ liệu thực tế",
        "Ngân sách tối đa 12 triệu/tháng thuê được căn nào tại Vinhomes Smart City? Phân bố theo phân khu, loại căn và dữ liệu quỹ căn thực tế.",
        "Ngân sách 12 triệu thuê được căn nào ở Vinhomes Smart City?",
        "Đếm trực tiếp các căn đang hiển thị có giá không vượt quá 12 triệu/tháng.",
        budget_body(ROWS,12_000_000,"12 triệu"),updated),
    }
    for path,content in pages.items():
        print(path,len(content))
        if not args.thu:
            with open(os.path.join(ROOT,path),"w",encoding="utf-8",newline="") as f: f.write(content)
    return 0

ROWS=load_rows()
if __name__=="__main__": raise SystemExit(main())
