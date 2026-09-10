#!/usr/bin/env python3
"""P5: tăng độ khác biệt hữu ích của trang căn hộ đang index.

Không đổi URL/canonical. Script chỉ xử lý URL đang nằm trong sitemap-can-ho.xml:
- rút title >75 ký tự nhưng giữ intent thuê + dự án + mã nhận diện ngắn
- làm H1 duy nhất nếu nhiều căn cùng loại/tòa/diện tích
- làm meta description duy nhất khi bị trùng
- thêm một dòng nhận diện bằng dữ liệu thật của căn
- thêm identifier/mainEntityOfPage vào RealEstateListing JSON-LD
- nếu căn chưa có ảnh/video thật, hiển thị og:image làm ảnh minh họa và ghi rõ là ảnh minh họa

Chạy nhiều lần không nhân bản nội dung. Dùng --thu để chỉ xem trước.
"""

from __future__ import annotations

import collections
import html
import json
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
RE_META_DESC = re.compile(r"<meta\b(?=[^>]*\bname=[\"']description[\"'])(?=[^>]*\bcontent=[\"']([^\"']*)[\"'])[^>]*>", re.I)
RE_OG_IMAGE = re.compile(r"<meta\b(?=[^>]*\bproperty=[\"']og:image[\"'])(?=[^>]*\bcontent=[\"']([^\"']+)[\"'])[^>]*>", re.I)
RE_JSONLD_BLOCK = re.compile(r"(<script\b[^>]*\btype=[\"']application/ld\+json[\"'][^>]*>)([\s\S]*?)(</script>)", re.I)
RE_TAG = re.compile(r"<[^>]+>")
RE_SCRIPT_STYLE = re.compile(r"<(script|style|noscript)\b[\s\S]*?</\1>", re.I)


def plain(fragment: str) -> str:
    fragment = RE_SCRIPT_STYLE.sub(" ", fragment)
    fragment = RE_TAG.sub(" ", fragment)
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip()


def sitemap_urls() -> list[str]:
    text = SITEMAP.read_text(encoding="utf-8")
    out = []
    for block in RE_URL_BLOCK.findall(text):
        m = RE_LOC.search(block)
        if not m:
            continue
        loc = html.unescape(m.group(1)).strip()
        if loc.startswith(TEN_MIEN + "/can-ho/") and loc != TEN_MIEN + "/can-ho/":
            out.append(loc)
    return sorted(set(out))


def file_for(loc: str) -> Path:
    return GOC / (urlparse(loc).path.lstrip("/") + "index.html")


def table_value(text: str, label: str) -> str:
    pat = re.compile(
        r"<tr>\s*<td>\s*" + re.escape(label) + r"\s*</td>\s*<td>\s*([\s\S]*?)\s*</td>\s*</tr>",
        re.I,
    )
    m = pat.search(text)
    return plain(m.group(1)) if m else ""


def meta_value(text: str, pattern: re.Pattern[str]) -> str:
    m = pattern.search(text)
    return html.unescape(m.group(1)).strip() if m else ""


def set_meta_content(text: str, key: str, attr: str, value: str) -> str:
    """Thay content của đúng meta tag, không phụ thuộc thứ tự attribute."""
    tag_pat = re.compile(
        r"<meta\b[^>]*\b" + re.escape(key) + r"=[\"']" + re.escape(attr) + r"[\"'][^>]*>",
        re.I,
    )
    m = tag_pat.search(text)
    if not m:
        return text
    tag = m.group(0)
    content_pat = re.compile(r"(\bcontent=[\"'])[^\"']*([\"'])", re.I)
    escaped = html.escape(value, quote=True)
    new_tag, n = content_pat.subn(lambda x: x.group(1) + escaped + x.group(2), tag, count=1)
    if not n:
        return text
    return text[:m.start()] + new_tag + text[m.end():]


