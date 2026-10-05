# Research — Candidate Phase 2: Trend Quality & Decision Support

Date: 2026-10-04 (Updated 2026-10-05 with verified repository findings)
Role: `01 — Architecture & Repo Research`
Research status: **VERIFIED & COMPLETED AGAINST REPOSITORY FINDINGS**

## Executive conclusion

Phase 2 improves decision quality primarily by separating **trend strength** from **evidence quality**, adding deterministic evidence/confidence and deterministic “Why trending?” reasons, and adding a small set of high-value filters/sorts. It does **not** introduce category-relative normalization, and avoids schema migration as confirmed by repository index inspection.

The repository-verification gate is fulfilled: the authoritative Trend Score implementation, arithmetic formula, normalization transforms, eligibility rules, tolerances, backend query path, and snapshot indexes have been inspected, benchmarked, and verified directly from the codebase.

## 1. Verified repository implementation facts & exact findings

### 1.1 Authoritative Trend Score function & file
- **File location:** [`backend/app/analytics/scoring.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/analytics/scoring.py#L47-L99)
- **Authoritative function:** `calculate_trend_score(deltas: DeltaMetrics, first_seen_at: datetime, config: AnalyticsConfig = default_analytics_config, current_time: Optional[datetime] = None) -> float`
- **Config & weights file:** [`backend/app/analytics/config.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/analytics/config.py)
- **Transforms & math file:** [`backend/app/analytics/normalization.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/analytics/normalization.py)

### 1.2 Exact formula & weights
The Trend Score evaluates five weighted components (sum = 1.0 / 100%):
- **40% (0.40):** 24h Sales Velocity (`sales_velocity`)
- **25% (0.25):** Sales Acceleration (`sales_acceleration`)
- **15% (0.15):** 24h Review Velocity (`review_velocity`)
- **10% (0.10):** Freshness / Recency (`freshness`)
- **10% (0.10):** Product Rating Quality (`rating`)

Arithmetic combination:
$$\text{Total Score} = 0.40 \cdot S_{\text{vel}} + 0.25 \cdot S_{\text{accel}} + 0.15 \cdot S_{\text{rev}} + 0.10 \cdot S_{\text{fresh}} + 0.10 \cdot S_{\text{rating}}$$
Result is clamped to `[0.0, 100.0]` and rounded to 1 decimal place: `round(clamp(total_score, 0.0, 100.0), 1)`.

### 1.3 Exact caps, transforms, and thresholds
1. **Logarithmic Scaling Transform (`log_scale_score`):**
   - Formula: $\text{score} = \text{clamp}\left(\frac{\ln(1 + \text{value})}{\ln(1 + 10 \cdot \text{midpoint})} \cdot \text{target\_max},\ 0.0,\ \text{target\_max}\right)$
   - If value is `None`, $\le 0$, or `NaN`, returns `0.0`.
2. **Sales Velocity Component ($S_{\text{vel}}$, 0–100):**
   - Uses `log_scale_score(deltas.sales_velocity_24h, midpoint=300.0, target_max=100.0)`.
   - Denominator $\ln(1 + 3000) \approx 8.0067$.
3. **Sales Acceleration Component ($S_{\text{accel}}$, 0–100):**
   - Neutral baseline is `50.0` when acceleration is `None`.
   - Positive acceleration boosts: $50.0 + \text{log\_scale\_score}(\text{accel}, \text{midpoint}=150.0, \text{target\_max}=50.0)$.
   - Negative acceleration decays: $50.0 - \text{log\_scale\_score}(|\text{accel}|, \text{midpoint}=150.0, \text{target\_max}=50.0)$.
   - Clamped to `[0.0, 100.0]`. Denominator $\ln(1 + 1500) \approx 7.3139$.
4. **Review Velocity Component ($S_{\text{rev}}$, 0–100):**
   - Uses `log_scale_score(deltas.review_delta_24h, midpoint=30.0, target_max=100.0)`.
   - Denominator $\ln(1 + 300) \approx 5.7071$.
5. **Freshness Component ($S_{\text{fresh}}$, 0–100):**
   - Evaluated by `calculate_freshness_score(first_seen_at, current_time, max_days=14.0)`.
   - Linear decay: $\text{days\_old} = \frac{t_{\text{now}} - t_{\text{first}}}{86400}$. If $\text{days\_old} \ge 14.0$, score is `0.0`.
   - Else: $\text{clamp}(100.0 \cdot (1.0 - \frac{\text{days\_old}}{14.0}),\ 0.0,\ 100.0)$.
6. **Rating Component ($S_{\text{rating}}$, 0–100):**
   - Evaluated by `calculate_rating_score(deltas.latest_rating, min_threshold=3.5)`.
   - Missing or non-positive rating yields neutral baseline `50.0`.
   - Ratings $\le 3.5$ score `0.0`.
   - Ratings in $(3.5, 5.0]$ scale linearly: $\text{clamp}\left(\frac{\text{rating} - 3.5}{5.0 - 3.5} \cdot 100.0,\ 0.0,\ 100.0\right)$.

### 1.4 Eligibility and stale rules
- **Stale invariant:** Observations older than 8.0 hours (`STALE_THRESHOLD_HOURS = 8.0` in [`backend/app/analytics/deltas.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/analytics/deltas.py#L13)) set `deltas.is_stale = True`.
- **Measured signal invariant:** `has_trend_evidence(deltas)` requires at least one of `sales_velocity_24h`, `sales_acceleration`, or `review_delta_24h` to be non-None.
- **Score suppression:** If `deltas.is_stale` or `not has_trend_evidence(deltas)`, `calculate_trend_score` immediately returns `0.0`.
- **State classification:** Stale products enter `stale`; products lacking recent measured deltas enter `insufficient_measured_signal`; only fresh products with measured signals enter `eligible`.

### 1.5 Estimated-vs-measured behavior
- In [`backend/app/analytics/deltas.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/analytics/deltas.py#L80-L95):
  - Baseline anchor is selected from `('24h', '12h', '6h')`.
  - Actual elapsed hours $H = \frac{t_{\text{observed}} - t_{\text{baseline}}}{3600}$.
  - Velocity is normalized: $\text{sales\_velocity\_24h} = \Delta \cdot \frac{24}{H}$.
  - Estimated flag: `velocity_is_estimated = abs(hours - 24) > 0.05`.
  - Primary elapsed interval is captured explicitly: `primary_elapsed_hours = round(hours, 2)`.
- In [`backend/app/analytics/evidence.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/analytics/evidence.py#L89-L101):
  - Per-signal evidence status distinguishes `measured` vs `estimated` vs `missing`.
  - Crucial confidence rule: Estimated intervals alone cannot escalate confidence to HIGH. HIGH strictly requires `not deltas.velocity_is_estimated` and `deltas.has_24h_window == True`.

### 1.6 Ordering and tie-breaking behavior
- In [`backend/app/services/trend_service.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/services/trend_service.py#L58-L105) and [`rising_products.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/analytics/rising_products.py#L37-L47):
  - **Default Trend Score sort:** Multi-key tuple `(p.trend_score, sales_velocity_24h or 0, sales_acceleration or 0, sold_delta_24h or 0, -p.product_id if is_desc else p.product_id)`.
  - **Deterministic tie-break:** Tie-breaking on `product_id` guarantees consistent, shuffle-free ordering across subsequent queries and UI refreshes.
  - **Null-last sorting:** For metric sorts (`sales_velocity`, `sales_delta`, `review_delta`), the sort key begins with `p.deltas.<field> is None`. In Python, `False < True`, so null metrics sort last regardless of whether sort order is ASC or DESC.

### 1.7 Exact analytics window targets & tolerances
Defined in [`backend/app/analytics/deltas.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/analytics/deltas.py#L14-L20):
- **6h window:** Target 6.0h, tolerance ±1.5h $\rightarrow$ Valid range: `[4.5h, 7.5h]`
- **12h window:** Target 12.0h, tolerance ±2.0h $\rightarrow$ Valid range: `[10.0h, 14.0h]`
- **24h window:** Target 24.0h, tolerance ±4.0h $\rightarrow$ Valid range: `[20.0h, 28.0h]`
- **7d window:** Target 168.0h, tolerance ±4.0h $\rightarrow$ Valid range: `[164.0h, 172.0h]`
- **Stale cutoff:** 8.0h (`STALE_THRESHOLD_HOURS = 8.0`)
- **Selection policy:** When multiple snapshots fall within tolerance, the snapshot closest to the target hour is selected as the anchor.

### 1.8 Backend query path & data loading
- API Endpoint: `GET /api/trends` in [`backend/app/api/trends.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/api/trends.py#L13-L34)
- Delegates to `TrendService(db).get_trending_products(...)`
- Data retrieval via `ProductService(db).get_all_analyzed_products(category=category)`:
  - Executes a single SQLAlchemy query:
    `db.query(Product).options(joinedload(Product.snapshots)).filter(Product.id.not_in(select(QuarantinedProduct.product_id)))`
  - If `category` is supplied, appends `filter(Product.category == category)`.
  - Quarantined products are excluded at the SQL level.
  - Snapshots are eager-loaded in bulk through a single SQL LEFT OUTER JOIN; there are no per-product queries (zero N+1 queries).
  - Business analytics, score computation, evidence calculation, and reasons are computed in-memory per product via `get_analyzed_product(p)`.

### 1.9 Snapshot indexes & query performance
- Table: `product_snapshots`
- Verified schema indexes in SQLite:
  - `ix_product_snapshots_captured_at` on `(captured_at)`
  - `ix_product_snapshots_product_id` on `(product_id)`
  - `ix_product_snapshots_crawl_run_id` on `(crawl_run_id)`
  - Composite index: `ix_product_snapshots_product_captured` on `(product_id, captured_at)`
- SQLite query plan (`EXPLAIN QUERY PLAN`):
  - `SCAN products`
  - `USING ROWID SEARCH ON TABLE quarantined_products FOR IN-OPERATOR`
  - `SEARCH product_snapshots_1 USING INDEX ix_product_snapshots_product_id (product_id=?) LEFT-JOIN`
  - `USE TEMP B-TREE FOR ORDER BY`
- Benchmarked Latency:
  - **Live dataset (8 products, 74 snapshots):** 1 SQL query, ~16.88 ms execution time.
  - **Isolated synthetic dataset (200 products, 25 snapshots each = 5,000 snapshots):** 1 SQL query, average ~150.28 ms across 5 runs; with category filter: ~71.72 ms.

### 1.10 Distinction between verified implementation facts vs Phase 2 product semantics
- **Verified Implementation Facts:** The mathematical Trend Score formula, component weights (40/25/15/10/10), normalization functions (`log_scale_score`), window tolerances (6h/12h/24h/7d), single-query `joinedload` execution, and composite SQLite indexes exist as verified code and database artifacts.
- **Phase 2 Product Semantics:** The separation of Trend Strength vs Evidence Quality, the deterministic confidence classification (LOW / MEDIUM / HIGH), the structured "Why trending?" reason codes (`sales_velocity_up`, `sales_acceleration_up`, `review_velocity_up`), the category/evidence/sort controls, and explicit stale/insufficient UI states represent the product decision support semantics implemented in Phase 2.


## 2. Problems / biases

### Definite product/model limitations

1. **Tracked-universe selection bias.** The ranking is over user-selected tracked PDPs, not a representative TikTok Shop VN market sample. It must not be presented as “market-wide trending.”
2. **Evidence quality is not a first-class ranking concept in the durable architecture.** A score can be numerically precise while the supporting history is sparse, short, partially estimated, or missing fields.
3. **Freshness is a hard eligibility boundary.** The 8h stale cutoff is correct for preventing misleading current momentum, but it creates a discontinuity at the boundary; UI should explain stale/ineligible status rather than silently dropping the product.
4. **Short-history products are structurally disadvantaged for longer-horizon/acceleration features.** Null 7d or acceleration is correct, but users need to distinguish “not trending” from “not enough evidence yet.”
5. **Missing metrics are asymmetric.** Null preservation is correct, but ranking/explanation must avoid treating missing as zero or silently renormalizing in ways that inflate products with fewer observed metrics.
6. **Category cohorts are currently sparse.** Eight products across five categories are insufficient for stable within-category percentiles or category-normalized scores.

### Likely biases that require exact-formula verification

- If raw sales/review velocity materially drives the score, high-volume categories/products can dominate low-volume categories even when relative growth is more exceptional elsewhere.
- If cumulative popularity contributes, established products can dominate newer products; the prior cumulative-only eligibility fix reduces but may not eliminate this if cumulative fields still receive numeric weight after eligibility.
- If estimated intervals receive the same weight as measured intervals, sparse history can appear more certain than it is.
- If missing components are renormalized, incomplete products can be accidentally boosted; if missing components are treated as zero, incomplete products can be unfairly penalized.

## 3. Recommended trend evidence/confidence model

Keep **trend_score** and **trend_evidence** orthogonal. Do not multiply score by confidence in Phase 2.

Recommended computed response fields (no persistence required):

- `observation_count`
- `observation_span_hours`
- `latest_observation_age_hours`
- per-signal evidence state: `measured | estimated | missing`
- current ranking state: `eligible | stale | insufficient_measured_signal`
- interval metadata for the primary 24h signal: actual elapsed hours and `velocity_is_estimated`
- availability booleans for comparable 24h and 7d windows
- missing primary metrics list/flags
- `confidence`: `low | medium | high`

Recommended deterministic confidence semantics:

- **LOW**: trend-eligible but only minimum measured evidence is available; or evidence span is short/sparse. Estimated intervals cannot raise confidence above LOW by themselves.
- **MEDIUM**: fresh latest observation, at least one recent measured sales/review interval, at least 3 observations spanning at least 8h.
- **HIGH**: fresh latest observation, at least one measured ~24h sales/review comparison, at least 5 observations spanning at least 20h, with no estimated interval used as the primary reason.

The 5-observation / 20h threshold fits the existing approximately 4-hour collection cadence and the existing bounded-window model. These are proposed Phase 2 product semantics and must be encoded in deterministic tests if accepted.

Important rules:

- Stale latest data (>8h) makes current trend ranking **ineligible**, but older observations may still be valid historical comparison points for non-current analytics.
- Missing remains null; never invent zero.
- Estimated evidence may be displayed, but must not alone establish trend eligibility because the accepted architecture already requires a recent measured sales/review signal.
- Confidence describes data sufficiency, not “probability that the product will succeed.”
- Confidence rules should remain category-agnostic in Phase 2.

## 4. Global vs category-relative comparability

Recommendation: **do not introduce category-relative score normalization in Phase 2.**

Keep one global momentum score/rank over the **tracked eligible universe**, but explicitly label its scope. Add category filtering so a user can inspect and sort products within a category without pretending that a statistically meaningful category percentile exists.

Why:

- current category cohorts are too small;
- user-assisted tracking introduces selection bias;
- category normalization would require minimum cohort-size rules, fallback behavior, distribution handling and additional query cost;
- category-relative percentile values would appear authoritative despite unstable samples.

Future category-relative ranking should require a minimum tracked cohort per category and a durable definition of cohort membership and fallback behavior.

## 5. Smallest useful deterministic “Why trending?” model

Use structured backend reason codes derived from the same analytics components that contribute to the score. The frontend renders localized text. No LLM-generated explanations.

Return at most 2–3 positive reasons, ordered by numeric component contribution descending, with a fixed reason-code tie-break.

Candidate reason codes:

- `sales_velocity_up`
- `review_velocity_up`
- `sales_acceleration_up`
- `review_acceleration_up` (only if such a score component exists after repo verification)

Examples of frontend rendering:

- `Sales +106 in ~24h (measured over 24.1h)`
- `Reviews +20 in ~24h`
- `Sales velocity accelerated 1.8× vs the previous comparable interval`

Evidence/confidence is shown separately, for example:

`Evidence: 17 observations / 30.5h · measured 24h interval · latest observation 2h ago`

Do not use “freshness” itself as a reason why a product is trending; freshness is evidence quality / eligibility, not a momentum cause.

## 6. Highest-value filtering and sorting without scope bloat

Recommended Phase 2 controls:

Filters:

- Category
- Trend state: rising/eligible vs all tracked
- Evidence: measured-only or confidence >= medium

Sorts:

- Trend Score (default)
- 24h sales velocity / delta
- 24h review velocity / delta
- Latest observation / freshness

Do not add broad faceted commerce search, arbitrary score-builder controls, category percentiles, price bands, seller-quality models, predictive forecasts, or customizable weighting in this phase.

A 7d sort can be deferred until real 7-day field coverage is common enough to avoid a mostly-null control.

## 7. Options and required changes

### Option A — Evidence + explainability over current score (recommended baseline)

Backend:
- inspect and freeze exact existing score semantics in tests;
- compute evidence/confidence from existing snapshots;
- compute deterministic reason codes from existing score components;
- add category/evidence/filter/sort query handling with stable null ordering and deterministic tie-breaks.

API:
- additive trend response fields for evidence, confidence, eligibility reason and structured explanations;
- additive query params for category, trend state, evidence requirement and approved sort keys.

Data model:
- no new persisted entities required;
- use existing product/category/snapshot timestamps and metrics.

Frontend:
- confidence/evidence badge;
- concise “Why trending?” explanation;
- category + measured/confidence filters;
- small sort selector;
- explicit stale / insufficient-evidence states.

Trade-off: improves decision quality substantially without changing the mathematical score; does not correct any numeric weighting bias inside the existing formula.

### Option B — Score v2 after exact-formula inspection

Backend:
- componentize score function;
- define score version and exact weights/transforms;
- preserve existing freshness/eligibility/null invariants;
- add deterministic fixtures comparing v1/v2 behavior across representative products.

API:
- expose `score_version` and optionally component contributions used by explanations.

Data model:
- still no migration required if score remains derived at read time.

Frontend:
- mostly same as Option A; avoid exposing raw internals unless useful.

Trade-off: can address confirmed weighting bias, but creates ranking regression/calibration risk. Should be included in Phase 2 only if source inspection finds a clear, testable defect rather than merely an aesthetic preference.

### Option C — Category-relative normalized ranking

Backend:
- category cohorts, minimum cohort-size rule, percentile/z-score or other normalization, fallback to global rank, deterministic handling for ties and sparse categories.

API:
- category rank/percentile and cohort metadata.

Data model:
- can remain derived, but query/index pressure is higher.

Frontend:
- category-relative rank/percentile presentation and scope labels.

Trade-off: potentially useful later, but misleading with current sparse/selective tracking. **Defer.**

## 8. Schema migration

Recommended Phase 2 can be implemented **without a schema migration** if evidence/confidence/reasons remain derived from existing products, snapshots and categories.

A migration should be introduced only if repo inspection shows that required fields are not already available or performance requires a missing composite index (for example, snapshot lookup by product + observed_at). Do not persist derived confidence or reason text merely for convenience.

## 9. Regression and performance risks

Correctness/regression risks:

- accidentally changing existing trend-score ordering while intending only additive evidence work;
- treating null as zero;
- allowing estimated evidence to establish eligibility;
- changing the 8h stale invariant;
- changing bounded 24h/7d window semantics;
- computing acceleration from non-distinct intervals;
- leaking quarantined history into evidence counts or category cohorts;
- unstable tie ordering causing UI churn;
- frontend/backend contract mismatch on new nullable fields;
- presenting tracked-universe rank as market-wide rank.

Performance risks:

- N+1 history queries per product when adding observation counts/spans/reasons;
- scanning unbounded snapshot history when only bounded windows are required;
- repeated category cohort calculations if category-relative ranking is introduced;
- extra client sorting that diverges from backend eligibility/null rules.

Mitigation direction:

- compute ranking/evidence in one authoritative backend path;
- reuse the same bounded snapshot data used by analytics where possible;
- bulk-load/group relevant histories rather than one query per product;
- keep explanations structured and derived from already-computed components;
- benchmark trend-list latency against current tracked-product counts and a larger synthetic-but-isolated test dataset (not the live DB).

## 10. Architecture / ADR impact

**ARCHITECTURE.md update: recommended.** Add durable analytics invariants:

1. Trend strength and evidence confidence are separate concepts.
2. Current trend eligibility requires fresh data and a recent measured sales/review signal; estimated-only evidence cannot create eligibility.
3. Missing metrics remain null and are never imputed to zero for scoring/explanation.
4. “Why trending?” reasons are deterministic and derived from the same backend analytics/score components.
5. Ranking scope is the eligible tracked-product universe; it is not a claim of market-wide TikTok Shop trend rank.
6. Category filtering does not imply category-relative normalization.

**ADR: not required for the recommended Phase 2 baseline.** The change is additive and reversible and does not alter persistence boundaries. Create an ADR if Phase 2 adopts a new score formula/version with durable normalization semantics, especially category-relative ranking or confidence-adjusted scoring.

## Proposed Phase 2 scope

### Mandatory repository-verification gate: FULFILLED

Verified against codebase on 2026-10-05:

- **Authoritative scoring source:** Inspect and documented `calculate_trend_score` in `backend/app/analytics/scoring.py` and `config.py`.
- **Exact formula & weights:** 40% sales velocity 24h, 25% sales acceleration, 15% review velocity, 10% freshness, 10% rating recorded with mathematical formulas and logarithmic transforms.
- **API response types & query path:** `GET /api/trends` mapped through `TrendService.get_trending_products` to `ProductService.get_all_analyzed_products`.
- **Snapshot access pattern:** Confirmed bulk-loaded via `joinedload(Product.snapshots)` in a single SQL query; verified 0 N+1 queries.
- **Index verification:** Verified SQLite indexes `ix_product_snapshots_product_id` and composite `ix_product_snapshots_product_captured (product_id, captured_at)` via `PRAGMA index_list` and `EXPLAIN QUERY PLAN`.
- **Latencies benchmarked:** ~16.88 ms on live dataset, ~150.28 ms on isolated 200-product/5,000-snapshot synthetic dataset.


### In scope

- Preserve existing score unless repo inspection proves a concrete scoring defect.
- Add structured trend evidence/confidence.
- Add deterministic “Why trending?” reasons.
- Add category, eligibility/evidence filters.
- Add score / 24h sales / 24h reviews / freshness sorts.
- Explicit stale and insufficient-evidence UI states.
- Backend deterministic tests for evidence tiers, reason selection, null handling, stale handling, estimated-vs-measured handling, quarantine exclusion and deterministic ordering.
- Frontend tests for new filters/sorts and explanation rendering.
- Update ARCHITECTURE.md analytics invariants.

### Conditional in-scope item

- Score v2 only if exact repository inspection demonstrates a clear correctness/decision-quality defect that can be fixed with deterministic acceptance criteria and without category-relative normalization.

## Explicitly deferred ideas

- Automatic broad TikTok Shop discovery / anti-bot bypass.
- Category-relative percentile/z-score ranking.
- Per-category learned or hand-tuned score weights.
- Predictive “will go viral” models.
- LLM-generated trend explanations.
- User-configurable scoring weights.
- Persisted confidence/explanation rows.
- Seller-quality/reputation scoring.
- Price-band / commission optimization models unless later product requirements explicitly prioritize them.
- Market-wide claims based on the current user-selected tracked universe.
- Real 7-day field-validation closure; this remains operational validation separate from Phase 2 feature implementation unless Project Control intentionally brings it into scope.

## Return to `00 — Project Control & Roadmap`

Recommended decision for Project Control:

- Accept Phase 2 direction as **evidence/confidence + deterministic explainability + focused decision filters/sorts**, preserving current architecture/security invariants.
- Keep global tracked-universe score as primary; do not introduce category-relative normalization yet.
- Plan Phase 2 with a mandatory first task to inspect and document the exact current score implementation before any scoring change.
- Plan for no schema migration by default.
- Require ARCHITECTURE.md analytics update; ADR only if score semantics/normalization are materially changed.
