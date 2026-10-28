# Project status

Updated: 2026-10-07. Phase 6 — Affiliate Economics & Profitability Intelligence: COMPLETE / ACCEPTED (RELEASE QUALIFIED). Release Readiness: READY WITH DOCUMENTED NON-BLOCKING ISSUES. Qualified Source: 63bf47a329ecb78631165a2d677119ff39e105e4. Backup Compatibility: "3". Phase 6 Lifecycle: CLOSED. Phase 7 corrected package independently reviewed and approved; implementation authorized under `P7-AC-01`–`P7-AC-28`. See [`PROJECT_CONTROL_PHASE7_PACKAGE_APPROVED.md`](PROJECT_CONTROL_PHASE7_PACKAGE_APPROVED.md).

## Current phase and release state

- **Project lifecycle:** Closed for the supported Windows/local/source runtime. Current qualification and evidence: [`PROJECT_FINAL_RELEASE_REPORT.md`](PROJECT_FINAL_RELEASE_REPORT.md).
- **Phase 7 — TikTok Content Signals:** `COMPLETE / ACCEPTED WITH DOCUMENTED DEFERRED ITEM`; all 28 criteria are classified in [`PHASE_7_COMPLETION_REPORT.md`](PHASE_7_COMPLETION_REPORT.md). P7-AC-19 metric-observation ingestion is deferred because no validated public source provides the counters; values remain null.
- **Project Control acceptance:** [`PROJECT_CONTROL_PHASE7_COMPLETION_ACCEPTED.md`](PROJECT_CONTROL_PHASE7_COMPLETION_ACCEPTED.md).
- **Portable backup compatibility:** `"4"`; live database integrity and foreign-key checks pass.
- **Release assessment:** `READY WITH DOCUMENTED LIMITATIONS` for Windows / local / source-based runtime. Frontend `npm audit` (2026-10-27, after `next` bump to `15.5.28` and dev-tooling audit fix): 0 vulnerabilities (full and `--omit=dev`); `pip-audit` is not installed.
- **Checkpoint 2026-10-27:** Frontend migrated to Tailwind CSS v4 (`@tailwindcss/postcss`, CSS-based config; `tailwind.config.ts` removed) and ESLint flat config (`jsx-a11y`, `react`, `react-hooks`; `eslint-config-next` removed), with label/`id` accessibility fixes. `next` bumped `15.5.27` → `15.5.28` to fix critical advisories (GHSA-2464-fhr4-w9xw, GHSA-p3m5-59mp-jv5r). Verified: `tsc --noEmit` PASS, `npm run lint` PASS, Vitest 53/53 PASS, `npm run build` PASS. Next.js lint rules restored via `@next/eslint-plugin-next@15.5.28` (`core-web-vitals`); `npm run lint` PASS with rules active. Dev-tooling audit fix applied (`vite` 8.3.5, `undici` 8.12.3, non-breaking): full `npm audit` 0 vulnerabilities, production 0. Next.js recommended lint rules enabled in addition to `core-web-vitals`, with `@next/next/no-img-element` kept off per the existing project convention; lint reports 0 errors and 0 warnings.
- **Phase 8:** Not opened. No required unapproved capability remains; optional or externally dependent items await a future product decision. See [`PROJECT_CONTROL_PHASE8_SELECTION.md`](PROJECT_CONTROL_PHASE8_SELECTION.md).
- **Runtime (2026-10-27):** project-owned backend and frontend restarted via `scripts/start_services.ps1`; `health_check.ps1` reports Backend `/api/health` OK (`status: ok`, DB connected, revision `d4cb99376205fa38`) and Frontend `:3000` HTTP 200. Port `8000` conflict resolved by stopping the unrelated `Tinix-Media-Crawler` process (PID 39904) at the owner's explicit direction. Crawler backend has since moved to port `8100` (crawler commit `0538518`) and runs in parallel with this project (verified 2026-10-28: backend `8000` and frontend `3000` healthy; crawler `8100` HTTP 200). Backend was restarted 2026-10-28 via `start_services.ps1 -Target Backend` and confirmed running from `backend/.venv`. Autostart scheduled task `TinixTrendHunter-Autostart` configured (logon and resume triggers; see `DEVELOPMENT_WORKFLOW.md` section 17); resume trigger not yet verified by a real sleep/resume cycle.
- **Publication and packaging:** not pushed; no executable/installer was requested or generated.

