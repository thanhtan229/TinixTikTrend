# Phase 3 Plan — Monitoring, Watchlists & Alerts

- **Phase:** Phase 3 — Monitoring, Watchlists & Alerts
- **Date:** 2026-10-05
- **Status:** **APPROVED FOR IMPLEMENTATION**
- **Reference Research:** [`research/PHASE_3_MONITORING_WATCHLISTS_ALERTS_RESEARCH.md`](research/PHASE_3_MONITORING_WATCHLISTS_ALERTS_RESEARCH.md)
- **Target Architecture:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
- **Architectural Decision Record:** [`ADR-003`](docs/architecture/ADR-003.md)

---

## 1. Executive Summary & Core Objective

Phase 1 established multi-product ingestion, resilient crawling, SQLite snapshot persistence, and restart recovery. Phase 2 established orthogonal trend evidence/confidence, deterministic scoring and reasons, zero N+1 query performance, and user-facing filtering/sorting.

Phase 3 shifts the platform from passive point-in-time exploration to active operational surveillance. It provides:
1. **Curated Watchlist:** An implicit/default personal watchlist backed by durable membership, separating focused surveillance from global market intelligence while preserving historical Product, Snapshot, Rule, and Event data upon watch/unwatch.
2. **One-Time Migration/Backfill:** Idempotent, retry-safe migration of the legacy tracked universe with a durable completion marker that prevents automatic repopulation on future restarts.
3. **Scheduled Refresh Source:** Watchlist membership becomes the authoritative source for periodic scheduled crawls, and valid user-submitted PDPs are automatically added to the watchlist.
4. **Three Product-Scoped Alert Rule Types:**
   - `sales_velocity_above` (momentum threshold)
   - `trend_score_above` (score threshold)
   - `price_change_pct` (relative price threshold with strict direction `up` | `down` | `either`)
5. **Decoupled Post-Commit Evaluation:** Product snapshots commit first; alert evaluation runs in an isolated post-commit transaction so alert failures never compromise ingestion.
6. **Deterministic Replay, Cursors & State:** Durable monotonic cursors (`last_evaluated_snapshot_id`), condition states (`last_condition_met`), cooldown tracking (`last_triggered_at`), and composite uniqueness `UNIQUE(rule_id, triggering_snapshot_id)` guarantee zero duplicate alert events.
7. **Startup Catch-Up Lifecycle:** Interrupted crawls are reconciled, lagging alert rules are caught up synchronously before background scheduler jobs start and before the HTTP server becomes ready.
8. **Deterministic As-Of Analytics Reuse:** Historical replay evaluates Phase 2 analytics strictly as-of the triggering snapshot, bounded to $172\text{h}$, without mutating Phase 2 formulas or creating alert-specific scores.

---

## 2. In-Scope Scope Boundaries & Deliverables

### In-Scope Deliverables:
1. **Watchlist Domain:**
   - Single implicit/default Watchlist backed by durable `WatchlistItem` table (`product_id`, `created_at`, `notes`).
   - One-time migration/backfill of legacy tracked products (`url IS NOT NULL` and not quarantined) using durable completion marker in `SystemMetadata`.
   - Watch / Unwatch API and UI actions; removing a product from watchlist preserves all Product, Snapshot, Rule, and Event history.
   - Watchlist membership drives scheduled crawler refresh.
   - Successful user-submitted valid PDP automatically watched.
2. **Alert Rules Domain:**
   - Exactly three product-scoped rule types: `sales_velocity_above`, `trend_score_above`, `price_change_pct`.
   - Durable `AlertRule` entity (`product_id`, `rule_type`, `threshold`, `direction`, `cooldown_minutes`, `is_enabled`, `last_evaluated_snapshot_id`, `last_condition_met`, `last_triggered_at`).
   - Direction validation: `direction` must be `up`, `down`, or `either` for `price_change_pct`; direction must be rejected for non-price rules.
   - Strict positive finite threshold validation (`threshold > 0`).
   - Price calculation: `pct_change = (current_price - previous_price) / previous_price * 100` where both prices are strictly positive and non-null.
   - Emitted event persists actual movement direction (`up` / `down`) for deterministic explanation.
   - Price alerts are never described as "trending".
   - Cooldown semantics: Default 0 minutes. Suppress only when `trigger_time - last_triggered_at < cooldown_duration`. Exact boundary is eligible. Suppressed crossing advances condition state to met. Cooldown expiry alone never creates an event.
   - Baseline initialization: No retroactive alerts on rule creation, modification, or re-enable.
