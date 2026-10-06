# Project Control Phase 6 Research Acceptance Record

- **Date:** 2026-10-06
- **Role:** `00 — Project Control & Roadmap`
- **Selected Phase:** Phase 6 — Affiliate Economics & Profitability Intelligence
- **Phase 6 Status:** `SELECTED / RESEARCH COMPLETE`
- **Research Gate:** `CLOSED / ACCEPTED`
- **Research Status:** `CLOSED / ACCEPTED` (research artifact: [`research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md`](research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md))
- **Research Readiness:** `RESEARCH READY FOR PROJECT CONTROL`
- **Product Recommendation:** `RECOMMEND WITH REVISED SCOPE — ACCEPTED`
- **Selected Product Direction:** `VND-only, manual-first Product Economics Scenarios`
- **Architecture Gate:** `ADR-005 REQUIRED BEFORE PHASE 6 IMPLEMENTATION-PLAN APPROVAL`
- **Phase Plan Status:** `NOT STARTED`
- **Implementation Status:** `NOT AUTHORIZED`
- **Acceptance Criteria:** `NONE DEFINED YET` (no Phase 6 acceptance criteria exist yet)
- **Authoritative Phase 6 Selection Commit:** `d97f00f7819e778954a76abe3605e1442ea4155d`
- **Superseded Identifier Discrepancy:** Previously reported identifier `d97f00f9a25b16f398f658be424b94f1e58286ad` is superseded and corrected to `d97f00f7819e778954a76abe3605e1442ea4155d`.
- **Previous Release State:** Phase 5 release qualification remains **READY WITH DOCUMENTED NON-BLOCKING ISSUES** for the supported **Windows / local / source-based runtime** (qualified repository revision: `6e218929e3ff3ae091da1582de48fa0582802d8a`; qualified product-code revision: `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98`; latest release-state reconciliation commit: `ef09b710bebc21df4cb64ff89a31a95a6ec46dbb`). Acceptance of Phase 6 research does not invalidate the qualified Phase 5 release.

---

## 1. Project Control Decision

Project Control has formally reviewed and **ACCEPTED** the research findings in [`research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md`](research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md).

1. **Research Gate Closed:** The Phase 6 research gate is closed as `CLOSED / ACCEPTED`.
2. **Product Direction Accepted:** The product recommendation `RECOMMEND WITH REVISED SCOPE` is accepted. The selected direction is **VND-only, manual-first Product Economics Scenarios**.
3. **Repository Verification Complete:** Repository verification against repository HEAD `d97f00f7819e778954a76abe3605e1442ea4155d` is verified and confirmed.
4. **Planning Status:** Phase 6 implementation planning has **NOT STARTED**. Planning may begin only after the required architectural decision record (**ADR-005**) is drafted and reviewed.
5. **Implementation Status:** Phase 6 implementation is **NOT AUTHORIZED**. No production code or tests may be modified.

---

## 2. Commit SHA Discrepancy Correction

Repository verification confirmed the authoritative actual Phase 6 selection HEAD commit:

`d97f00f7819e778954a76abe3605e1442ea4155d`

A previously reported identifier:

`d97f00f9a25b16f398f658be424b94f1e58286ad`

is incorrect and did not match the actual Git commit hash.

**Project Control Determination:**
- The authoritative commit for Phase 6 selection is `d97f00f7819e778954a76abe3605e1442ea4155d`.
- The incorrect identifier `d97f00f9a25b16f398f658be424b94f1e58286ad` is formally superseded and corrected across all durable Project Control records.
- Current repository state is clean and unambiguous.

---

## 3. Accepted Revised Scope & Architecture Constraints

The accepted MVP direction is **VND-only, manual-first Product Economics Scenarios**.

The following architectural and planning constraints are durably bound:

1. **Domain Boundary Separation:**
   - Economics remains strictly separate from Trend Score, trend evidence, and trend confidence.
   - Economics data must not modify, weight, or contaminate the Phase 2 Trend Score.
   - No blended trend-profit score.
2. **Attribution Boundary:**
   - Product sold count and sales velocity must **never** be treated as affiliate attribution or creator earnings.
   - Prohibited formula: `sales_velocity × commission_per_order` as "estimated affiliate earnings".
   - Attributable orders require explicit user scenario assumptions or future authoritative attribution sources.
3. **Commission Provenance Authority:**
   - Existing `ProductSnapshot.commission_rate` is market observation data only; it is **not** automatic economics authority.
   - Authoritative calculation rate is solely the explicit scenario assumption.
4. **Product-Scoped Multiple Scenarios:**
   - One `Product` may have multiple named economics scenarios (e.g., "Conservative", "Base", "Aggressive").
5. **Default Scenario Invariants:**
   - Zero scenarios on a Product means zero defaults.
   - Whenever scenarios exist for a Product, **exactly one** committed default exists.
   - The first scenario created for a Product auto-defaults.
   - Default switching is atomic.
   - Deleting the default scenario while other scenarios remain deterministically promotes the oldest remaining scenario by `(created_at, id)`.
6. **Currency & Numeric Semantics:**
   - Currency is **VND-only**; no multi-currency support, no FX conversions.
   - Money values are persisted as whole-VND integers.
   - Commission rates are persisted as integer basis points (`10,000 bps = 100%`).
7. **Cost Structure:**
   - Fixed campaign costs:
     - Sample / product acquisition cost;
     - Content production cost;
     - Planned promotion / ad spend.
   - Variable cost per attributable order remains separate.
   - **Unknown / null is not zero:** missing assumptions must not silently default to 0.
8. **Observed Price Proxy:**
   - Observed Product price (`analysis.deltas.latest_price`) can only be explicitly copied and frozen as a user-labeled proxy with a timestamp.
   - It is never dynamically linked to fluctuating crawler observations.