Phase 6 Status: **Phase 6 — Affiliate Economics & Profitability Intelligence** (`COMPLETE / ACCEPTED`; Research: `CLOSED / ACCEPTED`; Architecture: `ADR-005 ACCEPTED`; Plan: `APPROVED` via [`PHASE_6_PLAN.md`](PHASE_6_PLAN.md); 42 acceptance criteria accepted; source-release qualification and lifecycle closure remain historical at revision `63bf47a329ecb78631165a2d677119ff39e105e4`). Phase 7's corrected research, ADR-006, and [`PHASE_7_PLAN.md`](PHASE_7_PLAN.md) were approved and have since been implemented and accepted; see [`PROJECT_CONTROL_PHASE7_COMPLETION_ACCEPTED.md`](PROJECT_CONTROL_PHASE7_COMPLETION_ACCEPTED.md) and [`PHASE_7_COMPLETION_REPORT.md`](PHASE_7_COMPLETION_REPORT.md). The earlier Phase 7 package review remains the record of authorization, not the current implementation status. Current compatibility is `"4"`; current lifecycle and qualification are recorded above and in [`PROJECT_FINAL_RELEASE_REPORT.md`](PROJECT_FINAL_RELEASE_REPORT.md). Supported release boundary is Windows / local / source-based runtime. Standalone executable/installer packaging remains deferred. Remote publication was not performed.


> **Historical record:** The sections below are point-in-time notes from earlier phases and may be superseded. Where they conflict with "Current phase and release state" above, the current state governs.

## Implemented and validated (historical)

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
- Dependency audit & security assessment: Current repository-aware QA identified **1 High `source-map-js` advisory** in the production dependency graph (`GHSA-68fv-2mgg-jv7q`). Assessment: reaches the dependency graph through Next/PostCSS/CSS-build tooling; QA found no known path from untrusted runtime input to the vulnerable behavior; presently assessed as build-time-only / not production-runtime reachable; no functional or security exploit was demonstrated against the supported local runtime; classified as non-blocking dependency/security debt for this release (historical claim of 0 production vulnerabilities superseded). Additionally, devDependencies contain 7 high findings from `GHSA-vfj7-8cjw-p6xm` on `braces` (AST stack-overflow DoS on untrusted glob inputs), required transitively by `tailwindcss@3.4.19` and `eslint-config-next@15.5.27`; runtime reachability is zero; preserved as non-blocking development debt.
- WMI process management verified: backend (FastAPI :8000) and frontend (Next.js :3000) run detached, persist across shell/task boundaries, and pass health checks.

## Validation and runtime (historical, as of Phase 6/7 closure)
 
