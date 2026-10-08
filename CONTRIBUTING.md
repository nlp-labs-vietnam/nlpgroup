# 🤝 Hướng dẫn đóng góp (Contributing Guide)

Chào mừng bạn đến với **NLP-Solar-Vietnam**! Chúng tôi rất vui mừng khi bạn quan tâm và muốn đóng góp vào hệ sinh thái điện mặt trời thông minh dành riêng cho Việt Nam.

Dự án này là nỗ lực của cộng đồng nhằm biến các định luật vật lý phức tạp thành ngôn ngữ dễ hiểu, giúp đưa năng lượng mặt trời đến từng mái nhà Việt Nam. Mọi đóng góp, dù lớn hay nhỏ, đều rất đáng quý.

---

## 🌟 Những vị trí chúng tôi đang tìm kiếm

Dự án phát triển đa ngành, do đó chúng tôi hoan nghênh sự đóng góp từ nhiều lĩnh vực:

| # | Vai trò | Đóng góp cụ thể |
|---|---|---|
| 1 | **Kỹ sư Điện mặt trời & Năng lượng** | Kiểm chứng độ chính xác `solar-physics-vn`, cung cấp dữ liệu bức xạ thực tế, tối ưu góc nghiêng |
| 2 | **Nhà nghiên cứu & Kỹ sư NLP/AI** | Cải thiện NER tiếng Việt, fine-tune mô hình embedding, tối ưu RAG pipeline |
| 3 | **Chuyên gia Pháp lý & Chính sách** | Cập nhật Quy hoạch Điện VIII, DPPA, TCVN vào `evn-rag-knowledgebase` |
| 4 | **Cộng đồng Mã nguồn mở** | Code Python, tài liệu (docs), báo cáo lỗi (issues), viết tests |

---

## 🛠️ Quy trình đóng góp Code & Tài liệu

Chúng tôi sử dụng **GitHub Flow** tiêu chuẩn:

### 1. Fork & Clone

```bash
# Fork repository trên GitHub, sau đó clone về máy
git clone https://github.com/<tên-của-bạn>/nlpgroup.git
cd nlpgroup
```

### 2. Cài đặt môi trường

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### 3. Tạo nhánh mới

Quy ước đặt tên nhánh:

| Loại | Tiền tố | Ví dụ |
|---|---|---|
| Tính năng mới | `feature/` | `feature/add-dak-lak-tmy-data` |
| Sửa lỗi | `fix/` | `fix/ner-direction-southeast` |
| Tài liệu | `docs/` | `docs/update-legal-dppa-2025` |

```bash
git checkout -b feature/ten-tinh-nang-cua-ban
```

### 4. Phát triển & Kiểm thử

```bash
# Chạy toàn bộ test trước khi commit
python -m pytest tests/ -v

# Kiểm tra định dạng code
python -m ruff check .
python -m black --check .
```

> ✅ **Yêu cầu:** Tất cả 27 tests hiện có phải tiếp tục pass. Nếu bạn thêm tính năng mới, hãy bổ sung test tương ứng vào [`tests/test_core.py`](tests/test_core.py).

### 5. Commit với thông điệp rõ ràng

