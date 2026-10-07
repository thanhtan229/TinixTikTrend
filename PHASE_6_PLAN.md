# Phase 6 — Affiliate Economics & Profitability Intelligence

Status: `APPROVED`  
Roadmap reference: `PROJECT_CONTROL_PHASE6_SELECTION.md` / `PROJECT_CONTROL_PHASE6_RESEARCH_ACCEPTED.md` / `PROJECT_CONTROL_ADR005_ACCEPTED.md` / `PROJECT_CONTROL_PHASE6_PLAN_APPROVED.md` / latest reconciled `PLAN.md` / `PROJECT_STATUS.md`  
Created: `2026-10-06`  
Last revised: `2026-10-07` (Remediated against Project Control Findings A–N)  
Approved: `2026-10-07`  
Implementation authorization: **AUTHORIZED**  
Project Control approval: **APPROVED**  
Approved plan baseline commit: `4713fa422eb7f407b78995a9d453711910efc354`  

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
5. **Lossless Integer Arithmetic:** Backend calculations use pure integer ratio and ceiling arithmetic without passing through binary float.
6. **Lossless API & JS Safe-Integer Contract:** All persisted and derived monetary figures fit strictly within $[0, \text{Number.MAX_SAFE_INTEGER}]$ ($< 9 \times 10^{15}$).
7. **Single New Model:** Exactly one new database table: `economics_scenarios`.
8. **Deterministic Concurrency & Exactly-One-Default Invariant:** When $\ge 1$ scenarios exist for a Product, exactly one default scenario exists. First scenario auto-defaults; deleting the default deterministically promotes the oldest remaining scenario by `(created_at ASC, id ASC)`. Transactional retries and partial unique index enforce this at runtime and database levels.
9. **Strict Provenance & Mutation Contract:** Generic updates cannot forge proxy sources, timestamps, or toggle default status. Manual commission base edits reset provenance to `user_entered`.
10. **Single Backend Calculation Authority:** All formulas and rounding (round-half-up whole VND via integer ratios) execute on read in backend authority. Derived results are never persisted.
11. **Frozen Observed-Price Proxy:** Current Product price may be copied as a labeled, timestamped frozen proxy. It does not auto-mutate on crawler runs.
12. **Dynamic Schema & Compatibility Advance `"2" → "3"`:** Adding `economics_scenarios` triggers an advance of `portable_backup_compatibility_version` from `"2"` to `"3"` under ADR-004 same-version restore rules.
13. **Query Budgets (Zero N+1):** Collection member list with economics $\le 3$ SQL queries; Compare with economics $\le 3$ queries (without Collection) / $\le 4$ queries (with Collection). Zero HTTP fanout.

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
- Deterministic concurrency handling with bounded transaction retries (`BEGIN IMMEDIATE`) and structured HTTP 409 Conflict mapping.

#### 3. Pure Calculation Engine & Integer Arithmetic
- Single deterministic pure calculation module (`app.analytics.economics`).
- Pure integer ratio arithmetic with `RATE_SCALE = 10_000`; never passes intermediate calculations through binary `float`.
- Integer-based round-half-up to nearest whole VND: $(2N + D) // (2D)$ for numerator $N$ and denominator $D$.
- Calculations:
  - Estimated commission per attributable order;
  - Total fixed campaign cost;
  - Unit contribution margin per attributable order;
  - Break-even attributable orders using exact integer numerator and ceiling division $(A + B - 1) // B$;
  - Expected gross commission, expected variable cost, expected net contribution;
  - Scenario return on cost ratio.
- Strict null propagation (missing required inputs yield `null`; unknown $\ne 0$; explicit $0$ is valid).
- Zero persisted derived values in database.

#### 4. REST API Surface & Mutation Security
- Product-scoped scenario endpoints:
  - `GET /api/products/{product_id}/economics` (list scenarios with derived metrics);
  - `POST /api/products/{product_id}/economics` (create scenario);
  - `GET /api/products/{product_id}/economics/{scenario_id}` (get single scenario with derived metrics);
  - `PATCH /api/products/{product_id}/economics/{scenario_id}` (update scenario assumptions);
  - `POST /api/products/{product_id}/economics/{scenario_id}/duplicate` (duplicate scenario with validated new name);
  - `DELETE /api/products/{product_id}/economics/{scenario_id}` (delete scenario with deterministic promotion);
  - `POST /api/products/{product_id}/economics/{scenario_id}/set-default` (atomically set default scenario);
  - `POST /api/products/{product_id}/economics/{scenario_id}/rebase-price` (explicitly rebase/freeze latest observed Product price).
- Strict mutation contract: Client cannot forge proxy source or timestamp. Generic PATCH cannot write `is_default` or proxy metadata. Editing base amount resets source to `user_entered` and clears timestamp.
- Strict error mapping: HTTP 404 (missing product/scenario), HTTP 400 (quarantined product, price unavailable), HTTP 409 (duplicate scenario name, concurrency conflict), HTTP 422 (validation out-of-bounds, fractional bps).

#### 5. User Interface (Product Detail, Collections, Compare)
- **Product Detail Workspace:**
  - Dedicated compact Economics workspace section (`ProductEconomicsSection.tsx`);
  - Scenario selector tabs/dropdown;
  - Create, Edit, Duplicate, Delete scenario controls;
  - Set Default action and visual default badge;
  - Assumption inputs with whole-VND formatting and commission rate percentage input (max 2 decimal places);
  - Action to capture/freeze latest observed Product price as proxy;
  - Clear provenance labels: `User assumption`, `Observed price proxy`, `Scenario estimate`, `Missing`;
  - Commercial disclosure banner: actual payouts differ due to buyer discounts, refunds, cancellations, and settlement context;
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
  - Version `"2"` backups rejected with HTTP 400 (API preflight) and exit code 1 (launcher pre-validation) before destructive restore;
  - Version `"3"` backups round-trip validated across scenarios, assumptions, nulls, defaults, and provenance;
  - Pre-restore safety backup created with SQLite online backup engine before file replacement;
  - Atomic replacement with manifest tracking and rollback on post-replacement failure;
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

### 7.3 Column Definitions, Safe-Integer Bounds & Semantics

To guarantee that all inputs and calculated values remain strictly within JavaScript `Number.MAX_SAFE_INTEGER` ($9,007,199,254,740,991 \approx 9 \times 10^{15}$), the plan freezes bounded validation ranges:

