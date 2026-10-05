# Production review remediation plan

Updated: 2026-10-05. Scope: C1, H1–H8, M1–M3 in FINAL_REVIEW.md, Phase 2, Phase 3, Phase 4, and release qualification.

## Baseline Validation: PASS

- [x] Back up SQLite and quarantine contaminated legacy products without deleting history.
- [x] Upgrade patched Next.js; validate dependency compatibility and production build.
- [x] Enforce verified Shop identity, nullable metrics, public HTTPS destinations and loopback runtime.
- [x] Correct time coverage, stale metrics and scheduled tracked-product refresh.
- [x] Correct keyword routing, partial/failed runs, transaction rollback and restart recovery.
- [x] Repair UI polling, visible errors, stale-response handling and UTC serialization.
- [x] Replace broad process termination with project ownership checks and hidden standard launcher.
- [x] Run targeted backend/frontend tests, lint, typecheck and build.
- [x] Add user-operated local session setup and scoped reuse, with availability UI and security tests.
- [x] Collect user-provided VN PDPs, validate identity/metrics, repeated upsert, tracked refresh, charts and restart persistence (8 verified live products in tracking with 74 snapshots).
- [x] Filter history by real timestamp ranges, explain empty ranges, preserve zero values, add detail retry.
- [x] Exclude cumulative-only products from trend momentum score/rank until a recent measured sales/review signal exists.

## Production / Release Acceptance Gates

- [x] **Gate 1: Live validation across several verified TikTok Shop VN products**
  - **Status: VALIDATED / PASS.**
  - **Evidence:** 8 verified live TikTok Shop VN products successfully ingested, parsed, and tracked in database (Products 21–28) across 5 distinct categories:
    - Product 21 (`1737036472084039604`): Chuối Sấy Mè (BĂNG BĂNG FOOD) — 17 real snapshots across >30 hours.
    - Product 22 (`1729741207556360748`): Khay Dụng Cụ Đeo Lens (huynhanh.lens) — sold 304,771.
    - Product 23 (`1733672972590221277`): Cần Câu Tay 3H Trúc Xanh (King Câu Fishing) — sold 9,949.
    - Product 24 (`1735676446643881779`): Combo 10 Đôi Tất Nữ (Thuỳy Linh Shop) — sold 32,175.
    - Product 25 (`1730993952816662577`): Bộ 5 Thảm Lau Chân (Gia Dụng Xanh) — sold 143,913.
    - Product 26 (`1730929283006368543`): COMBO 10 bịch khăn giấy Sipiao (Sipiao Facial Tissue) — sold 1,256,839.
    - Product 27 (`1729639161540807174`): Combo 3 túi Khăn vải khô Ecobi (EcoWipes Việt Nam) — sold 203,329.
    - Product 28 (`1729610871527213560`): Đậu Phộng Rang Tỏi Ớt (Thực Phẩm Sạch.NFood) — sold 134,217.
    Canonical product identities verified; shop names, categories, prices, ratings, and sold counts accurately captured.

- [ ] **Gate 2: Automatic broad home/category discovery**
  - **Status: DEFERRED for this release (known external-platform limitation).**
  - **Project Control Decision:** Automatic broad discovery through TikTok Shop VN home/category routes is NOT required for release acceptance. The supported release workflow is user-assisted / URL-input tracking of TikTok Shop VN PDPs.
  - **Why Deferred & Live Evidence:** Both home routes (`https://shop.tiktok.com/vn`) and category routes (e.g. `https://shop.tiktok.com/vn/c/food-beverages/700437`) consistently return HTTP/HTML TikTok Security Check challenges under normal permitted browser and session reuse without CAPTCHA solver (reproduced in crawl runs 35 and prior).
  - **Scope Boundary:** Implementing CAPTCHA solving, anti-bot bypass, stealth circumvention, or fabricated discovery data is strictly outside the project architecture and release scope.
  - **Future Roadmap:** Automatic broad discovery is preserved in project history as deferred functionality and may be revisited in a later explicitly planned phase.

