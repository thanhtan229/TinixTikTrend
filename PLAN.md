# Production review remediation plan

Updated: 2026-10-06. Scope: C1, H1–H8, M1–M3 in FINAL_REVIEW.md, Phase 2, Phase 3, Phase 4, Phase 5 completion, and Phase 5 release QA qualification state.

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

## Phase 5 — Opportunity Workspace: Collections, Saved Views & Product Compare: COMPLETE / ACCEPTED

- **Decision State:**
  - **Phase 5 Status:** `COMPLETE / ACCEPTED`
  - **Phase Name:** `Opportunity Workspace — Collections, Saved Views & Product Compare`
  - **Research Gate:** `CLOSED` (no additional research required before implementation)
  - **Authoritative Plan:** [`PHASE_5_PLAN.md`](PHASE_5_PLAN.md)
  - **Authoritative Acceptance Criteria Surface:** `P5-AC-01` through `P5-AC-36` (all 36 authoritative criteria accepted and passing)
  - **Plan Status:** `COMPLETE / ACCEPTED`
  - **Implementation Status:** `COMPLETE / ACCEPTED`
  - **ADR Requirement:** ADR-003 unchanged; ADR-004 semantics unchanged (`portable_backup_compatibility_version` advanced from `"1"` to `"2"`).
  - **Architecture Invariants:** `ARCHITECTURE.md` updated and active.
  - **Compatibility Version:** Advanced to `"2"`; same-version restore semantics strictly enforced.
  - **Release Qualification:** Previous Windows / local / source-based release qualification remains historical evidence (`4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`); independent Phase 5 release QA attempted but release qualification blocked solely by unavailable checkout in QA environment; retry requires repository-aware QA against revision `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98` or an explicitly reconciled descendant; no product/code blocker identified; no Phase 6 selected.

- **Implementation Validation Evidence:**
  - **Backend pytest:** `178 passed`, 1 StarletteDeprecationWarning (100% PASS).
  - **Frontend Vitest:** `46 passed` across 8 test suites (100% PASS).
  - **TypeScript:** `npx tsc --noEmit` PASS (clean).
  - **Lint:** `npm run lint` (`eslint src`) PASS (clean).
  - **Production build:** `npm run build` (`next build`) PASS (compiled successfully, 4 static/dynamic routes generated).
  - **Healthcheck:** `healthcheck.bat` PASS (FastAPI :8000 status: ok, database: connected, region: VN; Next.js :3000 HTTP 200 OK).
  - **SQLite Integrity & Foreign Keys:** `PRAGMA integrity_check` = `[('ok',)]`; `PRAGMA foreign_key_check` = `[]` clean.
  - **No Blocker:** Zero Phase 5 blockers remain.

- **Query Budgets & Performance Evidence:**
  - **Collection member list query budget:** Exactly `2` SQL queries in accepted evidence (Zero N+1).
  - **Compare query budget:** Exactly `3` SQL queries with collection context / `2` without collection context (Zero N+1, single bulk HTTP request).
  - **Compare benchmark (200 products / 5,000 snapshots):**
    - Median: `5.47ms`
    - p95/Max: `5.62ms`
    - Hard performance gate (`<200ms`): PASS
    - Research performance target (`<50ms`): PASS
  - **Saved View application:** Exactly `0` additional SavedView query/fetch path beyond the underlying table query.

- **Backup & In-Place Bootstrap Compatibility:**
  - **Portable backup compatibility version:** Advanced to `"2"`.
  - **Same-version restore policy:** Phase-4 / version-1 portable backups rejected with structured HTTP 400 under unchanged same-version restore policy prior to quiescence.
  - **Phase-5 / version-2 backup round-trip:** PASS (hot online backup via `BACKUP.bat`, schema verification, marker `"2"` verification, and full round-trip offline restore pass).
  - **In-place additive bootstrap:** PASS (`Base.metadata.create_all()` additively provisions `collections`, `collection_items`, `saved_views` without Alembic, preserving Phase 1–4 tables and data).

- **Frozen Architectural Boundaries:**
  - `WatchlistItem` remains the sole monitoring / scheduled-refresh authority.
  - Collections represent independent decision-organization state.
  - Collection membership never implies watch/unwatch.
  - Unwatch does not remove Collection membership, review status, or decision notes.
  - `WatchlistItem.notes` remains internal provenance.
  - User decision notes belong to `CollectionItem.notes`.
  - Baseline domain model: `Collection`, `CollectionItem`, `SavedView`, and transient read-only Compare.
  - CollectionItem status vocabulary: `new | reviewing | candidate | rejected`.
  - Product may belong to multiple Collections.
  - Compare accepts exactly 2–5 products, reuses authoritative Phase 2 analytics evaluated against a single request `as_of_utc`.
  - No new comparison score formulas, winners, or AI summaries.
  - Saved Views use strictly typed/versioned payloads (`trends` 9 parameters, `watchlist` 7 parameters).
  - Saved Views apply to existing component-local React state without URL sync; Watchlist apply resets `skip` to `0`.
  - Bounded query budgets and Zero N+1 strictly enforced.
  - `ARCHITECTURE.md` updated with Phase 5 principles.
  - Operator documentation in `README.md` updated with v2 backup/restore boundary and Opportunity Workspace usage.

