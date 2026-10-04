# Agent Guidelines & Development Workflow

> **Source of Truth:**
> - Development Lifecycle & Workflow Rules: [`DEVELOPMENT_WORKFLOW.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/DEVELOPMENT_WORKFLOW.md)
> - UX/UI Design Standards: [`UX_UI.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/UX_UI.md)
> - Product Architecture: [`Project.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/Project.md)

All agents working on this project MUST strictly follow the rules below:

---

## 1. Mặc định là Development Mode (TUYỆT ĐỐI KHÔNG tự động đóng gói `.exe`)
- KHÔNG tự động package `.exe`, installer hay release artifact sau mỗi lần coding.
- CHỈ package `.exe` khi người dùng yêu cầu rõ ràng bằng các từ khóa: `build exe`, `package`, `release`, hoặc yêu cầu test executable.
- Nếu không có yêu cầu cụ thể trên, hãy luôn chạy ứng dụng trực tiếp từ source / development runtime.

---

## 2. Vòng lặp Phát triển Mặc định (Default Development Loop)
Mỗi iteration phải tuân thủ trình tự:
`Understand → Code → Targeted Validation → Build when justified → Restart/Reload → Health Check → Ready for User Test`

- **Build vs Package:** `build` dùng để phát hiện compile/type/bundle errors. `package` là tạo `.exe`. Không đồng nhất 2 khái niệm này.
- **Khi nào Build:** Chỉ build khi thay đổi TypeScript types, dependencies, bundler configs, shared models, API contracts, hoặc native layer. Thay đổi UI/CSS/text nhỏ KHÔNG cần full build.
- **Validation:** Chạy kiểm thử có mục tiêu (pytest cho backend, typecheck/lint/build cho frontend) tùy phạm vi thay đổi.

---

## 3. Quản lý Tiến trình & Khởi động lại (Idempotent Process Management)
- **Không để duplicate instances:** Luôn dừng sạch tiến trình cũ trên Port 8000 và 3000 trước khi restart.
- **Sử dụng script chuẩn:**
  - Khởi động lại dịch vụ: Chạy `RESTART.bat` (mặc định khởi động cả hai, hoặc `RESTART.bat frontend` / `RESTART.bat backend`).
  - Khởi động lần đầu + mở trình duyệt: Chạy `start.bat`.
  - Dừng dịch vụ: Chạy `stop.bat` (hoặc `stop.bat frontend` / `stop.bat backend`).
  - Kiểm tra sức khỏe: Chạy `healthcheck.bat` (hoặc `healthcheck.bat frontend` / `healthcheck.bat backend`).
  - Tra cứu nhật ký khởi chạy: Xem file `logs/services.log`.
- **Không làm phiền desktop người dùng:** Tránh mở nhiều terminal window dư thừa và tránh mở nhiều tab trình duyệt mới sau mỗi lần restart.

---

## 4. Health Check bắt buộc sau Restart
Không được tuyên bố ứng dụng đã sẵn sàng test nếu chưa thực hiện Health Check thực tế:
- **Backend:** `http://127.0.0.1:8000/api/health` phải phản hồi HTTP 200 và JSON có `"status": "ok"`, `"database": "connected"`.
- **Frontend:** `http://127.0.0.1:3000` phải phản hồi HTTP 200.

---

## 5. Báo cáo Bắt buộc cuối mỗi Task Coding (Section 15)
Trước khi kết thúc lượt trao đổi, agent phải cung cấp báo cáo ngắn gọn theo cấu trúc sau:
1. **Thay đổi chính:** Mô tả những gì vừa được thực hiện.
2. **Validation đã chạy:** Danh sách test, typecheck hoặc compile đã thực hiện.
3. **Có build hay không:** Có chạy build hay chỉ reload/restart.
4. **Frontend đã restart/reload hay chưa:** Trạng thái frontend runtime.
5. **Backend có restart hay không:** Trạng thái backend runtime.
6. **Health/Status hiện tại:** Kết quả health check thực tế (Backend, Frontend).
7. **Blocker nếu còn:** Bất kỳ vấn đề hoặc lỗi nào cần lưu ý (nếu có).