- [x] **Gate 3: Live multi-product + analytics validation**
  - **Status: VALIDATED for release under revised acceptance criteria.**
  - **Previous Acceptance Criterion:** "24h/7d real observation history across multiple products".
  - **Project Control Revision:** Project Control intentionally revised the release acceptance strategy to avoid making release completion depend solely on seven days of elapsed wall-clock time. The revised criterion is: *"Live multi-product collection and real 24h behavior validated; 7-day analytics behavior deterministically verified by automated tests. Real 7-day field observation is deferred post-release operational validation."*
  - **Sub-gate Evaluation:**
    - **Real multi-product ingestion: PASS.** 8 verified live TikTok Shop VN products (Products 21–28) tracked with canonical shop and product metadata across 5 categories with 74 snapshots in `affiliate.db`.
    - **Real 24h behavior: PASS.** Product 21 (`1737036472084039604`) has >30 hours of continuous real observation across 17 snapshots (sales 12,808 -> 12,960; measured 24h delta +106 units with `velocity_is_estimated = false`).
    - **Deterministic 7d analytics tests: PASS.** Deterministic automated test suite (`backend/tests/test_analytics.py`) proves all 10 analytics invariants using isolated in-memory fixtures: exact/near 7d deltas within 4h bounded tolerance, nullability for insufficient history (<164h), bounded tolerance candidate selection, real elapsed time semantics, preservation of zero values, nullability of missing metrics, stale observation suppression, acceleration requiring distinct intervals, exclusion of cumulative-only data from momentum scores, and strict quarantine exclusion across all analytics/trend queries.
    - **Real 7-day field observation: DEFERRED post-release operational validation.** Live 7-day field observation is preserved as a deferred operational validation item, NOT fabricated or claimed as completed evidence. Real SQLite database contains zero synthetic or backdated records.

- [x] **Gate 4: Review and classification of seven high development-dependency findings**
  - **Status: RESOLVED / CLASSIFIED as non-blocking development-tooling debt.**
  - **Current State:** Deep audit research confirmed 0 vulnerabilities in production (`npm audit --omit=dev` = 0). All 7 high audit findings originate from `GHSA-vfj7-8cjw-p6xm` on `braces` (AST stack-overflow DoS on untrusted glob inputs), pulled as a transitive dependency of `tailwindcss@3.4.19` (satisfying `^3.4.1` in `package.json`) and `eslint-config-next@15.5.27` in devDependencies. No patched release of `braces` exists in npm registry (3.0.3 is latest). Attack surface is completely unreachable in local runtime (no untrusted user globs processed by CLI dev tools). Classified as non-blocking development-tooling debt awaiting upstream release.

- [x] **Gate 5: Long-duration and restart/soak validation**
  - **Status: VALIDATED.**
  - **Current State:** Process management verified with WMI detachment ensuring Backend FastAPI (Port 8000) and Frontend Next.js (Port 3000) persist across subshell boundaries and pass health checks. Single active crawl reservation invariant verified (concurrent crawl rejected with HTTP 409 Conflict). Startup reconciliation of abandoned crawls verified (interrupted crawl run 33 reconciled to `partial` with explanation message persisted while retaining committed snapshots). Scheduled refresh continuity verified (APScheduler jobs active at 08:00, 12:00, 16:00, 20:00, 00:00). SQLite database integrity verified (`PRAGMA integrity_check` = `ok`).

All release acceptance criteria are now validated under the revised acceptance criteria. Release phase status: COMPLETE WITH DEFERRED ITEMS (Gate 2 broad discovery deferred; Gate 3 real 7-day field observation deferred post-release operational validation). No executable packaging has been performed.

---

## Phase 2 — Trend Quality & Decision Support: ACCEPTED / COMPLETE

- **Formal Phase 2 Plan:** [`PHASE_2_PLAN.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/PHASE_2_PLAN.md)
- **Verified Research:** [`research/PHASE_2_TREND_QUALITY_RESEARCH.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/research/PHASE_2_TREND_QUALITY_RESEARCH.md)
- **Status:** **VALIDATED & ACCEPTED**
  - [x] Authoritative Trend Score preserved (40% sales velocity 24h, 25% sales acceleration, 15% review velocity, 10% freshness, 10% rating).
  - [x] Trend evidence and confidence model (low/medium/high) orthogonal to score.
  - [x] Estimated intervals cannot escalate to high confidence.
  - [x] Deterministic "Why trending?" reasons rendered by component contribution.
  - [x] Category filtering implemented and verified in backend query, API parameters, and frontend UI.
  - [x] Filters for trend state (eligible, stale, insufficient_signal, all) and evidence (measured_only, confidence).
  - [x] Multi-attribute sorting (`trend_score`, `sales_velocity`, `sales_delta`, `review_delta`, `freshness`) with deterministic null-last ordering and stable tie-break on `product_id`.
  - [x] Zero schema migration: all derived at read time from existing snapshots.
  - [x] Zero N+1 query regression: single bulk query with `joinedload(Product.snapshots)` utilizing composite index `ix_product_snapshots_product_captured`.
  - [x] Full validation suite passing: 103 backend pytest, 18 frontend Vitest, clean typecheck, clean lint, clean Next.js production build, clean healthcheck, SQLite integrity and foreign key checks clean.
  - [x] Architecture updated: Section "Nguyên tắc Phân tích & Chất lượng Xu hướng" in `ARCHITECTURE.md` updated with 7 durable analytics invariants.

