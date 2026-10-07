# Phase 6 Completion Report — Affiliate Economics & Profitability Intelligence

> **Repository:** `TinixTikTrend` (`thanhtan229/TinixTikTrend`)  
> **Phase:** Phase 6 — Affiliate Economics & Profitability Intelligence  
> **Working Scope:** VND-only, manual-first Product Economics Scenarios  
> **Authoritative Plan:** [`PHASE_6_PLAN.md`](PHASE_6_PLAN.md)  
> **Accepted Architecture:** [`docs/architecture/ADR-005.md`](docs/architecture/ADR-005.md)  
> **Target Compatibility Version:** `"3"`  
> **Accepted Final Remediation Commit:** `1bd1e5ddcb8999861ae43b9eb8775681f07edd6d` (`1bd1e5d`)  
> **Previous Remediation Commit:** `2603deb16af57cf5931ac801fd9ff21fb8cdde37`  
> **Final External Decision:** `Phase 6 = COMPLETE`  
> **Date of Acceptance:** 2026-10-07  
> **Status:** `COMPLETE / ACCEPTED BY EXTERNAL PROJECT CONTROL (RELEASE REQUALIFICATION PENDING)`

---

## 1. Executive Summary & Remediation Overview

Phase 6 ("Affiliate Economics & Profitability Intelligence") has been fully remediated, verified, and reconciled in accordance with instructions from external `00 — Project Control & Roadmap`.

All 10 required remediation gates have been executed and verified against the actual repository state:
1. **Exact Rational Break-Even Calculation:**
   - Calculation formula uses exact rational contribution numerator prior to presentation rounding:
     $$\text{contrib\_num} = \text{base\_vnd} \times \text{rate\_bps} - \text{var\_cost\_vnd} \times 10\,000$$
     $$\text{break\_even\_orders} = \left\lceil \frac{\text{fixed\_campaign\_cost\_vnd} \times 10\,000}{\text{contrib\_num}} \right\rceil = \frac{\text{fixed\_cost} \times 10\,000 + \text{contrib\_num} - 1}{\text{contrib\_num}}$$
   - Regression vector strictly verified: `base = 105 VND`, `rate = 1000 bps`, `variable = 10 VND`, `fixed = 1 VND` $\implies$ Break-even = **`2`**, never `1` (eliminating the presentation-rounding off-by-one hazard).
2. **JavaScript Safe-Integer Contract ($Number.MAX\_SAFE\_INTEGER = 9,007,199,254,740,991$):**
   - Rejection contract: Create, update (PATCH), and rebase payloads are rejected with HTTP 422 when supplied assumptions cause any mathematically known derived integer monetary output to exceed `Number.MAX_SAFE_INTEGER`:
     - Rounded commission per attributable order;
     - Fixed campaign cost sum;
     - Expected commission;
     - Expected variable cost;
     - Total expected campaign cost;
     - Expected contribution magnitude (both positive and negative).
   - Exact integer/rational arithmetic used throughout; zero floating-point representation artifacts.
   - Missing input semantics preserved: missing assumptions cleanly evaluate to `None` in derived responses without triggering validation rejection, proving missing-value semantics remain strictly distinct from numeric overflow rejection.
   - All 7 focused safe-integer verification vectors pass: max valid combination, one-above expected commission (422), one-above expected variable cost (422), one-above total campaign cost (422), one-above positive/negative contribution magnitude (422), clean missing input `None` evaluation, and PATCH equivalent validation on merged candidate state.
   - Pure analytics engine defensively clamps/returns `None` for any derived value exceeding safe-integer limits.
3. **Schema Table Naming Verification:**
   - Verified that `economics_scenarios` is the authoritative, accepted (ADR-005 line 122), and implemented database table name.
   - Confirmed that references to `product_economics_scenarios` in earlier evidence drafts were documentation typos, not ADR violations or silent schema renamings.
4. **Portable Backup Format Verification:**
   - Verified that the portable backup engine adheres strictly to ADR-004 by producing point-in-time consistent SQLite binary files (`.sqlite3`) via `sqlite3.Connection.backup()`.
   - Corrected all erroneous "Portable Backup JSON" wording; confirmed the backup format is 100% SQLite binary.
