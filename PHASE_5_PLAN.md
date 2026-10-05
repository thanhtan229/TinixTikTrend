# Phase 5 — Opportunity Workspace: Collections, Saved Views & Product Compare

Status: `APPROVED — IMPLEMENTATION PENDING PROJECT CONTROL AUTHORIZATION`  
Roadmap reference: `PROJECT_CONTROL_PHASE5_SELECTION.md` / latest reconciled `PLAN.md` / `PROJECT_STATUS.md`  
Created: `2026-10-05`  
Implementation authorization: `NOT AUTHORIZED`

Qualified product-code baseline: `4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`  
Required Project Control selection baseline: `ded7221dc443485412ff0d1086eb618ce29116be`

---

## 1. Objective

Phase 5 turns the existing product workflow:

`track → analyze → explain → monitor → alert → export`

into an additive decision workspace:

`organize → review → compare → decide → revisit`

without changing the semantics of monitoring, scheduled refresh, crawling, Phase 2 analytics, Phase 3 alerts, or Phase 4 backup/restore policy.

The phase introduces three deliberately bounded capabilities:

1. **Collections** — persistent user organization of existing local Products, with Collection-specific review status and decision notes.
2. **Saved Views** — persistent, typed, versioned presets for deterministic Trends and Watchlist view state.
3. **Product Compare** — a read-only, transient 2–5 Product comparison surface backed by one bulk backend path that reuses authoritative analytics and alert data.

The central architecture boundary is frozen:

> **Watchlist = monitoring. Collections = decision organization.**

Phase 5 must not blur those domains.

---

## 2. Context / current state

### 2.1 Project Control state supplied for this plan

The authoritative Phase 5 handoff states:

- Phase 1–4: complete / accepted.
- Previous release qualification: `READY WITH DOCUMENTED NON-BLOCKING ISSUES`.
- Phase 5: `SELECTED / PLANNING REQUIRED`.
- Research gate: `CLOSED`.
- Research recommendation: `RECOMMEND AS NEXT PRODUCT PHASE`.
- Research readiness: `RESEARCH READY FOR PROJECT CONTROL`.
- Implementation: `NOT AUTHORIZED`.
- Phase 5 plan: not yet approved.

### 2.2 Durable repository baseline requirement

The implementation checkout must contain or descend from the Project Control Phase 5 selection state represented by:

`ded7221dc443485412ff0d1086eb618ce29116be`

or an explicitly newer **reconciled docs-only** state approved by Project Control.

The accepted product-code baseline remains:

`4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`

Workstream 0 must verify actual repository ancestry and state before any Phase 5 production coding begins. A newer checkout is acceptable only when its difference from the selection state is reconciled documentation/project-control state or another change explicitly approved by Project Control; implementation must not silently treat unrelated newer product code as part of the Phase 5 baseline.

If ancestry, accepted product-code state, Phase 4 completion state, or the Phase 5 selection/research artifacts materially disagree with this baseline, implementation must stop and return the discrepancy to `00 — Project Control & Roadmap` before coding proceeds. Chat-environment copies of project documents are not evidence that durable repository documents are stale and must not be used to create a durable project-state discrepancy.

### 2.3 Existing behavior that remains authoritative

Phase 5 builds on and must preserve the following established behavior:

- Phase 2 analytics retain nulls, freshness/eligibility semantics, deterministic score/reason calculations, evidence confidence, quarantine exclusion, and bounded no-N+1 query behavior.
- Phase 3 Watchlist membership is the sole scheduled-refresh authority.
- Watch / Unwatch preserves historical Product, ProductSnapshot, alert-rule, and alert-event data.
- Alert evaluation remains product-scoped and post-commit; no new alert-rule type is introduced here.
- Frontend requests preserve stale-response protection, visible loading/error/retry behavior, UTC handling, and honest null/stale rendering.
- Phase 4 portable backup/restore remains same-version only and continues to use the existing backup service/schema validation architecture.

---

## 3. Research conclusions

The Phase 5 research gate is closed. Broad research must not be repeated unless implementation exposes a genuinely new unresolved technical question.

The implementation plan is constrained by these research conclusions:

1. Collections are a **new decision-organization domain**, not a new monitoring mechanism.
2. `WatchlistItem` remains the only authoritative scheduled-refresh membership.
3. An unwatched local Product may remain in Collections and may still be compared.
4. User decision notes belong only on `CollectionItem.notes`; `WatchlistItem.notes` remains internal provenance.
5. Saved Views should persist a **typed/versioned deterministic definition**, not SQL, arbitrary DSL, result rows, or transient UI state.
6. Saved Views V1 apply to the dashboard's current component-local state/fetch path; URL/search-parameter synchronization is not required.
7. Watchlist Saved Views must never persist `skip`; applying one starts from the beginning of the result set.
8. Compare is transient and read-only, accepts exactly 2–5 Products, and is not a persistent Comparison domain.
9. Compare must reuse Phase 2 analytics rather than creating a new score, ranking formula, or category-relative normalization.
10. Compare must use one bulk backend request; browser fanout to one Product endpoint per selection is prohibited.
11. Compare alert information must be summarized in a grouped/batched query, not retrieved as full per-Product histories.
12. The existing `Base.metadata.create_all()` bootstrap is sufficient for the three additive Phase 5 tables; Alembic must not be introduced solely for this phase.
13. The portable backup compatibility version must advance from `"1"` to `"2"`; same-version restore semantics remain unchanged and no cross-version migration is added.
14. `BackupService.get_required_schema()` must continue deriving required tables from `Base.metadata.tables`; no parallel manual table allowlist is introduced.
15. No new ADR is currently required. ADR-003 must not be modified, and ADR-004 must not be semantically changed.

---

## 4. In scope

### 4.1 Collections

- Persistent `Collection` records.
- Persistent `CollectionItem` membership records.
- Collection create/list/get/update/delete.
- Collection member list.
- Add an existing local Product to a Collection.
- Remove a Product from a Collection.
- Collection-specific review status.
- Collection-specific user decision notes.
- Reverse lookup of Collections containing a Product.
- Add-to-Collection actions from Trends, Watchlist, and Product Detail.
- A compact Collections workspace/selector in the existing dashboard.

### 4.2 Saved Views

- Persistent `SavedView` records.
- Scopes: `trends` and `watchlist` only.
- Typed/versioned payload V1.
- Saved View list/get/create/update/delete.
- Strict validation of scope, payload version, filter values, sort values, and payload shape.
- Save/apply/delete controls on Trends and Watchlist.
- Apply through the existing component-local state and fetch path.

### 4.3 Compare

- Transient Compare tray in frontend state.
- Exactly 2–5 unique Product IDs.
- One typed read-only bulk backend compare path.
- Bulk Product identity/current data.
- Bulk authoritative Phase 2 analytics.
- Bulk Watch state.
- Optional selected-Collection decision context.
- Batched recent alert summary.
- Compact comparison modal/page/table.

### 4.4 Schema and portability

- Additive creation of `collections`, `collection_items`, and `saved_views`.
- Portable backup compatibility version `"2"`.
- Backup/restore validation and regression coverage for the new tables.
- Architecture documentation updates required by Phase 5 completion.

---

## 5. Out of scope

Phase 5 must not include:

- Tags or labels.
- Custom workflow/status builders.
- Kanban, tasks, due dates, or assignees.
- Persisted Comparison sessions/entities.
- Compare charts.
- AI recommendation or AI summarization.
- New Trend Score formulas.
- Category-relative scoring or percentiles.
- New alert-rule/event types.
- Crawler/discovery expansion.
- CAPTCHA solving, anti-bot bypass, or stealth circumvention.
- Affiliate profitability or commission modeling.
- Browser/cloud synchronization.
- Multi-user accounts.
- Cloud backend/services.
- Executable packaging.
- Arbitrary report builders.
- Cross-version restore migration.
- URL/search-param deep-link/filter synchronization.
- Saved View default/favorite behavior in V1.
- Collection archive semantics in the baseline; Phase 5 uses explicit delete semantics only.
- Broad refactors unrelated to satisfying Phase 5 acceptance criteria.

Attractive but unnecessary work discovered during implementation must be deferred and reported rather than silently added.

---

## 6. Existing-state assumptions

These assumptions must be checked against the actual repository during Workstream 0 without redefining approved Phase 5 contracts:

