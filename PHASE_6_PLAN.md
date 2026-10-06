# Phase 6 — Affiliate Economics & Profitability Intelligence

Status: `DRAFT / PROJECT CONTROL REVIEW REQUIRED`  
Roadmap reference: `PROJECT_CONTROL_PHASE6_SELECTION.md` / `PROJECT_CONTROL_PHASE6_RESEARCH_ACCEPTED.md` / `PROJECT_CONTROL_ADR005_ACCEPTED.md` / latest reconciled `PLAN.md` / `PROJECT_STATUS.md`  
Created: `2026-10-06`  
Implementation authorization: **NOT AUTHORIZED**  
Project Control approval: **PENDING**  

Authoritative actual selection baseline commit: `d97f00f7819e778954a76abe3605e1442ea4155d`  
Accepted research artifact: [`research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md`](research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md) (accepted under `8c3f8949b8c9e61691c2e2756557e9abadc035b5`)  
Authoritative architecture decision: [`docs/architecture/ADR-005.md`](docs/architecture/ADR-005.md) (accepted under `d5fc2519abc8c67cc3751d62939fd7213b9794a6`)  
Planning baseline commit: `d5fc2519abc8c67cc3751d62939fd7213b9794a6`  
Qualified repository release baseline: `6e218929e3ff3ae091da1582de48fa0582802d8a`  
Qualified product-code baseline: `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98`  

Current implemented portable backup compatibility: `"2"`  
Phase 6 target compatibility after schema implementation: `"3"`  

---

## 1. Objective

Phase 6 introduces transparent, manual-first affiliate economics modeling directly into the product decision workspace:

```
track → analyze → explain → monitor → alert → export → organize → review → compare → MODEL ECONOMICS → decide
```

The phase objective is defined strictly and narrowly:

> **Allow a user to model transparent affiliate economics for a Product using named, manual-first scenarios without conflating market demand with affiliate attribution.**

The workflow specifically answers:
> *“Under these explicit assumptions, what are the unit economics and break-even requirements for this affiliate opportunity?”*

### 1.1 What Phase 6 Does NOT Promise
- Phase 6 does **NOT** promise or attempt actual TikTok Shop payout prediction.
- Actual creator payouts depend on post-order buyer settlements, coupons/discounts, refunds, cancellations, creator tier agreements, and commission collaboration contexts.
- Phase 6 models user-defined business scenarios with deterministic math and clear provenance disclosures.

---

## 2. Context & Current State

### 2.1 Project Control State Supplied for this Plan
- **Phase 1–5 Status:** `COMPLETE / ACCEPTED`.
- **Phase 5 Source-Release Qualification:** `READY WITH DOCUMENTED NON-BLOCKING ISSUES` for the supported **Windows / local / source-based runtime** (qualified repository revision `6e218929e3ff3ae091da1582de48fa0582802d8a`, qualified product-code revision `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98`).
- **Phase 6 Status:** `SELECTED / RESEARCH COMPLETE / ARCHITECTURE ACCEPTED`.
- **Research Gate:** `CLOSED / ACCEPTED` ([`research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md`](research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md)).
- **Architecture Gate:** `CLOSED / ACCEPTED` ([`docs/architecture/ADR-005.md`](docs/architecture/ADR-005.md)).
- **ADR-005 Acceptance Record:** [`PROJECT_CONTROL_ADR005_ACCEPTED.md`](PROJECT_CONTROL_ADR005_ACCEPTED.md).
- **Implementation Authorization:** **NOT AUTHORIZED**.
- **Phase 6 Plan Approval:** **PENDING REVIEW BY 00 — PROJECT CONTROL & ROADMAP**.

### 2.2 Durable Repository Baseline Requirement
The planning and subsequent implementation checkouts must descend from or contain the accepted ADR-005 commit:

`d5fc2519abc8c67cc3751d62939fd7213b9794a6`

The authoritative actual Phase 6 selection HEAD commit is:

`d97f00f7819e778954a76abe3605e1442ea4155d`

(Previously reported identifier `d97f00f9a25b16f398f658be424b94f1e58286ad` has been superseded in durable Project Control state).

Workstream 0 must verify actual repository ancestry, clean working tree, and unchanged product code before any Phase 6 production coding is permitted to begin.

### 2.3 Existing Behavior that Remains Authoritative
Phase 6 builds strictly upon established system boundaries:
1. **Phase 2 Trend Analytics:** Preserves deterministic Trend Score, orthogonal evidence confidence, Why Trending explanations, null preservation, and quarantine exclusion.
2. **Phase 3 Watchlist & Alerts:** `WatchlistItem` remains the sole scheduled-refresh authority. Alert evaluation remains post-commit, product-scoped, and governed by ADR-003. No economics alerts are introduced.
3. **Phase 4 Disaster Recovery:** Same-version restore policy (ADR-004), offline launcher-owned restore (`RESTORE.bat`), candidate file pre-validation, pre-restore safety backups, and host-bound session isolation remain unchanged.
4. **Phase 5 Opportunity Workspace:** Collections remain purely for decision organization. `CollectionItem.notes` remains user review notes. Compare remains transient (2–5 products) and read-only. Saved Views V1 schemas remain frozen and unchanged.
5. **Runtime Boundary:** Supported runtime remains Windows / local / source-based runtime. Standalone executable packaging remains deferred.

---

## 3. Research Conclusions & Architecture Decisions

This plan is strictly constrained by the accepted conclusions of [`research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md`](research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md) and the binding invariants of [`docs/architecture/ADR-005.md`](docs/architecture/ADR-005.md):

1. **Domain Separation:** Market Evidence, User Economics Assumptions, and Derived Economics must remain strictly separated.
2. **Attribution Boundary:** Market demand is not creator attribution. `sales_velocity × commission_per_order` is prohibited.
3. **Manual-First Strategy:** Economics assumptions are user-defined. `ProductSnapshot.commission_rate` is not an automatic calculation authority.
4. **VND-Only & Whole Integers:** Currency is whole VND only; commission rates are whole basis points ($10,000\text{ bps} = 100\%$).
5. **Single New Model:** Exactly one new database table: `economics_scenarios`.
6. **Exactly-One-Default Invariant:** When $\ge 1$ scenarios exist for a Product, exactly one default scenario exists. First scenario auto-defaults; deleting the default deterministically promotes the oldest remaining scenario by `(created_at ASC, id ASC)`.
7. **Single Backend Calculation Authority:** All formulas and rounding (round-half-up whole VND) execute on read in backend authority. Derived results are never persisted.
8. **Frozen Observed-Price Proxy:** Current Product price may be copied as a labeled, timestamped frozen proxy. It does not auto-mutate on crawler runs.
9. **Dynamic Schema & Compatibility Advance `"2" → "3"`:** Adding `economics_scenarios` triggers an advance of `portable_backup_compatibility_version` from `"2"` to `"3"` under ADR-004 same-version restore rules.
10. **Query Budgets (Zero N+1):** Collection member list with economics $\le 3$ SQL queries; Compare with economics $\le 3$ queries (without Collection) / $\le 4$ queries (with Collection).

---

## 4. Hard Architecture Invariants

Coding agents must treat the following invariants as non-negotiable boundaries:

### 4.1 Market Evidence vs Economics Invariant
Economics assumptions and derived metrics **MUST NEVER** alter or influence:
- Phase 2 Trend Score or score weighting;
- Trend eligibility, trend state, or velocity classifications;
- Evidence confidence (low/medium/high) or Why Trending explanations;
- Watchlist membership or monitoring lifecycle;
- Scheduled refresh crawl selection;
- Alert rule evaluation or trigger thresholds (ADR-003);
- Crawler execution, rate limiting, or discovery prioritization.

**Prohibition:** There shall be NO blended "trend-profit score", composite ranking, or sorting algorithm that combines market velocity with hypothetical profitability.

### 4.2 Attribution Invariant
Product sold count and sales velocity represent overall market demand across all platform sellers and creators. They **MUST NOT** be used to infer user attributable orders, affiliate revenue, affiliate earnings, creator conversion rate, or investment payback period.

**Prohibition:** The system explicitly prohibits calculating or displaying:
- `sales_velocity × commission_per_order` as creator or affiliate earnings;
- `sold_count × commission_per_order` as historical affiliate revenue;
- `fixed_campaign_cost / sales_velocity` as break-even time or payback period;
- Fabricated creator conversion rates or click-through rates from market data.

All campaign-level earnings projections require explicit user-entered order assumptions (`expected_attributed_orders`).

### 4.3 Source Strategy Invariant
Phase 6 MVP is strictly manual-first:
- User enters commission rate and cost assumptions.
- Crawler-observed `ProductSnapshot.commission_rate` is market observation data only; it is **NOT** used as an automatic calculation authority.
- No scraping of private TikTok Creator Center dashboards.
- No CAPTCHA solving, anti-bot circumvention, or browser automation against authenticated creator surfaces.
- No official TikTok Shop Partner / Affiliate API or OAuth integration in MVP.
- No silent background refresh or modification of user scenario assumptions from crawler runs.
- Observed Product price may only be copied as an explicit user-initiated frozen proxy.

---

## 5. Scope Definition

### 5.1 In Scope

