# Phase 6 Research — Affiliate Economics & Profitability Intelligence

Date: 2026-10-06  
Role: `01 — Architecture & Repo Research`  
Task type: research only  
Implementation authorization: **NOT AUTHORIZED**  
Product recommendation: **RECOMMEND WITH REVISED SCOPE**  
Research readiness: **RESEARCH READY FOR PROJECT CONTROL**

---

## 1. Executive conclusion

Phase 6 should not attempt to infer affiliate earnings from TikTok market sales or silently treat crawler-observed commission/price data as the user's real creator payout context.

The smallest coherent Phase 6 product is:

> **Manual-first, Product-scoped named Economics Scenarios** with explicit user assumptions, an optional frozen observed-VND-price proxy, one backend calculation authority, deterministic break-even/contribution formulas, and clear provenance labels.

Economics remains strictly separate from:

- Trend Score;
- trend eligibility/evidence;
- Watchlist monitoring;
- alert semantics;
- Collections organization;
- crawler/discovery semantics.

Repository verification is now complete. The prior source-access blocker is closed.

The research gate is technically ready to return to `00 — Project Control & Roadmap`.

Before Phase 6 planning begins, Project Control must reconcile one durable-state identifier discrepancy: the previously reported full Phase 6 selection SHA is not the actual Git SHA.

No Phase 6 implementation is authorized by this document.

---

## 2. Repository verification reconciliation

### 2.1 Authoritative actual repository state

Repository-aware verification established:

- branch: `main`;
- authoritative actual HEAD:
  `d97f00f7819e778954a76abe3605e1442ea4155d`;
- working tree: clean;
- local branch: ahead `origin/main` by 8 commits;
- no product-code or test changes after:
  `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98`.

Therefore source verification applies to the accepted Phase 5 product code.

### 2.2 SHA discrepancy requiring Project Control reconciliation

A previously supplied Phase 6 selection identifier was:

`d97f00f9a25b16f398f658be424b94f1e58286ad`

That full SHA is **not equal** to the actual repository HEAD:

`d97f00f7819e778954a76abe3605e1442ea4155d`

Do not describe these as the same commit.

Repository truth is the actual Git SHA:

`d97f00f7819e778954a76abe3605e1442ea4155d`

The older full SHA must be treated as a previously reported identifier discrepancy and corrected in durable Project Control state before Phase 6 plan approval.

This discrepancy does **not** require more architecture research because repository ancestry/product-code state is otherwise verified and the working tree is clean.

---

## 3. Verified current repository facts

### 3.1 Product and snapshot data

Verified current source state:

- `Product` itself has no price, currency or sold-count columns.
- `ProductSnapshot` stores nullable:
  - `price: Float`;
  - `original_price: Float`;
  - `commission_rate: Float`;
  - `sold_count: Integer`;
  - captured timestamp.
- price parsing accepts explicitly VND offers; non-VND price remains `null`;
- there is no explicit Product/ProductSnapshot currency column;
- frontend money formatting is VND-first/default-VND;
- current price surfaced to UI is:
  `analysis.deltas.latest_price`.

### 3.2 Semantics of existing snapshot commission rate

`ProductSnapshot.commission_rate` is a **verified existing field**.

However, repository existence does not establish that it is an authoritative creator-specific payout rate suitable for Phase 6 calculations.

Current external/domain research establishes that TikTok affiliate rates can depend on collaboration, creator, Shop Ads, tier and attribution context.

Therefore Phase 6 MUST NOT automatically use existing `ProductSnapshot.commission_rate` as the calculation authority unless a future source-specific research task proves:

- its exact source;
- creator/account context;
- collaboration context;
- freshness;
- applicability to the current user/scenario.

For Phase 6 MVP, the authoritative economics commission rate remains the **explicit scenario assumption**.

The existing snapshot field may remain market/platform observation data but does not silently become user economics truth.

### 3.3 Phase 5 backup/bootstrap

Verified:

- required backup schema is derived dynamically from `Base.metadata`;
- additive tables use the current `create_all()` + verify + compatibility-marker pattern;
- current portable compatibility version is `"2"`;
- adding one new required economics table changes required schema;
- under ADR-004 same-version semantics this requires compatibility `"2" → "3"`;
- v2 backup is rejected by the v3 application;
- Phase 5 bootstrap/backup tests provide the established test pattern.

### 3.4 Phase 5 Compare query baseline

Verified current Compare query counts:

- **2 queries** without Collection context;
- **3 queries** with Collection context.

