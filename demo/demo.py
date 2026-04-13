"""
Isolated demo runner.
This script does not modify root index.py, rag_answer.py, eval.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from preprocess import OUTPUT_DIR as PREPROCESS_OUTPUT_DIR
from preprocess import run_all as preprocess_run_all
from index import CHROMA_DB_DIR, build_index
from rag_answer import rag_answer


DEMO_ROOT = Path(__file__).parent
PROJECT_ROOT = DEMO_ROOT.parent
EXTERNAL_TEST_PATH = PROJECT_ROOT / "external_data" / "test_questions.json"
DEMO_MODES = ["dense", "hybrid"]


def print_block_header(title: str, width: int = 96) -> None:
    print("\n" + "=" * width)
    print(title)
    print("=" * width)


def print_sub_header(title: str, width: int = 96) -> None:
    print("\n" + "-" * width)
    print(title)
    print("-" * width)


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def print_chunk_details(chunks: List[Dict[str, Any]]) -> None:
    if not chunks:
        print("[Chunks] Không có chunk nào được chọn.")
        return

    print("[Chunks được chọn - IN ĐẦY ĐỦ]")
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {}) or {}
        source = _safe_text(meta.get("source", "unknown"))
        section = _safe_text(meta.get("section", ""))
        score = chunk.get("score", None)
        text = _safe_text(chunk.get("text", "")).strip()

        print("\n" + "~" * 96)
        print(f"Chunk #{i}")
        print(f"source : {source}")
        print(f"section: {section}")
        if score is not None:
            try:
                print(f"score  : {float(score):.6f}")
            except Exception:
                print(f"score  : {score}")
        print("text   :")
        print(text if text else "(empty)")
        print("~" * 96)


def run_single_query(query: str, mode: str) -> None:
    print_sub_header(f"Mode: {mode.upper()}")
    try:
        result = rag_answer(
            query=query,
            retrieval_mode=mode,
            top_k_search=10,
            top_k_select=3,
            use_rerank=False,
            verbose=False,
        )
    except Exception as exc:
        print(f"Lỗi khi chạy mode '{mode}': {exc}")
        return

    answer = _safe_text(result.get("answer", ""))
    sources = result.get("sources", []) or []
    chunks = result.get("chunks_used", []) or []

    print("[Câu trả lời của LLM]")
    print(answer if answer else "(empty)")

    print("\n[Nguồn lấy được]")
    if sources:
        for idx, src in enumerate(sources, 1):
            print(f"{idx}. {_safe_text(src)}")
    else:
        print("(Không có source)")

    print()
    print_chunk_details(chunks)


def run_external_tests() -> None:
    print_block_header("BƯỚC 3: CHẠY 10 TEST (DENSE + HYBRID)")

    if not EXTERNAL_TEST_PATH.exists():
        print(f"Không tìm thấy file test: {EXTERNAL_TEST_PATH}")
        return

    with EXTERNAL_TEST_PATH.open("r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Số test loaded: {len(questions)}")

    for idx, item in enumerate(questions, 1):
        qid = _safe_text(item.get("id", f"q{idx:02d}"))
        query = _safe_text(item.get("question", "")).strip()

        print_block_header(f"TEST {idx}/10 | {qid}")
        print(f"Query: {query}")

        for mode in DEMO_MODES:
            run_single_query(query, mode)


def chat_loop() -> None:
    print_block_header("BƯỚC 4: CHATBOT MODE (DENSE + HYBRID)")
    print("Nhập câu hỏi để chat. Gõ 'exit' hoặc 'quit' để thoát.")

    while True:
        print("\n" + ">" * 96)
        user_query = input("Bạn: ").strip()
        if not user_query:
            print("Vui lòng nhập câu hỏi.")
            continue
        if user_query.lower() in {"exit", "quit"}:
            print("Kết thúc chatbot demo.")
            break

        print_block_header(f"TRẢ LỜI CHO: {user_query}")
        for mode in DEMO_MODES:
            run_single_query(user_query, mode)


def main() -> None:
    print_block_header("FULL RAG DEMO (ISOLATED IN demo/)")

    print_block_header("BƯỚC 1: PREPROCESSING TÀI LIỆU")
    generated = preprocess_run_all()
    if generated:
        print("Đã preprocess các file:")
        for p in generated:
            print(f"- {p}")
    else:
        print("Không có file nào được preprocess (kiểm tra external_data/raw_data).")

    print_block_header("BƯỚC 2: BUILD INDEX VÀO CHROMADB")
    print(f"Nguồn docs để index: {PREPROCESS_OUTPUT_DIR}")
    print(f"Thư mục ChromaDB     : {CHROMA_DB_DIR}")
    build_index(docs_dir=PREPROCESS_OUTPUT_DIR, db_dir=CHROMA_DB_DIR, reset_collection=True)

    run_external_tests()
    chat_loop()


if __name__ == "__main__":
    main()
