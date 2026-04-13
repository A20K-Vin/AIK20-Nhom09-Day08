# Tuning Log — RAG Pipeline (Day 08 Lab)

> Template: Ghi lại mỗi thay đổi và kết quả quan sát được.
> A/B Rule: Chỉ đổi MỘT biến mỗi lần.

---

## Baseline (Sprint 2)

**Ngày:** 13/04/2026  
**Config:**
```
retrieval_mode = "dense"
chunk_size = 1600 characters (tương đương 400 tokens)
overlap = 320 characters (tương đương 80 tokens)
top_k_search = 10
top_k_select = 3
use_rerank = False
llm_model = got-4o-mini
```

**Scorecard Baseline:**
| Metric | Average Score |
|--------|--------------|
| Faithfulness | 4.60/5 |
| Relevance | 4.80/5 |
| Context Recall | 5.00/5 |
| Completeness | 3.90/5 |

**Câu hỏi yếu nhất (điểm thấp):**
q04 (Refund) — Faithfulness = 2/5, Completeness = 3/5.
Trả lời có thêm điều kiện “lỗi do nhà sản xuất” không có trong context, nên bị lỗi grounding.

q07 (Access Control) — Relevance = 3/5, Completeness = 2/5.
Câu hỏi alias “Approval Matrix” chưa được map tốt sang tên tài liệu hiện tại (Access Control SOP), nên thiếu ý chính.

q09 (Insufficient Context) — Completeness = 2/5.
Đây là câu cần abstain, nhưng baseline vẫn suy diễn theo ngữ cảnh access-control thay vì trả lời thiếu dữ liệu đúng intent expected answer.

**Giả thuyết nguyên nhân (Error Tree):**
- [ ] Indexing: Chunking cắt giữa điều khoản
- [ ] Indexing: Metadata thiếu effective_date
- [ ] Retrieval: Dense bỏ lỡ exact keyword / alias
- [ ] Retrieval: Top-k quá ít → thiếu evidence
- [ ] Generation: Prompt không đủ grounding
- [ ] Generation: Context quá dài → lost in the middle

---

## Variant 1 (Sprint 3)

**Ngày:** 13/04/2026  
**Biến thay đổi:** retrieval_mode  
**Lý do chọn biến này:**
> TODO: Giải thích theo evidence từ baseline results.
> Ví dụ: "Chọn hybrid vì q07 (alias query) và q09 (mã lỗi ERR-403) đều thất bại với dense.
> Corpus có cả ngôn ngữ tự nhiên (policy) lẫn tên riêng/mã lỗi (ticket code, SLA label)."

q04 (Refund) — Faithfulness = 2/5, Completeness = 3/5.
Trả lời có thêm điều kiện “trừ khi có lỗi do nhà sản xuất” nhưng không có trong context, nên bị lỗi grounded/hallucination nhẹ.

q07 (Access Control) — Relevance = 3/5, Completeness = 2/5.
Câu hỏi dạng alias (“Approval Matrix”) nhưng model chỉ mô tả chung tài liệu, không nêu được ý chính là tên hiện tại là Access Control SOP.

q09 (Insufficient Context) — Completeness = 2/5.
Đây là câu cần abstain, nhưng baseline lại suy diễn hướng xử lý quyền truy cập từ context khác thay vì nói “không đủ dữ liệu”, nên thiếu đúng intent của expected answer.
**Config thay đổi:**
```
retrieval_mode = "hybrid"   # hoặc biến khác
# Các tham số còn lại giữ nguyên như baseline
```

**Scorecard Variant 1:**
| Metric | Baseline | Variant | Delta |
|--------|----------|---------|-------|
| faithfulness | 4.60 | 4.50 | -0.10 |
| relevance | 4.80 | 4.40 | -0.40 |
| context_recall | 5.00 | 5.00 | +0.00 |
| completeness | 3.90 | 3.90 | +0.00 |

| Câu | Baseline F/R/Rc/C | Variant F/R/Rc/C | Better? |
|-----|--------------------|------------------|---------|
| q01 | 5/5/5/5 | 5/5/5/5 | Tie |
| q02 | 4/5/5/5 | 5/5/5/5 | Variant |
| q03 | 5/5/5/5 | 5/5/5/5 | Tie |
| q04 | 2/5/5/3 | 3/5/5/3 | Variant |
| q05 | 5/5/5/5 | 5/5/5/5 | Tie |
| q06 | 5/5/5/5 | 5/3/5/1 | Baseline |
| q07 | 5/3/5/2 | 2/5/5/2 | Baseline |
| q08 | 5/5/5/4 | 5/5/5/5 | Variant |
| q09 | 5/5/None/2 | 5/1/None/5 | Baseline |
| q10 | 5/5/5/3 | 5/5/5/3 | Tie |

