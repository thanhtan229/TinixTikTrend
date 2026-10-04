# Báo cáo sửa lỗi sau FINAL PRODUCTION REVIEW

Checkpoint: 03/10/2026, 09:01 UTC+7. Báo cáo audit gốc FINAL_REVIEW.md được giữ nguyên làm bằng chứng trước sửa.

## Kết quả

Đã triển khai bản sửa C1, H1–H8 và M1–M3, kiểm thử và áp dụng vào runtime development chuẩn. **Chưa đạt production acceptance** vì chưa có dữ liệu TikTok Shop VN đã xác minh qua nhiều chu kỳ thật. Không package exe.

| Finding | Bản sửa / bằng chứng |
|---|---|
| C1 | Next.js 14.2.35 → 15.5.27; ESLint tương thích, PostCSS override đã vá. Production dependency audit: 0 vulnerabilities; build pass. |
| H1 | Bỏ video-to-product và title-only fallback, bỏ giá/sold/rating/commission mặc định. Parser chỉ nhận identity cấu trúc khớp numeric product URL; trường thiếu null, sold0 giữ nguyên. Backup DB; cách ly 20 legacy feed products. |
| H2 | Baseline có tolerance hữu hạn, không dùng observation quá cũ làm window. Velocity dùng elapsed thực; acceleration cần hai interval distinct. Stale >8h không được xếp rising; UTC API và nhãn estimated/stale. |
| H3 | Mỗi chu kỳ refresh oldest tracked verified products (mặc định tối đa100), dedupe mỗi product/run; không refresh quarantine. Fixture tracked keyword cycle pass. |
| H4 | Keyword được chuyển đúng vào DiscoveryQuery.keyword; category dùng mapping keyword. Không trả video giả làm Shop result. |
| H5 | All-failure/empty run failed; mixed success partial. UI hiển thị error_message và trạng thái lỗi. |
| H6 | Reserve trước BackgroundTasks; toàn lifecycle try/finally release; rollback từng item; startup reconcile orphan runs. DB lock, commit failure và item rollback tests pass. |
| H7 | Launcher verify exact executable/command/ancestor trước stop; chỉ taskkill tree đã xác minh. Foreign port conflict abort. Hidden windows, không duplicate runtime, standard restart replacement verified. |
| H8 | Bind loopback; HTTPS TikTok product allowlist, DNS public IP checks, redirect validation và browser request guards. Private-target/redirect/API boundary tests pass. |
| M1 | Polling tuần tự + refs cho callback/status; refresh khi crawl kết thúc. Mounted component test pass. |
| M2 | Fetch error có retry, clear stale data, sequence guard chống response cũ. Mounted component test pass. |
| M3 | Naive SQLite UTC được serialize có timezone; scheduler Vietnam timezone rõ ràng. API timezone test pass. |

## Validation

- Backend: **51 pytest PASS**, một warning deprecation FastAPI/httpx.
- Frontend: **2 mounted recovery tests PASS**; ESLint PASS, TypeScript noEmit PASS.
- Next.js production build PASS; không tạo executable/installer.
- Production npm audit (`--omit=dev`): **0 vulnerabilities**. Full audit còn **7 high** dev dependencies liên quan braces/toolchain Tailwind3/ESLint. Chưa có patched braces version trong kết quả audit; không dùng force major upgrade để che finding. Không đưa CSS/glob không tin cậy vào build toolchain.
- PowerShell script parse và ownership selector checks PASS.
- Browser thật sau restart: dashboard tải, quarantine notice đúng, summary0 và empty state hợp lệ; chuyển Rising không lỗi. Initial console warning/error list rỗng. Mounted tests bổ sung completion/error handling; không coi fixture là live collection PASS.
- Live safe discovery: HTTP-first/browser fallback kết thúc với RuntimeError `No verified TikTok Shop product links were available`. Không ghi dữ liệu thử vào DB thật; browser collector đóng sạch. Đây là limitation, không phải live Shop acceptance PASS.

## Bảo toàn dữ liệu

