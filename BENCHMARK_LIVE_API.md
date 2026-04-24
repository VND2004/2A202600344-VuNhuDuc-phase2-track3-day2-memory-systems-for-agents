# BENCHMARK LIVE API - Multi-Memory Agent

Chạy benchmark gọi LLM API thật (NVIDIA) trên 10 multi-turn conversations.

| # | Scenario | Turns | Expected key | No-memory result | With-memory result | Prompt chars | Prompt words | Pass? |
|---|----------|------:|--------------|------------------|--------------------|-------------:|-------------:|-------|
| 1 | Profile recall: name after 6 turns | 7 | Linh | Mình không có bộ nhớ dài hạn nên không chắc thông tin trước đó. | Bạn tên là Linh. | 245 | 31 | Pass |
| 2 | Conflict update: allergy overwrite | 5 | đậu nành | Mình không có bộ nhớ dài hạn nên không chắc thông tin trước đó. | Bạn dị ứng đậu nành. | 333 | 53 | Pass |
| 3 | Profile recall: occupation | 4 | backend developer | Mình trả lời theo lượt hiện tại, không giữ được bối cảnh cũ. | Bạn là backend developer. | 458 | 81 | Pass |
| 4 | Episodic recall: completed task | 4 | User update | Mình trả lời theo lượt hiện tại, không giữ được bối cảnh cũ. | Bạn đã hoàn thành việc đặt `DB_HOST` bằng tên service. | 406 | 71 | Fail |
| 5 | Semantic retrieval: docker service name | 4 | service name | Có thể dùng localhost để gọi service khác trong Docker Compose. | **Hướng dẫn nhanh về “docker service name” trong Docker Compose**

1. **Service name là gì?**  
   - Trong file `docker-compose.yml`, mỗi khối `service:` được đặt một tên (ví dụ `web`, `db`, `redis`).  
   - Tên này được dùng làm **hostname** trong mạng (network) mặc định của Compose, cho phép các container liên lạc với nhau.

2. **Cách gọi nhau**  
   - Thay vì dùng `localhost` hay `127.0.0.1`, bạn dùng tên service.  
   - Ví dụ: container `web` muốn kết nối tới database `db` → `DB_HOST=db`.

3. **Mạng (network)**  
   - Compose tự tạo một mạng riêng cho dự án.  
   - Tất cả services trong cùng file `docker-compose.yml` nằm trong mạng này, vì vậy tên service luôn được phân giải thành IP nội bộ.

4. **Ví dụ thực tế**  
   ```yaml
   version: '3.8'
   services:
     web:
       build: .
       ports:
         - "8000:8000"
       environment:
         - DB_HOST=db
     db:
       image: postgres:15
       volumes:
         - db-data:/var/lib/postgresql/data
   networks:
     default:
   volumes:
     db-data:
   ```
   - Ở đây, `web` kết nối tới `db` bằng `DB_HOST=db`.  
   - Không cần `localhost` hoặc IP cố định.

5. **Lưu ý**  
   - Nếu bạn tạo nhiều mạng riêng biệt (`networks:`), chỉ các service trong cùng mạng mới có thể gọi nhau bằng tên.  
   - Khi thay đổi tên service, hãy cập nhật biến môi trường hoặc cấu hình ứng dụng tương ứng.

> **Tóm tắt**: Trong Docker Compose, các container liên lạc với nhau bằng **service name** (được đặt trong `docker-compose.yml`) trong cùng một network; không dùng `localhost`. | 467 | 77 | Pass |
| 6 | Semantic retrieval: conflict handling guideline | 4 | ưu tiên thông tin mới nhất | Mình trả lời theo lượt hiện tại, không giữ được bối cảnh cũ. | Conflict handling cho user profile nên:

1. **Ưu tiên thông tin mới nhất** – khi có dữ liệu trùng lặp, giữ bản ghi có thời gian cập nhật gần nhất.  
2. **Lưu timestamp** – ghi lại thời điểm cập nhật để có thể theo dõi lịch sử và xác định nguồn dữ liệu chính xác.

Như vậy, khi gặp xung đột, chỉ giữ bản ghi có timestamp cao hơn và ghi lại thời gian đó. | 430 | 70 | Pass |
| 7 | Trim budget behavior | 8 | Minh | Mình không có bộ nhớ dài hạn nên không chắc thông tin trước đó. | Bạn tên là Minh.  
Về sở thích, hiện tại tôi không có dữ liệu nào được lưu trữ. | 484 | 70 | Pass |
| 8 | Episodic + semantic mixed query | 4 | retry strategy | Có thể dùng localhost để gọi service khác trong Docker Compose. | Lần trước bạn đã hoàn thành task “retry timeout” và đã ghi nhận thành công.  
FAQ nói rằng khi API timeout, bạn nên lưu lại **episodic memory** về chiến lược retry đã thành công để có thể tái sử dụng lần sau. | 519 | 91 | Fail |
| 9 | Profile preference recall | 4 | clean architecture | Mình trả lời theo lượt hiện tại, không giữ được bối cảnh cũ. | Bạn thích kiến trúc sạch (clean architecture). | 335 | 49 | Pass |
| 10 | Long conversation memory persistence | 9 | cà phê | Mình trả lời theo lượt hiện tại, không giữ được bối cảnh cũ. | Bạn có thể tổng hợp profile chính như sau:

- **Tên:** An  
- **Allergy:** Cà phê  
- **Chức vụ:** Data engineer  

(Chưa có thông tin về sở thích hoặc các chi tiết khác.) | 511 | 69 | Pass |

## Notes
- Kết quả with-memory phụ thuộc vào phản hồi LLM thực tế tại thời điểm chạy.
- Tiêu chí pass dùng so khớp không phân biệt dấu và hoa/thường với expected key.
