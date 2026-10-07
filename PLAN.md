# Production review remediation plan

Updated: 2026-10-06. Scope: C1, H1–H8, M1–M3 in FINAL_REVIEW.md, Phase 2, Phase 3, Phase 4, Phase 5 completion and release qualification, Phase 6 research acceptance, and ADR-005 architecture acceptance.

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

- [x] **Gate 4: Review and classification of seven high development-dependency findings & current dependency state**
  - **Status: RESOLVED / CLASSIFIED as non-blocking development-tooling and dependency debt.**
  - **Historical Baseline & Current Audit State:** Baseline remediation resolved critical dependencies. Under current repository-aware Phase 5 release QA, 1 High `source-map-js` advisory is present in the production dependency graph (`GHSA-68fv-2mgg-jv7q`), reaching via Next/PostCSS/CSS tooling; assessed as build-time-only / not production-runtime reachable with no exploit path demonstrated against the local runtime; classified as non-blocking dependency debt (superseding earlier claims of 0 production vulnerabilities). Additionally, 7 high audit findings from `GHSA-vfj7-8cjw-p6xm` on `braces` remain in devDependencies via `tailwindcss@3.4.19` (satisfying `^3.4.1` in `package.json`) and `eslint-config-next@15.5.27`; attack surface completely unreachable in local runtime; classified as non-blocking development-tooling debt awaiting upstream release.

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
  - **Release Qualification:** `READY WITH DOCUMENTED NON-BLOCKING ISSUES` for the supported `Windows / local / source-based runtime`. Project Control accepted the repository-aware QA report (decision record: [`PROJECT_CONTROL_PHASE5_RELEASE_QUALIFIED.md`](PROJECT_CONTROL_PHASE5_RELEASE_QUALIFIED.md)); prior QA-environment availability blocker closed (historical record: [`PROJECT_CONTROL_PHASE5_QA_BLOCKED.md`](PROJECT_CONTROL_PHASE5_QA_BLOCKED.md)); qualified repository revision: `6e218929e3ff3ae091da1582de48fa0582802d8a`; qualified product-code revision: `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98`; historical Phase 4 release baseline remains valid (`4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`); packaging remains deferred; Phase 6 selected subsequently for research.

- **Implementation Validation Evidence:**
  - **Backend pytest:** `178 passed` (focused Phase 5 suite `25/25` PASS), 1 StarletteDeprecationWarning (100% PASS).
  - **Frontend Vitest:** `46 passed` across 8 test suites (100% PASS).
  - **TypeScript:** `npx tsc --noEmit` PASS (clean).
  - **Lint:** `npm run lint` (`eslint src`) PASS (clean).
  - **Production build:** `npm run build` (`next build`) PASS (compiled successfully, 4 static/dynamic routes generated).
  - **Healthcheck:** `healthcheck.bat` PASS (FastAPI :8000 status: ok, database: connected, region: VN; Next.js :3000 HTTP 200 OK).
  - **SQLite Integrity & Foreign Keys:** `PRAGMA integrity_check` = `[('ok',)]`; `PRAGMA foreign_key_check` = `[]` clean.
  - **No Blocker:** Zero Phase 5 blockers remain. Prior QA environment availability blocker closed by repository-aware QA.

