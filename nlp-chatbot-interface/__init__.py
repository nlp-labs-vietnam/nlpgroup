"""
nlp-chatbot-interface
=====================
Giao diện chatbot tư vấn điện mặt trời bằng tiếng Việt (Text-to-Solar).

Chạy: python app.py
"""

from .text_to_solar import TextToSolarEngine, SolarQuery, SolarReport
from .ner_extractor import SolarNERExtractor

__version__ = "0.1.0"
__all__ = ["TextToSolarEngine", "SolarQuery", "SolarReport", "SolarNERExtractor"]
