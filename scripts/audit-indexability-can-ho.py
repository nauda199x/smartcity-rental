#!/usr/bin/env python3
"""Audit indexability cho toàn bộ URL căn hộ đang nằm trong sitemap-can-ho.xml.

Mục tiêu: bắt lỗi trước khi Google Search Console phải báo. Script chỉ đọc repo,
không sửa HTML. Exit 1 khi có lỗi có thể cản index/crawl; warning không làm fail.

Kiểm tra mỗi URL căn hộ:
- file HTML tồn tại
- index/follow, không noindex
- canonical self đúng tuyệt đối
- title, H1, meta description tồn tại; title không trùng giữa các URL sitemap
- JSON-LD có RealEstateListing + BreadcrumbList; URL listing khớp canonical
- có og:image và nếu ảnh thuộc chính domain thì file ảnh tồn tại
- có ít nhất một liên kết <a href> nội bộ từ một trang HTML khác trỏ tới URL
- URL sitemap không trùng và không chứa query/hash

Chạy: python3 scripts/audit-indexability-can-ho.py
"""

from __future__ import annotations

import collections
import html
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

GOC = Path(__file__).resolve().parent.parent
TEN_MIEN = "https://timthuesmartcity.com"
SITEMAP = GOC / "sitemap-can-ho.xml"

RE_URL_BLOCK = re.compile(r"<url>([\s\S]*?)</url>", re.I)
RE_LOC = re.compile(r"<loc>([^<]+)</loc>", re.I)
RE_TITLE = re.compile(r"<title>([\s\S]*?)</title>", re.I)
RE_H1 = re.compile(r"<h1\b[^>]*>([\s\S]*?)</h1>", re.I)
RE_META_DESC = re.compile(
    r"<meta\b(?=[^>]*\bname=[\"']description[\"'])(?=[^>]*\bcontent=[\"']([^\"']*)[\"'])[^>]*>",
    re.I,
)
RE_META_ROBOTS = re.compile(
    r"<meta\b(?=[^>]*\bname=[\"']robots[\"'])(?=[^>]*\bcontent=[\"']([^\"']*)[\"'])[^>]*>",
    re.I,
)
RE_CANONICAL = re.compile(
    r"<link\b(?=[^>]*\brel=[\"']canonical[\"'])(?=[^>]*\bhref=[\"']([^\"']+)[\"'])[^>]*>",
    re.I,
)
RE_OG_IMAGE = re.compile(
    r"<meta\b(?=[^>]*\bproperty=[\"']og:image[\"'])(?=[^>]*\bcontent=[\"']([^\"']+)[\"'])[^>]*>",
    re.I,
)
RE_JSONLD = re.compile(
    r"<script\b[^>]*\btype=[\"']application/ld\+json[\"'][^>]*>([\s\S]*?)</script>",
    re.I,
)
RE_A_HREF = re.compile(r"<a\b[^>]*\bhref=[\"']([^\"']+)[\"'][^>]*>", re.I)
RE_SCRIPT_STYLE = re.compile(r"<(script|style|noscript)\b[\s\S]*?</\1>", re.I)
RE_TAG = re.compile(r"<[^>]+>")


def text_plain(fragment: str) -> str:
    fragment = RE_SCRIPT_STYLE.sub(" ", fragment)
    fragment = RE_TAG.sub(" ", fragment)
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip()


def one(pattern: re.Pattern[str], text: str) -> str:
    m = pattern.search(text)
    return html.unescape(m.group(1)).strip() if m else ""


def loc_to_file(loc: str) -> Path | None:
    if not loc.startswith(TEN_MIEN + "/can-ho/") or not loc.endswith("/"):
        return None
    parsed = urlparse(loc)
    if parsed.query or parsed.fragment:
        return None
    rel = parsed.path.lstrip("/") + "index.html"
    return GOC / rel


def iter_schema_nodes(value):
    if isinstance(value, dict):
        yield value
        graph = value.get("@graph")
        if graph is not None:
            yield from iter_schema_nodes(graph)
    elif isinstance(value, list):
        for item in value:
            yield from iter_schema_nodes(item)


def type_has(node: dict, wanted: str) -> bool:
    typ = node.get("@type")
    if isinstance(typ, str):
        return typ == wanted
    if isinstance(typ, list):
        return wanted in typ
    return False