3. **Alert Events Domain:**
   - Durable `AlertEvent` entity (`rule_id`, `product_id`, `triggering_snapshot_id`, `rule_type`, `threshold`, `actual_value`, `actual_direction`, `message`, `is_read`, `created_at`).
   - Database constraint `UNIQUE(rule_id, triggering_snapshot_id)`.
   - Durable unread badge counter, mark single read, mark all read.
4. **Execution & Lifecycle Domain:**
   - Ingestion commits snapshot first; post-commit alert evaluator runs in separate transaction.
   - Ingestion never rolled back by alert evaluation failure; failed alert transaction leaves cursor behind.
   - Event creation and cursor/state advancement are atomic.
   - Synchronous startup sequence: `schema/bootstrap/backfill → crawl reconciliation → alert catch-up → scheduler start → application ready`.
   - Catch-up failure halts startup/scheduler to avoid replay gap.
5. **Analytics Reuse:**
   - Reuse Phase 2 `calculate_product_deltas`, `calculate_trend_score`, and evidence gating without formula alterations.
   - Bounded snapshot window ($S_k.\text{captured\_at} - 172\text{h}$ to $S_k.\text{captured\_at}$) with `current_time = S_k.captured_at`.
   - Single analytics evaluation per product/snapshot shared across all active rules.
6. **Frontend Extensions:**
   - Watchlist tab on main dashboard.
   - Star watch/unwatch toggle on ProductCard and Product Detail.
   - Alert configuration modal on Product Detail.
   - Alert center bell icon with unread badge counter in header and drawer/modal.
7. **Documentation & Architecture:**
   - `ADR-003` created in `docs/architecture/ADR-003.md`.
   - `ARCHITECTURE.md` updated with Phase 3 invariants.

### Explicitly Out-of-Scope (Prohibited):
- Named or multiple watchlists.
- Global / cross-product alert rules.
- Generalized AND/OR rule expressions or arbitrary DSL.
- Review-delta or raw-sales-delta alert rules.
- Trend-state or confidence-transition alert rules.
- External notification channels (email, Telegram, Discord, webhooks, push, SMS, OS toasts).
- LLM / generative alert summaries or predictive AI.
- Redis, message queues (RabbitMQ, Kafka), Celery, or distributed workers.
- Broad home/category crawl discovery bypass.

---

## 3. Ingestion-Alert Decoupling Architecture

```
[ TikTok Shop Crawler ]
         │
         ▼
[ Extract & Validate PDP ]
         │
         ▼
[ Upsert Product & Create Snapshot ]
         │
         ▼
[ Commit Ingestion Transaction ] (Product & ProductSnapshot durable in SQLite)
         │
         ├─────────────────────────────────────────────────┐
         ▼ (Post-commit Hook)                              │
[ Post-Commit Alert Evaluator ]                            │
  - Fetch active rules for product                         │
  - Slice snapshots <= current snapshot (bounded 172h)     │
  - Calculate deterministic As-Of analytics once           │
  - Evaluate edge crossing & cooldown                      │
  - Prepare AlertEvent & advance AlertRule cursor/state    │
         │                                                 │
         ▼                                                 │
[ Separate Alert Transaction ]                             │
  - Commit (AlertEvent + Cursor Update ATOMIC)             │
  - On Failure: Rollback Alert Transaction ONLY            │ (Snapshot remains intact!)
         │                                                 │
         ▼                                                 │
[ If User-Submitted PDP & Valid ] ─────────────────────────┘
  - Ensure Product in Watchlist
```

---

## 4. Data Models & Schema Design

