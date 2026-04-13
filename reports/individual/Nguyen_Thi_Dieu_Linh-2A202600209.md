# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Thị Diệu Linh   
**Vai trò trong nhóm:** Retrieval Owner  
**Ngày nộp:** 13/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

> Mô tả cụ thể phần bạn đóng góp vào pipeline:
> - Sprint nào bạn chủ yếu làm?  
Tôi tập trung chủ yếu vào Sprint 3, giai đoạn tối ưu hóa (Tuning) hiệu suất hệ thống RAG từ Baseline (Dense retrieval) lên các biến thể nâng cao.
> - Cụ thể bạn implement hoặc quyết định điều gì?  
Xây dựng Sparse Retrieval: Tôi  implement hàm retrieve_sparse sử dụng thuật toán BM25 (thư viện rank_bm25). Quyết định này nhằm khắc phục điểm yếu của Dense search trong việc truy xuất các từ khóa đặc hiệu, thuật ngữ chuyên ngành và mã lỗi kỹ thuật (như ERR-403-AUTH).  
Thiết lập Hybrid Pipeline: Tôi đã xây dựng hàm retrieve_hybrid để kết hợp kết quả từ cả hai không gian Vector (Dense) và Keyword (Sparse). Tôi đã áp dụng thuật toán Reciprocal Rank Fusion (RRF) để tính toán lại điểm số (score) cho các chunk dữ liệu, giúp cân bằng giữa ý nghĩa ngữ nghĩa và độ khớp từ khóa chính xác.  
> - Công việc của bạn kết nối với phần của người khác như thế nào?  
Công việc của tôi đóng vai trò là trung gian trong Pipeline. Tôi tiếp nhận query đã được tiền xử lý từ phần Input/Index.  
Kết quả trả về từ phần của tôi là danh sách top_k các chunks dữ liệu chất lượng nhất, đây là đầu vào trực tiếp cho phần sinh câu trả lời.  
Nếu phần Retrieval của tôi không tìm được đúng dữ liệu (như trường hợp Sources: []), nó sẽ kích hoạt cơ chế Abstain (từ chối trả lời) trong phần Prompt, giúp hệ thống tránh được lỗi ảo tưởng thông tin.

_________________

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

>Thông qua các nội dung thực hành, tôi đã hiểu hơn về concept trong phát triển ứng dụng LLMs:
>- Grounded Prompt (Prompt dựa trên dữ liệu cơ sở): Việc tối ưu hóa câu lệnh không chỉ dừng lại ở cấu trúc ngôn ngữ mà còn nằm ở khả năng kiểm soát tri thức. Triển khai grounding giúp mô hình truy xuất và phản hồi dựa trên các nguồn tài liệu tin cậy được cung cấp sẵn thay vì chỉ dựa vào xác suất thống kê từ dữ liệu huấn luyện. Điều này đóng vai trò tiên quyết trong việc hạn chế hiện tượng hallucination, đảm bảo tính xác thực và độ tin cậy của thông tin đầu ra trong các ứng dụng thực tế.
>- Evaluation Loop (Vòng lặp đánh giá): Lab thực hành giúp tôi tiếp cận quy trình phát triển AI theo hướng thực nghiệm. Thay vì điều chỉnh prompt một cách cảm tính, Evaluation Loop thiết lập một hệ quy chiếu để đo lường hiệu suất một cách khách quan. Thông qua việc thử nghiệm liên tục, phân tích sai số và tinh chỉnh tham số dựa trên kết quả định lượng, tôi hiểu rằng đây là quy trình bắt buộc để đạt được sự ổn định và tối ưu hóa chất lượng hệ thống một cách bền vững.
_________________

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