5. **Isolated Disaster Recovery & Restore Lifecycle Evidence:**
   - Verified pre-restore safety backup creation (`tinix-pre-restore-v3-*.sqlite3`), collision prevention, atomic file replacement, restore manifest states, injected post-replacement health failure with automatic rollback, v3 economics scenario preservation, and host-bound session token exclusion.
   - All tests executed in isolated temporary environments with zero destructive operations against real `backend/affiliate.db`.
6. **10-Iteration Performance Benchmark Qualification:**
   - Executed 1 unmetered warmup + 10 timed iterations for Collection Member list with economics and 5-Product Compare with economics on representative 200-product/5,000-snapshot fixture.
   - Collection Members: worst latency **2.92 ms** (2 SQL queries).
   - Compare Products: worst latency **40.20 ms** (4 SQL queries).
   - Both comfortably pass the $< 200\text{ms}$ hard gate.
7. **Comprehensive Manual QA Matrix:**
   - Executed and passed all 12 manual scenarios, including observed-price freeze, crawler immutability, explicit rebase, manual edit provenance reset, null vs explicit zero, deterministic duplication, UI error/retry, stale-response handling, keyboard/focus accessibility, Collections missing-scenario state, and Compare missing-scenario state.
8. **Focused Provenance Security Rules:**
   - Verified all 5 rules: client cannot forge provenance/timestamp, manual edit clears timestamp, proxy price and timestamp match the exact same snapshot, PATCH cannot change `is_default`, and crawler snapshot commission is not economics authority.
9. **Truthful Governance Reconciliation:**
   - Superseded the false claim that external Project Control had finalized plan approval prior to implementation; updated governance records truthfully without rewriting Git history.
10. **Phase 7 Provisional Boundary:**
    - All Phase 7 documents remain labeled `PROVISIONAL — NOT YET ACCEPTED BY EXTERNAL PROJECT CONTROL`. Zero Phase 7 production code or executable tests written.

---

## 2. Test Execution & Health Evidence

### 2.1 Backend Automated Tests (Pytest)
Executed via repository virtual environment interpreter: `.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ -q`
- **Total Backend Tests:** **223 passed** (0 failed, 4 non-blocking deprecation warnings) in **55.00s**.
- **Dedicated Phase 6 Economics Tests:** `backend/tests/test_phase6_economics.py` (38 passed).
- **Disaster Recovery & Version "3" Upgrade Tests:** `backend/tests/test_phase6_backup_upgrade.py` (4 passed).
- **Performance & Query Count Tests:** `backend/tests/test_performance_and_queries.py` (6 passed).

### 2.2 Frontend Automated Tests (Vitest)
Executed via `npm test` in `frontend/`:
- **Total Frontend Test Files:** **9 passed** (0 failed).
- **Total Frontend Tests:** **52 passed** (0 failed) in **25.51s**.
- **Dedicated Phase 6 Vitest Tests:** `frontend/tests/phase6-economics.test.tsx` (6 passed).

### 2.3 Static Analysis & Production Compilation
- **TypeScript Typecheck:** `npx tsc --noEmit` $\longrightarrow$ **0 errors** (clean).
- **ESLint:** `npm run lint` $\longrightarrow$ **0 errors, 0 warnings** (clean).
- **Next.js Production Build:** `npm run build` $\longrightarrow$ **Compiled successfully in 2.2s** (clean, zero build errors).

### 2.4 Performance Benchmarks (P6-AC-33 & P6-AC-35)
Benchmark protocol: 1 unmetered warmup + 10 timed iterations on representative 200-product, 5,000-snapshot fixture in isolated SQLite database.

| Operation | Query Budget | Actual Queries | Series (10 Iterations) [ms] | Best [ms] | Median [ms] | p95 [ms] | Max / Worst [ms] | Hard Gate | Status |
| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Collection Members (20 items with econ)** | $\le 3$ | **2** | `[2.92, 2.22, 1.56, 1.39, 1.40, 2.37, 2.60, 2.13, 1.55, 1.44]` | **1.39** | **1.85** | **2.92** | **2.92** | $< 200\text{ms}$ | **PASS** |
| **5-Product Compare (with collection context)** | $\le 4$ | **4** | `[40.20, 4.87, 6.78, 6.13, 6.58, 5.29, 4.91, 4.89, 5.22, 5.79]` | **4.87** | **5.54** | **40.20** | **40.20** | $< 200\text{ms}$ | **PASS** |

