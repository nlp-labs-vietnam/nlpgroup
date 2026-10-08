"""
VietnamSolarSystem
==================
Lớp chính mô phỏng hệ thống điện mặt trời tại Việt Nam.
Bọc pvlib với các hiệu chỉnh đặc thù cho khí hậu VN.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import pvlib
import pandas as pd


# ---------------------------------------------------------------------------
# Hằng số hiệu chỉnh cho Việt Nam
# ---------------------------------------------------------------------------

# Hệ số tổn thất nhiệt độ bổ sung (°C trên điểm STC 25°C)
# Tấm pin Mono-PERC thường tầm -0.35%/°C; VN mùa hè ~40°C ngoài trời
_TEMP_LOSS_COEFF_DEFAULT = -0.0035  # %/°C

# Hệ số tổn thất bổ sung do bụi & độ ẩm cao (đặc thù Tây Nguyên, ven biển)
_SOILING_LOSS_VN = 0.02  # 2% trung bình năm

# Hằng số mô hình nhiệt Faiman cho khí hậu nhiệt đới
_FAIMAN_U0 = 25.0
_FAIMAN_U1 = 6.84


@dataclass
class SimulationResult:
    """Kết quả mô phỏng sản lượng điện mặt trời."""

    capacity_kwp: float
    annual_yield_kwh: float
    specific_yield_kwh_per_kwp: float
    performance_ratio: float
    location: str = ""
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"=== Kết quả mô phỏng NLP-Solar-VN ===",
            f"Công suất lắp đặt  : {self.capacity_kwp:.1f} kWp",
            f"Sản lượng năm      : {self.annual_yield_kwh:,.0f} kWh/năm",
            f"Sản lượng riêng    : {self.specific_yield_kwh_per_kwp:,.0f} kWh/kWp/năm",
            f"Hiệu suất hệ thống : {self.performance_ratio:.1%}",
        ]
        if self.location:
            lines.insert(1, f"Khu vực            : {self.location}")
        if self.notes:
            lines.append("\nGhi chú:")
            lines.extend(f"  • {n}" for n in self.notes)
        return "\n".join(lines)


class VietnamSolarSystem:
    """
    Mô phỏng hệ thống PV tại Việt Nam với hiệu chỉnh khí hậu bản địa.

    Parameters
    ----------
    latitude : float
        Vĩ độ (°N).  Ví dụ: 13.75 (Gia Lai), 10.82 (TP.HCM), 16.05 (Đà Nẵng).
    longitude : float
        Kinh độ (°E).
    tilt : float, optional
        Góc nghiêng tấm pin (°).  Mặc định = |latitude| (quy tắc ngón tay cái).
    azimuth : float, optional
        Góc phương vị (°).  180 = hướng Nam (tối ưu ở Bắc bán cầu).
    altitude : float, optional
        Độ cao so với mực nước biển (m).
    name : str, optional
        Tên địa điểm, dùng cho báo cáo.
    soiling_loss : float, optional
        Hệ số tổn thất bụi bẩn/độ ẩm (0–1).  Mặc định = 0.02.
    """

    def __init__(
        self,
        latitude: float,
        longitude: float,
        tilt: Optional[float] = None,
        azimuth: float = 180.0,
        altitude: float = 0.0,
        name: str = "",
        soiling_loss: float = _SOILING_LOSS_VN,
    ) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.tilt = tilt if tilt is not None else abs(latitude)
        self.azimuth = azimuth
        self.altitude = altitude
        self.name = name
        self.soiling_loss = soiling_loss

        self.location = pvlib.location.Location(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            tz="Asia/Ho_Chi_Minh",
            name=name,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def simulate_annual_yield(
        self,
        capacity_kwp: float,
        weather: Optional[pd.DataFrame] = None,
        module_params: Optional[dict] = None,
        inverter_params: Optional[dict] = None,
    ) -> SimulationResult:
        """
        Mô phỏng sản lượng điện năm cho hệ thống có công suất `capacity_kwp`.

        Parameters
        ----------
        capacity_kwp : float
            Công suất đỉnh hệ thống (kWp).
        weather : pd.DataFrame, optional
            Dữ liệu thời tiết theo giờ (GHI, DNI, DHI, temp_air, wind_speed).
            Nếu None, dữ liệu TMY sẽ được tải từ PVGIS.
        module_params : dict, optional
            Tham số mô-đun PV.  Mặc định: tấm Mono-PERC tiêu chuẩn 400W.
        inverter_params : dict, optional
            Tham số inverter.  Mặc định: inverter string 3-phase, η=97%.

        Returns
        -------
        SimulationResult
        """
        if weather is None:
            weather = self._fetch_tmy()

        # Tính toán vị trí mặt trời
        solar_position = self.location.get_solarposition(weather.index)

        # Bức xạ trên mặt phẳng nghiêng (POA)
        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=self.tilt,
            surface_azimuth=self.azimuth,
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"],
            dni=weather["dni"],
            ghi=weather["ghi"],
            dhi=weather["dhi"],
        )

        # Nhiệt độ tấm pin (mô hình Faiman)
        cell_temp = pvlib.temperature.faiman(
            poa_global=poa["poa_global"],
            temp_air=weather.get("temp_air", pd.Series(30.0, index=weather.index)),
            wind_speed=weather.get("wind_speed", pd.Series(1.0, index=weather.index)),
            u0=_FAIMAN_U0,
            u1=_FAIMAN_U1,
        )

        # Hiệu suất hệ thống đơn giản hóa (DC → AC)
        dc_output = poa["poa_global"] * capacity_kwp  # W/m² × kWp (tỷ lệ)
        temp_loss = _TEMP_LOSS_COEFF_DEFAULT * (cell_temp - 25.0)
        dc_corrected = dc_output * (1 + temp_loss) * (1 - self.soiling_loss)

        # Tổn thất inverter + cáp (mặc định 5%)
        ac_output_kwh = (dc_corrected * 0.95).clip(lower=0).sum() / 1000.0

        pr = ac_output_kwh / (capacity_kwp * 8760 * poa["poa_global"].mean() / 1000.0)
        specific = ac_output_kwh / capacity_kwp

        notes = []
        if self.latitude < 12:
            notes.append("Khu vực xích đạo: bức xạ cao nhưng góc nghiêng thấp tối ưu.")
        if cell_temp.mean() > 45:
            notes.append("Nhiệt độ tế bào trung bình cao — cân nhắc tấm pin có hệ số nhiệt tốt hơn.")

        return SimulationResult(
            capacity_kwp=capacity_kwp,
            annual_yield_kwh=round(ac_output_kwh, 1),
            specific_yield_kwh_per_kwp=round(specific, 1),
            performance_ratio=round(pr, 3),
            location=self.name,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_tmy(self) -> pd.DataFrame:
        """Tải dữ liệu TMY từ PVGIS (yêu cầu kết nối internet)."""
        try:
            weather, _, _, _ = pvlib.iotools.get_pvgis_tmy(
                latitude=self.latitude,
                longitude=self.longitude,
                outputformat="json",
                usehorizon=True,
            )
            return weather
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"Không thể tải dữ liệu TMY từ PVGIS cho ({self.latitude}, {self.longitude}). "
                f"Kiểm tra kết nối mạng hoặc cung cấp `weather` thủ công.\n"
                f"Chi tiết: {exc}"
            ) from exc
