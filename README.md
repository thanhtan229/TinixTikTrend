# TikTok Shop Affiliate Trend Hunter

Ứng dụng cục bộ (local-first) giúp phát hiện và xếp hạng các sản phẩm tiềm năng trên TikTok Shop cho Affiliate Marketing, tối ưu chi phí 0đ, tập trung vào tín hiệu sản phẩm tăng trưởng nhanh (Rising, Velocity, Acceleration, New, Best Sellers).

---

## 🛠️ Yêu cầu Hệ thống
- Hệ điều hành: Windows 10/11
- Python 3.11+
- Node.js 20.19+ & npm (runtime hiện tại dùng Next.js 15.5.27)

---

## ⚡ Khởi chạy Nhanh 1-Click (Khuyên dùng trên Windows)

Chỉ cần click đúp vào các file script tại thư mục gốc:
- **`start.bat`**: Khởi chạy Backend & Frontend bằng cửa sổ ẩn, kiểm tra Health Check và mở Dashboard tại `http://127.0.0.1:3000`. Chỉ dừng tiến trình có bằng chứng thuộc project; nếu port bị ứng dụng khác chiếm, script báo lỗi và giữ nguyên ứng dụng đó.
- **`RESTART.bat`**: Khởi động lại nhanh cho quá trình Development (chuẩn hóa theo [`DEVELOPMENT_WORKFLOW.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/DEVELOPMENT_WORKFLOW.md)): Dừng an toàn các process cũ, giải phóng port, khởi động lại backend & frontend, kiểm tra Health Check thực tế (không spam mở thêm tab trình duyệt mới). Hỗ trợ tùy chọn: `RESTART.bat frontend` (chỉ restart UI) hoặc `RESTART.bat backend` (chỉ restart API).
- **`stop.bat`**: Dừng đúng dịch vụ thuộc project và các tiến trình con. Hỗ trợ: `stop.bat frontend`, `stop.bat backend`.
- **`healthcheck.bat`**: Kiểm tra tức thì trạng thái hoạt động (Health status) của Backend API và Frontend UI. Hỗ trợ: `healthcheck.bat frontend`, `healthcheck.bat backend`.
- **`logs/services.log`**: Nhật ký chi tiết tiến trình khởi động, PID và kết quả health check.

---

## 🚀 Hướng dẫn Cài đặt Thủ công (Manual Setup)

```powershell
# Chuyển vào thư mục backend
cd backend

# Tạo môi trường ảo Python
python -m venv .venv

# Kích hoạt môi trường ảo (PowerShell)
.venv\Scripts\Activate.ps1
# Hoặc Command Prompt:
# .venv\Scripts\activate.bat

# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

# Cài đặt trình duyệt cho Playwright
playwright install chromium

# Khởi chạy server FastAPI
uvicorn app.main:app --host 127.0.0.1 --reload --port 8000
```

Backend API sẽ chạy tại: `http://localhost:8000`
Tài liệu Swagger UI: `http://localhost:8000/docs`

---

### 2. Cài đặt & Khởi chạy Frontend

```powershell
# Mở một cửa sổ terminal mới và chuyển vào thư mục frontend
cd frontend

# Cài đặt dependencies
npm install

# Khởi chạy Next.js development server
npm run dev
```

Dashboard giao diện người dùng sẽ chạy tại: `http://localhost:3000`

---

## 🧪 Chạy Kiểm thử (Tests)

```powershell
cd backend
.venv\Scripts\Activate.ps1
pytest
```

---

## 📂 Cấu trúc Dự án

```text
tiktok-affiliate-trend-hunter/
├── backend/
│   ├── app/
│   │   ├── api/            # API Endpoints (Health, Products, Trends, Dashboard, Crawler)
│   │   ├── collectors/     # TikTok Shop Collectors (HTTP-first & Playwright fallback)
│   │   ├── models/         # SQLAlchemy Models (Product, Snapshot, CrawlRun, Category)
│   │   ├── services/       # Business & Data Services
│   │   ├── analytics/      # Deltas, Velocity, Scoring & Normalization
│   │   ├── scheduler/      # APScheduler jobs
│   │   ├── db/             # DB Base & Session management
│   │   ├── core/           # Config, Logging, Exceptions
│   │   └── main.py         # FastAPI App Entrypoint
│   ├── tests/              # Pytest Unit & Integration Tests
│   └── requirements.txt
├── frontend/               # Next.js TypeScript Dashboard UI
├── docs/                   # Architecture & Research Documentation
└── research/               # Reference Repo Analysis
```


## Trạng thái sau production review (03/10/2026)

### Phiên TikTok do người dùng tự đăng nhập

Khi crawler báo `Security Check`, chạy `CONNECT_TIKTOK.bat`, tự đăng nhập/xác minh trong cửa sổ mở ra, sau đó nhập `SAVE` trong terminal để lưu phiên. Enter hủy và giữ nguyên phiên cũ. Quay lại dashboard và quét lại URL sản phẩm; không cần restart server sau mỗi lần lưu phiên vì mỗi collector mới đọc lại state.

Phiên chỉ được lưu cục bộ tại `backend/.local/tiktok-session.json`, đã được Git ignore. File này chứa thông tin đăng nhập: không gửi file vào chat, không commit hoặc chia sẻ. Không đọc profile Chrome/Edge đang có, không tự nhập password/OTP hay tự giải CAPTCHA. Cookie hết hạn và domain không thuộc TikTok bị loại; HTTP giữ domain/path/secure/expiry. Người dùng có thể xóa file trên để ngừng dùng phiên.

Kiểm tra file mà không mở browser: từ thư mục `backend`, chạy `.venv\Scripts\python.exe -m app.connect_tiktok --check`. `LOCAL_SESSION_AVAILABLE` chỉ nói có state hợp lệ, không chứng minh TikTok cho truy cập Shop. Một phiên đã đăng nhập vẫn có thể bị chặn hoặc thiếu sản phẩm ở thị trường hiện tại.

Launcher chuẩn dùng backend không `--reload`, bind `127.0.0.1`; sau sửa source hãy chạy `RESTART.bat backend`. Frontend launcher dùng cache `.next-dev`, tách khỏi `.next` của production build. API `/api/health` trả thêm `revision` để đối chiếu code đã nạp.

Chỉ nhận URL sản phẩm TikTok Shop đầy đủ và dữ liệu cấu trúc có định danh khớp URL. Video feed, trang lỗi, số liệu giả và commission mặc định không được dùng làm sản phẩm. Trường chưa có dữ liệu được giữ là `null`; số 0 đã xác minh vẫn được giữ.

20 bản ghi cũ có định danh `tt_item_` đã được cách ly khỏi API/xếp hạng. Toàn bộ 20 sản phẩm và 50 snapshots vẫn còn trong database. Bản sao trước sửa nằm tại `backups/affiliate-before-production-fixes-20261003-082934.db`.

Đã kiểm chứng thu thập thật với URL `https://shop.tiktok.com/vn/pdp/1737036472084039604` ngày 03/10/2026. Dán URL đầy đủ vào form quét; tham số tracking được bỏ khi chuẩn hóa. Parser đọc khối sản phẩm VN trong `__MODERN_ROUTER_DATA__`, đối chiếu ID, giữ riêng số liệu sản phẩm và shop. Giá là giá hiển thị tại lần chụp, có thể là mức thấp nhất của nhiều phân loại và thay đổi theo ưu đãi/phiên truy cập.

Ba lần quan sát đã lưu thành một sản phẩm và ba snapshots, còn nguyên sau restart. Quét mặc định vẫn cập nhật sản phẩm đang theo dõi khi discovery không tìm được link mới; trạng thái khi đó là `partial`. Discovery trang chủ/danh mục qua HTTP và browser hiện trả Security Check. Điểm xu hướng chỉ được tính/xếp hạng khi có tín hiệu bán hoặc đánh giá theo thời gian; dữ liệu tích lũy ở lần chụp đầu không bị coi là đà tăng. Chi tiết sản phẩm có bộ lọc lịch sử 24h/7d/30d/toàn bộ; cửa sổ thiếu dữ liệu hiển thị trạng thái trống. Các delta 24h/7d hiện vẫn `null`. Chưa xác nhận độ hữu ích Affiliate hoặc nghiệm thu production. Xem `FIX_REPORT.md` và audit gốc `FINAL_REVIEW.md`.

---

## 📊 Xuất Báo cáo CSV, Sao lưu & Phục hồi Cục bộ (Phase 4)

### 1. Xuất Dữ liệu CSV Tương thích Excel (`utf-8-sig`)
- **Xu hướng & Watchlist:** Nhấn nút `[Xuất CSV]` trên thanh công cụ của tab tương ứng để tải tệp CSV phản ánh chính xác kết quả đang truy vấn theo bộ lọc và giới hạn hiển thị hiện tại.
- **Lịch sử Snapshot Sản phẩm:** Tại trang chi tiết sản phẩm, chọn một trong ba khoảng thời gian: `24h`, `7d`, hoặc `30d`, sau đó nhấn `[Xuất CSV]`. Khoảng *"Tất cả"* chỉ dành cho xem biểu đồ trực quan, không hỗ trợ xuất để tránh tràn tài nguyên.
- **Lịch sử Cảnh báo:** Mở Trung tâm Cảnh báo trên thanh tiêu đề và nhấn `[Xuất CSV]` để tải toàn bộ các sự kiện cảnh báo đã phát sinh.
- **Kỹ thuật Keyset Streaming & Đóng băng Dữ liệu:** Tất cả các luồng xuất dữ liệu lịch sử đều đóng băng danh sách tại thời điểm bắt đầu request và phân trang keyset theo từng batch 1000 bản ghi trên session SQLite ngắn hạn. Nhờ đó loại trừ hoàn toàn việc khóa database kéo dài trong lúc tải xuống mạng và loại trừ các bản ghi có ID cao hơn bị ghi lùi thời gian (backdated).

### 2. Tạo Bản Sao lưu Nóng (Operator Hot SQLite Backup với `BACKUP.bat`)
- Chạy entry point dành riêng cho người vận hành tại thư mục gốc dự án:
  ```cmd
  BACKUP.bat
  ```
- Quy trình sao lưu: Sử dụng API `sqlite3.Connection.backup()` chuẩn của Python, thực hiện sao lưu online sang tệp tạm staging, kiểm định toàn diện (SQLite Magic Header, schema bắt buộc suy xuất từ SQLAlchemy model metadata, marker phiên bản tương thích `portable_backup_compatibility_version = "1"`, `PRAGMA integrity_check`, `PRAGMA foreign_key_check`), từ chối ghi đè nếu trùng tên, và đổi tên nguyên tử vào thư mục quản lý:
  ```
  backend/.local/backups/tinix-affiliate-v1-YYYYMMDDTHHMMSS.ffffffZ.sqlite3
  ```
- **Lưu ý bảo mật & phạm vi:** Thông tin phiên đăng nhập TikTok (`backend/.local/tiktok-session.json`) và cookie được cô lập hoàn toàn khỏi tệp sao lưu database. Tính năng tải bản sao lưu qua trình duyệt đã được hoãn lại (deferred) theo quyết định của Project Control để đảm bảo tính an toàn cục bộ.

### 3. Phục hồi Dữ liệu Ngoại tuyến (`RESTORE.bat`)
Nhằm loại trừ triệt để lỗi khóa file của Windows (`WinError 32`), quy trình phục hồi diễn ra ngoại tuyến khi các dịch vụ đã dừng:
- **Phục hồi từ bản sao lưu quản lý:**
  ```cmd
  RESTORE.bat backend\.local\backups\tinix-affiliate-v1-YYYYMMDDTHHMMSS.ffffffZ.sqlite3
  ```
  Quy trình tự động: Kiểm định tập tin ứng viên trước khi dừng dịch vụ $\to$ Khởi tạo manifest giao dịch tại `backend/.local/restore/manifest.json` $\to$ Dừng sạch dịch vụ (giải phóng cổng 8000 và 3000) $\to$ Tạo bản sao lưu an toàn trước phục hồi bằng SQLite backup engine (`tinix-pre-restore-v1-YYYYMMDDTHHMMSS.ffffffZ.sqlite3`) kèm kiểm định toàn vẹn không ghi đè $\to$ Thay thế nguyên tử cơ sở dữ liệu `affiliate.db` $\to$ Khởi động lại dịch vụ $\to$ Chạy migration/reconciliation & catch-up cảnh báo $\to$ Kiểm tra sức khỏe hệ thống (Health Check) $\to$ Tự động rollback nếu khởi động hoặc kiểm tra sức khỏe thất bại.
- **Khắc phục sự cố gián đoạn (Crash Recovery):**
  ```cmd
  RESTORE.bat --recover
  ```
  Nếu có sự cố mất điện hoặc tiến trình bị tắt đột ngột khi đang phục hồi, cờ `--recover` sẽ phân tích manifest giao dịch: nếu gián đoạn trước khi thay thế file DB sẽ hủy về `ABORTED` an toàn; nếu gián đoạn tại/sau khi thay thế file DB sẽ hoàn tất hoặc tự động rollback về bản safety backup đã được kiểm định hợp lệ (`ROLLED_BACK`), giải phóng bộ bảo vệ Pre-Start Manifest Guard.