def short_id(code: str, slug: str) -> str:
    code = code.strip()
    if code:
        parts = [p for p in re.split(r"[.\s]+", code) if p]
        if len(parts) >= 2:
            value = "-".join(parts[-2:])
        else:
            value = parts[-1]
        value = re.sub(r"[^0-9A-Za-z+_-]", "", value)
        if value:
            return value[-14:]
    return "-".join(slug.rsplit("-", 2)[-2:])[-14:].upper()


def compact_title(text: str, code: str, slug: str) -> str:
    loai = table_value(text, "Loại")
    dt = table_value(text, "Diện tích")
    toa = table_value(text, "Tòa")
    gia = table_value(text, "Giá thuê")
    sid = short_id(code, slug)
    candidates = [
        f"Cho thuê {loai} {toa} {dt} Vinhomes Smart City – {gia} · #{sid}",
        f"Cho thuê căn {loai} {toa} {dt} Smart City – {gia} · #{sid}",
        f"Thuê {loai} {toa} {dt} Smart City – {gia} · #{sid}",
        f"Thuê {loai} {toa} {dt} Smart City · #{sid}",
    ]
    for candidate in candidates:
        if len(candidate) <= 75:
            return candidate
    return candidates[-1]


def update_listing_schema(text: str, code: str, loc: str) -> str:
    def walk(value):
        if isinstance(value, dict):
            typ = value.get("@type")
            types = [typ] if isinstance(typ, str) else typ if isinstance(typ, list) else []
            if "RealEstateListing" in types:
                value["identifier"] = code
                value["mainEntityOfPage"] = {"@type": "WebPage", "@id": loc}
                about = value.get("about")
                if isinstance(about, dict) and code:
                    about["identifier"] = code
            for key, child in list(value.items()):
                if key != "mainEntityOfPage":
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    def repl(m: re.Match[str]) -> str:
        raw = m.group(2).strip()
        try:
            data = json.loads(html.unescape(raw))
        except (json.JSONDecodeError, TypeError):
            return m.group(0)
        before = json.dumps(data, ensure_ascii=False, sort_keys=True)
        walk(data)
        after_compare = json.dumps(data, ensure_ascii=False, sort_keys=True)
        if after_compare == before:
            return m.group(0)
        after = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return m.group(1) + after + m.group(3)

    return RE_JSONLD_BLOCK.sub(repl, text)


def identity_note(text: str, code: str) -> str:
    loai = table_value(text, "Loại") or "căn hộ"
    dt = table_value(text, "Diện tích")
    toa = table_value(text, "Tòa")
    noi_that = table_value(text, "Nội thất")
    gia = table_value(text, "Giá thuê")
    vao_o = table_value(text, "Ngày vào ở")
    parts = [f"Mã căn {code}: {loai}"]
    if dt:
        parts.append(dt)
    if toa:
        parts.append(f"tòa {toa}")
    if noi_that:
        parts.append(noi_that.lower())
    if gia:
        parts.append(f"giá {gia}")
    if vao_o:
        parts.append(vao_o.lower())
    return "; ".join(parts) + "."


def add_identity_note(text: str, note: str) -> str:
    existing = re.compile(r"<p\s+class=[\"']ct-identity-note[\"'][^>]*>[\s\S]*?</p>", re.I)
    replacement = '<p class="ct-identity-note">%s</p>' % html.escape(note)
    if existing.search(text):
        return existing.sub(replacement, text, count=1)
    pat = re.compile(r"(<p\s+class=[\"']tt[\"'][^>]*>[\s\S]*?</p>)", re.I)
    return pat.sub(r"\1\n  " + replacement, text, count=1)


