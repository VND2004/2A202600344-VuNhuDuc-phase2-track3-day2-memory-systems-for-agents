# Reflection - Privacy and Limitations

## 1) Memory nào giúp agent nhiều nhất?
Semantic memory giúp nhiều nhất trong bài này vì nó bổ sung tri thức FAQ/nguyên tắc ngoài hội thoại hiện tại, đặc biệt ở các câu hỏi Docker và conflict handling.

## 2) Memory nào nhạy cảm/rủi ro nhất nếu retrieve sai?
Long-term profile là nhạy cảm nhất vì chứa thông tin cá nhân (tên, dị ứng, preference, nghề nghiệp). Nếu retrieve sai hoặc stale, agent có thể đưa ra khuyến nghị nguy hiểm (ví dụ allergy sai).

## 3) Nếu user yêu cầu xóa memory thì xóa ở đâu?
Cần xóa đồng thời ở tất cả backend:
- data/profile_store.json: xóa user profile.
- data/episodes.json: xóa toàn bộ episodes của user.
- short-term memory trong RAM: clear history theo user.
- semantic memory: trong solution này semantic là corpora chung, không lưu cá nhân; nếu có embedding cá nhân thì cần xóa vector/chunk theo user id.

## 4) Consent, TTL, deletion policy
- Consent: chỉ lưu profile khi user cung cấp rõ ràng thông tin.
- TTL: episode cũ nên có hạn sử dụng để tránh tích lũy quá mức.
- Deletion: cần endpoint/command xóa memory theo user id và kiểm tra đã xóa ở mỗi backend.

## 5) Limitation kỹ thuật hiện tại
- Semantic retrieval đang keyword-based fallback, chưa dùng embedding search thật sự.
- Conflict handling profile đang overwrite theo key, chưa có confidence score.
- Token budget trim đang dựa trên số ký tự, chưa dùng tokenizer thật sự.
- Chưa có cơ chế phân quyền và mã hóa dữ liệu profile tại backend.
- Chưa test tại quy mô lớn (nhiều user đồng thời, kho dữ liệu lớn).