Tuân theo chuẩn [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat(solar-physics): them du lieu TMY cho tinh Dak Lak"
git commit -m "fix(ner): sua regex nhan dien huong Dong Nam"
git commit -m "docs(legal): cap nhat thong tu DPPA 2025"
```

### 6. Push & Tạo Pull Request

```bash
git push origin feature/ten-tinh-nang-cua-ban
```

Mở Pull Request vào nhánh `main`. PR template sẽ yêu cầu:
- Mô tả những gì đã thay đổi
- Test đã chạy (kết quả `pytest`)
- Screenshots / output mẫu (nếu có)

---

## 🐞 Báo cáo lỗi & Đề xuất tính năng (Issues)

Trước khi mở Issue mới, hãy kiểm tra xem vấn đề đã được báo cáo chưa tại [Issues](https://github.com/nlp-labs-vietnam/nlpgroup/issues).

**Khi báo cáo lỗi, hãy cung cấp:**
- Phiên bản Python và hệ điều hành
- Các bước tái hiện lỗi
- Thông báo lỗi đầy đủ (traceback)
- Kết quả mong đợi vs. kết quả thực tế

**Nhãn Issue phổ biến:**
- `bug` — lỗi chức năng
- `enhancement` — đề xuất tính năng mới
- `data` — yêu cầu dữ liệu bức xạ / pháp lý
- `good first issue` — phù hợp cho người mới đóng góp

---

## 💡 Ý tưởng đóng góp nhanh (Good First Issues)

Nếu bạn chưa biết bắt đầu từ đâu, đây là những việc nhỏ có tác động lớn:

- [ ] Bổ sung dữ liệu TMY cho các tỉnh còn thiếu (Hà Giang, Cà Mau, Phú Quốc...)
- [ ] Cải thiện regex NER nhận diện đơn vị tiền tệ dạng `"1tr5"`, `"hai triệu"`
- [ ] Dịch docstring sang tiếng Anh để cộng đồng quốc tế có thể tham gia
- [ ] Thêm test case cho `SolarGridAgent` chiến lược `reliability`
- [ ] Cập nhật giá điện EVN theo bậc thang mới nhất (2024–2025)

---

## 💰 Hỗ trợ tài chính & Gây quỹ

NLP-Solar-Vietnam là dự án **phi lợi nhuận, mã nguồn mở**. Chi phí vận hành bao gồm: server chạy LLM, Vector DB, API dữ liệu thời tiết và nhân lực bảo trì.

### Kênh ủng hộ cá nhân

| Kênh | Link |
|---|---|
| ⭐ **GitHub Sponsors** | [github.com/sponsors/nlp-labs-vietnam](https://github.com/sponsors/nlp-labs-vietnam) |
| ☕ **Buy Me a Coffee** | [buymeacoffee.com/nlp-solar-vn](https://buymeacoffee.com/nlp-solar-vn) *(sắp ra mắt)* |
| 🌐 **Open Collective** | [opencollective.com/nlp-solar-vietnam](https://opencollective.com/nlp-solar-vietnam) *(sắp ra mắt)* |

### Tài trợ doanh nghiệp (Corporate Sponsorship)

Nếu công ty của bạn hoạt động trong lĩnh vực điện mặt trời, AI hoặc năng lượng sạch và muốn đồng hành:

- Cung cấp hạ tầng server / GPU
- Tài trợ kinh phí nghiên cứu
- Cung cấp dữ liệu thực tế (bức xạ, sản lượng vận hành)

📧 Liên hệ: **contact@nlp-labs-vietnam.com**

### Tài trợ từ tổ chức & Quỹ (Grants)

Chúng tôi đang nộp hồ sơ xin tài trợ từ:
- [LF Energy](https://lfenergy.org/) — Linux Foundation Energy
- [Google for Startups — AI for Climate](https://startup.google.com/)
- [Microsoft AI for Earth](https://www.microsoft.com/en-us/ai/ai-for-earth)
- Các quỹ năng lượng tái tạo tại Việt Nam (VNEEC, GreenID)

---

## 📜 Quy tắc ứng xử (Code of Conduct)

Dự án này tuân thủ [Contributor Covenant](https://www.contributor-covenant.org/). Chúng tôi cam kết tạo ra một môi trường mở, thân thiện và tôn trọng cho tất cả mọi người, bất kể kinh nghiệm, giới tính, quốc tịch hay quan điểm.

---

Cảm ơn bạn đã đồng hành cùng chúng tôi trên hành trình phủ xanh năng lượng tại Việt Nam! ☀️🇻🇳

> *"Becquerel khám phá ra ánh sáng có thể tạo ra điện. Chúng tôi dạy AI hiểu cách đưa điện đó đến từng mái nhà Việt Nam."*
