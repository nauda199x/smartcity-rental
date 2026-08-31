#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, datetime, html, json, os, re, statistics
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA=os.path.join(ROOT,"data.json")
PAGE=os.path.join(ROOT,"gia-thue-studio-smart-city.html")
START="<!-- STUDIO-DATA:BAT-DAU -->"; END="<!-- STUDIO-DATA:KET-THUC -->"
def clean(v): return str("" if v is None else v).strip()
def visible(r): return clean(r.get("Hiển thị trên Web")).lower()=="có"
def money(v):
    if isinstance(v,(int,float)): return int(v)
    return int(re.sub(r"[^0-9]","",clean(v)) or 0)
def fmt(v): return (("%g"%(v/1_000_000)).replace(".",","))+" triệu"
def today_vn(): return (datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=7)).date()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--thu",action="store_true"); args=ap.parse_args()
    with open(DATA,encoding="utf-8") as f: raw=json.load(f)
    rows=[r for r in raw if visible(r) and clean(r.get("Loại")).lower()=="studio" and money(r.get("Giá thuê"))>0]
    vals=sorted(money(r.get("Giá thuê")) for r in rows)
    if not vals: print("Không có Studio hợp lệ — giữ nguyên bài."); return 0
    med=statistics.median(vals); interiors={}
    for r in rows:
        nt=clean(r.get("Nội thất")) or "Chưa ghi"; interiors.setdefault(nt,[]).append(money(r.get("Giá thuê")))
    lis=[]
    for nt,a in sorted(interiors.items(), key=lambda kv:(-len(kv[1]),kv[0])):
        if len(a)<3: continue
        lis.append("<li><strong>%s:</strong> %d căn · %s–%s · trung vị %s/tháng</li>"%(html.escape(nt),len(a),fmt(min(a)),fmt(max(a)),fmt(statistics.median(sorted(a)))))
    body=START+"\n    <div class=\"note-box\"><strong>Dữ liệu quỹ căn hiện tại:</strong> %d căn Studio đang hiển thị, giá từ <strong>%s</strong> đến <strong>%s/tháng</strong>, trung vị <strong>%s/tháng</strong>. Đây là giá chào thuê của nguồn hàng đang vận hành, không phải bảng giá niêm yết cố định.</div>\n    <ul>%s</ul>\n    <p>Xem từng căn đang trống tại <a href=\"/studio/\">Studio Vinhomes Smart City cho thuê</a>, hoặc đối chiếu toàn thị trường tại <a href=\"/bang-gia-thue-vinhomes-smart-city.html\">bảng giá thuê Vinhomes Smart City</a>.</p>\n    "%(len(rows),fmt(min(vals)),fmt(max(vals)),fmt(med),"".join(lis))+END
    with open(PAGE,encoding="utf-8") as f: page=f.read()
    new=re.sub(re.escape(START)+r".*?"+re.escape(END),body,page,flags=re.S)
    d=today_vn()
    new=re.sub(r'"dateModified"\s*:\s*"\d{4}-\d{2}-\d{2}"','"dateModified": "%s"'%d.isoformat(),new)
    new=re.sub(r'<p class="meta">Cập nhật:.*?</p>','<p class="meta">Cập nhật: Tháng %02d/%d · Tìm Thuê Smart City</p>'%(d.month,d.year),new,count=1)
    if args.thu: print("Sẽ cập nhật",len(rows),"Studio",fmt(min(vals)),fmt(max(vals)),fmt(med)); return 0
    with open(PAGE,"w",encoding="utf-8",newline="") as f: f.write(new)
    print("Đã cập nhật",len(rows),"Studio",fmt(min(vals)),fmt(max(vals)),fmt(med)); return 0
if __name__=="__main__": raise SystemExit(main())