1. The implementation checkout satisfies the repository-baseline requirement in Section 2.2 and contains the accepted Phase 4 portable backup/restore implementation with compatibility marker `"1"`.
2. `Base.metadata.create_all()` remains the active schema bootstrap mechanism and there is no Alembic migration framework.
3. Model imports are structured so new SQLAlchemy models can be registered in `Base.metadata` before bootstrap and backup schema validation runs.
4. `BackupService.get_required_schema()` derives required tables from `Base.metadata.tables`.
5. Trends and Watchlist filters are driven by component-local React state rather than URL/search parameters.
6. The approved Trends Saved View V1 field set is frozen in Section 10.2: `category`, `trend_state`, `measured_only`, `confidence`, `sort_by`, `sort_direction`, `limit`, `search`, and `min_score`. Trends has no normal offset and Phase 5 must not invent one.
7. The approved Watchlist Saved View V1 field set is frozen in Section 10.3: `category`, `trend_state`, `measured_only`, `confidence`, `sort_by`, `sort_direction`, and `limit`. Operational `skip` remains transient and is never persisted. Existing local `search` and `min_score` state do not apply to Watchlist V1.
8. Workstream 0 may verify those frozen field names/semantics against source and may reuse existing endpoint validators/constants, but it may not add, remove, rename, or otherwise redefine the approved V1 field sets. A material source mismatch must be returned to Project Control before implementation proceeds.
9. Phase 2 analytics can be reused for a bounded set of Products without altering formulas. A small extraction/refactor is permitted only if necessary to expose the same authoritative calculation to the bulk Compare service.
10. AlertEvent has an existing Product-oriented query path/index suitable for one grouped recent-summary query over the requested Products.
11. Runtime SQLite foreign-key enforcement may be disabled (`PRAGMA foreign_keys = 0`), so application logic must enforce destructive boundaries without relying only on database cascades.
12. Existing Product deletion, if any, already has an ownership convention. Phase 5 may integrate dependent `CollectionItem` cleanup into that path but must not make `CollectionItem` an owner of Product.
13. The existing frontend/API naming and module conventions should be extended rather than replaced by a new parallel architecture.

If any material assumption is false, Codex must report the discrepancy and the smallest required plan adjustment to Project Control. It must not invent a broad replacement architecture or silently redefine the Saved View V1 contracts.

---

## 7. Domain / persistence design

### 7.1 `Collection`

Minimum persistent fields:

- `id`
- `name`
- optional `description`
- `created_at`
- `updated_at`

Rules:

- Name must be non-empty after the repository's normal whitespace normalization.
- Duplicate Collection names are allowed unless an existing project-wide naming convention already forbids them; do not add a new uniqueness rule solely for Phase 5.
- No workflow metadata, owner/user field, tags, ranking, color system, or arbitrary metadata blob.
- No archive field in V1. Delete is explicit and destructive only to the Collection and its CollectionItems.
- Deleting a Collection must never delete Product, ProductSnapshot, WatchlistItem, AlertRule, or AlertEvent records.

### 7.2 `CollectionItem`

Minimum persistent fields:

- `id`
- `collection_id`
- `product_id`
- `review_status`
- `notes`
- `created_at`
- `updated_at`

Required constraints:

- `UNIQUE(collection_id, product_id)`.
- Reverse lookup index on `collection_items(product_id)`.
- `collection_id` references Collection.
- `product_id` references Product but the relationship must not imply ownership of Product.

Fixed `review_status` vocabulary:

- `new`
- `reviewing`
- `candidate`
- `rejected`

Rules:

- Default status: `new`.
- Status and notes are scoped to a specific `(collection_id, product_id)` membership.
- A Product may belong to multiple Collections and may have different status/notes in each.
- `notes` stores user decision notes only. Do not reuse or copy `WatchlistItem.notes`.
- Removing a CollectionItem deletes only that membership row.
- Removing a Product from Watchlist must not remove or mutate CollectionItem.
- Removing Collection membership must not mutate AlertRule/AlertEvent.
- Adding to Collection must not create Watchlist membership or schedule collection.
- Only existing non-quarantined local Products may be added. Collection membership is not a Product-ingestion path.

### 7.3 `SavedView`

Minimum persistent fields:

- `id`
- `name`
- `scope`
- `payload_version`
- `payload`
- `created_at`
- `updated_at`

Rules:

- `scope` is exactly `trends` or `watchlist`.
- `payload_version` is integer `1` for Phase 5.
- `payload` is stored as structured JSON using the repository's normal SQLAlchemy/SQLite JSON approach.
- Scope is immutable after creation in V1. Update requests attempting to change scope are rejected; moving a view between scopes requires creating a new Saved View.
- Update may change name and the validated payload for the existing scope/version.
- Payloads are **strict, full-shape objects**: all keys defined for that scope in Section 10 are required; unknown keys and scope-inappropriate keys are rejected; payload decoding does not invent omitted defaults.
- Filter/sort enum validation must reuse or mirror the authoritative existing Trends/Watchlist endpoint constants so Saved Views cannot store a state the underlying view cannot execute.
- No default/favorite Saved View behavior in Phase 5.
- Duplicate names are allowed; identity is by SavedView ID.
- No SQL, arbitrary filter DSL, result rows, Product-ID result sets, pagination offset, loading/error state, stale-response token, modal state, Compare selection, or URL/search-param state may be persisted.

### 7.4 Ownership / cascade model

Application logic is authoritative because SQLite foreign keys may be disabled at runtime.

Required behavior:

- `Collection` may own its `CollectionItem` children for ORM lifecycle purposes.
- Product must **not** own-orphan `CollectionItem` in a way that lets CollectionItem deletion delete Product.
- Collection deletion must explicitly delete dependent CollectionItems and then the Collection in one transaction; correctness must not depend solely on `ON DELETE CASCADE`.
- If an existing Product-delete path exists, it must explicitly handle dependent CollectionItems using existing Product ownership conventions before Product deletion; no new Product delete feature is introduced for Phase 5.
- Unwatch only removes WatchlistItem according to existing Phase 3 behavior.
- Collection-item removal only removes CollectionItem.
- Transaction failure must roll back the entire requested Collection mutation.

---

## 8. API / service design

Exact route prefixes and file names must follow the repository's existing FastAPI conventions. The contracts below are normative even if route spelling differs slightly to match those conventions.

### 8.1 Collections service boundary

Required operations:

- List Collections.
- Get one Collection.
- Create Collection.
- Update Collection name/description.
- Delete Collection.
- List Collection members.
- Add existing Product to Collection.
- Remove Product from Collection.
- Update CollectionItem status and/or notes.
- Reverse lookup: list Collections containing a Product.

Behavior:

- Duplicate `(collection_id, product_id)` add returns a conflict/domain error; do not create duplicate rows.
- Missing Collection/Product returns the repository-standard not-found response.
- Quarantined Product is unavailable for Collection membership through normal APIs.
- Member list must load Product identity in bulk and must not issue one Product query per member.
- Collection mutations must never call crawler, scheduler, watch, or alert-rule creation logic.

Conceptual REST shape, adapted to existing router conventions:

- `GET <collections-prefix>`
- `POST <collections-prefix>`
- `GET/PATCH/DELETE <collections-prefix>/{collection_id}`
- `GET <collections-prefix>/{collection_id}/items`
- `POST <collections-prefix>/{collection_id}/items`
- `PATCH/DELETE <collections-prefix>/{collection_id}/items/{product_id}`
- `GET <products-prefix>/{product_id}/collections` or the equivalent existing lookup style

Do not add an arbitrary query language.

### 8.2 Saved Views service boundary

Required operations:

- List Saved Views, optionally filtered by `scope`.
- Get one Saved View.
- Create Saved View.
- Update Saved View name/payload for its existing immutable scope.
- Delete Saved View.

Validation happens at the API/service boundary and through typed scope-specific schemas:

- scope is exactly `trends` or `watchlist`;
- `payload_version` is exactly integer `1`;
- Trends payload key set is exactly the nine keys frozen in Section 10.2;
- Watchlist payload key set is exactly the seven keys frozen in Section 10.3;
- every required key must be present and unknown keys are rejected;
- `scope` cannot be changed by update;
- enum/range values must pass the authoritative existing endpoint/state validation described in Section 10;
- Watchlist `skip`, `search`, and `min_score` are rejected if supplied;
- Trends offset/skip is rejected because no normal Trends offset exists;
- SQL, arbitrary DSL, result rows/Product IDs, loading/error state, stale-response tokens, modal state, Compare selection, and URL/search-param state are rejected.

Saved View listing returns enough typed payload data for frontend apply. Applying an already loaded Saved View must not require a separate SavedView database fetch; it hydrates current component-local state and follows the existing Trends/Watchlist fetch path.

### 8.3 Compare service boundary

Use one read-only service and one bulk API call.

Conceptual request:

```json
{
  "product_ids": [21, 22],
  "collection_id": 7
}
```

`collection_id` is optional and supplies one selected Collection context only. It must not cause retrieval of arbitrary full Collection histories.

At the start of each Compare request, the service captures exactly one timezone-aware UTC timestamp:

`as_of_utc`

That value is captured once before Product analytics/alert evaluation and is reused for the entire response. It is not recomputed per Product, per query, or per analytics call.

Input rules:

- At least 2 Product IDs.
- At most 5 Product IDs.
- IDs must be unique.
- Frontend dedupes selection by Product ID.
- Backend rejects duplicate IDs rather than silently changing request cardinality.
- Preserve caller Product order in the response.
- If any requested Product is missing or quarantined, reject the compare request with the repository-standard not-found/unavailable response and identify unavailable IDs; do not silently return a partial comparison.
- If `collection_id` is supplied and missing, reject the request; a Product not belonging to that valid Collection simply has null Collection context.