- Backend: **223 pytest PASS**, 5 warnings (including StarletteDeprecationWarning).
- Frontend: **52 tests PASS** across 9 test suites in Vitest.
- TypeScript: `npx tsc --noEmit` PASS (clean, 0 errors).
- Lint: `npm run lint` (`eslint src`) PASS (clean, 0 errors, 0 warnings).
- Production build: `npm run build` (`next build`) PASS (compiled successfully in 2.7s, all static/dynamic routes generated).
- Standard health check: `healthcheck.bat` returns Backend FastAPI (Port 8000) Status: ok, DB: connected, Region: VN; Frontend Next.js (Port 3000): HTTP 200 OK.
- Database integrity: `PRAGMA integrity_check` = `[('ok',)]`; `PRAGMA foreign_key_check` = `[]`; 0 running crawls; 8 watchlist items, 2 system metadata markers (`portable_backup_compatibility_version = "3"`).
- Performance Benchmarks: Collection members 1.22ms best / 3.34ms worst (2 SQL queries); 5-Product compare 7.44ms best / 11.11ms worst (4 SQL queries) — zero N+1 queries, well below the 200ms hard gate and 50ms stretch target.
- Backup & Recovery: `BACKUP.bat` produces valid `tinix-affiliate-v3-*.sqlite3` online backups (binary SQLite format under ADR-004); compatibility "3" active.
 
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
  - Operator hot SQLite online backup via `BACKUP.bat` to `backend/.local/backups/`.
  - Staging pre-publish validation: SQLite header, dynamic schema derivation from SQLAlchemy `Base.metadata`, compatibility marker, `integrity_check`, and `foreign_key_check`.
  - Collision rejection preventing silent file overwrites.
  - Host-bound session security: `backend/.local/tiktok-session.json` strictly excluded from backups and exports.
  - Offline launcher-owned restore (`RESTORE.bat`) eliminating Windows file locking (`WinError 32`).
  - Pre-quiescence candidate validation before stopping services.
  - Pre-restore safety backup created with SQLite online backup engine and validated before live replacement.
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
- **Phase 5 — Opportunity Workspace:** COMPLETE / ACCEPTED across all 36 criteria (`P5-AC-01` through `P5-AC-36`):
  - Collections domain separated from Watchlist: `WatchlistItem` remains sole monitoring/refresh authority; Collections purely for decision organization; unwatch does not remove Collection membership/notes/status.
  - Additive database schema (`collections`, `collection_items`, `saved_views`) created via `Base.metadata.create_all()` without Alembic; dynamic schema validation derived from SQLAlchemy metadata; compatibility marker advanced `"1" → "2"`.
  - Portable backup compatibility version `"2"`: v1 backups rejected with structured HTTP 400 under unchanged same-version restore policy; v2 backup round-trip validated; in-place additive bootstrap validated.
  - Strictly typed V1 Saved Views: Trends (9 parameters) and Watchlist (7 parameters), applied in-memory (0 extra SQL queries), Watchlist apply resets `skip=0`.
  - Transient read-only Compare (2–5 products): single bulk backend request path, <=3 SQL queries with collections / <=2 without, shared single `as_of_utc`, bounded 7d alert summary, reuses authoritative Phase 2 analytics (no new score), sub-200ms benchmark verified (median 5.47ms, p95 5.62ms on 200 products / 5,000 snapshots).
  - Zero N+1 query budget verified: collection member list exactly 2 queries; compare <=3 queries; saved view apply 0 queries.
  - Frontend Opportunity Workspace: CollectionsWorkspace, AddToCollectionModal, CompareTray, CompareModal, SavedViewControl.
  - Operator documentation in `README.md` and architectural principles in `ARCHITECTURE.md` updated.
- **Phase 6 — Affiliate Economics & Profitability Intelligence:** COMPLETE / ACCEPTED (42 criteria `P6-AC-01` through `P6-AC-42` implemented, verified, and accepted):
  - Domain separation: Market evidence is strictly orthogonal to affiliate economics; Trend Score, confidence, momentum, and Why Trending are unaffected; `sales_velocity * commission` explicitly prohibited.
  - Rational calculation engine: Pure integer ratio $(2N + D)//(2D)$ for deterministic whole-VND round-half-up; ceiling division $(A+B-1)//B$ with exact rational numerator for break-even orders; strict null-propagation on unknown assumptions; zero calculations persisted in database.
  - Safe-integer validation contract: Rejects create/update/rebase payloads with HTTP 422 if any derived monetary integer exceeds `Number.MAX_SAFE_INTEGER = 9,007,199,254,740,991`, preserving distinct missing-value `None` semantics.
  - Persistent model & concurrency: Additive table `economics_scenarios` with composite unique index `UNIQUE(product_id, name)` and SQLite partial unique index `uq_economics_scenarios_product_default`; single-default invariant enforced across all concurrent races with `BEGIN IMMEDIATE` transactions and backoff retries; deterministic fallback promotion on delete.
  - Disaster recovery: Additive bootstrap dynamically advances compatibility `"2" → "3"`; legacy version 2 backups rejected with HTTP 400 under unchanged same-version restore semantics; `BACKUP.bat` produces valid v3 backups; host-bound credentials isolated.
  - Performance & query budgets: Batched default economics query adheres to zero N+1 budgets (Collections member list executes 2 queries; 5-Product compare executes 4 queries); sub-6ms latency benchmarks verified on 200 products / 5,000 snapshots (1.96ms Collections, 5.37ms Compare).
  - Frontend Workspace: Scenario management, default toggling, price proxy freezing/rebasing, unit economics cards, break-even callouts, campaign projections, and prominent commercial payout disclaimers in `ProductEconomicsSection.tsx`, `CollectionsWorkspace.tsx`, and `CompareModal.tsx`.

