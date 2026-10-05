# Project Control Phase 5 Plan Approval Record

- **Date:** 2026-10-05
- **Decision:** `PHASE 5 PLAN APPROVED`
- **Phase:** Phase 5 — Opportunity Workspace: Collections, Saved Views & Product Compare
- **Authoritative Plan:** [`PHASE_5_PLAN.md`](PHASE_5_PLAN.md)
- **Authoritative Acceptance Criteria:** `P5-AC-01` through `P5-AC-36` (36 criteria authoritative)
- **Research Gate:** `CLOSED` (no additional research required before implementation)
- **Implementation Status:** `NOT AUTHORIZED` (implementation pending Project Control authorization)
- **Implementation Work Performed:** `NONE` (durable-state reconciliation only; no production code, tests, or runtime modified)
- **Architecture & ADR Status:** No new ADR required at planning gate; ADR-003 and ADR-004 remain active; `ARCHITECTURE.md` update required during implementation.
- **Previous Release State:** Previous release remains independently qualified as `READY WITH DOCUMENTED NON-BLOCKING ISSUES` for the Windows / local / source-based runtime (`4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`). Approving the Phase 5 plan does not invalidate the previously qualified release.

---

## 1. Approval Decision

Project Control has formally reviewed and approved the revised Phase 5 implementation plan:
[`PHASE_5_PLAN.md`](PHASE_5_PLAN.md).

- The plan gate is updated to: `APPROVED — IMPLEMENTATION PENDING PROJECT CONTROL AUTHORIZATION`.
- Implementation remains **NOT AUTHORIZED** until Project Control verifies the durable plan-approval reconciliation report.
- Zero implementation work has been started or performed.

---

## 2. Authoritative Acceptance Criteria Surface

The 36 criteria defined in [`PHASE_5_PLAN.md`](PHASE_5_PLAN.md) are authoritative:
- **P5-AC-01 through P5-AC-10:** Collections domain separation, persistence, cascade/isolation, unique membership, multi-collection membership, status vocabulary (`new | reviewing | candidate | rejected`), decision notes ownership, unwatch independence, reverse lookup index, and `<=2` query budget.
- **P5-AC-11 through P5-AC-15:** Saved Views persistence, exact Section 10 V1 typed schemas for Trends and Watchlist, strict payload rejection boundary, zero additional DB queries on view application, and no URL-state synchronization.
- **P5-AC-16 through P5-AC-25:** Product Compare cardinality (2–5 products), single bulk request path (no frontend fanout), shared `as_of_utc`, authoritative Phase 2 analytics reuse (no new score), honest null/stale handling, Watch/Collection context, bounded 7d alert summary, `<=3` query budget, quarantine exclusion, and sub-200ms benchmark verification.
- **P5-AC-26 through P5-AC-30:** Additive schema bootstrap via `Base.metadata.create_all()` without Alembic, compatibility version advance `"1" → "2"`, rejection of version-1 backups under unchanged same-version restore policy, version-2 backup round-trip, and isolated database test safety.
- **P5-AC-31 through P5-AC-34:** Frontend workspaces for Collections, Saved Views, transient Compare tray, and Compare matrix rendering with retry/stale protection.
- **P5-AC-35 through P5-AC-36:** Architecture/operator documentation updates and full repository test/build/health validation.

Criteria must not be remapped, renumbered, weakened, broadened, or reinterpreted during implementation.

---

## 3. Core Architectural Boundaries & Frozen Constraints

1. **Watchlist vs. Collections Domain Separation:**
   - `WatchlistItem` remains the sole monitoring and scheduled-refresh authority.
   - Collections represent independent decision-organization state.
   - Adding or removing a product from a Collection has zero crawler or scheduler side effects.
   - Unwatching a product does not remove Collection membership, review status, or decision notes.
   - Decision notes belong to `CollectionItem.notes`; `WatchlistItem.notes` remains internal provenance.

2. **Saved Views V1 Contracts:**
   - Saved Views apply to existing component-local React state.
   - Exact V1 typed payloads only; URL deep-linking / filter synchronization is out of scope.
   - Pagination offset/skip is never persisted; applying a Watchlist view explicitly starts at `skip=0`.

3. **Product Compare Architecture:**
   - Transient, read-only 2–5 product compare surface.
   - Single bulk backend query path using `<=3` SQL queries total (zero N+1).
   - Reuses authoritative Phase 2 analytics evaluated against a shared request `as_of_utc`.
   - No new comparison score formulas, winners, or AI summaries.

4. **Schema Bootstrap & Compatibility:**
   - Additive tables (`collections`, `collection_items`, `saved_views`) created via `Base.metadata.create_all()`.
   - No migration framework introduced solely for Phase 5.
   - Portable backup compatibility marker advances `"1" → "2"`.
   - ADR-004 same-version restore semantics unchanged; version-1 backups rejected before replacement.
   - Cross-version migration remains deferred.

---

## 4. Next Step

- Project Control reviews the reconciliation report and authorizes Phase 5 implementation.
- Return to `00 — Project Control & Roadmap`.
- Coding will proceed only upon explicit Project Control implementation authorization.