Top-level response must expose `as_of_utc` using the repository's normal explicit UTC serialization convention, unless the existing response envelope has an equivalent explicit request-evaluation timestamp field that can represent the same value without ambiguity.

Response per Product should include only authoritative current data already available in the product:

- Product ID/identity/title/shop/category.
- Watch state.
- Optional selected-Collection context: membership present/absent, `review_status`, `notes`.
- Trend Score.
- Trend eligibility/state.
- Evidence confidence / measured-vs-estimated semantics already exposed by Phase 2.
- Deterministic Why Trending reasons.
- 24h sales velocity.
- 24h sales delta.
- Existing authoritative 7d/bounded deltas where available.
- Acceleration.
- Review metrics currently exposed by analytics.
- Current price.
- Freshness.
- Rating/review count.
- Compact recent-alert summary.

Every Product's Phase 2 analytics evaluation must receive the same `current_time=as_of_utc`. Current Watchlist membership and selected-Collection membership are ordinary current read state; they are not historical-as-of data and must not alter analytics calculations.

Compare must not calculate or expose:

- a new comparison score;
- a new rank;
- a winner/recommendation field;
- normalized substitute values for missing metrics;
- synthetic eligibility.

### 8.4 Compare query model

The service must fit within **3 SQL queries total** for 2–5 Products.

Target model:

1. **Products + bounded snapshots + Watch state** in one bulk query or one equivalent eager-loaded statement. Reuse the same authoritative Phase 2 analytics functions over the resulting bounded data, passing the single request `as_of_utc` as `current_time` for every Product.
2. **Grouped recent AlertEvent summary** for all Product IDs in one query, bounded by the same `as_of_utc` as defined in Section 8.5.
3. **Selected Collection context** for all Product IDs in one query when `collection_id` is supplied; if no Collection context is requested, this query may be omitted.

Alternative shapes are allowed only if they stay within the same total query budget, preserve one shared `as_of_utc`, and preserve zero N+1 behavior.

### 8.5 Alert summary contract

Baseline Compare alert summary is intentionally small:

- `recent_alert_count_7d`
- `latest_alert_at`

The bounded event set for each requested Product is exactly:

`created_at >= as_of_utc - 7 days`

and

`created_at <= as_of_utc`

Rules:

- Both interval boundaries are inclusive.
- Future AlertEvents (`created_at > as_of_utc`) are excluded.
- `recent_alert_count_7d` counts only events in that bounded set.
- `latest_alert_at` is the maximum `created_at` from that same bounded set and is null when the bounded set is empty.
- All Products use the same request-level `as_of_utc`.
- Do not retrieve complete histories per Product.
- Do not add a new AlertRule type.
- Optional latest-event metadata remains deferred unless Project Control explicitly adds it in a later plan; Phase 5 baseline does not require it.

---

## 9. Frontend design

UI changes must be additive and compact. Do not redesign the dashboard.

### 9.1 Collections workspace

Add a compact Collections surface consistent with the existing dashboard navigation/layout.

Minimum behavior:

- List Collections.
- Create Collection.
- Rename/update description.
- Delete Collection with explicit confirmation that only Collection organization data is removed.
- Select a Collection and show members.
- Display Product identity plus Collection-specific `review_status` and `notes`.
- Edit status from the fixed vocabulary.
- Edit/save notes explicitly; avoid introducing a complex background autosave system solely for Phase 5.
- Remove Product from Collection.
- Surface Watch state without making it a Collection responsibility.

### 9.2 Add-to-Collection actions

Required on:

- Trends.
- Watchlist.
- Product Detail.

Behavior:

- Operates only on an already existing local Product.
- Lets the user choose an existing Collection.
- Shows visible success/error state.
- Duplicate membership is handled as an explicit already-added/conflict state, not by creating another row.
- Does not automatically Watch the Product.
- Does not mutate alert rules.

Inline Collection creation from the add dialog is not required; Collection creation is available from the workspace.

### 9.3 Saved View controls

Add to Trends and Watchlist:

- Saved View selector.
- Save current view.
- Update/rename selected Saved View.
- Delete selected Saved View.
- Apply selected Saved View.

Applying must:

- Populate the existing component-local state.
- Trigger the existing normal data-fetch path once.
- Preserve existing stale-response protection.
- Preserve visible loading/error/retry behavior.
- On Watchlist, set `skip = 0` regardless of the user's current page.
- Not modify URL/search parameters.
- Not persist Compare selection.

The page should preload/list Saved Views for its scope. Selecting/applying a loaded view therefore causes **0 SavedView DB queries** beyond the underlying normal Trends/Watchlist request.

### 9.4 Compare tray

Use transient frontend state only; do not use database, localStorage, URL parameters, or browser/cloud sync.

Minimum behavior:

- Products may be selected for Compare from Trends, Watchlist, and Collection member lists.
- Selection is keyed/deduped by Product ID.
- Tray may show 1 selected Product, but Compare action is disabled until 2 are selected.
- Cap selection at 5 with an accessible visible message.
- Remove one selection or clear all.
- Reload/navigation state may clear selection; persistence is intentionally out of scope.
- Opening Compare makes exactly one backend compare request.

### 9.5 Compare surface

Use a compact table/modal/page consistent with current UI conventions.

Must show:

- Product identity.
- Watch state.
- Collection status/notes when a Collection context was supplied.
- Authoritative analytics fields.
- Evidence confidence.
- Why Trending reasons.
- Stale/ineligible state.
- Null values as unavailable/empty according to current UI convention, never zero-filled.
- Recent alert count and latest alert timestamp.

No charting and no winner score.

### 9.6 Frontend quality invariants

All new flows must preserve:

- stale-response protection;
- visible loading states;
- visible errors;
- safe retry;
- null preservation;
- evidence confidence;
- stale/ineligible labeling;
- keyboard/accessibility behavior consistent with existing components;
- no optimistic success state that survives a failed backend mutation.

---

## 10. Saved View contract

### 10.1 Common envelope and strictness

Saved View V1 uses `payload_version = 1` on the `SavedView` row. The JSON payload contains only the scope-specific fields below; `scope` itself remains a row field and is immutable after creation.

For both scopes:

- payload is a strict full-shape object;
- every listed key is required;
- unknown keys are rejected;
- missing keys are rejected rather than filled with implicit decode defaults;
- `payload_version` values other than integer `1` are rejected;
- update cannot change `scope`;
- no SQL, arbitrary filter DSL, result rows, Product-ID result sets, pagination offset/skip, loading/error state, stale-response token, modal/dropdown state, Compare selection, or URL/search-param state may be stored;
- applying a Saved View hydrates the existing component-local state and uses the existing fetch path; it does not introduce URL/search-param synchronization.

Validation sources are frozen as follows:

- `trend_state`: existing Phase 2 enum — `all`, `eligible`, `stale`, `insufficient_signal`.
- `confidence`: existing Phase 2 confidence vocabulary — `low`, `medium`, `high`; `null` means no confidence filter.
- `measured_only`: existing Phase 2 evidence filter boolean; `false` means no measured-only restriction.
- `sort_by`: existing Phase 2 sort enum — `trend_score`, `sales_velocity`, `sales_delta`, `review_delta`, `freshness`.
- `sort_direction`: existing sort direction enum — `asc`, `desc`.
- `category`: existing category-filter semantics; persisted as a category string accepted by the current endpoint or `null` for no category filter. Phase 5 does not create a separate category enum.
- `limit`: required non-null integer validated by the same existing endpoint bounds/validator used by the corresponding Trends/Watchlist request. Phase 5 does not create a wider or separate Saved View limit range.

Workstream 0 verifies that these frozen schemas map to the selected repository baseline and binds to existing constants/validators where practical. It may not redefine the V1 key sets or semantics. A material baseline mismatch returns to Project Control.

### 10.2 Trends Saved View V1

The persisted JSON key set is **exactly**:

```text
category
trend_state
measured_only
confidence
sort_by
sort_direction
limit
search
min_score
```

Field semantics and normalized no-filter representation:

- `category: string | null` — `null` means no category restriction.
- `trend_state: "all" | "eligible" | "stale" | "insufficient_signal"` — required and never null; `"all"` is the no-restriction value.
- `measured_only: boolean` — required; `false` is the no-restriction value.
- `confidence: "low" | "medium" | "high" | null` — `null` means no confidence restriction.
- `sort_by: "trend_score" | "sales_velocity" | "sales_delta" | "review_delta" | "freshness"` — required and never null.
- `sort_direction: "asc" | "desc"` — required and never null.
- `limit: integer` — required and never null; validated by the current Trends endpoint limit validator/bounds.
- `search: string` — current deterministic Trends component-local text-search state; empty string `""` means no local text filter. It remains frontend-local and does not create a new backend search query parameter.
- `min_score: number | null` — current deterministic Trends component-local minimum-score state; `null` means no minimum-score filter. Non-null values must pass the same range/normalization used by the current Trends control; Phase 5 does not invent a new score scale.