Backup SQLite trước sửa: `backups/affiliate-before-production-fixes-20261003-082934.db` (backup API, integrity verified). Sau startup migration và final restart: original **20 products / 50 product_snapshots**, integrity=`ok`; **20 quarantined_products**, visible verified products0. Dữ liệu gốc không bị xóa; bảng quarantine chỉ loại khỏi API/analytics. Crawl history cũ được giữ như bằng chứng lịch sử.

## Runtime đã áp dụng

Chạy `RESTART.bat` standard, exit0. Ownership/PID replacement xác minh:

- Backend wrapper **103224** (worker107124) → **110248**, started `2026-10-03T02:00:23.1093937Z`.
- Frontend **90184** → **88796**, started `2026-10-03T02:00:24.2420608Z`.
- Ba PID cũ không còn tồn tại sau restart; launcher verify listener ancestry cho project trong services.log.
- Backend `/api/health`: HTTP200, status=`ok`, database=`connected`, revision=`57bc800826a8488d` **khớp disk source revision**.
- Frontend `http://127.0.0.1:3000`: HTTP200; development cache `.next-dev`, dashboard reload sau replacement. Production build `.next` riêng.
- Không có crawl đang chạy trước restart, không ngắt task user. Backend/frontend bind127.0.0.1. Runtime dùng original DB và lịch scheduler bình thường.

## Phần chưa xác minh / còn mở

1. Cần accessible verified TikTok Shop VN product và nhiều observations thực để chứng minh sales fields, historical windows và usefulness. Generic Explore trong phiên này chưa trả Shop links; không thể kết luận tool đang hữu ích cho quyết định Affiliate.
2. Full development dependency audit còn7high; production dependency audit sạch. Cần đánh giá migration toolchain khi có patch tương thích.
3. Mobile layout, chart với verified live history, long-duration network/reboot/lock soak chưa kiểm tra đầy đủ.
4. Scenario tạo process giả lập tranh chấp port bị automatic approval review từ chối với lý do **blocked by policy**. Không chạy workaround; đã kiểm tra selector read-only và restart đúng project thực tế. Foreign-listener conflict runtime scenario vẫn NOT TESTED.

Ứng dụng development đã nạp bản sửa và có thể kiểm thử tại http://127.0.0.1:3000. Quyết định production vẫn **NOT READY** cho tới khi các live-data acceptance ở trên được chứng minh.


## Follow-up checkpoint — 03/10/2026, 09:12 UTC+7

Tiếp tục theo yêu cầu hoàn thiện; user cho phép chọn URL bất kỳ.

- Sửa thêm association JSON-LD: URL, @id và offer URL khác requested ID không thể gán metadata sibling vào sản phẩm đang quét. Đọc listing link escape JSON slash / Unicode slash và HTML entities; loại video như trước. Negative/overflow metrics không biến thành số dương hoặc infinity. Giới hạn tracked_products_per_run trong1..1000.
- Sửa mobile header bị chen và thêm accessible labels cho form quét, refresh/search/category/score controls. Thực tế390px không có horizontal overflow; form nhãn đúng và kết quả failed crawl hiển thị.
- Collector nhận diện trang Security Check/Access Denied dù HTTP200, dừng với BlockedError, không launch browser để cố vượt challenge. Crawl service phản ánh nguyên nhân tiếng Việt rõ ràng và không tạo snapshot. Test xác minh security check không gọi browser fallback.
- Backend **57 tests PASS**, frontend **2 mounted tests PASS**, lint và TypeScript PASS. Không full build lại vì chỉ đổi UI/validation backend, không đổi dependencies/types/API contracts; production build đã PASS ở checkpoint trước. Không package exe.
- Trên database thật, UI default crawl run11 failed không có verified links. Sau user cho phép URL bất kỳ, dùng https://shop.tiktok.com/view/product/1729570313535393936 từ tài liệu TikTok Shop Partner Center https://partner.tiktokshop.com/docv2/page/affiliate-integration . Chưa xác nhận region hay tính hiện hành của ví dụ. Direct response HTTP200, title Security Check, không JSON-LD. Runs12 và13 kết thúc failed, product URL candidate1, snapshots0; run13 hiển thị đúng lỗi Security Check. Không coi ví dụ tài liệu là live product đã xác minh.
- UI busy → failed → idle được kiểm chứng bằng browser thật, dashboard refresh sau completion. Bằng chứng screenshot: docs/screenshots/mobile-security-check.jpg. Temporary viewport đã reset.
- Audit full vẫn7high, npm registry braces latest3.0.3 vẫn nằm trong affected range của GHSA-vfj7-8cjw-p6xm https://github.com/advisories/GHSA-vfj7-8cjw-p6xm . Next lint plugin16 cũng vẫn kéo fast-glob; Tailwind4 riêng không giải quyết toàn bộ dependency path. Không downgrade/remove lint rules hay chỉnh audit metadata để che finding.