One batched economics/default-scenario query is feasible.

Candidate Phase 6 budgets:

- **<= 3 total** without Collection context;
- **<= 4 total** with Collection context;
- zero N+1.

### 3.5 Phase 5 Collections query baseline

Verified:

- current Collection member-list budget is exactly **2 queries**;
- one batched default-scenario lookup is feasible;
- candidate Phase 6 Collection list budget:
  **<= 3 total queries**;
- zero N+1;
- no persistent `CollectionItem → EconomicsScenario` reference is necessary for MVP.

### 3.6 Saved Views

Phase 5 Saved View V1 strict schemas are verified.

They remain frozen and unchanged in Phase 6 MVP.

### 3.7 CSV/export

Existing export architecture is verified.

Economics CSV is **DEFERRED from Phase 6 MVP** unless Project Control later identifies a compelling product need.

### 3.8 Dependencies

Manual-first scenario economics requires no new third-party dependency.

---

## 4. Domain boundary

The architecture must preserve three separate classes of information.

### 4.1 Market / trend evidence

Examples:

- observed VND price;
- Product sold count;
- sales velocity;
- review/rating data;
- Trend Score;
- trend evidence/confidence;
- freshness/staleness;
- crawler-observed snapshot fields.

This describes the market/product.

### 4.2 User/business economics assumptions

Examples:

- assumed affiliate commission rate;
- assumed commission base per attributable order;
- sample/product acquisition cost;
- content production cost;
- planned promotion/ad spend;
- variable cost per attributable order;
- optional expected attributable orders.

This describes the user's business scenario.

### 4.3 Derived profitability estimates

Examples:

- estimated commission per attributable order;
- fixed campaign cost;
- contribution per attributable order;
- break-even attributable orders;
- optional expected commission;
- optional expected contribution;
- optional scenario return on cost.

These are deterministic results from the scenario assumptions.

They are not observed TikTok payout.

---

## 5. Binding economics invariants

### 5.1 No affiliate attribution from market sales

The following formula is prohibited:

`sales_velocity × commission_per_order`

as “estimated affiliate earnings”.

Do NOT calculate:

- daily affiliate commission from market sales velocity;
- attributable orders from Product sold count;
- affiliate revenue from cumulative sold count;
- payback time from market sales velocity.

Product sold count/sales velocity remains **MARKET EVIDENCE ONLY**.

Actual/expected affiliate attribution requires explicit user attributable-order assumptions or a future authoritative attribution source.

### 5.2 Fixed vs variable costs

Fixed campaign costs:

- sample/product acquisition cost;
- content production cost;
- planned promotion/ad spend.

Variable cost:

- variable cost per attributable order.

The complete fixed campaign cost is never subtracted from every individual order.

### 5.3 Unknown is not zero

Unknown financial assumptions remain `null`.

If the user explicitly states a cost is zero/not applicable, integer zero is valid.

Dependent derived metrics remain `null` if a required input is unknown.

This preserves the project's existing null semantics and prevents false profitability.

---

## 6. Current official TikTok Shop economics findings

Current official TikTok Shop Vietnam documentation supports these domain conclusions.

### 6.1 Affiliate payout is attribution-based

Creator affiliate commission applies to items sold through the creator's affiliate content/channel.

General Product sold count is not creator-attributed order count.

### 6.2 Commission calculation base

Official creator documentation describes commission based on:

`actual buyer-paid price × commission rate`

where actual paid price can differ from public/store price due to coupons/discounts/tax treatment.

Other official material describes final commission using revenue after refunds.

Therefore public/observed Product price is not guaranteed to equal the final eligible commission base.

### 6.3 Estimated commission is not final payout

Final commission can differ because of:

- buyer cancellation;
- partial/full refund;
- settlement status;
- actual paid amount;
- commission context.

Phase 6 estimates must be labeled as scenario estimates.

### 6.4 Commission rate is contextual

Official TikTok documentation supports contexts including:

- Open Collaboration;
- Target Collaboration;
- Standard commission;
- Shop Ads commission;
- tiered commission;
- affiliate-link attribution;
- rate-transition/protection behavior.

Therefore one crawler-observed rate is not automatically universal for the Product/user.

### 6.5 Official Affiliate APIs exist but are conditional

TikTok Shop Partner Center documents Affiliate APIs, but access requires approved integration/authorization context.

Potential future requirements include:

- Partner/ISV access;
- Affiliate API activation;
- Creator/Seller authorization;
- OAuth/access tokens;
- token refresh/revocation handling;
- external network dependency;
- permission/scope management.