### 4.1 `watchlists` / `watchlist_items`
```python
class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    product = relationship("Product", backref="watchlist_item")
```

### 4.2 `system_metadata`
```python
class SystemMetadata(Base):
    __tablename__ = "system_metadata"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
```

### 4.3 `alert_rules`
```python
class AlertRule(Base):
    __tablename__ = "alert_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False) # sales_velocity_above, trend_score_above, price_change_pct
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # up, down, either (price only)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_evaluated_snapshot_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_condition_met: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    product = relationship("Product", backref="alert_rules")
    __table_args__ = (
        Index("ix_alert_rules_product_active", "product_id", "is_enabled"),
    )
```

### 4.4 `alert_events`
```python
class AlertEvent(Base):
    __tablename__ = "alert_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    triggering_snapshot_id: Mapped[int] = mapped_column(Integer, ForeignKey("product_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_direction: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # up / down
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    rule = relationship("AlertRule", backref="events")
    product = relationship("Product", backref="alert_events")
    triggering_snapshot = relationship("ProductSnapshot")

    __table_args__ = (
        UniqueConstraint("rule_id", "triggering_snapshot_id", name="uq_alert_events_rule_snapshot"),
        Index("ix_alert_events_unread_created", "is_read", "created_at"),
        Index("ix_alert_events_product_created", "product_id", "created_at"),
    )
```

---

## 5. Legacy Tracked Universe Migration & Durable Bootstrap Marker

1. During `init_db(db)`:
   - Check if `SystemMetadata(key="legacy_tracked_backfill_completed")` exists.
   - If not found:
     - Query all unquarantined products with `Product.url IS NOT NULL`.
     - Insert each into `WatchlistItem(product_id=p.id, notes="Legacy tracked backfill")`.
     - Insert `SystemMetadata(key="legacy_tracked_backfill_completed", value="true")`.
     - Commit the transaction.
   - If found:
     - Skip backfill completely. Do NOT inspect row count of `WatchlistItem`. An empty watchlist is preserved.
   - If any exception occurs before commit, the entire transaction rolls back; the marker is not saved, allowing safe retry on next boot.

---

## 6. Post-Commit Evaluation, Atomic Transactions & Durable Cursors

1. **Isolation Guarantee:**
   - In `CrawlService._upsert_product_and_snapshot`, the snapshot is committed via `self.db.commit()`.
   - Alert evaluation is called in an isolated block:
     ```python
     try:
         alert_service = AlertService(self.db)
         alert_service.evaluate_snapshot(product_id=product.id, snapshot_id=snapshot.id)
     except Exception as exc:
         self.db.rollback() # rolls back only alert changes
         logger.error(f"Post-commit alert evaluation failed: {exc}")
     ```
2. **Atomicity Guarantee:**
   - When evaluating rule $R$ on snapshot $S_k$:
     - If triggered: `db.add(AlertEvent(...))` and update `R.last_evaluated_snapshot_id = S_k.id`, `R.last_condition_met = True`, `R.last_triggered_at = S_k.captured_at`.
     - If not triggered / suppressed: update `R.last_evaluated_snapshot_id = S_k.id`, `R.last_condition_met = condition_met`.
     - Both event insert and rule state updates commit together in `db.commit()`.
3. **Idempotency Guarantee:**
   - SQLite enforces `UNIQUE(rule_id, triggering_snapshot_id)`.
   - If a retry attempts to insert a duplicate event, it is rejected by SQLite integrity constraints.

---

## 7. Alert Rule Semantics

### 7.1 Sales Velocity Above (`sales_velocity_above`)
- Evaluates Phase 2 calculated `sales_velocity_24h`.
- Gating: Must have measured/eligible signal; if velocity is null or product has insufficient signal, condition is FALSE.
- Condition met: `sales_velocity_24h >= threshold`.

### 7.2 Trend Score Above (`trend_score_above`)
- Evaluates Phase 2 calculated `trend_score`.
- Gating: Must be eligible (`ranking_state == "eligible"`); if stale or insufficient signal, condition is FALSE.
- Condition met: `trend_score >= threshold`.

