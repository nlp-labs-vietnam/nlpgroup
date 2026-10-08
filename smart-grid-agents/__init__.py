"""
smart-grid-agents
=================
Tác tử AI điều phối micro-grid năng lượng mặt trời cho Việt Nam.
Dựa trên kiến trúc LF Energy (Shapeshifter, CoMPAS).
"""

from .solar_grid_agent import SolarGridAgent, GridState, Action
from .energy_manager import EnergyManagementSystem

__version__ = "0.1.0"
__all__ = ["SolarGridAgent", "GridState", "Action", "EnergyManagementSystem"]