This is a legitimate future integration, not Phase 6 MVP.

---

## 7. Data-source recommendation

### Option A — automatic crawler/private-page commission extraction

**REJECT for Phase 6 MVP.**

Reasons:

- public PDP is not a stable creator-specific commission source;
- commission context varies;
- private creator dashboard scraping would expand the local-session/security boundary;
- it risks coupling economics truth to fragile crawler behavior;
- no CAPTCHA/anti-bot bypass is allowed.

### Option B — official Affiliate API

**DEFER / CONDITIONAL FUTURE WORK.**

It is the preferred future automatic source if the project later has valid Partner/Creator authorization.

It is not the minimum local Phase 6 architecture.

### Option C — manual user-entered assumptions

**CONFIRMED BASELINE.**

This gives:

- transparent inputs;
- no external account dependency;
- deterministic offline behavior;
- no invented attribution;
- user-specific economics context.

### Final data-source recommendation

**Manual-first**, with optional explicit use of current observed VND Product price as a frozen proxy.

No silent platform refresh.
No silent replacement of user assumptions.
No private creator-dashboard scraping.

---

## 8. Final scenario model

### 8.1 Ownership

Recommend one new persistent entity:

`EconomicsScenario`

Ownership:

`Product 1 → many EconomicsScenario`

Do not persist scenario data on:

- Product;
- WatchlistItem;
- CollectionItem.

Reason:

economics is a separate business-assumption domain and multiple scenarios per Product are useful.

### 8.2 Multiple scenarios

**CONFIRMED.**

Examples:

- Organic;
- Paid promotion;
- Higher commission offer;
- Sample-cost case.

This enables real decision comparison without a general spreadsheet engine.

### 8.3 Final recommended fields

All items below are **PROPOSED / RECOMMENDED**, not existing Phase 6 implementation.

Conceptual fields:

- `id`
- `product_id`
- `name`
- `commission_rate_bps`
- `commission_base_vnd`
- `commission_base_source`
- `commission_base_observed_at`
- `sample_cost_vnd`
- `content_cost_vnd`
- `promotion_cost_vnd`
- `variable_cost_per_attributed_order_vnd`
- `expected_attributed_orders`
- `is_default`
- `created_at`
- `updated_at`

No generic `currency` column in Phase 6 MVP.

No formula JSON.
No line-item table.
No persisted derived values.

### 8.4 Economic meaning of each field

#### `commission_rate_bps`

User-entered affiliate commission assumption.

- integer basis points;
- `100 bps = 1%`;
- valid bounded range:
  `0..10000`;
- fixed until explicit user edit;
- never inferred from sales velocity.

#### `commission_base_vnd`

Assumed eligible buyer-paid amount per attributable order.

It is a scenario input, not automatically the current Product price.

#### `commission_base_source`

Recommended constrained values:

- `user_entered`
- `observed_price_proxy`

#### `commission_base_observed_at`

Required when `commission_base_source = observed_price_proxy`.

Records which Product-price observation was frozen into the scenario.

Null for manually entered base amount.

#### Fixed costs

- `sample_cost_vnd`
- `content_cost_vnd`
- `promotion_cost_vnd`

Each independently nullable.

Unknown does not mean zero.

#### Variable cost

`variable_cost_per_attributed_order_vnd`

Nullable integer VND.

#### `expected_attributed_orders`

Optional integer assumption.

This is explicitly user-entered.

It is never derived from Product sold count or trend data.

### 8.5 Why no currency field

Phase 6 MVP currency is fixed to:

`VND`

Repository facts:

- parser only accepts explicit VND prices;
- non-VND prices remain null;
- no Product currency field exists;
- frontend is VND-first;
- no FX engine exists or is approved.

Introducing a nominal arbitrary `currency` column would imply support the product does not actually have.

Economic consequence:

Phase 6 scenarios are VND-only.

Multi-currency/FX support requires separate future architecture/product work.

---

## 9. Numeric and rounding decision

### 9.1 Options evaluated

#### Option A — Float

Matches legacy `ProductSnapshot.price`/`commission_rate`.

**Rejected for new financial assumptions.**

Reason:

binary floating point is approximate and can create non-deterministic-looking financial artifacts.

Legacy market observations using Float do not require new financial state to repeat that representation.

#### Option B — integer VND + integer commission basis points

**RECOMMENDED.**

Persist money as whole VND integer values.