Final runtime: backend PID89196, started 2026-10-03T02:11:05.3946831Z; frontend PID104036, started 2026-10-03T02:08:41.8262941Z. Standard restart verified ownership; revision 738445f96ed473f2 matches disk. Backend HTTP200/statusok/databaseconnected; frontend HTTP200. Original20products/50snapshots integrityOK, no active crawl interrupted.

Production acceptance vẫn mở: cần phiên truy cập hợp lệ/nguồn dữ liệu thật đã được TikTok cho phép và nhiều observations theo thời gian. Authorization chọn URL bất kỳ không làm Security Check trả dữ liệu. Không tự giải/bypass CAPTCHA; không thay missing history bằng fixtures.


## Triển khai tiếp — 03/10/2026, 16:08 UTC+7

- Thêm CONNECT_TIKTOK.bat và app.connect_tiktok để người dùng tự đăng nhập trong browser riêng. Chỉ SAVE mới ghi state cục bộ; Enter hủy, giữ phiên cũ. Chưa chạy đăng nhập tài khoản thật vì không có phiên/tài khoản do user cung cấp; không đọc browser profile hiện có, không tự nhập password/OTP và không tự xử lý CAPTCHA.
- State tại backend/.local/tiktok-session.json được Git ignore. Lọc TikTok cookie/origin, loại cookie hết hạn/foreign domain, HTTP giữ scope/path/secure/expiry và Playwright khôi phục storage_state. File hỏng/quá2MB báo lỗi đã sanitize, không trả/in cookie trong API/log. Ghi tạm rồi replace để bảo toàn bản cũ nếu validation thất bại.
- Collector mới đọc state cho mỗi run, không cần restart để nhận phiên vừa lưu. Nếu có state và HTTP gặp challenge, chỉ thử navigation bình thường trong context đã nạp state; challenge trên browser vẫn thất bại, không bypass và không tạo snapshot.
- Status API/UI có missing/available/invalid; không có cookie/localStorage trong response. Available chỉ nói có state cục bộ, không chứng minh đăng nhập thành công hay có quyền Shop. Dashboard thật đã hiển thị đúng missing cùng hướng dẫn; không có console warn/error trong smoke.
- **66 backend tests PASS**, một warning FastAPI/httpx deprecation; **2 UI tests PASS**, ESLint PASS và production Next.js build/type validation PASS. pip check không có broken requirements. CLI --check xác nhận NO_LOCAL_SESSION. Smoke Chromium thật nạp cookie fixture thành công, không request mạng/không credential thật, đóng sạch.
- Chưa package exe. Bằng chứng dashboard: docs/screenshots/local-session-status.jpg. README và ARCHITECTURE/PLAN đã cập nhật workflow.

Final restart standard All exit0: backend 17936 started 2026-10-03T09:06:54.2886152Z; frontend 114900 started 2026-10-03T09:06:54.9960966Z. Old project PIDs117444/113256 absent. Backend HTTP200/statusok/databaseconnected, revision bbc58ad0af2b3a01 khớp source; frontend HTTP200. Không có run active trước restart; không ngắt crawl. DB20products/50snapshots/20quarantine integrityOK.

Blocker cụ thể: hiện local_session_status=missing. Cần user chạy CONNECT_TIKTOK.bat, tự đăng nhập/xác minh và SAVE, sau đó test URL Shop thật và nhiều chu kỳ. Cơ chế session đã test; thành công authenticated live collection chưa được chứng minh. Full development audit7high từ checkpoint trước vẫn mở, dependencies không đổi; production acceptance chưa READY.


