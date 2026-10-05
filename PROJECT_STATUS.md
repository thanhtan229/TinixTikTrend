# Project status

Updated: 2026-10-05 18:45 UTC+7. Phase: Phase 4 — Reporting & Productization.

Phase 4 status: **COMPLETE / ACCEPTED**. Project Control final QA decision: **READY WITH DOCUMENTED NON-BLOCKING ISSUES**. All Phase 4 acceptance criteria (P4-AC-01 through P4-AC-35) are validated under the authoritative [`PHASE_4_PLAN.md`](PHASE_4_PLAN.md), [`research/PHASE_4_REPORTING_PRODUCTIZATION_RESEARCH.md`](research/PHASE_4_REPORTING_PRODUCTIZATION_RESEARCH.md), and [`docs/architecture/ADR-004.md`](docs/architecture/ADR-004.md). Reporting delivers deterministic UTF-8 BOM CSV exports across Trends, Watchlist, bounded Product History (24h/7d/30d), and Alert History with keyset streaming and request-start high-watermark membership freeze. Hot SQLite backups via native `sqlite3.Connection.backup()` are managed under `backend/.local/backups/` with pre-publish schema, marker, integrity, and foreign key verification. Launcher-owned offline restore (`RESTORE.bat`) is governed by transaction manifest `backend/.local/restore/manifest.json`, Pre-Start Manifest Guard, validated pre-restore safety backups, atomic database replacement, and automated rollback upon health check failure. Disaster recovery (`RESTORE.bat --recover`) deterministically resolves interrupted operations. System diagnostics (`/api/diagnostics`) strictly redacts credentials and session material with explicit on-demand deep checks. Full test suites pass cleanly (**153 backend pytest**, **35 frontend Vitest**), TypeScript typecheck clean, ESLint clean, Next.js production build clean, healthcheck clean, and live SQLite database integrity verified. Source-control handoff: **COMPLETE**. Qualified source revision: `4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`. Release readiness: **READY WITH DOCUMENTED NON-BLOCKING ISSUES**. The project is qualified for its supported **Windows / local / source-based runtime**. Remote publication is a separate explicitly authorized action; qualified revision has not been pushed to `origin/main`. No release blockers exist. Phase 5 status: **NOT SELECTED / NOT STARTED**. No executable has been packaged.


## Implemented and validated

- **Baseline validation: PASS.** Review findings C1, H1–H8 and M1–M3 remain addressed.
- **Gate 1 (Live validation across several verified VN PDPs): VALIDATED / PASS.** 8 verified live TikTok Shop VN products successfully ingested, parsed, and tracked in database (Products 21–28):
  - Product 21 (`1737036472084039604`): Chuối Sấy Mè (BĂNG BĂNG FOOD) — 17 snapshots across >30 hours.
  - Product 22 (`1729741207556360748`): Khay Dụng Cụ Đeo Lens (huynhanh.lens) — sold 304,771.
  - Product 23 (`1733672972590221277`): Cần Câu Tay 3H Trúc Xanh (King Câu Fishing) — sold 9,949.
  - Product 24 (`1735676446643881779`): Combo 10 Đôi Tất Nữ (Thuỳy Linh Shop) — sold 32,175.
  - Product 25 (`1730993952816662577`): Bộ 5 Thảm Lau Chân (Gia Dụng Xanh) — sold 143,913.
  - Product 26 (`1730929283006368543`): COMBO 10 bịch khăn giấy Sipiao (Sipiao Facial Tissue) — sold 1,256,839.
  - Product 27 (`1729639161540807174`): Combo 3 túi Khăn vải khô Ecobi (EcoWipes Việt Nam) — sold 203,329.
  - Product 28 (`1729610871527213560`): Đậu Phộng Rang Tỏi Ớt (Thực Phẩm Sạch.NFood) — sold 134,217.