Persist commission rate as integer basis points.

Advantages:

- exact SQLite INTEGER storage;
- matches VND whole-unit UX;
- deterministic arithmetic;
- simple JSON/TypeScript number representation within practical local-app ranges;
- no Decimal serialization framework required;
- easy validation;
- no binary floating-point artifacts.

#### Option C — Decimal/Numeric

Technically possible but not preferred for persistence here.

SQLite NUMERIC affinity does not itself guarantee arbitrary exact decimal storage; values may still be represented as INTEGER or REAL depending on the inserted value/driver behavior.

A fully exact Decimal approach would require an explicit representation/adapter discipline.

For a VND-only app, integer money + basis points is smaller and more robust.

### 9.2 Final persisted representation

Money:

`INTEGER VND`

Commission rate:

`INTEGER basis points`

Expected orders:

`INTEGER`

### 9.3 Calculation representation

Backend financial calculations use exact integer/rational arithmetic.

Define:

`RATE_SCALE = 10_000`

For non-negative scenario inputs:

`commission_numerator = commission_base_vnd × commission_rate_bps`

Exact commission rational:

`commission_numerator / RATE_SCALE`

### 9.4 Rounding policy

Persisted assumptions are never rounded except when converting validated UI percent input to basis points.

All derived money displayed/returned by the API is rounded to whole VND using one backend policy:

**round-half-up to nearest VND**

No frontend-independent rounding authority.

Where formulas can remain exact for decision logic (for example break-even), calculate using integer/rational form before final presentation rounding.

### 9.5 API boundary

Recommended API semantics:

- money fields serialize as integer VND;
- commission rate may accept/display a user-friendly percent, but backend converts/validates against basis points;
- authoritative response includes normalized basis points and derived integer-VND outputs;
- frontend does not implement an independent calculation engine.

---

## 10. Default scenario semantics

### 10.1 Cardinality invariant

For a Product:

- zero scenarios → zero defaults;
- one or more scenarios → **exactly one committed default**.

Therefore zero defaults is **not valid** once scenarios exist.

### 10.2 First scenario

The first scenario created for a Product automatically becomes default.

### 10.3 Additional scenario

Additional scenarios default to `is_default = false` unless the create operation explicitly requests it as the new default.

### 10.4 Setting default

Setting a scenario as default is one atomic backend transaction:

1. clear existing default for that Product;
2. set target scenario default;
3. commit.

No intermediate committed state with two defaults.

### 10.5 Unique partial index

Recommended:

a unique partial index on `product_id` for rows where `is_default = true`.

This enforces **at most one** default at database level.

The service enforces **at least one when scenarios exist**.

### 10.6 Deleting current default

If the Product has no other scenarios:

- delete;
- Product now has zero scenarios and zero defaults.

If other scenarios remain:

- delete current default and atomically promote the deterministic successor:
  oldest remaining by `(created_at ASC, id ASC)`.

This keeps the invariant without leaving downstream Collection/Compare summary behavior ambiguous.

The user can explicitly set a different default afterward.

### 10.7 Why no persistent CollectionItem→scenario reference

Collection and Compare can use the Product default scenario.

Persisting a CollectionItem-level preferred-scenario FK is unnecessary for MVP and would multiply state/consistency semantics.

---

## 11. Calculation authority

### 11.1 One backend authority

All economics formulas must have one backend authority.

Recommended architecture:

- pure calculation module for deterministic formulas;
- scenario service for CRUD/orchestration/default semantics;
- APIs return normalized assumptions + derived results.

Frontend is presentation/input state only.

### 11.2 No duplicated frontend finance authority

Frontend may format values and render server results.

It must not become a second authoritative formula/rounding implementation.

If future UI uses interactive preview before save, that preview must be explicitly provisional and server response remains authoritative.

MVP does not require client-side formula duplication.

---

## 12. Formula semantics

All formulas below are scenario estimates.

### 12.1 Estimated commission per attributable order

Exact rational:

`commission_base_vnd × commission_rate_bps / 10_000`

Displayed/API monetary value:

round-half-up to whole VND.

Required inputs:

- commission base;
- commission rate.

Missing input → `null`.

### 12.2 Fixed campaign cost

`fixed_campaign_cost_vnd = sample_cost_vnd + content_cost_vnd + promotion_cost_vnd`

Calculate only when all three fields are known or explicitly zero.

Any unknown component → `null`.

### 12.3 Contribution per attributable order

Conceptually:

`commission_per_order - variable_cost_per_attributed_order`

