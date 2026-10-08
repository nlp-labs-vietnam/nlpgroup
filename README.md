# ☀️ NLP-Solar-Vietnam

> **Từ định luật vật lý của Becquerel đến mái nhà Việt Nam** — Kết hợp thuật toán vật lý năng lượng mặt trời (pvlib) với sức mạnh Xử lý Ngôn ngữ Tự nhiên (NLP) để tạo ra hệ sinh thái điện mặt trời thông minh, dành riêng cho Việt Nam.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![pvlib](https://img.shields.io/badge/powered%20by-pvlib--python-orange.svg)](https://pvlib-python.readthedocs.io/)
[![LF Energy](https://img.shields.io/badge/inspired%20by-LF%20Energy-green.svg)](https://lfenergy.org/)

---

## 🌍 Bối cảnh & Di sản

Các "cha đẻ" của ngành năng lượng mặt trời — **Alexandre-Edmond Becquerel** (khám phá hiệu ứng quang điện, 1839), **Charles Fritts** (tế bào quang điện đầu tiên, 1883) và **Russell Ohl** (junction p-n silicon, 1940) — đã để lại di sản là các **định luật vật lý bất biến**. Thế kỷ 21 "phần mềm hóa" những định luật đó thành:

| Tầng di sản | Ví dụ |
|---|---|
| **Vật lý cốt lõi** (thế kỷ 19–20) | Hiệu ứng quang điện, junction p-n, bức xạ nhiệt |
| **Thư viện mã nguồn mở** (hiện đại) | `pvlib-python` (Sandia NL), LF Energy (Shapeshifter, CoMPAS) |
| **Ứng dụng AI/NLP** ← *dự án này* | RAG pháp lý, tư vấn viên tiếng Việt, điều phối micro-grid |

**NLP-Solar-Vietnam** là cầu nối từ tầng thứ hai lên tầng thứ ba, bản địa hóa hoàn toàn cho khí hậu, pháp lý và ngôn ngữ Việt Nam.

---

## 🗂️ Cấu trúc Repository

```text
nlpgroup/
├── solar-physics-vn/        # Module vật lý — fork & bản địa hóa pvlib cho VN
├── evn-rag-knowledgebase/   # Cơ sở dữ liệu vector: Quy hoạch Điện VIII, TCVN, DPPA
├── smart-grid-agents/       # Tác tử AI điều phối micro-grid (dựa trên LF Energy)
├── open-solar-designs/      # Bản vẽ & cấu hình phần cứng tối ưu cho VN
├── nlp-chatbot-interface/   # Giao diện chatbot tiếng Việt (Text-to-Solar)
├── data/                    # Dữ liệu bức xạ, thời tiết, TMY các tỉnh VN
├── notebooks/               # Jupyter notebooks minh họa & thử nghiệm
├── tests/                   # Kiểm thử tự động
└── docs/                    # Tài liệu kỹ thuật tiếng Việt
```

---

## 🔬 Module 1 — `solar-physics-vn`: Vật lý Bản địa hóa

**Nguồn gốc:** Fork từ [`pvlib-python`](https://github.com/pvlib/pvlib-python) (Sandia National Laboratories, Mỹ).

**Bài toán:** Thuật toán của Sandia rất mạnh nhưng được hiệu chỉnh cho khí hậu Bắc Mỹ và Châu Âu. Việt Nam có đặc thù riêng:
- Bức xạ nhiệt cao, ổn định (5.0–6.0 kWh/m²/ngày tại Nam Trung Bộ và Tây Nguyên)
- Mùa mưa kéo dài, độ ẩm cao làm giảm hiệu suất module
- Góc nghiêng tối ưu khác với vĩ độ cao (φ ≈ 10°–23° Bắc)

**Tính năng:**
- Pipeline tự động tải dữ liệu khí hậu từ NASA POWER / PVGIS cho tất cả tỉnh VN
- Mô hình hiệu chỉnh tổn thất do nhiệt độ cao và độ ẩm
- Tính toán góc nghiêng & hướng panel tối ưu theo từng vùng địa lý
- Tích hợp ML để hiệu chỉnh sai số theo dự báo thời tiết tiếng Việt

```python
from solar_physics_vn import VietnamSolarSystem

system = VietnamSolarSystem(
    latitude=13.75,   # Gia Lai
    longitude=108.24,
    tilt=13.0,        # Góc tối ưu cho vĩ độ này
    azimuth=180       # Hướng Nam
)
result = system.simulate_annual_yield(capacity_kwp=10.0)
print(result.summary())  # Sản lượng dự báo, LCOE, thời gian hoàn vốn
```

---

## 📚 Module 2 — `evn-rag-knowledgebase`: RAG Pháp lý & Quy hoạch

**Bài toán:** Rào cản lớn nhất của điện mặt trời VN không phải kỹ thuật — mà là **thủ tục pháp lý**: hòa lưới, DPPA, quy định EVN, Quy hoạch Điện VIII, TCVN.

**Kiến trúc RAG:**
```
[Văn bản pháp lý PDF] → [Chunking + Embedding] → [Vector DB (Chroma/FAISS)]
                                                          ↑
[Câu hỏi tiếng Việt] → [NLP: Phân tích ý định] → [Retrieval] → [LLM: Sinh câu trả lời]
```

**Nguồn dữ liệu được tích hợp:**
- Quy hoạch Điện VIII (Quyết định 500/QĐ-TTg)
- Nghị định, Thông tư về phát triển điện mặt trời (2023–2025)
- Tiêu chuẩn TCVN về hệ thống PV nối lưới
- Cơ chế mua bán điện trực tiếp DPPA
- Tài liệu kỹ thuật từ Open Source Solar Project

**Ví dụ truy vấn:**
> *"Quy định mới nhất về lắp đặt điện mặt trời mái nhà xưởng tự sản tự tiêu công suất 500 kWp tại Bình Dương là gì?"*

Hệ thống trích xuất điều khoản pháp lý liên quan + bản vẽ kỹ thuật tương ứng.

---

## 🤖 Module 3 — `nlp-chatbot-interface`: Tư vấn viên AI (Text-to-Solar)

**Đây là nơi NLP tỏa sáng nhất:** Biến kỹ thuật phức tạp thành ngôn ngữ đời thường.

**Luồng xử lý `Text-to-Solar`:**

```
Người dùng nhập (tiếng Việt)
        ↓
[NER: Trích xuất thực thể]
  • Hướng mái: "Nam"
  • Diện tích: 40 m²
  • Hóa đơn điện: 1.5 triệu/tháng
  • Khu vực: "TP. Hồ Chí Minh"
        ↓
[Gọi API → solar-physics-vn (pvlib core)]
  • Tính công suất phù hợp
  • Mô phỏng sản lượng năm
  • Tối ưu cấu hình Inverter + Panel
        ↓
[NLG: Sinh báo cáo tiếng Việt]
  • Cấu hình đề xuất (số lượng, model)
  • Dự toán chi phí & hoàn vốn
  • Trích dẫn pháp lý liên quan (từ RAG)
```

**Ví dụ:**
> *"Nhà tôi mái tôn hướng Nam, 40m², tháng trả 1.5 triệu tiền điện, tư vấn hệ thống phù hợp."*

→ AI trả về báo cáo đầy đủ: hệ thống 5 kWp, 12 tấm Mono-PERC, 1 Inverter 5kW, sản lượng ~7,200 kWh/năm, hoàn vốn ~4.5 năm.

---

## ⚡ Module 4 — `smart-grid-agents`: Điều phối Micro-grid AI

**Nguồn gốc:** Dựa trên kiến trúc của [LF Energy](https://lfenergy.org/) — đặc biệt là **Shapeshifter** (giao thức linh hoạt nhu cầu) và **CoMPAS** (phân tích bảo vệ lưới điện).

**Mục tiêu:** Xây dựng các Agent AI tự động điều phối:
- 🔋 Khi nào **lưu điện vào pin** (giá thấp, sản lượng cao)
- 🔌 Khi nào **đẩy lên lưới EVN** (giá cao, sản lượng vượt tải)
- 🚗 Khi nào **sạc xe điện** từ mặt trời (kết nối EVerest OCPP)
- 🏭 Tối ưu hóa tải công nghiệp theo thời gian biểu TOU (Time-of-Use)

**Kiến trúc Agent:**
```python
class SolarGridAgent:
    """Tác tử AI điều phối năng lượng micro-grid."""
    
    def decide(self, state: GridState) -> Action:
        # Đọc: sản lượng PV, giá điện thời gian thực, trạng thái pin
        # Suy luận: tối ưu hóa theo mục tiêu (tiết kiệm / phát thải / độ tin cậy)
        # Hành động: gửi lệnh đến EMS/inverter qua MQTT/Modbus
        ...
```

---

## 🗺️ Lộ trình Phát triển

| Giai đoạn | Thời gian | Mục tiêu |
|---|---|---|
| **Phase 1** | Tháng 1–3 | Fork pvlib, pipeline dữ liệu bức xạ VN, NER cơ bản |
| **Phase 2** | Tháng 4–6 | RAG pháp lý (Quy hoạch Điện VIII), chatbot MVP |
| **Phase 3** | Tháng 7–9 | Text-to-Solar hoàn chỉnh, API công khai |
| **Phase 4** | Tháng 10–12 | Smart Grid Agents, tích hợp EVerest/EMS |

---

## 🚀 Bắt đầu nhanh

```bash
# Clone repository
git clone https://github.com/nlp-labs-vietnam/nlpgroup.git
cd nlpgroup

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy demo tính toán sản lượng cho Gia Lai
python notebooks/demo_solar_gia_lai.py

# Khởi động chatbot tư vấn (sau khi cấu hình LLM API key)
python nlp-chatbot-interface/app.py
```

---

## 🤝 Đóng góp

Dự án này chào đón sự đóng góp từ:
- **Kỹ sư điện mặt trời** Việt Nam (dữ liệu thực tế, phản hồi mô hình)
- **Nhà nghiên cứu NLP** (cải thiện mô hình ngôn ngữ tiếng Việt)
- **Pháp lý & Chính sách** (cập nhật quy định mới)
- **Cộng đồng mã nguồn mở** (code, test, tài liệu)

Xem hướng dẫn tại [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## 📖 Tài liệu Tham khảo & Nguồn mở

- [pvlib-python](https://github.com/pvlib/pvlib-python) — Sandia National Laboratories
- [LF Energy Projects](https://lfenergy.org/projects/) — Shapeshifter, CoMPAS, EVerest
- [Open Source Solar Project](https://www.opensourcesolar.org/)
- [NASA POWER API](https://power.larc.nasa.gov/) — Dữ liệu bức xạ toàn cầu
- [PVGIS](https://joint-research-centre.ec.europa.eu/pvgis-photovoltaic-geographical-information-system_en) — EU JRC
- Quy hoạch Điện VIII — Quyết định 500/QĐ-TTg (2023)

---

## 📜 Giấy phép

Dự án này được phát hành theo giấy phép [MIT](LICENSE).

> *"Becquerel khám phá ra ánh sáng có thể tạo ra điện. Chúng tôi dạy AI hiểu cách đưa điện đó đến từng mái nhà Việt Nam."*
