# Current architecture

Updated: 2026-10-06.

Next.js 15 / React 18 dashboard on 127.0.0.1:3000 calls FastAPI on 127.0.0.1:8000. SQLAlchemy stores products, snapshots, crawl runs, categories and additive quarantine records in local SQLite. APScheduler triggers collection at configured Vietnam local times.

The crawl service reserves one active run before enqueueing work. Each cycle discovers candidates and refreshes up to 100 oldest tracked verified products. Canonical numeric product identity deduplicates candidates and snapshots. Each product transaction commits its snapshot and counters together; failures roll back that item. Startup reconciles orphan running runs. Empty or entirely failed runs are failed; mixed results are partial.

The collector uses HTTP first and lazily starts Playwright. Product URLs are restricted to supported TikTok HTTPS product paths. HTTP redirects and browser requests are checked for public destinations; private network targets are rejected. Structured product identity must match the requested URL. Missing metrics remain null. Generic page titles and feed videos cannot become products.

Analytics uses UTC observations, bounded tolerances around requested time windows, actual elapsed time for velocity and distinct comparable intervals for acceleration. Observations older than eight hours cannot contribute current rising scores. Quarantined history is preserved but excluded from product APIs and rankings.

Frontend fetches guard against stale responses, expose failures with retry and refresh once when a crawl finishes. SQLite naive UTC values are serialized with timezone information. Charts retain missing values instead of inventing zero.

Standard Windows scripts verify command/executable ownership and listener ancestry before stopping process trees. Unowned port conflicts abort startup. Hidden source runtimes use separate .next-dev cache; builds use .next. Backend health exposes a source revision calculated at import. This is a local development runtime, not a packaged or remotely deployed service.


## Phiên truy cập cục bộ (03/10/2026)

`CONNECT_TIKTOK.bat` mở công cụ để người dùng tự đăng nhập, chỉ lưu khi người dùng nhập SAVE. Không đọc profile trình duyệt hiện có và không tự xử lý password/OTP/CAPTCHA. State tại backend/.local/tiktok-session.json được Git ignore, lọc domain TikTok, loại cookie hết hạn và ghi qua temporary file rồi replace. HTTP giữ domain/path/secure/expiry; Playwright nạp storage_state. Context không được coi là authenticated chỉ vì có file.

API crawler/status chỉ trả local_session_status = missing/available/invalid; không trả cookie hoặc localStorage. Collector mới đọc lại file mỗi run; state lỗi được báo rõ và không in JSON gốc ra UI/log. Khi đã có state và HTTP vẫn trả Security Check, có thể thử navigation bình thường trong context đã nạp state; nếu browser vẫn gặp challenge, run thất bại và không ghi snapshot. Không tự vượt challenge.

## Nguyên tắc Phân tích & Chất lượng Xu hướng (Phase 2 - 05/10/2026)

1. **Tách biệt Sức mạnh Xu hướng và Độ tin cậy Bằng chứng:** `trend_score` và `trend_evidence` là hai khái niệm trực giao. Độ tin cậy (low / medium / high) mô tả mức độ đầy đủ của dữ liệu thu thập, không nhân trực tiếp làm giảm hoặc méo mó công thức điểm số toán học.
2. **Điều kiện Xếp hạng Xu hướng:** Chỉ xếp hạng xu hướng cho các sản phẩm có dữ liệu mới (thời gian quan sát cuối <= 8h) và có tín hiệu đo lường thực tế (tốc độ bán, gia tốc hoặc đánh giá ~24h). Dữ liệu chỉ có khoảng ước tính không được tự động tạo tư cách hợp lệ (eligible).
3. **Bảo toàn Giá trị Thiếu (Null Preservation):** Các chỉ số thiếu tiếp tục giữ nguyên là `null`, tuyệt đối không giả định hay gán bằng `0` để chấm điểm hoặc giải thích.
4. **Giải thích Xu hướng Tất định ("Why trending?"):** Lý do xu hướng được tính toán tất định dựa trên mã cấu trúc backend từ chính các thành phần động lực đóng góp vào điểm số; không dùng văn bản suy diễn từ LLM.
5. **Phạm vi Xếp hạng:** Xếp hạng xu hướng áp dụng trên tập sản phẩm được người dùng theo dõi và hợp lệ (eligible tracked-product universe); không tuyên bố là xếp hạng toàn thị trường TikTok Shop.
6. **Lọc Danh mục và Chuẩn hóa:** Việc lọc theo danh mục cho phép người dùng quan sát trong từng ngành hàng mà không ngộ nhận sự tồn tại của phân vị chuẩn hóa theo danh mục (category-relative percentile).
7. **Bảo vệ Hiệu năng & Không N+1 Queries:** Truy vấn dữ liệu xu hướng nạp toàn bộ snapshot liên quan trong duy nhất một câu lệnh SQL (`joinedload(Product.snapshots)`) kết hợp chỉ mục phức hợp `ix_product_snapshots_product_captured (product_id, captured_at)` và loại trừ sản phẩm cách ly tại tầng database, bảo đảm thời gian phản hồi API luôn dưới 200ms mà không gây N+1 queries.

