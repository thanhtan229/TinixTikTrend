# Project Control ADR-005 Acceptance Record

- **Date:** 2026-10-06
- **Role:** `00 — Project Control & Roadmap`
- **ADR Title:** [`ADR-005 — Affiliate economics assumptions, provenance, numeric semantics, and calculation authority`](docs/architecture/ADR-005.md)
- **Project Control Decision:** `ACCEPTED`
- **Accepted Draft Commit:** `fcf5ff722391f4c8e0f5e75c43e78c7dd18bc4b4`
- **Accepted Research Baseline:** [`research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md`](research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md) (accepted under commit `8c3f8949b8c9e61691c2e2756557e9abadc035b5`, documented in [`PROJECT_CONTROL_PHASE6_RESEARCH_ACCEPTED.md`](PROJECT_CONTROL_PHASE6_RESEARCH_ACCEPTED.md))
- **Phase 6 Status:** `SELECTED / RESEARCH COMPLETE / ARCHITECTURE ACCEPTED`
- **Architecture Gate:** `CLOSED / ACCEPTED`
- **Phase Plan Status:** `NOT YET APPROVED` (Phase 6 planning is now authorized to begin)
- **Implementation Status:** `NOT AUTHORIZED`
- **Acceptance Criteria:** `NONE DEFINED YET` (no Phase 6 acceptance criteria exist yet)
- **Current Product Compatibility:** `"2"` (Phase 5 product state unchanged)
- **Target Phase 6 Compatibility:** `"3"` (upon future Phase 6 schema implementation)
- **Previous Release State:** Phase 5 source-release qualification remains **READY WITH DOCUMENTED NON-BLOCKING ISSUES** for the supported **Windows / local / source-based runtime** (qualified repository revision: `6e218929e3ff3ae091da1582de48fa0582802d8a`; qualified product-code revision: `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98`; formal qualification record: [`PROJECT_CONTROL_PHASE5_RELEASE_QUALIFIED.md`](PROJECT_CONTROL_PHASE5_RELEASE_QUALIFIED.md)). Acceptance of ADR-005 does not alter or invalidate the qualified Phase 5 release.

---

## 1. Project Control Decision

Project Control has formally reviewed and **ACCEPTED** [`ADR-005 — Affiliate economics assumptions, provenance, numeric semantics, and calculation authority`](docs/architecture/ADR-005.md) as proposed under commit `fcf5ff722391f4c8e0f5e75c43e78c7dd18bc4b4`.

1. **Architecture Gate Closed:** The Phase 6 architecture gate is formally **CLOSED / ACCEPTED**.
2. **Planning Authorized:** Phase 6 implementation planning is now **AUTHORIZED TO BEGIN**. Planning must strictly comply with ADR-005 and the accepted Phase 6 research artifact.
3. **Implementation Not Authorized:** Phase 6 implementation remains strictly **NOT AUTHORIZED**. No production code, tests, or dependencies may be created or modified until the Phase 6 implementation plan is reviewed and approved by Project Control.
4. **No Premature Acceptance Criteria:** No acceptance criteria or test cases are established in this task.
5. **Release State Preserved:** The running application remains on the Phase 5 qualified release state at compatibility version `"2"`.

---

## 2. Authoritative Frozen Architecture Invariants

All architectural decisions established in ADR-005 are frozen as authoritative constraints:

1. **Domain Separation:**
   - Strict separation across Market Evidence (crawler observations, Trend Score), User Economics Assumptions (manual scenario parameters), and Derived Economics (read-time calculations).
   - Economics assumptions and derived metrics must **never** influence or alter the Phase 2 Trend Score, momentum, evidence confidence, or "Why trending" explanations.
   - Blended "trend-profit" metrics are strictly prohibited.
2. **Attribution Boundary:**
   - Product cumulative sold count and 24-hour sales velocity represent overall market activity, not affiliate attribution.
   - Prohibited formula: `sales_velocity × commission_per_order` as "estimated affiliate earnings".
   - Attributable orders require explicit user scenario assumptions or future authoritative attribution sources.
3. **Manual-First Source Strategy:**
   - MVP economics relies on explicit, user-defined scenarios.
   - Crawler-observed `ProductSnapshot.commission_rate` is market observation data only and possesses no automatic calculation authority.
   - Market product price (`analysis.deltas.latest_price`) can only be explicitly copied and frozen as a labeled proxy with timestamp; it is never dynamically linked to fluctuating crawler observations.
