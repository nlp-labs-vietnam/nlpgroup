"""
Tests — NLP-Solar-Vietnam
Kiểm thử cơ bản cho các module cốt lõi.

Chạy: pytest tests/ -v
"""

import sys
import os
import pytest

# Đảm bảo import được các module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solar-physics-vn"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "nlp-chatbot-interface"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "smart-grid-agents"))


# ---------------------------------------------------------------------------
# Tests: climate_zones
# ---------------------------------------------------------------------------

class TestClimateZones:
    def test_all_zones_loaded(self):
        from climate_zones import VIETNAM_CLIMATE_ZONES
        assert len(VIETNAM_CLIMATE_ZONES) >= 5

    def test_get_climate_zone_gia_lai(self):
        from climate_zones import get_climate_zone
        zone = get_climate_zone("Gia Lai")
        assert zone is not None
        assert zone.code == "central_highlands"

    def test_get_climate_zone_hcm(self):
        from climate_zones import get_climate_zone
        zone = get_climate_zone("Hồ Chí Minh")
        assert zone is not None
        assert zone.code == "south"

    def test_get_climate_zone_unknown(self):
        from climate_zones import get_climate_zone
        zone = get_climate_zone("Không Tồn Tại XYZ")
        assert zone is None

    def test_ghi_values_realistic(self):
        """Bức xạ VN phải nằm trong khoảng 3.5–6.5 kWh/m²/ngày."""
        from climate_zones import VIETNAM_CLIMATE_ZONES
        for zone in VIETNAM_CLIMATE_ZONES.values():
            assert 3.0 <= zone.ghi_annual_avg <= 7.0, f"GHI bất hợp lệ: {zone}"


# ---------------------------------------------------------------------------
# Tests: NER Extractor
# ---------------------------------------------------------------------------

class TestSolarNERExtractor:
    @pytest.fixture
    def ner(self):
        from ner_extractor import SolarNERExtractor
        return SolarNERExtractor()

    def test_extract_direction_south(self, ner):
        q = ner.extract("Mái nhà hướng Nam, diện tích 40m²")
        assert q.roof_direction == "Nam"

    def test_extract_direction_southeast(self, ner):
        q = ner.extract("Panel lắp mái hướng đông nam")
        assert q.roof_direction == "Đông Nam"

    def test_extract_area(self, ner):
        q = ner.extract("Diện tích mái 50 m², ở Gia Lai")
        assert q.roof_area_m2 == 50.0

    def test_extract_area_m2_notation(self, ner):
        q = ner.extract("Mái 30m2 hướng Nam")
        assert q.roof_area_m2 == 30.0

    def test_extract_bill_million(self, ner):
        q = ner.extract("tiền điện 1.5 triệu/tháng")
        assert q.monthly_bill_vnd == pytest.approx(1_500_000.0)

    def test_extract_bill_thousand(self, ner):
        q = ner.extract("hóa đơn điện 800 nghìn mỗi tháng")
        assert q.monthly_bill_vnd == pytest.approx(800_000.0)

    def test_extract_location_gia_lai(self, ner):
        q = ner.extract("Nhà tôi ở Gia Lai, mái hướng Nam")
        assert q.location == "Gia Lai"

    def test_extract_location_hcm(self, ner):
        q = ner.extract("Căn hộ TP. Hồ Chí Minh, quận 7")
        assert "Hồ Chí Minh" in (q.location or "")

    def test_extract_goal_saving(self, ner):
        q = ner.extract("Muốn tiết kiệm tiền điện hàng tháng")
        assert q.goal == "tiết kiệm"

    def test_is_sufficient_with_area_and_location(self, ner):
        q = ner.extract("Nhà ở Gia Lai, mái 50m²")
        assert q.is_sufficient() is True

    def test_is_sufficient_missing_location(self, ner):
        q = ner.extract("Mái nhà 40m² hướng Nam")
        assert q.is_sufficient() is False