No `skip`, `offset`, page number, or equivalent pagination key exists in Trends V1. Normal Trends results expose no normal offset, so none may be persisted or invented.

Applying a Trends Saved View restores all nine values into the existing Trends state path and then issues the normal Trends data request. Local `search` and `min_score` continue to behave as the existing component-local deterministic filters; Phase 5 does not move them into URL state or create new backend filtering semantics.

### 10.3 Watchlist Saved View V1

The persisted JSON key set is **exactly**:

```text
category
trend_state
measured_only
confidence
sort_by
sort_direction
limit
```

Field semantics and normalized no-filter representation:

- `category: string | null` — `null` means no category restriction.
- `trend_state: "all" | "eligible" | "stale" | "insufficient_signal"` — required and never null; `"all"` is the no-restriction value.
- `measured_only: boolean` — required; `false` is the no-restriction value.
- `confidence: "low" | "medium" | "high" | null` — `null` means no confidence restriction.
- `sort_by: "trend_score" | "sales_velocity" | "sales_delta" | "review_delta" | "freshness"` — required and never null.
- `sort_direction: "asc" | "desc"` — required and never null.
- `limit: integer` — required and never null; validated by the current Watchlist endpoint limit validator/bounds.

Watchlist V1 explicitly does **not** contain `search` or `min_score`; those existing local deterministic fields apply to Trends, not Watchlist. Watchlist operational `skip` exists but is transient and is never persisted. `skip`, derived page number, `search`, and `min_score` are rejected as unknown/scope-inappropriate Watchlist payload keys.

Applying a Watchlist Saved View restores the seven persisted values, explicitly sets current `skip = 0`, and then issues the normal Watchlist request from the beginning of that result set.

### 10.4 Payload version behavior

- Phase 5 supports only `payload_version = 1`.
- Unknown/future versions are rejected with a clear validation error.
- V1 payloads are not silently upgraded or downgraded.
- Saved View cross-version migration is future work.

---

## 11. Compare contract

### 11.1 Cardinality and identity

- Exactly 2–5 unique Product IDs per compare request.
- Frontend prevents duplicate tray entries.
- Backend validates uniqueness independently.
- Response order matches request order.
- Missing/quarantined Product makes the request fail explicitly rather than returning misleading partial data.

### 11.2 Request-level `as_of_utc` and authoritative analytics reuse

At Compare service entry, capture exactly one timezone-aware UTC request timestamp, `as_of_utc`, before Product analytics and alert-summary evaluation. The same value is reused for the entire response and is exposed at the response top level using the repository's normal UTC serialization convention or an equivalent explicit response-envelope timestamp.

For every requested Product:

- existing Phase 2 analytics logic is reused;
- the analytics calculation receives the same `current_time=as_of_utc`;
- no Product may obtain a separately sampled current time;
- formulas remain behaviorally equivalent to Phase 2;
- bounded snapshot loading and quarantine exclusion remain enforced;
- existing Phase 2 tests continue to pass;
- no new scoring/ranking semantics are introduced.

A small extraction into a shared batch-safe helper is permitted only when needed to pass one `as_of_utc` consistently without changing analytics formulas or results.

### 11.3 Null / stale / eligibility semantics

- Null stays null.
- Ineligible Product remains ineligible.
- Stale Product may be displayed but must be labeled stale.
- Compare must not synthesize a rank for ineligible Products.
- Evidence confidence retains its existing meaning and is not used as a hidden score multiplier.
- All freshness/staleness/eligibility decisions that depend on current time use the same request `as_of_utc`.

### 11.4 Collection context

When `collection_id` is supplied:

- Return the corresponding CollectionItem `review_status` and `notes` for each member Product.
- Non-member Products return null Collection context.
- Do not copy status/notes from another Collection.
- Do not mutate Collection state from Compare.
- Collection membership is current read state; it does not use or change `as_of_utc` analytics semantics.

### 11.5 Watch state

Return current Watchlist membership as a display field only. Watch state is current read state, not historical-as-of state. Compare must not add/remove Watchlist membership or let Watch state change Phase 2 analytics semantics.

### 11.6 Alert context

Return the compact grouped summary defined in Section 8.5 from exactly the bounded AlertEvent set:

`as_of_utc - 7 days <= created_at <= as_of_utc`

Future events are excluded. `latest_alert_at` is selected only from that bounded set. No full per-Product alert history and no new alert type are introduced.

---

## 12. Schema / bootstrap / compatibility behavior

### 12.1 New tables

Add exactly these baseline tables:

- `collections`
- `collection_items`
- `saved_views`

Do not add:

- tags table;
- comparisons table;
- decision-history table;
- workflow tables;
- Saved View result tables.

### 12.2 Bootstrap

- Register/import the new SQLAlchemy models before `Base.metadata.create_all()` executes.
- Continue using the existing additive `create_all()` bootstrap.
- Do not introduce Alembic solely for Phase 5.
- Startup on an existing Phase 4 database adds exactly the three missing Phase 5 tables: `collections`, `collection_items`, `saved_views`.
- Existing Phase 1–4 portable database tables and rows must remain unchanged except for the intentional compatibility-marker transition described below.
- Bootstrap remains idempotent across repeated starts.
- Phase 5 startup must not reach normal application-ready/scheduler continuation until required Phase 5 schema presence and compatibility-marker state have both been verified successfully.

### 12.3 Portable compatibility marker

The Phase 4 compatibility marker:

`portable_backup_compatibility_version = "1"`

must become:

`portable_backup_compatibility_version = "2"`

Ownership rule:

- Update the existing Phase 4 backup/restore compatibility-version owner/constant in place.
- Do not create a second version constant in Collection/SavedView code.
- The Phase 5 schema registration/bootstrap and marker transition belong to the same startup/implementation gate.
- On a representative Phase 4 database whose current marker is `"1"`, startup first ensures the required Phase 5 tables exist, verifies the required schema, then advances the existing compatibility owner to `"2"` before normal application readiness.
- A repeated startup with already-correct Phase 5 schema and marker `"2"` is a no-op for compatibility state.
- If table creation, required-schema verification, or the marker transition fails, startup must fail/withhold normal application readiness. The application must never continue normally with Phase 5 tables while still advertising compatibility `"1"`.
- A retry after such a failure must be safe/idempotent: existing additively created Phase 5 tables may remain, but readiness stays blocked until schema verification succeeds and the existing owner reports `"2"`.

### 12.4 Required schema

- Keep `BackupService.get_required_schema()` deriving required schema from `Base.metadata.tables`.
- Ensure the three Phase 5 model tables are present in metadata when required schema is computed.
- Do not introduce a separate manual allowlist for Phase 5 tables.

### 12.5 Mandatory isolated Phase-4 → Phase-5 in-place upgrade gate

Before Phase 5 can satisfy completion, run an isolated file-backed upgrade test starting from a representative accepted Phase 4/version-1 database.

The fixture must contain representative existing portable state, including:

- Product rows;
- ProductSnapshot rows;
- Watchlist membership;
- AlertRule rows;
- AlertEvent rows;
- alert evaluation/cursor state;
- existing `SystemMetadata`, including unrelated metadata plus compatibility marker `"1"`.

The test must prove, in order:

1. startup begins from Phase 4 schema/state with compatibility marker `"1"`;
2. the pre/post user-table set difference is exactly `collections`, `collection_items`, `saved_views`;
3. representative Phase 1–4 portable database state and unrelated `SystemMetadata` values remain preserved;
4. the existing compatibility owner advances to `"2"` only after required Phase 5 schema is present/verified;
5. normal application readiness is reached only when required schema and marker `"2"` are both correct;
6. a second startup is idempotent and preserves the same state;
7. injected schema/bootstrap/required-schema/marker-transition failure prevents normal application readiness rather than running with a Phase 5 schema while advertising `"1"`.

This is an in-place startup/bootstrap validation, not cross-version restore migration. It must use an isolated temporary/file-backed database and must never use real `backend/affiliate.db`.

---

## 13. Backup / restore implications

Backup/restore compatibility is a mandatory Phase 5 workstream.

Required behavior:

1. New Phase 5 backups advertise compatibility version `"2"`.
2. A Phase 4/version-1 backup candidate is rejected by the Phase 5 app under the existing same-version policy.
3. Rejection occurs during validation before destructive restore/replace behavior.
4. No cross-version conversion or restore migration is attempted.
5. A valid version-2 backup passes required-schema validation with `collections`, `collection_items`, and `saved_views` present.
6. Version-2 backup/restore round-trip preserves Collections, CollectionItems, review status, CollectionItem notes, Saved Views, and Saved View scope/version/payload.
7. Existing Product/ProductSnapshot/Watchlist/AlertRule/AlertEvent/cursor/SystemMetadata portable state remains preserved according to Phase 4 behavior.
8. The separate in-place Phase-4 → Phase-5 startup/bootstrap gate in Section 12.5 proves upgrade of a live-format version-1 database to schema/compatibility version `"2"`; that gate does not make version-1 backup files restorable by the version-2 app.
9. TikTok local session state remains non-portable and excluded exactly as Phase 4 defines.
10. Existing rollback/recovery behavior for failed restore remains unchanged.
11. All destructive restore/recovery and in-place upgrade tests must use isolated temporary/file-backed databases and must never touch real `backend/affiliate.db`.