| Column Name | Type | Nullable | Default | Bounds & Safe Limits |
| :--- | :--- | :---: | :---: | :--- |
| `id` | `INTEGER` | No | PK | Surrogate integer primary key |
| `product_id` | `INTEGER` | No | — | Foreign key to `products.id` (`ON DELETE CASCADE`) |
| `name` | `VARCHAR(255)` | No | — | Scenario label. Unique per product (`1..255` chars) |
| `commission_rate_bps` | `INTEGER` | Yes | `NULL` | Commission rate in basis points: $0 \le \text{bps} \le 10,000$ ($10,000\text{ bps} = 100\%$) |
| `commission_base_vnd` | `INTEGER` | Yes | `NULL` | Commission base per order in whole VND: $0 \le \text{base} \le 100,000,000,000$ ($100$ billion VND) |
| `commission_base_source` | `VARCHAR(32)` | No | `'user_entered'` | Provenance: strictly `'user_entered'` or `'observed_price_proxy'` |
| `commission_base_observed_at`| `TIMESTAMP` | Yes | `NULL` | UTC snapshot timestamp if proxy; `NULL` if manual |
| `sample_cost_vnd` | `INTEGER` | Yes | `NULL` | Fixed sample cost: $0 \le \text{cost} \le 100,000,000,000$ VND |
| `content_cost_vnd` | `INTEGER` | Yes | `NULL` | Fixed content production cost: $0 \le \text{cost} \le 100,000,000,000$ VND |
| `promotion_cost_vnd` | `INTEGER` | Yes | `NULL` | Fixed campaign ad spend: $0 \le \text{cost} \le 100,000,000,000$ VND |
| `variable_cost_per_attributed_order_vnd` | `INTEGER` | Yes | `NULL` | Variable cost per order: $0 \le \text{cost} \le 100,000,000,000$ VND |
| `expected_attributed_orders`| `INTEGER` | Yes | `NULL` | User-assumed order count: $0 \le \text{orders} \le 1,000,000$ ($1$ million orders) |
| `is_default` | `BOOLEAN` | No | `0` | Default scenario flag for Collection/Compare summary |
| `created_at` | `TIMESTAMP` | No | UTC now | Record creation timestamp (UTC) |
| `updated_at` | `TIMESTAMP` | No | UTC now | Record last updated timestamp (UTC) |

### 7.4 Lossless JavaScript / TypeScript Safe-Integer Guarantee
Under the maximum bounds:
- Max base: $10^{11}$ VND.
- Max rate: $10,000\text{ bps} = 1.0$.
- Max expected orders: $10^6$ orders.
- Maximum possible expected gross commission:
  $$\frac{10^{11} \times 10,000 \times 10^6}{10,000} = 10^{17} / 10^4 = 10^{13}\text{ VND} = 10,000,000,000,000\text{ VND}$$
Because $10^{13} \ll 9.007 \times 10^{15}$ (`Number.MAX_SAFE_INTEGER`), **every derived monetary value in whole VND is guaranteed to be lossless in JSON and TypeScript `number`**. No 64-bit integer truncation or BigInt string-marshalling is required.

### 7.5 Frontend Percentage to Basis Points Precision Contract
- User input represents commission as a percentage string or number (e.g., `"12.5%"` or `12.5`).
- Permitted precision: **At most 2 decimal places** in percentage representation (e.g., `12.34%` $\implies 1234\text{ bps}$, $0.01\% \implies 1\text{ bps}$).
- Exact conversion: $\text{bps} = \operatorname{round}(\text{percent} \times 100)$.
- Rejection policy: Fractional basis points are rejected with HTTP 422:
  `"Tỷ lệ hoa hồng tối đa 2 chữ số thập phân (bội số của 0.01% / 1 basis point)."`
- Float round-trip surprises are eliminated by parsing the percentage string directly or checking `abs(round(val * 100) - val * 100) < 1e-9`.

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

### 8.2 SQLite Concurrency Engine & Transaction Locking
To eliminate concurrency deadlocks and partial unique index violations on SQLite:
1. **Immediate Write Locking:** All scenario creation, default-switching, and deletion operations initiate transactions using `BEGIN IMMEDIATE` (via SQLAlchemy connection execution). This acquires a reserved SQLite lock immediately, preventing other connections from entering conflicting write states.
2. **Bounded Service Retries:** If SQLite reports `sqlite3.OperationalError: database is locked` or `busy`, the service executes bounded retries (up to 3 attempts with 50ms, 100ms exponential backoff).
3. **Partial Unique Index Violation Handling:** If a race condition triggers an `IntegrityError` on `uq_economics_scenarios_product_default`, the service rolls back cleanly. If retries are exhausted, it returns a structured HTTP 409 Conflict:
   `"Xung đột kịch bản mặc định do thao tác đồng thời. Vui lòng thử lại."`
4. **Atomicity Guarantee:** Deleting the default and promoting the oldest remaining scenario occurs inside a single transaction. If promotion fails, the entire deletion rolls back.

### 8.3 Deterministic Concurrency Test Matrix (8 Required Scenarios)

The test suite in `backend/tests/test_phase6_economics.py` must prove the following 8 cases using isolated file-backed SQLite databases, independent connections, and deterministic barriers (`threading.Barrier`):