## Authenticated follow-up — 03/10/2026 16:25 UTC+7

User đã đăng nhập và hoàn tất lưu state. CLI/status xác nhận local_session_status=available. Không in cookie/token/localStorage; unit tests được isolate khỏi file session thật bằng autouse fixture.

Live run15: URL ví dụ1729570313535393936 với phiên đã lưu, HTTP-first và browser fallback vẫn trả Security Check, failed, snapshot0. Run16: keyword son môi TikTok Shop, failed vì không có link Shop đã xác minh, snapshot0. Đây là kiểm chứng thất bại có phục hồi, không phải acceptance thu thập dữ liệu thành công.

Sửa lý do BlockedError theo trạng thái session: đã có phiên thì nói rõ đã nạp nhưng trang vẫn bị chặn, không lặp hướng dẫn đăng nhập. Regression test verifies failed run, snapshot0 và busy release. **67pytest PASS**, một warning deprecation FastAPI/httpx. Không frontend code/dependency/API contract changes; không full build lại; không packageexe.

Backend restart standard exit0, PID63520 →106684, start2026-10-03T09:25:00.1056806Z, old server replaced. HealthHTTP200/statusok/databaseconnected; revisionf0f1127383024881 khớp source. Frontend đang chạy PID106864, HTTP200, không cần restart/reload lượt sửa backend này. No active crawl interrupted.

Run17 sau sửa, cùng URL ví dụ: failed/securitycheck, candidate1, created0/updated0/snapshots0, is_runningfalse; error chính xác đã nạp phiên. OriginalDB20products/50snapshots/20quarantine, integrityOK. Trạng thái authenticated live-data acceptance vẫn mở; đã đề nghị link Shop đang truy cập được trong phiên user thay cho ví dụ tài liệu chưa xác minh market/current availability. Không tự xử lý challenge và không tạo fake metrics.


## VN PDP live acceptance checkpoint — 03/10/2026 16:38 UTC+7

User cung cấp URL shop.tiktok.com/vn/pdp/1737036472084039604. Đã thêm validator/listing support cho đúng đường dẫn numeric VN PDP, loại tracking query và fragment. Các đường dẫn lạ, encoded IDs, traversal và non-VN PDP vẫn bị từ chối.

Parser mới đọc __MODERN_ROUTER_DATA__ → loaderData → page_config product_detail → product_info component. Bắt buộc sale_region VN, error_code0 và product_id khớp requested ID. Lấy riêng product sold/review/rating; không lấy shop totals hoặc recommendation. VND real_price/original_price là giá hiển thị, mức tối thiểu khi có SKU range; không lấy stock/commission không xác minh. Fixture chỉ giữ các trường sản phẩm công khai đã quan sát, ảnh fixture thay bằng example.com; không lưu HTML/session/reviewer data. UI có category thực Đồ ăn & Đồ uống, placeholder VN PDP và giải thích giá hiển thị.

Validation: **86 backend pytest PASS**, một Starlette/httpx deprecation warning; Python compileall PASS; **2 mounted UI tests PASS**, ESLint PASS và tsc --noEmit PASS. Không full Next build lại vì không thay types/dependencies/bundler/API contract; production build đã PASS checkpoint trước. Không package exe. Live collector parse HTTP source_channel=http, không cần browser fallback cho PDP.

Real pipeline (database thật, không inject fixtures):
- Run18 completed: found1, created1, updated0, snapshot1.
- Run19 triggered từ UI với tracking query: completed, found1, created0, updated1, snapshot1. Busy → idle và dashboard refresh đúng.
- Run20 default run: discovery Explore chưa có link Shop; partial nhưng tracked product được cập nhật, created0, updated1, snapshot1. Browser dùng cho discovery, PDP vẫn HTTP.
- Product21, external ID1737036472084039604, title500g Chuối Sấy Mè..., shop BĂNG BĂNG FOOD, sold12808, product rating4.6, review730. Shop rating4.7/totals31801 không bị gán sang product. Snapshots51/52/53 giá lần lượt42892/43965/47611 VND; phản ánh giá hiển thị trả về ở từng lần, không hứa là giá checkout. Sold/review không đổi giữa ba quan sát. Commission null; các delta24h/7d/velocity/acceleration null vì lịch sử chỉ vài phút.
- DB21 products /53 product_snapshots /20quarantine, integrity_check=ok. Chỉ một product mang ID yêu cầu; 20products/50snapshots gốc vẫn còn nguyên. Visible verified products1.