- **Query Budgets & Performance Evidence:**
  - **Collection member list query budget:** Exactly `2` SQL queries in accepted evidence (Zero N+1).
  - **Compare query budget:** Exactly `3` SQL queries with collection context / `2` without collection context (Zero N+1, single bulk HTTP request).
  - **Compare benchmark (200 products / 5,000 snapshots / 5-product compare):**
    - Best: `4.42ms`
    - Median: `5.14ms`
    - p95: `5.42ms`
    - Worst: `5.42ms`
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
  - 1 High `source-map-js` advisory in the production dependency graph (`GHSA-68fv-2mgg-jv7q`): reaches dependency graph through Next/PostCSS/CSS-build tooling; QA found no known path from untrusted runtime input to the vulnerable behavior; presently assessed as build-time-only / not production-runtime reachable; no functional or security exploit was demonstrated against the supported local runtime; classified as non-blocking dependency/security debt for this release (earlier claims of 0 production vulnerabilities superseded).
  - Development-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`) in devDependencies (`tailwindcss@3.4.19` and `eslint-config-next@15.5.27`, zero production runtime reachability).
  - `StarletteDeprecationWarning` during test execution (`httpx` integration with `starlette.testclient`).
  - Runtime connection `PRAGMA foreign_keys = 0` (`OFF`) preserved for cross-phase operational stability.
  - Scratch-file cleanup deviation: five untracked conversational scratch `.txt` files were deleted during implementation workspace cleanup; classification: unrelated cleanup deviation, zero production/runtime/test/config impact, no known release impact, no reconstruction required, no further remediation required.
  - QA evidence-quality notes:
    1. No explicit manual keyboard/accessibility checklist was supplied in final QA evidence (automated UI/acceptance coverage passed; no accessibility regression demonstrated; classified as evidence-quality gap, not release blocker).
    2. QA was described as observational, but live API checks created and then deleted temporary Collection and Saved View records (no source modification; no destructive restore; zero release-state impact; wording correction only).

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

## Phase 6 — Affiliate Economics & Profitability Intelligence: SELECTED / RESEARCH COMPLETE / ARCHITECTURE ACCEPTED

- **Decision State:**
  - **Phase 6 Status:** `SELECTED / RESEARCH COMPLETE / ARCHITECTURE ACCEPTED`
  - **Phase Name:** `Affiliate Economics & Profitability Intelligence`
  - **Selection Record:** [`PROJECT_CONTROL_PHASE6_SELECTION.md`](PROJECT_CONTROL_PHASE6_SELECTION.md)
  - **Authoritative Selection Commit:** `d97f00f7819e778954a76abe3605e1442ea4155d`
  - **Superseded Identifier Discrepancy:** Previously reported identifier `d97f00f9a25b16f398f658be424b94f1e58286ad` is superseded and corrected to `d97f00f7819e778954a76abe3605e1442ea4155d`.
  - **Research Gate:** `CLOSED / ACCEPTED`
  - **Research Artifact:** [`research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md`](research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md)
  - **Research Readiness:** `RESEARCH READY FOR PROJECT CONTROL`
  - **Research Acceptance Record:** [`PROJECT_CONTROL_PHASE6_RESEARCH_ACCEPTED.md`](PROJECT_CONTROL_PHASE6_RESEARCH_ACCEPTED.md)
  - **Product Recommendation:** `RECOMMEND WITH REVISED SCOPE — ACCEPTED`
  - **Selected MVP Direction:** `VND-only, manual-first Product Economics Scenarios`
  - **Architecture Gate:** `CLOSED / ACCEPTED`
  - **ADR-005 Status:** `ACCEPTED` ([`docs/architecture/ADR-005.md`](docs/architecture/ADR-005.md))
  - **ADR-005 Acceptance Record:** [`PROJECT_CONTROL_ADR005_ACCEPTED.md`](PROJECT_CONTROL_ADR005_ACCEPTED.md)
  - **Phase Plan Status:** `NOT YET APPROVED` (Phase 6 planning is now authorized to begin)
  - **Implementation Status:** `NOT AUTHORIZED`
  - **Acceptance Criteria:** `NONE DEFINED YET` (no Phase 6 acceptance criteria exist yet)
  - **Planning Authorization:** Phase 6 planning may now begin against the accepted research and accepted ADR-005. The future plan must strictly comply with ADR-005 and the accepted research artifact. Implementation remains NOT AUTHORIZED until the Phase 6 implementation plan is reviewed and approved by Project Control.

- **Accepted Revised Scope & Architectural Constraints:**
  - **MVP Product Direction:** VND-only, manual-first Product Economics Scenarios.
  - **Economics Isolation:** Economics remains strictly separate from Phase 2 Trend Score, trend evidence, and trend confidence. No blended trend-profit score.
  - **Attribution Boundary:** Product sold count and sales velocity must never be treated as affiliate attribution or creator earnings. Prohibited formula: `sales_velocity × commission_per_order` as "estimated affiliate earnings".
  - **Commission Authority:** Existing `ProductSnapshot.commission_rate` is market observation data only; it is not automatic economics authority. Authoritative rate is solely the explicit scenario assumption.
  - **Multiple Scenarios:** One `Product` may have multiple named economics scenarios.
  - **Default Invariants:** Zero scenarios means zero defaults. Whenever scenarios exist for a Product, exactly one committed default exists. First scenario auto-defaults. Default switching is atomic. Deleting the default while other scenarios remain deterministically promotes the oldest remaining scenario by `(created_at, id)`.
  - **Currency & Persistence:** VND-only; no multi-currency or FX engine. Scenario assumptions use integer whole-VND money values and integer basis points for commission (`10,000 bps = 100%`).
  - **Cost Structure:** Fixed campaign costs are sample cost, content production cost, and planned promotion spend. Variable cost per order remains separate. Unknown/null is not zero (missing values do not silently default to 0).
  - **Observed Price Proxy:** Observed Product price can only be explicitly copied and frozen as a labeled proxy with timestamp; it is never dynamically linked to fluctuating crawler observations.
  - **Calculation Authority:** Derived economics are calculated by one backend authority and are not persisted. No financial calculation or rounding authority in frontend.
  - **Workspace & Export Isolation:** Saved View V1 schemas remain frozen and unchanged. No economics alerts in MVP. Economics CSV is deferred.
  - **External Scope Boundary:** No official Affiliate API/OAuth integration in MVP; no private Creator Center scraping; no CAPTCHA bypass; no new third-party dependencies.

- **Accepted Numeric & Formula Policy:**
  - **Persisted Assumptions:**
    - Money = whole-VND integer;
    - Commission = integer basis points (`10,000 bps = 100%`).
  - **Backend Calculation Authority:** Derived formulas remain backend-authoritative.
  - **Key Derived Concepts:**
    - Estimated commission per attributable order: `commission_base_vnd × (commission_bps / 10000)`
    - Fixed campaign cost: `sample_cost_vnd + content_cost_vnd + ad_spend_vnd` (sum of non-null components)
    - Contribution per attributable order: `estimated_commission_per_order - variable_cost_per_order`
    - Break-even attributable orders: `ceil(fixed_campaign_cost / contribution_per_order)` when contribution > 0
    - Optional expected economics: Expected commission, expected contribution, and return on cost computed only when explicit user `expected_attributable_orders` exists.
  - **Prohibitions:** No sales-velocity earnings proxy; no attributable-order inference; no frontend financial calculation authority.

- **Persistence & Compatibility Direction:**
  - **Required Table:** Exactly one proposed table: `economics_scenarios`.
  - **No Additional MVP Tables:** No tables for cost line items, economics history, commission observations, formula definitions, or persisted derived results.
  - **Backup Compatibility Advance:** If implemented, portable backup compatibility must advance `"2" → "3"` under unchanged ADR-004 same-version restore semantics.
  - **Compatibility Rules:** v2 backup not silently restorable by v3 application; no cross-version migration in Phase 6; fresh v3 backup required after successful upgrade; additive `Base.metadata.create_all()` + dynamic schema verification pattern expected to be reused. Compatibility code is not modified in this reconciliation.

- **Performance & Query Planning Constraints:**
  - **Candidate Query Budgets:**
    - Product scenario list/economics: `<= 1` scenario query.
    - Collection member list with economics: `<= 3` SQL queries total.
    - Compare with economics (no Collection context): `<= 3` SQL queries total.
    - Compare with economics and Collection context: `<= 4` SQL queries total.
    - Zero N+1 strictly enforced.
  - **Regression Ceiling Recommendation:** `< 200ms` on relevant 200-product / 5,000-snapshot representative paths. `< 50ms` remains an optimization/research target, not yet a hard gate unless planning later explicitly adopts it.

- **Architecture Gate: ADR-005 Accepted:**
  - **Status:** `CLOSED / ACCEPTED`
  - **Authoritative ADR:** [`docs/architecture/ADR-005.md`](docs/architecture/ADR-005.md)
  - **ADR Title:** `ADR-005 — Affiliate economics assumptions, provenance, numeric semantics, and calculation authority`
  - **Decision Record:** [`PROJECT_CONTROL_ADR005_ACCEPTED.md`](PROJECT_CONTROL_ADR005_ACCEPTED.md)
  - **Accepted Invariants:**
    - Domain separation: Market evidence vs. user assumptions vs. derived economics.
    - Prohibition of sold-count / sales-velocity affiliate attribution.
    - Manual-first source strategy; crawler `ProductSnapshot.commission_rate` is not automatic economics authority.
    - Observed product price can only be copied and frozen as a labeled proxy with timestamp; no dynamic linking to fluctuating crawler observations.
    - Product-scoped multiple economics scenarios with exactly-one-default invariant when scenarios exist.
    - Currency is VND-only; integer whole-VND persistence; commission rates in integer basis points (`10,000 bps = 100%`).
    - Null ≠ zero semantics: missing assumption fields are preserved as null.
    - Fixed campaign costs vs. variable cost per attributable order separation.
    - Calculation and rounding authority rests strictly with backend (round-half-up whole-VND); no derived values persisted in database.
    - Additive schema: exactly one required new table `economics_scenarios`.
    - Portable backup compatibility advances `"2" → "3"` upon Phase 6 schema implementation under unchanged ADR-004 same-version restore semantics. Current implemented product remains compatibility `"2"`.
    - Saved View V1 schemas, alert rules, and crawler unchanged for MVP.
    - No official Affiliate API/OAuth in MVP; no private dashboard scraping; no new third-party dependencies.

- **Phase 6 Authoritative Plan & Approval:**
  - Authoritative Plan: [`PHASE_6_PLAN.md`](PHASE_6_PLAN.md)
  - Plan Status: `APPROVED`
  - Implementation Status: `AUTHORIZED`
  - Approved Plan Revision Baseline: `4713fa422eb7f407b78995a9d453711910efc354`
  - Project Control Approval Record: [`PROJECT_CONTROL_PHASE6_PLAN_APPROVED.md`](PROJECT_CONTROL_PHASE6_PLAN_APPROVED.md)
  - Authoritative Acceptance Criteria: 42 criteria (`P6-AC-01` through `P6-AC-42`), covering domain separation, exact integer ratio rounding, deterministic concurrency, proxy provenance, query budgets, v2->v3 bootstrap, and ADR-004 restore/recovery safety.
  - Workstreams: 10 dependency-ordered workstreams (WS-0 through WS-9).
  - Implementation is authorized to proceed strictly against the approved plan.


- **Preserved Architecture Boundaries:**
  - `Watchlist = monitoring`;
  - `Collections = decision organization`;
  - `WatchlistItem.notes` provenance ownership;
  - `CollectionItem.notes` decision-note ownership;
  - Phase 2 authoritative Trend Score/evidence semantics (economics data must NOT modify Trend Score);
  - Phase 3 alert semantics;
  - Phase 4 same-version backup policy;
  - Phase 5 Saved View contracts;
  - Transient Compare semantics;
  - Shared Compare `as_of_utc`;
  - Compatibility version `"2"` until Phase 6 implementation explicitly advances it to `"3"`.

- **Preserved Debt & Deferred State:**
  - 1 High `source-map-js` advisory in the production dependency graph (build-time-only / non-runtime-reachable);
  - Development-only `braces` advisory in devDependencies;
  - `StarletteDeprecationWarning`;
  - Runtime `PRAGMA foreign_keys = 0`;
  - Broad discovery/CAPTCHA limitations deferred;
  - Standalone executable packaging deferred;
  - Cloud/multi-user deferred;
  - Previous Phase 5 out-of-scope items unless Phase 6 later explicitly selects one through approved scope.

---

## Project Control Reconciliation & Release Qualification

- **Project Control Final QA Decision (Historical):** `READY WITH DOCUMENTED NON-BLOCKING ISSUES` (for baseline commit `4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`).
- **Phase 4 Status:** `COMPLETE / ACCEPTED` (all acceptance criteria P4-AC-01 through P4-AC-35 validated and accepted).
- **Phase 5 Implementation Status:** `COMPLETE / ACCEPTED` (authoritative plan: [`PHASE_5_PLAN.md`](PHASE_5_PLAN.md), authoritative acceptance criteria: `P5-AC-01` through `P5-AC-36` all accepted/passing; implementation acceptance remains valid).
- **Phase 5 Source-Release Qualification:** `READY WITH DOCUMENTED NON-BLOCKING ISSUES` (Project Control accepted the repository-aware QA report; prior QA-environment availability blocker closed; qualified repository revision: `6e218929e3ff3ae091da1582de48fa0582802d8a`; qualified product-code revision: `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98`; formal qualification record: [`PROJECT_CONTROL_PHASE5_RELEASE_QUALIFIED.md`](PROJECT_CONTROL_PHASE5_RELEASE_QUALIFIED.md); historical blocked record preserved in [`PROJECT_CONTROL_PHASE5_QA_BLOCKED.md`](PROJECT_CONTROL_PHASE5_QA_BLOCKED.md)).
- **Active Phase:** Phase 6 — Affiliate Economics & Profitability Intelligence (`PLAN APPROVED / IMPLEMENTATION AUTHORIZED`; research `CLOSED / ACCEPTED`, ADR-005 `ACCEPTED`, product direction `RECOMMEND WITH REVISED SCOPE — ACCEPTED`, architecture gate `CLOSED / ACCEPTED`, plan `APPROVED` via [`PHASE_6_PLAN.md`](PHASE_6_PLAN.md), approved plan baseline `4713fa422eb7f407b78995a9d453711910efc354`, 42 acceptance criteria `P6-AC-01` through `P6-AC-42`, approval record [`PROJECT_CONTROL_PHASE6_PLAN_APPROVED.md`](PROJECT_CONTROL_PHASE6_PLAN_APPROVED.md); implementation is authorized to proceed; current product compatibility remains `"2"`; target Phase 6 compatibility is `"3"` upon schema implementation). Selecting, researching, planning, and implementing Phase 6 does not invalidate the qualified Phase 5 release. Selection record: [`PROJECT_CONTROL_PHASE6_SELECTION.md`](PROJECT_CONTROL_PHASE6_SELECTION.md); research acceptance record: [`PROJECT_CONTROL_PHASE6_RESEARCH_ACCEPTED.md`](PROJECT_CONTROL_PHASE6_RESEARCH_ACCEPTED.md); ADR-005 acceptance record: [`PROJECT_CONTROL_ADR005_ACCEPTED.md`](PROJECT_CONTROL_ADR005_ACCEPTED.md); research artifact: [`research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md`](research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md); authoritative ADR: [`docs/architecture/ADR-005.md`](docs/architecture/ADR-005.md); authoritative plan: [`PHASE_6_PLAN.md`](PHASE_6_PLAN.md).
- **Architecture & ADRs:** ADR-003 and ADR-004 remain active (`portable_backup_compatibility_version` in currently implemented product remains `"2"`); ADR-005 now `ACCEPTED` (selects target compatibility `"3"` for future Phase 6 schema); `ARCHITECTURE.md` updated with Phase 6 architecture section.
- **QA Code & Runtime Qualification:** PASS. Backend 178/178 pytest PASS (focused Phase 5 suite 25/25 PASS), Frontend 46/46 Vitest PASS, TypeScript clean, ESLint clean, Next.js build clean, healthcheck clean, SQLite integrity and FK checks clean. Collections query count: 2 SQL queries; Compare: 3 SQL queries with Collection context / 2 without; Saved View apply: 0 additional queries; Zero N+1; representative Compare benchmark (200 products / 5,000 snapshots / 5-product compare: best 4.42ms, median 5.14ms, p95 5.42ms, worst 5.42ms; <200ms hard gate PASS, <50ms research target PASS); Phase-4/v1 → Phase-5/v2 isolated bootstrap PASS; version-1 backup rejection PASS; version-2 backup/restore round-trip PASS; no functional regression detected; ADR-003 unchanged; ADR-004 same-version semantics unchanged.
- **Source-Control Handoff:** QUALIFIED / RECONCILED. Qualified repository revision: `6e218929e3ff3ae091da1582de48fa0582802d8a`; qualified product-code revision: `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98`.
- **Supported Release Boundary:** `Windows / local / source-based runtime`. Standalone executable/installer packaging remains deferred.
- **Release Blockers:** NONE. Prior QA-environment availability blocker closed by repository-aware QA. Zero product/code/architecture blockers exist.
- **Remote Publication:** Remote publication is a separate explicitly authorized action; target revisions have not been pushed to `origin/main`.
- **Preserved Accepted Non-Blocking Debt:**
  - 1 High `source-map-js` advisory in the production dependency graph (`GHSA-68fv-2mgg-jv7q`): reaches dependency graph through Next/PostCSS/CSS-build tooling; QA found no known path from untrusted runtime input to the vulnerable behavior; presently assessed as build-time-only / not production-runtime reachable; no functional or security exploit was demonstrated against the supported local runtime; classified as non-blocking dependency/security debt for this release (earlier claims of 0 production vulnerabilities superseded).
  - Development-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`) in devDependencies (`tailwindcss@3.4.19` and `eslint-config-next@15.5.27`, zero production runtime reachability).
  - `StarletteDeprecationWarning` during test execution (`httpx` integration with `starlette.testclient`).
  - Runtime `PRAGMA foreign_keys = 0` (`OFF`) maintained for cross-phase operational stability.
  - Scratch-file cleanup deviation (five untracked `.txt` scratch files cleaned up; no code/test/config impact).
  - QA evidence-quality notes:
    1. No explicit manual keyboard/accessibility checklist was supplied in final QA evidence (automated UI/acceptance coverage passed; no accessibility regression demonstrated; classified as evidence-quality gap, not release blocker).
    2. QA was described as observational, but live API checks created and then deleted temporary Collection and Saved View records (no source modification; no destructive restore; zero release-state impact; wording correction only).
- **Preserved Accepted Deferred Scope:**
  - Broad automatic discovery / CAPTCHA bypass deferred.
  - Real 7-day field observation deferred.
  - Browser DB transfer deferred (operator launcher CLI `BACKUP.bat` / `RESTORE.bat` only).
  - Cross-version database migrations deferred (same-version restore enforced via compatibility marker "2").
  - TikTok session portability deferred (host-bound local session isolated from backups/exports).
  - Standalone executable/installer packaging deferred (local Windows source-based runtime).
  - Phase 5 deferred items (tags, persisted compare, compare charts, AI recommendations, URL sync, collection archiving).
  - All other previously documented deferred items.
