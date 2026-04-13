# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Hoàng Duy  
**MSSV:** 2A202600158  
**Vai trò trong nhóm:** Eval Owner  
**Ngày nộp:** 13/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Tôi phụ trách vai trò **Eval Owner**, chịu trách nhiệm chính cho hai file `eval.py` và `run_grading.py`.

Về `eval.py`, tôi implement toàn bộ phần **LLM-as-Judge**: viết hàm `_call_judge()` gọi `gpt-4o` với JSON response format, sau đó dùng nó để implement ba hàm chấm tự động — `score_faithfulness`, `score_answer_relevance`, và `score_completeness`. Ngoài ra, tôi fix bug falsy-zero (`if avg` → `if avg is not None`) ở ba chỗ khiến điểm 0.0 hiển thị sai thành N/A, và sửa lại BASELINE_CONFIG (`use_rerank=False`) cùng VARIANT_CONFIG (`retrieval_mode="hybrid"`) để A/B testing đúng quy tắc một biến.

Về `run_grading.py`, tôi tạo script chạy toàn bộ 10 câu trong `grading_questions.json` với config tốt nhất của nhóm (`hybrid`, `use_rerank=True`, `top_k_search=10`, `top_k_select=3`), ghi output ra `logs/grading_run.json` theo đúng format yêu cầu. Kết quả 10/10 câu chạy thành công, không có PIPELINE_ERROR.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Sau lab này, tôi hiểu rõ hơn rằng **evaluation pipeline cũng cần được debug nghiêm túc như production code**, không chỉ là phụ lục của pipeline chính.

Cụ thể, bug `if avg` (falsy zero) là lỗi điển hình của Python: khi `score_context_recall` trả về `0.0`, biểu thức `if avg` đánh giá là `False` và metric hiển thị "N/A" thay vì `0.0`. Đây là loại lỗi silent — không crash, không traceback, nhưng làm sai kết quả hoàn toàn. Nếu không kiểm tra output kỹ, nhóm sẽ nghĩ context recall không đo được thay vì biết pipeline đang retrieval kém.

Tôi cũng hiểu rõ hơn tầm quan trọng của **A/B rule một biến**: khi baseline và variant cùng bật `use_rerank=True`, delta luôn là 0 và kết quả A/B không có ý nghĩa thống kê nào. Chỉ khi giữ một biến thay đổi mới rút ra được kết luận nhân quả đúng.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Điều khiến tôi bất ngờ nhất là **cross-encoder ms-marco-MiniLM-L-6-v2 thực sự hoạt động kém hơn trên tiếng Việt** so với dense retrieval đơn thuần.

Giả thuyết ban đầu: bật rerank với cross-encoder sẽ luôn cải thiện context quality vì model có khả năng so sánh query-document trực tiếp. Thực tế: variant (`hybrid + rerank`) có điểm faithfulness và completeness thấp hơn baseline (`dense`) ở nhiều câu. Lý do là ms-marco được train trên MS MARCO dataset tiếng Anh — khi áp dụng lên tài liệu tiếng Việt, nó rerank theo pattern không liên quan đến nội dung thực, dẫn đến các chunk tốt bị đẩy xuống dưới top-3.

Khó khăn thực tế nhất là debug cross-encoder: không có lỗi nào được throw, pipeline chạy bình thường, nhưng quality giảm. Chỉ khi đọc kỹ scorecard từng câu mới thấy pattern này.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi gq05:** "Một contractor bên ngoài công ty có thể được cấp quyền Admin Access không? Nếu có, cần những điều kiện và approver nào?"

**Kết quả pipeline:** `answer = "Không đủ dữ liệu để trả lời."` — pipeline abstain sai.

**Phân tích root cause — lỗi nằm ở retrieval:**

File `it/access-control-sop.md` có hai chunk quan trọng cho câu này:
- **Section 1** (scope): "Áp dụng cho tất cả nhân viên, **contractor**, và third-party vendor."
- **Section 2** (Level 4): "Admin Access: Phê duyệt IT Manager + CISO, 5 ngày làm việc, training bắt buộc."

Với `top_k_select=3`, reranker ưu tiên Section 2 (có từ "Admin Access" khớp trực tiếp query) nhưng đẩy Section 1 ra ngoài top-3 vì chunk này không chứa "Admin Access" mà chỉ nói về scope. Kết quả: LLM nhận được thông tin về Level 4 nhưng không biết contractor được phép nên abstain.

**Nguyên nhân sâu hơn:** cross-encoder ms-marco score theo keyword match, Section 1 là context gián tiếp (scope declaration) bị đánh giá thấp hơn Section 2 là context trực tiếp. Đây là failure mode đặc trưng của câu cần **multi-section synthesis** trong cùng một tài liệu.

**Fix đề xuất:** Tăng `top_k_select` từ 3 lên 5 để giữ cả Section 1 và Section 2 trong context gửi vào prompt.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

**Cải tiến 1:** Tăng `top_k_select=5` vì scorecard cho thấy gq05 fail do mất Section 1 (scope chunk) khi chỉ giữ top-3. Chi phí context tăng nhẹ nhưng câu cần multi-section retrieval sẽ được fix.

**Cải tiến 2:** Thay `ms-marco-MiniLM-L-6-v2` bằng cross-encoder multilingual (ví dụ `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`) vì eval cho thấy reranker tiếng Anh reorder sai trên corpus tiếng Việt, khiến variant tệ hơn baseline thay vì tốt hơn.

---
