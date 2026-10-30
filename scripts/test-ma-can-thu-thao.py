#!/usr/bin/env python3
"""Kiểm thử mã căn hiển thị dùng chung trong trình dựng trang SEO."""
from ma_can_hien_thi import ma_can_hien_thi, ma_can_tu_ma

assert ma_can_hien_thi({"Mã nội bộ": "TT.2N.4127", "Mã căn": "4127"}) == "4127"
assert ma_can_hien_thi({"Mã nội bộ": "TT.ST.5207"}) == "5207"
assert ma_can_hien_thi({"Mã nội bộ": "TT.2NP.1234", "Mã căn": ""}) == "1234"
assert ma_can_hien_thi({"Mã nội bộ": "CT.2N1.280"}) == "CT.2N1.280"
assert ma_can_tu_ma("TT.2N.4127") == "4127"
assert ma_can_tu_ma("CT.Stu.978") == "CT.Stu.978"
print("PASS: mã Thu Thảo là STT, nguồn An Việt giữ nguyên")