| Test Case | Concurrent Operations | Synchronization Mechanism | Expected Outcome & Invariant Check |
| :--- | :--- | :--- | :--- |
| **Case 1: Concurrent First Scenario Create** | Thread 1 and Thread 2 simultaneously create Scenario A and Scenario B on a product with 0 scenarios. | Barrier before `db.commit()` | Both transactions succeed or one retries. Exactly 2 scenarios created; **exactly 1 default exists**. |
| **Case 2: Concurrent Create Requesting Default** | Thread 1 and Thread 2 simultaneously create Scenario A (`is_default=True`) and Scenario B (`is_default=True`). | Barrier before commit | Serialized via lock/retry. Both scenarios exist; **exactly 1 default exists** (last committed wins). |
| **Case 3: Simultaneous Set-Default Different Targets** | Thread 1 sets Scenario A as default; Thread 2 sets Scenario B as default. | Barrier after clearing default | Serialized via `BEGIN IMMEDIATE`. **Exactly 1 default exists**. No duplicate default violation. |
| **Case 4: Set-Default Racing with Delete-Current-Default** | Thread 1 sets Scenario B as default; Thread 2 deletes current default Scenario A. | Barrier mid-transaction | Serialized cleanly. Oldest remaining promoted or Scenario B committed as default. **Exactly 1 default exists**. |
| **Case 5: Delete-Default Racing with Scenario Create** | Thread 1 deletes sole Scenario A; Thread 2 creates Scenario B. | Barrier before commit | If Thread 1 commits first: product has Scenario B as default. If Thread 2 commits first: deletion of A promotes B. **Exactly 1 default exists**. |
| **Case 6: Injected Rollback on Promotion** | Delete Scenario A (default); inject exception before promoting Scenario B. | Mock/hook raising exception | Entire transaction rolls back. Scenario A remains in DB with `is_default = 1`. **Zero scenarios left without default**. |
| **Case 7: Direct Partial Unique Index Violation** | Raw SQL statement attempting to insert a second `is_default = 1` row for the same product. | Direct SQL execute | SQLite raises `sqlite3.IntegrityError` on `uq_economics_scenarios_product_default`. |
| **Case 8: Retry Exhaustion & Error Mapping** | Artificially exhaust retries under simulated permanent lock. | Mocked lock error | Service returns structured HTTP 409 Conflict. Database remains uncorrupted. |

---

## 9. Numeric Representation & Calculation Engine

### 9.1 Exact Integer Ratio Arithmetic (Finding A)
All economics calculations proceed through the pure module `app.analytics.economics`. To eliminate floating-point imprecision, calculations use **exact integer ratio arithmetic** without intermediate float conversions.

Let numerator $N$ and denominator $D$ be non-negative integers ($D > 0$).
The authoritative round-half-up whole-VND rounding helper is defined purely over integers:
$$\operatorname{round\_half\_up\_ratio}(N, D) = \left\lfloor \frac{2N + D}{2D} \right\rfloor = (2N + D) // (2D)$$

#### Verification of Integer Rounding Vectors:
- Exact $.5$ boundary: $N = 105, D = 10 \implies 10.5 \implies (210 + 10) // 20 = 220 // 20 = 11$.
- Exact $.5$ boundary: $N = 115, D = 10 \implies 11.5 \implies (230 + 10) // 20 = 240 // 20 = 12$.
- Below $.5$: $N = 104, D = 10 \implies 10.4 \implies (208 + 10) // 20 = 218 // 20 = 10$.
- Above $.5$: $N = 106, D = 10 \implies 10.6 \implies (212 + 10) // 20 = 222 // 20 = 11$.
- Zero: $N = 0, D = 10,000 \implies 0 \implies 10,000 // 20,000 = 0$.
- Large values: $N = 999,999,999,995, D = 10 \implies (1,999,999,999,990 + 10) // 20 = 1,000,000,000,000$.

### 9.2 Authoritative Pure Calculation Formulas

#### 1. Estimated Commission per Attributable Order
$$N = \text{commission\_base\_vnd} \times \text{commission\_rate\_bps}, \quad D = 10,000$$
$$\text{commission\_per\_order\_vnd} = (2 \times N + 10,000) // 20,000$$
- *Prerequisites:* `commission_base_vnd` and `commission_rate_bps` must both be non-null. Otherwise `NULL`.

#### 2. Total Fixed Campaign Cost
$$\text{fixed\_campaign\_cost\_vnd} = \text{sample\_cost\_vnd} + \text{content\_cost\_vnd} + \text{promotion\_cost\_vnd}$$
- *Prerequisites:* Evaluated only when all three fixed-cost components are known (non-null or explicitly $0$). If any component is unknown (`NULL`), result is `NULL`.

#### 3. Contribution Margin per Attributable Order
$$\text{contribution\_per\_order\_vnd} = \text{commission\_per\_order\_vnd} - \text{variable\_cost\_per\_attributed\_order\_vnd}$$
- *Prerequisites:* Requires non-null calculated commission per order and non-null variable cost. Otherwise `NULL`.

#### 4. Break-Even Attributable Orders (Exact Integer Ceiling Division)
To eliminate off-by-one errors from premature rounding, break-even uses the exact integer numerator:
$$\text{contrib\_num} = (\text{commission\_base\_vnd} \times \text{commission\_rate\_bps}) - (\text{variable\_cost\_per\_attributed\_order\_vnd} \times 10,000)$$

If `fixed_campaign_cost_vnd` is known ($\ge 0$) and $\text{contrib\_num} > 0$:
- If $\text{fixed\_campaign\_cost\_vnd} == 0 \implies \text{break\_even\_orders} = 0$.
- Else:
  $$A = \text{fixed\_campaign\_cost\_vnd} \times 10,000, \quad B = \text{contrib\_num}$$
  $$\text{break\_even\_orders} = (A + B - 1) // B$$
- *Prerequisites:* If $\text{contrib\_num} \le 0$ (unit contribution is zero or negative), fixed costs are unknown, or inputs are incomplete, `break_even_orders` evaluates to `NULL`.

#### 5. Expected Campaign Economics (Evaluated only when `expected_attributed_orders` is non-null)
- **Expected Gross Commission:**
  $$N = \text{commission\_base\_vnd} \times \text{commission\_rate\_bps} \times \text{expected\_attributed\_orders}, \quad D = 10,000$$
  $$\text{expected\_commission\_vnd} = (2 \times N + 10,000) // 20,000$$
- **Expected Variable Cost:**
  $$\text{expected\_variable\_cost\_vnd} = \text{variable\_cost\_per\_attributed\_order\_vnd} \times \text{expected\_attributed\_orders}$$
- **Expected Net Contribution:**
  $$\text{expected\_contribution\_vnd} = \text{expected\_commission\_vnd} - \text{fixed\_campaign\_cost\_vnd} - \text{expected\_variable\_cost\_vnd}$$
  *(Requires all inputs to be non-null).*
- **Scenario Return on Cost Ratio:**
  Let $\text{total\_campaign\_cost} = \text{fixed\_campaign\_cost\_vnd} + \text{expected\_variable\_cost\_vnd}$.  
  If $\text{total\_campaign\_cost} > 0$ and `expected_contribution_vnd` is known:
  $$\text{return\_on\_cost\_ratio} = \operatorname{round}\left( \frac{\text{expected\_contribution\_vnd}}{\text{total\_campaign\_cost}}, 4 \right)$$
  Returned as a float ratio (e.g. $0.45 = +45\%$). Clearly labeled as a scenario estimate, never as guaranteed commercial ROI.