Operator-facing documentation must make the compatibility consequence explicit: a Phase 4/version-1 portable backup is not restorable by the Phase 5/version-2 application under unchanged same-version semantics. After successful Phase 5 in-place bootstrap, operators should create a new version-2 portable backup. Documentation must not promise cross-version migration, and TikTok session portability remains excluded.

---

## 14. Architecture constraints

The following invariants are mandatory:

1. **Monitoring and decision organization are separate domains.**
2. **Watchlist remains scheduler authority.**
3. Collections have no monitoring side effect.
4. Adding to Collection never automatically Watches a Product.
5. Unwatch preserves Collection membership/status/notes.
6. Collection removal/deletion never destroys Product, ProductSnapshot, WatchlistItem, AlertRule, or AlertEvent history.
7. An unwatched local Product may remain in Collections and Compare.
8. Collection status/notes are `CollectionItem`-scoped.
9. `WatchlistItem.notes` remains internal provenance; user decision notes belong only to `CollectionItem.notes`.
10. Saved Views store typed/versioned definitions, not SQL, result sets, arbitrary DSL, or transient UI state.
11. Saved Views V1 apply to component-local state and do not require URL/search-param synchronization.
12. Compare is transient, read-only, and reuses authoritative analytics.
13. No new comparison score/rank/recommendation formula.
14. Existing null, stale, eligibility, evidence-confidence, and quarantine semantics remain authoritative.
15. Collections and Compare must preserve bounded-query/no-N+1 behavior.
16. Portable backup compatibility version is `"2"`; same-version restore policy is unchanged.
17. Runtime correctness must not rely only on SQLite FK cascades.
18. Phase 1–4 accepted behavior outside Phase 5 scope must remain stable.

Relevant ADRs:

- ADR-003: active; do not modify its monitoring/alert semantics.
- ADR-004: active; same-version portable backup/restore semantics remain unchanged.

No new ADR is currently required. If implementation reveals a costly-to-reverse, cross-cutting decision not already covered by the research, implementation must stop that decision from being hidden in code and flag an ADR requirement to Project Control.

---

## 15. Edge cases / failure handling

### 15.1 Collections

- Empty/whitespace Collection name: reject.
- Missing Collection: not found.
- Missing/quarantined Product: reject add.
- Duplicate membership: reject/conflict; database unique constraint remains final race protection.
- Concurrent duplicate add: exactly one membership survives; other request receives conflict/error without duplicate rows.
- Product belongs to multiple Collections: supported.
- Same Product has different status/notes across Collections: supported and isolated.
- Unwatch while in one or more Collections: Collection state unchanged.
- Delete Collection: explicitly remove its CollectionItems and Collection in one transaction; preserve all Product/history/monitoring/alert records.
- Delete/remove transaction failure: rollback; no partial membership mutation.
- Existing Product deletion, if supported: clean dependent CollectionItems according to existing ownership conventions without relying only on FK cascade.

### 15.2 Saved Views

- Unknown scope: reject.
- Unknown `payload_version`: reject.
- Invalid JSON/object shape: reject.
- Unknown keys: reject.
- Invalid filter/sort enum: reject.
- Watchlist payload containing `skip`: reject.
- Payload containing SQL/DSL/result IDs/transient state: reject by schema.
- Deleted Saved View selected in stale frontend state: surface not-found/error and refresh selector safely.
- Underlying normal Trends/Watchlist request fails after apply: retain visible error/retry behavior; do not report apply as successful data load.

### 15.3 Compare

- Fewer than 2 IDs: reject/disable.
- More than 5 IDs: reject/disable.
- Duplicate IDs: frontend dedupes; backend rejects duplicate payload independently.
- Missing/quarantined ID: fail entire compare request with unavailable IDs.
- Optional Collection does not exist: reject.
- Product not in selected Collection: return null Collection context, not an error.
- No alerts in the bounded window: count `0`, latest timestamp `null`.
- Alert exactly at `as_of_utc - 7 days`: included.
- Alert exactly at `as_of_utc`: included.
- Alert later than `as_of_utc`: excluded from count and `latest_alert_at`.
- Missing metric: return/render null.
- Stale/ineligible Product: return/render honest state; no synthetic eligibility/rank.
- All Product analytics use the same request `as_of_utc`; a per-Product clock sample is a contract violation.
- Compare backend failure: visible error with safe retry; tray selection remains available for retry.
- Rapidly changed compare selection: existing stale-response protection must prevent an older response from overwriting the latest selection.

### 15.4 Bootstrap / backup / restore

- Representative Phase 4 database with marker `"1"`: additive startup creates only the three Phase 5 tables, preserves existing portable state, and advances the existing compatibility owner to `"2"` before readiness.
- Repeated Phase 5 startup: idempotent.
- Schema/bootstrap/required-schema/marker-transition failure: block normal application readiness; never continue with Phase 5 schema plus marker `"1"`.
- Version-1 portable backup candidate: reject before destructive restore.
- Version-2 candidate missing a required Phase 5 table: reject as invalid schema.
- Failed restore: preserve existing Phase 4 rollback/recovery semantics.
- Session portability: remain excluded.
- All upgrade/restore failure fixtures: isolated temporary/file-backed databases only; never real `backend/affiliate.db`.

---

## 16. Performance / query budgets

These are acceptance gates.

### 16.1 Collections

Collection member list:

- `<= 2 SQL queries` total.
- Zero per-member Product query.
- Zero N+1 behavior.
- Reverse Product-to-Collection lookup must use the `collection_items(product_id)` index.

Preferred shape:

1. Collection items + Product identity + Watch state in one joined/eager query.
2. Optional one bulk analytics/snapshot query only if the final Collection workspace actually displays analytics. Do not spend the second query when not needed.

### 16.2 Compare

For 2–5 Products:

- `<= 3 SQL queries total`.
- Zero N+1 behavior.
- Exactly one browser/API Compare request.
- No per-Product frontend fanout.

The query model in Section 8.4 is the default target.

### 16.3 Compare latency benchmark

Use the existing representative **200-Product / 5,000-snapshot** benchmark fixture/environment from prior phases.

Required measurement:

- Benchmark the 5-Product Compare service/API after warmup using the repository's existing benchmark methodology where available.
- Record environment, iteration count, median/p95 or the metrics already used by the existing benchmark harness.
- Hard regression ceiling: Compare must remain within the existing Phase 3 sub-200ms representative latency gate on the same fixture/harness.
- Research target: `<50ms` for a 5-Product Compare request.

This draft does **not** claim `<50ms` has already been measured. During implementation, validate whether `<50ms` is stable and has reasonable headroom. If it is, codify it as a stricter regression assertion. If it is not, do not weaken the query-count/no-N+1 gates; report the measured result and cause in the completion report for Project Control review.

### 16.4 Saved Views

Applying an already loaded Saved View must introduce:

- `0 additional SavedView DB queries`

beyond the normal underlying Trends/Watchlist data request.

Implementation consequence: scope-specific Saved View list responses include validated payloads, and frontend apply is local-state hydration followed by the existing data request.

---

## 17. Expected modules / files affected

Exact paths must follow the current repository; do not create parallel layers merely to match speculative names below.

Likely backend areas:

- SQLAlchemy model registration/model modules for Collection, CollectionItem, SavedView.
- Pydantic/request/response schemas for Collections, Saved Views, and Compare.
- Existing FastAPI router registration and new/extended routers for the three capabilities.
- Collection service/repository logic.
- Saved View validation/service logic.
- Compare bulk-query/service logic.
- Shared Phase 2 analytics helper only if extraction is necessary for reuse.
- Existing alert-event query/service for grouped summaries.
- Existing Phase 4 backup/restore compatibility constant/service.
- Application bootstrap/model import wiring.
- Backend tests for models/services/API/query counts/performance/backup restore.

Likely frontend areas:

- Existing API client/types.
- Existing dashboard/navigation shell.
- Trends surface.
- Watchlist surface.
- Product Detail surface.
- New compact Collections workspace components.
- Saved View selector/save/apply controls.
- Compare tray and comparison surface.
- Frontend Vitest tests for the above flows.

Documentation likely affected at implementation completion:

- `ARCHITECTURE.md`.
- `README.md` or the repository's equivalent operator-facing backup/restore documentation for the version-1 → version-2 compatibility consequence and post-upgrade backup instruction.
- `PLAN.md` / `PROJECT_STATUS.md` only through the normal Project Control reconciliation lifecycle after completion review; implementation should report recommended state changes rather than declaring the phase accepted itself.

---

## 18. Implementation sequencing / workstreams

Implementation is not authorized until Project Control approves this plan.

Once authorized, use the following sequence.

### Workstream 0 — Repository/source verification