## Giám sát, Watchlist & Cảnh báo (Phase 3 - 05/10/2026 - ADR-003)

1. **Watchlist là nguồn quét định kỳ:** Tập sản phẩm trong bảng `watchlist_items` là nguồn cung cấp danh sách cho scheduler quét định kỳ (scheduled refresh). Sản phẩm PDP hợp lệ do người dùng nộp trực tiếp tự động được thêm vào Watchlist. Hủy theo dõi (Unwatch) chỉ xóa quyền thành viên nhưng bảo toàn toàn bộ dữ liệu lịch sử Product, Snapshot, Rule và AlertEvent.
2. **Migration một lần với Durable Marker:** Quá trình di chuyển tập sản phẩm legacy sang Watchlist chỉ chạy một lần duy nhất nhờ marker `legacy_tracked_backfill_completed` trong bảng `system_metadata`. Một Watchlist cố ý để trống hoặc do người dùng dọn sạch tuyệt đối không bị tự động nạp lại ở các lần khởi động sau.
3. **Phân tách Giao dịch Thu thập và Cảnh báo:** Snapshot được commit hoàn tất trong giao dịch thu thập trước khi bộ đánh giá cảnh báo được kích hoạt. Bộ đánh giá thực thi trong giao dịch cơ sở dữ liệu riêng biệt; lỗi cảnh báo không bao giờ rollback dữ liệu thu thập.
4. **Đánh giá Ít nhất Một lần, Hiệu ứng Đúng Một lần (At-least-once with exactly-once effect):** Con trỏ `last_evaluated_snapshot_id` kiểm soát các snapshot chưa đánh giá. Ràng buộc duy nhất `UNIQUE(rule_id, triggering_snapshot_id)` tại database bảo đảm không bao giờ phát sinh sự kiện trùng lặp khi chạy lại hay phục hồi sau sự cố.
5. **Tiến trình Nguyên tử (Atomic Advancement):** Việc tạo bản ghi `AlertEvent`, cập nhật `last_condition_met`, ghi nhận `last_triggered_at` và thăng cấp con trỏ `last_evaluated_snapshot_id` diễn ra trong một commit duy nhất, đảm bảo tính nhất quán tuyệt đối.
6. **Thứ tự Khởi động Đồng bộ:** Thứ tự lifecycle bắt buộc: `schema/bootstrap/backfill` → `crawl reconciliation` → `alert catch-up` → `scheduler start` → `application ready`. Nếu catch-up thất bại, hệ thống ngăn chặn khởi động scheduler để không tạo ra lỗ hổng replay dữ liệu.
7. **Tái sử dụng Phân tích Tất định theo Thời điểm (Deterministic As-of Analytics):** Khi replay đánh giá cảnh báo, toàn bộ chỉ số động lực Phase 2 được tính toán tất định theo mốc thời gian `captured_at` của snapshot kích hoạt, giới hạn trong cửa sổ 172h và loại trừ toàn bộ snapshot tương lai. Phân tích chỉ tính một lần cho mỗi cặp (sản phẩm, snapshot) và chia sẻ cho tất cả luật của sản phẩm đó, loại bỏ N+1 queries.
8. **Ngữ nghĩa Luật Giá & Giãn cách (Cooldown):** Luật giá bắt buộc có `direction ∈ {'up', 'down', 'either'}` và `threshold > 0`, tính trên giá hợp lệ > 0, phát sinh sự kiện lưu rõ `actual_direction`, và không bao giờ được mô tả là "trending". Cooldown mặc định 0 phút, chỉ triệt tiêu khi `trigger_time - last_triggered_at < cooldown_duration`; chạm mốc biên vẫn hợp lệ để kích hoạt; việc hết hạn cooldown đơn thuần không bao giờ tự động tạo sự kiện trễ. Không tạo cảnh báo hồi tố cho dữ liệu quá khứ khi tạo mới hoặc sửa luật.
9. **Không Queue / Không Broker Ngoại vi:** Ứng dụng desktop cục bộ tuyệt đối không sử dụng Redis, Celery, hàng đợi bên ngoài hay scheduler thứ hai. Toàn bộ tính bền vững dựa trên SQLite.