### 9.3 Normalization Boundary for Legacy Snapshot Price
When `ProductSnapshot.price: Float` is captured as an observed price proxy, it crosses the **single deliberate normalization boundary**:
$$\text{commission\_base\_vnd} = \operatorname{int}\left( \operatorname{Decimal}(\operatorname{str}(\text{latest\_price})).quantize(\operatorname{Decimal}('1'), rounding=\operatorname{ROUND\_HALF\_UP}) \right)$$
Once converted to whole-VND integer, all downstream scenario operations and calculations remain 100% integer arithmetic.

---

## 10. Frozen Observed-Price Proxy & Provenance Mutation Contract

### 10.1 Provenance Mutation Rules (Finding D)
To ensure provenance integrity and prevent forged client states:
1. **Creation Semantics (`POST`):**
   - If `use_observed_price = True`:
     - Client **MUST NOT** provide `commission_base_vnd` (if provided, rejected with HTTP 422: `"Cannot supply manual commission_base_vnd when use_observed_price is true"`).
     - Backend fetches `analysis.deltas.latest_price` from the latest committed snapshot.
     - If snapshot or price is missing/invalid, request fails with HTTP 400 Bad Request.
     - Normalizes float price to whole integer VND.
     - Sets `commission_base_source = 'observed_price_proxy'`.
     - Freezes `commission_base_observed_at = snapshot.captured_at` from the **exact same observation**.
   - If `use_observed_price = False`:
     - Sets `commission_base_source = 'user_entered'`.
     - Sets `commission_base_observed_at = None`.
2. **Generic Update Semantics (`PATCH`):**
   - Schema `EconomicsScenarioUpdate` accepts only user assumptions: `name`, `commission_rate_bps`, `commission_base_vnd`, `sample_cost_vnd`, `content_cost_vnd`, `promotion_cost_vnd`, `variable_cost_per_attributed_order_vnd`, `expected_attributed_orders`.
   - Client **CANNOT** write `commission_base_source` or `commission_base_observed_at`.
   - Client **CANNOT** write `is_default` via PATCH (must use dedicated `set-default` endpoint).
   - If `commission_base_vnd` is provided in PATCH:
     - Automatically resets `commission_base_source = 'user_entered'`.
     - Automatically resets `commission_base_observed_at = None`.
3. **Rebase Proxy Action (`POST .../rebase-price`):**
   - Dedicated endpoint to refresh the proxy from the latest available market price.
   - Atomically updates `commission_base_vnd` and `commission_base_observed_at` from the latest snapshot. Sets source to `'observed_price_proxy'`.
   - Fails with HTTP 400 if product has no valid snapshot price.

---

## 11. Backend API & Service Surface

### 11.1 Route Definitions (`backend/app/api/economics.py`)

All economics endpoints are Product-scoped:

```python
router = APIRouter(prefix="/products/{product_id}/economics", tags=["Economics"])
```

1. `GET /api/products/{product_id}/economics`
   - Returns all scenarios for the product ordered by `created_at ASC`, including calculated derived metrics.
   - Total SQL queries: $\le 2$ (Query 1: Product validation & quarantine check; Query 2: `SELECT * FROM economics_scenarios WHERE product_id = :id`).
   - Response: `List[EconomicsScenarioResponse]`
2. `POST /api/products/{product_id}/economics`
   - Creates a new scenario for the product.
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
   - Clones an existing scenario.
   - Body: `EconomicsScenarioDuplicate(name=...)`. Caller supplies a unique name. If name already exists for that product, returns HTTP 409 Conflict.
   - Cloned scenario always defaults to `is_default = false`.
   - Status: HTTP 201 Created
6. `DELETE /api/products/{product_id}/economics/{scenario_id}`
   - Deletes scenario. If deleted scenario was default and other scenarios remain, atomically promotes the oldest remaining scenario.
   - Status: HTTP 204 No Content
7. `POST /api/products/{product_id}/economics/{scenario_id}/set-default`
   - Atomically promotes target scenario to default.
   - Response: `EconomicsScenarioResponse`
8. `POST /api/products/{product_id}/economics/{scenario_id}/rebase-price`
   - Re-synchronizes commission base with latest observed snapshot price.
   - Response: `EconomicsScenarioResponse`

### 11.2 Pydantic Schemas