For displayed value:

use the authoritative rounded commission/order minus variable cost.

For break-even logic, use exact rational contribution where possible to avoid an avoidable off-by-one caused by presentation rounding.

Missing required value → `null`.

### 12.4 Break-even attributable orders

Let:

`exact_contribution_numerator =
 commission_base_vnd × commission_rate_bps
 - variable_cost_per_attributed_order_vnd × 10_000`

If:

- fixed campaign cost known;
- exact contribution numerator > 0;

then:

`break_even_orders =
 ceil(fixed_campaign_cost_vnd × 10_000
      / exact_contribution_numerator)`

Otherwise:

`null`

This avoids using market sales velocity and avoids rounding the unit contribution before the break-even decision.

### 12.5 Expected scenario commission

Only when `expected_attributed_orders` is supplied.

Exact:

`commission_base_vnd × commission_rate_bps × expected_attributed_orders / 10_000`

Round once at final monetary output to whole VND.

Do not multiply a previously rounded per-order display value if exact integer/rational inputs are available.

### 12.6 Expected variable cost

`variable_cost_per_attributed_order_vnd × expected_attributed_orders`

### 12.7 Expected scenario contribution

`expected_commission
 - fixed_campaign_cost
 - expected_variable_cost`

Only when all required inputs are known.

### 12.8 Scenario return on cost

Optional transparent metric:

`expected_contribution / (fixed_campaign_cost + expected_variable_cost)`

Only if:

- expected attributed orders supplied;
- denominator known and > 0.

Return as a transparent percentage/ratio.

Do not call it guaranteed ROI.

### 12.9 Metrics explicitly prohibited

No:

- sales-velocity commission proxy;
- cumulative-sold affiliate revenue;
- inferred attributed orders;
- inferred conversion rate;
- inferred CTR;
- market-velocity payback;
- actual payout claim;
- blended “profitability score”;
- Trend Score modification.

---

## 13. Provenance and time semantics

### 13.1 User commission rate

Manual in MVP.

Stays fixed until explicit edit.

`updated_at` communicates when assumption was last changed.

No invented “stale after N days” rule.

### 13.2 Observed-price proxy

If the user chooses current Product price as the commission-base proxy:

1. copy/freeze `analysis.deltas.latest_price`;
2. validate it is present;
3. convert to the VND integer representation using the backend's defined VND normalization;
4. record `commission_base_source = observed_price_proxy`;
5. record the observation/capture timestamp.

Later Product price changes do not silently mutate the scenario.

User may explicitly refresh/rebase the scenario.

### 13.3 Existing `ProductSnapshot.commission_rate`

Do not silently copy it into the scenario.

A future user action may expose it only if later research establishes adequate provenance/context and labels it correctly.

### 13.4 History/versioning

No immutable economics history table in MVP.

To preserve alternate assumptions, user creates/duplicates another named scenario.

---

## 14. Trend Score isolation

Hard invariants:

- economics NEVER changes Trend Score;
- economics NEVER changes trend eligibility;
- economics NEVER changes evidence confidence;
- economics NEVER changes Why Trending;
- economics NEVER changes Watchlist membership;
- economics NEVER changes alert evaluation;
- economics NEVER changes crawler behavior;
- economic sorting is visually and contractually separate from trend ranking.

No opaque combined trend/economics score.

---

## 15. Collections integration

Preserve:

`Collections = decision organization`

Recommended integration:

- Collection member row may show default-scenario summary;
- scenario editor can be opened from Product/Collection context;
- Collection status remains separate;
- `CollectionItem.notes` remains decision notes, not structured finance;
- no CollectionItem scenario FK in MVP.

### Query budget

Current Collection member list:

`2 queries`

Phase 6 with batched default scenarios:

`<= 3 total queries`

Zero N+1.

---

## 16. Compare integration

Keep one existing Phase 5 transient Compare.

Add optional transparent economics columns.

Each Product uses its default scenario.

If Product has no scenario:

economics fields show unavailable.

Do not create a second Economics Compare subsystem.

Candidate fields:

- scenario name;
- assumed commission rate;
- assumed commission base;
- commission-base provenance;
- estimated commission/order;
- contribution/order;
- break-even orders;
- optional expected attributed orders;
- expected contribution;
- scenario return on cost.

### Query budgets

Verified current:

- 2 queries without Collection context;
- 3 queries with Collection context.

Add one batched default-scenario query:

- `<= 3` without Collection context;
- `<= 4` with Collection context.