## Báo cáo, Sao lưu & Phục hồi Cục bộ (Phase 4 - 05/10/2026 - ADR-004)

1. **Ranh giới Dữ liệu Khả chuyển (Portable State Boundary):** Ranh giới sao lưu khả chuyển được giới hạn tuyệt đối trong tập tin `backend/affiliate.db` bao gồm các bảng ứng dụng authoritative được mô hình hóa qua SQLAlchemy `Base.metadata` (`products`, `product_snapshots`, `crawl_runs`, `categories`, `product_video_links`, `quarantined_products`, `watchlist_items`, `system_metadata`, `alert_rules`, `alert_events`). Phiên đăng nhập TikTok (`backend/.local/tiktok-session.json`), cookie, localStorage và các bí mật máy trạm được cô lập tuyệt đối khỏi các kho lưu trữ sao lưu khả chuyển.
2. **Đóng băng Thành viên Xuất CSV & Keyset Streaming:** 
   - Xuất lịch sử snapshot sản phẩm (`/api/products/{id}/export-history`) đóng băng tập dữ liệu ngay đầu request qua mốc `as_of_utc`, mốc thời gian dưới suy dẫn, và con trỏ bất biến `max_snapshot_id_at_start`. Keyset truy vấn tăng dần `(captured_at, snapshot_id) ASC`.
   - Xuất lịch sử cảnh báo (`/api/alerts/events/export`) đóng băng tập dữ liệu qua `max_event_id_at_start` và keyset giảm dần `(created_at, event_id) DESC`.
   - Mọi bản ghi có ID lớn hơn mốc bắt đầu đều bị loại trừ tuyệt đối kể cả khi timestamp bị ghi lùi về quá khứ (backdated).
   - Generator truyền dữ liệu (streaming) sử dụng database session ngắn hạn cho từng batch (1000 bản ghi) và đóng session ngay sau khi đọc, tuyệt đối không duy trì transaction/session đọc kéo dài qua toàn bộ luồng truyền tải mạng, loại bỏ hiện tượng tranh chấp khóa ghi của crawler chạy nền.
   - Toàn bộ luồng CSV được gắn tiền tố UTF-8 BOM (`\ufeff`) bảo đảm hiển thị tiếng Việt hoàn hảo trên Microsoft Excel (Windows).
   - Xuất lịch sử sản phẩm chỉ hỗ trợ `24h`, `7d`, `30d`; phạm vi `all` (`Tất cả`) chỉ hiển thị trên giao diện và trả về HTTP 400 nếu yêu cầu xuất.
   - Xuất Xu hướng và Watchlist tái sử dụng trực tiếp nghiệp vụ của `TrendService` và `WatchlistService`, xuất chính xác tập kết quả đang hiển thị theo bộ lọc và phân trang hiện tại; không thêm truy vấn metadata riêng cho từng dòng.
