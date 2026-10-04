# Final Production Review

## STATUS

**NOT READY** — chưa an toàn để dùng làm công cụ ra quyết định Affiliate thực tế.

Review bắt đầu ngày 02/10/2026, hoàn tất ngày 03/10/2026, múi giờ UTC+7. Chỉ audit/test; không sửa source, refactor, cài thêm dependencies hoặc đóng gói executable.

Có **9 finding MUST FIX BEFORE RELEASE**: 1 CRITICAL, 8 HIGH. Thêm 3 finding MEDIUM SHOULD FIX BEFORE RELEASE. Các triệu chứng chung được nhóm; không tính mỗi advisory hoặc mỗi giá trị giả thành issue riêng.

## BASELINE

- `git status --short`: **không thực hiện được**, thư mục project không phải Git repository. Không xác định được uncommitted changes, phiên bản commit hoặc thời điểm regression bắt đầu.
- Findings mô tả lỗi của implementation đang có; **không kết luận đây là regression mới**. Không có historical baseline đáng tin cậy để phân biệt lỗi cũ/mới.
- Đã đọc `AGENTS.md`, `DEVELOPMENT_WORKFLOW.md`, `UX_UI.md`, `Project.md`, `README.md`, `PLAN.md`, `ARCHITECTURE.md`, `PROJECT_STATUS.md`, `RESEARCH.md`, `RESEARCH_COMPARISON.md`, tài liệu `docs/architecture/`, `docs/research/`, và script/runtime/test thực tế.
- `PLAN.md`, `ARCHITECTURE.md`, `PROJECT_STATUS.md`, `RESEARCH.md`, `RESEARCH_COMPARISON.md` vẫn là template với `TBD`, chưa ghi trạng thái thực tế. Không dùng chúng làm bằng chứng milestone đã hoàn tất. Không tìm thấy `RELEASE_WORKFLOW.md`, migration framework, updater, CI/CD hay cấu hình packaging.
- Implementation: Next.js App Router → FastAPI → SQLAlchemy/SQLite; manual BackgroundTasks và APScheduler gọi cùng CrawlService; browser discovery và HTTP/browser product collector; analytics tính từ snapshots.
- Next.js cài thực tế: **14.2.35**. Frontend package version **0.1.0**, API version **1.0.0**; hai số này chưa có release contract chung, không coi riêng khác biệt này là lỗi release.
- Database gốc chỉ mở read-only khi kiểm tra và sao lưu: integrity check `ok`; **20 products, 50 snapshots, 10 completed crawl runs**; cả 20 product có ID `tt_item_*`, **30 snapshots** có price=149000/rating=4.8. Đây là bằng chứng contamination đã tồn tại, không chỉ giả thuyết từ code.
- Các scenario ghi dữ liệu dùng SQLite in-memory hoặc bản sao trong `%TEMP%`; scheduler tắt trong server audit để tránh crawl tự động. Không sửa dữ liệu thật.

### Đối chiếu documentation với implementation

| Cam kết | Implementation thực tế |
|---|---|
| `Project.md` §6/§54: video không tự động là product; metric thiếu phải null | Discovery đổi video thành product, gán metric mặc định; UI thay null bằng hoa hồng/điểm chart giả — H1 |
| §16/§43/§57: nhiều crawl cycle tạo history hữu ích | Scheduled crawl chỉ lấy feed mới, không refresh danh sách product đã lưu — H3 |
| §18/§20: velocity/acceleration dựa đúng lịch sử | Cửa sổ thời gian chọn baseline quá xa, dùng lại tín hiệu cũ — H2 |
| Research: HTTP-first/session bootstrap, category/tag URL | Discovery dùng browser Explore; category/keyword từ API không đi tới search; cookies lấy trước khi duyệt trang — H4; chưa có phép đo chứng minh tuyên bố tiết kiệm 90% |
| README/workflow: dừng an toàn đúng process | Stop script kill theo port và selector chung cho mọi project — H7 |
| Milestone nghiên cứu/validation thực tế | `research/test_product_scrape.py` dùng HTML tự viết; không chứng minh collector hoạt động với sản phẩm Shop VN thật |

## TEST / BUILD RESULTS