9. **Calculation Authority:**
   - Derived economics are calculated by **one backend authority** and are **not persisted**.
   - No financial calculation or rounding authority is duplicated on the frontend.
10. **Workspace & Export Isolation:**
    - Phase 5 Saved View V1 schemas remain frozen and unchanged.
    - No economics alert types in MVP.
    - Economics CSV export is deferred.
11. **External Boundaries:**
    - No official Affiliate API / OAuth integration in MVP.
    - No private Creator Center scraping.
    - No CAPTCHA / anti-bot bypass mechanisms.
    - No new third-party dependencies required.

---

## 4. Accepted Numeric & Formula Policy

The research-level architecture decision awaiting ADR formalization establishes:

### Persisted Assumptions
- Money = whole-VND integer (e.g. `250000` VND);
- Commission = integer basis points (`1 bps = 0.01%`; `10,000 bps = 100.00%`).

### Backend Calculation Authority & Derived Concepts
Derived metrics are computed on the backend at read time and not stored in the database:
- **Estimated commission per attributable order:**
  `commission_base_vnd × (commission_bps / 10000)`
- **Fixed campaign cost:**
  `sample_cost_vnd + content_cost_vnd + ad_spend_vnd` (sum of non-null components)
- **Contribution per attributable order:**
  `estimated_commission_per_order_vnd - variable_cost_per_order_vnd`
- **Break-even attributable orders:**
  `ceil(fixed_campaign_cost_vnd / contribution_per_order_vnd)` when contribution > 0
- **Optional expected economics:**
  Only computed when an explicit user `expected_attributable_orders` assumption is provided:
  - Expected commission: `expected_attributable_orders × estimated_commission_per_order`
  - Expected contribution: `(expected_attributable_orders × contribution_per_order) - fixed_campaign_cost`
  - Expected return on cost: `expected_contribution / total_cost`

**Prohibitions:**
- No sales-velocity earnings proxy.
- No automatic conversion-rate or attributable-order inference.
- No frontend financial calculation authority.

---

## 5. Persistence & Backup Compatibility Direction

- **Proposed Required Table:** Exactly one new table: `economics_scenarios`.
- **No Additional Tables in MVP:** No tables for cost line items, economics history, commission observations, formula definitions, or persisted derived metrics.
- **Backup Compatibility Advance:**
  - If persistence is implemented, `portable_backup_compatibility_version` must advance:
    `"2" → "3"`
    under unchanged ADR-004 same-version restore semantics.
  - Version 2 backups will be rejected with structured HTTP 400 by version 3 applications prior to quiescence.
  - No cross-version migration in Phase 6.
  - Fresh v3 backup required after successful upgrade.
  - Additive `Base.metadata.create_all()` + dynamic schema verification pattern will be reused.
- **Current State:** Compatibility code remains untouched in this reconciliation task.

---

## 6. Query Planning & Performance Constraints

### Candidate Query Budgets
- **Product scenario list / economics:** `<= 1` scenario query.
- **Collection member list with economics:** `<= 3` SQL queries total (Collection items query + snapshots/analytics query + batched default scenarios query).
- **Compare with economics (no Collection context):** `<= 3` SQL queries total.
- **Compare with economics (with Collection context):** `<= 4` SQL queries total.
- **Zero N+1:** Strictly enforced across all paths.

### Performance Ceilings
- **Representative regression ceiling recommendation:** `< 200ms` on representative 200-product / 5,000-snapshot paths.
- `< 50ms` remains an optimization/research target, not a hard gate unless adopted during planning.

---

## 7. Architecture Gate: ADR-005 Required

**`ADR-005 REQUIRED BEFORE PHASE 6 IMPLEMENTATION-PLAN APPROVAL`**

- **Proposed Title:** `ADR-005 — Affiliate economics assumptions, provenance, numeric semantics, and calculation authority`
- **Mandatory Sequence:** ADR-005 must be drafted, reviewed, and accepted by Project Control before `PHASE_6_PLAN.md` is approved.
- **Expected ADR Scope:**
  1. Separation of market evidence, user assumptions, and derived profitability;
  2. Prohibition of sold-count/sales-velocity attribution;
  3. Manual-first assumption provenance policy;
  4. Observed-price frozen proxy semantics;
  5. VND-only MVP constraint;
  6. Integer VND and basis-points storage;
  7. Backend calculation and deterministic rounding authority;
  8. Fixed campaign costs vs. variable costs per order;
  9. Strict null ≠ zero semantics;
  10. Product-scoped multiple scenarios with exactly-one-default invariant;
  11. Isolation from Trend Score, Watchlist, alerts, and crawler;
  12. Portable backup compatibility advance `"2" → "3"`;
  13. Future official Affiliate API source and override precedence.

*Note: ADR-005 is NOT created in this reconciliation task.*

---

## 8. Preserved Technical Debt & Deferred Scope

The following accepted non-blocking debt and deferred scope items are preserved unchanged:
- 1 High `source-map-js` advisory in the production dependency graph (`GHSA-68fv-2mgg-jv7q`), presently assessed build-time-only / non-runtime-reachable;
- Development-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`) in devDependencies;
- `StarletteDeprecationWarning` during test runs;
- Runtime `PRAGMA foreign_keys = 0` (`OFF`);
- Broad discovery and CAPTCHA bypass limitations deferred;
- Standalone executable packaging deferred;
- Cloud synchronization and multi-user capabilities deferred;
- All previous Phase 5 deferred items preserved.

---

## 9. Next Action

1. Draft and review **`ADR-005 — Affiliate economics assumptions, provenance, numeric semantics, and calculation authority`**.
2. Return to `00 — Project Control & Roadmap`.