- **Preserved Accepted Non-Blocking Technical Debt & Deviations:**
  - Development-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`) in devDependencies (`tailwindcss@3.4.19` and `eslint-config-next@15.5.27`, zero production runtime reachability).
  - `StarletteDeprecationWarning` during test execution (`httpx` integration with `starlette.testclient`).
  - Runtime connection `PRAGMA foreign_keys = 0` (`OFF`) preserved for cross-phase operational stability.
  - Scratch-file cleanup deviation: five untracked conversational scratch `.txt` files were deleted during implementation workspace cleanup; classification: unrelated cleanup deviation, zero production/runtime/test/config impact, no known release impact, no reconstruction required, no further remediation required.

- **Preserved Explicit Deferred & Out-of-Scope Items:**
  - Tags and arbitrary product labels.
  - Collection archive behavior.
  - Custom workflow/status builder.
  - Kanban/tasks/due dates/assignees.
  - Persisted comparison sessions and comparison history.
  - Compare charts in baseline.
  - AI recommendations and automated summaries.
  - New Trend Score formulas.
  - New alert-rule types.
  - Broad crawler/discovery expansion and CAPTCHA/anti-bot bypass.
  - Affiliate profitability calculation.
  - Browser/cloud sync and multi-user/cloud backend.
  - Standalone executable packaging.
  - Cross-version backup migration framework.
  - URL deep-link/filter synchronization.
  - Saved View default/favorite flags and future schema migration.
  *(These explicit deferred items do not downgrade Phase 5 from `COMPLETE / ACCEPTED`.)*

---

## Project Control Reconciliation & Release Qualification

- **Project Control Final QA Decision (Historical):** `READY WITH DOCUMENTED NON-BLOCKING ISSUES` (for baseline commit `4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`).
- **Phase 4 Status:** `COMPLETE / ACCEPTED` (all acceptance criteria P4-AC-01 through P4-AC-35 validated and accepted).
- **Phase 5 Implementation Status:** `COMPLETE / ACCEPTED` (authoritative plan: [`PHASE_5_PLAN.md`](PHASE_5_PLAN.md), authoritative acceptance criteria: `P5-AC-01` through `P5-AC-36` all accepted/passing; implementation acceptance remains valid).
- **Phase 5 Source-Release Qualification:** `BLOCKED / QA ENVIRONMENT UNAVAILABLE`. Independent release QA attempted, but release qualification is blocked solely by unavailable checkout in QA execution environment (lacking repository checkout and `.git` state). No product/code blocker identified; no Phase 5 regression demonstrated; no code remediation required; qualified revision from QA run: `NONE`; target revision remains `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98`; retry requires repository-aware QA against revision `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98` or an explicitly reconciled descendant. Record: [`PROJECT_CONTROL_PHASE5_QA_BLOCKED.md`](PROJECT_CONTROL_PHASE5_QA_BLOCKED.md).
- **Next Phase:** `NONE SELECTED` (Phase 6 is not selected / not started).
- **Architecture & ADRs:** ADR-003 and ADR-004 remain active (`portable_backup_compatibility_version` advanced to `"2"`); `ARCHITECTURE.md` updated; no new ADR required.
- **QA Code & Runtime Qualification:** Backend 178 pytest PASS, Frontend 46 Vitest PASS, TypeScript clean, ESLint clean, Next.js build clean, healthcheck clean, SQLite integrity and FK checks clean.
- **Source-Control Handoff:** In progress for Phase 5 QA retry; target revision `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98`.
- **Supported Release Boundary:** `Windows / local / source-based runtime`.
- **Remote Publication:** Remote publication is a separate explicitly authorized action; target revision has not been pushed to `origin/main`.
- **Preserved Accepted Non-Blocking Debt:**
  - Runtime `PRAGMA foreign_keys = 0` (`OFF`) maintained for cross-phase operational stability.
  - Development-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`) in devDependencies.
  - `StarletteDeprecationWarning` during test execution (`httpx` integration with `starlette.testclient`).
  - Scratch-file cleanup deviation (five untracked `.txt` scratch files cleaned up; no code/test/config impact).
- **Preserved Accepted Deferred Scope:**
  - Broad automatic discovery / CAPTCHA bypass deferred.
  - Real 7-day field observation deferred.
  - Browser DB transfer deferred (operator launcher CLI `BACKUP.bat` / `RESTORE.bat` only).
  - Cross-version database migrations deferred (same-version restore enforced via compatibility marker "2").
  - TikTok session portability deferred (host-bound local session isolated from backups/exports).
  - Standalone executable/installer packaging deferred (local Windows source-based runtime).
  - Phase 5 deferred items (tags, persisted compare, compare charts, AI recommendations, URL sync, collection archiving).
  - All other previously documented deferred items.