```python
class EconomicsScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    commission_rate_bps: Optional[int] = Field(None, ge=0, le=10000)
    commission_base_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    use_observed_price: bool = False
    sample_cost_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    content_cost_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    promotion_cost_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    variable_cost_per_attributed_order_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    expected_attributed_orders: Optional[int] = Field(None, ge=0, le=10**6)
    is_default: bool = False

class EconomicsScenarioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    commission_rate_bps: Optional[int] = Field(None, ge=0, le=10000)
    commission_base_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    sample_cost_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    content_cost_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    promotion_cost_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    variable_cost_per_attributed_order_vnd: Optional[int] = Field(None, ge=0, le=10**11)
    expected_attributed_orders: Optional[int] = Field(None, ge=0, le=10**6)

class EconomicsScenarioDuplicate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

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
   - Commission rate input in percentage (e.g. `12.5%`, max 2 decimals), converted to basis points on save. Rejects fractional bps.
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
- Preserves selection order. Zero per-product HTTP fanout.
- No blended comparison score or ranking.

---

## 13. Query Budgets & Performance Methodology

### 13.1 Query Gate Boundaries (Zero N+1)
All Phase 6 data access must adhere to strict query budgets:
1. **Product Economics Scenarios:**
   - $\le 1$ `economics_scenarios` query.
   - Total SQL queries for endpoint $\le 2$ (Query 1: Product exists and not quarantined; Query 2: `SELECT * FROM economics_scenarios WHERE product_id = :id ORDER BY created_at ASC`).
   - Derived economics computed in memory.
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
   - **Budgets:**
     - Without collection context: **$\le 3$ SQL queries total**.
     - With collection context: **$\le 4$ SQL queries total**.
     - Zero N+1. Zero per-product HTTP fanout.

### 13.2 Performance Benchmark Methodology (Finding L)
- **Fixture Lineage:**
  - 200 Products;
  - 5,000 Product Snapshots;
  - 100 Watchlist items;
  - Representative scenario distribution (some products with 1 scenario, some with 3+, some with 0);
  - Isolated file-backed database fixture (`tmp_path`).
- **Measurement Protocol:**
  - 1 warmup iteration (unmetered);
  - 10 timed iterations;
  - Record full latency series: best, median, p95, worst (max), and exact query count.
- **Hard Regression Gate:**
  - Collection member list with economics: **max / worst $< 200\text{ms}$**.
  - 5-Product Compare with economics: **max / worst $< 200\text{ms}$**.
- **Optimization Target:**
  - Report honestly against the $< 50\text{ms}$ research target (non-blocking optimization target).

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
- Injecting a schema failure leaves marker at `"2"` and aborts startup.

### 14.3 Backup & Restore Policy (ADR-004 Unchanged — Finding G)
Under ADR-004's authoritative offline launcher-owned restore policy:
- **Same-Version Restore:** Version `"2"` backups are rejected with HTTP 400 (API preflight) and exit code 1 (`RESTORE.bat` pre-validation) before stopping services or touching files.
- **Pre-Restore Safety Backup:** Before destructive database replacement, `RESTORE.bat` executes an online SQLite backup (`tinix-pre-restore-v3-...sqlite3`).
- **Atomic Replacement & Manifest Tracking:** Manifest at `backend/.local/restore/manifest.json` tracks status (`PENDING` $\to$ `COMPLETED`).
- **Automated Rollback & Crash Recovery:** Injected failure after replacement triggers automated rollback to the pre-restore safety backup. Interrupted restores are recoverable via `RESTORE.bat --recover`.
- **Round-Trip Integrity:** Version `"3"` backups preserve all scenarios, assumptions, nulls, explicit zeros, default flags, and frozen price proxy timestamps.
- **Exclusion Guarantees:** Local TikTok session (`backend/.local/tiktok-session.json`) remains host-bound and strictly excluded from backups.
- **Isolated Testing:** All destructive backup and restore tests execute on isolated temporary file-backed databases (`tmp_path`); never touch live `backend/affiliate.db`.

---

## 15. Security, Privacy & Diagnostics (Finding H)

1. **Local-First Privacy:** All financial assumptions, costs, and profit calculations are stored exclusively in the local SQLite database. No financial data is ever transmitted to external servers, cloud analytics, or TikTok endpoints.
2. **Zero Credentials/Tokens:** Scenarios require no TikTok partner credentials, OAuth tokens, or payment details.
3. **Safe Diagnostics:** `/api/diagnostics` reports only safe aggregate table row counts (`table_counts["economics_scenarios"] = ...`). No scenario names, commission rates, cost figures, or derived outputs are exposed via diagnostics.
4. **Preserved Security Debt:**
   - 1 High `source-map-js` advisory (`GHSA-68fv-2mgg-jv7q`) in production dependency graph: non-blocking build-time debt.
   - Development-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`) in devDependencies: non-blocking development debt.
   - `StarletteDeprecationWarning`: non-blocking.
   - Runtime `PRAGMA foreign_keys = 0`: preserved for stability.

---

## 16. Mandatory Manual QA Matrix (Finding K)

Implementation qualification requires executing and verifying the following manual test matrix against the running development runtime:

| Step | Test Area | User Action / Flow | Expected System Behavior |
| :---: | :--- | :--- | :--- |
| **M1** | Scenario Creation | Navigate to Product Detail $\to$ Click `+ Tạo kịch bản` $\to$ Enter Name, Rate (10%), Base (100,000 VND), Sample Cost (20,000 VND). | Scenario created, marked with default star badge. Unit economics display: Commission = 10,000 VND, Contribution = 10,000 VND, Fixed Cost = 20,000 VND, Break-Even = 2 orders. |
| **M2** | Price Proxy Freeze | Click `+ Tạo kịch bản` $\to$ Click `Lấy giá hiển thị hiện tại` $\to$ Save. | Commission base field is populated with rounded VND snapshot price; provenance badge shows `Giá quan sát đóng băng` with capture timestamp. |
| **M3** | Default Switching | Create Scenario B $\to$ Verify B has no default badge $\to$ Click `Đặt làm mặc định` on B. | Default star badge moves to B; Scenario A loses default badge. Collection and Compare immediately reflect B's metrics. |
| **M4** | Default Promotion on Delete | Delete Scenario B (current default). | Scenario B deleted; Scenario A is automatically promoted to default and displays star badge. |
| **M5** | Null vs Zero Semantics | Edit Scenario A $\to$ Set Promotion Cost to `0` $\to$ Leave Content Cost blank. | Fixed cost and Break-Even render `—` (Chưa thiết lập) because Content Cost is unknown. Promotion cost explicitly displays `0 đ`. |
| **M6** | Input Bounds & Validation | Try to enter Commission Rate `100.5%` or negative cost `-1000`. | Frontend validation blocks submission or API returns clean validation error. |
| **M7** | Price Rebase Action | In scenario with frozen proxy, click `Cập nhật theo giá mới nhất`. | Base price updates to latest snapshot; observation timestamp refreshes; toast notification confirms rebase. |
| **M8** | Duplicate Scenario | Click `Nhân bản` $\to$ Enter unique name $\to$ Submit. | New scenario created with identical assumptions, `is_default = false`. |
| **M9** | Collections Workspace | Open Collections $\to$ View member table containing the product. | Member row displays default scenario's Commission/order, Contribution/order, and Break-even orders. |
| **M10**| Compare Workspace | Add 2–5 products to Compare Tray $\to$ Open Compare modal. | Economics row group displays each product's default scenario economics. Products with no scenarios show clean empty indicators (`—`). |
| **M11**| Stale Response & Retry | Simulate slow network/API error during scenario fetch. | Visible error message displayed with a working `Thử tải lại` (Retry) button. |
| **M12**| Accessibility & Focus | Use `Tab`, `Shift+Tab`, `Enter`, `Escape` to navigate workspace and modals. | Modals trap focus; `Escape` closes modal; focus restores to trigger button; all action buttons have clear aria labels. |

---

## 17. Authoritative Acceptance Criteria (P6-AC-01 to P6-AC-42 — Finding N)