Zero N+1.

No per-Product economics HTTP fanout.

---

## 17. Saved Views

Phase 5 V1 schemas are strict and frozen.

**CONFIRMED: leave Saved View V1 unchanged.**

Phase 6 MVP does not add economics keys.

If economics later becomes a dedicated list/filter workspace that genuinely needs persisted presets, research a new payload version separately.

---

## 18. Alerts

**CONFIRMED: no new economics alert types in Phase 6 MVP.**

Reasons:

- commission is manual in baseline;
- no automatic authoritative commission-change feed exists;
- scenario edits are direct user actions;
- break-even/result changes are visible immediately;
- extending Phase 3 alert semantics is not required for the core economic decision workflow.

Defer:

- commission-rate-change alerts;
- break-even crossing;
- profitability thresholds.

---

## 19. Persistence recommendation

### 19.1 Minimum new schema

One required table:

`economics_scenarios`

This is a **PROPOSED / RECOMMENDED** table.

No Phase 6 implementation currently exists.

### 19.2 No extra tables

Do not add MVP tables for:

- assumption line items;
- economics history;
- commission observations;
- formula definitions;
- calculation results.

### 19.3 Ownership and deletion

Proposed:

- Product owns many scenarios;
- deleting a scenario affects no Product/Snapshot/Watchlist/Collection/Alert data;
- Product deletion may clean scenario rows under existing repository relationship/cascade conventions.

Exact SQLAlchemy relationship syntax belongs to implementation planning, not this research artifact.

### 19.4 Uniqueness

Recommended:

`UNIQUE(product_id, name)`

Subject to current repository string/case semantics.

### 19.5 Indexes

Recommended minimum:

- index on `product_id`;
- unique partial default index on `product_id WHERE is_default`.

No index on derived metrics because derived metrics are not persisted.

### 19.6 Existing Float market observations

Do not migrate existing ProductSnapshot prices/rates merely because new financial assumptions use integers.

Market-observation storage and user-finance storage can have different representations because they serve different semantics.

---

## 20. Backup / compatibility decision

**CONFIRMED.**

If `economics_scenarios` is added as a required Base model:

`portable_backup_compatibility_version "2" → "3"`

Preserve ADR-004 policy:

- same-version restore;
- no cross-version migration;
- v2 backup rejected by v3 app;
- fresh v3 backup after successful bootstrap/upgrade;
- isolated upgrade/restore tests;
- dynamic required schema from `Base.metadata`.

No marker change is performed during research.

---

## 21. Performance constraints

No Phase 6 measured latency is claimed.

### Scenario list / Product economics

- likely <= 1 scenario query;
- no snapshot-history scan required for stored assumptions.

### Collection economics

- <= 3 SQL queries total;
- zero N+1.

### Compare economics

- <= 3 total without Collection context;
- <= 4 total with Collection context;
- zero N+1.

### Latency

Retain the established representative:

- 200 Product;
- 5,000 snapshot fixture.

Recommended regression ceiling for Phase 6 planning:

`< 200ms`

for relevant representative list/compare paths unless Project Control/QA later approves a more specific budget.

`< 50ms` may remain an optimization/research target, not a mandatory research claim.

---

## 22. Frontend recommendation

### Product Detail

Add compact Economics panel:

- scenario selector;
- Add/Edit/Duplicate/Delete;
- default marker/action;
- assumptions/provenance;
- backend-derived outputs.

### Collection row

Optional compact default-scenario summary:

- commission/order;
- contribution/order;
- break-even orders.

Avoid dense finance table.

### Compare

Optional economics columns.

### Input UX

VND-only.

Fields:

- commission %;
- assumed commission base VND;
- source;
- sample cost;
- content cost;
- promotion cost;
- variable cost/order;
- optional expected attributed orders.

### Disclosure

Display:

- `User assumption`;
- `Observed price proxy`;
- `Scenario estimate`;
- `Missing`.

Also state that actual TikTok payout can differ due to paid price, discounts, refund/settlement and commission context.

---

## 23. CSV / export

**DEFER Economics CSV from Phase 6 MVP.**

Existing export architecture can support a future scenario CSV, but economics decision support does not require export to be coherent.

Do not enlarge Phase 6 solely to add reporting.

---

## 24. Security / privacy / dependencies

### Local-first

Scenario assumptions remain local SQLite application data.

No Phase 6 MVP external API.

No financial input leaves the machine automatically.

### Backup

Economics scenarios are included in portable backup because they are application data.