- Verify repository ancestry contains or descends from Project Control selection commit `ded7221dc443485412ff0d1086eb618ce29116be`, or is an explicitly newer reconciled docs-only state approved by Project Control.
- Verify accepted product-code baseline remains `4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936` unless Project Control has explicitly reconciled a newer product-code baseline.
- Verify accepted Phase 4 implementation/state and Phase 5 selection/research artifacts are present in the actual checkout.
- Verify current model/router/service/frontend conventions.
- Verify the frozen Trends and Watchlist Saved View V1 fields in Sections 10.2/10.3 map to the selected source baseline and bind to existing validators/constants where practical; this workstream may **not** redefine either V1 field set.
- Verify current BackupService compatibility-owner/schema behavior and startup ordering needed for the Section 12.5 gate.
- Verify current alert-event index/query path supports one grouped bounded query.
- If ancestry, product-code baseline, Phase 4 state, frozen Saved View mapping, or another material assumption conflicts with the repository, stop before coding and return the discrepancy to `00 — Project Control & Roadmap`.

### Workstream 1 — Schema + compatibility atomic change

Implement together:

- Collection model.
- CollectionItem model + unique constraint + reverse index.
- SavedView model.
- model/bootstrap registration.
- existing backup compatibility owner transition to `"2"`.
- required-schema metadata coverage tests.
- startup readiness gate ensuring schema verification + marker `"2"` before normal application-ready continuation.
- isolated representative Phase-4/version-1 → Phase-5/version-2 in-place bootstrap test, including idempotent repeated startup and injected failure/readiness-block tests.

Reason: the app must never continue normally with Phase 5 schema while advertising compatibility version `"1"`. No Alembic and no cross-version restore migration are introduced.

### Workstream 2 — Collections backend

- Collection CRUD/delete service/API.
- Membership add/remove/list/update.
- Reverse lookup.
- fixed status validation.
- destructive-boundary tests.
- no scheduler/watch/alert side-effect tests.
- query-count tests.

### Workstream 3 — Saved Views backend

- Implement immutable-scope, `payload_version=1` typed validation.
- Implement the exact nine-key Trends schema from Section 10.2.
- Implement the exact seven-key Watchlist schema from Section 10.3.
- Require full-shape payloads and reject missing/unknown/scope-inappropriate keys.
- Reuse existing trend-state/confidence/evidence/sort/limit validation sources; do not invent a parallel permissive schema.
- CRUD API/service.
- Reject Trends pagination fields and Watchlist `skip`, `search`, `min_score`.
- Exact payload round-trip tests, scope-immutability tests, no-default-view tests, and SQL/DSL/transient-state rejection tests.

### Workstream 4 — Compare backend

- Capture one request-level `as_of_utc` exactly once at service entry and expose it explicitly in the response envelope.
- Reuse shared/batch-safe Phase 2 analytics without formula changes, passing the same `current_time=as_of_utc` for every Product.
- Bulk Product/snapshot/watch loading.
- Optional selected-Collection current context.
- One grouped alert summary query bounded by `as_of_utc - 7 days <= created_at <= as_of_utc`.
- Exclude future AlertEvents and derive `latest_alert_at` only from the bounded set.
- Cardinality/uniqueness/quarantine handling.
- Shared-`as_of_utc` analytics tests and 7-day boundary/future-event alert tests.
- `<=3`-query regression tests.
- Representative latency benchmark.

### Workstream 5 — Frontend API/types

- Add typed client contracts for Collections, Saved Views, Compare.
- Reuse existing error/loading/stale-response patterns.

### Workstream 6 — Collections frontend

- Collections workspace.
- member status/notes.
- add/remove flows.
- add-to-Collection actions from Trends, Watchlist, Product Detail.

### Workstream 7 — Saved Views frontend

- Trends selector/save/update/delete/apply using exactly the nine-key Section 10.2 payload, including current local `search` and `min_score`.
- Watchlist selector/save/update/delete/apply using exactly the seven-key Section 10.3 payload; no Watchlist `search`/`min_score` persistence.
- Reset Watchlist `skip` to zero on apply.
- Ensure apply causes only the normal data request and no URL/search-param synchronization.

### Workstream 8 — Compare frontend

- transient tray.
- 2–5 cap/dedupe.
- one-request compare open.
- comparison rendering.
- null/stale/evidence/alert display.
- error/retry/stale-response behavior.

### Workstream 9 — Backup/restore integration

- version-1 portable-backup rejection test under unchanged same-version policy.
- version-2 validation.
- isolated file-backed version-2 round-trip preserving all new state and representative existing portable state.
- Phase 4 → Phase 5 in-place bootstrap gate from Section 12.5, if not already housed with startup tests in Workstream 1.
- failure/recovery regression.
- session non-portability regression.
- operator-facing `README.md`/equivalent update stating that version-1 backups are not restorable by the version-2 app, that a fresh version-2 backup should be created after successful upgrade/bootstrap, that TikTok session state remains excluded, and that no cross-version migration is promised.

### Workstream 10 — Full validation + architecture documentation

- Run full backend/frontend/regression/build/health/integrity suites.
- Update `ARCHITECTURE.md` with Phase 5 invariants, including request-level Compare `as_of_utc` consistency and compatibility version `"2"`/same-version semantics where relevant.
- Verify operator backup/upgrade documentation from Workstream 9 is present and accurate.
- Do not modify ADR-003.
- Do not semantically change ADR-004.
- Produce completion report; do not self-approve Phase 5.

---

## 19. Validation plan

### 19.1 Collections backend

Validate:

- Collection create/list/get/update/delete.
- Empty-name validation.
- duplicate membership rejection including concurrent/race protection.
- same Product in multiple Collections.
- fixed review-status validation.
- per-Collection decision notes.
- Watchlist notes remain untouched.
- unwatch independence.
- remove-membership boundaries.
- delete-Collection boundaries.
- Product/Snapshot/Watchlist/AlertRule/AlertEvent preservation.
- no scheduler/crawler side effects.
- reverse membership lookup correctness/index use.
- member list query count `<=2` and zero N+1.

### 19.2 Saved Views backend

Validate:

- CRUD for both scopes.
- scope immutable after create.
- `payload_version = 1`; unknown versions rejected.
- Trends payload requires exactly: `category`, `trend_state`, `measured_only`, `confidence`, `sort_by`, `sort_direction`, `limit`, `search`, `min_score`.
- Watchlist payload requires exactly: `category`, `trend_state`, `measured_only`, `confidence`, `sort_by`, `sort_direction`, `limit`.
- missing required keys rejected.
- unknown keys rejected.
- Trends `skip`/offset/page keys rejected.
- Watchlist `skip`, `search`, `min_score`, and derived page keys rejected.
- exact no-filter representations round-trip: `category=null`, `confidence=null`, `measured_only=false`; Trends additionally `search=""`, `min_score=null`; `trend_state="all"` is the explicit no-restriction enum value.
- exact trend-state/confidence/sort-direction/sort-field enum rejection/acceptance.
- category and limit validation bind to the existing corresponding endpoint semantics/validator.
- Trends local `search`/`min_score` round-trip without introducing new backend filtering semantics.
- SQL/DSL/result IDs/transient/URL state rejected.
- no default-view behavior.

### 19.3 Compare backend

Validate:

- minimum 2 Products.
- maximum 5 Products.
- duplicate-ID rejection.
- response order preservation.
- missing Product handling.
- quarantine exclusion.
- exactly one `as_of_utc` captured per request and exposed explicitly in the top-level response/equivalent envelope.
- every Product's Phase 2 analytics invocation receives the identical `current_time=as_of_utc`.
- analytics parity with existing Product/Trends analytics when evaluated against the same snapshots and `as_of_utc`.
- null preservation.
- stale/ineligible behavior.
- no new score/rank field.
- current Watch state does not alter analytics semantics.
- optional selected-Collection current context does not alter analytics semantics.
- Product not in selected Collection returns null context.
- grouped 7-day alert count/latest timestamp uses exactly `as_of_utc - 7 days <= created_at <= as_of_utc`.
- event exactly at lower boundary included.
- event exactly at `as_of_utc` included.
- event before lower boundary excluded.
- future event after `as_of_utc` excluded and cannot become `latest_alert_at`.
- no-alert case.
- query count `<=3`.
- zero N+1.
- one API request from frontend.
- benchmark on 200-Product/5,000-snapshot fixture.

### 19.4 Bootstrap / backup / restore

Validate in isolated temporary/file-backed databases only:

**Phase-4 → Phase-5 in-place startup gate:**

- begin from representative Phase 4 schema/state and compatibility marker `"1"`;
- fixture contains representative Product, ProductSnapshot, Watchlist, AlertRule, AlertEvent, alert cursor/evaluation state, and unrelated SystemMetadata;
- pre/post user-table set difference is exactly `collections`, `collection_items`, `saved_views`;
- all representative Phase 1–4 portable state and unrelated SystemMetadata are preserved;
- required schema includes the three Phase 5 tables via `Base.metadata.tables`;
- existing compatibility owner becomes `"2"` only after required schema is correct;
- application readiness is withheld until schema + marker are correct;
- second startup is idempotent;
- injected schema/bootstrap/required-schema/marker-transition failure blocks readiness and never continues normally with Phase 5 schema + marker `"1"`.