**Nhận xét:**
> TODO: Variant 1 cải thiện ở câu nào? Tại sao?
Variant cải thiện rõ ở q02, q04, q08.

> q02: Faithfulness tăng 4 → 5 (trả lời bám context hơn).
q04: Faithfulness tăng 2 → 3 (giảm bớt suy diễn, dù vẫn chưa hoàn toàn đúng kỳ vọng).
q08: Completeness tăng 4 → 5 (đủ ý hơn ở điều kiện remote).
> Có câu nào kém hơn không? Tại sao?
Có, giảm ở q06, q07, q09.

> q06: Relevance/Completeness giảm mạnh (5/5 → 3/1) do lệch ngữ cảnh escalation P1.

> q07: Faithfulness giảm (5 → 2) vì không xử lý tốt query alias “Approval Matrix” ↔ “Access Control SOP”.

> q09: Relevance giảm (5 → 1) vì variant trả lời quá ngắn (“Tôi không biết.”), đúng hướng abstain nhưng thiếu thông tin định hướng theo expected answer.
**Kết luận:**
> TODO: Variant 1 có tốt hơn baseline không?
Không tốt hơn tổng thể.
> Bằng chứng là gì? (điểm số, câu hỏi cụ thể)

Bằng chứng:

> Điểm trung bình giảm ở 2 metric chính: Faithfulness 4.60 → 4.50 (-0.10), Relevance 4.80 → 4.40 (-0.40).

> Context Recall giữ nguyên 5.00, Completeness giữ nguyên 3.90 (không có cải thiện tổng thể).

> Dù có 3 câu cải thiện (q02, q04, q08), các lỗi giảm chất lượng ở q06, q07, q09 có tác động lớn hơn, nên baseline vẫn ổn định hơn cho bộ test này.
---

## Variant 2 (nếu có thời gian)

**Biến thay đổi:** use_rerank  
**Config:** True
```
retrieval_mode = "dense"
use_rerank = True
top_k_search = 10
top_k_select = 3
# Giữ nguyên các tham số khác để đúng A/B rule (chỉ đổi 1 biến).
# Evidence từ baseline: lỗi chính nằm ở ranking/chọn ngữ cảnh cho câu khó,
# đặc biệt q09 (câu cần abstain) nên thử rerank để ưu tiên context liên quan hơn.
```

**Scorecard Variant 2:**
| Metric | Baseline | Variant | Delta |
|--------|----------|---------|-------|
| faithfulness | 4.60 | 4.60 | +0.00 |
| relevance | 4.60 | 5.00 | +0.40 |
| context_recall | 5.00 | 5.00 | +0.00 |
| completeness | 3.90 | 3.90 | +0.00 |

| Câu | Baseline F/R/Rc/C | Variant F/R/Rc/C | Better? |
|-----|--------------------|------------------|---------|
| q01 | 5/5/5/5 | 5/5/5/5 | Tie |
| q02 | 4/5/5/5 | 4/5/5/5 | Tie |
| q03 | 5/5/5/5 | 5/5/5/5 | Tie |
| q04 | 2/5/5/3 | 2/5/5/3 | Tie |
| q05 | 5/5/5/5 | 5/5/5/5 | Tie |
| q06 | 5/5/5/5 | 5/5/5/5 | Tie |
| q07 | 5/5/5/1 | 5/5/5/1 | Tie |
| q08 | 5/5/5/4 | 5/5/5/4 | Tie |
| q09 | 5/1/None/5 | 5/5/None/5 | Variant |
| q10 | 5/5/5/1 | 5/5/5/1 | Tie |

---

## Tóm tắt học được

> TODO (Sprint 4): Điền sau khi hoàn thành evaluation.

1. **Lỗi phổ biến nhất trong pipeline này là gì?**
   > Lỗi phổ biến nhất là retrieval đúng source nhưng chọn/chấm chưa đúng intent câu hỏi, dẫn tới answer lệch trọng tâm (đặc biệt với câu alias và câu cần abstain). Ngoài ra model đôi lúc thêm suy diễn ngoài context ở các câu policy.

2. **Biến nào có tác động lớn nhất tới chất lượng?**
   > Biến có tác động lớn nhất là retrieval strategy (dense vs hybrid/rerank). Trong kết quả hiện tại, đổi sang variant làm giảm rõ Relevance (4.80 -> 4.40), cho thấy retrieval/ranking quyết định chất lượng nhiều hơn các phần còn lại.

3. **Nếu có thêm 1 giờ, nhóm sẽ thử gì tiếp theo?**
   > Nhóm sẽ thử query transformation nhẹ + rule abstain rõ hơn (đặc biệt cho query alias như “Approval Matrix” và câu out-of-doc như ERR-403-AUTH), rồi chạy lại A/B chỉ đổi 1 biến để kiểm tra có tăng Relevance mà không giảm Faithfulness hay không.