### No new dependencies

Manual-first architecture uses existing stack and standard integer arithmetic.

Do not add:

- finance library;
- spreadsheet engine;
- FX library;
- TikTok API SDK;
- Decimal persistence adapter.

### Future official Affiliate API

Requires separate security/architecture review for:

- Partner/ISV approval;
- OAuth;
- access/refresh tokens;
- authorization scopes;
- revocation;
- external service failure;
- source precedence.

---

## 25. ADR-005 decision

### Decision

**ADR-005 is REQUIRED before Phase 6 implementation-plan approval.**

Do not create it in this research chat.

Project Control should authorize/draft/review ADR-005 as the next durable architecture step if it accepts this product direction.

### Recommended ADR scope

`ADR-005 — Affiliate economics assumptions, provenance, numeric semantics, and calculation authority`

It should freeze:

1. market evidence vs user assumptions vs derived economics;
2. prohibition on sold-count/sales-velocity affiliate attribution inference;
3. manual-first source strategy;
4. observed Product price only as explicit frozen proxy;
5. VND-only MVP;
6. integer VND + basis-points persisted representation;
7. backend rounding/calculation authority;
8. fixed vs variable cost semantics;
9. null ≠ zero;
10. multiple Product-scoped scenarios;
11. exactly one default when scenarios exist;
12. Trend Score/evidence/monitoring isolation;
13. compatibility `"2" → "3"`;
14. future official Affiliate API source/override precedence.

This decision is long-lived, cross-cutting and likely to be revisited when automatic platform economics becomes possible.

---

## 26. Final CONFIRMED / ADJUST / REJECT matrix

| Research item | Final status | Final conclusion |
|---|---|---|
| Manual-first strategy | **CONFIRMED** | Phase 6 MVP uses explicit user economics assumptions. |
| Product-scoped `EconomicsScenario` | **CONFIRMED** | Separate from Product market state, Watchlist and CollectionItem. |
| Multiple scenarios per Product | **CONFIRMED** | Supports organic/paid/high-rate/sample-cost contexts without spreadsheet generality. |
| Default scenario semantics | **ADJUST** | Exactly one default whenever scenarios exist; first auto-default; atomic switch; deterministic promotion on deleting default. |
| Scenario input fields | **CONFIRMED / REFINED** | Keep commission rate/base/provenance/timestamp + fixed costs + variable/order cost + optional expected attributed orders + name/timestamps/default. |
| Numeric representation | **ADJUST** | Use integer VND + integer basis points; do not copy legacy Float convention. |
| Currency | **ADJUST** | VND fixed in MVP; no generic currency field and no FX. |
| Frozen observed-price proxy | **CONFIRMED** | Explicit user-selected proxy with observation timestamp; no silent refresh. |
| Existing snapshot commission rate | **REJECT as automatic authority** | Field exists, but source/context is insufficient to make it scenario truth. |
| Fixed vs variable cost semantics | **CONFIRMED** | Sample/content/promotion are fixed; variable/order cost is separate. |
| Unknown/null semantics | **CONFIRMED** | Unknown remains null; explicit zero remains valid. |
| Derived values persisted | **REJECT** | Compute on read in backend authority. |
| Sales-velocity/sold-count attribution | **REJECT** | Market evidence cannot become affiliate earnings/orders. |
| Saved View V1 economics keys | **REJECT** | V1 remains unchanged/frozen. |
| Economics alerts | **REJECT for MVP** | No automatic source or core need. |
| Compare economics integration | **CONFIRMED** | Optional columns on existing transient Compare; default scenario per Product. |
| Collection economics summary | **CONFIRMED** | Batched default-scenario summary; no CollectionItem finance storage. |
| CollectionItem→scenario FK | **REJECT for MVP** | Default Product scenario is sufficient. |
| Economics CSV | **REJECT / DEFER** | Existing export architecture is reusable later but not needed for MVP. |
| Compatibility `2 → 3` | **CONFIRMED** | New required table under ADR-004 same-version policy. |
| ADR-005 | **CONFIRMED / REQUIRED** | Required before implementation-plan approval; not created in this research chat. |
| New third-party dependencies | **REJECT** | Existing stack + integer arithmetic is sufficient. |
| Official Affiliate API | **DEFER** | Legitimate future automatic source; requires approval/OAuth/security architecture. |
| Private Creator dashboard scraping | **REJECT** | Outside current session/security boundary. |
| VND/no FX | **CONFIRMED** | Truthful fit to repository's current observed-price semantics. |