Runtime: standard RESTART.bat All exit0, backend106684→102056, frontend106864→115632 (started2026-10-03T09:35:19.0313103Z). Sau live runs, restart backend thêm để kiểm tra persistence:102056→78964, started2026-10-03T09:37:13.2420966Z. Không có crawl active trước hai lần restart, không ngắt task. Ownership launcher verified, health backend HTTP200/statusok/databaseconnected, frontend HTTP200. Revision e9d57271383ac2f6 khớp disk. API sau restart còn nguyên snapshots51/52/53.

UI thật: dashboard sản phẩm đúng, detail730reviews/4.6, hai line charts và bảng history render từ snapshots thật; console warning/error rỗng trong smoke. Mobile390px documentWidth375 không horizontal overflow, ảnh loaded, charts2; viewport reset sau test. Bằng chứng docs/screenshots/vn-pdp-live-history.jpg và vn-pdp-mobile.jpg.

Production vẫn NOT READY: broad discovery chưa thành công; chưa có history đủ24h/7d, nhiều sản phẩm và soak dài để đánh giá trend usefulness. Full development dependency audit7high từ checkpoint trước vẫn mở, dependencies không đổi. Direct VN collection, repeated snapshots và restart persistence đã được chứng minh; blocker accessible product link đã giải quyết.


## History, trend evidence and discovery checkpoint — 03/10/2026 18:31 UTC+7

- Discovery requests now use the Shop VN home page for generic exploration and a real category breadcrumb URL observed on the product page for food. Verified category/home requests through both authenticated HTTP and standard browser navigation; both displayed Security Check. No bypass was attempted. Link parser now validates complete matched URLs and resolves relative links against the source page; it cannot truncate an invalid longer path into an accepted product ID.
- Fixed crawl candidate de-duplication: explicit newly pasted URL has priority over the saved/tracked URL with the same product ID. A regression test checks collector fetch, metadata update and single product record. Bounded `/crawler/runs` limit to1..100. UI explains when discovery is partial while tracked products still refresh.
- Addressed misleading trend score found in live detail: a single cumulative sales/review observation used to receive non-zero score from freshness/rating even with no measured change. Scores now require at least one recent velocity/acceleration/review delta; Trending excludes products without such evidence. ProductCard/detail badge explains missing evidence, and empty Trending explains that further comparable observations are needed. Live product score now0, because all three observations were captured minutes apart and cumulative sold/review stayed flat.
- Extracted `ProductHistory` UI with 24h,7d,30d and all controls using actual UTC timestamps, chronological charts, full timestamps/table, counts, explicit empty state and real zero values. Added detail fetch retry and corrected zero-rating display.
- Test/build: **91 backend tests PASS**, one Starlette/httpx deprecation notice; compileall PASS. **6 frontend tests PASS**, ESLint PASS, `tsc --noEmit` PASS, Next production build PASS (15.5.27). No exe packaging.
- User’s real SQLite remains 21 products/53 snapshots/20 quarantine; integrity ok, no running crawl. Runs18–20 are live checkpoints described above; no live crawl triggered in this iteration. Product21 snapshots51–53 persist; `/api/trends` now returns[] until another sufficiently spaced observation creates momentum evidence.
- Prior backend process had exited, with no port listener and no active CrawlRun. Ownership inspected; standard `RESTART.bat` All started backend/frontends. Wrapper/listener pairs: backend88276/103988 on port8000; frontend44088/48232 on3000, each a single project-owned listener. Exit0, both HTTP200. Backend statusok/databaseconnected, loaded revision9870cbdee0f5c21c.
- Remaining release gates: broad discovery currently meets TikTok Security Check, adequate24h/7d history, multiple live products, developer dependency audit7high and a long-duration soak.