- URL validation enhanced: `PRODUCT_PATH` in `backend/app/core/urls.py` supports product title slugs (`/(?:view/product|product|item|(?:vn|vi-vn|vi-VN)/pdp|pdp)/(?:[a-zA-Z0-9_\-]+/)?(\d+)/?$`), and `CrawlRequest.product_links` reports exact line numbers for any invalid URL.
- Live database integrity preserved: **28 products / 100 product snapshots / 20 quarantined legacy rows / 46 crawl runs**, SQLite integrity `ok`, foreign key check clean (`[]`), 0 running/orphan crawls, and zero fabricated/backdated historical records.
- Real 24h observation window achieved for Product 21: first seen 2026-10-03 09:35:28 UTC, latest observed 2026-10-04 16:05:44 UTC (>30.5 hours). Sold count moved 12,808 -> 12,960 (+152 total; +106 in the ~24h window). Review count rose 730 -> 750 (+20). Measured 24h sales velocity is 106.0 units/day (`velocity_is_estimated` cleanly false). 7d delta, acceleration, and commission rate remain cleanly null in live database.
- Deterministic 7-day analytics behavior proven: automated test suite (`backend/tests/test_analytics.py`) verifies all 10 invariants under isolated in-memory test fixtures without touching live data.
- Single crawl reservation invariant verified: concurrent crawl trigger rejected with HTTP 409 Conflict.
- Startup reconciliation verified: simulated abandoned crawl run 33 in `running` status was reconciled to `partial` upon restart with `finished_at` and explanation message persisted, preserving database integrity.
- Broad discovery tested & deferred: home route (`https://shop.tiktok.com/vn`) and category routes consistently return TikTok Security Check challenges under HTTP and Playwright session reuse without solver (reproduced on crawl run 35), confirming Gate 2 cannot pass without anti-bot bypass. CAPTCHA solving, anti-bot bypass, and fabricated discovery data are strictly outside architecture and release scope.
- Dependency research completed: `npm audit --omit=dev` confirms **0 vulnerabilities** in production. All 7 high findings stem from `GHSA-vfj7-8cjw-p6xm` on `braces` (AST stack-overflow DoS on untrusted glob inputs), required transitively by `tailwindcss@3.4.19` (declared as `^3.4.1` in `frontend/package.json`) and `eslint-config-next@15.5.27` in devDependencies. No patched release of `braces` exists in npm registry (3.0.3 is latest). Runtime reachability is zero. Classified as non-blocking development debt.
- WMI process management verified: backend (FastAPI :8000) and frontend (Next.js :3000) run detached, persist across shell/task boundaries, and pass health checks.

## Validation and runtime
 
- Backend: **153 pytest PASS**, 1 StarletteDeprecationWarning.
- Frontend: **35 tests PASS** across 7 test suites in Vitest.
- TypeScript: `npx tsc --noEmit` PASS (clean).
- Lint: `npm run lint` (`eslint src`) PASS (clean).
- Production build: `npm run build` (`next build`) PASS (compiled successfully, 4 static/dynamic routes generated).
- Standard health check: `healthcheck.bat` returns Backend FastAPI (Port 8000) Status: ok, DB: connected, Region: VN; Frontend Next.js (Port 3000): HTTP 200 OK.
- Database integrity: `PRAGMA integrity_check` = `[('ok',)]`; `PRAGMA foreign_key_check` = `[]`; 0 running crawls; 8 watchlist items, 2 system metadata markers.
 
## Acceptance gate summary
 