**Portable backup/restore:**

- compatibility marker reports `"2"`.
- version-1 candidate rejected before destructive restore.
- version-2 candidate validates.
- version-2 backup/restore round-trip preserves Collection/CollectionItem/SavedView state.
- status/notes/payload/version preserved exactly.
- existing Product/ProductSnapshot/Watchlist/AlertRule/AlertEvent/cursor/SystemMetadata portable state preserved.
- TikTok session remains non-portable.
- recovery/rollback behavior remains intact.

Never point upgrade, destructive restore, or recovery tests at real `backend/affiliate.db`.

### 19.5 Frontend

Collections:

- create/update/delete Collection.
- add Product from Trends.
- add Product from Watchlist.
- add Product from Product Detail.
- duplicate-add feedback.
- remove member.
- status edit.
- notes edit/save.
- unwatch leaves Collection member visible/intact.

Saved Views:

- save/apply/update/rename/delete Trends view using exactly the nine persisted V1 keys; `search` and `min_score` round-trip through existing local Trends state.
- save/apply/update/rename/delete Watchlist view using exactly the seven persisted V1 keys; Watchlist never persists `search`, `min_score`, or `skip`.
- Watchlist apply resets to first page/`skip=0`.
- no URL/search-param synchronization introduced.
- applying a loaded view performs no additional SavedView DB fetch and follows the normal data request path.
- stale-response protection remains correct.

Compare:

- tray minimum/disabled state.
- 5-item maximum.
- dedupe.
- remove/clear.
- one backend request on open.
- Product ordering.
- null/stale/ineligible/evidence rendering.
- Collection context rendering.
- alert summary rendering.
- loading/error/retry.
- stale-response handling when selection changes rapidly.

Accessibility:

- controls usable by keyboard according to existing conventions.
- disabled states and errors are exposed visibly/accessibly.

### 19.6 Full regression / repository validation

Run the repository-standard equivalents of:

- full backend pytest suite;
- full frontend Vitest suite;
- TypeScript typecheck (`npx tsc --noEmit` or current equivalent);
- lint (`npm run lint` or current equivalent);
- Next.js production build (`npm run build` or current equivalent);
- standard project healthcheck;
- representative performance/query tests;
- SQLite `PRAGMA integrity_check`;
- SQLite `PRAGMA foreign_key_check`.

No accepted Phase 1–4 regression is permitted.

Any failing check must be reported with the exact command/error and classified; tests or acceptance criteria must not be weakened merely to obtain green status.

---

## 20. Authoritative acceptance criteria

The following **36** criteria are authoritative for Phase 5 completion review.

- [ ] **P5-AC-01 — Domain separation:** Watchlist remains the sole scheduled-refresh authority; Collection create/add/remove/update/delete causes no crawler/scheduler membership side effect.
- [ ] **P5-AC-02 — Collection persistence:** Collection create/list/get/update/delete persists correctly with name, optional description, and timestamps using the existing SQLite/SQLAlchemy architecture.
- [ ] **P5-AC-03 — Collection destructive boundary:** Deleting a Collection removes only that Collection and its CollectionItems; Product, ProductSnapshot, WatchlistItem, AlertRule, and AlertEvent records are preserved.
- [ ] **P5-AC-04 — Unique membership:** `(collection_id, product_id)` is unique; duplicate and concurrent duplicate adds cannot create two rows and surface a deterministic conflict/error.
- [ ] **P5-AC-05 — Multi-Collection membership:** One Product can belong to multiple Collections simultaneously without shared status/notes state.
- [ ] **P5-AC-06 — Review status:** CollectionItem status defaults to `new` and accepts only `new`, `reviewing`, `candidate`, `rejected`.
- [ ] **P5-AC-07 — Decision notes ownership:** User notes persist only on CollectionItem; `WatchlistItem.notes` is neither reused nor mutated by Collection flows.
- [ ] **P5-AC-08 — Unwatch independence:** Removing Watchlist membership leaves every CollectionItem, review status, and decision note for that Product unchanged.
- [ ] **P5-AC-09 — Reverse membership lookup:** Product-to-Collection lookup is correct and uses the required `collection_items(product_id)` index.
- [ ] **P5-AC-10 — Collection query budget:** Collection member list uses `<=2` SQL queries with zero per-member Product queries/N+1 behavior.
- [ ] **P5-AC-11 — Saved View persistence/version/scope:** SavedView CRUD works for scopes `trends` and `watchlist` with immutable scope, `payload_version=1`, strict full-shape typed JSON payload round-trip, and rejection of unsupported versions or scope changes.
- [ ] **P5-AC-12 — Trends Saved View V1 exact contract:** Trends payload contains exactly `category`, `trend_state`, `measured_only`, `confidence`, `sort_by`, `sort_direction`, `limit`, `search`, `min_score`; it uses the Section 10.2 null/no-filter semantics and authoritative enums/validators, and contains no offset/skip/page field.
- [ ] **P5-AC-13 — Watchlist Saved View V1 exact contract:** Watchlist payload contains exactly `category`, `trend_state`, `measured_only`, `confidence`, `sort_by`, `sort_direction`, `limit`; `search`, `min_score`, `skip`, and derived page state are rejected/not persisted, and applying the view explicitly starts with `skip=0`.
- [ ] **P5-AC-14 — Saved View safety/strictness boundary:** Missing required keys, unknown keys, scope-inappropriate keys, SQL, arbitrary filter DSL, result rows/Product-ID result sets, loading/error state, stale-response tokens, modal state, Compare selection, and URL/search-param state are rejected rather than persisted.
- [ ] **P5-AC-15 — Saved View apply behavior/query budget:** Applying an already loaded Saved View hydrates only the existing component-local state defined by its exact V1 schema, triggers the normal Trends/Watchlist data path, adds `0` SavedView DB queries, introduces no URL synchronization, and preserves stale-response/error/retry behavior.
- [ ] **P5-AC-16 — Compare cardinality:** Backend accepts exactly 2–5 unique Product IDs, rejects duplicates/out-of-range cardinality, preserves request order, and frontend independently enforces/dedupes tray selection.
- [ ] **P5-AC-17 — Compare bulk path:** Opening Compare makes exactly one frontend API request; no per-Product endpoint fanout is used.
- [ ] **P5-AC-18 — Compare analytics authority and single request time:** Each Compare request captures exactly one timezone-aware `as_of_utc`, exposes it explicitly in the response/equivalent envelope, and passes that identical value as `current_time` to authoritative Phase 2 analytics for every Product; no new comparison score, winner, recommendation, or ranking formula is added.
- [ ] **P5-AC-19 — Compare null/stale/eligibility:** Null remains null; stale/ineligible Products are labeled honestly using the shared `as_of_utc`; Compare never converts an ineligible Product into an eligible rank.
- [ ] **P5-AC-20 — Compare Product/current Watch context:** Compare returns Product identity/current fields and current Watch state for each requested Product; current Watch membership is display context only and does not alter analytics semantics.
- [ ] **P5-AC-21 — Compare Collection context:** When a valid `collection_id` is supplied, each Product returns only that Collection's current status/notes if membership exists; non-members return null context, Compare performs no mutation, and Collection context does not alter analytics semantics.
- [ ] **P5-AC-22 — Compare bounded alert summary:** One batched query returns `recent_alert_count_7d` and `latest_alert_at` from exactly `as_of_utc - 7 days <= created_at <= as_of_utc`; both boundaries are included, events before the lower bound and future events are excluded, and `latest_alert_at` can only come from that bounded set.
- [ ] **P5-AC-23 — Compare query budget:** A 2–5 Product compare uses `<=3` SQL queries total with zero N+1 behavior.
- [ ] **P5-AC-24 — Quarantine exclusion:** Quarantined Products cannot be added through normal Collection APIs and cannot be returned as Compare candidates; a compare request containing one fails explicitly rather than partially.
- [ ] **P5-AC-25 — Compare performance evidence:** The 5-Product compare benchmark is run on the existing 200-Product/5,000-snapshot fixture, remains below the existing sub-200ms regression ceiling on the same harness, and reports whether the research `<50ms` target is stable enough to codify.
- [ ] **P5-AC-26 — Phase-4 → Phase-5 additive in-place bootstrap:** Starting from an isolated representative Phase-4/version-1 database, Phase-5 startup through existing `Base.metadata.create_all()` adds exactly `collections`, `collection_items`, `saved_views`, preserves representative Product/ProductSnapshot/Watchlist/AlertRule/AlertEvent/cursor/SystemMetadata state, is idempotent on repeated startup, and introduces no Alembic.
- [ ] **P5-AC-27 — Compatibility owner/readiness gate:** `BackupService.get_required_schema()` includes all three Phase 5 tables through `Base.metadata.tables`; the existing compatibility owner advances from `"1"` to `"2"` only after required schema is correct, and any schema/bootstrap/required-schema/marker-transition failure blocks normal application readiness so the app never runs normally with Phase 5 schema while advertising `"1"`.
- [ ] **P5-AC-28 — Version-1 portable-backup rejection:** A valid Phase-4/version-1 portable backup candidate is rejected by Phase 5 under unchanged same-version policy before destructive restore actions; no cross-version restore migration is attempted.
- [ ] **P5-AC-29 — Version-2 round-trip:** A Phase-5/version-2 portable backup validates and round-trips Collections, CollectionItems, review status, notes, Saved Views, scope/version/payload, plus representative existing portable Product/ProductSnapshot/Watchlist/AlertRule/AlertEvent/cursor/SystemMetadata state.
- [ ] **P5-AC-30 — Upgrade/restore safety and isolation:** In-place upgrade, destructive restore, recovery, and failure-injection tests use only isolated temporary/file-backed databases, never real `backend/affiliate.db`; existing Phase 4 rollback/recovery behavior remains intact and TikTok local session state remains non-portable.
- [ ] **P5-AC-31 — Collections frontend:** The dashboard provides a compact Collection workspace plus Add-to-Collection actions from Trends, Watchlist, and Product Detail, with working add/remove/status/notes flows and visible errors.
- [ ] **P5-AC-32 — Saved Views frontend:** Trends and Watchlist provide save/select/apply/update/delete controls mapped exactly to their Section 10 V1 schemas; applying uses current local state/fetch paths, Watchlist resets `skip=0`, and no URL/search-param synchronization is introduced.
- [ ] **P5-AC-33 — Compare tray frontend:** Compare tray is transient, dedupes by Product ID, allows removal/clear, enforces maximum 5, and disables Compare until at least 2 Products are selected.
- [ ] **P5-AC-34 — Compare rendering quality:** Comparison UI renders authoritative data, shared `as_of_utc` context/equivalent timestamp, null/stale/ineligible/evidence states and bounded alert summary correctly, with loading/error/retry and stale-response protection.
- [ ] **P5-AC-35 — Architecture and operator documentation:** `ARCHITECTURE.md` records the required Phase 5 invariants while ADR-003 remains unchanged and ADR-004 same-version semantics remain unchanged; `README.md`/operator documentation states that Phase-4/version-1 backups are not restorable by the Phase-5/version-2 app, instructs creation of a new version-2 backup after successful upgrade/bootstrap, keeps TikTok session portability excluded, and does not promise cross-version migration.
- [ ] **P5-AC-36 — Full repository validation:** Full backend tests, full frontend Vitest, typecheck, lint, production build, standard healthcheck, performance/query tests, SQLite integrity check, and foreign-key check succeed with no accepted Phase 1–4 regression, or any failure is explicitly documented/classified and prevents completion as appropriate.

