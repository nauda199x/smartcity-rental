#!/usr/bin/env python3
"""Regression: khối 6 card phòng ngủ không được trở lại sau các lượt SEO."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "landing", ROOT / "scripts" / "toi-uu-landing-chinh.py")
landing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(landing)

home = (ROOT / "index.html").read_text(encoding="utf-8")
assert "Tìm căn hộ Smart City theo số phòng ngủ" not in home
assert landing.QUICK_START not in home and landing.QUICK_END not in home
assert "seo-rent-shortcuts" not in home

# Không làm mất bộ lọc hiện tại, lưới căn hoặc các liên kết SEO danh mục.
for required in ['id="filtersSection"', 'id="typeFilters"',
                 'id="listingGrid"', 'class="list-head"']:
    assert required in home, required
for _typ, route, _label in landing.TYPE_ROUTES:
    assert 'href="%s"' % route in home, route

rows = landing.doc_data()
stats = landing.thong_ke(rows)
updated = landing.apply(home, stats, rows)
assert landing.QUICK_START not in updated
assert "seo-rent-shortcuts" not in updated
assert "Tìm căn hộ Smart City theo số phòng ngủ" not in updated
assert not landing.audit(updated, stats), landing.audit(updated, stats)

# Mô phỏng homepage cũ có block để chắc chắn script dọn sạch,
# kể cả sau khi chạy lại nhiều lần.
old = (home.replace('<div class="list-head">',
    landing.QUICK_START + '\n<nav class="seo-rent-shortcuts">'
    'Tìm căn hộ Smart City theo số phòng ngủ</nav>\n' +
    landing.QUICK_END + '\n<div class="list-head">', 1))
cleaned = landing.apply(old, stats, rows)
assert 'seo-rent-shortcuts' not in cleaned
assert landing.QUICK_START not in cleaned
assert cleaned == landing.apply(cleaned, stats, rows), "Script SEO chưa idempotent"
print("PASS: gỡ hẳn khối phòng ngủ, giữ filter và danh sách, không tự tái tạo")
