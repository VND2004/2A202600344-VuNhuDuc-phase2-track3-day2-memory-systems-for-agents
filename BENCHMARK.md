# BENCHMARK - Multi-Memory Agent

So sánh no-memory vs with-memory trên 10 multi-turn conversations.
Token budget ước lượng bằng số ký tự và số từ trong prompt đã assemble.

| # | Scenario | Turns | No-memory result | With-memory result | Prompt chars | Prompt words | Pass? |
|---|----------|------:|------------------|--------------------|-------------:|-------------:|-------|
| 1 | Profile recall: name after 6 turns | 7 | Mình không có bộ nhớ dài hạn nên không chắc thông tin trước đó. | Bạn tên là Linh. | 414 | 65 | Pass |
| 2 | Conflict update: allergy overwrite | 5 | Mình không có bộ nhớ dài hạn nên không chắc thông tin trước đó. | Thông tin hiện tại: bạn dị ứng đậu nành. | 508 | 90 | Pass |
| 3 | Profile recall: occupation | 4 | Mình trả lời theo lượt hiện tại, không giữ được bối cảnh cũ. | Bạn làm backend developer. | 490 | 78 | Pass |
| 4 | Episodic recall: completed task | 4 | Mình trả lời theo lượt hiện tại, không giữ được bối cảnh cũ. | Lần trước bạn đã ghi nhận: User update: Tôi đã đặt DB_HOST bằng tên service (kết quả: Task marked as completed by user). | 406 | 71 | Pass |
| 5 | Semantic retrieval: docker service name | 4 | Có thể dùng localhost để gọi service khác trong Docker Compose. | Gợi ý từ semantic memory: Trong Docker Compose, các service gọi nhau bằng service name trong cùng network, không dùng localhost. | 467 | 77 | Pass |
| 6 | Semantic retrieval: conflict handling guideline | 4 | Mình trả lời theo lượt hiện tại, không giữ được bối cảnh cũ. | Thông tin semantic liên quan: Conflict handling cho user profile nên ưu tiên thông tin mới nhất và lưu timestamp cập nhật. | 430 | 70 | Pass |
| 7 | Trim budget behavior | 8 | Mình không có bộ nhớ dài hạn nên không chắc thông tin trước đó. | Bạn tên là Minh. | 484 | 70 | Pass |
| 8 | Episodic + semantic mixed query | 4 | Có thể dùng localhost để gọi service khác trong Docker Compose. | Lần trước: User update: Tôi đã hoàn thành task retry timeout xong / FAQ: Khi API timeout, cần lưu episodic memory về retry strategy đã thành công để dùng lại lần sau. | 519 | 91 | Pass |
| 9 | Profile preference recall | 4 | Mình trả lời theo lượt hiện tại, không giữ được bối cảnh cũ. | Preference của bạn là clean architecture. | 458 | 75 | Pass |
| 10 | Long conversation memory persistence | 9 | Mình trả lời theo lượt hiện tại, không giữ được bối cảnh cũ. | Profile hiện tại: name=An, allergy=cà phê, occupation=data engineer, preference=chưa rõ. | 511 | 69 | Pass |

## Coverage
- Profile recall: scenarios 1, 3, 9, 10
- Conflict update: scenario 2
- Episodic recall: scenarios 4, 8
- Semantic retrieval: scenarios 5, 6, 8
- Trim/token budget: scenario 7 (và cột prompt chars/words toàn bộ bảng)

## Notes
- No-memory mode có chủ đích không giữ profile/episodic/semantic context.
- With-memory mode inject 4 memory sections vào prompt assembled.