> - Trong bài test với mã lỗi ERR-403-AUTH, cả ba chiến lược đều cho ra kết quả cuối cùng là "Không đủ dữ liệu". Tuy nhiên, điều không đúng kỳ vọng nằm ở phần trích dẫn (Sources). Trong khi tôi mong đợi ít nhất chiến lược Sparse hoặc Hybrid phải tìm thấy tài liệu hướng dẫn về quyền truy cập (access-control-sop.md) để làm căn cứ, thì kết quả thực tế ở bản Baseline lại trả về danh sách nguồn trống rỗng, khiến câu trả lời của AI thiếu tính thuyết phục và không có cơ sở đối chiếu.    
> - Lỗi mất thời gian nhất là xử lý sự sai lệch giữa các kết quả Retrieval. Việc Sparse search trả về rỗng trong khi Dense search vẫn tìm thấy file "có vẻ liên quan" khiến tôi phải tốn công kiểm tra lại xem mã lỗi đã được đánh chỉ mục (index) đúng cách trong ChromaDB hay chưa.  
> - Giả thuyết ban đầu của bạn là gì và thực tế ra sao?  
Giả thuyết: Cứ bật Hybrid lên là mặc định sẽ lấy được cái tốt nhất của cả hai bên: vừa hiểu nghĩa, vừa bắt được từ khóa mã lỗi. 
Thực tế: Hybrid hay Sparse thực chất chỉ giúp AI tìm thấy đúng file tốt hơn thôi, còn nếu trong file đó thực sự không có định nghĩa mã lỗi, AI vẫn phải trung thực từ chối (Abstain). Thực tế cho thấy sự khác biệt nằm ở "chất lượng của sự từ chối":  
Dense: Thường bỏ qua vì không hiểu nghĩa của mã lỗi.  
Sparse: Tìm thấy đúng tài liệu nhờ khớp từ khóa nhưng vẫn không trả lời được vì tài liệu thiếu thông tin chi tiết.  
Hybrid: Kết hợp cả hai, dẫn đến một câu trả lời mang tính chất "có căn cứ hơn" (trích dẫn được tài liệu) dù kết quả cuối cùng vẫn là không biết.

_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

> Chọn 1 câu hỏi trong test_questions.json mà nhóm bạn thấy thú vị.
> Phân tích:
> - Baseline trả lời đúng hay sai? Điểm như thế nào?
> - Lỗi nằm ở đâu: indexing / retrieval / generation?
> - Variant có cải thiện không? Tại sao có/không?

**Câu hỏi:** q04 - "Sản phẩm kỹ thuật số có được hoàn tiền không?"

**Phân tích:**
1. Baseline trả lời đúng hay sai? Điểm như thế nào?

Kết quả: Baseline trả lời Sai về mặt nội dung logic (Faithfulness thấp).

Điểm số: Faithfulness chỉ đạt 2/5.

Trạng thái: Mặc dù hệ thống tìm được đúng tài liệu (policy/refund-v4.pdf) với điểm Recall tuyệt đối (5/5), nhưng cả hai phiên bản đều đưa ra thông tin sai lệch so với thực tế của tài liệu.

2. Xác định nguyên nhân lỗi (Root Cause)  

Lỗi này không nằm ở khâu Indexing hay Retrieval mà nằm ở Generation (Khâu sinh câu trả lời):

Lỗi Grounding: Mô hình đã tự ý thêm điều kiện "hoàn tiền nếu lỗi do nhà sản xuất". Đây là một dạng kiến thức ngoài (out-of-bound knowledge) mà LLM tự suy diễn, không hề có trong tập Context được cung cấp.

Lỗi xử lý logic ngoại lệ: Trong tài liệu có nhiều thông tin về việc "cho phép hoàn tiền trong 7 ngày", LLM đã bị ảnh hưởng bởi các quy tắc chung này và bỏ qua dòng thông tin quan trọng về ngoại lệ (exception) dành riêng cho hàng kỹ thuật số.

3. So sánh Baseline và Variant

Sự giống nhau: Cả hai đều lấy được đúng chunk dữ liệu cần thiết.

Tại sao Variant không cải thiện được? Vì Hybrid và Rerank chỉ giúp tối ưu hóa việc tìm thấy tài liệu. Khi lỗi nằm ở khả năng đọc hiểu và tuân thủ kỷ luật "chỉ trả lời dựa trên context" của LLM, thì việc cung cấp context chính xác hơn cũng không giải quyết được vấn đề nếu Prompt chưa đủ mạnh để ngăn chặn sự suy diễn của mô hình.

_________________

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

> 1-2 cải tiến cụ thể bạn muốn thử.
> Không phải "làm tốt hơn chung chung" mà phải là:
> "Tôi sẽ thử X vì kết quả eval cho thấy Y."  

Cải tiến: Tối ưu hóa "Query Transformation" (Decomposition & Expansion)

Tôi sẽ thử: Triển khai thêm bước Query Decomposition (tách câu hỏi phức tạp thành các câu hỏi con) trước khi thực hiện Retrieval.

Lý do (Dựa trên kết quả Eval): Chỉ số Completeness hiện tại chỉ đạt 3.90/5. Đặc biệt ở các câu hỏi như q08 (HR Policy) hay q10, dù Recall tốt nhưng câu trả lời chưa đầy đủ ý. Việc tách nhỏ query sẽ giúp hệ thống truy xuất được đa dạng các chunk thông tin khác nhau, từ đó giúp LLM tổng hợp câu trả lời chi tiết và đầy đủ hơn thay vì chỉ tập trung vào một khía cạnh của câu hỏi.
_________________

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*
*Ví dụ: `reports/individual/nguyen_van_a.md`*
