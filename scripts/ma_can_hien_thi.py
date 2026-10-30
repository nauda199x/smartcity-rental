"""Mã căn công khai theo nguồn, tách khỏi khóa định danh nội bộ của hệ thống."""
import re

MA_THU_THAO = re.compile(r"^TT\.(?:ST|1N|2N|2NP|3N)\.(\d{3,6})$")


def ma_can_tu_ma(ma):
    """Dự phòng cho trang đã thuê chỉ còn lưu khóa nội bộ."""
    ma = str(ma or "").strip()
    m = MA_THU_THAO.fullmatch(ma)
    return m.group(1) if m else ma


def ma_can_hien_thi(can):
    """Nguồn Thu Thảo: STT cột A; mọi nguồn cũ giữ nguyên mã."""
    ma = str(can.get("Mã nội bộ", "") or "").strip()
    m = MA_THU_THAO.fullmatch(ma)
    if not m:
        return ma
    stt = str(can.get("Mã căn", "") or "").strip()
    return stt if re.fullmatch(r"\d{3,6}", stt) else m.group(1)
