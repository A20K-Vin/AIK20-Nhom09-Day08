"""
run_grading.py — Chạy pipeline với grading_questions.json và lưu log
Chạy lệnh: python run_grading.py
Output: logs/grading_run.json
"""

import json
from pathlib import Path
from datetime import datetime
from rag_answer import rag_answer

GRADING_QUESTIONS_PATH = Path(__file__).parent / "data" / "grading_questions.json"
LOG_OUTPUT_PATH = Path(__file__).parent / "logs" / "grading_run.json"

# Dùng config tốt nhất của nhóm
RETRIEVAL_MODE = "hybrid"
USE_RERANK = True
TOP_K_SEARCH = 10
TOP_K_SELECT = 3


def run_grading():
    LOG_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(GRADING_QUESTIONS_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Chạy grading với {len(questions)} câu hỏi...")
    print(f"Config: retrieval_mode={RETRIEVAL_MODE}, use_rerank={USE_RERANK}\n")

    log = []
    for q in questions:
        print(f"  [{q['id']}] {q['question'][:60]}...")
        try:
            result = rag_answer(
                q["question"],
                retrieval_mode=RETRIEVAL_MODE,
                top_k_search=TOP_K_SEARCH,
                top_k_select=TOP_K_SELECT,
                use_rerank=USE_RERANK,
                verbose=False,
            )
            log.append({
                "id": q["id"],
                "question": q["question"],
                "answer": result["answer"],
                "sources": result["sources"],
                "chunks_retrieved": len(result["chunks_used"]),
                "retrieval_mode": result["config"]["retrieval_mode"],
                "timestamp": datetime.now().isoformat(),
            })
            print(f"    → {result['answer'][:80]}...")
        except Exception as e:
            log.append({
                "id": q["id"],
                "question": q["question"],
                "answer": f"PIPELINE_ERROR: {e}",
                "sources": [],
                "chunks_retrieved": 0,
                "retrieval_mode": RETRIEVAL_MODE,
                "timestamp": datetime.now().isoformat(),
            })
            print(f"    → ERROR: {e}")

    with open(LOG_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Log lưu tại: {LOG_OUTPUT_PATH}")
    print(f"Tổng: {len(log)} câu")


if __name__ == "__main__":
    run_grading()