## Live observation and display fix checkpoint — 03/10/2026 18:48 UTC+7

- After a two-hour interval, direct refresh of the user-provided product completed as run21 (completed, found1, updated1, snapshot1). Product21 now has four real snapshots. Sold count increased12808→12823; reviews remained730 and rating4.6. Observed pace is176.0006 units/day, explicitly estimated from about2.04 hours of observations; trend score55.6. This is still too little history for production trend acceptance.
- Browser review exposed a locale-formatting defect: generic number formatting rendered176.0006 as`176,001`, which looks like a six-digit count in Vietnamese. Added a dedicated one-decimal rate formatter and a mounted regression test; the running detail page now shows`+176,0` beside the estimated-per-day label.
- Frontend validation: **6 tests PASS**, ESLint PASS, TypeScript noEmit PASS. Targeted product-detail regression PASS. No new production build for this presentation-only change; prior production build remains green. No executable packaging.
- Replaced only the project frontend using `RESTART.bat frontend`; log records old wrapper44088 stopped and new wrapper43932 started, with listener107864. Browser reload visibly confirms updated output. Backend stayed on project-owned wrapper88276/listener103988 because backend source was unchanged.
- Healthcheck: backend HTTP200/statusok/databaseconnected, frontend HTTP200. SQLite integrity=`ok`; 21 products,54 snapshots,20 quarantined rows, and no active crawl. Latest loaded backend revision9870cbdee0f5c21c.
- Release gates remain open: home/category discovery returns Security Check; only one verified product with ~2h coverage, no 24h/7d or multi-product confirmation; seven high development-dependency audit findings; long soak not done. No security challenge was bypassed.


## Dependency audit recheck — 03/10/2026 18:53 UTC+7

- Re-ran the npm audit against the current lockfile. Production dependencies: **0 vulnerabilities**. Full development graph: **7 high**, chained through `braces`/`micromatch`/`fast-glob`, including Tailwind3 and Next15's ESLint plugin.
- `npm audit fix --dry-run` makes no changes and recommends Tailwind4.3.3 (semver-major) plus downgrading `eslint-config-next` to14.2.35 (semver-major, misaligned with the installed Next15.5.27). Registry has no `braces`3.0.4 release. No downgrade or forced override was applied. Any Tailwind4 or lint-stack migration needs its own compatibility and visual validation.


## UI review and multi-product collection checkpoint — 03/10/2026 19:18 UTC+7

- Second review caught signed-value defects beyond the original decimal issue. Shared signed formatters now add `+` only to positive deltas, preserve `-` on declines, and abbreviate large magnitudes symmetrically. Product cards use “Chênh lệch” labels; detail view distinguishes units/day from a 24h review delta and marks negative values in red.
- The manual crawl form now uses a labelled multi-line URL field. It trims and deduplicates exact lines, exposes a live count, enforces the backend limit of100, and blocks submission above that limit. API payload is typed rather than `any`.
- Validation after review: **11 frontend tests PASS**, ESLint PASS, TypeScript noEmit PASS, production Next build PASS. Tests cover negative and zero delta formatting, compact signed values, multi-line URL dedupe and over-limit prevention.
- Browser smoke verified the updated product page and dashboard. The URL form displayed `2 / 100 link duy nhất` after a local-only input check; no crawl was submitted using test URLs. Latest `RESTART.bat frontend` replaced frontend wrapper104308 with wrapper74492/listener85860. Backend wrapper88276/listener103988 remains unchanged and healthy.
- Current healthchecks pass: backend HTTP200/statusok/databaseconnected and frontend HTTP200. SQLite integrity=`ok`, 21 products/54 snapshots/20 quarantine rows, zero active crawls. Run21 remains the latest live capture; daily pace remains estimated from only~2h history.
- The new field gives the user a safe way to provide several real PDPs without relying on blocked Shop discovery. User action needed for acceptance: paste3–5 distinct product-detail URLs that open normally while signed in, submit one crawl, and keep local services running through at least24h (7d evidence needs7d). Broad discovery still meets Security Check; do not attempt to bypass it.
