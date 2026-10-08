"""
NLP-Solar-Vietnam — Chatbot Tư vấn Điện Mặt Trời
=================================================
REST API + CLI entry point.

Chạy API server:
    python app.py

Hoặc dùng uvicorn trực tiếp:
    uvicorn app:app --reload --port 8000

Gọi thử CLI:
    python app.py --query "Nhà tôi ở Gia Lai, mái hướng Nam 50m², tiền điện 2 triệu/tháng"
"""

from __future__ import annotations
import argparse
import sys

# ── FastAPI App ──────────────────────────────────────────────────────────────
try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel

    app = FastAPI(
        title="NLP-Solar-Vietnam API",
        description="Tư vấn hệ thống điện mặt trời bằng tiếng Việt",
        version="0.1.0",
    )

    class QueryRequest(BaseModel):
        text: str
        use_pvlib: bool = True

    class QueryResponse(BaseModel):
        recommended_kwp: float
        panel_count: int
        annual_yield_kwh: float
        estimated_cost_million_vnd: float
        payback_years: float
        co2_saved_tons_per_year: float
        report_text: str
        notes: list[str]

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "service": "NLP-Solar-Vietnam", "version": "0.1.0"}

    @app.post("/analyze", response_model=QueryResponse)
    async def analyze_solar(req: QueryRequest) -> QueryResponse:
        """
        Phân tích câu hỏi tiếng Việt và trả về tư vấn hệ thống điện mặt trời.

        Ví dụ body:
        ```json
        {
          "text": "Nhà tôi ở TP.HCM, mái tôn hướng Nam 40m², tiền điện 1.5 triệu/tháng"
        }
        ```
        """
        from nlp_chatbot_interface.text_to_solar import TextToSolarEngine

        engine = TextToSolarEngine(use_pvlib=req.use_pvlib)
        report = engine.analyze(req.text)

        return QueryResponse(
            recommended_kwp=report.recommended_kwp,
            panel_count=report.panel_count,
            annual_yield_kwh=report.annual_yield_kwh,
            estimated_cost_million_vnd=round(report.estimated_cost_vnd / 1_000_000, 1),
            payback_years=report.payback_years,
            co2_saved_tons_per_year=report.co2_saved_tons_per_year,
            report_text=report.to_vietnamese(),
            notes=report.notes,
        )

    @app.post("/rag/query")
    async def rag_query(body: dict) -> JSONResponse:
        """Truy vấn hệ thống RAG pháp lý điện mặt trời."""
        from evn_rag_knowledgebase.rag_pipeline import SolarLegalRAG

        question = body.get("question", "")
        if not question:
            return JSONResponse({"error": "Thiếu trường 'question'"}, status_code=400)

        rag = SolarLegalRAG()
        try:
            rag.load_vector_store()
        except Exception:
            return JSONResponse(
                {"error": "Vector store chưa được khởi tạo. Chạy ingest_documents() trước."},
                status_code=503,
            )

        result = rag.query(question)
        return JSONResponse({"answer": result.answer, "sources": result.sources})

except ImportError:
    app = None  # type: ignore[assignment]


# ── CLI Entry Point ──────────────────────────────────────────────────────────

def run_cli(query: str, use_pvlib: bool = False) -> None:
    """Chạy phân tích từ command line."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "nlp-chatbot-interface"))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "solar-physics-vn"))

    from text_to_solar import TextToSolarEngine

    engine = TextToSolarEngine(use_pvlib=use_pvlib)
    report = engine.analyze(query)
    print(report.to_vietnamese())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NLP-Solar-Vietnam CLI")
    parser.add_argument("--query", "-q", type=str, help="Câu hỏi tiếng Việt")
    parser.add_argument("--serve", action="store_true", help="Khởi động API server")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-pvlib", action="store_true", help="Dùng ước tính đơn giản (offline)")

    args = parser.parse_args()

    if args.serve:
        if app is None:
            print("Lỗi: fastapi chưa được cài đặt. Chạy: pip install fastapi uvicorn")
            sys.exit(1)
        import uvicorn
        uvicorn.run("app:app", host="0.0.0.0", port=args.port, reload=True)
    elif args.query:
        run_cli(args.query, use_pvlib=not args.no_pvlib)
    else:
        # Demo mặc định
        demo_query = "Nhà tôi ở Gia Lai, mái tôn hướng Nam, diện tích 50m², tiền điện 2 triệu/tháng, muốn tiết kiệm chi phí."
        print(f"Demo query: {demo_query}\n")
        run_cli(demo_query, use_pvlib=False)