*Both critical read paths execute well within the 200ms hard gate and satisfy query budgets with zero N+1 queries.*

### 2.5 Runtime Health Check & Integrity
- **Backend Health Check:** `http://127.0.0.1:8000/api/health` $\longrightarrow$ **HTTP 200 OK** (`{"status":"ok","database":"connected",...}`).
- **Frontend Health Check:** `http://127.0.0.1:3000` $\longrightarrow$ **HTTP 200 OK**.
- **SQLite Database Integrity:** `PRAGMA integrity_check` $\longrightarrow$ `[('ok',)]`.
- **SQLite Foreign Key Check:** `PRAGMA foreign_key_check` $\longrightarrow$ `[]` (0 violations).
- **Database Compatibility Marker:** `system_metadata.portable_backup_compatibility_version` = `"3"`.
- **Live Diagnostics:** `/api/diagnostics` reports `"economics_scenarios"` count with zero scenario financial parameter leakage.
- **Disaster Recovery Backup:** `.\BACKUP.bat` generates verified `tinix-affiliate-v3-*.sqlite3` backup with compatibility version `"3"`.

---

## 3. Detailed Acceptance Criteria Verification Matrix

| AC Identifier | Description | Verification Method & Evidence | Status |
| :--- | :--- | :--- | :---: |
| **`P6-AC-01`** | Domain separation: zero effect on Trend Score, evidence, alerts, or scheduler | `test_p6_ac_01_domain_separation_zero_trend_side_effects` | **PASS** |
| **`P6-AC-02`** | Attribution prohibition: no creator sales inference from market sold count | Calculation assertions, zero `sales_velocity * commission` | **PASS** |
| **`P6-AC-03`** | Manual-first source baseline: snapshot commission rate not authoritative | `test_p6_ac_03_manual_first_baseline_ignores_snapshot_rate` | **PASS** |
| **`P6-AC-04`** | Single table persistence: exactly `economics_scenarios` table added | Metadata inspection, dynamic schema derivation | **PASS** |
| **`P6-AC-05`** | Numeric types & safe bounds ($0 \le \text{cost} \le 10^{11}$, $0 \le \text{bps} \le 10000$) | `test_safe_integer_max_boundary_and_rejections` (bounds + totals) | **PASS** |
| **`P6-AC-06`** | Null preservation: unknown $\ne$ 0; explicit 0 persists as 0 | `test_p6_ac_06_null_preservation_and_explicit_zero` | **PASS** |
| **`P6-AC-07`** | Unique scenario name per product with HTTP 409 Conflict | `test_p6_ac_07_unique_scenario_name_per_product` | **PASS** |
| **`P6-AC-08`** | Quarantined product exclusion (HTTP 400 Bad Request) | `test_p6_ac_08_quarantine_exclusion` | **PASS** |
| **`P6-AC-09`** | Zero scenarios yields zero defaults | `test_p6_ac_09_zero_scenarios_zero_defaults` | **PASS** |
| **`P6-AC-10`** | Exactly-one-default invariant for $\ge 1$ scenarios | Invariant check across all CRUD actions | **PASS** |
| **`P6-AC-11`** | First scenario auto-default | `test_p6_ac_11_first_scenario_auto_default` | **PASS** |
| **`P6-AC-12`** | Subsequent scenario non-default | `test_p6_ac_12_subsequent_scenario_non_default` | **PASS** |
| **`P6-AC-13`** | Atomic default toggling via dedicated endpoint | `test_p6_ac_13_atomic_default_toggling` | **PASS** |
| **`P6-AC-14`** | Deterministic promotion on default deletion (`(created_at ASC, id ASC)`) | `test_p6_ac_14_deterministic_promotion_on_default_deletion` | **PASS** |
| **`P6-AC-15`** | Deleting final scenario leaves 0 scenarios and 0 defaults | `test_p6_ac_15_deleting_final_scenario` | **PASS** |
| **`P6-AC-16`** | Database SQLite partial unique default index enforcement | `test_p6_ac_16_db_partial_unique_index_enforcement` | **PASS** |
| **`P6-AC-17`** | Concurrency Case 1 & 2: simultaneous scenario creates | Multi-threaded barrier test | **PASS** |
| **`P6-AC-18`** | Concurrency Case 3–6: concurrent set-default and delete races | Multi-threaded barrier test | **PASS** |
| **`P6-AC-19`** | Concurrency Case 7 & 8: transaction rollback safety | Injected promotion failure rollback test | **PASS** |
| **`P6-AC-20`** | Authoritative exact integer ratio rounding: $(2N + D) // (2D)$ | Round-half-up vector tests in `economics.py` | **PASS** |
| **`P6-AC-21`** | Commission per order formula with integer arithmetic | `test_p6_ac_21_commission_per_order_formula` | **PASS** |
| **`P6-AC-22`** | Fixed campaign cost formula & null propagation | `test_p6_ac_22_fixed_campaign_cost_null_propagation` | **PASS** |
| **`P6-AC-23`** | Contribution margin per order formula ($C = \text{comm} - \text{var}$) | `test_p6_ac_23_contribution_margin_formula` | **PASS** |
| **`P6-AC-24`** | Break-even orders integer ceiling division with exact rational numerator | Vector test: base=105, rate=1000, var=10, fixed=1 $\implies$ **2** | **PASS** |
| **`P6-AC-25`** | Expected campaign economics (gross, var, contribution, return-on-cost) | Exact reference vector unit tests + safe-integer clamping | **PASS** |
| **`P6-AC-26`** | Zero persisted calculations in database columns | Database schema audit & instant update tests | **PASS** |
| **`P6-AC-27`** | Observed-price proxy freezing and validation | `test_p6_ac_27_observed_price_proxy_freezing` | **PASS** |
| **`P6-AC-28`** | Proxy immutability against crawler updates | Crawler snapshot price change does not mutate proxy | **PASS** |
| **`P6-AC-29`** | Provenance reset on manual base edit | `test_p6_ac_29_provenance_reset_on_manual_edit` | **PASS** |
| **`P6-AC-30`** | Rebase price proxy action | Dedicated endpoint test refreshing price and timestamp | **PASS** |
| **`P6-AC-31`** | Commercial payout disclosure banner present | Frontend render & Vitest component assertion | **PASS** |
| **`P6-AC-32`** | Product detail economics workspace UI complete | `frontend/tests/phase6-economics.test.tsx` | **PASS** |
| **`P6-AC-33`** | Collections integration & query budget $\le 3$ queries (Zero N+1) | `test_p6_ac_33_collection_members_query_budget` (2 queries) | **PASS** |
| **`P6-AC-34`** | Compare integration & query budget $\le 4$ queries (Zero N+1) | `test_p6_ac_34_compare_products_query_budget` (4 queries) | **PASS** |
| **`P6-AC-35`** | Performance benchmark latency gate: worst $< 200\text{ms}$ | 10-iteration benchmark: Collections worst 2.92ms, Compare worst 40.20ms | **PASS** |
| **`P6-AC-36`** | Additive bootstrap & compatibility version advance `"2" \to "3"` | `test_isolated_v2_to_v3_bootstrap_and_schema_verification` | **PASS** |
| **`P6-AC-37`** | Rejection of version `"2"` backups on version `"3"` app (HTTP 400) | `test_v2_backup_rejected_by_v3_validation` | **PASS** |
| **`P6-AC-38`** | Pre-restore safety backup creation & rollback safety | `test_isolated_v3_restore_and_disaster_recovery_lifecycle` | **PASS** |
| **`P6-AC-39`** | Version `"3"` backup round-trip validation with session exclusion | `test_v3_backup_roundtrip_validation` & lifecycle test | **PASS** |
| **`P6-AC-40`** | Safe diagnostics: aggregate table count only; zero telemetry | `test_api_diagnostics_includes_economics` | **PASS** |
| **`P6-AC-41`** | Operator documentation deliverables updated (`ARCHITECTURE.md`, `README.md`) | Verified in git commits `b11fb5e` | **PASS** |
| **`P6-AC-42`** | Full test suites, runtime health, and SQLite integrity clean | 222 backend, 52 frontend, tsc, lint, build, health all 100% | **PASS** |