---

## 21. Documentation requirements

Phase 5 completion must update `ARCHITECTURE.md` with at least these durable statements:

1. Monitoring and decision organization are separate domains.
2. Watchlist remains scheduler authority.
3. Collections have no monitoring side effect.
4. Unwatch preserves Collection state.
5. Review status/decision notes are CollectionItem-scoped.
6. `WatchlistItem.notes` remains internal provenance.
7. Saved Views store strict typed/versioned definitions, not result sets, SQL, arbitrary DSL, or transient state.
8. Saved Views V1 use the exact scope-specific contracts in Section 10, apply to component-local state/fetch paths, and do not require URL synchronization.
9. Compare is read-only/transient and reuses authoritative analytics.
10. A Compare request uses one shared request-level `as_of_utc` for all time-dependent Phase 2 analytics and its bounded alert summary.
11. No new comparison score/ranking/recommendation formula exists.
12. Existing null/stale/eligibility/evidence/quarantine semantics remain authoritative.
13. Collections and Compare preserve bounded-query/no-N+1 behavior.
14. Portable backup compatibility version is now `"2"`; same-version restore policy remains unchanged.
15. Phase-4 → Phase-5 in-place schema bootstrap is additive/idempotent and application readiness requires both required Phase 5 schema and compatibility marker `"2"`.

Operator-facing `README.md` or the repository's equivalent backup/restore documentation must also state:

- Phase-4/version-1 portable backups are **not restorable** by the Phase-5/version-2 application under unchanged same-version policy.
- After successful Phase-5 in-place upgrade/bootstrap, operators should create a new portable backup with compatibility version `"2"`.
- TikTok local session state remains non-portable/excluded.
- Phase 5 provides no cross-version backup migration/conversion promise.

No new ADR is planned.

Do not modify ADR-003.  
Do not semantically change ADR-004.

If implementation discovers a genuinely new cross-cutting/costly-to-reverse architecture decision, the completion report must identify the proposed ADR and affected architecture sections; it must not silently encode the decision only in implementation.

After implementation, Codex may recommend `PLAN.md` / `PROJECT_STATUS.md` updates in its completion report, but Phase 5 acceptance and durable project-state reconciliation remain Project Control responsibilities.

---

## 22. Deferred / future work

Known deferred items outside Phase 5:

- Tags/labels.
- Collection archive behavior.
- Custom workflows/status builders.
- Tasks, due dates, assignees, kanban.
- Persisted comparison sessions/history.
- Compare charts.
- Comparison scoring/recommendations.
- AI summaries/recommendations.
- New trend formulas or category-relative scoring.
- New alert types.
- Automatic broad discovery / crawler expansion.
- CAPTCHA/anti-bot bypass.
- Affiliate profitability/commission modeling.
- Cloud/browser synchronization.
- Multi-user/cloud backend.
- Executable packaging.
- Arbitrary report builder.
- Cross-version backup migration.
- URL-deep-link/filter-state synchronization.
- Saved View default/favorite semantics.
- Saved View schema-version migration beyond V1.
- Optional richer latest-alert metadata if later justified within query budget.
- Any unrelated refactor or cleanup discovered during implementation.

Existing project deferred items and technical debt from earlier phases remain where Project Control has already recorded them unless explicitly re-scoped.

---

## 23. Completion-report requirements

Codex must use the project's completion-report discipline and provide evidence sufficient for independent ChatGPT/Project Control review.

The report must include:

1. Proposed phase status only; Codex must not self-accept Phase 5.
2. Scope completed, organized by Collections, Saved Views, Compare, portability, frontend, and documentation.
3. Key implementation details and any small shared-analytics refactor required for Compare.
4. Exact files/modules changed and reason.
5. A complete table for **P5-AC-01 through P5-AC-36** with `PASS / FAIL / PARTIAL` and concrete evidence.
6. Exact validation commands and results for:
   - backend tests;
   - frontend Vitest;
   - typecheck;
   - lint;
   - production build;
   - standard healthcheck;
   - SQLite integrity/FK checks;
   - query-count tests;
   - performance benchmark;
   - backup/restore tests.
7. Query-count evidence:
   - Collection member list `<=2`;
   - Compare `<=3`;
   - Saved View apply adds `0` SavedView DB queries;
   - no browser per-Product Compare fanout.
8. Saved View contract evidence showing the exact Trends nine-key and Watchlist seven-key payloads, scope immutability, strict unknown/missing-key rejection, Watchlist `skip=0` apply behavior, and `0` additional SavedView DB queries on apply.
9. Compare determinism/performance evidence:
   - one response-level `as_of_utc`;
   - proof every Product analytics call used that same `current_time`;
   - 7-day alert lower-bound/upper-bound/future-event tests;
   - fixture, environment/harness, iterations/metric, measured benchmark result, and `<50ms` target assessment. Do not invent results.
10. Bootstrap/backup/restore evidence:
   - representative Phase-4/version-1 file-backed starting database;
   - pre/post new-table set exactly `collections`, `collection_items`, `saved_views`;
   - representative Phase 1–4 portable state preserved;
   - marker transition `"1"` → `"2"` only after required schema is correct;
   - repeated-start idempotency;
   - injected bootstrap/marker-transition failure blocks readiness;
   - version-1 portable-backup rejection;
   - version-2 validation and round-trip;
   - session remains non-portable;
   - isolated database paths used for all upgrade/destructive tests;
   - operator documentation updated with version-1 rejection/post-upgrade version-2 backup guidance/no cross-version promise.
11. Deviations from this plan with reason.
12. Unresolved issues/blockers.
13. Deferred work and suggested destination.
14. Technical debt introduced/discovered.
15. Architecture implications, including confirmation that ADR-003 was not modified and ADR-004 semantics were not changed, or an explicit ADR requirement if a new durable decision emerged.
16. Recommended Project Control updates to `PLAN.md` / `PROJECT_STATUS.md` / roadmap state.
17. A final reminder that the next lifecycle step is **ChatGPT completion review → completion decision → project-state reconciliation**, not automatic progression to another phase.

---

## Plan gate

This document is a planning artifact only.

Status remains:

`APPROVED — IMPLEMENTATION PENDING PROJECT CONTROL AUTHORIZATION`

Implementation authorization remains:

`NOT AUTHORIZED`

No production implementation may be inferred from this plan, and Phase 5 must not be marked complete until the normal implementation, completion-report, review, decision, and project-state reconciliation lifecycle has occurred.