3. **Động cơ Sao lưu Nóng của Operator (Operator Hot SQLite Online Backup):** Tạo bản sao lưu nhất quán tại thời điểm thông qua entry point `BACKUP.bat` sử dụng `sqlite3.Connection.backup()` vào thư mục quản lý runtime `backend/.local/backups/tinix-affiliate-v1-YYYYMMDDTHHMMSS.ffffffZ.sqlite3`. Tính năng tải sao lưu qua trình duyệt được hoãn lại. Tập tin sao lưu chỉ được xuất bản sau khi vượt qua kiểm định tiền phát hành trên file staging: kiểm tra header SQLite, schema cấu trúc suy xuất động từ SQLAlchemy model metadata, marker phiên bản tương thích `portable_backup_compatibility_version = "1"`, `PRAGMA integrity_check` và `PRAGMA foreign_key_check`. Ngăn chặn ghi đè tập tin ngoài ý muốn.
4. **Quy trình Phục hồi Ngoại tuyến Dưới quyền Launcher (Offline Launcher-Owned Restore):**
   - Loại trừ triệt để lỗi khóa file Windows (`WinError 32`) bằng quy trình phục hồi ngoại tuyến khi ứng dụng đã dừng sạch qua `RESTORE.bat` / `scripts/restore.ps1`.
   - Kiểm định toàn diện tập tin ứng viên (Candidate Validation) trước khi dừng dịch vụ.
   - Tạo bản sao lưu an toàn tự động của cơ sở dữ liệu hiện tại bằng SQLite backup engine kèm kiểm định toàn vẹn trước khi cho phép thay thế (`backend/.local/backups/tinix-pre-restore-v1-YYYYMMDDTHHMMSS.ffffffZ.sqlite3`). Tuyệt đối không xóa hay ghi đè bản sao lưu an toàn hiện có.
   - Theo dõi trạng thái phục hồi qua Manifest giao dịch đặt tại vị trí bền vững `backend/.local/restore/manifest.json` với ba trạng thái kết thúc duy nhất: `COMPLETED`, `ROLLED_BACK`, `ABORTED`.
   - Bộ bảo vệ Pre-Start Manifest Guard trong `scripts/start_services.ps1` và `RESTART.bat` chặn đứng khởi động thông thường nếu manifest chưa kết thúc.
   - Chế độ phục hồi (`RESTORE.bat --recover`) khôi phục an toàn các lần phục hồi bị gián đoạn: sự cố trước khi thay thế chuyển về `ABORTED`, sự cố từ khi thay thế trở đi khôi phục về trạng thái an toàn `COMPLETED` hoặc `ROLLED_BACK`.
   - Khởi động lại chạy đầy đủ reconciliation, `AlertService.catch_up_alerts()` và kiểm tra sức khỏe hệ thống.
5. **Thực thi Khóa Ngoại là Nợ Kỹ thuật Không Chặn (Non-Blocking FK Technical Debt):** Kết nối runtime ứng dụng tiếp tục giữ nguyên mặc định SQLite (`PRAGMA foreign_keys = 0`) để tránh rủi ro hồi quy ngoài phạm vi Phase 4. Mọi quy trình kiểm định sao lưu, ứng viên phục hồi và chẩn đoán chuyên sâu đều bắt buộc thực thi `PRAGMA foreign_key_check`.
6. **Chẩn đoán Hệ thống Cục bộ An toàn (Safe Local System Diagnostics):** Cung cấp API `/api/diagnostics` trả về dung lượng cơ sở dữ liệu, số lượng dòng các bảng, trạng thái scheduler, và trạng thái phiên TikTok dạng enum (`available` / `missing` / `invalid`). Tuyệt đối che giấu, không lộ cookie, token, header xác thực hay danh sách file tùy ý. Kiểm tra toàn vẹn chuyên sâu (`/api/diagnostics/deep`) chỉ chạy khi người dùng chủ động kích hoạt.

## Không gian Cơ hội: Bộ sưu tập, Chế độ xem đã lưu & So sánh Sản phẩm (Phase 5 - 06/10/2026)

1. **Phân tách Tuyệt đối giữa Giám sát và Tổ chức Quyết định (`Watchlist` vs `Collections`):**
   - `WatchlistItem` tiếp tục giữ vai trò duy nhất quản lý việc quét định kỳ (scheduled refresh).
   - `Collections` và `CollectionItems` thuần túy phục vụ tổ chức và đánh giá cơ hội kinh doanh (decision organization).
   - Thêm sản phẩm vào Bộ sưu tập tuyệt đối không tự động kích hoạt theo dõi (Watch) hay tạo `WatchlistItem`.
   - Hủy theo dõi (Unwatch) một sản phẩm tuyệt đối không ảnh hưởng, không xóa sản phẩm khỏi Bộ sưu tập, và không làm mất trạng thái hay ghi chú quyết định (`CollectionItem.status`, `CollectionItem.notes`).
   - `WatchlistItem.notes` tiếp tục là trường nội bộ phục vụ nguồn gốc theo dõi; ghi chú quyết định của người dùng chỉ lưu tại `CollectionItem.notes`.
   - Các thao tác trên Bộ sưu tập không gây ra bất kỳ tác dụng phụ nào tới crawler, scheduler hay tập luật cảnh báo.