### Domain Separation & Attribution Invariants
- **`P6-AC-01` — Strict Domain Separation:**  
  *Requirement:* Economics scenario creation, editing, or deletion must have zero effect on Phase 2 Trend Score, trend state, momentum signals, evidence confidence, Why Trending reasons, Watchlist membership, scheduled refresh, or alert rule evaluation.  
  *Evidence:* Automated test asserting identical trend scores and alert triggers before and after creating scenarios.  
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
- **`P6-AC-05` — Numeric Types & Safe-Integer Bounds Validation:**  
  *Requirement:* Money fields persist as integer VND ($0 \le \text{cost} \le 10^{11}$). Commission rate persists as basis points ($0 \le \text{bps} \le 10,000$). Negative values or out-of-bound values are rejected with HTTP 422. All values safely within `Number.MAX_SAFE_INTEGER`.  
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
  *Requirement:* Two concurrent threads attempting first-scenario creation both succeed or retry cleanly; exactly one becomes default.  
  *Evidence:* Multi-threaded test with barrier asserting 2 created scenarios, exactly 1 default.  
  *Validation:* Concurrency test suite.
- **`P6-AC-18` — Concurrency: Race on Set-Default and Delete:**  
  *Requirement:* Concurrent `set-default` and `delete` operations maintain the exactly-one-default invariant without database corruption or dangling states.  
  *Evidence:* Multi-threaded barrier test verifying exactly 1 default committed.  
  *Validation:* Concurrency test suite.
- **`P6-AC-19` — Concurrency: Rollback Safety on Promotion:**  
  *Requirement:* Injected failure during default promotion rolls back the entire transaction, preserving the original default.  
  *Evidence:* Rollback injection test verifying no uncommitted or zero-default state.  
  *Validation:* Concurrency test suite.

### Calculation Engine, Precision & Rounding
- **`P6-AC-20` — Authoritative Exact Integer Ratio Rounding:**  
  *Requirement:* Backend rounds derived monetary outputs to whole VND using exact integer ratio arithmetic $(2N + D) // (2D)$. Bankers rounding and binary float divisions are prohibited.  
  *Evidence:* Boundary tests verifying $10.5 \to 11$, $11.5 \to 12$, $10.49 \to 10$, $10.51 \to 11$.  
  *Validation:* `backend/tests/test_phase6_economics.py`.
- **`P6-AC-21` — Commission per Order Formula:**  
  *Requirement:* Evaluates $(2N + 10,000) // 20,000$ when both base and bps exist; otherwise `null`.  
  *Evidence:* Exact integer arithmetic assertions across test vectors.  
  *Validation:* Unit tests.
- **`P6-AC-22` — Fixed Campaign Cost & Null Propagation:**  
  *Requirement:* Evaluates sum of sample, content, and promotion costs only when all three are non-null/zero. If any is missing, fixed cost is `null`.  
  *Evidence:* Assertions with missing components returning `null`.  
  *Validation:* Unit tests.
- **`P6-AC-23` — Contribution Margin per Order Formula:**  
  *Requirement:* Evaluates commission per order minus variable cost per order. If variable cost is unknown, evaluates to `null`.  
  *Evidence:* Unit test assertions.  
  *Validation:* Unit tests.
- **`P6-AC-24` — Break-Even Attributable Orders Exact Math:**  
  *Requirement:* Calculated using exact integer ceiling division $(A + B - 1) // B$. Returns `null` if $\text{contrib\_num} \le 0$ or fixed costs unknown.  
  *Evidence:* Boundary tests asserting exact integer output without off-by-one errors from intermediate float rounding.  
  *Validation:* Unit tests.
- **`P6-AC-25` — Expected Campaign Economics:**  
  *Requirement:* Expected gross commission, variable cost, net contribution, and return-on-cost evaluated only when `expected_attributed_orders` is non-null. Exact integer arithmetic rounded once at final output.  
  *Evidence:* Verification of expected metrics against exact reference vectors.  
  *Validation:* Unit tests.
- **`P6-AC-26` — Zero Persisted Calculations:**  
  *Requirement:* No calculated metrics are stored in database columns. Modifying assumptions instantly updates derived metrics on next read.  
  *Evidence:* DB inspection showing only raw input columns; updating rate immediately changes response.  
  *Validation:* Database test.

### Frozen Observed-Price Proxy & Provenance Mutation
- **`P6-AC-27` — Observed-Price Proxy Freezing & Validation:**  
  *Requirement:* Choosing `use_observed_price=True` freezes latest snapshot price and timestamp into scenario. Supplying manual base when `use_observed_price=True` is rejected with HTTP 422.  
  *Evidence:* API call with `use_observed_price=True` freezes current price and timestamp; manual conflict rejected.  
  *Validation:* API test.
- **`P6-AC-28` — Proxy Immutability Against Crawlers:**  
  *Requirement:* New crawler snapshots with different prices do not alter existing frozen proxy scenarios.  
  *Evidence:* Ingesting a new snapshot with 2x price does not mutate scenario's `commission_base_vnd`.  
  *Validation:* Integration test.
- **`P6-AC-29` — Provenance Reset on Manual Base Edit:**  
  *Requirement:* Generic PATCH editing `commission_base_vnd` automatically resets `commission_base_source = 'user_entered'` and clears `commission_base_observed_at`. Client cannot forge source or timestamp.  
  *Evidence:* PATCH test asserting provenance reset and rejection of forged provenance headers.  
  *Validation:* API test.
- **`P6-AC-30` — Deterministic Duplicate Semantics:**  
  *Requirement:* `duplicate` endpoint accepts explicit `name`. If name is already taken, returns HTTP 409 Conflict. Cloned scenario defaults to `is_default = false`.  
  *Evidence:* Duplicate test verifying unique name validation and non-default status.  
  *Validation:* API test.
- **`P6-AC-31` — Explicit Price Rebase:**  
  *Requirement:* `rebase-price` endpoint updates `commission_base_vnd` and `commission_base_observed_at` to latest snapshot price. Fails with HTTP 400 if product has no price.  
  *Evidence:* Rebase updates price to new snapshot timestamp.  
  *Validation:* API test.

### Workspace Integrations & Query Budgets
- **`P6-AC-32` — Product Detail Economics Section UX:**  
  *Requirement:* Product Detail renders scenario switcher, create/edit modal, default marker, provenance labels (`User assumption`, `Observed price proxy`, `Missing`), commercial payout disclosure, and loading/retry states.  
  *Evidence:* Frontend Vitest component tests verifying rendered elements and user interactions.  
  *Validation:* `frontend/tests/phase6-economics.test.tsx`.