#### 1. Data Model & Persistence
- Single new database table: `economics_scenarios`.
- Full set of conceptual fields: `id`, `product_id`, `name`, `commission_rate_bps`, `commission_base_vnd`, `commission_base_source`, `commission_base_observed_at`, `sample_cost_vnd`, `content_cost_vnd`, `promotion_cost_vnd`, `variable_cost_per_attributed_order_vnd`, `expected_attributed_orders`, `is_default`, `created_at`, `updated_at`.
- SQLite composite unique constraint `UNIQUE(product_id, name)`.
- Foreign key index on `product_id` referencing `products.id` with `ON DELETE CASCADE`.
- SQLite partial unique index: `CREATE UNIQUE INDEX uq_economics_scenarios_product_default ON economics_scenarios(product_id) WHERE is_default = 1;`.
- Strict VND-only whole integer representation for money; integer basis points ($0 \dots 10,000\text{ bps}$) for commission rates.

#### 2. Default Scenario Invariants & Concurrency Orchestration
- Zero scenarios $\to$ zero defaults.
- $\ge 1$ scenario $\to$ exactly one committed default scenario.
- First scenario created for a Product is auto-committed as default.
- Subsequent scenarios default to `is_default = false` unless explicitly promoted.
- Atomic default toggling within a single database transaction.
- Deleting a non-default preserves the existing default.
- Deleting the current default when alternatives remain atomically promotes the oldest remaining scenario by `(created_at ASC, id ASC)`.
- Deleting the sole scenario leaves 0 scenarios and 0 defaults.
- Explicit concurrency handling and test matrix covering race conditions, simultaneous creates, and rollback guarantees.

#### 3. Pure Calculation Engine & Rounding Authority
- Single deterministic pure calculation module (`app.analytics.economics`).
- Exact rational arithmetic with `RATE_SCALE = 10_000`.
- Single backend rounding policy: round-half-up to nearest whole VND (`round_half_up_vnd`).
- Calculations:
  - Estimated commission per attributable order;
  - Total fixed campaign cost;
  - Unit contribution margin per attributable order;
  - Break-even attributable orders using exact rational contribution numerator;
  - Expected gross commission, expected variable cost, expected net contribution;
  - Scenario return on cost ratio.
- Strict null propagation (missing required inputs yield `null`; unknown $\ne 0$; explicit $0$ is valid).
- Zero persisted derived values in database.

#### 4. REST API Surface
- Product-scoped scenario endpoints:
  - `GET /api/products/{product_id}/economics` (list scenarios with derived metrics);
  - `POST /api/products/{product_id}/economics` (create scenario);
  - `GET /api/products/{product_id}/economics/{scenario_id}` (get single scenario with derived metrics);
  - `PATCH /api/products/{product_id}/economics/{scenario_id}` (update scenario assumptions);
  - `POST /api/products/{product_id}/economics/{scenario_id}/duplicate` (duplicate scenario);
  - `DELETE /api/products/{product_id}/economics/{scenario_id}` (delete scenario with deterministic promotion);
  - `POST /api/products/{product_id}/economics/{scenario_id}/set-default` (atomically set default scenario);
  - `POST /api/products/{product_id}/economics/{scenario_id}/rebase-price` (explicitly rebase/freeze latest observed Product price).
- Strict error mapping: HTTP 404 (missing product/scenario), HTTP 400 (quarantined product, price unavailable), HTTP 409 (duplicate scenario name, concurrency conflict), HTTP 422 (validation out-of-bounds).

#### 5. User Interface (Product Detail, Collections, Compare)
- **Product Detail Workspace:**
  - Dedicated compact Economics workspace section (`ProductEconomicsSection.tsx`);
  - Scenario selector tabs/dropdown;
  - Create, Edit, Duplicate, Delete scenario controls;
  - Set Default action and visual default badge;
  - Assumption inputs with whole-VND formatting and commission rate percentage input;
  - Action to capture/freeze latest observed Product price as proxy;
  - Clear provenance labels: `User assumption`, `Observed price proxy`, `Scenario estimate`, `Missing`;
  - Commercial disclosure: actual payouts differ due to buyer discounts, refunds, cancellations, and settlement context;
  - Derived unit economics cards, break-even order callout, and optional expected campaign metrics;
  - UI stale-response protection, loading states, visible error handling, retry buttons.
- **Collections Integration:**
  - Compact default-scenario summary in Collection member rows (estimated commission/order, contribution/order, break-even orders);
  - Honest empty/missing state when Product has no scenarios;
  - Batched backend retrieval ($\le 3$ SQL queries total; zero N+1).
- **Compare Integration:**
  - Extend existing transient Compare table with optional economics columns based on each Product's default scenario;
  - Displays scenario name, rate, base, provenance, commission/order, contribution/order, break-even orders, expected orders, expected contribution, return on cost;
  - Honest empty state for products without scenarios;
  - Single bulk request; query budget $\le 3$ SQL queries (without Collection) / $\le 4$ SQL queries (with Collection); zero N+1.

#### 6. Database Schema, Bootstrap & Disaster Recovery
- Additive schema creation via `Base.metadata.create_all()`.
- Dynamic schema verification derived from `Base.metadata`.
- Durable compatibility marker transition:
  $$\text{portable\_backup\_compatibility\_version: } \mathbf{"2" \longrightarrow "3"}$$
- Unchanged ADR-004 same-version restore enforcement:
  - Version `"2"` backups rejected with HTTP 400 before destructive restore;
  - Version `"3"` backups round-trip validated across scenarios, assumptions, nulls, defaults, and provenance;
  - Host-bound TikTok session strictly excluded.

### 5.2 Explicit Scope Exclusions (Out of Scope)
The following capabilities are strictly out of scope for Phase 6 MVP:
1. Automatic Creator Center or private TikTok dashboard scraping;
2. CAPTCHA solving, stealth browser automation, or anti-bot circumvention;
3. Official TikTok Shop Partner / Affiliate API integration or OAuth flows;
4. Actual payout ingestion, settlement report parsing, or bank integration;
5. Attributed-order ingestion or webhook handling;
6. Historical commission rate tracking or commission change logs;
7. Dedicated economics alerts (e.g., break-even crossing or commission alerts);
8. Foreign exchange (FX) conversion or multi-currency data structures;
9. Seller-side economics (platform commission tiers, merchant fulfillment fees, payment gateway cuts);
10. Tax calculation, VAT, withholding tax, or formal accounting/bookkeeping;
11. Payout reconciliation or dispute tracking;
12. Ad-platform integrations (TikTok Ads Manager API);
13. Campaign execution, affiliate link generation, or UTM tracking;
14. Traffic, impressions, or click-through-rate (CTR) ingestion;
15. Conversion-rate inference from external platforms;
16. Revenue attribution derived from market sales data;
17. AI-generated profit recommendations or budget optimization;
18. Arbitrary spreadsheet expression or formula builder;
19. Generic cost line-item accounting table;
20. Economics CSV export stream;
21. New Trend Score formula or blended trend-profit composite score;
22. Cloud database hosting, multi-tenant schemas, or multi-user permissions;
23. Cross-version backup migration tooling;
24. Standalone desktop executable packaging (`.exe` / installer);
25. Product deletion workflow (repository has no product deletion feature).

---

## 6. Existing-State Assumptions

This plan assumes and preserves the following verified facts:
1. **Product & Snapshot Pricing:** `Product` entity has no price or currency columns. `ProductSnapshot` stores `price: Float` and `commission_rate: Float`. Ingestion accepts only explicit VND prices; non-VND prices are parsed as `null`. Frontend formatting defaults to VND.
2. **Current Price Authority:** The authoritative current market price displayed in UI is derived at read time via `analysis.deltas.latest_price`.
3. **Quarantine Domain:** Quarantined products (`quarantined_products`) are unverified legacy artifacts excluded from trends, analytics, collections, and compare. Phase 6 enforces that quarantined products cannot have economics scenarios created or updated.
4. **Collections vs Watchlists:** `Watchlist = monitoring. Collections = decision organization.` `CollectionItem.notes` contains user decision notes; structured financial assumptions must never be placed into `CollectionItem.notes`.
5. **Saved View V1 Immutability:** Saved View V1 schemas (`market_trends`, `opportunity_workspace`) remain strictly frozen. No economics parameters are added to Saved View V1.
6. **Alert System Immutability:** ADR-003 and Phase 3 alert evaluation rules (`sales_velocity_above`, `trend_score_above`, `price_change_pct`) remain completely untouched.
7. **Local SQLite Engine:** SQLite runs locally with connection setting `PRAGMA foreign_keys = OFF` for cross-phase operational stability, verified via explicit `PRAGMA foreign_key_check` and application-level integrity guards.

---

## 7. Domain & Persistence Design

### 7.1 Entity Relationship & Cardinality
Phase 6 introduces exactly one new persistent entity:

```
┌──────────────┐         1 : 0..*         ┌────────────────────────┐
│   Product    │ ──────────────────────── │   EconomicsScenario    │
└──────────────┘                          └────────────────────────┘
```

- Each `EconomicsScenario` belongs directly to exactly one `Product`.
- One `Product` owns zero, one, or multiple named scenarios.
- No direct persistent foreign key between `CollectionItem` and `EconomicsScenario` in MVP.
- Collections and Compare reference the Product's default scenario.

### 7.2 Database Table Specification: `economics_scenarios`

