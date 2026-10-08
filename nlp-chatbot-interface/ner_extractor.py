"""
Solar NER Extractor — Trích xuất thực thể từ câu hỏi tiếng Việt.

Trích xuất: hướng mái, diện tích, hóa đơn điện, địa điểm, mục tiêu.
Phương pháp: Rule-based + Regex (Phase 1), nâng cấp lên PhoBERT NER (Phase 2).
"""

from __future__ import annotations
import re
try:
    from .text_to_solar import SolarQuery
except ImportError:
    from text_to_solar import SolarQuery  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Từ điển & Regex cho Tiếng Việt
# ---------------------------------------------------------------------------

# Hướng mái
_DIRECTION_MAP = {
    r"\bnam\b": "Nam",
    r"\bbắc\b": "Bắc",
    r"\bđông[\s\-]?nam\b": "Đông Nam",
    r"\bđông[\s\-]?bắc\b": "Đông Bắc",
    r"\btây[\s\-]?nam\b": "Tây Nam",
    r"\btây[\s\-]?bắc\b": "Tây Bắc",
    r"\bđông\b": "Đông",
    r"\btây\b": "Tây",
}

# Số tiền (hỗ trợ: 1.5 triệu, 1,5tr, 1500000, 800k, ...)
_MONEY_PATTERNS = [
    (r"(\d+(?:[.,]\d+)?)\s*(?:triệu|tr\b)", 1_000_000),
    (r"(\d+(?:[.,]\d+)?)\s*(?:nghìn|ngàn|k\b)", 1_000),
    (r"(\d{4,})", 1),
]

# Diện tích
_AREA_PATTERNS = [
    r"(\d+(?:[.,]\d+)?)\s*m(?:²|2|\^2)",
    r"(\d+(?:[.,]\d+)?)\s*mét\s*(?:vuông|2)",
]

# Tỉnh thành
_PROVINCES = [
    "Hà Nội", "TP. Hồ Chí Minh", "TP Hồ Chí Minh", "Hồ Chí Minh",
    "Đà Nẵng", "Cần Thơ", "Hải Phòng",
    "Bình Dương", "Đồng Nai", "Bà Rịa", "Vũng Tàu",
    "Gia Lai", "Đắk Lắk", "Đắk Nông", "Kon Tum", "Lâm Đồng",
    "Khánh Hòa", "Ninh Thuận", "Bình Thuận",
    "Quảng Nam", "Quảng Ngãi", "Bình Định", "Phú Yên",
    "Nghệ An", "Hà Tĩnh", "Thừa Thiên Huế",
    "Long An", "Tiền Giang", "Kiên Giang", "An Giang",
    "Sơn La", "Điện Biên", "Lai Châu", "Lào Cai",
]

# Mục tiêu
_GOAL_KEYWORDS = {
    "tiết kiệm": r"\btiết\s*kiệm\b",
    "đầu tư": r"\bđầu\s*tư\b",
    "tự cung": r"\btự\s*(?:cung|dùng|sản|tiêu)\b",
}


class SolarNERExtractor:
    """
    Trích xuất thực thể từ câu hỏi tư vấn điện mặt trời tiếng Việt.

    Ví dụ
    -----
    >>> ner = SolarNERExtractor()
    >>> q = ner.extract("Nhà tôi ở Gia Lai, mái hướng Nam 50m², tiền điện 2 triệu/tháng")
    >>> print(q.location, q.roof_direction, q.roof_area_m2, q.monthly_bill_vnd)
    Gia Lai Nam 50.0 2000000.0
    """

    def extract(self, text: str) -> SolarQuery:
        """
        Phân tích câu hỏi và trích xuất các thực thể.

        Parameters
        ----------
        text : str
            Câu hỏi tiếng Việt tự do.

        Returns
        -------
        SolarQuery
        """
        text_lower = text.lower()

        return SolarQuery(
            raw_text=text,
            roof_direction=self._extract_direction(text_lower),
            roof_area_m2=self._extract_area(text_lower),
            monthly_bill_vnd=self._extract_money_bill(text_lower),
            location=self._extract_location(text),
            goal=self._extract_goal(text_lower),
            budget_vnd=self._extract_budget(text_lower),
        )

    # ------------------------------------------------------------------
    # Entity extractors
    # ------------------------------------------------------------------

    def _extract_direction(self, text: str) -> str | None:
        # Kiểm tra compound directions (đông nam, tây bắc, ...) trước khi kiểm tra đơn
        compound_patterns = {k: v for k, v in _DIRECTION_MAP.items() if len(v) > 3}
        simple_patterns = {k: v for k, v in _DIRECTION_MAP.items() if len(v) <= 3}
        for pattern, label in {**compound_patterns, **simple_patterns}.items():
            if re.search(pattern, text, re.IGNORECASE | re.UNICODE):
                return label
        return None

    def _extract_area(self, text: str) -> float | None:
        for pattern in _AREA_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
            if m:
                return float(m.group(1).replace(",", "."))
        return None

    def _extract_money_bill(self, text: str) -> float | None:
        """Trích xuất hóa đơn điện hàng tháng."""
        context_re = re.compile(
            r"(?:tiền\s*điện|hóa\s*đơn|trả|tháng\s*trả|xài|dùng|tốn)\s*[:\-]?\s*"
            r"(\d+(?:[.,]\d+)?)\s*(triệu|tỷ|tr|nghìn|ngàn|k)?",
            re.IGNORECASE | re.UNICODE,
        )
        # Thử với "hóa đơn điện X đơn vị"
        m = context_re.search(text)
        if m:
            return self._parse_amount(m.group(1), m.group(2))
        # Fallback: "X nghìn/triệu mỗi/một tháng" (đơn vị trước mỗi tháng)
        fallback_re = re.compile(
            r"(\d+(?:[.,]\d+)?)\s*(triệu|tỷ|tr|nghìn|ngàn|k)\s*(?:mỗi|một|\/|mỗi\s*tháng|\/tháng)",
            re.IGNORECASE | re.UNICODE,
        )
        m2 = fallback_re.search(text)
        if m2:
            return self._parse_amount(m2.group(1), m2.group(2))
        return None

    def _extract_budget(self, text: str) -> float | None:
        budget_re = re.compile(
            r"(?:ngân\s*sách|budget|vốn|chi\s*phí|đầu\s*tư)\s*[:\-]?\s*"
            r"(\d+(?:[.,]\d+)?)\s*(triệu|tr|tỷ)?",
            re.IGNORECASE | re.UNICODE,
        )
        m = budget_re.search(text)
        if not m:
            return None
        multiplier = {"tỷ": 1_000_000_000, "triệu": 1_000_000, "tr": 1_000_000}.get(
            (m.group(2) or "").lower(), 1
        )
        return float(m.group(1).replace(",", ".")) * multiplier

    def _extract_location(self, text: str) -> str | None:
        text_lower = text.lower()
        for province in sorted(_PROVINCES, key=len, reverse=True):  # Dài trước
            if province.lower() in text_lower:
                return province
        return None

    def _extract_goal(self, text: str) -> str | None:
        for goal, pattern in _GOAL_KEYWORDS.items():
            if re.search(pattern, text, re.IGNORECASE | re.UNICODE):
                return goal
        return None

    @staticmethod
    def _parse_amount(number_str: str, unit: str | None) -> float:
        value = float(number_str.replace(",", "."))
        unit = (unit or "").lower()
        if unit in {"triệu", "tr"}:
            return value * 1_000_000
        if unit in {"nghìn", "ngàn", "k"}:
            return value * 1_000
        return value