- **Phase 1 Release Acceptance Gates:** COMPLETE WITH DEFERRED ITEMS (Gate 1 PASS, Gate 2 DEFERRED, Gate 3 PASS under revised criteria, Gate 4 RESOLVED, Gate 5 PASS).
- **Phase 2 — Trend Quality & Decision Support:** VALIDATED / ACCEPTED across all 14 criteria.
- **Phase 3 — Monitoring, Watchlists & Alerts:** COMPLETE / ACCEPTED across all 18 criteria.
- **Phase 4 — Reporting & Productization:** COMPLETE / ACCEPTED across all 35 criteria (P4-AC-01 through P4-AC-35):
  - Deterministic CSV export engine with UTF-8 BOM (`\ufeff`) across Product History, Trends, Watchlist, and Alert Events.
  - Bounded Product History export (`24h`, `7d`, `30d`; `range=all` structured 400; UI disabled).
  - Keyset-streaming CSV generation with short-lived SQLite sessions and request-start high-watermark membership freeze.
  - Trends and Watchlist export mirroring active query result set without extra per-row metadata queries.
  - Persisted Alert History export in deterministic descending order.
  - Operator hot SQLite online backup via `BACKUP.bat` to `backend/.local/backups/tinix-affiliate-v1-YYYYMMDDTHHMMSS.ffffffZ.sqlite3`.
  - Staging pre-publish validation: SQLite header, dynamic schema derivation from SQLAlchemy `Base.metadata`, compatibility marker "1", `integrity_check`, and `foreign_key_check`.
  - Collision rejection preventing silent file overwrites.
  - Host-bound session security: `backend/.local/tiktok-session.json` strictly excluded from backups and exports.
  - Offline launcher-owned restore (`RESTORE.bat`) eliminating Windows file locking (`WinError 32`).
  - Pre-quiescence candidate validation before stopping services.
  - Pre-restore safety backup (`tinix-pre-restore-v1-*.sqlite3`) created with SQLite online backup engine and validated before live replacement.
  - Atomic database replacement with automated rollback on startup or health check failure.
  - Transaction manifest at `backend/.local/restore/manifest.json` with terminal states `COMPLETED`, `ROLLED_BACK`, `ABORTED`.
  - Pre-Start Manifest Guard blocking normal startup if restore is incomplete.
  - Crash recovery via `RESTORE.bat --recover` deterministically resolving interrupted restore attempts.
  - State preservation: Watchlist, Alert Rules, Alert Events, and cursors survive restore; alert catch-up remains idempotent.
  - Safe system diagnostics (`/api/diagnostics`) with allowlisted statistics and strict credential/session redaction.
  - On-demand explicit deep diagnostics (`/api/diagnostics/deep`).
  - Minimal frontend CSV export actions and System Diagnostics modal.
  - Runtime connection `PRAGMA foreign_keys = OFF` preserved for cross-phase stability.
  - Sub-200ms latency regression gate verified on 200-product/5,000-snapshot synthetic dataset (Trends ~117ms, Watchlist ~66ms; 1 query each).

## Project Control reconciliation

- **Project Control Final QA Decision:** `READY WITH DOCUMENTED NON-BLOCKING ISSUES`.
- **Phase 1 release remediation:** `COMPLETE WITH DEFERRED ITEMS`.
- **Phase 2 — Trend Quality & Decision Support:** `COMPLETE / ACCEPTED`.
- **Phase 3 — Monitoring, Watchlists & Alerts:** `COMPLETE / ACCEPTED`.
- **Phase 4 — Reporting & Productization:** `COMPLETE / ACCEPTED`.
- **Phase 4 acceptance criteria:** `P4-AC-01 through P4-AC-35 ACCEPTED / PASS`.
- **Architecture & ADRs:** ADR-003 and ADR-004 `ACCEPTED / ACTIVE`.
- **Repository QA & Runtime Qualification:** `PASS`.
- **Source-control handoff:** `COMPLETE`.
- **Qualified source revision:** `4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`.
- **Release readiness:** `READY WITH DOCUMENTED NON-BLOCKING ISSUES`.
- **Supported release boundary:** `Windows / local / source-based runtime`.
- **Release blockers:** None.
- **Remote publication:** Qualified revision has not been pushed to `origin/main`; remote publication is a separate explicitly authorized action.
- **Phase 5 status:** `NOT SELECTED / NOT STARTED`.
- **Preserved accepted non-blocking debt:**
  - Runtime `PRAGMA foreign_keys = 0` (`OFF`) maintained for cross-phase stability.
  - Development-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`) in devDependencies.
  - `StarletteDeprecationWarning` during test execution (`httpx` with `starlette.testclient`).
- **Preserved accepted deferred scope:**
  - Broad automatic discovery / CAPTCHA bypass deferred (TikTok Security Check challenge).
  - Real 7-day field observation deferred (post-release operational validation).
  - Browser DB transfer deferred (operator offline CLI only).
  - Cross-version database migrations deferred (same-version restore enforced).
  - TikTok session portability deferred (host-bound local session isolated from backups).
  - Standalone executable packaging deferred (local Windows source-based runtime).
  - All other previously documented deferred items.