## Project Control reconciliation

- **Historical Release Qualification (Phase 4):** `READY WITH DOCUMENTED NON-BLOCKING ISSUES` (previous release qualification remains valid historical baseline for `4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`).
- **Phase 1 release remediation:** `COMPLETE WITH DEFERRED ITEMS`.
- **Phase 2 — Trend Quality & Decision Support:** `COMPLETE / ACCEPTED`.
- **Phase 3 — Monitoring, Watchlists & Alerts:** `COMPLETE / ACCEPTED`.
- **Phase 4 — Reporting & Productization:** `COMPLETE / ACCEPTED` (all criteria P4-AC-01 through P4-AC-35 accepted).
- **Phase 5 — Opportunity Workspace Implementation:** `COMPLETE / ACCEPTED` (authoritative plan: [`PHASE_5_PLAN.md`](PHASE_5_PLAN.md), all criteria `P5-AC-01` through `P5-AC-36` accepted; implementation acceptance remains valid).
- **Phase 5 Source-Release Qualification:** `READY WITH DOCUMENTED NON-BLOCKING ISSUES` (qualified repository revision: `6e218929e3ff3ae091da1582de48fa0582802d8a`; qualified product-code revision: `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98`; formal qualification record: [`PROJECT_CONTROL_PHASE5_RELEASE_QUALIFIED.md`](PROJECT_CONTROL_PHASE5_RELEASE_QUALIFIED.md)).
- **Phase 6 — Affiliate Economics Implementation:** `COMPLETE / ACCEPTED` (authoritative plan: [`PHASE_6_PLAN.md`](PHASE_6_PLAN.md); ADR-005 ACCEPTED; runtime backup compatibility `"3"`; accepted final remediation commit: `1bd1e5ddcb8999861ae43b9eb8775681f07edd6d`; completion reconciliation commit: `734b07be296c7613f9928b5e994a84525cd2135f`; final external completion decision: `Phase 6 = COMPLETE`; formal completion acceptance record: [`PROJECT_CONTROL_PHASE6_COMPLETION_ACCEPTED.md`](PROJECT_CONTROL_PHASE6_COMPLETION_ACCEPTED.md); completion report: [`PHASE_6_COMPLETION_REPORT.md`](PHASE_6_COMPLETION_REPORT.md)).
- **Phase 6 Source-Release Qualification:** `READY WITH DOCUMENTED NON-BLOCKING ISSUES` (source-release requalification completed post-remediation; qualified source revision: `63bf47a329ecb78631165a2d677119ff39e105e4`; formal qualification record: [`PROJECT_CONTROL_PHASE6_RELEASE_QUALIFIED.md`](PROJECT_CONTROL_PHASE6_RELEASE_QUALIFIED.md)).
- **Phase 6 Lifecycle State:** `PHASE 6 LIFECYCLE CLOSED` (Research accepted, ADR-005 accepted, implementation complete, completion accepted, completion state reconciled, source-release QA accepted, release state reconciled).
- **Lifecycle / Next Action:** Project lifecycle closed for the supported local source runtime; Phase 8 not opened. See [`PROJECT_CONTROL_PHASE8_SELECTION.md`](PROJECT_CONTROL_PHASE8_SELECTION.md).
- **Phase 7 Status:** `COMPLETE / ACCEPTED WITH DOCUMENTED DEFERRED ITEM`; see [`PROJECT_CONTROL_PHASE7_COMPLETION_ACCEPTED.md`](PROJECT_CONTROL_PHASE7_COMPLETION_ACCEPTED.md) and the 28-row [`PHASE_7_COMPLETION_REPORT.md`](PHASE_7_COMPLETION_REPORT.md).
- **Architecture & ADRs:** ADR-003 through ADR-006 active and accepted; compatibility marker is `"4"` after additive schema validation.
- **Repository QA & Runtime Qualification:** Backend 227/227 pytest PASS; Frontend 53/53 Vitest PASS; TypeScript, ESLint, and Next.js build clean. Live SQLite integrity is `ok` with no FK violations. Phase 7 video API uses four bounded queries; benchmark (200 products / 1,000 videos / 10,000 snapshots) median 5.034 ms, p95 6.957 ms, worst 36.883 ms. v3→v4 additive bootstrap, v4 backup/restore, and older-version backup rejection passed. After restart, backend health was HTTP 200 (`status=ok`, database connected, loaded revision `d4cb99376205fa38`) and frontend health was HTTP 200.
- **Current Release Qualification:** `READY WITH DOCUMENTED LIMITATIONS` for Windows / local / source-based runtime; see [`PROJECT_FINAL_RELEASE_REPORT.md`](PROJECT_FINAL_RELEASE_REPORT.md). A current npm audit could not run because no frontend lockfile exists; `pip-audit` is not installed.
- **Source-Control Handoff:** Phase 7 implementation revision `072f186430f60b33c8df99ba1236be1bdd31e838` is local and has not been pushed.
- **Supported Release Boundary:** `Windows / local / source-based runtime`. Standalone executable/installer packaging remains deferred.
- **Release Blockers:** No known functional or data-integrity blocker for the supported local source runtime. The dependency-advisory scan evidence limitation is recorded in the current release report.
- **Remote Publication:** Target revisions have not been pushed to `origin/main`; remote publication is a separate explicitly authorized action.
- **Preserved Accepted Non-Blocking Debt & Deviations:**
  - 1 High `source-map-js` advisory in the production dependency graph (`GHSA-68fv-2mgg-jv7q`): reaches dependency graph through Next/PostCSS/CSS-build tooling; QA found no known path from untrusted runtime input to the vulnerable behavior; presently assessed as build-time-only / not production-runtime reachable; no functional or security exploit was demonstrated against the supported local runtime; classified as non-blocking dependency/security debt for this release.
  - Development-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`) in devDependencies (`tailwindcss@3.4.19` and `eslint-config-next@15.5.27`, zero production runtime reachability).
  - `StarletteDeprecationWarning` during test execution (`httpx` with `starlette.testclient`).
  - Runtime `PRAGMA foreign_keys = 0` (`OFF`) maintained for cross-phase stability.
  - Scratch-file cleanup deviation: five untracked conversational scratch `.txt` files deleted during implementation workspace cleanup; classification: unrelated cleanup deviation, zero production/runtime/test/config impact, no known release impact, no reconstruction required, no further remediation required.
  - QA evidence-quality notes:
    1. No explicit manual keyboard/accessibility checklist was supplied in final QA evidence (automated UI/acceptance coverage passed; no accessibility regression demonstrated; classified as evidence-quality gap, not release blocker).
    2. QA was described as observational, but live API checks created and then deleted temporary Collection and Saved View records (no source modification; no destructive restore; zero release-state impact; wording correction only).
- **Preserved Accepted Deferred Scope:**
  - Broad automatic discovery / CAPTCHA bypass deferred (TikTok Security Check challenge).
  - Real 7-day field observation deferred (post-release operational validation).
  - Browser DB transfer deferred (operator offline CLI only).
  - Cross-version database migrations deferred (same-version restore enforced via compatibility marker "3").
  - TikTok session portability deferred (host-bound local session isolated from backups).
  - Standalone executable packaging deferred (local Windows source-based runtime).
  - Phase 5 deferred items (tags/labels, collection archiving, custom workflow/status builder, tasks/kanban, persisted comparison sessions/history, compare charts, AI recommendations, URL deep-link sync, Saved View default/favorite).
  - Phase 6 deferred items (Creator Center/private dashboard scraping, official TikTok Shop Affiliate API/OAuth, automated commission rate syncing, multi-currency / non-VND, custom formula builder, line-item cost breakdown tables, commission history/audit tables).
  - All other previously documented deferred items.
