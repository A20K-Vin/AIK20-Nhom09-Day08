# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Triệu Gia Khánh - 2A202600225

**Vai trò trong nhóm:** Documentation Owner (Kiêm rerank + query transformation)  

**Ngày nộp:** 13/04/2026  

**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

> Mô tả cụ thể phần bạn đóng góp vào pipeline:
> - Sprint nào bạn chủ yếu làm?
> - Cụ thể bạn implement hoặc quyết định điều gì?
> - Công việc của bạn kết nối với phần của người khác như thế nào?

Trong lab này, em phụ trách vai trò Documentation Owner và đồng thời tham gia phần retrieval improvement ở sprint 3 và sprint 4.  

Ở sprint 3, em tập trung vào rerank. Em giữ nguyên cấu hình retrieve dense ban đầu để tuân thủ A/B rule, sau đó bật thêm `use_rerank=True` với cross-encoder để sắp lại top candidate trước khi đưa vào prompt.  

Ở sprint 4, em làm query transformation ở mức nhẹ: chuẩn hóa alias, bổ sung từ khóa đồng nghĩa, và làm rõ intent cho các câu hỏi dễ lệch ngữ cảnh. Mục tiêu là tăng khả năng map đúng tài liệu trước khi retrieve.  

Song song đó, em viết lại `docs/architecture.md` và `docs/tuning-log.md` để cả nhóm dùng chung một cách mô tả pipeline, cùng thuật ngữ và cùng logic so sánh baseline/variant.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

> Chọn 1-2 concept từ bài học mà bạn thực sự hiểu rõ hơn sau khi làm lab.
> Ví dụ: chunking, hybrid retrieval, grounded prompt, evaluation loop.
> Giải thích bằng ngôn ngữ của bạn — không copy từ slide.

Sau lab này, em hiểu rõ hơn vai trò của ranking quality trong retrieval pipeline.  

Trước đây em thường nghĩ “retrieve được đúng source là đủ”. Nhưng khi chấm scorecard, em thấy nếu thứ tự context chưa đúng intent thì câu trả lời vẫn có thể thiếu ý hoặc lệch trọng tâm. Rerank giúp giải quyết đúng chỗ này: không mở rộng kho tri thức, nhưng ưu tiên lại những đoạn liên quan nhất.  

Concept thứ hai em hiểu rõ hơn là query transformation. Nhiều câu hỏi thực tế dùng alias hoặc cách diễn đạt khác với tên tài liệu gốc. Nếu không chuẩn hóa từ đầu, retriever dễ lấy context gần nghĩa nhưng không trúng ý chính. Em thấy transform query là bước “làm sạch đầu vào” rất quan trọng trước khi tối ưu các bước sau.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

> Điều gì xảy ra không đúng kỳ vọng?
> Lỗi nào mất nhiều thời gian debug nhất?
> Giả thuyết ban đầu của bạn là gì và thực tế ra sao?

Điều khiến em ngạc nhiên là không phải cứ thêm kỹ thuật mới thì điểm sẽ tăng đồng đều ở mọi metric.  

Khi thử variant retrieval khác baseline, có câu tăng Faithfulness hoặc Completeness, nhưng lại có câu giảm Relevance khá mạnh. Điều này làm kết quả trung bình không tốt hơn như kỳ vọng ban đầu.  

Phần khó nhất là debug các câu dạng alias và câu cần abstain. Giả thuyết đầu của em là lỗi nằm ở chunk hoặc thiếu metadata. Sau khi đối chiếu scorecard chi tiết từng câu, em thấy nguyên nhân lớn hơn nằm ở ranking và cách diễn đạt query. Vì vậy em chuyển trọng tâm sang rerank + query transformation thay vì thay đổi quá nhiều biến cùng lúc.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

> Chọn 1 câu hỏi trong test_questions.json mà nhóm bạn thấy thú vị.
> Phân tích:
> - Baseline trả lời đúng hay sai? Điểm như thế nào?
> - Lỗi nằm ở đâu: indexing / retrieval / generation?
> - Variant có cải thiện không? Tại sao có/không?

**Câu hỏi:** q09 (Insufficient Context / cần abstain)

**Phân tích:**

Đây là câu em thấy quan trọng vì nó kiểm tra tính “an toàn” của pipeline, không chỉ kiểm tra việc trả lời đúng nội dung.  

Ở baseline, hệ thống vẫn cố trả lời theo ngữ cảnh access-control dù dữ kiện chưa đủ để kết luận. Điểm Completeness thấp vì answer không đi đúng intent expected answer (cần thừa nhận thiếu dữ liệu và trả lời theo hướng an toàn).  

Khi chuyển sang variant có rerank, câu này cải thiện Relevance rõ rệt. Lý do là rerank đẩy lên các chunk liên quan trực tiếp đến giới hạn thông tin, giảm bớt các chunk “na ná” nhưng dễ dẫn model suy diễn.  

Sau đó em bổ sung query transformation cho nhóm câu khó tương tự: thêm chuẩn hóa alias và tín hiệu nhận biết câu hỏi thiếu ngữ cảnh. Cách này không làm thay đổi indexing, nhưng giúp retrieval nhận diện intent tốt hơn ngay từ đầu.  

Qua câu q09, em rút ra rằng lỗi không chỉ ở generation prompt. Nếu retrieval stage chưa đúng intent thì prompt grounded vẫn có thể sinh câu trả lời chưa phù hợp với yêu cầu abstain.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

> 1-2 cải tiến cụ thể bạn muốn thử.
> Không phải "làm tốt hơn chung chung" mà phải là:
> "Tôi sẽ thử X vì kết quả eval cho thấy Y."

Nếu có thêm thời gian, em sẽ thử một pipeline hai tầng cho query transformation:  

(1) rule-based rewrite cho alias phổ biến theo domain từ scorecard,  
(2) LLM rewrite có ràng buộc “không thêm thông tin ngoài query gốc”.  

Em chọn hướng này vì kết quả eval cho thấy các câu alias và câu thiếu ngữ cảnh là nhóm gây giảm điểm Relevance nhiều nhất, trong khi rerank đã xử lý tốt một phần nhưng chưa đủ ổn định.

---
*Lưu file này với tên: `reports/individual/[ten_ban].md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*

