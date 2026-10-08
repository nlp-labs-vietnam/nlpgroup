"""
solar-physics-vn
================
Bản địa hóa pvlib-python cho khí hậu và địa lý Việt Nam.

Nguồn gốc: Fork từ pvlib-python (Sandia National Laboratories)
Mục tiêu: Hiệu chỉnh thuật toán cho bức xạ, độ ẩm và nhiệt độ đặc thù VN.
"""

from .vietnam_solar import VietnamSolarSystem
from .climate_zones import VIETNAM_CLIMATE_ZONES, get_climate_zone
from .data_pipeline import NASAPowerClient, PVGISClient

__version__ = "0.1.0"
__all__ = [
    "VietnamSolarSystem",
    "VIETNAM_CLIMATE_ZONES",
    "get_climate_zone",
    "NASAPowerClient",
    "PVGISClient",
]