def normalize_internal_href(href: str) -> str | None:
    href = html.unescape(href.strip())
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    if href.startswith(TEN_MIEN):
        href = href[len(TEN_MIEN):]
    elif href.startswith("http://") or href.startswith("https://") or href.startswith("//"):
        return None
    if not href.startswith("/"):
        return None
    href = href.split("#", 1)[0].split("?", 1)[0]
    return href or "/"


def build_inbound_counts(target_paths: set[str]) -> tuple[dict[str, int], dict[str, set[str]]]:
    counts = {p: 0 for p in target_paths}
    sources = {p: set() for p in target_paths}
    for path in GOC.rglob("*.html"):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        source_rel = path.relative_to(GOC).as_posix()
        for href in RE_A_HREF.findall(text):
            internal = normalize_internal_href(href)
            if internal not in target_paths:
                continue
            target_rel = internal.lstrip("/") + "index.html"
            if source_rel == target_rel:
                continue
            if source_rel not in sources[internal]:
                sources[internal].add(source_rel)
                counts[internal] += 1
    return counts, sources


def main() -> int:
    if not SITEMAP.exists():
        print("CRITICAL: không tìm thấy sitemap-can-ho.xml")
        return 1

    sitemap_text = SITEMAP.read_text(encoding="utf-8")
    locs = []
    for block in RE_URL_BLOCK.findall(sitemap_text):
        m = RE_LOC.search(block)
        if m:
            locs.append(html.unescape(m.group(1)).strip())

    apartment_locs = [u for u in locs if u.startswith(TEN_MIEN + "/can-ho/") and u != TEN_MIEN + "/can-ho/"]
    duplicate_locs = [u for u, n in collections.Counter(apartment_locs).items() if n > 1]

    critical: list[str] = []
    warnings: list[str] = []
    if duplicate_locs:
        critical.append("Sitemap có URL căn hộ trùng: " + ", ".join(duplicate_locs[:10]))

    target_paths = set()
    for loc in apartment_locs:
        p = urlparse(loc)
        if p.query or p.fragment:
            critical.append(f"{loc}: sitemap URL chứa query/hash")
        if not loc.endswith("/"):
            critical.append(f"{loc}: URL không có trailing slash")
        target_paths.add(p.path)

    inbound, inbound_sources = build_inbound_counts(target_paths)

    titles: dict[str, list[str]] = collections.defaultdict(list)
    descriptions: dict[str, list[str]] = collections.defaultdict(list)
    h1s: dict[str, list[str]] = collections.defaultdict(list)
    checked = 0
    local_og_images = 0
    video_only_like = 0

    for loc in sorted(set(apartment_locs)):
        file_path = loc_to_file(loc)
        if file_path is None:
            critical.append(f"{loc}: cấu trúc URL không hợp lệ")
            continue
        if not file_path.is_file():
            critical.append(f"{loc}: không có file {file_path.relative_to(GOC)}")
            continue

        checked += 1
        text = file_path.read_text(encoding="utf-8")

        robots_values = [html.unescape(x).strip().lower() for x in RE_META_ROBOTS.findall(text)]
        if any("noindex" in x or re.search(r"(^|[,\s])none([,\s]|$)", x) for x in robots_values):
            critical.append(f"{loc}: đang noindex nhưng vẫn nằm trong sitemap")
        if not robots_values:
            warnings.append(f"{loc}: không có meta robots (mặc định vẫn index được)")

        canonicals = [html.unescape(x).strip() for x in RE_CANONICAL.findall(text)]
        if len(canonicals) != 1:
            critical.append(f"{loc}: cần đúng 1 canonical, hiện có {len(canonicals)}")
        elif canonicals[0] != loc:
            critical.append(f"{loc}: canonical sai -> {canonicals[0]}")

        title_matches = RE_TITLE.findall(text)
        title = text_plain(title_matches[0]) if title_matches else ""
        if len(title_matches) != 1 or not title:
            critical.append(f"{loc}: title thiếu hoặc có nhiều hơn 1 thẻ")
        else:
            titles[title].append(loc)
            if len(title) > 75:
                warnings.append(f"{loc}: title dài {len(title)} ký tự")

        h1_matches = RE_H1.findall(text)
        h1 = text_plain(h1_matches[0]) if h1_matches else ""
        if len(h1_matches) != 1 or not h1:
            critical.append(f"{loc}: H1 thiếu hoặc có nhiều hơn 1 thẻ")
        else:
            h1s[h1].append(loc)

        desc = one(RE_META_DESC, text)
        if not desc:
            critical.append(f"{loc}: thiếu meta description")
        else:
            descriptions[desc].append(loc)
            if len(desc) < 90:
                warnings.append(f"{loc}: meta description khá ngắn ({len(desc)} ký tự)")

        schema_nodes = []
        schema_parse_errors = 0
        for raw in RE_JSONLD.findall(text):
            try:
                data = json.loads(html.unescape(raw).strip())
                schema_nodes.extend(iter_schema_nodes(data))
            except (json.JSONDecodeError, TypeError):
                schema_parse_errors += 1
        if schema_parse_errors:
            critical.append(f"{loc}: có {schema_parse_errors} JSON-LD không parse được")

        listings = [n for n in schema_nodes if isinstance(n, dict) and type_has(n, "RealEstateListing")]
        breadcrumbs = [n for n in schema_nodes if isinstance(n, dict) and type_has(n, "BreadcrumbList")]
        if not listings:
            critical.append(f"{loc}: thiếu RealEstateListing schema")
        else:
            listing_urls = [str(n.get("url", "")).strip() for n in listings if n.get("url")]
            if loc not in listing_urls:
                critical.append(f"{loc}: RealEstateListing.url không khớp URL trang")
        if not breadcrumbs:
            critical.append(f"{loc}: thiếu BreadcrumbList schema")

        og_image = one(RE_OG_IMAGE, text)
        if not og_image:
            warnings.append(f"{loc}: thiếu og:image")
        else:
            if og_image.startswith(TEN_MIEN + "/"):
                local_og_images += 1
                image_path = GOC / urlparse(og_image).path.lstrip("/")
                if not image_path.is_file():
                    warnings.append(f"{loc}: og:image local không tồn tại trong repo -> {og_image}")

        has_img = bool(re.search(r"<img\b", text, re.I))
        has_video = bool(re.search(r"<(video|source)\b", text, re.I)) or "VIDEO" in text
        if not has_img and not has_video:
            warnings.append(f"{loc}: không thấy ảnh hoặc video trong nội dung")
        elif not has_img and has_video:
            video_only_like += 1

        path_only = urlparse(loc).path
        if inbound.get(path_only, 0) == 0:
            critical.append(f"{loc}: không có internal link <a href> từ trang HTML khác")

        body_text = text_plain(text)
        if len(body_text) < 500:
            warnings.append(f"{loc}: lượng text HTML thấp ({len(body_text)} ký tự)")

    for title, urls in titles.items():
        if len(urls) > 1:
            critical.append(f"TITLE TRÙNG ({len(urls)} URL): {title} -> " + ", ".join(urls[:6]))
    for desc, urls in descriptions.items():
        if len(urls) > 1:
            warnings.append(f"DESCRIPTION TRÙNG ({len(urls)} URL): {desc[:90]}...")
    for h1, urls in h1s.items():
        if len(urls) > 1:
            warnings.append(f"H1 TRÙNG ({len(urls)} URL): {h1}")

    print("=" * 72)
    print("AUDIT INDEXABILITY CĂN HỘ — timthuesmartcity.com")
    print("=" * 72)
    print(f"URL căn hộ trong sitemap : {len(apartment_locs)}")
    print(f"Trang HTML đã kiểm tra   : {checked}")
    print(f"Title duy nhất           : {len(titles)}")
    print(f"OG image cùng domain     : {local_og_images}")
    print(f"Trang dạng video-only    : {video_only_like}")
    if checked:
        inbound_values = [inbound.get(urlparse(u).path, 0) for u in set(apartment_locs)]
        print(f"Inbound internal link    : min={min(inbound_values)} · median={sorted(inbound_values)[len(inbound_values)//2]} · max={max(inbound_values)}")
    print(f"CRITICAL                 : {len(critical)}")
    print(f"WARNING                  : {len(warnings)}")

    if critical:
        print("\nCRITICAL — có thể cản index/crawl:")
        for item in critical[:120]:
            print("  -", item)
        if len(critical) > 120:
            print(f"  ... và {len(critical) - 120} lỗi nữa")

    if warnings:
        print("\nWARNING — nên tối ưu nhưng không trực tiếp chặn index:")
        for item in warnings[:80]:
            print("  -", item)
        if len(warnings) > 80:
            print(f"  ... và {len(warnings) - 80} cảnh báo nữa")

    if critical:
        print("\nKẾT LUẬN: FAIL — còn lỗi indexability cần sửa.")
        return 1
    print("\nKẾT LUẬN: PASS — không phát hiện lỗi kỹ thuật chặn index trong sitemap căn hộ.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