- **`P6-AC-33` — Collections Integration & $\le 3$ Query Budget:**  
  *Requirement:* Collection member list displays default scenario summary via batched query. Query count $\le 3$ SQL queries total; zero N+1.  
  *Evidence:* Query listener assertion on collection member retrieval with economics.  
  *Validation:* `backend/tests/test_performance_and_queries.py`.
- **`P6-AC-34` — Compare Integration & $\le 4$ Query Budget:**  
  *Requirement:* 5-Product compare renders default scenario economics columns. Query count $\le 3$ (without collection) / $\le 4$ (with collection). Zero N+1. Zero per-product HTTP fanout.  
  *Evidence:* Query listener assertion on CompareService call with economics.  
  *Validation:* `backend/tests/test_performance_and_queries.py`.
- **`P6-AC-35` — Performance Regression Gate (Max <200ms):**  
  *Requirement:* Collection member list and 5-Product compare on representative 200-product/5,000-snapshot fixture execute with worst/max latency $<200\text{ms}$ across 10 iterations.  
  *Evidence:* Benchmark test reporting best, median, p95, worst latencies.  
  *Validation:* Performance benchmark suite.

### Disaster Recovery, Bootstrap & Upgrades
- **`P6-AC-36` — Additive Bootstrap & Compatibility Advance `"2" \to "3"`:**  
  *Requirement:* Startup runs `create_all()`, verifies required schema dynamically, and advances compatibility marker from `"2"` to `"3"`. Injected failure leaves marker at `"2"` and aborts startup.  
  *Evidence:* Isolated bootstrap test verifying schema creation and marker transition.  
  *Validation:* `backend/tests/test_phase6_backup_upgrade.py`.
- **`P6-AC-37` — Rejection of Version `"2"` Backups:**  
  *Requirement:* Version `"2"` backups are rejected with HTTP 400 (API preflight) and exit code 1 (`RESTORE.bat` pre-validation) before stopping services or touching database files.  
  *Evidence:* Restore candidate validation test rejecting v2 backup on v3 application.  
  *Validation:* Backup test suite.
- **`P6-AC-38` — Pre-Restore Safety Backup & Atomic Replacement:**  
  *Requirement:* `RESTORE.bat` creates a valid pre-restore safety backup before replacement. Injected failure post-replacement automatically rolls back to safety backup.  
  *Evidence:* Rollback injection test on isolated file-backed database.  
  *Validation:* Disaster recovery test suite.
- **`P6-AC-39` — Version `"3"` Backup Round-Trip Integrity:**  
  *Requirement:* Creating a v3 backup and restoring into an empty database fully restores all scenarios, nulls, defaults, and provenance. Local session remains excluded.  
  *Evidence:* Full backup creation, inspection, and restore round-trip test.  
  *Validation:* Backup test suite.

### Privacy, Documentation & Validation Discipline
- **`P6-AC-40` — Safe Diagnostics & Zero Telemetry:**  
  *Requirement:* `/api/diagnostics` reports only safe table row count for `economics_scenarios`. No scenario names, rates, costs, or assumptions exposed. Zero external network telemetry.  
  *Evidence:* API diagnostics payload inspection test and network egress audit.  
  *Validation:* `backend/tests/test_phase6_economics.py`.
- **`P6-AC-41` — Operator Documentation Deliverables:**  
  *Requirement:* `ARCHITECTURE.md` updated to document Phase 6 implementation; `README.md` updated with backup compatibility version `"3"`, v2 rejection notices, and session exclusion.  
  *Evidence:* Git diff and document review.  
  *Validation:* Documentation review.
- **`P6-AC-42` — Full Test Suite, Health & Integrity Clean:**  
  *Requirement:* Backend pytest (executed via repository venv python), frontend Vitest, TypeScript typecheck (`tsc --noEmit`), ESLint, Next.js build, `healthcheck.bat`, and SQLite integrity (`PRAGMA integrity_check`, `PRAGMA foreign_key_check`) all pass cleanly.  
  *Evidence:* Clean CLI execution logs across all tools.  
  *Validation:* Full validation runner.

---

## 18. Implementation Sequencing & Workstreams

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
└───────────────────────────┘
```

### Workstream 0: Baseline & Ancestry Verification
- **Objectives:** Verify clean Git working tree, commit ancestry descending from ADR-005 (`d5fc2519abc8c67cc3751d62939fd7213b9794a6`), and ensure all pre-Phase-6 tests pass.
- **Deliverables:** Verified baseline confirmation.
- **Dependencies:** None.

### Workstream 1: Pure Economics Calculation Engine & Precision Tests
- **Objectives:** Create `backend/app/analytics/economics.py`. Implement integer ratio rounding $(2N + D) // (2D)$, exact rational math (`RATE_SCALE = 10_000`), unit commission, contribution margin, break-even orders via integer ceiling division, expected campaign economics, and strict null propagation.
- **Deliverables:** Pure calculation module, isolated unit test suite in `backend/tests/test_phase6_economics.py` covering formulas, exact boundaries, and null trees.
- **Dependencies:** Workstream 0.

### Workstream 2: Data Model, Concurrency & Default Scenario Invariants
- **Objectives:** Create `backend/app/models/economics_scenario.py`. Register model on `Base.metadata`. Implement composite unique index on `(product_id, name)` and partial unique default index. Implement `EconomicsService` with atomic default management (`BEGIN IMMEDIATE`), deterministic promotion on delete, bounded retries, and transactional concurrency guards.
- **Deliverables:** SQLAlchemy model, service class, unit/concurrency tests verifying all 8 race condition scenarios.
- **Dependencies:** Workstream 1.

### Workstream 3: Bootstrap, Dynamic Schema Derivation & Compatibility Version `"3"`
- **Objectives:** Advance `BackupService.COMPATIBILITY_VERSION = "3"` in `backend/app/services/backup_service.py`. Update `BACKUP_FILENAME_PATTERN` and `SAFETY_BACKUP_PATTERN` regex. Update `backend/app/db/init_db.py` to register model and advance compatibility marker only after dynamic schema verification.
- **Deliverables:** Updated backup service and init_db, isolated upgrade test verifying v2 $\to$ v3 transition.
- **Dependencies:** Workstream 2.

### Workstream 4: Backend REST APIs & Rebase Proxy
- **Objectives:** Create `backend/app/api/economics.py`. Wire CRUD, set-default, duplicate, and rebase-price routes. Enforce quarantine exclusion, safe-integer boundary validations, provenance mutation guards, and conflict error codes. Update `main.py` router registration. Include safe table count in `/api/diagnostics`.
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
- **Objectives:** Implement automated tests for rejection of v2 backups on v3 app, round-trip v3 backup creation and restore, safety backup creation, and crash recovery. Verify zero session leakage. All tests run on isolated temporary databases.
- **Deliverables:** Full disaster recovery test suite in `backend/tests/test_phase6_backup_upgrade.py`.
- **Dependencies:** Workstream 7.

### Workstream 9: Full Regression, Benchmark, Manual QA & Documentation
- **Objectives:** Execute representative 200-product/5,000-snapshot benchmarks (max latency <200ms hard gate). Run full regression suites (pytest 178+, Vitest 46+, typecheck, lint, production build). Execute manual QA matrix. Update `ARCHITECTURE.md` and `README.md`. Prepare completion report.
- **Deliverables:** Performance evidence, documentation updates, final completion report.
- **Dependencies:** Workstream 8.

---

## 19. Expected Modules & Files Affected

### New Files to Create During Implementation
1. `backend/app/models/economics_scenario.py` — SQLAlchemy model for `economics_scenarios`.
2. `backend/app/analytics/economics.py` — Pure calculation module and integer ratio rounding policy.
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

## 20. Phase 1–5 Regression Protection Matrix

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

## 21. Authoritative Validation Commands (Finding M)

The implementation agent must execute and pass the following repository-standard commands using the dedicated virtual environment interpreter:

### 1. Backend Validation
```powershell
# Focused Phase 6 unit, concurrency, and API tests
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/test_phase6_economics.py -v

