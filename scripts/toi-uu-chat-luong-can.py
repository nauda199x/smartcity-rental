#!/usr/bin/env python3
"""P5: tăng độ khác biệt hữu ích của trang căn hộ đang index.

Không đổi URL/canonical. Script chỉ xử lý URL đang nằm trong sitemap-can-ho.xml:
- rút title >75 ký tự nhưng giữ intent thuê + dự án + mã nhận diện ngắn
- làm H1 duy nhất nếu nhiều căn cùng loại/tòa/diện tích
- làm meta description duy nhất khi bị trùng
- thêm một dòng nhận diện bằng dữ liệu thật của căn (mã, loại, diện tích, tòa, nội thất, giá, vào ở)
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
    # key=name/property, attr=description/og:title/twitter:title
    pat = re.compile(
        r"(<meta\b(?=[^>]*\b" + re.escape(key) + r"=[\"']" + re.escape(attr) +
        r"[\"'])(?=[^>]*\bcontent=[\"']))([^\"']*)([\"'][^>]*>)",
        re.I,
    )
    escaped = html.escape(value, quote=True)
    return pat.sub(lambda m: m.group(1) + escaped + m.group(3), text, count=1)


def short_id(code: str, slug: str) -> str:
    code = code.strip()
    if code:
        parts = [p for p in re.split(r"[.\s]+", code) if p]
        if len(parts) >= 2:
            s = "-".join(parts[-2:])
        else:
            s = parts[-1]
        s = re.sub(r"[^0-9A-Za-z+_-]", "", s)
        if s:
            return s[-14:]
    tail = slug.rsplit("-", 2)[-2:]
    return "-".join(tail)[-14:].upper()


def compact_title(text: str, code: str, slug: str) -> str:
    loai = table_value(text, "Loại")
    dt = table_value(text, "Diện tích")
    toa = table_value(text, "Tòa")
    gia = table_value(text, "Giá thuê")
    sid = short_id(code, slug)
    candidate = f"Cho thuê {loai} {toa} {dt} Vinhomes Smart City – {gia} · #{sid}"
    if len(candidate) <= 75:
        return candidate
    candidate = f"Cho thuê {loai} {toa} {dt} Smart City – {gia} · #{sid}"
    if len(candidate) <= 75:
        return candidate
    return candidate[:74].rstrip(" –·|")


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
            for k, v in list(value.items()):
                if k not in {"mainEntityOfPage"}:
                    walk(v)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    def repl(m: re.Match[str]) -> str:
        raw = m.group(2).strip()
        try:
            data = json.loads(html.unescape(raw))
        except (json.JSONDecodeError, TypeError):
            return m.group(0)
        before = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        walk(data)
        after = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        if after == before:
            return m.group(0)
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
    if 'class="ct-identity-note"' in text or "class='ct-identity-note'" in text:
        return re.sub(
            r"<p\s+class=[\"']ct-identity-note[\"'][^>]*>[\s\S]*?</p>",
            '<p class="ct-identity-note">%s</p>' % html.escape(note),
            text,
            count=1,
            flags=re.I,
        )
    pat = re.compile(r"(<p\s+class=[\"']tt[\"'][^>]*>[\s\S]*?</p>)", re.I)
    return pat.sub(r'\1\n  <p class="ct-identity-note">' + html.escape(note) + "</p>", text, count=1)


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
    # Fallback an toàn: chỉ chèn trong gallery rỗng nếu đúng cấu trúc generator.
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
    for p in pages:
        if p["h1"]:
            h1_groups[p["h1"]].append(p)
        if p["desc"]:
            desc_groups[p["desc"]].append(p)
    duplicate_h1 = {k for k, v in h1_groups.items() if len(v) > 1}
    duplicate_desc = {k for k, v in desc_groups.items() if len(v) > 1}

    changed = 0
    stats = collections.Counter()
    new_titles = set()

    for p in pages:
        text = p["text"]
        code = table_value(text, "Mã căn") or p["slug"]
        sid = short_id(code, p["slug"])

        tm = RE_TITLE.search(text)
        old_title = plain(tm.group(1)) if tm else ""
        if old_title and len(old_title) > 75:
            new_title = compact_title(text, code, p["slug"])
            # Bảo đảm không vô tình tạo title trùng sau khi rút gọn.
            if new_title in new_titles:
                new_title = (new_title[: max(20, 70 - len(code))].rstrip(" –·|") + " · " + code)[:75]
            if new_title != old_title:
                text = RE_TITLE.sub("<title>%s</title>" % html.escape(new_title), text, count=1)
                text = set_meta_content(text, "property", "og:title", new_title)
                text = set_meta_content(text, "name", "twitter:title", new_title)
                stats["title"] += 1
                old_title = new_title
        if old_title:
            new_titles.add(old_title)

        if p["h1"] in duplicate_h1 and f"#{sid}" not in p["h1"]:
            new_h1 = p["h1"] + f" · Căn #{sid}"
            text = RE_H1.sub("<h1>%s</h1>" % html.escape(new_h1), text, count=1)
            stats["h1"] += 1

        if p["desc"] in duplicate_desc and code.lower() not in p["desc"].lower():
            new_desc = p["desc"].rstrip(" .") + f". Mã căn {code}."
            text = set_meta_content(text, "name", "description", new_desc)
            stats["description"] += 1

        note = identity_note(text, code)
        before = text
        text = add_identity_note(text, note)
        if text != before:
            stats["identity"] += 1

        before = text
        text = update_listing_schema(text, code, p["loc"])
        if text != before:
            stats["schema"] += 1

        before = text
        text = add_media_fallback(text, code)
        if text != before:
            stats["media_fallback"] += 1

        if text != p["text"]:
            changed += 1
            if not dry:
                p["path"].write_text(text, encoding="utf-8", newline="")

    mode = "cần đổi" if dry else "đã tối ưu"
    print(f"P5 chất lượng trang căn: {len(pages)} URL · {changed} file {mode}.")
    print(
        "Chi tiết: title=%d · H1=%d · description=%d · identity=%d · schema=%d · media fallback=%d"
        % (stats["title"], stats["h1"], stats["description"], stats["identity"], stats["schema"], stats["media_fallback"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