---

## 27. Remaining risks and external assumptions

No material repository-architecture blocker remains.

Remaining risks are explicit product/data risks:

### 27.1 Durable SHA discrepancy

Project Control must correct the previously reported Phase 6 selection SHA before plan approval.

Repository truth:

`d97f00f7819e778954a76abe3605e1442ea4155d`

### 27.2 Commission assumption can become stale

User-entered rate can change on TikTok.

Mitigation:

- `updated_at`;
- clear assumption label;
- explicit user edit.

Do not invent automatic expiry.

### 27.3 Product price proxy is not actual paid commission base

Coupons/discounts/refunds/settlement can change actual commission.

Mitigation:

- explicit `observed_price_proxy` provenance;
- frozen timestamp;
- scenario-estimate disclosure.

### 27.4 Official API access remains conditional

Future automatic source requires actual Partner/Creator authorization and market availability.

Do not assume current operator has this access.

### 27.5 Existing SQLite FK-OFF debt

Phase 6 must follow the project's current persistence/integrity conventions and offline FK checks.

Do not use Phase 6 to redesign global FK behavior unless a separate bug/architecture decision requires it.

---

## 28. Recommended explicit out-of-scope

Phase 6 MVP excludes:

- automatic private Creator Center scraping;
- CAPTCHA/anti-bot bypass;
- official Affiliate API integration;
- seller-platform-fee profitability;
- tax/accounting advice;
- tax withholding calculations;
- bookkeeping;
- payout reconciliation;
- bank integrations;
- ad-platform integrations;
- automated campaign execution;
- traffic/click ingestion;
- conversion-rate inference;
- revenue attribution without attributable-order data;
- AI profit recommendations;
- generic spreadsheet/formula builder;
- generic cost-line-item accounting;
- FX engine;
- economics alerts;
- commission history ingestion;
- cross-version backup migration;
- new Trend Score formula;
- blended trend-profit score;
- multi-user financial permissions;
- cloud finance backend;
- Economics CSV/reporting expansion.

---

## 29. Planning constraints

If Project Control accepts this research, Phase 6 planning must preserve:

1. no affiliate attribution from market sold count/sales velocity;
2. economics separate from Trend Score/evidence;
3. one Product → many named scenarios;
4. exactly one default scenario whenever scenarios exist;
5. scenario assumptions persisted as integer VND/basis points;
6. VND-only MVP;
7. null is not zero;
8. fixed and variable costs separated;
9. observed Product price is only a user-selected frozen proxy;
10. existing snapshot commission rate is not automatic scenario authority;
11. derived values are calculated by one backend authority;
12. no financial formula authority duplicated in frontend;
13. break-even attributable orders is a core transparent metric;
14. expected economics requires explicit expected attributable orders;
15. no conversion-rate inference;
16. Saved View V1 unchanged;
17. no economics alert types;
18. Compare economics uses one batched default-scenario query;
19. Collection economics uses batched default-scenario lookup;
20. no N+1;
21. `portable_backup_compatibility_version "2" → "3"` if implemented;
22. no cross-version backup migration;
23. Economics CSV deferred;
24. no new third-party dependencies;
25. ADR-005 accepted before Phase 6 implementation-plan approval.

---

## 30. Product recommendation

**RECOMMEND WITH REVISED SCOPE**

Recommended Phase 6 product:

> A VND-only, manual-first Affiliate Economics Scenario workspace for Products, with multiple named scenarios, explicit commission/cost assumptions, one deterministic default, transparent provenance, backend-authoritative formulas, break-even attributable orders, and optional expected contribution.

Do not make automatic TikTok commission ingestion an MVP requirement.

Do not infer affiliate economics from market demand.

---

## 31. Project Control handoff

Return this document to:

`00 — Project Control & Roadmap`

Required Project Control actions before planning:

1. accept/reject the revised Phase 6 product direction;
2. reconcile the full-SHA discrepancy in durable state;
3. if accepted, authorize and accept ADR-005;
4. only after ADR/state reconciliation, create `PHASE_6_PLAN.md`;
5. implementation remains unauthorized until the normal lifecycle reaches that gate.

No further repository research is required for the proposed MVP unless Project Control changes the source strategy (for example, chooses official Affiliate API integration).

---

## 32. Research readiness

**RESEARCH READY FOR PROJECT CONTROL**

---

## 33. Implementation authorization

**NOT AUTHORIZED**

Do not create Phase 6 implementation code from this research document alone.