| Kiểm tra | Kết quả | Giới hạn |
|---|---|---|
| Backend `.venv/Scripts/python.exe -m pytest tests -q` | **PASS: 28 tests**, 1 deprecation warning | `DATABASE_URL=sqlite:///:memory:`; fixture API/parser/analytics; không bao phủ happy-path live crawler, lỗi DB hay UI |
| Frontend `tsc --noEmit --incremental false` | **PASS** | Static typecheck |
| `npm run build` | **PASS** | Next.js 14.2.35; `/`, `/products/[id]`; không package exe |
| `npm run lint` với `CI=1` | **NOT RUN / BLOCKED** | Lệnh mở wizard chọn ESLint vì chưa có config/dependency; exit 1. Không tạo config để giữ scope audit. Build pass không đồng nghĩa lint pass |
| `pip check` | **PASS** | Không có dependency requirement bị hỏng |
| AST parse toàn bộ `backend/app` | **PASS: 45 Python files** | Kiểm tra cú pháp, không thay thế runtime tests |
| `npm audit --omit=dev --json` | **FAIL: 2 affected packages**, next CRITICAL, bundled postcss HIGH | C1 đã đối chiếu advisory chính thức; không mặc định mọi advisory đều khai thác được trong project |
| Production runtime smoke trên copy DB | **PASS** | Backend health 200/status ok/database connected; frontend `/` và `/products/1` 200; API products/detail/dashboard/trends/crawler status 200. Dùng loopback và APP_ENV=testing |
| Live TikTok discovery, limit=2 | **FAIL acceptance** | **0 product URLs, 2 video items**, cả 2 nhận price/rating mặc định. Không lưu live result vào DB thật |
| Fault injection / SQLite exclusive lock / reopen persistence | **FAIL các scenario H1/H2/H5/H6** | Chi tiết bên dưới; các kết quả được tái hiện bằng module thật với input kiểm soát |
| Browser manual/E2E | **NOT TESTED** | Codex IAB timeout khi attach webview sau 2 lần thử; không có E2E suite project. HTTP 200 không chứng minh UI tương tác pass |

Không quan sát thấy flaky test trong suite đã chạy; không suy ra suite luôn ổn định. Các lỗi discovery/analytics/recovery được tái hiện riêng sau baseline, dù 28 test vẫn pass.

## CRITICAL FINDINGS

### C1 — Next.js đang dùng có RCE đã công bố trên Windows

