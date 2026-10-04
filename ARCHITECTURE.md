# Current architecture

Updated: 2026-10-03.

Next.js 15 / React 18 dashboard on 127.0.0.1:3000 calls FastAPI on 127.0.0.1:8000. SQLAlchemy stores products, snapshots, crawl runs, categories and additive quarantine records in local SQLite. APScheduler triggers collection at configured Vietnam local times.

The crawl service reserves one active run before enqueueing work. Each cycle discovers candidates and refreshes up to 100 oldest tracked verified products. Canonical numeric product identity deduplicates candidates and snapshots. Each product transaction commits its snapshot and counters together; failures roll back that item. Startup reconciles orphan running runs. Empty or entirely failed runs are failed; mixed results are partial.

The collector uses HTTP first and lazily starts Playwright. Product URLs are restricted to supported TikTok HTTPS product paths. HTTP redirects and browser requests are checked for public destinations; private network targets are rejected. Structured product identity must match the requested URL. Missing metrics remain null. Generic page titles and feed videos cannot become products.

Analytics uses UTC observations, bounded tolerances around requested time windows, actual elapsed time for velocity and distinct comparable intervals for acceleration. Observations older than eight hours cannot contribute current rising scores. Quarantined history is preserved but excluded from product APIs and rankings.

Frontend fetches guard against stale responses, expose failures with retry and refresh once when a crawl finishes. SQLite naive UTC values are serialized with timezone information. Charts retain missing values instead of inventing zero.

Standard Windows scripts verify command/executable ownership and listener ancestry before stopping process trees. Unowned port conflicts abort startup. Hidden source runtimes use separate .next-dev cache; builds use .next. Backend health exposes a source revision calculated at import. This is a local development runtime, not a packaged or remotely deployed service.


## Phiên truy cập cục bộ (03/10/2026)

`CONNECT_TIKTOK.bat` mở công cụ để người dùng tự đăng nhập, chỉ lưu khi người dùng nhập SAVE. Không đọc profile trình duyệt hiện có và không tự xử lý password/OTP/CAPTCHA. State tại backend/.local/tiktok-session.json được Git ignore, lọc domain TikTok, loại cookie hết hạn và ghi qua temporary file rồi replace. HTTP giữ domain/path/secure/expiry; Playwright nạp storage_state. Context không được coi là authenticated chỉ vì có file.

API crawler/status chỉ trả local_session_status = missing/available/invalid; không trả cookie hoặc localStorage. Collector mới đọc lại file mỗi run; state lỗi được báo rõ và không in JSON gốc ra UI/log. Khi đã có state và HTTP vẫn trả Security Check, có thể thử navigation bình thường trong context đã nạp state; nếu browser vẫn gặp challenge, run thất bại và không ghi snapshot. Không tự vượt challenge.