### 7.3 Price Change Percentage (`price_change_pct`)
- Requires `direction` in `{"up", "down", "either"}`.
- Threshold must be finite and `> 0`.
- Requires current price $P_{curr} > 0$ and previous price $P_{prev} > 0$.
- $P_{prev}$ is the price from the chronologically preceding snapshot.
- Compute: $\text{pct\_change} = \frac{P_{curr} - P_{prev}}{P_{prev}} \times 100$.
- Evaluate:
  - `up`: $\text{pct\_change} \ge \text{threshold}$
  - `down`: $-\text{pct\_change} \ge \text{threshold}$
  - `either`: $|\text{pct\_change}| \ge \text{threshold}$
- Actual movement direction: `'up'` if $\text{pct\_change} \ge 0$ else `'down'`. Persisted in `AlertEvent.actual_direction`.
- Message format: "Giá [tăng/giảm] X% (từ Y đ thành Z đ)". Never described as "trending".

### 7.4 Cooldown & Edge Triggering
- Transition requirement: An alert only fires on a FALSE $\rightarrow$ TRUE condition crossing (`not rule.last_condition_met and condition_met`).
- Cooldown check:
  - If `cooldown_duration == 0`: Always eligible.
  - If `cooldown_duration > 0`: Suppress ONLY when `trigger_time - last_triggered_at < cooldown_duration`.
  - Boundary: Before boundary $\rightarrow$ suppress; exact boundary $\rightarrow$ eligible; after boundary $\rightarrow$ eligible.
  - Suppressed crossing still advances `rule.last_condition_met = True`.
  - Cooldown expiry alone never creates a delayed event.

### 7.5 No Retroactive Baseline Alerts
- When a rule is created, edited, or re-enabled:
  - Initialize `last_evaluated_snapshot_id = latest_snapshot.id`.
  - Initialize `last_condition_met = condition_met_on_latest_snapshot`.
  - Do NOT emit any alert events during rule creation or edit.

---

## 8. Startup Lifecycle & Deterministic Replay Catch-Up

Sequence in `lifespan`:
```
1. init_db()
   - Base.metadata.create_all()
   - Quarantine legacy rows
   - Backfill legacy tracked products to WatchlistItem (one-time)
   - Reconcile abandoned CrawlRun (running -> partial/failed)
   - Seed categories
   - db.commit()
2. catch_up_alerts()
   - Find all enabled AlertRules where last_evaluated_snapshot_id < max(snapshot_id) for product
   - Replay pending snapshots in chronological order
   - Commit events and advance cursors atomically
   - If catch_up_alerts fails -> RAISE and abort startup!
3. start_scheduler()
   - Activate cron triggers for scheduled refresh
4. yield
   - Application ready for HTTP traffic
```

---

## 9. Deterministic As-Of Analytics Reuse

To evaluate snapshot $S_k$:
- Query snapshots for $product\_id$ where $captured\_at \le S_k.captured\_at$ and $captured\_at \ge S_k.captured\_at - 172\text{h}$, ordered ascending by $captured\_at$.
- Call `calculate_product_deltas(snapshots, current_time=S_k.captured_at)`.
- Call `calculate_trend_score(deltas, first_seen_at=product.first_seen_at, current_time=S_k.captured_at)`.
- Call `calculate_trend_evidence(snapshots, deltas, current_time=S_k.captured_at)`.
- Evaluate all active rules for that product against this single analytics result.

---

## 10. API Design & Contracts

### Watchlist Router (`/api/watchlist`)
- `GET /api/watchlist`: List watched products with analytics (supports category, sort, pagination).
- `POST /api/watchlist/{product_id}`: Add product to watchlist. Returns `{"is_watched": true, "product_id": id}`.
- `DELETE /api/watchlist/{product_id}`: Remove product from watchlist. Preserves all history. Returns `{"is_watched": false, "product_id": id}`.
- `GET /api/watchlist/{product_id}/status`: Returns `{"is_watched": bool}`.