2. **Khởi tạo Schema Tăng cường & Kiểm định Động (Additive Bootstrap & Dynamic Required Schema Validation):**
   - Không áp dụng Alembic cho Phase 5. Khởi tạo schema additive bằng `Base.metadata.create_all()`, tạo chính xác 3 bảng mới: `collections`, `collection_items`, `saved_views`.
   - Ràng buộc thành viên bắt buộc: `UNIQUE(collection_id, product_id)` và chỉ mục đảo `collection_items(product_id)`.
   - Kiểm định schema động suy xuất từ chính model metadata của SQLAlchemy (`inspect(db.connection())`) trước khi nâng cấp giá trị marker khả chuyển `portable_backup_compatibility_version` từ `"1"` lên `"2"` trong `system_metadata`.
   - Ứng dụng chỉ sẵn sàng (application ready) sau khi toàn bộ schema bắt buộc và marker `"2"` được xác nhận hợp lệ.
3. **Chế độ xem đã lưu Kiểu tĩnh V1 (Strictly Typed V1 Saved Views):**
   - Phân định phạm vi rõ ràng: `trends` (đúng 9 tham số: `category`, `trend_state`, `measured_only`, `confidence`, `sort_by`, `sort_direction`, `limit`, `search`, `min_score`) và `watchlist` (đúng 7 tham số: `category`, `trend_state`, `measured_only`, `confidence`, `sort_by`, `sort_direction`, `limit`).
   - Không hỗ trợ đồng bộ trạng thái qua query params trên URL; quản lý hoàn toàn qua component-local state.
   - Khi áp dụng một chế độ xem đã lưu vào Watchlist, tham số `skip` luôn được reset về `0`.
   - Việc áp dụng một chế độ xem đã nạp trong bộ nhớ tạo ra đúng `0` câu lệnh SQL truy vấn `SavedView` phụ trợ.
4. **So sánh Sản phẩm Phi trạng thái & Gộp Truy vấn (Stateless Single-Request Product Compare):**
   - Khay so sánh lưu trữ tạm thời trong bộ nhớ frontend (transient memory); tuyệt đối không lưu vào Database, `localStorage`, hay URL search params.
   - Cho phép so sánh từ 2 đến tối đa 5 sản phẩm; giữ nguyên thứ tự yêu cầu; từ chối so sánh nếu có sản phẩm cách ly hoặc không tồn tại.
   - Ghi nhận duy nhất một mốc thời gian UTC có múi giờ (`as_of_utc`) tại thời điểm bắt đầu xử lý request và dùng chung mốc này cho toàn bộ sản phẩm so sánh (`current_time = as_of_utc`).
   - Tóm tắt cảnh báo 7 ngày thực hiện gộp trong 1 câu truy vấn với cửa sổ chặt chẽ: `as_of_utc - 7 days <= created_at <= as_of_utc`.
   - Không sáng tạo điểm số so sánh tổng hợp, không xếp hạng "người chiến thắng", không đưa ra khuyến nghị tự động. Bảo toàn tuyệt đối ngữ nghĩa bằng chứng và giá trị `null`.
5. **Ngân sách Truy vấn Hiệu năng Chặt chẽ (Strict Query Budgets):**
   - Lấy danh sách thành viên Bộ sưu tập: tối đa `<= 2` câu lệnh SQL (Zero N+1).
   - So sánh 2–5 sản phẩm: tối đa `<= 3` câu lệnh SQL (Zero N+1) trên duy nhất 1 HTTP request. Thời gian phản hồi thực tế đạt dưới 10ms (vượt xa ngưỡng cứng `< 200ms` và mục tiêu nghiên cứu `< 50ms`).
6. **Ranh giới Phiên bản Sao lưu Khả chuyển "2" (ADR-004 Evolution):**
   - Nâng cấp marker khả chuyển lên `"2"`. Giữ nguyên nguyên tắc kiểm định nghiêm ngặt cùng phiên bản: ứng dụng Phase 5 từ chối phục hồi các bản sao lưu phiên bản 1 (HTTP 400) trước khi thực hiện bất kỳ thao tác xóa/ghi đè nào.
   - Sao lưu phiên bản 2 bảo toàn toàn bộ dữ liệu Phase 1–5 (`collections`, `collection_items`, `saved_views` cùng toàn bộ bảng cũ).
   - Phiên đăng nhập TikTok tiếp tục được loại trừ hoàn toàn khỏi tệp sao lưu.

## Kinh tế Tiếp thị Liên kết & Kịch bản Quyết định (Phase 6 - 07/10/2026 - ADR-005)

