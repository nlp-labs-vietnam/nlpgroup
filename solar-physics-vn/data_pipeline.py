"""
Data Pipeline — Tải dữ liệu bức xạ và thời tiết cho Việt Nam.

Hỗ trợ:
- NASA POWER API  (https://power.larc.nasa.gov/)
- PVGIS           (https://re.jrc.ec.europa.eu/pvg_tools/)
"""

from __future__ import annotations
import os
import json
import urllib.request
from pathlib import Path
from typing import Optional
import pandas as pd

_CACHE_DIR = Path(__file__).parent.parent / "data" / "radiation"


class NASAPowerClient:
    """
    Truy xuất dữ liệu bức xạ và khí hậu từ NASA POWER API.

    Ví dụ
    -----
    >>> client = NASAPowerClient()
    >>> df = client.fetch_hourly(latitude=13.75, longitude=108.24, year=2023)
    """

    _BASE_URL = (
        "https://power.larc.nasa.gov/api/temporal/hourly/point"
        "?parameters={params}&community=RE&longitude={lon}&latitude={lat}"
        "&start={start}&end={end}&format=JSON"
    )
    _DEFAULT_PARAMS = "ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DNI,ALLSKY_SFC_SW_DIFF,T2M,WS10M"

    def __init__(self, cache: bool = True) -> None:
        self.cache = cache
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def fetch_hourly(
        self,
        latitude: float,
        longitude: float,
        year: int,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """
        Tải dữ liệu theo giờ cho một năm cụ thể.

        Returns
        -------
        pd.DataFrame
            Cột: ghi, dni, dhi, temp_air, wind_speed.  Index: DatetimeIndex (UTC+7).
        """
        cache_file = _CACHE_DIR / f"nasa_power_{latitude:.3f}_{longitude:.3f}_{year}.parquet"

        if self.cache and cache_file.exists() and not force_refresh:
            return pd.read_parquet(cache_file)

        url = self._BASE_URL.format(
            params=self._DEFAULT_PARAMS,
            lat=latitude,
            lon=longitude,
            start=f"{year}0101",
            end=f"{year}1231",
        )

        with urllib.request.urlopen(url, timeout=30) as resp:
            payload = json.loads(resp.read())

        properties = payload["properties"]["parameter"]
        timestamps = pd.date_range(
            start=f"{year}-01-01",
            periods=8760,
            freq="1h",
            tz="Asia/Ho_Chi_Minh",
        )

        df = pd.DataFrame(
            {
                "ghi": list(properties["ALLSKY_SFC_SW_DWN"].values()),
                "dni": list(properties["ALLSKY_SFC_SW_DNI"].values()),
                "dhi": list(properties["ALLSKY_SFC_SW_DIFF"].values()),
                "temp_air": list(properties["T2M"].values()),
                "wind_speed": list(properties["WS10M"].values()),
            },
            index=timestamps[:len(list(properties["ALLSKY_SFC_SW_DWN"].values()))],
        )

        # Thay thế giá trị fill (-999) bằng NaN
        df = df.replace(-999.0, float("nan"))

        if self.cache:
            df.to_parquet(cache_file)

        return df


class PVGISClient:
    """
    Truy xuất dữ liệu TMY (Typical Meteorological Year) từ PVGIS EU JRC.

    Ví dụ
    -----
    >>> client = PVGISClient()
    >>> df = client.fetch_tmy(latitude=10.82, longitude=106.63)
    """

    def fetch_tmy(
        self,
        latitude: float,
        longitude: float,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """
        Tải TMY từ PVGIS và trả về DataFrame tương thích pvlib.

        Returns
        -------
        pd.DataFrame
            Cột: ghi, dni, dhi, temp_air, wind_speed.
        """
        import pvlib

        cache_file = _CACHE_DIR / f"pvgis_tmy_{latitude:.3f}_{longitude:.3f}.parquet"

        if not force_refresh and cache_file.exists():
            return pd.read_parquet(cache_file)

        weather, _, _, _ = pvlib.iotools.get_pvgis_tmy(
            latitude=latitude,
            longitude=longitude,
            outputformat="json",
            usehorizon=True,
        )

        if cache_file:
            weather.to_parquet(cache_file)

        return weather