```sql
CREATE TABLE economics_scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    commission_rate_bps INTEGER NULL,
    commission_base_vnd INTEGER NULL,
    commission_base_source VARCHAR(32) NOT NULL DEFAULT 'user_entered',
    commission_base_observed_at TIMESTAMP NULL,
    sample_cost_vnd INTEGER NULL,
    content_cost_vnd INTEGER NULL,
    promotion_cost_vnd INTEGER NULL,
    variable_cost_per_attributed_order_vnd INTEGER NULL,
    expected_attributed_orders INTEGER NULL,
    is_default BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT uq_economics_scenarios_product_name UNIQUE (product_id, name)
);

CREATE INDEX ix_economics_scenarios_product_id ON economics_scenarios(product_id);

CREATE UNIQUE INDEX uq_economics_scenarios_product_default 
ON economics_scenarios(product_id) 
WHERE is_default = 1;
```

### 7.3 Column Definitions & Constraints

| Column Name | Type | Nullable | Default | Description / Bounds |
| :--- | :--- | :---: | :---: | :--- |
| `id` | `INTEGER` | No | PK | Surrogate integer primary key |
| `product_id` | `INTEGER` | No | — | Foreign key to `products.id` (`ON DELETE CASCADE`) |
| `name` | `VARCHAR(255)` | No | — | Scenario label. Unique per product (`1..255` chars) |
| `commission_rate_bps` | `INTEGER` | Yes | `NULL` | Commission rate in basis points ($0 \dots 10,000$). $10,000\text{ bps} = 100\%$ |
| `commission_base_vnd` | `INTEGER` | Yes | `NULL` | Commission base per order in whole VND ($0 \le \text{base} \le 10^{12}$) |
| `commission_base_source` | `VARCHAR(32)` | No | `'user_entered'` | Provenance: `'user_entered'` or `'observed_price_proxy'` |
| `commission_base_observed_at`| `TIMESTAMP` | Yes | `NULL` | UTC snapshot timestamp if proxy; `NULL` if manual |
| `sample_cost_vnd` | `INTEGER` | Yes | `NULL` | Fixed sample/product acquisition cost ($0 \le \text{cost} \le 10^{12}$) |
| `content_cost_vnd` | `INTEGER` | Yes | `NULL` | Fixed content production cost ($0 \le \text{cost} \le 10^{12}$) |
| `promotion_cost_vnd` | `INTEGER` | Yes | `NULL` | Fixed campaign ad spend ($0 \le \text{cost} \le 10^{12}$) |
| `variable_cost_per_attributed_order_vnd` | `INTEGER` | Yes | `NULL` | Variable cost per order ($0 \le \text{cost} \le 10^{12}$) |
| `expected_attributed_orders`| `INTEGER` | Yes | `NULL` | User-assumed order count ($0 \le \text{orders} \le 10^7$) |
| `is_default` | `BOOLEAN` | No | `0` | Default scenario flag for Collection/Compare summary |
| `created_at` | `TIMESTAMP` | No | UTC now | Record creation timestamp (UTC) |
| `updated_at` | `TIMESTAMP` | No | UTC now | Record last updated timestamp (UTC) |

### 7.4 Field Validation & Semantics
1. **Unknown $\ne$ Zero:** Missing assumptions remain `NULL`. Explicit zero (`0`) represents a deliberate user assertion that the cost or rate is zero (e.g., free sample, organic promotion, zero handling fee). Input schemas must never coerce `NULL` to `0`.
2. **Numeric Bounds:**
   - Money values cannot be negative: $\text{val} \ge 0$.
   - Commission rate basis points: $0 \le \text{commission\_rate\_bps} \le 10,000$.
   - Upper application bound: Money fields capped at $1,000,000,000,000$ VND ($1$ trillion VND) to prevent payload abuse or 64-bit integer overflow.
   - Expected orders: $0 \le \text{expected\_attributed\_orders} \le 10,000,000$.
3. **No Persisted Derived Values:** No columns for calculated commission, contribution margin, break-even orders, net profit, or return on cost. All computed on read.
4. **No Extra Tables:** No expense line items table, no economics history log table, no crawler commission tracking table.

---

## 8. Default Scenario Invariants & Concurrency Orchestration

The default scenario invariant is a critical concurrency gate. The system guarantees that for every Product:
- If a Product has $0$ scenarios $\implies$ $0$ default scenarios.
- If a Product has $\ge 1$ scenarios $\implies$ **exactly one committed default scenario**.

### 8.1 Invariant Rules
1. **First Scenario Auto-Default:** Creating the first scenario for a Product automatically sets `is_default = true`.
2. **Subsequent Scenario Creation:** Additional scenarios default to `is_default = false` unless `is_default = true` is explicitly requested in the payload. If requested, the existing default is atomically cleared.
3. **Atomic Default Promotion:** Setting a scenario as default atomically clears `is_default = false` across all scenarios for that `product_id` and sets `is_default = true` on the target scenario in a single database transaction.
4. **Deleting Non-Default:** Deleting a non-default scenario leaves the existing default untouched.
5. **Deleting Current Default:**
   - If other scenarios remain for that Product, the service atomically deletes the default and promotes the **oldest remaining scenario** ordered by `(created_at ASC, id ASC)`.
   - If no other scenarios remain, the default is deleted and the Product returns to $0$ scenarios / $0$ defaults.

### 8.2 Database Partial Unique Index Enforcement
SQLite enforces at most one default per product at the database storage engine level:
```sql
CREATE UNIQUE INDEX uq_economics_scenarios_product_default 
ON economics_scenarios(product_id) 
WHERE is_default = 1;
```
If any concurrent transaction attempts to commit a second default scenario, SQLite raises an `IntegrityError`, preventing duplicate defaults.

### 8.3 Concurrency & Race Condition Handling Matrix

| Concurrency Scenario | Potential Hazard | Service & Transaction Orchestration | Outcome Guarantee |
| :--- | :--- | :--- | :--- |
| **1. Two simultaneous first-scenario creates** | Both threads detect 0 existing scenarios; both attempt to commit `is_default = 1`. | Both execute inside a transaction. First thread commits `is_default = 1`. Second thread hits `IntegrityError` on `uq_economics_scenarios_product_default`. | Second thread catches partial unique violation, rolls back, retries inside a clean transaction, observes 1 existing scenario, and inserts as `is_default = 0`. Exactly 1 default remains. |
| **2. Simultaneous create with explicit `is_default=true`** | Two threads try to create new scenarios and promote both to default. | Both execute default clearing and insertion. First commits. Second hits `IntegrityError` or re-clears and commits. | Serializable transaction or immediate retry. Exactly 1 default remains. |
| **3. Simultaneous `set-default` on different rows** | Thread A sets Scenario 1 as default; Thread B sets Scenario 2 as default. | Each executes `UPDATE economics_scenarios SET is_default = 0 WHERE product_id = :p` followed by `UPDATE economics_scenarios SET is_default = 1 WHERE id = :target`. | Last committed transaction wins cleanly. Partial unique index prevents interleaving. Exactly 1 default remains. |
| **4. `set-default` racing with `delete-default`** | Thread A deletes Scenario 1 (current default); Thread B sets Scenario 2 as default. | Thread A begins promotion of oldest remaining; Thread B explicitly promotes Scenario 2. | Transaction boundary serializes execution via SQLite table locking. Both result in valid target state. Exactly 1 default remains. |
| **5. `delete-default` racing with scenario creation** | Thread A deletes the sole scenario; Thread B creates Scenario 2. | Thread A leaves 0 scenarios; Thread B creates first scenario and auto-promotes to default. | If Thread B commits before Thread A, Thread A's deletion promotes Scenario 2. In all commit orderings: exactly 1 default. |
| **6. Transaction rollback mid-operation** | System crashes or error occurs after clearing defaults but before setting target default. | Default clearing and target setting are executed inside a single `with db.begin():` block. | Uncommitted changes roll back completely to the previous committed state. Product never remains with 0 defaults. |
| **7. Partial unique index violation** | Raw concurrent statement bypasses service checks. | SQLite raises `IntegrityError`. | Mapped to HTTP 409 Conflict with structured retry guidance. No corrupt state persisted. |

---

## 9. Numeric Representation & Calculation Engine

### 9.1 Numeric Domain
- **Money:** Stored as `INTEGER` whole VND. Eliminates binary floating-point representation errors (`0.1 + 0.2 != 0.3`).
- **Commission Rate:** Stored as `INTEGER` basis points (`bps`):
  $$100\text{ bps} = 1.00\%, \quad 1,250\text{ bps} = 12.50\%, \quad 10,000\text{ bps} = 100.00\%$$
- **Expected Orders:** Stored as `INTEGER` ($\ge 0$).

### 9.2 Authoritative Rounding Policy: Round-Half-Up to Whole VND
The project defines a single, deterministic backend rounding policy:
$$\operatorname{round\_half\_up\_vnd}(x) = \left\lfloor x + 0.5 \right\rfloor$$
Implemented using Python's `decimal.Decimal(str(x)).quantize(Decimal('1'), rounding=decimal.ROUND_HALF_UP)`. Python's native `round()` (bankers rounding / round-half-to-even) **MUST NOT** be used for monetary outputs.

#### Rounding Test Boundaries
- Exact $.5$ boundary: $10.5 \to 11$, $11.5 \to 12$, $12.5 \to 13$.
- Below $.5$ boundary: $10.4999 \to 10$.
- Above $.5$ boundary: $10.5001 \to 11$.
- Zero boundary: $0.0 \to 0$.
- Large values: $999,999,999,999.5 \to 1,000,000,000,000$.

