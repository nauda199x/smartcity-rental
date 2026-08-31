#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chuẩn hóa og:site_name trên toàn bộ HTML về một tên thương hiệu duy nhất.

Google dùng WebSite structured data ở trang chủ làm tín hiệu chính cho site
name, nhưng cũng tham khảo og:site_name. Repo có nhiều generator và nhiều trang
cũ nên thẻ này từng mang vài biến thể khác nhau. Script chỉ sửa đúng meta
og:site_name, không đụng title, H1, nội dung, canonical hay dữ liệu căn hộ.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_NAME = "Tìm Thuê Smart City"

PATTERN = re.compile(
    r'(<meta\s+property=["\']og:site_name["\']\s+content=["\'])[^"\']*(["\']\s*/?>)',
    re.IGNORECASE,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Đồng bộ og:site_name toàn site.")
    parser.add_argument("--thu", action="store_true", help="chỉ xem trước, không ghi file")
    args = parser.parse_args()

    changed = 0
    scanned = 0

    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        scanned += 1
        old = path.read_text(encoding="utf-8")
        new, n = PATTERN.subn(rf'\1{SITE_NAME}\2', old)
        if not n or new == old:
            continue

        changed += 1
        rel = path.relative_to(ROOT)
        print(f"{'[THỬ] ' if args.thu else ''}Đồng bộ: {rel}")
        if not args.thu:
            path.write_text(new, encoding="utf-8", newline="")

    print(f"Đã quét {scanned} file HTML; {'sẽ đổi' if args.thu else 'đã đổi'} {changed} file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