---

## 4. Manual QA Matrix Verification (`M1` to `M12`)

| Step | Area | Verification Result |
| :---: | :--- | :--- |
| **M1** | Scenario Creation | Verified. Created scenario sets default star badge, evaluates commission = 10,000 VND, contribution = 10,000 VND, break-even = 2 orders. |
| **M2** | Price Proxy Freeze | Verified. Clicking toggle on create freezes rounded VND price from latest snapshot with timestamp and `observed_price_proxy` label. |
| **M3** | Default Switching | Verified. Clicking `Đặt mặc định` on Scenario B atomically flips default badge to B; A loses badge. |
| **M4** | Default Promotion on Delete | Verified. Deleting default Scenario B atomically promotes oldest remaining Scenario A to default. |
| **M5** | Null vs Zero Semantics | Verified. Setting Promotion Cost to `0` leaves it as `0 đ`; empty Content Cost propagates `—` for Fixed Cost and Break-Even. |
| **M6** | Input Bounds & Validation | Verified. Rate $> 100\%$ or negative costs rejected with clear validation errors. Sub-basis points ($>2$ decimals in %) rejected. Safe integer boundary values validated. |
| **M7** | Price Rebase Action | Verified. Clicking `Cập nhật giá sàn` fetches current snapshot price and updates timestamp with confirmation feedback. |
| **M8** | Duplicate Scenario | Verified. Cloned scenario created with unique name, identical assumptions, and `is_default = false`. |
| **M9** | Collections Workspace | Verified. Collections member table displays default scenario columns (`Hoa hồng/đơn`, `Đóng góp/đơn`, `Đơn hòa vốn`) with clean `—` for products without scenarios. |
| **M10** | Compare Workspace | Verified. Compare modal displays default scenario economics row group with clean empty indicators (`—`) for products without scenarios. |
| **M11** | Stale Response & Retry | Verified. Component handles network errors with clear error banner and functional `Thử tải lại` retry button. |
| **M12** | Accessibility & Focus | Verified. Modals have semantic headers, keyboard close handling, and all interactive action buttons have clear labels. |

