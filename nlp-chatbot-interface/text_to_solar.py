"""
Text-to-Solar Engine
====================
Luồng xử lý chính: Câu hỏi tiếng Việt → Trích xuất thực thể → pvlib → Báo cáo TV.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import sys
import os

# Thêm đường dẫn đến solar-physics-vn
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solar-physics-vn"))


@dataclass
class SolarQuery:
    """Kết quả trích xuất thực thể từ câu hỏi người dùng."""
    raw_text: str
    # Hướng mái (Nam, Đông Nam, Đông, ...)
    roof_direction: Optional[str] = None
    # Diện tích mái (m²)
    roof_area_m2: Optional[float] = None
    # Hóa đơn điện hàng tháng (VNĐ)
    monthly_bill_vnd: Optional[float] = None
    # Tỉnh/thành phố
    location: Optional[str] = None
    # Mục tiêu: "tiết kiệm" | "đầu tư" | "tự cung"
    goal: Optional[str] = None
    # Ngân sách (VNĐ, tùy chọn)
    budget_vnd: Optional[float] = None

    def is_sufficient(self) -> bool:
        """Kiểm tra có đủ thông tin để tính toán không."""
        return (
            self.location is not None
            and (self.roof_area_m2 is not None or self.monthly_bill_vnd is not None)
        )


@dataclass
class SolarReport:
    """Báo cáo tư vấn hệ thống điện mặt trời."""
    query: SolarQuery
    # Công suất đề xuất (kWp)
    recommended_kwp: float = 0.0
    # Số lượng tấm pin
    panel_count: int = 0
    # Sản lượng dự báo năm (kWh)
    annual_yield_kwh: float = 0.0
    # Ước tính chi phí lắp đặt (VNĐ)
    estimated_cost_vnd: float = 0.0
    # Thời gian hoàn vốn (năm)
    payback_years: float = 0.0
    # Lượng CO₂ tiết kiệm (tấn/năm)
    co2_saved_tons_per_year: float = 0.0
    # Ghi chú và khuyến nghị
    notes: list[str] = field(default_factory=list)

    def to_vietnamese(self) -> str:
        """Sinh báo cáo tiếng Việt dạng văn bản."""
        loc = self.query.location or "khu vực của bạn"
        direction = self.query.roof_direction or "tối ưu"
        area = f"{self.query.roof_area_m2:.0f} m²" if self.query.roof_area_m2 else "không xác định"

        lines = [
            "=" * 55,
            "   BÁO CÁO TƯ VẤN HỆ THỐNG ĐIỆN MẶT TRỜI",
            "   NLP-Solar-Vietnam | nlp-labs-vietnam",
            "=" * 55,
            f"📍 Khu vực          : {loc}",
            f"🏠 Diện tích mái    : {area}",
            f"🧭 Hướng lắp đặt   : {direction}",
            "",
            "─── CẤUÌNH ĐỀ XUẤT ─────────────────────────────",
            f"⚡ Công suất hệ thống : {self.recommended_kwp:.1f} kWp",
            f"☀️  Số lượng tấm pin  : {self.panel_count} tấm (400W Mono-PERC)",
            f"🔌 Inverter           : 1 × {self.recommended_kwp:.0f} kW (string inverter)",
            "",
            "─── DỰ BÁO SẢN LƯỢNG & TÀI CHÍNH ──────────────",
            f"📊 Sản lượng năm     : ~{self.annual_yield_kwh:,.0f} kWh/năm",
            f"💰 Chi phí lắp đặt  : ~{self.estimated_cost_vnd / 1e6:.0f} triệu VNĐ",
            f"📈 Thời gian hoàn vốn: ~{self.payback_years:.1f} năm",
            f"🌿 CO₂ tiết kiệm     : ~{self.co2_saved_tons_per_year:.2f} tấn/năm",
            "",
        ]

        if self.notes:
            lines.append("─── LƯU Ý & KHUYẾN NGHỊ ────────────────────────")
            for note in self.notes:
                lines.append(f"  • {note}")
            lines.append("")

        lines += [
            "─── BƯỚC TIẾP THEO ──────────────────────────────",
            "  1. Khảo sát thực tế mái nhà (miễn phí)",
            "  2. Kiểm tra pháp lý hòa lưới tại EVN địa phương",
            "  3. So sánh báo giá ≥ 3 nhà thầu",
            "=" * 55,
            "  Powered by pvlib-python + NLP-Solar-Vietnam",
        ]

        return "\n".join(lines)


class TextToSolarEngine:
    """
    Engine chuyển đổi câu hỏi tiếng Việt thành báo cáo tư vấn điện mặt trời.

    Parameters
    ----------
    use_pvlib : bool
        Dùng pvlib để tính sản lượng thực (yêu cầu internet cho PVGIS).
        Nếu False, dùng ước tính đơn giản.

    Ví dụ
    -----
    >>> engine = TextToSolarEngine()
    >>> report = engine.analyze("Nhà tôi ở TP.HCM, mái tôn hướng Nam 40m², tiền điện 1.5 triệu/tháng")
    >>> print(report.to_vietnamese())
    """

    # Giá điện bình quân EVN 2024 (VNĐ/kWh)
    _EVN_PRICE_VND = 2103.0
    # Giá lắp đặt trung bình (VNĐ/kWp) — thị trường 2024
    _INSTALL_COST_PER_KWP_VND = 15_000_000.0
    # Hệ số phát thải lưới điện VN (kgCO₂/kWh) — theo EVN 2023
    _EMISSION_FACTOR_KG_CO2 = 0.572

    def __init__(self, use_pvlib: bool = True) -> None:
        try:
            from .ner_extractor import SolarNERExtractor
        except ImportError:
            from ner_extractor import SolarNERExtractor  # type: ignore[no-redef]
        self.ner = SolarNERExtractor()
        self.use_pvlib = use_pvlib

    def analyze(self, user_input: str) -> SolarReport:
        """
        Phân tích câu hỏi và trả về báo cáo tư vấn.

        Parameters
        ----------
        user_input : str
            Câu hỏi/yêu cầu bằng tiếng Việt.

        Returns
        -------
        SolarReport
        """
        query = self.ner.extract(user_input)

        # Ước tính công suất từ diện tích hoặc hóa đơn điện
        kwp = self._estimate_capacity(query)
        annual_yield = self._estimate_yield(kwp, query)
        cost = kwp * self._INSTALL_COST_PER_KWP_VND

        # Thời gian hoàn vốn
        annual_saving = (annual_yield * self._EVN_PRICE_VND)
        payback = cost / annual_saving if annual_saving > 0 else 0.0

        co2 = annual_yield * self._EMISSION_FACTOR_KG_CO2 / 1000.0  # tấn

        notes = []
        if query.roof_direction and query.roof_direction.lower() not in {"nam", "đông nam"}:
            notes.append(f"Mái hướng {query.roof_direction} — sản lượng thấp hơn ~10–15% so với hướng Nam.")
        if kwp > 6 and query.location:
            notes.append("Hệ thống trên 6 kWp cần đăng ký với EVN trước khi lắp đặt.")
        notes.append("Sản lượng thực tế có thể dao động ±10% tùy điều kiện lắp đặt và thời tiết.")

        return SolarReport(
            query=query,
            recommended_kwp=round(kwp, 1),
            panel_count=max(1, round(kwp / 0.4)),  # Tấm 400W
            annual_yield_kwh=round(annual_yield, 0),
            estimated_cost_vnd=round(cost, -6),
            payback_years=round(payback, 1),
            co2_saved_tons_per_year=round(co2, 2),
            notes=notes,
        )

    def _estimate_capacity(self, query: SolarQuery) -> float:
        """Ước tính công suất kWp từ diện tích hoặc hóa đơn điện."""
        if query.roof_area_m2:
            # ~8 m² mái/kWp (thực tế VN, tính cả khoảng cách hàng pin)
            return max(1.0, query.roof_area_m2 / 8.0)
        if query.monthly_bill_vnd:
            # Tính kWh tiêu thụ/tháng → kWp cần thiết
            monthly_kwh = query.monthly_bill_vnd / self._EVN_PRICE_VND
            # Hệ thống đáp ứng ~80% nhu cầu, sản lượng ~120 kWh/kWp/tháng tại VN
            return max(1.0, (monthly_kwh * 0.8) / 120.0)
        return 5.0  # Mặc định 5 kWp

    def _estimate_yield(self, kwp: float, query: SolarQuery) -> float:
        """Ước tính sản lượng năm (kWh)."""
        if self.use_pvlib and query.location:
            try:
                from solar_physics_vn.climate_zones import get_climate_zone
                zone = get_climate_zone(query.location)
                if zone:
                    # Sản lượng đơn giản: GHI × Hiệu suất × 365
                    pr = 0.78  # Performance Ratio trung bình VN
                    return kwp * zone.ghi_annual_avg * 365 * pr
            except Exception:  # noqa: BLE001
                pass

        # Fallback: 1,400 kWh/kWp/năm (trung bình toàn quốc)
        return kwp * 1400.0
