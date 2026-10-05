# Project Control Phase 5 Selection Record

- **Date:** 2026-10-05
- **Selected Phase:** Phase 5 — Opportunity Workspace: Collections, Saved Views & Product Compare
- **Phase 5 Status:** `SELECTED / PLANNING REQUIRED`
- **Research Gate:** `CLOSED`
- **Research Recommendation:** `RECOMMEND AS NEXT PRODUCT PHASE`
- **Research Readiness:** `RESEARCH READY FOR PROJECT CONTROL`
- **Implementation Status:** `NOT AUTHORIZED`
- **Phase Plan Status:** `NOT YET APPROVED`
- **Previous Release State:** Previous release remains `READY WITH DOCUMENTED NON-BLOCKING ISSUES` for the Windows / local / source-based runtime (`4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`). Selection of Phase 5 does not invalidate the previously qualified release.

---

## Selection Decision

Project Control has formally selected **Phase 5 — Opportunity Workspace: Collections, Saved Views & Product Compare** as the next product development phase.

The research gate is **CLOSED** with readiness assessed as `RESEARCH READY FOR PROJECT CONTROL`.

**Implementation is NOT AUTHORIZED** and no Phase 5 implementation plan has yet been approved.

---

## Core Boundary & Frozen Planning Constraints

1. **Watchlist & Refresh Authority:**
   - `WatchlistItem` remains the sole monitoring and scheduled-refresh authority.
   - Collections represent independent decision-organization state.
   - Collection membership never implies watch/unwatch.
   - Unwatch action does not remove Collection membership, status, or user notes.

2. **Provenance & Notes Separation:**
   - `WatchlistItem.notes` remains internal provenance.
   - User decision notes belong exclusively to `CollectionItem.notes`.

3. **Baseline Domain Model:**
   - `Collection`
   - `CollectionItem`
   - `SavedView`
   - Transient read-only Compare

4. **Item Status Vocabulary:**
   - Bounded status vocabulary: `new | reviewing | candidate | rejected`.
   - A product may belong to multiple Collections concurrently.
   - Tags and custom statuses are deferred.

5. **Compare Domain Constraints:**
   - Compare accepts exactly 2–5 products.
   - Compare reuses authoritative Phase 2 analytics directly.
   - No new comparison score formulas.
   - No per-product frontend API fanout.

6. **Saved Views Constraints:**
   - Saved Views use typed and versioned payloads.
   - Saved Views apply directly to existing component-local React state.
   - No URL-state synchronization scope.
   - Pagination offset and skip parameters are never persisted.

7. **Schema & Migration Boundaries:**
   - Minimum additive schema: `collections`, `collection_items`, `saved_views`.
   - Current `Base.metadata.create_all()` architecture remains the additive-table bootstrap.
   - No migration framework will be introduced solely for Phase 5.
   - Portable backup compatibility version must advance from `"1" → "2"` when the Phase 5 schema is implemented.
   - ADR-004 same-version restore semantics remain unchanged.
   - Cross-version migration remains deferred.
   - `ARCHITECTURE.md` update will be required during Phase 5.
   - No new ADR is currently required.

---

## Planning Performance Constraints

- **Collection membership list:** `<= 2` SQL queries.
- **Compare 2–5 products:** `<= 3` SQL queries total.
- **Saved View application:** Zero additional DB queries beyond the underlying Trends/Watchlist request.
- **Query discipline:** Zero N+1 query regressions across all endpoints.

---

## Explicit Phase 5 Out-of-Scope

The following capabilities are explicitly out of scope for Phase 5:
- Tags and labels;
- Custom workflow or status builders;
- Kanban boards, task tracking, due dates, and assignees;
- Persisted comparison sessions;
- Compare charts in baseline;
- AI recommendations and automated summaries;
- New Trend Score formulas;
- New alert-rule types;
- Crawler and discovery changes;
- CAPTCHA solving and anti-bot bypass;
- Affiliate profitability and payout models;
- Browser sync and cloud synchronization;
- Multi-user authentication and cloud backend;
- Standalone executable packaging;
- Arbitrary report builder;
- Cross-version restore migration;
- URL deep-link and filter synchronization project.

---

## Next Step

- Author and submit the formal Phase 5 Implementation Plan (`PHASE_5_PLAN.md`) for Project Control review and approval.
- Implementation remains strictly unauthorized until the Phase 5 plan receives formal sign-off.
