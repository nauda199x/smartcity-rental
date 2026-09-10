#!/usr/bin/env python3
"""P4: làm title trang căn chi tiết duy nhất khi dữ liệu tạo ra title trùng.

Không đổi title của phần lớn căn. Chỉ khi >=2 URL `/can-ho/.../` có cùng <title>,
script thêm mã căn ở cuối title của nhóm đó. OG/Twitter title được đồng bộ; bước
tối ưu ảnh chạy sau sẽ dựng lại WebPage image schema theo title mới.

Mục đích: tránh nhiều căn cùng tòa + diện tích + giá cạnh tranh nhau bằng title
giống hệt, trong khi vẫn giữ cụm từ khóa chính ở đầu title.
"""

import argparse
import html
import os
import re
import sys
from collections import defaultdict

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAN_HO = os.path.join(GOC, "can-ho")


def title_of(text):
    m = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip() if m else ""


def code_of(text, slug):
    patterns = [
        r"<tr>\s*<td>\s*Mã căn\s*</td>\s*<td>\s*([^<]+?)\s*</td>\s*</tr>",
        r"Mã căn:\s*<b>\s*([^<]+?)\s*</b>",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I | re.S)
        if m:
            code = html.unescape(m.group(1)).strip()
            if code:
                return code
    # Fallback ổn định: chỉ dùng đoạn cuối slug, không sinh random.
    m = re.search(r"-([a-z0-9]+(?:-[a-z0-9]+)?)$", slug, re.I)
    return m.group(1).upper() if m else slug[-14:].upper()


def set_meta_title(text, old_title, new_title):
    esc_new = html.escape(new_title, quote=True)
    text = re.sub(r"<title>.*?</title>", "<title>%s</title>" % esc_new,
                  text, count=1, flags=re.I | re.S)
    text = re.sub(
        r"(<meta\s+property=[\"']og:title[\"']\s+content=[\"'])[^\"']*([\"'])",
        lambda m: m.group(1) + esc_new + m.group(2), text, count=1, flags=re.I)
    text = re.sub(
        r"(<meta\s+name=[\"']twitter:title[\"']\s+content=[\"'])[^\"']*([\"'])",
        lambda m: m.group(1) + esc_new + m.group(2), text, count=1, flags=re.I)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thu", action="store_true")
    args = ap.parse_args()
    if not os.path.isdir(CAN_HO):
        print("Không có thư mục can-ho; bỏ qua.")
        return 0

    pages = []
    groups = defaultdict(list)
    for name in sorted(os.listdir(CAN_HO)):
        path = os.path.join(CAN_HO, name, "index.html")
        if not os.path.isfile(path):
            continue
        text = open(path, encoding="utf-8").read()
        title = title_of(text)
        if not title:
            continue
        item = {"path": path, "slug": name, "text": text, "title": title}
        pages.append(item)
        groups[title].append(item)

    duplicate_groups = [items for items in groups.values() if len(items) > 1]
    changed = 0
    for items in duplicate_groups:
        for item in items:
            code = code_of(item["text"], item["slug"])
            suffix = " | %s" % code
            if item["title"].endswith(suffix):
                continue
            new_title = item["title"] + suffix
            new_text = set_meta_title(item["text"], item["title"], new_title)
            if new_text == item["text"]:
                continue
            changed += 1
            if not args.thu:
                with open(item["path"], "w", encoding="utf-8", newline="") as f:
                    f.write(new_text)

    print("P4 title dedupe: %d trang căn · %d nhóm title trùng · %d file %s." % (
        len(pages), len(duplicate_groups), changed,
        "cần đổi" if args.thu else "đã đổi"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