### 9.3 Deterministic Formula Specifications

All economics calculations proceed through the pure backend module `app.analytics.economics`.

#### 1. Estimated Commission per Attributable Order
$$\text{commission\_per\_order\_vnd} = \operatorname{round\_half\_up\_vnd}\left( \frac{\text{commission\_base\_vnd} \times \text{commission\_rate\_bps}}{10,000} \right)$$
- *Prerequisites:* `commission_base_vnd` and `commission_rate_bps` must both be non-null. Otherwise `NULL`.

#### 2. Total Fixed Campaign Cost
$$\text{fixed\_campaign\_cost\_vnd} = \text{sample\_cost\_vnd} + \text{content\_cost\_vnd} + \text{promotion\_cost\_vnd}$$
- *Prerequisites:* Evaluated only when all three fixed-cost components are known (non-null or explicitly $0$). If any component is unknown (`NULL`), result is `NULL`.

#### 3. Contribution Margin per Attributable Order
$$\text{contribution\_per\_order\_vnd} = \text{commission\_per\_order\_vnd} - \text{variable\_cost\_per\_attributed\_order\_vnd}$$
- *Prerequisites:* Requires non-null calculated commission per order and non-null variable cost. Otherwise `NULL`.

#### 4. Break-Even Attributable Orders
To prevent off-by-one errors caused by premature presentation rounding, break-even uses the exact rational contribution margin numerator:
$$\text{contrib\_num} = (\text{commission\_base\_vnd} \times \text{commission\_rate\_bps}) - (\text{variable\_cost\_per\_attributed\_order\_vnd} \times 10,000)$$

If `fixed_campaign_cost_vnd` is known ($\ge 0$) and $\text{contrib\_num} > 0$:
$$\text{break\_even\_orders} = \left\lceil \frac{\text{fixed\_campaign\_cost\_vnd} \times 10,000}{\text{contrib\_num}} \right\rceil$$

- *Prerequisites:* If $\text{contrib\_num} \le 0$ (unit contribution is zero or negative), fixed costs are unknown, or inputs are incomplete, `break_even_orders` evaluates to `NULL`.

#### 5. Expected Campaign Economics (Evaluated only when `expected_attributed_orders` is non-null)
- **Expected Gross Commission:**
  $$\text{expected\_commission\_vnd} = \operatorname{round\_half\_up\_vnd}\left( \frac{\text{commission\_base\_vnd} \times \text{commission\_rate\_bps} \times \text{expected\_attributed\_orders}}{10,000} \right)$$
  *(Calculated using exact rational arithmetic and rounded once at final monetary output).*
- **Expected Variable Cost:**
  $$\text{expected\_variable\_cost\_vnd} = \text{variable\_cost\_per\_attributed\_order\_vnd} \times \text{expected\_attributed\_orders}$$
- **Expected Net Contribution:**
  $$\text{expected\_contribution\_vnd} = \text{expected\_commission\_vnd} - \text{fixed\_campaign\_cost\_vnd} - \text{expected\_variable\_cost\_vnd}$$
  *(Requires all inputs to be non-null).*
- **Scenario Return on Cost Ratio:**
  Let $\text{total\_campaign\_cost} = \text{fixed\_campaign\_cost\_vnd} + \text{expected\_variable\_cost\_vnd}$.  
  If $\text{total\_campaign\_cost} > 0$ and `expected_contribution_vnd` is known:
  $$\text{return\_on\_cost\_ratio} = \frac{\text{expected\_contribution\_vnd}}{\text{total\_campaign\_cost}}$$
  Returned as a float ratio (e.g. $0.45 = +45\%$). Clearly labeled as a scenario estimate, never as guaranteed commercial ROI.

### 9.4 Null Propagation Dependency Map

```
commission_base_vnd (NULL) ───────┬─► commission_per_order_vnd = NULL
                                  ├─► contribution_per_order_vnd = NULL
                                  ├─► break_even_orders = NULL
                                  └─► expected_commission_vnd = NULL

sample_cost_vnd (NULL) ───────────┬─► fixed_campaign_cost_vnd = NULL
content_cost_vnd (NULL) ──────────┼─► break_even_orders = NULL
promotion_cost_vnd (NULL) ────────┴─► expected_contribution_vnd = NULL

expected_attributed_orders (NULL) ┬─► expected_commission_vnd = NULL
                                  ├─► expected_variable_cost_vnd = NULL
                                  ├─► expected_contribution_vnd = NULL
                                  └─► return_on_cost_ratio = NULL
```

*Note:* Missing `expected_attributed_orders` does NOT invalidate unit economics (`commission_per_order_vnd`, `contribution_per_order_vnd`) or `break_even_orders`.

---

## 10. Frozen Observed-Price Proxy Semantics

When a user initializes or rebases a scenario using the current observed Product price:
1. The backend inspects the latest available snapshot price: `analysis.deltas.latest_price`.
2. If `latest_price` is missing or $\le 0$, the request fails with HTTP 400 Bad Request (`"No valid observed price available for this product"`).
3. The float price is rounded to whole integer VND via `round_half_up_vnd(latest_price)` and stored in `commission_base_vnd`.
4. Provenance is set: `commission_base_source = 'observed_price_proxy'`.
5. The snapshot's capture timestamp is frozen into: `commission_base_observed_at = snapshot.captured_at`.
6. Subsequent crawler runs, price discounts, or flash sales **DO NOT MUTATE** the scenario record.
7. Re-synchronizing to newer market prices requires an explicit user action (`rebase-price`).
8. For manually entered base amounts: `commission_base_source = 'user_entered'` and `commission_base_observed_at = NULL`.
9. The backend validates that source/value/timestamp combinations cannot become contradictory.

---

## 11. Backend API & Service Surface

### 11.1 Route Definitions (`backend/app/api/economics.py`)

All economics endpoints are Product-scoped:

```python
router = APIRouter(prefix="/products/{product_id}/economics", tags=["Economics"])
```

1. `GET /api/products/{product_id}/economics`
   - Returns all scenarios for the product ordered by `created_at ASC`, including calculated derived metrics on each scenario.
   - Response: `List[EconomicsScenarioResponse]`
2. `POST /api/products/{product_id}/economics`
   - Creates a new scenario for the product.
   - If first scenario, auto-promotes to default.
   - Body: `EconomicsScenarioCreate`
   - Status: HTTP 201 Created
3. `GET /api/products/{product_id}/economics/{scenario_id}`
   - Returns a single scenario with calculated derived metrics.
   - Response: `EconomicsScenarioResponse`
4. `PATCH /api/products/{product_id}/economics/{scenario_id}`
   - Updates scenario assumptions.
   - Body: `EconomicsScenarioUpdate`
   - Response: `EconomicsScenarioResponse`
5. `POST /api/products/{product_id}/economics/{scenario_id}/duplicate`
   - Clones an existing scenario under a new unique name (e.g., `"{name} (Bản sao)"`).
   - Cloned scenario defaults to `is_default = false`.
   - Status: HTTP 201 Created
6. `DELETE /api/products/{product_id}/economics/{scenario_id}`
   - Deletes scenario. If deleted scenario was default and other scenarios remain, atomically promotes the oldest remaining scenario.
   - Status: HTTP 204 No Content
7. `POST /api/products/{product_id}/economics/{scenario_id}/set-default`
   - Atomically promotes target scenario to default.
   - Response: `EconomicsScenarioResponse`
8. `POST /api/products/{product_id}/economics/{scenario_id}/rebase-price`
   - Fetches latest snapshot price, updates `commission_base_vnd`, sets `commission_base_source = 'observed_price_proxy'`, and updates `commission_base_observed_at`.
   - Response: `EconomicsScenarioResponse`

### 11.2 Pydantic Schemas

```python
class EconomicsScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    commission_rate_bps: Optional[int] = Field(None, ge=0, le=10000)
    commission_base_vnd: Optional[int] = Field(None, ge=0, le=10**12)
    use_observed_price: bool = False
    sample_cost_vnd: Optional[int] = Field(None, ge=0, le=10**12)
    content_cost_vnd: Optional[int] = Field(None, ge=0, le=10**12)
    promotion_cost_vnd: Optional[int] = Field(None, ge=0, le=10**12)
    variable_cost_per_attributed_order_vnd: Optional[int] = Field(None, ge=0, le=10**12)
    expected_attributed_orders: Optional[int] = Field(None, ge=0, le=10**7)
    is_default: bool = False

class DerivedEconomics(BaseModel):
    commission_per_order_vnd: Optional[int] = None
    fixed_campaign_cost_vnd: Optional[int] = None
    contribution_per_order_vnd: Optional[int] = None
    break_even_orders: Optional[int] = None
    expected_commission_vnd: Optional[int] = None
    expected_variable_cost_vnd: Optional[int] = None
    expected_contribution_vnd: Optional[int] = None
    return_on_cost_ratio: Optional[float] = None

class EconomicsScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    name: str
    commission_rate_bps: Optional[int] = None
    commission_base_vnd: Optional[int] = None
    commission_base_source: str
    commission_base_observed_at: Optional[datetime] = None
    sample_cost_vnd: Optional[int] = None
    content_cost_vnd: Optional[int] = None
    promotion_cost_vnd: Optional[int] = None
    variable_cost_per_attributed_order_vnd: Optional[int] = None
    expected_attributed_orders: Optional[int] = None
    is_default: bool
    created_at: datetime
    updated_at: datetime
    
    # Read-time calculated metrics
    derived: DerivedEconomics
```