# ---------------------------------------------------------------------------
# Tests: Text-to-Solar Engine
# ---------------------------------------------------------------------------

class TestTextToSolarEngine:
    @pytest.fixture
    def engine(self):
        from text_to_solar import TextToSolarEngine
        return TextToSolarEngine(use_pvlib=False)  # offline mode

    def test_analyze_basic(self, engine):
        report = engine.analyze("Nhà ở Gia Lai, mái 50m², hướng Nam")
        assert report.recommended_kwp > 0
        assert report.annual_yield_kwh > 0
        assert report.payback_years > 0

    def test_capacity_from_area(self, engine):
        report = engine.analyze("Nhà ở TP.HCM, mái 80m²")
        # 80m² / 8 = 10 kWp
        assert report.recommended_kwp == pytest.approx(10.0, abs=0.5)

    def test_capacity_from_bill(self, engine):
        report = engine.analyze("Nhà ở Hà Nội, tiền điện 2 triệu/tháng")
        # 2M / 2103 VNĐ/kWh ≈ 951 kWh/tháng → 0.8*951/120 ≈ 6.3 kWp
        assert 4.0 <= report.recommended_kwp <= 9.0

    def test_report_has_vietnamese_text(self, engine):
        report = engine.analyze("Nhà ở Gia Lai, mái 50m², hướng Nam")
        text = report.to_vietnamese()
        assert "Gia Lai" in text or "kWp" in text
        assert "kWh" in text

    def test_co2_savings_positive(self, engine):
        report = engine.analyze("Nhà ở Gia Lai, mái 50m²")
        assert report.co2_saved_tons_per_year > 0


# ---------------------------------------------------------------------------
# Tests: SolarGridAgent
# ---------------------------------------------------------------------------

class TestSolarGridAgent:
    @pytest.fixture
    def agent(self):
        from solar_grid_agent import SolarGridAgent
        return SolarGridAgent(strategy="cost")

    @pytest.fixture
    def state_surplus(self):
        from solar_grid_agent import GridState
        return GridState(pv_power_kw=8.0, load_power_kw=2.0, battery_soc=0.3, hour=12)

    @pytest.fixture
    def state_deficit_peak(self):
        from solar_grid_agent import GridState
        return GridState(pv_power_kw=1.0, load_power_kw=3.0, battery_soc=0.6, hour=18)

    def test_surplus_stores_battery_when_low_soc(self, agent, state_surplus):
        from solar_grid_agent import Action
        action = agent.decide(state_surplus)
        assert action == Action.STORE_BATTERY

    def test_surplus_with_ev_charges_ev(self, agent):
        from solar_grid_agent import GridState, Action
        state = GridState(pv_power_kw=8.0, load_power_kw=2.0, battery_soc=0.5,
                         ev_connected=True, ev_soc=0.4)
        assert agent.decide(state) == Action.CHARGE_EV

    def test_deficit_peak_uses_battery(self, agent, state_deficit_peak):
        from solar_grid_agent import Action
        action = agent.decide(state_deficit_peak)
        assert action == Action.SELF_CONSUME

    def test_invalid_strategy_raises(self):
        from solar_grid_agent import SolarGridAgent
        with pytest.raises(ValueError, match="Chiến lược không hợp lệ"):
            SolarGridAgent(strategy="invalid")

    def test_explain_returns_vietnamese(self, agent, state_surplus):
        explanation = agent.explain(state_surplus)
        assert len(explanation) > 10
        assert "[" in explanation  # Chứa tên action

    def test_emission_strategy(self):
        from solar_grid_agent import SolarGridAgent, GridState, Action
        agent = SolarGridAgent(strategy="emission")
        state = GridState(pv_power_kw=8.0, load_power_kw=2.0, battery_soc=0.96)
        # Battery đầy → self_consume thay vì export
        action = agent.decide(state)
        assert action == Action.SELF_CONSUME
