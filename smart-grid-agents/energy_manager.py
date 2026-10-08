"""
Energy Management System (EMS) — Điều phối tổng thể micro-grid.
Giao tiếp với inverter/pin/EV qua MQTT và Modbus TCP.
"""

from __future__ import annotations
import time
import logging
from typing import Callable, Optional

from .solar_grid_agent import SolarGridAgent, GridState, Action

logger = logging.getLogger(__name__)


class EnergyManagementSystem:
    """
    Hệ thống quản lý năng lượng (EMS) tự động.

    Chạy vòng lặp điều khiển theo chu kỳ, đọc trạng thái từ inverter
    và gửi lệnh điều phối.

    Parameters
    ----------
    agent : SolarGridAgent
        Tác tử AI ra quyết định.
    interval_seconds : int
        Chu kỳ điều khiển (giây).  Mặc định: 60s.
    state_reader : Callable, optional
        Hàm đọc trạng thái thực tế từ inverter/MQTT.
        Nếu None, dùng dữ liệu mô phỏng.

    Ví dụ
    -----
    >>> ems = EnergyManagementSystem(SolarGridAgent(strategy="cost"))
    >>> ems.run(max_cycles=10)  # Chạy 10 chu kỳ demo
    """

    def __init__(
        self,
        agent: Optional[SolarGridAgent] = None,
        interval_seconds: int = 60,
        state_reader: Optional[Callable[[], GridState]] = None,
    ) -> None:
        self.agent = agent or SolarGridAgent(strategy="cost")
        self.interval_seconds = interval_seconds
        self.state_reader = state_reader or self._default_state_reader
        self._history: list[dict] = []

    def run(self, max_cycles: Optional[int] = None) -> None:
        """Khởi động vòng lặp điều khiển EMS."""
        cycle = 0
        logger.info("EMS khởi động — chiến lược: %s", self.agent.strategy)

        while max_cycles is None or cycle < max_cycles:
            state = self.state_reader()
            action = self.agent.decide(state)
            explanation = self.agent.explain(state)

            logger.info("[Chu kỳ %d] %s", cycle + 1, explanation)
            self._execute_action(action, state)
            self._history.append({"cycle": cycle, "action": action.name, "state": state})

            cycle += 1
            if max_cycles is None or cycle < max_cycles:
                time.sleep(self.interval_seconds)

    def get_history(self) -> list[dict]:
        """Trả về lịch sử các quyết định đã thực thi."""
        return list(self._history)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _execute_action(self, action: Action, state: GridState) -> None:
        """Gửi lệnh đến phần cứng (MQTT/Modbus)."""
        # TODO: tích hợp MQTT client để gửi lệnh thực tế
        # Hiện tại: log và mô phỏng
        action_map = {
            Action.STORE_BATTERY: "SET inverter mode=charge",
            Action.EXPORT_TO_GRID: "SET inverter mode=export",
            Action.CHARGE_EV: "SET ev_charger mode=solar_only",
            Action.SELF_CONSUME: "SET inverter mode=self_consume",
            Action.IDLE: "SET inverter mode=auto",
        }
        cmd = action_map.get(action, "NOOP")
        logger.debug("→ Lệnh phần cứng: %s", cmd)

    @staticmethod
    def _default_state_reader() -> GridState:
        """Đọc trạng thái mô phỏng (demo)."""
        import random
        import datetime
        hour = datetime.datetime.now().hour
        # Mô phỏng đường cong PV dạng chuông
        pv = max(0.0, 8.0 * (1 - ((hour - 12) / 6) ** 2)) + random.gauss(0, 0.3)
        load = 2.0 + random.gauss(0, 0.2)
        return GridState(
            pv_power_kw=round(max(0, pv), 2),
            load_power_kw=round(max(0.5, load), 2),
            battery_soc=round(random.uniform(0.3, 0.8), 2),
            hour=hour,
        )