> **Trạng thái:** Đã triển khai hoàn tất theo [`ADR-005`](docs/architecture/ADR-005.md) và [`PHASE_6_PLAN.md`](PHASE_6_PLAN.md). Sản phẩm hiện hành vận hành tại Phase 6 với phiên bản tương thích sao lưu khả chuyển `"3"`.

1. **Phân tách Miền Độc lập (Domain Separation):**
   - Kinh tế tiếp thị liên kết (Affiliate Economics) phân tách tuyệt đối khỏi Trend Score, tín hiệu bằng chứng (evidence) và độ tin cậy (confidence) của Phase 2.
   - Dữ liệu và giả định kinh tế không bao giờ làm méo mó, thay đổi hay nhân vào điểm số xu hướng thị trường. Tuyệt đối không tạo điểm số lai (blended trend-profit score).
2. **Không Suy diễn Phân bổ Doanh số Thị trường (No Market-Sales Attribution):**
   - Số lượng bán tích lũy (`Product.sold_count`) và tốc độ bán 24h (`sales_velocity_24h`) là quan sát khách quan về thị trường chung, không phản ánh doanh số của affiliate.
   - Nghiêm cấm công thức nhân tốc độ bán thị trường với hoa hồng để suy diễn "thu nhập ước tính" (`sales_velocity × commission`). Hoa hồng chỉ được tính trên đơn hàng có phân bổ trực tiếp thông qua giả định kịch bản người dùng (`expected_attributed_orders`).
3. **Chiến lược Nguồn Giả định Thủ công (Manual-First Source Strategy):**
   - MVP ưu tiên dữ liệu giả định do người dùng tự nhập và quản lý theo kịch bản.
   - Trường hoa hồng thu thập từ crawler (`ProductSnapshot.commission_rate`) chỉ là dữ liệu quan sát tham khảo, không có thẩm quyền kinh tế tự động.
   - Giá sản phẩm thị trường chỉ được sao chép và đóng băng thành proxy có nhãn và dấu thời gian khi người dùng chủ động yêu cầu (`commission_base_source = 'observed_price_proxy'`), tuyệt đối không liên kết động vào dữ liệu crawler biến động.
4. **Kịch bản Thuộc sở hữu Product & Bất biến Duy nhất Một Mặc định (Exactly-One-Default Invariant):**
   - Mô hình dữ liệu phân cấp: Một `Product` sở hữu nhiều kịch bản kinh tế có tên (`economics_scenarios`).
   - Bất biến mặc định: Khi một Product có ít nhất một kịch bản, **luôn tồn tại đúng một** kịch bản mặc định (`is_default = true`).
   - Cưỡng chế tại database: Chỉ mục cục bộ duy nhất `uq_economics_scenarios_product_default (product_id) WHERE is_default = 1`.
   - Khóa giao dịch: `BEGIN IMMEDIATE` với cơ chế retry hàm mũ (50ms, 100ms, 200ms) phòng chống tranh chấp đồng thời (race conditions).
   - Kịch bản đầu tiên tạo cho một sản phẩm tự động nhận cờ mặc định.
   - Chuyển đổi mặc định diễn ra nguyên tử trong giao dịch database.
   - Xóa kịch bản mặc định khi vẫn còn kịch bản khác tự động thăng cấp kịch bản cũ nhất còn lại theo thứ tự `(created_at ASC, id ASC)`. Khi sản phẩm không có kịch bản nào, số mặc định bằng 0.
5. **Ngữ nghĩa Số học & Tiền tệ Toàn vẹn (Integer VND & Basis Points):**
   - Hệ thống thuần túy hỗ trợ VND (VND-only MVP); không hỗ trợ đa tiền tệ hoặc quy đổi ngoại tệ (FX).
   - Giá trị tiền tệ được lưu trữ dưới dạng số nguyên VND (integer whole-VND, không có đơn vị thập phân), giới hạn $0 \le \text{money} \le 10^{11}$.
   - Tỷ lệ hoa hồng được lưu trữ dưới dạng điểm cơ bản nguyên (`bps`, $0 \le \text{bps} \le 10,000$, 10,000 bps = 100%). Từ chối phân số thập phân của bps (sub-bps rejection).
   - Bảo toàn giá trị thiếu (`null ≠ 0`): Các trường giả định chưa nhập giữ nguyên `null`, tuyệt đối không tự động gán bằng `0`.
    - Phân tách rõ ràng giữa chi phí cố định (mẫu sản phẩm, sản xuất nội dung, ngân sách quảng cáo) và chi phí biến đổi cho mỗi đơn hàng phân bổ.
    - Hợp đồng thẩm định an toàn JavaScript: Toàn bộ đầu ra tiền tệ nguyên phái sinh được thẩm định không vượt quá $Number.MAX\_SAFE\_INTEGER = 9\,007\,199\,254\,740\,991$ ($2^{53} - 1$). Payload tạo mới, cập nhật hoặc rebase gây tràn số bị từ chối với HTTP 422, bảo toàn ngữ nghĩa phân biệt giữa thiếu giả định (`null`) và tràn số transport.
