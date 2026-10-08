"""
Phân vùng khí hậu Việt Nam cho tính toán điện mặt trời.
Dựa trên phân loại của Bộ Xây dựng (TCVN 4100:2014) và nghiên cứu NIAPP.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ClimateZone:
    """Thông tin một vùng khí hậu."""

    code: str
    name: str
    # Bức xạ nằm ngang toàn phần trung bình năm (kWh/m²/ngày)
    ghi_annual_avg: float
    # Nhiệt độ không khí trung bình năm (°C)
    temp_avg_c: float
    # Góc nghiêng tối ưu tấm pin (°)
    optimal_tilt: float
    # Các tỉnh đại diện
    provinces: tuple[str, ...]


VIETNAM_CLIMATE_ZONES: dict[str, ClimateZone] = {
    "north_humid": ClimateZone(
        code="north_humid",
        name="Bắc Bộ — Ẩm ướt, nhiều mây",
        ghi_annual_avg=3.8,
        temp_avg_c=24.0,
        optimal_tilt=20.0,
        provinces=("Hà Nội", "Hải Phòng", "Nam Định", "Ninh Bình", "Thái Bình"),
    ),
    "north_mountain": ClimateZone(
        code="north_mountain",
        name="Tây Bắc — Núi cao, biên độ nhiệt lớn",
        ghi_annual_avg=4.2,
        temp_avg_c=20.0,
        optimal_tilt=22.0,
        provinces=("Sơn La", "Điện Biên", "Lai Châu", "Lào Cai", "Hà Giang"),
    ),
    "central_coast": ClimateZone(
        code="central_coast",
        name="Duyên hải Nam Trung Bộ — Nắng nhiều, gió mạnh",
        ghi_annual_avg=5.5,
        temp_avg_c=27.5,
        optimal_tilt=14.0,
        provinces=(
            "Đà Nẵng", "Quảng Nam", "Quảng Ngãi", "Bình Định",
            "Phú Yên", "Khánh Hòa", "Ninh Thuận", "Bình Thuận",
        ),
    ),
    "central_highlands": ClimateZone(
        code="central_highlands",
        name="Tây Nguyên — Bức xạ cao, mưa mùa rõ rệt",
        ghi_annual_avg=5.7,
        temp_avg_c=22.0,
        optimal_tilt=13.0,
        provinces=("Gia Lai", "Đắk Lắk", "Đắk Nông", "Kon Tum", "Lâm Đồng"),
    ),
    "south": ClimateZone(
        code="south",
        name="Nam Bộ — Nắng ổn định, ít mây mùa khô",
        ghi_annual_avg=5.2,
        temp_avg_c=28.0,
        optimal_tilt=10.0,
        provinces=(
            "TP. Hồ Chí Minh", "Bình Dương", "Đồng Nai", "Bà Rịa - Vũng Tàu",
            "Long An", "Tiền Giang", "Cần Thơ", "An Giang", "Kiên Giang",
        ),
    ),
}


def get_climate_zone(province: str) -> ClimateZone | None:
    """
    Trả về vùng khí hậu cho một tỉnh/thành phố.

    Parameters
    ----------
    province : str
        Tên tỉnh/thành phố (không phân biệt hoa thường).

    Returns
    -------
    ClimateZone or None
    """
    province_lower = province.lower()
    for zone in VIETNAM_CLIMATE_ZONES.values():
        if any(p.lower() in province_lower or province_lower in p.lower() for p in zone.provinces):
            return zone
    return None