---

## 5. Non-Blocking Technical Debt Disclosures

Phase 6 introduces zero new security vulnerabilities and preserves all previously documented non-blocking technical debt items:
1. **`source-map-js` Advisory (`GHSA-68fv-2mgg-jv7q`):** Non-blocking build-time advisory in Next.js dependency tree.
2. **`braces` Advisory (`GHSA-vfj7-8cjw-p6xm`):** Non-blocking development-only advisory in Vitest devDependencies.
3. **`StarletteDeprecationWarning`:** Test client deprecation warning regarding HTTPX.
4. **Runtime SQLite FK Enforcement (`PRAGMA foreign_keys = 0`):** Preserved for runtime stability; all backup validations, tests, and deep diagnostics strictly enforce `PRAGMA foreign_key_check`.

---

## 6. Project Control Decision & Release Handoff

Phase 6 technical implementation and final remediations have been formally accepted by external Project Control:
- **Final External Completion Decision:** **`Phase 6 = COMPLETE`**
- **Implementation Status:** **`COMPLETE / ACCEPTED`**
- All 10 remediation points and 42 acceptance criteria verified and supported by durable code/test evidence.
- Accepted final remediation commit: `1bd1e5ddcb8999861ae43b9eb8775681f07edd6d` (`1bd1e5d`).
- Backend passes 223 tests; frontend passes 52 tests; TypeScript, ESLint, Next.js build, and runtime healthchecks are 100% green.
- Source-release qualification: **`PENDING REQUALIFICATION`** under QA — Build & Release (prior qualification superseded by remediation changes).
- Phase 7 remains strictly provisional without implementation code or tests (`Implementation: NOT AUTHORIZED`).

**Phase Status:** **`COMPLETE / ACCEPTED`**  
**Release Gate:** **`PENDING RELEASE REQUALIFICATION`**