### 11.3 Error Handling & Status Codes
- **HTTP 404 Not Found:** Product does not exist; Scenario does not exist; Scenario does not belong to specified `product_id`.
- **HTTP 400 Bad Request:** Product is quarantined (`QuarantinedProduct`); No valid observed price available when `use_observed_price=True` or during `rebase-price`.
- **HTTP 409 Conflict:** Scenario with this name already exists for this product (`uq_economics_scenarios_product_name`); Concurrent transaction conflict during default switching.
- **HTTP 422 Unprocessable Entity:** Validation errors (e.g. `commission_rate_bps < 0` or `> 10000`, negative costs, empty name).

---

## 12. Frontend Workspace Design

### 12.1 Product Detail Economics Section (`ProductEconomicsSection.tsx`)
Rendered directly within `frontend/src/app/products/[id]/page.tsx`:
1. **Header & Scenario Switcher:**
   - Tabs or select dropdown displaying all scenarios for the product.
   - Visual star badge indicating the default scenario.
   - Quick action buttons: `+ Tạo kịch bản`, `Nhân bản`, `Sửa`, `Xóa`, `Đặt làm mặc định`.
2. **Assumption Editing Modal/Form:**
   - Input for scenario name.
   - Commission rate input in percentage (e.g. `12.5%`), converted to basis points on save.
   - Commission base VND input with a button: `Lấy giá hiển thị hiện tại` (triggers observed price proxy freeze).
   - Fixed cost inputs: Chi phí mẫu, Chi phí sản xuất nội dung, Chi phí quảng cáo/quảng bá.
   - Variable cost input: Chi phí biến đổi trên mỗi đơn hàng affiliate.
   - Optional expected order volume input.
3. **Provenance Badges & Disclosure:**
   - Badges: `Giả định người dùng` (User assumption) vs `Giá quan sát đóng băng` (Observed price proxy with timestamp).
   - Missing indicator: `Chưa thiết lập` (Missing).
   - Commercial payout disclosure banner:
     > *"Lưu ý: Các chỉ số kinh tế là ước tính theo kịch bản giả định. Hoa hồng thực tế từ TikTok Shop có thể thay đổi phụ thuộc vào giá người mua thực trả, mã giảm giá, hoàn hàng, hủy đơn và điều kiện hợp tác cụ thể."*
4. **Calculated Metrics Display:**
   - Unit Economics: Hoa hồng ước tính/đơn, Lợi nhuận đóng góp/đơn.
   - Break-Even Card: Số đơn hàng cần đạt để hòa vốn chiến dịch (Điểm hòa vốn).
   - Campaign Projections (if expected orders provided): Tổng hoa hồng dự kiến, Tổng chi phí chiến dịch, Lợi nhuận ròng dự kiến, Tỷ suất lợi nhuận trên chi phí (Return on Cost).
5. **Robust Component State:**
   - Stale-response protection using active lifecycle guards.
   - Error banner with retry button.
   - Optimistic state updates reconciled against backend responses.

### 12.2 Collections Integration
In `CollectionsWorkspace.tsx` and collection member table:
- Display compact default scenario metrics in table columns:
  - `Hoa hồng/đơn (Mặc định)`
  - `Đóng góp/đơn`
  - `Đơn hòa vốn`
- If product has no scenarios: displays `—` (honestly uncalculated).
- Clicking opens scenario preview or navigates to Product Detail.

### 12.3 Compare Workspace Integration
In `CompareModal.tsx` and `ComparedProductResponse`:
- Add optional economics row group comparing each product's default scenario:
  - Kịch bản mặc định (`name`)
  - Tỷ lệ hoa hồng (`commission_rate_bps`)
  - Cơ sở tính hoa hồng & Nguồn (`commission_base_vnd`, `commission_base_source`)
  - Hoa hồng/đơn
  - Lợi nhuận đóng góp/đơn
  - Đơn hàng hòa vốn
  - Đơn dự kiến & Lợi nhuận dự kiến
  - Tỷ suất sinh lời kịch bản
- Products without scenarios display clean empty indicators (`—`).
- No blended comparison score or ranking.

---

## 13. Query Budgets & Performance

### 13.1 Query Gate Boundaries (Zero N+1)
All Phase 6 data access must adhere to strict query budgets:
1. **Product Economics Scenarios:**
   - Single query: `SELECT * FROM economics_scenarios WHERE product_id = :p ORDER BY created_at ASC`.
   - Derived economics computed in Python in memory.
   - **Budget: $\le 1$ SQL query.**
2. **Collection Member List with Economics:**
   - Query 1: Collection exists check.
   - Query 2: Eager joinedload `CollectionItem -> Product -> WatchlistItem`.
   - Query 3: Batched default scenario lookup:
     `SELECT * FROM economics_scenarios WHERE product_id IN (:ids) AND is_default = 1`.
   - **Budget: $\le 3$ SQL queries total.** Zero N+1.
3. **Compare Products with Economics:**
   - Baseline without collection: 2 SQL queries (products + snapshots joined, alerts summary).
   - Baseline with collection: 3 SQL queries.
   - Phase 6 adds 1 batched default scenario lookup:
     `SELECT * FROM economics_scenarios WHERE product_id IN (:ids) AND is_default = 1`.
   - **Candidate Budgets:**
     - Without collection context: **$\le 3$ SQL queries total**.
     - With collection context: **$\le 4$ SQL queries total**.
     - Zero N+1. Zero per-product HTTP fanout.

### 13.2 Performance Benchmark Gates
- Benchmark Fixture Lineage:
  - 200 Products;
  - 5,000 Product Snapshots;
  - 100 Watchlist items;
  - Meaningful subset of products with Economics Scenarios (some with 1, some with 3+, some with 0);
  - Isolated file-backed database fixture.
- **Hard Regression Gate:**
  - Collection member list and 5-Product Compare with economics must execute strictly in **$< 200\text{ms}$** (median and best).
- **Optimization Target:**
  - Measure and honestly report against the $< 50\text{ms}$ research target across 10 iterations (warmup = 1, reporting best, median, p95, worst).

---

## 14. Database Schema Bootstrap & Backup Compatibility

### 14.1 Additive Bootstrap Pattern
Phase 6 preserves the established additive bootstrap pattern in `backend/app/db/init_db.py`:
1. Register `EconomicsScenario` model on `Base.metadata`.
2. Additive `Base.metadata.create_all(bind=engine)`.
3. Validate required schema dynamically derived via `BackupService.get_required_schema()`.
4. If `economics_scenarios` or any required column is missing, raise `RuntimeError` and halt startup before updating the compatibility marker.
5. Only upon successful schema validation, advance `portable_backup_compatibility_version`:
   $$\text{"2"} \longrightarrow \text{"3"}$$
6. Repeated startups remain strictly idempotent.

### 14.2 Isolated Upgrade Validation Test
A dedicated automated test (`backend/tests/test_phase6_backup_upgrade.py`) must prove:
- Starts from an isolated Phase 5 database with compatibility marker `"2"`.
- Runs `init_db()`.
- Verifies `economics_scenarios` table and indexes are created.
- All Phase 1–5 data (Products, Snapshots, Watchlist, Alert Rules, Alert Events, Collections, Collection Items, Saved Views, Quarantine) remains completely intact.
- Marker advances to `"3"`.
- Injecting a schema failure (e.g. failing table creation) leaves marker at `"2"` and aborts startup.

### 14.3 Backup & Restore Policy (ADR-004 Unchanged)
- **Same-Version Restore:** Version `"2"` backups are rejected with structured HTTP 400 when tested against a Phase 6 version `"3"` application before any destructive file operation.
- **Round-Trip Integrity:** Version `"3"` backups preserve all scenarios, assumptions, null values, explicit zeros, default flags, and frozen price proxy timestamps.
- **Exclusion Guarantees:** Local TikTok session (`backend/.local/tiktok-session.json`) remains host-bound and strictly excluded from backups.
- **Operator Documentation:** README/operator guides must state:
  - Version `"2"` backups cannot be restored into Phase 6 application.
  - Operators must run `BACKUP.bat` to create a fresh version `"3"` backup immediately following Phase 6 upgrade.
  - Destructive tests must run exclusively on isolated temporary databases; never touch live `backend/affiliate.db`.

---

## 15. Security, Privacy & Diagnostics

