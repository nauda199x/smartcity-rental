#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0 SEO audit: ngăn URL query/filter trở thành trang crawl/index riêng.

Mục tiêu:
- Bộ lọc homepage vẫn dùng query để chia sẻ cho khách (Zalo/Facebook) nếu cần.
- Nhưng website không được tự tạo đường dẫn crawlable tới các URL query.
- Homepage query phải có query guard noindex + canonical sạch.
- Sitemap tuyệt đối không chứa URL có query.
- robots.txt không được chặn query, vì chặn crawl sẽ khiến Google không đọc được noindex.

Script chỉ đọc file, không sửa nội dung. Exit 1 khi phát hiện lỗi P0.
"""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {"timthuesmartcity.com", "www.timthuesmartcity.com"}
SKIP_DIRS = {".git", ".github", "node_modules"}

# Các query đang dùng thật trên homepage. Nếu sau này thêm filter mới, audit vẫn
# bắt mọi query internal crawlable; danh sách này dùng để in log dễ đọc hơn.
SEO_QUERY_KEYS = {
    "loai", "pk", "gia", "noithat", "q", "moi", "form"
}

CANONICAL_HOME = "https://timthuesmartcity.com/"
RE_CANONICAL = re.compile(
    r'<link\b(?=[^>]*\brel\s*=\s*["\']canonical["\'])(?=[^>]*\bhref\s*=\s*["\']([^"\']+)["\'])[^>]*>',
    re.I,
)


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        data = {str(k).lower(): (v or "") for k, v in attrs}
        href = data.get("href", "").strip()
        if not href:
            return
        rel = {x.lower() for x in data.get("rel", "").split() if x}
        self.links.append((href, rel))


def html_files():
    for path in ROOT.rglob("*.html"):
        rel_parts = path.relative_to(ROOT).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        yield path


def is_internal_query(href):
    """Trả (True, keys) nếu href là URL nội bộ có query; ngược lại False."""
    raw = href.strip()
    if not raw or raw.startswith("#"):
        return False, set()

    low = raw.lower()
    if low.startswith(("mailto:", "tel:", "javascript:", "data:", "blob:", "sms:")):
        return False, set()

    parsed = urlsplit(raw if not raw.startswith("//") else "https:" + raw)
    if parsed.scheme in ("http", "https") or parsed.netloc:
        host = (parsed.hostname or "").lower()
        if host not in HOSTS:
            return False, set()

    if not parsed.query:
        return False, set()

    keys = {k.lower() for k, _ in parse_qsl(parsed.query, keep_blank_values=True)}
    return True, keys


def audit_internal_query_links():
    violations = []
    nofollow_ok = []

    for path in html_files():
        raw = path.read_text(encoding="utf-8", errors="replace")
        parser = AnchorParser()
        try:
            parser.feed(raw)
        except Exception:
            # HTMLParser rất chịu lỗi; nhánh này chỉ để audit không văng vì một file lạ.
            continue

        relpath = path.relative_to(ROOT).as_posix()
        for href, rel in parser.links:
            internal, keys = is_internal_query(href)
            if not internal:
                continue
            item = (relpath, href, sorted(keys), sorted(keys & SEO_QUERY_KEYS))
            if "nofollow" in rel:
                nofollow_ok.append(item)
            else:
                violations.append(item)

    return violations, nofollow_ok


def audit_sitemaps():
    bad = []
    for path in ROOT.glob("sitemap*.xml"):
        raw = path.read_text(encoding="utf-8", errors="replace")
        for loc in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", raw, flags=re.I):
            if "?" in loc:
                bad.append((path.name, loc.strip()))
    return bad


def audit_home_guard():
    path = ROOT / "index.html"
    if not path.exists():
        return ["Thiếu index.html"]

    raw = path.read_text(encoding="utf-8", errors="replace")
    errors = []
    canons = RE_CANONICAL.findall(raw)

    if CANONICAL_HOME not in canons:
        errors.append(f"Homepage thiếu canonical chuẩn {CANONICAL_HOME}")
    if "SEO-QUERY-GUARD:START" not in raw or "SEO-QUERY-GUARD:END" not in raw:
        errors.append("Homepage thiếu marker SEO-QUERY-GUARD")
    if "noindex,follow,max-image-preview:large" not in raw.replace(" ", ""):
        errors.append("Homepage query guard chưa đặt noindex,follow")
    if "window.location.search" not in raw:
        errors.append("Homepage query guard không kiểm tra location.search")

    return errors


def audit_robots():
    path = ROOT / "robots.txt"
    if not path.exists():
        return ["Thiếu robots.txt"]
    bad = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("disallow:") and "?" in stripped:
            bad.append(stripped)
    return bad


def main():
    failures = 0
    query_bad, query_nofollow = audit_internal_query_links()
    sitemap_bad = audit_sitemaps()
    guard_bad = audit_home_guard()
    robots_bad = audit_robots()

    print("=" * 78)
    print("P0 QUERY URL / INDEXING AUDIT — timthuesmartcity.com")
    print("=" * 78)

    print("\n1. INTERNAL QUERY LINKS")
    if query_bad:
        for src, href, keys, seo_keys in query_bad:
            marker = f" · SEO keys={','.join(seo_keys)}" if seo_keys else ""
            print(f"FAIL {src} -> {href} · keys={','.join(keys) or '(none)'}{marker}")
            failures += 1
    else:
        print("PASS — không có internal query URL crawlable.")
    if query_nofollow:
        print(f"INFO — {len(query_nofollow)} query link có rel=nofollow (không tính lỗi).")

    print("\n2. SITEMAPS")
    if sitemap_bad:
        for name, loc in sitemap_bad:
            print(f"FAIL {name}: {loc}")
            failures += 1
    else:
        print("PASS — sitemap không chứa URL query.")

    print("\n3. HOMEPAGE QUERY GUARD")
    if guard_bad:
        for msg in guard_bad:
            print("FAIL", msg)
            failures += 1
    else:
        print("PASS — canonical homepage sạch + query guard noindex/follow đang có.")

    print("\n4. ROBOTS.TXT")
    if robots_bad:
        for rule in robots_bad:
            print(f"FAIL không chặn query trong robots.txt: {rule}")
            failures += 1
        print("     Lý do: Google phải crawl được URL query mới đọc được noindex.")
    else:
        print("PASS — robots.txt cho phép crawler đọc query guard/noindex.")

    print("\n" + "=" * 78)
    if failures:
        print(f"KẾT QUẢ: FAIL — {failures} lỗi P0")
    else:
        print("KẾT QUẢ: PASS — query URL không cạnh tranh index với URL SEO sạch")
    print("=" * 78)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