# Isolated upgrade, bootstrap, and backup tests
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/test_phase6_backup_upgrade.py -v

# Performance query count and benchmark tests
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/test_performance_and_queries.py -v -k "economics"

# Full backend test suite (all phases)
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ -v
```

### 2. Frontend Validation
```powershell
# Focused Phase 6 Vitest tests
cd frontend; npx vitest run tests/phase6-economics.test.tsx; cd ..

# Full frontend Vitest suite
cd frontend; npm test; cd ..

# TypeScript typecheck
cd frontend; npx tsc --noEmit; cd ..

# ESLint lint check
cd frontend; npm run lint; cd ..

# Production build compilation
cd frontend; npm run build; cd ..
```

### 3. Runtime Health & SQLite Integrity
```powershell
# Health check script
.\healthcheck.bat

# SQLite integrity and foreign-key check
.\backend\.venv\Scripts\python.exe -c "import sqlite3; con = sqlite3.connect('backend/affiliate.db'); print('Integrity:', con.execute('PRAGMA integrity_check').fetchall()); print('FK Check:', con.execute('PRAGMA foreign_key_check').fetchall()); con.close()"
```

### 4. Disaster Recovery Qualification
```powershell
# Validate BACKUP.bat generates valid v3 backup
.\BACKUP.bat

# Validate RESTORE.bat pre-validation rejects legacy v2 backup on v3 application
# (Executed on isolated test instance)
```

---

## 22. Documentation Requirements (Finding I)

Following implementation, the following documentation deliverables are required:
1. **`ARCHITECTURE.md`:** Update implementation status of Phase 6 from architecture-accepted to implemented. Record authoritative integer formulas, rounding policy, and query budgets.
2. **`README.md`:** Update operator disaster recovery section detailing backup compatibility version `"3"`, rejection of version `"2"` backups, requirement to generate fresh v3 backups, and session exclusion.
3. **`PHASE_6_COMPLETION_REPORT.md`:** Produce the comprehensive completion report detailing all 42 acceptance criteria, benchmark latency results, query counts, manual QA results, and test passes.
4. **`PLAN.md` & `PROJECT_STATUS.md`:** Reconcile project status and acceptance gates upon Project Control review.

---

## 23. Preserved Deferred Work

The following non-blocking debt and deferred roadmap items remain active and preserved:
1. High `source-map-js` advisory (`GHSA-68fv-2mgg-jv7q`) in production dependency graph: non-blocking build-time debt.
2. Development-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`) in devDependencies: non-blocking development debt.
3. `StarletteDeprecationWarning` during test runs: non-blocking.
4. Runtime connection `PRAGMA foreign_keys = OFF`: maintained for cross-phase operational stability.
5. Automatic broad home/category discovery & CAPTCHA bypass: deferred external platform limitation.
6. Standalone executable packaging (`.exe` / installer): deferred; supported release boundary remains Windows / local / source-based runtime.
7. Cloud / multi-user deployment: deferred.

---

## 24. Plan Gate & Verification Metadata

```yaml
Plan Metadata:
  Phase: "Phase 6 — Affiliate Economics & Profitability Intelligence"
  Scope: "VND-only, manual-first Product Economics Scenarios"
  Plan Status: "APPROVED"
  Implementation Authorization: "AUTHORIZED"
  Project Control Approval: "APPROVED"
  Authoritative Research Artifact: "research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md" (commit 8c3f8949b8c9e61691c2e2756557e9abadc035b5)
  Accepted Architecture Decision: "docs/architecture/ADR-005.md" (commit d5fc2519abc8c67cc3751d62939fd7213b9794a6)
  ADR-005 Acceptance Record: "PROJECT_CONTROL_ADR005_ACCEPTED.md"
  Plan Approval Record: "PROJECT_CONTROL_PHASE6_PLAN_APPROVED.md"
  Planning Baseline Commit: "d5fc2519abc8c67cc3751d62939fd7213b9794a6"
  Approved Plan Baseline Commit: "4713fa422eb7f407b78995a9d453711910efc354"
  Authoritative Actual Selection HEAD Commit: "d97f00f7819e778954a76abe3605e1442ea4155d"
  Current Implemented Compatibility Version: "2"
  Target Compatibility Version: "3"
  Acceptance Criteria Count: 42 (P6-AC-01 through P6-AC-42)
  Workstreams Count: 10 (WS-0 through WS-9)
```

**Implementation Authorization Notice:**  
Plan formally reviewed and approved by `00 — Project Control & Roadmap`. Implementation is AUTHORIZED.