4. **Product-Scoped Multiple Scenarios & Exactly-One-Default Invariant:**
   - Each `Product` owns zero, one, or more named `EconomicsScenario` records.
   - Invariant: When scenarios exist for a Product, **exactly one** default scenario (`is_default = true`) must exist.
   - When zero scenarios exist, exactly zero defaults exist.
   - The first scenario created for a Product automatically becomes the default.
   - Default switching is atomic.
   - Deleting the default scenario when other scenarios remain deterministically promotes the oldest remaining scenario by `(created_at, id)`.
5. **Currency & Numeric Semantics:**
   - Currency is strictly **VND-only**; no multi-currency support, no FX conversions.
   - Monetary values are persisted as whole-VND integers (`Integer`), eliminating floating-point rounding artifacts.
   - Commission rates are persisted as integer basis points (`commission_rate_bps`, where `10,000 bps = 100.00%`).
   - Null preservation: missing assumption fields are strictly `null` and never silently converted to `0` (`null ≠ 0`).
   - Strict separation between fixed campaign costs (sample, content production, ad spend) and variable cost per attributable order.
6. **Backend Calculation Authority:**
   - All financial calculations (estimated commission, contribution margin, break-even orders, expected gross commission, expected net contribution, return on cost) and rounding policies (round-half-up to whole VND) are executed exclusively by the backend at read time.
   - Derived economic metrics are **not persisted** in the database.
   - Frontend is strictly a presentation layer with zero financial calculation or rounding authority.
7. **Additive Persistence Boundary:**
   - Exactly one new database table is required: `economics_scenarios`.
   - No tables for cost line items, economics history, commission observations, formula definitions, or persisted derived metrics in MVP.
8. **Compatibility Advance `"2" → "3"`:**
   - When Phase 6 schema is implemented, `portable_backup_compatibility_version` in `system_metadata` will advance from `"2"` to `"3"`.
   - The current running application remains compatibility `"2"`.
9. **Workspace, Alerts, and Exports Isolation:**
   - Phase 5 Saved View V1 schemas (Trends and Watchlist) remain frozen and unchanged.
   - No economics alert types in MVP.
   - Economics CSV export is deferred.
10. **External Boundaries:**
    - No official TikTok Shop Partner/Affiliate API/OAuth integration in MVP.
    - No private Creator Center dashboard scraping or CAPTCHA bypass.
    - No new third-party dependencies.

---

## 3. Relationship to ADR-003 and ADR-004

- **ADR-003 (Durable Post-Commit Alert Evaluation and Replay Semantics):**
  - Remains active and unchanged.
  - Ingestion commits and alert evaluation remain isolated in separate transactions.
  - Startup catch-up ordering is unaffected (`schema/bootstrap/backfill` → `crawl reconciliation` → `alert catch-up` → `scheduler start` → `application ready`).
  - No economics alert rules are added to the alert evaluation engine in MVP.
- **ADR-004 (Local Backup/Restore Integrity, Keyset Streaming CSV Exports, and Compatibility Semantics):**
  - Remains active and unchanged.
  - Offline launcher-owned restore (`RESTORE.bat`), candidate file pre-validation, pre-restore safety backups, and same-version restore semantics continue to govern operational persistence.
  - Current product strictly enforces compatibility `"2"` and rejects version-1 backups.
  - When Phase 6 implementation advances the schema, compatibility `"3"` will enforce rejection of version-1 and version-2 backups before any destructive database modification.
  - TikTok session credentials remain host-bound and strictly excluded from backups.

---

## 4. Planning Constraints for Future Phase 6 Plan

Project Control establishes the following mandatory constraints for the future Phase 6 implementation plan:

1. **Compliance with ADR-005 and Accepted Research:**
   The implementation plan must strictly conform to all decisions frozen in ADR-005 and [`research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md`](research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md).

2. **Durable Concurrency and Invariant Testing:**
   The plan must explicitly define verification and automated test coverage for scenario default invariants and race conditions:
   - Concurrent creation of the first scenario for a product (ensuring deterministically exactly one default);
   - Concurrent attempts to set different default scenarios on the same product;
   - Racing delete of the current default scenario concurrent with default switching;
   - Database-level partial unique index enforcement (`UNIQUE(product_id) WHERE is_default = 1`);
   - Service-level exactly-one-default enforcement;
   - Transaction rollback behavior ensuring no partial commits;
   - Verification that a product with scenarios **never** exists in a committed state with zero defaults;
   - Verification that a product with scenarios **never** exists in a committed state with multiple defaults.

3. **No Implementation Without Plan Approval:**
   Planning is authorized; implementation is not. No code, test, or schema modifications may begin until `PHASE_6_PLAN.md` is approved by Project Control.

---

## 5. Next Lifecycle Action

1. Proceed to Phase 6 implementation planning against the accepted research and accepted ADR-005.
2. Return to `00 — Project Control & Roadmap`.