1. **Local-First Privacy:** All financial assumptions, costs, and profit calculations are stored exclusively in the local SQLite database. No financial data is ever transmitted to external servers, cloud analytics, or TikTok endpoints.
2. **Zero Credentials/Tokens:** Scenarios require no TikTok partner credentials, OAuth tokens, or payment details.
3. **Safe Diagnostics:** `/api/diagnostics` includes safe table row counts only (`table_counts["economics_scenarios"] = ...`). No scenario names, commission rates, or financial figures are exposed via diagnostics.
4. **Preserved Security Debt:**
   - 1 High `source-map-js` advisory (`GHSA-68fv-2mgg-jv7q`) in production dependency graph: remains classified as non-blocking build-time debt.
   - Development-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`) in devDependencies: remains classified as non-blocking development debt.
   - `StarletteDeprecationWarning`: remains non-blocking.
   - Runtime `PRAGMA foreign_keys = 0`: preserved for stability.

---

## 16. Authoritative Acceptance Criteria (P6-AC-01 to P6-AC-38)

The following 38 acceptance criteria are unambiguous and testable. Implementation cannot be accepted until all criteria pass.

### Domain Separation & Attribution Invariants
- **`P6-AC-01` — Strict Domain Separation:**  
  *Requirement:* Economics scenario creation, editing, or deletion must have zero effect on Phase 2 Trend Score, trend state, momentum signals, evidence confidence, Why Trending reasons, Watchlist membership, scheduled refresh, or alert rule evaluation.  
  *Evidence:* Automated test asserting identical trend scores and alert triggers before and after creating high-profit or zero-profit scenarios.  
  *Validation:* `backend/tests/test_phase6_economics.py`
- **`P6-AC-02` — Attribution Inference Prohibition:**  
  *Requirement:* No backend or frontend code shall infer creator attributable orders, affiliate revenue, or campaign payback from market sold count or sales velocity. Prohibit `sales_velocity * commission`.  
  *Evidence:* Codebase audit and test asserting that product sold count changes do not alter scenario calculations.  
  *Validation:* Grep assertion & pure calculation unit tests.
- **`P6-AC-03` — Manual-First Source Baseline:**  
  *Requirement:* `ProductSnapshot.commission_rate` is never automatically used as the calculation authority. Commission rate and base are user scenario inputs.  
  *Evidence:* Scenario created with null user commission rate evaluates to null commission per order even if product snapshots contain crawler-observed commission rates.  
  *Validation:* Unit tests in `backend/tests/test_phase6_economics.py`.

### Data Model & Persistence
- **`P6-AC-04` — Single Table Persistence:**  
  *Requirement:* Phase 6 introduces exactly one new table: `economics_scenarios`. No extra tables for line items, history, or calculation results.  
  *Evidence:* Database inspection verifying exactly `economics_scenarios` added to `Base.metadata.tables`.  
  *Validation:* `BackupService.get_required_schema()`.
- **`P6-AC-05` — Numeric Types & Bounds Validation:**  
  *Requirement:* Money fields persist as integer VND ($0 \le \text{cost} \le 10^{12}$). Commission rate persists as basis points ($0 \le \text{bps} \le 10,000$). Negative values or bps $>10,000$ are rejected with HTTP 422.  
  *Evidence:* API tests verifying boundary validation on create and update payloads.  
  *Validation:* API test suite.
- **`P6-AC-06` — Null Preservation (Unknown $\ne$ Zero):**  
  *Requirement:* Omitted or null input fields persist as `NULL` and are never silently coerced to `0`. Explicit `0` persists as `0`.  
  *Evidence:* Scenario created with `sample_cost_vnd = null` returns `null`; scenario created with `sample_cost_vnd = 0` returns `0`.  
  *Validation:* Service & database assertions.
- **`P6-AC-07` — Unique Scenario Name per Product:**  
  *Requirement:* A product cannot have two scenarios with the same name. Attempting to create or rename a scenario to an existing name on that product returns HTTP 409 Conflict.  
  *Evidence:* Duplicate name creation test asserting HTTP 409 and intact database.  
  *Validation:* API test suite.
- **`P6-AC-08` — Quarantined Product Exclusion:**  
  *Requirement:* Quarantined products cannot have economics scenarios created, updated, or retrieved. Requests return HTTP 400 Bad Request.  
  *Evidence:* Service test attempting scenario creation on a quarantined product.  
  *Validation:* `backend/tests/test_phase6_economics.py`.

### Default Scenario Invariants & Concurrency
- **`P6-AC-09` — Zero Scenarios Yields Zero Defaults:**  
  *Requirement:* A product with zero scenarios has zero default scenarios.  
  *Evidence:* Query asserting count of default scenarios for product with no scenarios is 0.  
  *Validation:* Unit test.
- **`P6-AC-10` — Exactly One Default Invariant:**  
  *Requirement:* Any product with $\ge 1$ scenarios must have exactly one committed default scenario at all times.  
  *Evidence:* Invariant check across all lifecycle states (create, update, delete).  
  *Validation:* Dedicated default invariant tests.
- **`P6-AC-11` — First Scenario Auto-Default:**  
  *Requirement:* The first scenario created for a product is automatically committed with `is_default = true`.  
  *Evidence:* Creating a scenario on a fresh product returns `is_default = true` without explicit flag.  
  *Validation:* API test.
- **`P6-AC-12` — Subsequent Scenario Non-Default:**  
  *Requirement:* Creating a second scenario defaults to `is_default = false` unless explicitly requested.  
  *Evidence:* Creating a second scenario without `is_default=true` results in `is_default = false` while first scenario remains default.  
  *Validation:* API test.
- **`P6-AC-13` — Atomic Default Toggling:**  
  *Requirement:* Setting a scenario as default atomically clears `is_default = false` on all siblings and sets `is_default = true` on the target scenario in a single transaction.  
  *Evidence:* Calling `set-default` flips default without intermediate state.  
  *Validation:* API test.
- **`P6-AC-14` — Deterministic Promotion on Default Deletion:**  
  *Requirement:* Deleting the current default when other scenarios remain atomically promotes the oldest remaining scenario ordered by `(created_at ASC, id ASC)`.  
  *Evidence:* Create scenarios A, B, C. A is default. Delete A. Assert B is promoted to default.  
  *Validation:* Service test.
- **`P6-AC-15` — Deleting Final Scenario:**  
  *Requirement:* Deleting the sole scenario leaves the product with 0 scenarios and 0 defaults.  
  *Evidence:* Delete sole scenario. Assert total scenarios = 0, default count = 0.  
  *Validation:* Service test.
- **`P6-AC-16` — Database Partial Unique Index Enforcement:**  
  *Requirement:* SQLite unique partial index `uq_economics_scenarios_product_default` prevents committing multiple defaults at SQL level.  
  *Evidence:* Direct raw SQL insert attempting two `is_default = 1` rows for same `product_id` raises `IntegrityError`.  
  *Validation:* Database test.
- **`P6-AC-17` — Concurrency: Simultaneous First Scenario Creates:**  
  *Requirement:* Two concurrent threads attempting first-scenario creation both succeed without leaving multiple defaults or deadlocks; exactly one becomes default.  
  *Evidence:* Multi-threaded test asserting 2 created scenarios, exactly 1 default.  
  *Validation:* Concurrency test suite.
- **`P6-AC-18` — Concurrency: Race on Set-Default and Delete:**  
  *Requirement:* Concurrent `set-default` and `delete` operations maintain the exactly-one-default invariant without database corruption or dangling states.  
  *Evidence:* Randomized multi-threaded stress test executing 20 concurrent operations on a product.  
  *Validation:* Concurrency test suite.

### Calculation Engine, Precision & Rounding
- **`P6-AC-19` — Authoritative Round-Half-Up whole VND:**  
  *Requirement:* Backend rounds derived monetary outputs to whole VND using round-half-up. bankers rounding is prohibited.  
  *Evidence:* Boundary tests verifying $10.5 \to 11$, $11.5 \to 12$, $10.49 \to 10$, $10.51 \to 11$.  
  *Validation:* `backend/tests/test_phase6_economics.py`.
- **`P6-AC-20` — Commission per Order Formula:**  
  *Requirement:* Evaluates $\operatorname{round\_half\_up\_vnd}(\text{base} \times \text{bps} / 10,000)$ when both inputs exist; otherwise `null`.  
  *Evidence:* Exact arithmetic assertions across multiple test vectors.  
  *Validation:* Unit tests.
- **`P6-AC-21` — Fixed Campaign Cost & Null Propagation:**  
  *Requirement:* Evaluates sum of sample, content, and promotion costs only when all three are non-null/zero. If any is missing, fixed cost is `null`.  
  *Evidence:* Assertions with missing components returning `null`.  
  *Validation:* Unit tests.
- **`P6-AC-22` — Contribution Margin per Order Formula:**  
  *Requirement:* Evaluates commission per order minus variable cost per order. If variable cost is unknown, evaluates to `null`.  
  *Evidence:* Unit test assertions.  
  *Validation:* Unit tests.
- **`P6-AC-23` — Break-Even Attributable Orders Exact Math:**  
  *Requirement:* Calculated using exact rational numerator $\operatorname{ceil}(\text{fixed\_cost} \times 10,000 / \text{contrib\_num})$. Returns `null` if $\text{contrib\_num} \le 0$ or fixed costs unknown.  
  *Evidence:* Boundary test asserting exact integer output without off-by-one errors from intermediate rounding.  
  *Validation:* Unit tests.
- **`P6-AC-24` — Expected Campaign Economics:**  
  *Requirement:* Expected gross commission, variable cost, net contribution, and return-on-cost evaluated only when `expected_attributed_orders` is non-null. Rounding applied once at final monetary output.  
  *Evidence:* Verification of expected metrics against exact reference vectors.  
  *Validation:* Unit tests.
- **`P6-AC-25` — Zero Persisted Calculations:**  
  *Requirement:* No calculated metrics are stored in database columns. Modifying assumptions instantly updates derived metrics on next read.  
  *Evidence:* DB inspection showing only raw input columns; updating rate immediately changes response.  
  *Validation:* Database test.

### Frozen Observed-Price Proxy
- **`P6-AC-26` — Observed-Price Proxy Freezing:**  
  *Requirement:* Choosing observed price proxy copies latest snapshot price into `commission_base_vnd`, sets `commission_base_source = 'observed_price_proxy'`, and records snapshot timestamp.  
  *Evidence:* API call with `use_observed_price=True` freezes current price and timestamp.  
  *Validation:* API test.
- **`P6-AC-27` — Proxy Immutability Against Crawlers:**  
  *Requirement:* New crawler snapshots with different prices do not alter existing frozen proxy scenarios.  
  *Evidence:* Ingesting a new snapshot with 2x price does not mutate scenario's `commission_base_vnd`.  
  *Validation:* Integration test.
- **`P6-AC-28` — Explicit Price Rebase:**  
  *Requirement:* `rebase-price` endpoint updates `commission_base_vnd` and `commission_base_observed_at` to latest snapshot price. Fails with HTTP 400 if product has no price.  
  *Evidence:* Rebase updates price to new snapshot timestamp.  
  *Validation:* API test.

### Workspace Integrations & Query Budgets
- **`P6-AC-29` — Product Detail Economics Section UX:**  
  *Requirement:* Product Detail renders scenario selector, create/edit modal, default marker, provenance labels (`User assumption`, `Observed price proxy`, `Missing`), commercial payout disclosure, and loading/retry states.  
  *Evidence:* Frontend Vitest component tests verifying rendered elements and user interactions.  
  *Validation:* `frontend/tests/phase6-economics.test.tsx`.
- **`P6-AC-30` — Collections Integration & $\le 3$ Query Budget:**  
  *Requirement:* Collection member list displays default scenario summary via batched query. Query count $\le 3$ SQL queries total; zero N+1.  
  *Evidence:* Query listener assertion on collection member retrieval with economics.  
  *Validation:* `backend/tests/test_performance_and_queries.py`.
- **`P6-AC-31` — Compare Integration & $\le 4$ Query Budget:**  
  *Requirement:* 5-Product compare renders default scenario economics columns. Query count $\le 3$ (without collection) / $\le 4$ (with collection). Zero N+1. Zero per-product HTTP fanout.  
  *Evidence:* Query listener assertion on CompareService call with economics.  
  *Validation:* `backend/tests/test_performance_and_queries.py`.
- **`P6-AC-32` — Performance Regression Gate (<200ms):**  
  *Requirement:* Collection member list and 5-Product compare on representative 200-product/5,000-snapshot fixture execute in $<200\text{ms}$.  
  *Evidence:* Benchmark test reporting best, median, p95 latencies.  
  *Validation:* Performance benchmark suite.

### Disaster Recovery, Bootstrap & Upgrades
- **`P6-AC-33` — Additive Bootstrap & Compatibility Advance `"2" \to "3"`:**  
  *Requirement:* Startup runs `create_all()`, verifies required schema dynamically, and advances compatibility marker from `"2"` to `"3"`. Injected failure leaves marker at `"2"` and aborts startup.  
  *Evidence:* Isolated bootstrap test verifying schema creation and marker transition.  
  *Validation:* `backend/tests/test_phase6_backup_upgrade.py`.
- **`P6-AC-34` — Rejection of Version `"2"` Backups:**  
  *Requirement:* Version `"2"` backups are rejected with HTTP 400 before stopping services or replacing database files.  
  *Evidence:* Restore candidate validation test rejecting v2 backup on v3 application.  
  *Validation:* Backup test suite.
- **`P6-AC-35` — Version `"3"` Backup Round-Trip Integrity:**  
  *Requirement:* Creating a v3 backup and restoring into an empty database fully restores all scenarios, nulls, defaults, and provenance.  
  *Evidence:* Full backup creation, inspection, and restore round-trip test.  
  *Validation:* Backup test suite.

### Non-Regression & Quality Verification
- **`P6-AC-36` — Saved Views V1 & Alerts Non-Regression:**  
  *Requirement:* Saved View V1 schemas remain unchanged. Phase 3 alert evaluation, triggers, and cursors remain completely unchanged.  
  *Evidence:* Full Phase 3 and Phase 5 test suites pass cleanly without modifications.  
  *Validation:* Existing test suites.
- **`P6-AC-37` — Full Automated Test Suite Clean:**  
  *Requirement:* All backend pytest (Phase 1–6) pass cleanly. All frontend Vitest pass cleanly. TypeScript typecheck clean (`tsc --noEmit`). ESLint clean (`npm run lint`). Production build clean (`npm run build`).  
  *Evidence:* CLI test and build outputs.  
  *Validation:* Validation test runner.
- **`P6-AC-38` — Live Database Integrity Clean:**  
  *Requirement:* `PRAGMA integrity_check` returns `ok`; `PRAGMA foreign_key_check` returns clean (`[]`).  
  *Evidence:* SQLite pragma outputs on application database.  
  *Validation:* Database integrity check.

---

## 17. Implementation Sequencing & Workstreams

Implementation must proceed in strict dependency order across 10 workstreams:

```
┌────────────────────────────────────────────────────────┐
│ Workstream 0: Baseline & Ancestry Verification         │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ Workstream 1: Pure Economics Calculation Engine        │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ Workstream 2: Data Model, Concurrency & Default Engine │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ Workstream 3: Bootstrap & Compatibility Version "3"    │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ Workstream 4: Backend REST APIs & Rebase Proxy         │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ Workstream 5: Product Detail Economics Workspace UI    │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ Workstream 6: Collections Default Economics Summary    │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ Workstream 7: Compare Workspace Economics Extension    │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ Workstream 8: Backup, Recovery & Upgrade Qualification │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ Workstream 9: Full Regression, Benchmark & Docs        │
└────────────────────────────────────────────────────────┘
```

### Workstream 0: Baseline & Ancestry Verification
- **Objectives:** Verify clean Git working tree, commit ancestry descending from ADR-005 (`d5fc2519abc8c67cc3751d62939fd7213b9794a6`), and ensure all pre-Phase-6 tests pass.
- **Deliverables:** Verified baseline confirmation.
- **Dependencies:** None.

### Workstream 1: Pure Economics Calculation Engine & Precision Tests
- **Objectives:** Create `backend/app/analytics/economics.py`. Implement `round_half_up_vnd`, exact rational math (`RATE_SCALE = 10_000`), unit commission, contribution margin, break-even orders, expected campaign economics, and strict null propagation.
- **Deliverables:** Pure calculation module, isolated unit test suite `backend/tests/test_phase6_economics.py` covering formulas, exact boundaries, and null trees.
- **Dependencies:** Workstream 0.

### Workstream 2: Data Model, Concurrency & Default Scenario Invariants
- **Objectives:** Create `backend/app/models/economics_scenario.py`. Register model on `Base.metadata`. Implement composite unique index on `(product_id, name)` and partial unique default index. Implement `EconomicsService` with atomic default management, deterministic promotion on delete, and transactional concurrency guards.
- **Deliverables:** SQLAlchemy model, service class, unit/concurrency tests verifying all 8 race condition scenarios.
- **Dependencies:** Workstream 1.

### Workstream 3: Bootstrap, Dynamic Schema Derivation & Compatibility Version `"3"`
- **Objectives:** Advance `BackupService.COMPATIBILITY_VERSION = "3"` in `backend/app/services/backup_service.py`. Update `BACKUP_FILENAME_PATTERN` and `SAFETY_BACKUP_PATTERN` regex. Update `backend/app/db/init_db.py` to register model and advance compatibility marker only after dynamic schema verification.
- **Deliverables:** Updated backup service and init_db, isolated upgrade test verifying v2 $\to$ v3 transition.
- **Dependencies:** Workstream 2.

### Workstream 4: Product Economics APIs & Rebase Proxy
- **Objectives:** Create `backend/app/api/economics.py`. Wire CRUD, set-default, duplicate, and rebase-price routes. Enforce quarantine exclusion, boundary validations, and conflict error codes. Update `main.py` router registration. Include safe table count in `/api/diagnostics`.
- **Deliverables:** FastAPI router, Pydantic schemas, comprehensive API test suite.
- **Dependencies:** Workstream 3.

### Workstream 5: Product Detail Economics Workspace UI
- **Objectives:** Create `frontend/src/components/ProductEconomicsSection.tsx`. Add scenario switcher, modal form for assumptions, observed-price freeze action, provenance badges, commercial payout disclosure banner, unit economics cards, break-even callouts, and expected metrics. Wire into `frontend/src/app/products/[id]/page.tsx`. Add API client methods in `frontend/src/lib/api.ts`.
- **Deliverables:** React components, TypeScript interfaces, Vitest test suite `frontend/tests/phase6-economics.test.tsx`.
- **Dependencies:** Workstream 4.

### Workstream 6: Collections Default Economics Summary & Query Budgets
- **Objectives:** Update `CollectionService.get_collection_members` to batch-load default scenarios for member products in a single query ($\le 3$ SQL queries total). Attach derived economics to member responses. Update `CollectionsWorkspace.tsx` to display compact summary columns.
- **Deliverables:** Backend batched loader, frontend collection columns, query count test.
- **Dependencies:** Workstream 5.

### Workstream 7: Compare Workspace Economics Extension & Query Budgets
- **Objectives:** Update `CompareService.compare_products` to batch-load default scenarios in a single query ($\le 3$ queries without collection / $\le 4$ with collection). Attach economics fields to `ComparedProductResponse`. Update `CompareModal.tsx` to render optional economics comparison rows.
- **Deliverables:** Compare service extension, frontend modal extension, query count tests.
- **Dependencies:** Workstream 6.

### Workstream 8: Backup, Recovery & Upgrade Qualification
- **Objectives:** Implement automated tests for rejection of v2 backups on v3 app, round-trip v3 backup creation and restore, safety backup creation, and crash recovery. Verify zero session leakage.
- **Deliverables:** Full disaster recovery test suite in `backend/tests/test_phase6_backup_upgrade.py`.
- **Dependencies:** Workstream 7.

### Workstream 9: Full Regression, Benchmark & Documentation
- **Objectives:** Execute representative 200-product/5,000-snapshot benchmarks (<200ms hard gate). Run full regression suites (pytest 178+, Vitest 46+, typecheck, lint, production build). Update `ARCHITECTURE.md` and `README.md`. Prepare completion report.
- **Deliverables:** Performance evidence, documentation updates, final completion report.
- **Dependencies:** Workstream 8.

---

## 18. Expected Modules & Files Affected

### New Files to Create During Implementation
1. `backend/app/models/economics_scenario.py` — SQLAlchemy model for `economics_scenarios`.
2. `backend/app/analytics/economics.py` — Pure calculation module and rounding policy.
3. `backend/app/services/economics_service.py` — Scenario CRUD, atomic defaults, concurrency, proxy logic.
4. `backend/app/api/economics.py` — FastAPI routes and Pydantic schemas.
5. `backend/tests/test_phase6_economics.py` — Pure math, rounding, CRUD, concurrency, and default invariant tests.
6. `backend/tests/test_phase6_backup_upgrade.py` — Isolated v2 $\to$ v3 bootstrap and backup round-trip tests.
7. `frontend/src/components/ProductEconomicsSection.tsx` — Product Detail economics workspace.
8. `frontend/tests/phase6-economics.test.tsx` — Frontend component tests.

### Existing Files to Modify During Implementation
1. `backend/app/models/__init__.py` — Register `EconomicsScenario`.
2. `backend/app/services/backup_service.py` — Advance compatibility version to `"3"`, update regex patterns.
3. `backend/app/db/init_db.py` — Import `EconomicsScenario`, schema validation, marker advance.
4. `backend/app/main.py` — Register economics API router.
5. `backend/app/api/diagnostics.py` — Add safe `economics_scenarios` count to diagnostics.
6. `backend/app/services/collection_service.py` — Add batched default scenario lookup ($\le 3$ queries).
7. `backend/app/api/collections.py` — Extend member response schema with default economics.
8. `backend/app/services/compare_service.py` — Add batched default scenario lookup ($\le 3$/$4$ queries).
9. `backend/app/types/...` / `frontend/src/types/index.ts` — TypeScript interfaces for economics.
10. `frontend/src/lib/api.ts` — API client functions for economics.
11. `frontend/src/app/products/[id]/page.tsx` — Embed `ProductEconomicsSection`.
12. `frontend/src/components/CollectionsWorkspace.tsx` — Render compact economics summary.
13. `frontend/src/components/CompareModal.tsx` — Render economics comparison rows.
14. `backend/tests/test_performance_and_queries.py` — Add Phase 6 query count and benchmark assertions.
15. `ARCHITECTURE.md` & `README.md` — Document Phase 6 architecture, formulas, and backup version `"3"`.

---

## 19. Phase 1–5 Regression Protection Matrix

| Subsystem | Existing Invariant Protected | Protection Mechanism in Phase 6 |
| :--- | :--- | :--- |
| **Phase 1 Crawling & Storage** | Cumulative sold count, price, snapshots, crawl runs remain objective market observations. | Economics models stored in separate table; crawlers do not read or write economics data. |
| **Phase 2 Trend Analytics** | Deterministic Trend Score, velocity, momentum, evidence confidence, Why Trending explanations. | Economics calculations strictly decoupled. No blended trend-profit scores. Prohibit `sales_velocity * commission`. |
| **Phase 3 Watchlist & Alerts** | `WatchlistItem` is sole monitoring authority. Alert rules (`sales_velocity_above`, `trend_score_above`, `price_change_pct`) and cooldowns. | No economics alert types. Alert engine remains untouched. |
| **Phase 4 Disaster Recovery** | Keyset streaming CSV, offline launcher-owned restore (`RESTORE.bat`), same-version restore enforcement. | Version `"2"` backups rejected before destructive replace; version `"3"` backups round-trip validated. TikTok session isolated. |
| **Phase 5 Collections** | Collections = decision organization. `CollectionItem.notes` contains user decision notes. | No financial parameters stored in `CollectionItem.notes`. Default scenario loaded in batched query ($\le 3$ queries). |
| **Phase 5 Saved Views** | Saved View V1 schemas (`market_trends`, `opportunity_workspace`) remain frozen and immutable. | Zero economics parameters added to Saved View V1 schemas. |
| **Phase 5 Compare** | Transient read-only 2–5 product comparison with shared `as_of_utc`. | Extended with optional default scenario columns in single bulk request ($\le 3$/$4$ queries). Zero N+1. |

---

## 20. Authoritative Validation Commands

The future implementation agent must execute and pass the following repository-standard commands before requesting qualification:

### 1. Backend Validation
```powershell
# Focused Phase 6 unit, concurrency, and API tests
pytest backend/tests/test_phase6_economics.py -v