### Alerts Router (`/api/alerts`)
- `GET /api/alerts/rules`: Query rules by `product_id`.
- `POST /api/alerts/rules`: Create rule (`product_id`, `rule_type`, `threshold`, `direction`, `cooldown_minutes`).
- `GET /api/alerts/rules/{rule_id}`: Get single rule.
- `PATCH /api/alerts/rules/{rule_id}`: Update threshold, cooldown, or toggle `is_enabled`.
- `DELETE /api/alerts/rules/{rule_id}`: Delete rule.
- `GET /api/alerts/events`: Paginated alerts history (`is_read`, `product_id`, `limit`, `skip`).
- `GET /api/alerts/unread-count`: Returns `{"unread_count": int}`.
- `PATCH /api/alerts/events/{event_id}/read`: Mark event as read.
- `POST /api/alerts/events/mark-all-read`: Mark all events as read.

---

## 11. Minimal UI Extensions

1. **Dashboard Watchlist Tab:** Main tab navigation adds `"watchlist"` option. Shows watched products grid.
2. **Watch / Unwatch Star Toggle:**
   - On `ProductCard`: Quick star icon toggle in header badge area.
   - On Product Detail: Prominent star button `[⭐ Theo dõi] / [★ Đang theo dõi]` in action header.
3. **Alert Setup Modal:** On Product Detail page, button `[🔔 Cài đặt cảnh báo]` opens modal to manage rules for that product.
4. **Notification Center:** Header bell icon `[🔔]` with counter badge (`bg-rose-500 text-white`). Clicking opens dropdown/drawer showing recent unread alert events, with action to mark read or view product.

---

## 12. Architectural Decision Record & Durable Updates

- Create `docs/architecture/ADR-003.md`:
  Records post-commit alert evaluation, durable cursors, edge crossing, zero retroactive baseline alerts, single default watchlist, and rejection of queues/Redis.
- Update `ARCHITECTURE.md`:
  Add Phase 3 invariants section.

---

## 13. Phase 3 Verification Matrix & Completion Criteria

| # | Acceptance Criterion | Verification Method | Expected Result |
|---|----------------------|---------------------|:---------------:|
| 1 | One implicit/default Watchlist backed by durable membership | Unit tests in `test_watchlist.py` | PASS |
| 2 | One-time migration/backfill of legacy tracked universe with durable marker | Restart test with empty watchlist | PASS |
| 3 | Watch / Unwatch preserves historical data | File-backed restart test | PASS |
| 4 | Watchlist membership becomes scheduled-refresh source | Unit test in `test_crawler.py` | PASS |
| 5 | User-submitted valid PDP becomes watched automatically | Crawl integration test | PASS |
| 6 | Exactly 3 rule types supported (`sales_velocity_above`, `trend_score_above`, `price_change_pct`) | Schema validation test | PASS |
| 7 | Price rule direction validation (`up`, `down`, `either`) & rejection for others | Rule creation API test | PASS |
| 8 | Price rule movement direction persistence & deterministic explanation (no "trending") | Event emission test | PASS |
| 9 | Cooldown semantics: exact boundary eligible, before suppressed, suppressed advances state | Cooldown unit test | PASS |
| 10 | Post-commit evaluation in separate transaction; failure never rolls back snapshot | Failure injection test | PASS |
| 11 | DB uniqueness on `(rule_id, triggering_snapshot_id)` prevents duplicates | Integrity test | PASS |
| 12 | Zero retroactive baseline alerts on create/edit/re-enable | Baseline initialization test | PASS |
| 13 | Synchronous startup order; catch-up failure halts scheduler/readiness | Lifespan test | PASS |
| 14 | Deterministic As-Of Phase 2 analytics reuse bounded to 172h | Replay determinism test | PASS |
| 15 | Minimal Watchlist & Alerts frontend components & Vitest suites | Vitest test suites | PASS |
| 16 | Zero N+1 query regression & sub-200ms latency on 200-product dataset | Benchmark validation | PASS |
| 17 | Full validation clean (pytest, Vitest, tsc, lint, build, healthcheck) | Automated verification suite | PASS |
| 18 | ADR-003 and ARCHITECTURE.md updated | Inspection | PASS |
