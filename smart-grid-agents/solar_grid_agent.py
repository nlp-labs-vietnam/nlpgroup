"""
SolarGridAgent — Tác tử AI điều phối năng lượng micro-grid.

Chiến lược mặc định: tối ưu hóa tiết kiệm chi phí (cost-minimization).
Giao tiếp với inverter/EMS qua MQTT hoặc Modbus TCP.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import datetime


class Action(Enum):
    """Các hành động điều phối năng lượng."""
    STORE_BATTERY = auto()    # Lưu điện vào pin
    EXPORT_TO_GRID = auto()   # Đẩy điện lên lưới EVN
    CHARGE_EV = auto()        # Sạc xe điện từ mặt trời
    SELF_CONSUME = auto()     # Tự tiêu thụ
    IDLE = auto()             # Chờ đợi


@dataclass
class GridState:
    """
    Trạng thái tức thời của micro-grid.

    Tất cả công suất tính bằng kW, năng lượng tính bằng kWh.
    """
    # Sản lượng PV hiện tại (kW)
    pv_power_kw: float = 0.0
    # Phụ tải tiêu thụ (kW)
    load_power_kw: float = 0.0
    # Trạng thái pin (State of Charge, 0.0–1.0)
    battery_soc: float = 0.5
    # Dung lượng pin (kWh)
    battery_capacity_kwh: float = 10.0
    # Giá điện EVN hiện tại (VNĐ/kWh)
    grid_price_vnd_per_kwh: float = 2000.0
    # Giá FIT/DPPA (VNĐ/kWh bán lên lưới)
    export_price_vnd_per_kwh: float = 1943.0
    # Giờ hiện tại trong ngày (0–23)
    hour: int = field(default_factory=lambda: datetime.datetime.now().hour)
    # Dự báo sản lượng PV 4 giờ tới (kW)
    pv_forecast_4h: list[float] = field(default_factory=list)
    # Trạng thái EV (đang kết nối?)
    ev_connected: bool = False
    # SOC xe điện (0.0–1.0, None nếu không kết nối)
    ev_soc: Optional[float] = None


class SolarGridAgent:
    """
    Tác tử AI điều phối năng lượng micro-grid theo chiến lược tối ưu.

    Parameters
    ----------
    strategy : str
        "cost"      — tối thiểu hóa chi phí điện.
        "emission"  — tối thiểu hóa phát thải CO₂.
        "reliability" — ưu tiên độ tin cậy nguồn điện.

    Ví dụ
    -----
    >>> agent = SolarGridAgent(strategy="cost")
    >>> state = GridState(pv_power_kw=5.0, load_power_kw=2.0, battery_soc=0.3)
    >>> action = agent.decide(state)
    >>> print(action)
    Action.STORE_BATTERY
    """

    # Ngưỡng SOC để bảo vệ pin (không xả dưới 20%, không sạc trên 95%)
    _SOC_MIN = 0.20
    _SOC_MAX = 0.95
    # Giờ cao điểm EVN (TOU pricing)
    _PEAK_HOURS = {9, 10, 11, 17, 18, 19, 20}

    def __init__(self, strategy: str = "cost") -> None:
        if strategy not in {"cost", "emission", "reliability"}:
            raise ValueError(f"Chiến lược không hợp lệ: '{strategy}'. Chọn: cost | emission | reliability")
        self.strategy = strategy

    def decide(self, state: GridState) -> Action:
        """
        Đưa ra quyết định điều phối tốt nhất cho trạng thái hiện tại.

        Parameters
        ----------
        state : GridState
            Trạng thái tức thời của micro-grid.

        Returns
        -------
        Action
            Hành động tốt nhất theo chiến lược đã chọn.
        """
        net_power = state.pv_power_kw - state.load_power_kw  # >0: thặng dư; <0: thiếu hụt

        if self.strategy == "cost":
            return self._decide_cost(state, net_power)
        elif self.strategy == "emission":
            return self._decide_emission(state, net_power)
        else:
            return self._decide_reliability(state, net_power)

    def explain(self, state: GridState) -> str:
        """Giải thích quyết định bằng tiếng Việt."""
        action = self.decide(state)
        net = state.pv_power_kw - state.load_power_kw
        surplus_deficit = f"thặng dư {net:.1f} kW" if net >= 0 else f"thiếu hụt {abs(net):.1f} kW"

        explanations = {
            Action.STORE_BATTERY: f"Lưu điện vào pin (SOC hiện tại: {state.battery_soc:.0%}). {surplus_deficit}.",
            Action.EXPORT_TO_GRID: f"Đẩy điện lên lưới EVN với giá {state.export_price_vnd_per_kwh:,.0f} đ/kWh. {surplus_deficit}.",
            Action.CHARGE_EV: f"Sạc xe điện từ mặt trời (EV SOC: {(state.ev_soc or 0):.0%}). {surplus_deficit}.",
            Action.SELF_CONSUME: f"Tự tiêu thụ điện mặt trời. {surplus_deficit}.",
            Action.IDLE: f"Chờ đợi — không đủ điều kiện cho hành động nào. {surplus_deficit}.",
        }
        return f"[{action.name}] {explanations.get(action, '')}"

    # ------------------------------------------------------------------
    # Strategy implementations
    # ------------------------------------------------------------------

    def _decide_cost(self, state: GridState, net: float) -> Action:
        """Chiến lược tối thiểu hóa chi phí."""
        is_peak = state.hour in self._PEAK_HOURS

        if net > 0:  # Thặng dư điện mặt trời
            # Ưu tiên: sạc EV (nếu kết nối) > lưu pin (nếu chưa đầy) > đẩy lên lưới
            if state.ev_connected and (state.ev_soc or 0) < 0.9:
                return Action.CHARGE_EV
            if state.battery_soc < self._SOC_MAX:
                return Action.STORE_BATTERY
            return Action.EXPORT_TO_GRID

        else:  # Thiếu hụt
            # Trong giờ cao điểm: dùng pin thay vì mua lưới
            if is_peak and state.battery_soc > self._SOC_MIN:
                return Action.SELF_CONSUME
            return Action.IDLE  # Mua điện lưới (inverter tự xử lý)

    def _decide_emission(self, state: GridState, net: float) -> Action:
        """Chiến lược tối thiểu hóa phát thải CO₂."""
        if net > 0:
            if state.ev_connected and (state.ev_soc or 0) < 0.9:
                return Action.CHARGE_EV
            if state.battery_soc < self._SOC_MAX:
                return Action.STORE_BATTERY
            return Action.SELF_CONSUME  # Ưu tiên tự dùng hơn đẩy lưới
        elif state.battery_soc > self._SOC_MIN:
            return Action.SELF_CONSUME
        return Action.IDLE

    def _decide_reliability(self, state: GridState, net: float) -> Action:
        """Chiến lược ưu tiên độ tin cậy — giữ pin ở mức cao."""
        if net > 0 and state.battery_soc < 0.80:
            return Action.STORE_BATTERY
        if net > 0 and state.battery_soc >= 0.80:
            return Action.SELF_CONSUME
        return Action.IDLE