# Isolated upgrade, bootstrap, and backup tests
pytest backend/tests/test_phase6_backup_upgrade.py -v

# Performance query count and benchmark tests
pytest backend/tests/test_performance_and_queries.py -v -k "economics"

# Full backend test suite (all phases)
pytest backend/tests/ -v
```

### 2. Frontend Validation
```powershell
# Focused Phase 6 Vitest tests
cd frontend; npx vitest run tests/phase6-economics.test.tsx

# Full frontend Vitest suite
npm test

# TypeScript typecheck
npx tsc --noEmit

# ESLint lint check
npm run lint

# Production build compilation
npm run build
```

### 3. Runtime Health & SQLite Integrity
```powershell
# Health check script
.\healthcheck.bat

# SQLite integrity and foreign-key check
python -c "import sqlite3; con = sqlite3.connect('backend/affiliate.db'); print('Integrity:', con.execute('PRAGMA integrity_check').fetchall()); print('FK Check:', con.execute('PRAGMA foreign_key_check').fetchall()); con.close()"
```

### 4. Disaster Recovery Qualification
```powershell
# Validate BACKUP.bat generates valid v3 backup
.\BACKUP.bat

# Validate RESTORE.bat pre-validation rejects legacy v2 backup on v3 application
# (Executed on isolated test instance)
```

---

## 21. Documentation Requirements

Following implementation, the following documentation deliverables are required:
1. **`ARCHITECTURE.md`:** Update implementation status of Phase 6 from architecture-accepted to implemented. Record authoritative formulas, rounding policy, and query budgets.
2. **`README.md`:** Update operator disaster recovery section detailing backup compatibility version `"3"`, rejection of version `"2"` backups, and requirement to generate fresh v3 backups.
3. **`PHASE_6_COMPLETION_REPORT.md`:** Produce the comprehensive completion report detailing all 38 acceptance criteria, benchmark latency results, query counts, and test passes.
4. **`PLAN.md` & `PROJECT_STATUS.md`:** Reconcile project status and acceptance gates upon Project Control review.

---

## 22. Preserved Deferred Work

The following non-blocking debt and deferred roadmap items remain active and preserved:
1. High `source-map-js` advisory (`GHSA-68fv-2mgg-jv7q`) in production dependency graph: non-blocking build-time debt.
2. Development-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`) in devDependencies: non-blocking development debt.
3. `StarletteDeprecationWarning` during test runs: non-blocking.
4. Runtime connection `PRAGMA foreign_keys = OFF`: maintained for cross-phase operational stability.
5. Automatic broad home/category discovery & CAPTCHA bypass: deferred external platform limitation.
6. Standalone executable packaging (`.exe` / installer): deferred; supported release boundary remains Windows / local / source-based runtime.
7. Cloud / multi-user deployment: deferred.

