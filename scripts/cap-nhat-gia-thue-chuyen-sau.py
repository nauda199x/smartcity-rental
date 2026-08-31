#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database giá thuê thực tế + snapshot theo tháng.

Đọc duy nhất data.json, không suy đoán. Mỗi lần chạy cập nhật:
- du-lieu-gia-thue/hien-tai.json
- du-lieu-gia-thue/lich-su/YYYY-MM.json
- fallback HTML bảng Phân khu × Loại căn × Nội thất (chỉ n >= 3)
"""
import argparse, datetime, html, json, os, re, statistics

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA=os.path.join(ROOT,"data.json")
OUT=os.path.join(ROOT,"du-lieu-gia-thue")
HISTORY=os.path.join(OUT,"lich-su")
PRICE_PAGE=os.path.join(ROOT,"bang-gia-thue-vinhomes-smart-city.html")
START="<!-- GIA-NOI-THAT:BAT-DAU -->"
END="<!-- GIA-NOI-THAT:KET-THUC -->"
MIN_SAMPLE=3

def clean(v): return str("" if v is None else v).strip()
def visible(r): return clean(r.get("Hiển thị trên Web")).lower()=="có"
def cash(v):
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
    if re.match(r"^V\d",t): return "Victoria"
    if re.match(r"^G\d",t): return "Sola Park"
    return ""
def stat(vals):
    if not vals: return None
    vals=sorted(vals)
    return {"n":len(vals),"min":min(vals),"max":max(vals),"median":statistics.median(vals)}
def fmt(v):
    return (("%g"%(v/1_000_000)).replace(".",","))+" tr"
def today_vn():
    return (datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=7)).date()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--thu",action="store_true")
    args=ap.parse_args()
    with open(DATA,encoding="utf-8") as f: raw=json.load(f)
    rows=[]
    for r in raw:
        if not visible(r): continue
        z,t,nt,p=zone(r.get("Tòa")),clean(r.get("Loại")),clean(r.get("Nội thất")),cash(r.get("Giá thuê"))
        if z and t and nt and p>0: rows.append({"zone":z,"type":t,"interior":nt,"price":p})
    def grouped(field):
        d={}
        for r in rows: d.setdefault(r[field],[]).append(r["price"])
        return {k:stat(v) for k,v in sorted(d.items())}
    triples={}
    for r in rows: triples.setdefault((r["zone"],r["type"],r["interior"]),[]).append(r["price"])
    tri=[{"zone":z,"type":t,"interior":nt,**stat(vals)} for (z,t,nt),vals in sorted(triples.items())]
    d=today_vn()
    snap={"updated":d.isoformat(),"source":"data.json","active_count":len(rows),"min_sample":MIN_SAMPLE,
          "overall":stat([r["price"] for r in rows]),"by_type":grouped("type"),
          "by_zone":grouped("zone"),"by_interior":grouped("interior"),"zone_type_interior":tri}
    if args.thu:
        print("Sẽ cập nhật",len(rows),"căn,",len(tri),"tổ hợp; tháng",d.strftime("%Y-%m"))
        return 0
    os.makedirs(HISTORY,exist_ok=True)
    for path in (os.path.join(OUT,"hien-tai.json"),os.path.join(HISTORY,d.strftime("%Y-%m")+".json")):
        with open(path,"w",encoding="utf-8") as f: json.dump(snap,f,ensure_ascii=False,indent=2); f.write("\n")
    if os.path.exists(PRICE_PAGE):
        with open(PRICE_PAGE,encoding="utf-8") as f: page=f.read()
        body=[]
        for x in tri:
            if x["n"]<MIN_SAMPLE: continue
            body.append('<tr><td>%s</td><td>%s</td><td>%s</td><td><strong>%d</strong></td><td><span class="bang-gia-khoang">%s–%s</span><small>Trung vị %s</small></td></tr>'%
                        (html.escape(x["zone"]),html.escape(x["type"]),html.escape(x["interior"]),x["n"],fmt(x["min"]),fmt(x["max"]),fmt(x["median"])))
        repl=START+"\n              "+("\n              ".join(body) if body else '<tr><td colspan="5">Chưa đủ dữ liệu.</td></tr>')+"\n              "+END
        page=re.sub(re.escape(START)+r".*?"+re.escape(END),repl,page,flags=re.S)
        with open(PRICE_PAGE,"w",encoding="utf-8",newline="") as f: f.write(page)
    print("Đã cập nhật database giá thuê:",len(rows),"căn,",len(tri),"tổ hợp.")
    return 0
if __name__=="__main__": raise SystemExit(main())
