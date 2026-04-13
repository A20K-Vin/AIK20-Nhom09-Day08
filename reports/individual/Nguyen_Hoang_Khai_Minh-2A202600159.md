# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Hoàng Khải Minh
**Vai trò trong nhóm:** Demo  
**Ngày nộp:** 13/4/2026
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

> Mô tả cụ thể phần bạn đóng góp vào pipeline:
> - Tôi chủ yếu làm sprint 1 và phần demo của  nhóm
> - Implement: index.py, demo/* (toàn bộ file trong demo)
> - File index.py là cơ sở để nhóm làm tiếp đoạn tiếp theo, và code tiếp theo của nhóm là cơ sở để tôi copy ngược lại vào các file trong Demo (để Demo, nếu có thay đổi gì trong code không ảnh hưởng đến luồng chính để chấm điểm)
> - Ở phần demo, tôi làm thêm preprocessing.py để xử lý dữ liệu các file .tex lấy từ arxiv. Ý tưởng chính là thay vì OCR PDF các paper, tôi sử dụng folder latex down được từ trang arxiv, đưa qua file preprocessing.py để tái cấu trúc paper lại thành 1 file text duy nhất. Ở demo này, tạm chấp nhận bỏ qua việc mất thông tin hình ảnh, đồ thị từ paper.

_________________

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Sau lab này, tôi hiểu rõ hơn mối quan hệ giữa indexing và chất lượng trả lời của RAG. Khi làm `index.py`, tôi thấy chỉ cần preprocess lệch format hoặc chunking không đúng ranh giới ý nghĩa thì retriever vẫn trả về “đúng file” nhưng sai đoạn, kéo theo câu trả lời bị thiếu ý hoặc lạc trọng tâm. Tôi cũng hiểu rõ hơn vì sao metadata rất quan trọng: source, section, effective_date không chỉ để hiển thị citation mà còn giúp debug chính xác lỗi nằm ở retrieval hay generation. 

Ngoài ra, khi tự tách và viết toàn bộ luồng trong folder `demo`, tôi hiểu pipeline end-to-end theo thứ tự vận hành thực tế: preprocess -> build index -> retrieve (dense/hybrid) -> grounded prompt -> answer -> đánh giá. Trước đây tôi nghĩ thay retrieval mode là đủ, nhưng sau khi chạy nhiều vòng tôi thấy tính ổn định của dữ liệu index (không lẫn corpus cũ) và cách chọn chunk top-k mới là yếu tố quyết định chất lượng output.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Khó khăn nhất là đoạn preprocessing data LaTex vì có nhiều markdown, kí tự phức tạp cần parsing. Hướng giải quyết ban đầu là parsing hết toàn bộ các file tex để lấy tên file và tên các \input trong file latex đó, ví dụ {"main.tex": ["introduction", "experiment"]} rồi từ đó build lại tree với root là main.tex. Tuy nhiên, sau khi nhờ AI đưa giải pháp tối ưu, AI đề xuất dùng đệ quy và tôi thấy cách đó oke hơn.

_________________

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

**Câu hỏi:** "Mức phạt khi vi phạm SLA P1 là bao nhiêu?" (gq07 trong `grading_questions.json`)

**Phân tích:**

Đây là câu tôi thấy quan trọng vì nó kiểm tra trực tiếp khả năng abstain (không bịa). Trong bộ `grading_questions.json`, expected answer nói rõ là tài liệu hiện có không chứa thông tin mức phạt SLA P1, nên hệ thống phải trả lời thiếu dữ liệu thay vì suy đoán. Đối chiếu với báo cáo nhóm trong `docs/tuning-log.md` và scorecard, pattern lỗi tương tự đã xuất hiện ở câu thiếu ngữ cảnh (q09): baseline có Faithfulness cao nhưng Relevance thấp ở một số vòng vì trả lời chưa đúng intent abstain; khi chuyển variant có rerank, Relevance của q09 tăng từ 1 lên 5 trong khi Faithfulness vẫn giữ 5. 

Từ đó tôi rút ra: lỗi chính không nằm ở generation đơn thuần mà nằm ở retrieval/ranking và rule trả lời khi không có bằng chứng. Nếu hệ thống kéo được chunk “na ná” chủ đề SLA, model rất dễ trả lời hợp lý bề mặt nhưng sai theo tài liệu. Với câu gq07, hướng đúng là ưu tiên cơ chế “evidence-only + abstain” và kiểm tra ngữ cảnh có thật sự chứa facts cần hỏi hay không trước khi generate.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)


Nếu có thời gian, tôi muốn tìm cách để mang cả thông tin hình ảnh vào để LLM có thể dùng được thông tin hình ảnh. Hiện thì tôi cũng chưa có suy nghĩ ra cách giải quyết vì một cái là file txt, một cái dạng ảnh kiểu pdf (mấy hình graph, đồ thị, ...)


_________________

---
