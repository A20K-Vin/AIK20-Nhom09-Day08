# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Thùy Linh - 2A202600216

**Vai trò trong nhóm:** Tech Lead

**Ngày nộp:** 13/04/2026  

**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong lab này, với tư cách là Tech Lead, em chịu trách nhiệm chính trong việc thiết lập cấu trúc repo và đảm bảo luồng dữ liệu thông suốt giữa các module. Em tập trung chủ yếu vào Sprint 1 và Sprint 2.

Ở Sprint 1, em trực tiếp implement hàm get_embedding() sử dụng OpenAI API và hoàn thiện logic upsert trong index.py. Em đã quyết định cấu trúc metadata gồm 3 trường: source, section và effective_date để hỗ trợ việc lọc dữ liệu sau này.

Ở Sprint 2, em xây dựng hàm retrieve_dense() để thực hiện vector search trên ChromaDB và thiết kế function call_llm() để kết nối với Gemini. Công việc của em đóng vai trò là "xương sống": tạo ra một baseline RAG hoàn chỉnh để Retrieval Owner có thể thử nghiệm các variant ở Sprint 3 và Eval Owner có dữ liệu để chấm điểm trong Sprint 4.

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Sau lab này, em hiểu rõ hơn về mối quan hệ mật thiết giữa Metadata và Retrieval Quality.

Trước đây, em chỉ nghĩ đơn giản là đưa văn bản vào vector database. Tuy nhiên, khi trực tiếp implement index.py, em nhận ra rằng nếu không xử lý chunking khéo léo (ví dụ: cắt ngang một điều khoản SLA), vector embedding sẽ bị mất ngữ cảnh, dẫn đến kết quả retrieval bị nhiễu. Việc gắn metadata cụ thể giúp hệ thống không chỉ tìm được đoạn văn bản liên quan mà còn cung cấp khả năng kiểm chứng (citation) chính xác.

Concept thứ hai là Grounded Prompting. Thông qua việc build hàm rag_answer(), em hiểu rằng sức mạnh của RAG không nằm ở việc LLM biết nhiều, mà ở việc LLM biết "tuân thủ". Việc thiết kế prompt để ép model chỉ trả lời dựa trên context và biết cách trả lời "Không đủ dữ liệu" (abstain) là kỹ thuật quan trọng nhất để chống lại hiện tượng ảo giác (hallucination) trong các hệ thống hỗ trợ nội bộ.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Điều khiến em ngạc nhiên nhất là độ trễ (latency) và chi phí token khi thực hiện embedding toàn bộ tài liệu policy. Ban đầu, em dự định chunking rất nhỏ để tăng tính chính xác, nhưng thực tế cho thấy số lượng chunk quá lớn khiến việc retrieval chậm lại đáng kể mà không mang lại hiệu quả vượt trội về độ chính xác.

Khó khăn lớn nhất mà em gặp phải là lỗi mismatch giữa chiều vector của model embedding và cấu hình của ChromaDB. Em đã mất khá nhiều thời gian debug trong Sprint 1 khi hệ thống liên tục báo lỗi không tương thích kích thước vector. Sau khi đối chiếu tài liệu, em phát hiện mình đang dùng text-embedding-3-small (1536 dims) nhưng lại cấu hình mặc định khác trong database. Giả thuyết ban đầu của em là lỗi do API key, nhưng thực tế là do cấu hình hạ tầng. Bài học rút ra là luôn phải kiểm tra tính đồng nhất của model định dạng dữ liệu ngay từ bước đầu tiên.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

Câu hỏi: q03 (Về SLA xử lý ticket P1)

Phân tích:

Baseline: Hệ thống trả lời đúng thời gian xử lý là 2 giờ nhưng thiếu thông tin về các điều kiện đi kèm (như giờ làm việc hành chính). Điểm Completeness chỉ đạt mức trung bình.

Lỗi nằm ở đâu: Lỗi nằm ở giai đoạn Indexing. Do em set chunk_size ở baseline hơi nhỏ, thông tin về SLA bị chia tách khỏi phần "Lưu ý chung" ở đầu tài liệu sla_p1_2026.txt. Khi retrieval, hệ thống lấy được chunk chứa con số "2 giờ" nhưng bỏ lỡ chunk chứa thông tin "chỉ áp dụng trong giờ hành chính".

Cải thiện: Ở variant sau đó (phối hợp cùng Retrieval Owner), chúng em đã tăng chunk_overlap và bổ sung metadata parent_section. Kết quả là model lấy được ngữ cảnh bao quát hơn.

Kết luận: Qua câu q03, em nhận thấy đối với các tài liệu quy định (policy), việc giữ được tính toàn vẹn của thông tin quan trọng hơn là việc chia nhỏ văn bản quá mức. Nếu retrieval stage không lấy đủ các ràng buộc pháp lý, generation stage dù tốt đến đâu cũng sẽ sinh ra câu trả lời gây hiểu lầm cho người dùng.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, em sẽ tập trung vào việc tối ưu Metadata Filtering. Hiện tại hệ thống đang tìm kiếm trên toàn bộ database, điều này gây lãng phí tài nguyên. Em muốn thử nghiệm việc phân loại câu hỏi (Query Classification) trước khi retrieve: nếu câu hỏi thuộc về "IT Helpdesk", hệ thống sẽ chỉ search trong các chunk có metadata source=it_helpdesk_faq.txt. Điều này chắc chắn sẽ tăng cả độ chính xác (Precision) lẫn tốc độ phản hồi của pipeline.
