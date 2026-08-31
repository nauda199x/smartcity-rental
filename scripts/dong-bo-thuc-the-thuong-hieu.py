#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chuẩn hóa tên thực thể trong structured data về Tìm Thuê Smart City.

Không thay chữ hiển thị trong body/header. Chỉ chạm:
- JSON-LD trường name có đúng các biến thể thương hiệu cũ
- og:site_name
Mục tiêu là author/publisher/WebSite/Organization cùng trỏ về một tên.
"""
import argparse, os, re

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET="Tìm Thuê Smart City"
OLD=("Cho thuê chung cư Smart City","Thuê Chung Cư Smart City","Timthuesmartcity.com")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--thu",action="store_true"); args=ap.parse_args()
    changed=0; json_names=0; og=0
    for base,dirs,files in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in (".git","node_modules")]
        for fn in files:
            if not fn.endswith(".html"): continue
            path=os.path.join(base,fn)
            with open(path,encoding="utf-8",errors="replace") as f: raw=f.read()
            new=raw
            # Work only inside JSON-LD blocks for name replacements.
            def fix_block(m):
                nonlocal json_names
                block=m.group(0)
                for old in OLD:
                    patt=re.compile(r'("name"\s*:\s*")'+re.escape(old)+r'(")')
                    block,n=patt.subn(r'\1'+TARGET+r'\2',block)
                    json_names+=n
                return block
            new=re.sub(r'<script\s+type=["\']application/ld\+json["\'][^>]*>.*?</script>',fix_block,new,flags=re.S|re.I)
            patt_og=re.compile(r'(<meta\s+property=["\']og:site_name["\']\s+content=["\'])[^"\']*(["\']\s*/?>)',re.I)
            new,n=patt_og.subn(r'\1'+TARGET+r'\2',new)
            og+=n
            if new!=raw:
                changed+=1
                print(("[THỬ] " if args.thu else "")+os.path.relpath(path,ROOT))
                if not args.thu:
                    with open(path,"w",encoding="utf-8",newline="") as f: f.write(new)
    print("File đổi:",changed,"| JSON-LD name:",json_names,"| og:site_name:",og)
    return 0

if __name__=="__main__": raise SystemExit(main())