6. **Thẩm quyền Tính toán & Làm tròn Thuộc Backend Duy nhất (Backend Calculation Authority):**
   - Toàn bộ công thức tài chính được tính toán tất định tại thời điểm đọc ở backend trong `backend/app/analytics/economics.py`.
   - Không lưu trữ (not persisted) bất kỳ chỉ số kinh tế phái sinh nào vào database.
   - Áp dụng chính sách làm tròn chuẩn round-half-up số nguyên thuần túy:
     $$\text{round\_ratio\_half\_up}(N, D) = (2N + D) // (2D)$$
   - Điểm hòa vốn sử dụng tử số đóng góp hữu tỉ chuẩn xác trước khi chia trần số nguyên để loại bỏ hoàn toàn sai lệch off-by-one do làm tròn hiển thị:
     $$\text{contrib\_num} = \text{base\_vnd} \times \text{rate\_bps} - \text{var\_cost\_per\_order\_vnd} \times 10\,000$$
     $$\text{break\_even\_orders} = \left\lceil \frac{\text{fixed\_campaign\_cost\_vnd} \times 10\,000}{\text{contrib\_num}} \right\rceil = (\text{fixed\_cost} \times 10\,000 + \text{contrib\_num} - 1) // \text{contrib\_num}$$
     (với $\text{contrib\_num} > 0$).
   - Frontend chỉ hiển thị, không nắm bất kỳ thẩm quyền tính toán hay làm tròn tài chính nào.
7. **Ranh giới Phiên bản Tương thích "3" & Kế thừa ADR-004 (Compatibility "2" → "3"):**
   - Schema Phase 6 được tích hợp qua additive bootstrap trong `init_db.py`, bổ sung bảng bắt buộc `economics_scenarios`.
   - Marker khả chuyển trong `system_metadata` được nâng cấp từ `"2"` lên `"3"` sau khi xác nhận toàn bộ schema động.
   - Toàn bộ cơ chế sao lưu nóng (`BACKUP.bat`) và phục hồi ngoại tuyến (`RESTORE.bat`) theo nguyên tắc cùng phiên bản của ADR-004 tiếp tục giữ nguyên hiệu lực. Ứng dụng Phase 6 từ chối phục hồi các bản sao lưu phiên bản 1 và 2.
8. **Ngân sách Truy vấn Hiệu năng Chặt chẽ (Strict Query Budgets & Benchmarks):**
   - Lấy danh sách kịch bản sản phẩm: $\le 2$ câu lệnh SQL.
   - Lấy danh sách thành viên Bộ sưu tập kèm kinh tế mặc định: $\le 3$ câu lệnh SQL (Zero N+1).
   - So sánh 2–5 sản phẩm kèm kinh tế mặc định: $\le 3$ câu lệnh SQL (không có collection) / $\le 4$ câu lệnh SQL (có collection) (Zero N+1).
   - Benchmark 200 sản phẩm / 5.000 snapshots đạt độ trễ worst $< 20\text{ms}$ (vượt xa ngưỡng cứng $< 200\text{ms}$ và mục tiêu $< 50\text{ms}$).
9. **Cô lập Không gian Làm việc & Ranh giới Phạm vi Ngoài:**
   - Saved View V1 (Trends & Watchlist) giữ nguyên cấu trúc tham số tĩnh, không mở rộng sang kinh tế trong MVP.
   - Không có luật cảnh báo kinh tế và không hỗ trợ xuất CSV kinh tế trong MVP.
   - Không tích hợp TikTok Affiliate API/OAuth, không cào Creator Center riêng tư, không CAPTCHA bypass, và không bổ sung thư viện phụ thuộc bên thứ ba.