def add_media_fallback(text: str, code: str) -> str:
    if re.search(r"<img\b", text, re.I) or re.search(r"<(video|source)\b", text, re.I):
        return text
    og = meta_value(text, RE_OG_IMAGE)
    if not og:
        return text
    parsed = urlparse(og)
    if parsed.netloc and parsed.netloc != urlparse(TEN_MIEN).netloc:
        return text
    src = parsed.path or og
    if not src.startswith("/"):
        return text
    figure = (
        '<figure class="ct-media-fallback">'
        '<img src="%s" alt="Ảnh minh họa Vinhomes Smart City cho căn %s; ảnh thực tế đang cập nhật" '
        'loading="eager" decoding="async" width="800" height="600">'
        '<figcaption>Ảnh minh họa khu đô thị; ảnh thực tế căn %s đang được cập nhật.</figcaption>'
        '</figure>\n    '
    ) % (html.escape(src, quote=True), html.escape(code, quote=True), html.escape(code))
    marker = '<div class="ct-no-photo">'
    if marker in text:
        return text.replace(marker, figure + marker, 1)
    pat = re.compile(r"(<section\s+class=[\"'][^\"']*ct-gallery-empty-source[^\"']*[\"'][^>]*>)", re.I)
    return pat.sub(r"\1\n    " + figure, text, count=1)


def main() -> int:
    dry = "--thu" in sys.argv
    if not SITEMAP.exists():
        print("Không tìm thấy sitemap-can-ho.xml")
        return 1

    pages = []
    for loc in sitemap_urls():
        path = file_for(loc)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        h1m = RE_H1.search(text)
        descm = RE_META_DESC.search(text)
        pages.append({
            "loc": loc,
            "path": path,
            "slug": urlparse(loc).path.rstrip("/").split("/")[-1],
            "text": text,
            "h1": plain(h1m.group(1)) if h1m else "",
            "desc": html.unescape(descm.group(1)).strip() if descm else "",
        })

    h1_groups = collections.defaultdict(list)
    desc_groups = collections.defaultdict(list)
    for page in pages:
        if page["h1"]:
            h1_groups[page["h1"]].append(page)
        if page["desc"]:
            desc_groups[page["desc"]].append(page)
    duplicate_h1 = {key for key, values in h1_groups.items() if len(values) > 1}
    duplicate_desc = {key for key, values in desc_groups.items() if len(values) > 1}

    changed = 0
    stats = collections.Counter()

    for page in pages:
        text = page["text"]
        code = table_value(text, "Mã căn") or page["slug"]
        sid = short_id(code, page["slug"])

        tm = RE_TITLE.search(text)
        old_title = plain(tm.group(1)) if tm else ""
        if old_title and len(old_title) > 75:
            new_title = compact_title(text, code, page["slug"])
            if new_title != old_title:
                text = RE_TITLE.sub("<title>%s</title>" % html.escape(new_title), text, count=1)
                text = set_meta_content(text, "property", "og:title", new_title)
                text = set_meta_content(text, "name", "twitter:title", new_title)
                stats["title"] += 1

        if page["h1"] in duplicate_h1 and f"#{sid}" not in page["h1"]:
            new_h1 = page["h1"] + f" · Căn #{sid}"
            text = RE_H1.sub("<h1>%s</h1>" % html.escape(new_h1), text, count=1)
            stats["h1"] += 1

        if page["desc"] in duplicate_desc and code.lower() not in page["desc"].lower():
            new_desc = page["desc"].rstrip(" .") + f". Mã căn {code}."
            updated = set_meta_content(text, "name", "description", new_desc)
            if updated != text:
                text = updated
                stats["description"] += 1

        note = identity_note(text, code)
        before = text
        text = add_identity_note(text, note)
        if text != before:
            stats["identity"] += 1

        before = text
        text = update_listing_schema(text, code, page["loc"])
        if text != before:
            stats["schema"] += 1

        before = text
        text = add_media_fallback(text, code)
        if text != before:
            stats["media_fallback"] += 1

        if text != page["text"]:
            changed += 1
            if not dry:
                page["path"].write_text(text, encoding="utf-8", newline="")

    mode = "cần đổi" if dry else "đã tối ưu"
    print(f"P5 chất lượng trang căn: {len(pages)} URL · {changed} file {mode}.")
    print(
        "Chi tiết: title=%d · H1=%d · description=%d · identity=%d · schema=%d · media fallback=%d"
        % (stats["title"], stats["h1"], stats["description"], stats["identity"], stats["schema"], stats["media_fallback"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