---

## 23. Plan Gate & Verification Metadata

```yaml
Plan Metadata:
  Phase: "Phase 6 — Affiliate Economics & Profitability Intelligence"
  Scope: "VND-only, manual-first Product Economics Scenarios"
  Plan Status: "DRAFT / PROJECT CONTROL REVIEW REQUIRED"
  Implementation Authorization: "NOT AUTHORIZED"
  Project Control Approval: "PENDING"
  Authoritative Research Artifact: "research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md" (commit 8c3f8949b8c9e61691c2e2756557e9abadc035b5)
  Accepted Architecture Decision: "docs/architecture/ADR-005.md" (commit d5fc2519abc8c67cc3751d62939fd7213b9794a6)
  ADR-005 Acceptance Record: "PROJECT_CONTROL_ADR005_ACCEPTED.md"
  Planning Baseline Commit: "d5fc2519abc8c67cc3751d62939fd7213b9794a6"
  Authoritative Actual Selection HEAD Commit: "d97f00f7819e778954a76abe3605e1442ea4155d"
  Current Implemented Compatibility Version: "2"
  Target Compatibility Version: "3"
  Acceptance Criteria Count: 38 (P6-AC-01 through P6-AC-38)
  Workstreams Count: 10 (WS-0 through WS-9)
```

**Implementation Warning:**  
No production code, test code, schema modification, or dependency installation may begin until `00 — Project Control & Roadmap` has formally reviewed and approved this plan.