---

## Phase 3 — Monitoring, Watchlists & Alerts: ACCEPTED / COMPLETE

- **Formal Phase 3 Plan:** [`PHASE_3_PLAN.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/PHASE_3_PLAN.md)
- **Verified Research:** [`research/PHASE_3_MONITORING_WATCHLISTS_ALERTS_RESEARCH.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/research/PHASE_3_MONITORING_WATCHLISTS_ALERTS_RESEARCH.md)
- **ADR-003:** [`docs/architecture/ADR-003.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/docs/architecture/ADR-003.md)
- **Status:** **VALIDATED & ACCEPTED**
- **Project Control Completion Decision (2026-10-05):** **COMPLETE**. The Phase 3 completion report and remediation/manual-QA evidence were reviewed and accepted. Project-state reconciliation is complete for Phase 3; Phase 4 has not been selected or started.
  - [x] Watchlist backed by durable `watchlist_items` table with `product_id`, `created_at`, `notes`.
  - [x] One-time idempotent legacy backfill with durable marker `legacy_tracked_backfill_completed` in `system_metadata`. Empty watchlists are never repopulated on subsequent restarts.
  - [x] Watch / Unwatch actions implemented without data loss (historical products, snapshots, rules, and events preserved).
  - [x] Watchlist membership is authoritative source for scheduled refresh; user-submitted PDPs automatically become watched.
  - [x] Three product-scoped alert rules: `sales_velocity_above`, `trend_score_above`, `price_change_pct`.
  - [x] Strict price rule semantics: `direction ∈ {'up', 'down', 'either'}`, threshold > 0, price calculation on non-null/positive prices, emitted events persist `actual_direction`, price alerts never described as "trending".
  - [x] Cooldown semantics: Default 0 minutes, suppress only when `trigger_time - last_triggered_at < cooldown_duration`, exact boundary eligible, suppressed crossings advance state to met, cooldown expiry alone never emits events.
  - [x] Decoupled post-commit alert evaluator in separate transaction; alert failure never rolls back ingestion; atomic event + cursor commit.
  - [x] Synchronous startup order: `schema/bootstrap/backfill` → `crawl reconciliation` → `alert catch-up` → `scheduler start` → `application ready`.
  - [x] Deterministic Phase 2 analytics reuse bounded to 172h; zero N+1 queries; latency < 200ms regression gate on 200-product/5,000-snapshot synthetic dataset.
  - [x] Minimal Watchlist/rule/alert frontend (watchlist tab, star watch/unwatch toggle, alert setup modal, notification center bell with unread badge).
  - [x] ADR-003 created and ARCHITECTURE.md updated with Phase 3 invariants.
  - [x] Validation suites passing: 124 backend pytest tests (100% PASS), 26 frontend Vitest tests (100% PASS), `tsc --noEmit` clean, ESLint clean, Next.js build clean, SQLite integrity and foreign key checks clean.

---

## Phase 4 — Reporting & Productization: COMPLETE / ACCEPTED

- **Formal Phase 4 Plan:** [`PHASE_4_PLAN.md`](PHASE_4_PLAN.md)
- **Verified Research:** [`research/PHASE_4_REPORTING_PRODUCTIZATION_RESEARCH.md`](research/PHASE_4_REPORTING_PRODUCTIZATION_RESEARCH.md)
- **ADR-004:** [`docs/architecture/ADR-004.md`](docs/architecture/ADR-004.md)
- **Status:** **COMPLETE / ACCEPTED**
- **Project Control Completion Decision (2026-10-05):** **COMPLETE**. All Phase 4 acceptance criteria (P4-AC-01 through P4-AC-35) verified and accepted. Code/runtime QA: **PASS**. Source-control handoff: **COMPLETE**. Qualified source revision: `4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`. Release readiness: **READY WITH DOCUMENTED NON-BLOCKING ISSUES**. Supported release boundary: **Windows / local / source-based**. Remote publication: qualified revision has not been pushed to `origin/main`. Phase 5: **NOT SELECTED / NOT STARTED**.
  - [x] Deterministic CSV export engine with UTF-8 BOM (`\ufeff`) across Product History, Trends, Watchlist, and Alert Events.
  - [x] Product History export (`GET /api/products/{id}/export-history`): Supports exactly `24h`, `7d`, `30d`. Rejects `all` and invalid ranges with structured 400. Keyset streaming `(captured_at, id) ASC` with membership freeze (`as_of_utc`, `max_snapshot_id_at_start`, lower bound).
  - [x] Trends & Watchlist CSV export mirrors active query results (respecting filters, order, limit, offset) with zero extra per-row metadata queries.
  - [x] Alert History export (`GET /api/alerts/events/export`): Keyset streaming `(created_at, id) DESC` with membership freeze (`max_event_id_at_start`).
  - [x] Short-lived database sessions per batch, preventing transaction locks across downloads and allowing concurrent writer commits.
  - [x] Hot SQLite backup engine via native `sqlite3.Connection.backup()` to `backend/.local/backups/tinix-affiliate-v1-YYYYMMDDTHHMMSS.ffffffZ.sqlite3`, excluding non-DB artifacts and session files.
  - [x] Candidate validation: SQLite header, dynamic schema derivation from SQLAlchemy `Base.metadata`, compatibility marker `portable_backup_compatibility_version = "1"`, `PRAGMA integrity_check`, and `PRAGMA foreign_key_check`.
  - [x] Offline launcher-owned restore (`RESTORE.bat`, `scripts/restore.ps1`) with transaction manifest `backend/.local/restore/manifest.json` and Pre-Start Manifest Guard in `scripts/start_services.ps1`.
  - [x] Disaster recovery: `RESTORE.bat --recover` safely handles interrupted restore attempts (ABORTED prior to replacement; ROLLED_BACK at/after replacement).
  - [x] Safe allowlisted system diagnostics (`GET /api/diagnostics`) with zero credential/cookie/token leaks, and explicit on-demand deep check (`GET /api/diagnostics/deep`).
  - [x] Frontend UI: Export CSV buttons on Trends, Watchlist, Product History (with "Tất cả" locked/explained), Alert Center, and System Diagnostics modal.
  - [x] Runtime `PRAGMA foreign_keys = OFF` preserved for cross-phase consistency.
  - [x] Validation suites passing: 153 backend pytest tests (100% PASS), 35 frontend Vitest tests (100% PASS), `tsc --noEmit` clean, ESLint clean, Next.js production build clean, live healthcheck clean.
  - [x] Preserved technical debt and deferred scope recorded consistently (broad discovery deferred, real 7-day field observation deferred, browser DB transfer deferred, executable packaging deferred).

---

## Project Control Reconciliation & Release Qualification

- **Project Control Final QA Decision (2026-10-05):** `READY WITH DOCUMENTED NON-BLOCKING ISSUES`
- **Phase 4 Status:** `COMPLETE / ACCEPTED` (all acceptance criteria P4-AC-01 through P4-AC-35 validated and accepted)
- **QA Code & Runtime Qualification:** `PASS` (153 backend pytest tests PASS, 35 frontend Vitest tests PASS, TypeScript typecheck clean, ESLint clean, Next.js production build clean, live healthcheck PASS, SQLite integrity and foreign-key checks PASS)
- **Source-Control Handoff:** `COMPLETE`
- **Qualified Source Revision:** `4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`
- **Release Readiness:** `READY WITH DOCUMENTED NON-BLOCKING ISSUES`
- **Supported Release Boundary:** `Windows / local / source-based`
- **Remote Publication:** Qualified revision has not been pushed to `origin/main` (remote publication is a separate explicitly authorized action).
- **Phase 5 Status:** `NOT SELECTED / NOT STARTED`
- **Preserved Accepted Non-Blocking Debt:**
  - Dev-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`) in devDependencies (`tailwindcss@3.4.19` and `eslint-config-next@15.5.27`, zero production runtime reachability).
  - `StarletteDeprecationWarning` during test execution (`httpx` integration with `starlette.testclient`).
  - Runtime `PRAGMA foreign_keys = 0` (`OFF`) preserved for cross-phase operational stability.
- **Preserved Accepted Deferred Scope:**
  - Broad automatic discovery / CAPTCHA bypass deferred (TikTok Security Check challenge; user-assisted PDP tracking is primary workflow).
  - Real 7-day field observation deferred (post-release operational validation; 7d analytics behavior proven via deterministic test fixtures).
  - Browser DB transfer deferred (operator offline launcher CLI `BACKUP.bat` / `RESTORE.bat` only).
  - Cross-version database migrations deferred (same-version restore enforced via compatibility marker "1").
  - TikTok session portability deferred (host-bound local session isolated from backups/exports).
  - Executable/installer packaging deferred (supported boundary is local Windows source-based runtime).
  - All other previously documented deferred items.