- **Severity:** CRITICAL.
- **Problem:** Next.js 14.2.35 nằm trong dải bị ảnh hưởng của GHSA-p293-qw3h-jr36/CVE-2026-75604. Project dùng App Router và Windows filesystem, đúng điều kiện platform/router nêu trong advisory. Launcher chạy `next dev` không cấu hình bind loopback.
- **Evidence:** `frontend/package-lock.json`, installed `node_modules/next/package.json`; npm audit; [advisory chính thức của Vercel](https://github.com/vercel/next.js/security/advisories/GHSA-p293-qw3h-jr36). Advisory xác định affected >=13.4 và <15.5.24; bản vá 15.5.24 hoặc 16.3.3.
- **User impact:** Rủi ro thực thi code trên máy Windows khi endpoint bị kẻ tấn công truy cập. Chưa thực hiện exploit và chưa xác nhận firewall/LAN reachability của máy này.
- **Reproduction:** Kiểm tra installed version và platform/App Router; chạy npm audit và đối chiếu advisory. Không cần chạy payload nguy hiểm để xác nhận dependency nằm trong phạm vi.
- **Recommended fix:** Nâng Next lên bản đã vá tương thích, cập nhật lockfile, typecheck/build và test route/runtime; bind localhost theo mục đích local-first. Không chạy `npm audit fix --force` một cách mù quáng. Các advisory khác cần xét feature applicability, không đếm thành finding riêng.
- **Release decision:** **MUST FIX BEFORE RELEASE**.

## HIGH FINDINGS

### H1 — Dữ liệu không xác thực được quảng bá và lưu như dữ liệu Shop thật

- **Severity:** HIGH.
- **Problem:** Video không có quan hệ Shop được tạo thành product; thiếu sales/price/rating được bù bằng số giả. Trang bị chặn cũng được nhận làm product; UI bù commission và chart null bằng giá trị không có nguồn.
- **Evidence:** `backend/app/collectors/tiktok_shop/discovery.py:85–114` tạo `tt_item_<video_id>`, sold=`parse_numeric_string(text) or 250`, rating=4.8, price=149000, `is_partial=False`. Live check: 2/2 video bị chuyển thành product. In-memory pipeline lưu đúng sold=250/price=149000/rating=4.8. DB thật đã có 20 video-products/30 snapshot mặc định. `parser.py:160–178` nhận title/URL là đủ; `product.py:42` chấp nhận mọi product từ rendered HTML. Scenario với product ID 123 cho kết quả tên từ `Known Product` thành `Access Denied`, thêm snapshot null và advance last_seen. `frontend/src/app/products/[id]/page.tsx:75–77,196` đổi null thành chart 0/commission 15%.
- **User impact:** Dashboard/Best Sellers/Trend Score dựa vào dữ liệu giả; có thể chọn sai sản phẩm Affiliate. Trang lỗi còn thay tên và latest metrics của product hợp lệ. Lịch sử đã nhiễm số giả không thể tự sửa chỉ bằng đổi collector.
- **Reproduction:** Discovery một card `/video/` không có thông tin bán hàng; chạy upsert rồi đọc snapshot. Hoặc trả HTML `<title>Access Denied</title>` ở product URL qua cả HTTP/browser. Mở chi tiết một product commission=null.
- **Recommended fix:** Chỉ tạo product khi có danh tính Shop được xác minh; tách video khỏi product. Giữ metric thiếu là null, bỏ các fallback giả của UI; reject error/challenge/login HTML. Quarantine dữ liệu `tt_item_*`/snapshot đã nhiễm sau backup, không tự xoá toàn bộ history. Số đếm VN cũng cần parser theo định dạng nguồn: hiện `12.500 sold`→12, `1,2K sold`→12000 trong phép thử; không diễn giải text card bất kỳ thành sales.
- **Release decision:** **MUST FIX BEFORE RELEASE**.

### H2 — Cửa sổ delta/velocity/acceleration và freshness của quan sát không đáng tin

- **Severity:** HIGH.
- **Problem:** `find_closest_snapshot` chỉ có bound phía trên, không giới hạn độ xa phía dưới; tolerance 24 giờ phía tương lai được áp dụng cả cửa sổ 6h. Nhiều cửa sổ dùng cùng một baseline không đủ lịch sử. Analytics còn lấy latest capture làm hiện tại dù capture đã cũ.
- **Evidence:** `backend/app/analytics/deltas.py:43–64,95–144`; `services/product_service.py:26` không truyền current_time. Hai snapshot cách 4h, sold 100→200 cho delta 6h/12h/24h đều 100, velocity/day=100 và acceleration=100 dù chưa có hai kỳ 6h. Khoảng trống 30 ngày cho `sold_delta_7d=100`. Product last_seen 7 ngày trước vẫn trả sold_24h=1500, velocity=1500, score=69.6 ở ngày review.
- **User impact:** Rising/Best Sellers theo 24h và 7d xếp hạng sai, dấu hiệu tăng tốc bị dựng từ thiếu lịch sử; dữ liệu một tuần trước vẫn trông như bán trong hôm nay.
- **Reproduction:** Gọi `calculate_product_deltas` với các cặp snapshot trên; gọi `get_analyzed_product` với latest snapshot 7 ngày trước.
- **Recommended fix:** Window-specific coverage/tolerance ở cả hai phía; không dùng cùng snapshot để khẳng định hai kỳ độc lập; tính velocity theo elapsed time thực và phân biệt estimate với observed delta. Truyền thời điểm hiện tại, gắn stale/incomplete, không dùng stale velocity làm tín hiệu hiện tại. Giữ historical totals để xem history.
- **Release decision:** **MUST FIX BEFORE RELEASE**.

### H3 — Scheduled crawl không refresh sản phẩm đã theo dõi

- **Severity:** HIGH.
- **Problem:** Sau khi nhận sản phẩm từ feed hoặc link nhập tay, schedule tiếp theo chỉ discovery Explore; không lấy các product URL đã lưu để tạo snapshot định kỳ.
- **Evidence:** `backend/app/services/crawl_service.py:126–157`, `scheduler/jobs.py:22`. Scenario có product đã lưu URL, một snapshot, discovery cycle sau chỉ trả item khác: **0 tracked URLs được fetch; product cũ vẫn 1 snapshot**. Không có path recrawl stored products trong scheduled job.
- **User impact:** Workflow chính không thu được history ổn định để nhận biết velocity; dữ liệu chỉ cập nhật nếu tình cờ hiện lại trong feed hoặc user tự nhập lại link.
- **Reproduction:** Crawl link product A; schedule cycle tiếp theo không còn A trong discovery; đếm snapshots của A.
- **Recommended fix:** Trong mỗi cycle, refresh tập product đã theo dõi theo policy có giới hạn; discovery bổ sung product mới. Dedupe theo canonical Shop ID và một snapshot/product/run. Kiểm chứng nhiều cycle Shop VN thật.
- **Release decision:** **MUST FIX BEFORE RELEASE**.

### H4 — Input từ khóa/ngành hàng bị bỏ qua

- **Severity:** HIGH.
- **Problem:** UI/API nhận keyword nhưng service chuyển vào `category_slug`; discovery chỉ dùng `query.keyword` để chọn search URL. Category slug cũng không điều hướng category, chỉ gắn nhãn lên item lấy từ Explore.
- **Evidence:** `services/crawl_service.py:128–136`, `collectors/tiktok_shop/discovery.py:30–33,110`. Input `keywords=['son-moi']` tạo query `{category_slug:'son-moi', keyword:null}` và actual URL `https://www.tiktok.com/explore`.
- **User impact:** User yêu cầu ngành hàng cụ thể nhưng nhận feed chung, có thể còn bị gắn category sai; công cụ quét tùy biến không làm đúng công việc được yêu cầu.
- **Reproduction:** Mở Quét theo Link/Từ khóa, nhập `son-moi`; theo query từ service tới `build_discovery_url`.
- **Recommended fix:** Truyền keyword/category đúng field và hỗ trợ hoặc từ chối category filter một cách rõ ràng; không lấy query làm category thật. Test UI→payload→URL→normalized category.
- **Release decision:** **MUST FIX BEFORE RELEASE**.

### H5 — Network/parser failure được báo completed

- **Severity:** HIGH.
- **Problem:** Discovery nuốt exception, vòng xử lý product chỉ log warning; run luôn đổi completed nếu không gặp outer error, kể cả không xử lý được product nào.
- **Evidence:** `discovery.py:120–134`; `crawl_service.py:139–163`. Inject timeout cho 1 URL: `{status:'completed', products_found:1, snapshots_created:0, error_message:null}`. UI chỉ hiện ready/count, không hiển thị latest run failed/partial/error_message (`CrawlerControl.tsx`).
- **User impact:** Mất mạng/bị chặn/parser hỏng vẫn trông như chạy thành công; không biết history đang mất chu kỳ, không có error/retry hướng dẫn hữu ích.
- **Reproduction:** Collector `get_product` raise TimeoutError hoặc trả None; chạy manual crawl rồi xem latest_run.
- **Recommended fix:** Return structured discovery/extraction failures; đếm outcomes, phân biệt legitimate empty result với access failure; all failed→failed, mixed→partial. Lưu lỗi đã sanitize và hiển thị failed/partial trên UI; giữ snapshots đã commit.
- **Release decision:** **MUST FIX BEFORE RELEASE**.

### H6 — Failure boundaries để lại crawler busy và trạng thái/persistence không nhất quán

- **Severity:** HIGH.
- **Problem:** Flag busy được set trước initial DB commit, trong khi try/finally chỉ bắt đầu sau commit. Product exception không rollback transaction trước khi xử lý item tiếp theo. Startup không reconcile run còn running sau interruption.
- **Evidence:** `crawl_service.py:103–123,146–159,171–180`; `main.py:19–25`; `db/init_db.py`. SQLite `BEGIN EXCLUSIVE` với short timeout gây OperationalError ở initial commit và **is_running=True** sau failure. Inject exception tạo snapshot cho item đầu, item sau thành công: **2 products, 1 snapshot, products_created=2, run completed**; thay đổi chưa rollback của item lỗi bị commit theo item sau. Reopen DB giữ history, nhưng status API trả `is_running=false` và `latest_run.status='running'`, finished_at=null cho run bị ngắt.
- **User impact:** DB bận tạm thời có thể khóa mọi crawl tiếp theo cho đến restart; partial failure làm lệch product/snapshot/counter. Sau crash/restart không biết run nào thực sự kết thúc.
- **Reproduction:** Giữ exclusive SQLite lock rồi trigger crawl; hoặc inject exception sau flush product trước snapshot; hoặc lưu run running rồi restart app.
- **Recommended fix:** Bọc toàn bộ lifecycle, kể cả initial persistence, trong try/finally; dùng transaction/savepoint mỗi product và rollback có chủ đích. Update counters sau successful unit. Reconcile interrupted runs khi startup thành failed/interrupted/partial với completed data được bảo toàn; retry DB có giới hạn. Không rollback toàn bộ những product đã commit trước đó.
- **Release decision:** **MUST FIX BEFORE RELEASE**.

### H7 — Start/stop/restart có thể kill dịch vụ của project khác

- **Severity:** HIGH.
- **Problem:** Stop script dùng port và command pattern chung làm tiêu chí sở hữu project.
- **Evidence:** `scripts/stop_services.ps1:60–87` kill mọi owner của port 8000/3000; kill python có `uvicorn app.main:app` hoặc `multiprocessing.spawn`; kill node có `*next*dev*`. `start_services.ps1:29` gọi script này ngay cả start lần đầu. Dry-run selector với `node D:\OtherApp\node_modules\next\dist\bin\next dev` cho **selected=True**. Chưa chạy lệnh kill để chứng minh, nhằm giữ an toàn các project khác.
- **User impact:** Một lần restart Trend Hunter có thể ngắt Next/FastAPI/Python worker khác, mất công việc chưa hoàn tất và trạng thái tác vụ.
- **Reproduction:** Có một project Next dev khác đang chạy trên port khác rồi đánh giá selector line 86; process vẫn khớp. Không cần terminate nó.
- **Recommended fix:** PID file có metadata project, command/executable/working directory ownership và process tree được xác minh; port chỉ hỗ trợ lookup. Nếu port thuộc project khác thì báo conflict. Giữ windows hidden và kiểm tra service start time/build identity.
- **Release decision:** **MUST FIX BEFORE RELEASE**.

### H8 — API local-first bị expose trên mọi interface và nhận URL tùy ý

- **Severity:** HIGH.
- **Problem:** Launcher hardcode backend `--host 0.0.0.0`, không có auth/host boundary cho run API; `product_urls: List[str]` được đưa thẳng vào HTTP client/browser có redirects. CORS không chặn client HTTP trực tiếp.
- **Evidence:** `scripts/start_services.ps1:39`; `backend/app/api/crawler.py:17–21,run`; `client.py:43,70`; `product.py:23,35`. TestClient POST không credentials với URL loopback nhận **200**, background task nhận nguyên URL. HTTP client thật fetch thành công một HTTP server loopback dùng riêng cho audit.
- **User impact:** Khi firewall cho phép inbound, thiết bị khác có thể đọc dữ liệu và trigger crawler; endpoint có thể bị dùng gửi GET vào địa chỉ nội bộ, consume browser/network và ghi dữ liệu không phải Shop. Không khẳng định exfiltration credential hoặc LAN exploit đã xảy ra.
- **Reproduction:** POST `/api/crawler/run` với `product_urls=['http://127.0.0.1:<port>/audit']`; collector fetch endpoint nội bộ. Thử nghiệm chỉ dùng endpoint vô hại do audit tạo.
- **Recommended fix:** Bind loopback cho local deployment; validate scheme/allowlist TikTok host và canonical product URL, kiểm tra mỗi redirect và không truy cập private/reserved hosts. Nếu LAN là chủ đích thì thêm authentication/authorization thật; không dùng CORS như access control.
- **Release decision:** **MUST FIX BEFORE RELEASE**.

## MEDIUM FINDINGS

### M1 — Dashboard không tự cập nhật khi crawler hoàn tất

- **Severity:** MEDIUM.
- **Problem/Evidence:** `frontend/src/components/CrawlerControl.tsx:29–38`: closure đọc cùng `status` trước/sau `await loadStatus()`. Nếu closure giữ true thì `!status.is_running` luôn false; closure giữ false thì prevRunning false. Mô phỏng đúng closure/setState semantics: next status=false, **onCrawlCompleted calls=0**.
- **User impact:** Crawler chạy xong nhưng list/counts tiếp tục là dữ liệu cũ cho tới refresh thủ công; user có thể nghĩ không thu thêm dữ liệu.
- **Reproduction:** Trigger crawl khi có dữ liệu mới; chờ transition running→idle; theo dõi callback loadData.
- **Recommended fix:** So sánh previous status với object mới trả về; dùng effect/ref hoặc completion run ID để gọi refresh đúng một lần, giữ callback hiện tại.
- **Release decision:** **SHOULD FIX BEFORE RELEASE**. Manual refresh hiện là workaround.

### M2 — Lỗi tải dashboard bị giấu thành empty hoặc stale results

- **Severity:** MEDIUM.
- **Problem/Evidence:** `frontend/src/app/page.tsx:32–52,249`: catch chỉ console.error, không set error/clear products. Initial API failure kết thúc ở “Chưa tìm thấy sản phẩm phù hợp”; failure khi đổi tab/category giữ list của tab/category trước nhưng hiển thị dưới lựa chọn mới. Không abort/sequence guard cho request chồng nhau. Đây là kết luận từ control flow; chưa test click thật vì browser blocker.
- **User impact:** Khi API mất kết nối, user dễ thao tác dựa trên list của bộ lọc khác hoặc tưởng database rỗng và trigger crawl không cần thiết.
- **Reproduction:** Tải list, đổi tab khi fetchTrends bị reject; products state không thay đổi, loading=false và tab mới vẫn selected.
- **Recommended fix:** Error state rõ ràng, retry; nếu giữ stale data thì ghi nhãn đúng query và last successful fetch; bỏ response lỗi/thành công đã obsolete bằng request identity.
- **Release decision:** **SHOULD FIX BEFORE RELEASE**.

### M3 — Thời gian DB/API mất timezone làm UI lệch 7 giờ

- **Severity:** MEDIUM.
- **Problem/Evidence:** SQLite trả naive datetime dù model dùng `DateTime(timezone=True)`; products/crawler serialize raw DB datetimes. API sample started_at=`2026-10-02T13:35:04.095004` không có Z/offset. `frontend/src/lib/utils.ts:39–46` dùng `new Date(...)` và local formatter. Với Asia/Bangkok, chuỗi này thành `06:35:04Z` thay vì `13:35:04Z`: **lệch -7 giờ**.
- **User impact:** Giờ crawl, first/last detected và chart history sai so với lịch tự động; khó biết quan sát nào mới hoặc run nào bị gián đoạn.
- **Reproduction:** Parse cùng timestamp có/không Z trong browser/Node có timezone UTC+7; so sánh ISO kết quả.
- **Recommended fix:** Chuẩn hóa datetime UTC aware tại API boundary trước serialization, xuất ISO có Z/+00:00; test roundtrip SQLite→API→local formatter. Không sửa hàng loạt timestamp lưu như local time.
- **Release decision:** **SHOULD FIX BEFORE RELEASE**.

## REGRESSION RISKS

- Không có Git/history và status checkpoint hữu dụng để chứng minh feature trước đây đã hoạt động. Tất cả finding là current defects.
- Suite hiện kiểm tra simulated analytics/parser/API; crawler tests chỉ status/list và flag busy→409, không chạy persistence/network failure lifecycle. Không có frontend/E2E suite.
- Sau fixes, ưu tiên regression cases: verified product/null metrics, blocked HTML, keyword routing, refresh tracked products, 4h/30d/stale windows, DB lock/rollback/restart, exact process ownership và completed-run dashboard refresh. Không chỉ chạy lại 28 test hiện có.

## DATA INTEGRITY

- **PASS:** SQLite integrity check; schema/model basics; old snapshots được append và còn sau dispose/reopen; upsert có unique external_product_id; fixture seed không gọi từ startup.
- **FAIL:** semantic integrity do H1/H2; product/snapshot consistency và run status do H6. “DB không corrupt vật lý” không có nghĩa dữ liệu phù hợp để sử dụng.
- Mỗi product thành công có commit riêng nên lịch sử đã commit có thể giữ khi run bị ngắt. Chưa kill máy/process giữa từng SQL statement; không khẳng định toàn bộ crash behavior đã pass.
- Không có schema migrations, versioned backup/restore/update protocol. Không chạy migration lên DB thật hoặc tự xoá snapshot nhiễm. Bắt buộc backup và xác định provenance trước sửa dữ liệu.

## SECURITY

- C1 và H8 là các rủi ro cụ thể cần sửa. Không nâng tất cả npm advisories thành nhiều issue; không thực hiện exploit.
- Source ứng dụng/config example/fixtures đã đọc không chứa secret/token hard-coded rõ ràng. Không dump cookie/env bí mật trong report. Đây không phải chứng nhận toàn bộ máy/filesystem không có secret.
- Không có auth/payment/cloud sync/updater trong scope implementation; không đề xuất hệ thống multi-user chỉ để làm checklist. Loopback isolation phù hợp app local.

## STABILITY / RECOVERY

- Startup và read APIs hoạt động trên copied DB; backend độc lập không crash khi scenario collector return lỗi được xử lý. Bounded HTTP retry/backoff/timeouts có triển khai.
- Failure reporting sai (H5), busy flag/rollback/restart status sai (H6), launcher ownership sai (H7).
- App shutdown hiện gọi scheduler.shutdown(wait=False); không có reconciliation cho interrupted crawl. Machine reboot/DB unavailable dài hạn/filesystem failure chưa fault-test trên dữ liệu thật.
- Chưa kiểm chứng automatic launch sau reboot; README chỉ hướng dẫn user chạy script thủ công, không coi thiếu auto-launch là feature bug.

## PERFORMANCE

- Với DB đang có 20 products/50 snapshots, smoke APIs trả thành công; không có bằng chứng performance blocker ở workload hiện tại.
- `ProductService.get_all_analyzed_products` eager-load **toàn bộ snapshots**, sort/tính Python mỗi request. UI gọi summary rồi trends, lặp phân tích; không có pagination lịch sử/detail. Đây là hướng cần đo khi dữ liệu lớn, **không gán severity chỉ từ code** và không đề xuất micro-optimization.
- Discovery giới hạn số card và sequential processing; HTTP semaphore/backoff có bound. Không thấy retry vô hạn trong path đã đọc.
- Không chạy long-term soak, CPU/RAM benchmark, 90-day dataset hoặc browser stress. Không chứng nhận khả năng scale chưa đo.

## RELEASE / UPDATE

- Production frontend build pass; không có executable/installer/updater/CI release trong project; package/update artifact/checksum/signature/apply/rollback **NOT APPLICABLE** cho implementation hiện có.
- Không tạo `.exe`. Review source runtime không phải acceptance installer.
- `Base.metadata.create_all` chỉ tạo bảng thiếu, không migrate schema hiện hữu. Chưa có concrete upgrade schema cần áp dụng trong review nên không dựng thêm finding migration giả định.
- Không có `RELEASE_WORKFLOW.md`; README đang hướng dẫn development runtime `next dev`/uvicorn reload. Chưa chứng nhận production launcher an toàn; H7/H8 và C1 phải xử lý trước dùng thường xuyên.

## MANUAL ACCEPTANCE

| Scenario production | Kết quả | Bằng chứng/giới hạn |
|---|---|---|
| Fresh startup trên copy DB | **PASS** | Uvicorn lifespan + Next production server; health/read APIs |
| List→dashboard/trends→detail API | **PASS** | HTTP 200; detail có snapshots; fixture suite có 404/filter/rank assertions |
| Product detail HTML route | **PASS smoke** | `/products/1` HTTP 200; không xác nhận hydrate/chart bằng browser |
| Discovery Shop VN thật | **FAIL** | Live: 0 Shop URLs, 2 video-items/metric mặc định — H1 |
| Manual keyword→đúng search | **FAIL** | Input son-moi vẫn Explore — H4 |
| Scheduled run→refresh product history | **FAIL** | Seed known URL, next feed khác, URL không fetch — H3 |
| 4h/incomplete, 30d gap, stale 7d analytics | **FAIL** | H2 outputs được tái hiện |
| Network lost/extraction timeout | **FAIL** | Run completed, 0 snapshots, no error — H5 |
| DB tạm locked→có thể chạy lại | **FAIL** | Real SQLite exclusive lock để lại busy flag — H6 |
| Partial product exception→không commit dữ liệu dở | **FAIL** | 2 products/1 snapshot và completed — H6 |
| Access denied page→giữ metadata hợp lệ | **FAIL** | Tên thành Access Denied, thêm null snapshot — H1 |
| Snapshot history sau reopen | **PASS** | File SQLite separate connection giữ 1 product/1 snapshot |
| Interrupted run sau restart | **FAIL, verified runtime** | Restart backend thật trên copy DB: latest_run source audit-interruption vẫn running, memory idle — H6; không power-cut DB thật |
| Duplicate-run rejection khi busy | **PASS** | Existing pytest HTTP409; không chứng nhận multi-process locking |
| Launcher chỉ stop project này | **FAIL dry-run** | Selector nhận foreign Next dev — H7; không kill unrelated app |
| Restrict custom URLs | **FAIL** | Unauthenticated arbitrary URL 200 + real harmless loopback GET — H8 |
| Crawl completed→dashboard reload | **FAIL simulation** | Callback 0; chưa browser click acceptance — M1 |
| SQLite timestamp→UTC+7 UI | **FAIL simulation** | Naive time lệch 7h — M3 |
| UI click/search/tab/filter/mobile/chart interaction | **NOT TESTED** | Browser webview attachment timeout; source review không thay thế manual PASS |
| Multi-day live sales usefulness / real Shop sold fields | **NOT TESTED** | Collector chưa đáp ứng verified Shop data; không có dữ liệu thực phù hợp để xác nhận |
| Reboot/power-loss/locked filesystem/network restore soak | **NOT TESTED** | Không thử phá runtime/data thật |
| Executable/update/migration/rollback | **NOT APPLICABLE / NOT TESTED** | Không có implementation release/update; không package |

## MUST FIX BEFORE RELEASE

1. **C1:** Nâng Next.js đã vá RCE Windows và validate compatibility.
2. **H1:** Dừng tạo/lưu/display số liệu giả; reject blocked HTML; backup/quarantine data đã nhiễm.
3. **H2:** Sửa coverage/time reference của delta, velocity, acceleration và stale observations.
4. **H3:** Tạo history bằng periodic refresh verified tracked products.
5. **H4:** Keyword/category routing đúng input và dữ liệu thực.
6. **H5:** Run failure/partial phản ánh đúng kết quả và hiển thị lỗi.
7. **H6:** Recovery toàn lifecycle; rollback per-product; reconcile interrupted runs.
8. **H7:** Process ownership chính xác trong start/stop/restart.
9. **H8:** Loopback API boundary và product URL/redirect validation.

**SHOULD FIX BEFORE RELEASE:** M1 completion refresh; M2 visible fetch failure/stale query handling; M3 timezone serialization.

Acceptance để chuyển sang READY: chạy lại automated suite/build và những reproduction ở trên, UI manual thực tế, sau đó nhiều chu kỳ crawl với **verified TikTok Shop VN products**/history không có fabricated metrics. Không cần polish hay refactor để vượt quality gate.

## SAFE TO DEFER

- UI polish, naming/style/refactor; phase 2 content/creator intelligence và affiliate scoring mở rộng.
- Performance optimization chỉ sau workload benchmark chứng minh bottleneck.
- Search hiện chỉ lọc top 50 kết quả do frontend không gửi search tới products API; không phải global database search. Có thể defer nếu UI ghi rõ phạm vi Top results; cần kiểm tra lại khi mở rộng workflow tra cứu toàn kho.
- Installer/auto-update/cloud/multi-user là scope tương lai, không phải finding của release source runtime hiện tại.

## FINAL DECISION

**NOT READY. SAFE TO USE NOW: No** cho quyết định Affiliate dựa trên dữ liệu ứng dụng.

Test/build pass chứng minh foundation compile và một phần API/analytics fixture hoạt động; không khắc phục dữ liệu giả, thiếu lịch sử định kỳ, số liệu time windows sai, recovery lỗi và security dependency đang có. Có thể dùng trong môi trường audit cô lập để kiểm tra, với dữ liệu được ghi rõ là test.

**Runtime cuối review:** Chỉ khởi động runtime audit trên bản sao DB, loopback; source/user database không được cập nhật. Standard `start/RESTART/stop` không chạy vì H7. Không có coding changes nên quy tắc restart sau sửa code không áp dụng. Health pass trong phiên smoke không được diễn đạt thành ứng dụng đã sẵn sàng dùng thật. Trạng thái cleanup runtime audit được ghi trong kết quả cuối dưới đây.

- Restart backend audit đã xác minh ownership theo executable path/command/parent tree: wrapper/worker **105912/108204** được thay bằng **48232/105648**, process mới khởi động **03/10/2026 08:20:13 UTC+7**. Backend health sau replacement: **HTTP 200, status=ok, database=connected**; frontend production runtime: **HTTP 200**. Không ngắt task thật của user; chỉ dùng database audit và scheduler disabled.
- Sau smoke/restart validation, đã dừng đúng backend/frontend audit và child processes. Final state: **127.0.0.1:8000 và :3000 không còn listener**; không để app chạy với copy DB mà user có thể nhầm là dữ liệu thật.
- Kiểm tra cuối: **70 source/config/test/launcher files** khớp hash checkpoint, không có thay đổi source trong bước verification/cleanup; original DB vẫn **20 products/50 snapshots**, integrity=`ok`.
- Chỉ artifact report này được thêm vào project; test scripts/logs/DB audit ở `%TEMP%`, build/cache do validation tạo. Các evidence reproduction chính đã được ghi inline để report không phụ thuộc lifetime của thư mục tạm.


## Remediation checkpoint — 03/10/2026

Sau yêu cầu sửa lỗi của user, bản sửa C1/H1–H8/M1–M3 đã triển khai, test và restart runtime chuẩn. Xem [FIX_REPORT.md](FIX_REPORT.md) cho kết quả hiện tại và bằng chứng. Nội dung audit phía trên mô tả trạng thái trước sửa. Production acceptance vẫn NOT READY vì chưa xác minh dữ liệu Shop thật qua nhiều chu kỳ.
