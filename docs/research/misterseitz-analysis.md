# Phân tích Kỹ thuật Repository Tham chiếu: MisterSeitz/TikTok-Shop-Product-and-Creator-Tracker

## 1. Tổng quan Repository
- **URL**: `https://github.com/MisterSeitz/TikTok-Shop-Product-and-Creator-Tracker`
- **Mục đích**: Thu thập siêu dữ liệu sản phẩm TikTok Shop (giá, giảm giá, tồn kho, người bán, đánh giá, lượt mua, video của nhà sáng tạo liên kết) và phát hiện thay đổi giữa các lần chạy.
- **Entry point**: `main.py`
- **Dependencies chính**: `apify>=1.3.0`, `playwright>=1.40.0`, `httpx>=0.25.0`

---

## 2. Kiến trúc & Vòng đời Playwright
- **Khởi tạo**: Khởi chạy một instance Chromium duy nhất (`playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])`).
- **Context & Session**: 
  - Tạo context theo từng request thông qua `create_context_for_req()`.
  - Sử dụng Mobile User-Agent (`iPhone OS 16_0 Safari/604.1`) hoặc Desktop User-Agent (`Chrome/116.0.0.0`). Mobile UA ít bị chặn và phản hồi DOM gọn gàng hơn.
  - Thiết lập `locale` (hoặc `Accept-Language`) để định hướng vùng địa lý (VD: `vi-VN` cho Việt Nam).
- **Điều hướng & Tải động**:
  - `page.goto(url, wait_until="networkidle", timeout=30000)`
  - Hàm `auto_scroll_page()` thực hiện cuộn trang từng bước (`window.scrollBy(0, 1200)`) để kích hoạt lazy-loading của các sản phẩm và video liên kết.

---

## 3. Cơ chế Khám phá (Discovery) & Thu thập Dữ liệu
- **Khám phá theo danh mục & từ khóa**:
  - Chuyển đổi từ khóa/danh mục sang định dạng slug tag: `https://www.tiktok.com/tag/{slug}` (ví dụ: `fashion-and-accessories`, `suc-khoe-lam-dep`).
  - Phân tích danh sách link `<a>` trên trang để lọc ra các ứng viên sản phẩm có chứa `/product/`, `/item/`, `/shop/`, `/video/`.
- **Cấu trúc dữ liệu thu thập**:
  - Sản phẩm: `product_id`, `title`, `description`, `price` (current, original, currency), `availability`, `rating`, `review_count`, `images`.
  - Shop/Seller: `handle`, `name`, `url`.
  - Video & Creator: `video_url`, `likes`, `comments`, `creator_id`.
  - Biến động: `detected_changes` (giá, tồn kho, `first_seen`).

---

## 4. Nghiên cứu Tối ưu hóa: Giảm tải Playwright (HTTP-First Strategy)
MisterSeitz phụ thuộc hoàn toàn vào việc mở trang Playwright cho mọi URL, dẫn đến:
- Tiêu tốn CPU/RAM cao khi số lượng sản phẩm tăng.
- Thời gian crawl chậm do phải render toàn bộ JavaScript của trình duyệt.

### Giải pháp tối ưu của chúng ta (HTTP-First, Playwright Fallback):
1. **Trích xuất JSON nhúng (SSR Embedded Data)**:
   - Các trang TikTok / TikTok Shop thường chứa dữ liệu sản phẩm trong các thẻ script JSON:
     - `<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">`
     - `<script id="SIGI_STATE" type="application/json">`
     - `<script id="__NEXT_DATA__" type="application/json">`
     - `<script type="application/ld+json">`
   - Ta có thể gửi HTTP GET request bằng `httpx` (mang theo User-Agent và Cookies/Session), lấy chuỗi HTML và phân tích Regex/JSON parser trực tiếp mà không cần mở trình duyệt.
2. **Quy trình phối hợp**:
   ```text
   HTTP Client (httpx)
          │
          ├─► Thành công có JSON/HTML Data? ──► [Parse Trực tiếp] (90% nhẹ hơn)
          │
          └─► Bị chặn / Cần giải mã JS?     ──► [Playwright Fallback]
   ```
3. **Quản lý Session**:
   - Khởi tạo Playwright một lần khi khởi động để lấy Cookie phiên & Header hợp lệ, sau đó cấp phát Cookie này cho `httpx.AsyncClient`.

---

## 5. Bảng Phân loại & Chiến lược Tái sử dụng Linh kiện

| Thành phần | Phân loại | Giải pháp chi tiết trong kiến trúc của chúng ta |
| :--- | :--- | :--- |
| **Mobile User-Agent & VN Locale** | `REUSE CONCEPT` | Áp dụng cấu hình UA Mobile và header `vi-VN,vi;q=0.9,en-US;q=0.8` cho cả HTTP và Playwright. |
| **Category Slug & Tag URL** | `REUSE CONCEPT` | Tái sử dụng logic chuẩn hóa slug danh mục và các pattern URL TikTok Shop VN. |
| **Trích xuất dữ liệu nhúng** | `REUSE CONCEPT` | Trích xuất từ các khối JSON-LD, SIGI_STATE, UNIVERSAL_DATA. |
| **Playwright Browser Manager** | `ADAPT` | Chuyển từ mô hình mở context liên tục sang Singleton Browser Context dùng chung, quản lý vòng đời chặt chẽ. |
| **Auto-scroll & Lazy Load** | `ADAPT` | Tinh chỉnh thời gian chờ linh hoạt và giới hạn số lần cuộn an toàn. |
| **Data Storage & Snapshots** | `REWRITE` | Thay thế hoàn toàn Apify Key-Value Store bằng cơ sở dữ liệu quan hệ cục bộ SQLite + SQLAlchemy (`Product`, `ProductSnapshot`, `CrawlRun`). |
| **Phân tích Xu hướng & Delta** | `REWRITE` | Sử dụng module `app.analytics` nội bộ của chúng ta với thuật toán Trend Score (0-100), Sales Velocity và Sales Acceleration. |
| **Structured Logging** | `REWRITE` | Sử dụng `app.core.logging.log_event` thay cho Apify logger. |
| **Apify SDK / Cloud Actor / Slack** | `IGNORE` | Không sử dụng. Ứng dụng chạy local-first độc lập 100%. |

---

## 6. Kết luận & Định hướng Milestone 4B
- Milestone 4A hoàn tất: Đã làm rõ cơ chế crawl của MisterSeitz, các điểm yếu về hiệu năng và phương án tối ưu hóa HTTP-first.
- Tiếp tục sang **Milestone 4B**: Xây dựng module `collectors/tiktok_shop/` sạch sẽ, độc lập, tuân thủ đúng chuẩn giao diện chuẩn hóa của dự án.
