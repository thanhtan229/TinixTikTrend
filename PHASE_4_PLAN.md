# Phase 4 Plan — Reporting & Productization

- **Phase:** Phase 4 — Reporting & Productization
- **Date:** 2026-10-05
- **Status:** **APPROVED FOR IMPLEMENTATION**
- **Reference Research:** [`research/PHASE_4_REPORTING_PRODUCTIZATION_RESEARCH.md`](research/PHASE_4_REPORTING_PRODUCTIZATION_RESEARCH.md)
- **Target Architecture:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
- **Architectural Decision Record:** [`ADR-004`](docs/architecture/ADR-004.md)

---

## 1. Executive Summary & Core Objective

Phases 1–3 established reliable data ingestion, orthogonal trend scoring, and automated alert monitoring. Phase 4 transitions TikTok Trend Hunter into a durable, operator-ready, and exportable system.

Key capabilities delivered in Phase 4:
1. **Deterministic Data Portability & Reporting:** Clean, standards-compliant CSV exports with UTF-8 BOM (`utf-8-sig`) for Excel compatibility.
   - Keyset-paginated streaming of Product Snapshot History and Alert Events using short-lived transactions and high-watermark membership freezes.
   - Authoritative Trends and Watchlist result-set exports mirroring displayed query semantics.
2. **Hot SQLite Backup Engine:** Point-in-time consistent backups via Python's native `sqlite3.Connection.backup()` API, protected by pre-publish integrity and foreign key validation.
3. **Offline Launcher-Owned Restore Lifecycle:** Resilient offline restoration with `RESTORE.bat`, atomic manifest tracking, pre-start guards, staging validation, automated pre-restore safety backups, and disaster recovery.
4. **Local Allowlisted Diagnostics:** System health, database footprint, crawl status, and session availability visibility with strict credential redaction and on-demand deep integrity checks.

---

## 2. In-Scope Scope Boundaries & Deliverables

### In-Scope Deliverables:
1. **CSV Export Engine (`backend/app/services/export_service.py` & API endpoints):**
   - Product History export (`GET /api/products/{id}/export-history`): Supported ranges `24h`, `7d`, `30d`. Rejects `all` or invalid ranges with 400. Keyset streaming `(captured_at, snapshot_id) ASC` with membership freeze (`as_of_utc`, `max_snapshot_id_at_start`).
   - Trends export (`GET /api/trends/export`): Mirrors `TrendService.get_trending_products`, exports current queried result set including filters/limits.
   - Watchlist export (`GET /api/watchlist/export`): Mirrors `WatchlistService.get_watched_products`, exports current queried result set.
   - Alert History export (`GET /api/alerts/events/export`): Keyset streaming `(created_at, event_id) DESC` with membership freeze (`max_event_id_at_start`).
   - Short-lived database sessions per batch of 1000 rows (no long-lived transaction across streaming).
   - UTF-8 BOM (`\ufeff`) on all exports.
2. **Operator Hot Backup Engine (`BACKUP.bat` & `backend/app/services/backup_service.py`):**
   - SQLite online backup via `BACKUP.bat` to `backend/.local/backups/tinix-affiliate-v1-YYYYMMDDTHHMMSS.ffffffZ.sqlite3`.
   - Excludes TikTok session artifacts (`backend/.local/tiktok-session.json`) and credentials.
   - Pre-publish validation on staging file: SQLite header, required schema tables and columns derived dynamically from SQLAlchemy model metadata, compatibility marker "1", `integrity_check`, and `foreign_key_check`.
   - Rejects file collisions and overwrites.
   - Browser backup download is deferred out of scope.
3. **Compatibility Marker:**
   - Seed `portable_backup_compatibility_version = "1"` in `system_metadata` during startup bootstrap.
   - Same-version restore only.
4. **Launcher-Owned Offline Restore (`RESTORE.bat` & `scripts/restore.ps1`):**
   - Restore manifest `backend/.local/restore/manifest.json` with terminal states: `COMPLETED`, `ROLLED_BACK`, `ABORTED`.
   - Pre-start manifest guard in `scripts/start_services.ps1` and `RESTART.bat`.
   - Pre-quiescence candidate validation (candidate file, header, integrity, FK, schema via model metadata, compatibility).
   - Service quiescence via `stop_services.ps1` (ports 8000 & 3000 freed).
   - Validated safety backup `backend/.local/backups/tinix-pre-restore-v1-YYYYMMDDTHHMMSS.ffffffZ.sqlite3` created via SQLite backup engine with pre-replacement integrity/FK verification; no overwrite.
   - Atomic database file replacement with automatic rollback on error.
   - Normal startup, reconciliation (`init_db`), alert catch-up (`AlertService.catch_up_alerts`), and health validation.
   - Recovery mode: `RESTORE.bat --recover`.
5. **System Diagnostics (`/api/diagnostics` & `/api/diagnostics/deep`):**
   - Allowlisted stats: DB file size, table row counts, scheduler next run times, crawl status, and session availability enum (`available` / `missing` / `invalid`).
   - Explicit deep integrity/FK check endpoint.
   - Strict redaction of secrets, tokens, cookies, auth headers, and filesystem paths.
6. **Frontend UI Extensions:**
   - "Xuất CSV" buttons on Trends, Watchlist, Product History, and Alert Center.
   - Disabled state with explanation for "Tất cả" in Product History.
   - System Diagnostics modal in Header with safe statistics, operator restore guidance, and manual deep check trigger (no browser backup download/create controls).
7. **Documentation & ADR:**
   - `ADR-004` created in `docs/architecture/ADR-004.md`.
   - `ARCHITECTURE.md` updated with Phase 4 invariants.
   - `README.md` updated with operator documentation.

### Explicitly Out-of-Scope (Prohibited):
- Multi-version cross-schema database migrations (Alembic or other migration tools).
- Browser-upload in-process restore or `python-multipart` dependency.
- Standalone `.exe` packaging or release installer pipelines.
- Broad TikTok discovery / anti-bot / CAPTCHA bypass.
- AI-generated summary reports or external LLM integrations.
- Cloud backup storage or external sync mechanisms.
- Enabling runtime `PRAGMA foreign_keys = ON` on normal application connections.

---

## 3. Critical Architecture Invariants

### 3.1 Historical Keyset Streaming & Membership Freeze
```
[ Request Start ]
       │
       ├─ Freeze: as_of_utc = datetime.now(timezone.utc)
       ├─ Freeze: lower_bound = as_of_utc - range_delta (24h/7d/30d)
       ├─ Freeze: max_id = SELECT MAX(id) WHERE captured_at <= as_of_utc AND captured_at >= lower_bound
       │
       ▼
[ Batch Keyset Loop ] (Batch size = 1000)
       │
       ├─ Acquire short-lived DB session
       ├─ Query: product_id == P AND captured_at >= lower_bound AND captured_at <= as_of_utc
       │         AND id <= max_id
       │         AND (captured_at, id) > (cursor_captured_at, cursor_id)
       │         ORDER BY captured_at ASC, id ASC LIMIT 1000
       ├─ Close short-lived DB session
       ├─ Yield CSV rows
       │
       └─ Repeat until batch yields < 1000 rows
```
- Higher-ID snapshots or events committed after request start are strictly excluded, even if their recorded timestamps fall within the queried time window.
- The SQLite read lock is released between batches, preventing writer starvation for background crawls.

### 3.2 Restore Lifecycle State Machine
```
[ Operator: RESTORE.bat <file> ]
       │
       ▼
 [ VALIDATING_CANDIDATE ] ──(Invalid candidate)──> [ ABORTED ] (Services never stopped)
       │
       ▼
 [ STOPPING_SERVICES ] (Ports 8000 & 3000 freed)
       │
       ▼
 [ SAFETY_BACKUP_CREATED ] (affiliate.db copied to backups/tinix-pre-restore-v1-*.sqlite3 without overwrite)
       │
       ▼
 [ REPLACEMENT_STARTED ]
       │
       ├──(Replacement failure)──> [ ROLLED_BACK ]
       │
       ▼
 [ STARTING_SERVICES & HEALTH CHECK ]
       │
       ├──(Health failure)────────> [ ROLLED_BACK ]
       │
       ▼
  [ COMPLETED ] (Terminal: Ordinary start unblocked)
```

---

## 20. Authoritative Acceptance Criteria & Verification Matrix (P4-AC-01 to P4-AC-35)

### Reporting

**P4-AC-01**
Trends CSV is generated from the authoritative Trends service using the active supported filters, sort and pagination/limit/offset parameters where applicable, and exactly matches the currently displayed/query result membership and order; it does not widen export to every matching database row.

**P4-AC-02**
Watchlist CSV is generated from the authoritative analyzed Watchlist service using the active supported filter/sort/pagination parameters, exactly matches the current displayed/query result set, introduces no per-row membership metadata query, and excludes `watched_at` / `notes` from the Phase 4 fixed MVP contract.

**P4-AC-03**
Product History export accepts exactly `24h`, `7d` and `30d`; computes the window from server request-start `as_of_utc`; includes only `captured_at >= as_of_utc - requested_range && captured_at <= as_of_utc`; orders by `(captured_at, snapshot_id)` ascending; returns structured `400` for `range=all` or any unsupported range; and the UI disables export with a bounded-window explanation while `Tất cả` is selected.

**P4-AC-04**
Alert History export uses persisted `AlertEvent` rows without rerunning alert evaluation and uses the authoritative persisted event timestamp plus `event_id` for deterministic descending history ordering.

**P4-AC-05**
Every CSV begins with exactly one UTF-8 BOM and preserves Vietnamese Unicode.

**P4-AC-06**
CSV headers and column order equal the fixed contract for each export.

**P4-AC-07**
Null fields serialize blank, real numeric zero remains `0`, timestamps are UTC and numbers are locale-independent.

**P4-AC-08**
Commas, quotes and embedded newlines round-trip through a standards-compliant CSV parser.

**P4-AC-09**
Historical exports freeze request-start membership without a long-lived SQLite read transaction: Product History captures request-start `as_of_utc`, its derived lower window bound, and immutable `max_snapshot_id_at_start`; Alert History captures immutable `max_event_id_at_start` together with its current filters. Every batch reapplies those fixed membership predicates, uses a separate short-lived read transaction/session, and traverses deterministically by ascending `(captured_at, snapshot_id)` for Product History or descending `(created_at, event_id)` for Alert History. All request-start members are emitted exactly once with no duplicates or skips, and every post-initialization insert is excluded—including a higher-ID ProductSnapshot or AlertEvent whose persisted timestamp is backdated into the initial export time/order range.

**P4-AC-10**
Export cancellation/error releases active batch DB/session resources and does not mutate application data.

### Backup / compatibility

**P4-AC-11**
Live Phase 4 bootstrap owns exactly `portable_backup_compatibility_version="1"` in `SystemMetadata`.

**P4-AC-12**
`BACKUP.bat` produces a validated backup under `backend/.local/backups/` using SQLite online backup while normal application operation may continue.

**P4-AC-13**
A backup is not published unless compatibility, required schema, `integrity_check` and `foreign_key_check` all pass.

**P4-AC-14**
Existing final backup filenames are never silently overwritten.

**P4-AC-15**
Backup failure leaves the source database unchanged and does not expose a partial file as a valid backup.

**P4-AC-16**
Portable backup contains Phase 1–3 database state but does not package or copy `backend/.local/tiktok-session.json` or other excluded runtime/session artifacts.

### Restore / recovery

**P4-AC-17**
`RESTORE.bat` accepts an explicit candidate path and, when no candidate is supplied and no incomplete transaction exists, selects only from the managed backup directory without general filesystem browsing; an existing non-terminal restore transaction always takes recovery precedence over a new candidate.

**P4-AC-18**
Non-SQLite, corrupt, schema-invalid, FK-invalid, markerless, older-version and newer-version candidates are rejected before the live DB is touched.

**P4-AC-19**
Final replacement does not begin until application-owned services are quiesced and a validated pre-restore safety backup exists.

**P4-AC-20**
Live database replacement is atomic and occurs with no application DB handles intentionally left open.

**P4-AC-21**
A successful restore restarts through normal launcher/bootstrap/reconciliation, including Phase 3 alert catch-up, and passes health plus integrity/FK verification before transitioning to `COMPLETED`.

**P4-AC-22**
A post-replacement startup/health failure causes automatic rollback to the validated safety backup and the requested restore is not reported successful.

**P4-AC-23**
Every non-terminal restore manifest blocks normal `START` / `RESTART` before backend startup; `RESTORE.bat --recover` deterministically transitions pre-replacement interruption to `ABORTED` and resolves at/after-replacement interruption to `COMPLETED` or `ROLLED_BACK` before normal startup is permitted.

**P4-AC-24**
Watchlist items, alert rules, alert events and alert cursors survive a same-version backup/restore round trip and Phase 3 catch-up remains idempotent.

### Diagnostics / UX / safety

**P4-AC-25**
Cheap diagnostics expose only the documented allowlist and do not return cookies, localStorage, raw session JSON, credentials, auth headers or arbitrary filesystem listings.

**P4-AC-26**
`integrity_check` and `foreign_key_check` run only through the explicit deep-diagnostics action, not normal UI reads/modal opening.

**P4-AC-27**
Trends, Watchlist, Product History and Alert History each provide a minimal `Xuất CSV` action with loading, visible error and safe retry/stale-response handling; Trends/Watchlist propagate current pagination membership and Product History disables export for `Tất cả`.

**P4-AC-28**
Browser UI does not implement database restore upload; restore UX is instructions/status only.

**P4-AC-29**
Runtime connection-level FK enforcement is unchanged by Phase 4.

**P4-AC-30**
Existing Phase 2/3 normal read paths show no material regression under the existing representative fixture, with measurements recorded rather than inferred.

### Repository validation

**P4-AC-31**
Full backend pytest suite `PASS`. Existing known warnings may be documented separately. Any backend test failure makes this criterion `FAIL` unless Project Control explicitly revises the accepted plan.

**P4-AC-32**
Full frontend Vitest suite, TypeScript typecheck and lint pass.

**P4-AC-33**
Next.js production build and standard healthcheck pass.

**P4-AC-34**
Required isolated backup/restore/recovery and ID-high-watermark historical-streaming validation passes without destructive access to the real `backend/affiliate.db`.

**P4-AC-35**
Documentation covers the supported operator workflow and explicitly documents bounded Product History export, current-result export membership, request-start high-watermark historical membership, same-version restore, manifest recovery guard, session exclusion, deferred browser restore and deferred packaging.

---

### Authoritative Acceptance Criteria Summary Table

| AC Code | Domain | Summary Meaning | Verification Method |
|:---|:---|:---|:---|
| **P4-AC-01** | Reporting | Trends CSV current-result parity & ordering (no widening to all DB rows) | Query parity & API test |
| **P4-AC-02** | Reporting | Watchlist CSV current-result parity (no extra per-row metadata queries) | Query parity & query count |
| **P4-AC-03** | Reporting | Product History bounded export (`24h`, `7d`, `30d`; `range=all` returns 400; UI disabled) | API functional & UI tests |
| **P4-AC-04** | Reporting | Alert History export uses persisted `AlertEvent` rows in deterministic descending order | API integration test |
| **P4-AC-05** | Reporting | Every CSV begins with exactly one UTF-8 BOM and preserves Vietnamese Unicode | CSV byte & encoding test |
| **P4-AC-06** | Reporting | Fixed CSV headers and column order across all four exports | CSV header verification |
| **P4-AC-07** | Reporting | Null blank, real numeric zero `0`, UTC timestamps, locale-independent numbers | Field serialization test |
| **P4-AC-08** | Reporting | RFC 4180 commas, quotes, newlines round-trip | CSV RFC 4180 round-trip |
| **P4-AC-09** | Reporting | Historical export request-start membership freeze & high-watermark exclusion | Concurrency & backdate test |
| **P4-AC-10** | Reporting | Export cancellation/error releases batch DB/session resources without data mutation | Resource cleanup test |
| **P4-AC-11** | Backup/compat | Live Phase 4 bootstrap owns `portable_backup_compatibility_version="1"` in `SystemMetadata` | Bootstrap & marker test |
| **P4-AC-12** | Backup/compat | `BACKUP.bat` produces validated backup under `backend/.local/backups/` via SQLite online backup | File-backed backup test |
| **P4-AC-13** | Backup/compat | Backup not published unless compatibility, schema, integrity, and FK checks pass | Pre-publish validator test |
| **P4-AC-14** | Backup/compat | Existing final backup filenames are never silently overwritten | Collision rejection test |
| **P4-AC-15** | Backup/compat | Backup failure leaves source DB unchanged and does not expose partial file | Failure atomicity test |
| **P4-AC-16** | Backup/compat | Portable backup contains Phase 1–3 DB state, excludes `tiktok-session.json` & runtime | Security boundary test |
| **P4-AC-17** | Restore/recov | `RESTORE.bat` candidate selection & recovery precedence over new candidate | Candidate selection test |
| **P4-AC-18** | Restore/recov | Non-SQLite, corrupt, schema/FK invalid, markerless/version mismatch rejected before DB touched | Staging validator test |
| **P4-AC-19** | Restore/recov | Final replacement requires quiesced services and validated safety backup | Pre-replacement guard test |
| **P4-AC-20** | Restore/recov | Live database replacement is atomic with no application handles open | Atomic swap test |
| **P4-AC-21** | Restore/recov | Successful restore restarts via normal launcher/reconciliation/catch-up, passes health & integrity | End-to-end restore test |
| **P4-AC-22** | Restore/recov | Post-replacement failure causes automatic rollback to validated safety backup | Rollback injection test |
| **P4-AC-23** | Restore/recov | Non-terminal manifest blocks START/RESTART; `RESTORE.bat --recover` resolves to terminal | Manifest & recovery test |
| **P4-AC-24** | Restore/recov | Watchlist/rules/events/cursors survive same-version restore; alert catch-up idempotent | State preservation test |
| **P4-AC-25** | Diag/UX/safety | Cheap diagnostics expose allowlist only; strictly no cookies/tokens/credentials/paths | Diagnostics redaction test |
| **P4-AC-26** | Diag/UX/safety | `integrity_check` and `foreign_key_check` run only via explicit deep-diagnostics action | Deep diagnostics test |
| **P4-AC-27** | Diag/UX/safety | Minimal `Xuất CSV` action with loading/error/retry across all 4 surfaces; `Tất cả` disabled | Frontend Vitest & manual QA |
| **P4-AC-28** | Diag/UX/safety | Browser UI does not implement database restore upload; instructions/status only | UI security boundary test |
| **P4-AC-29** | Diag/UX/safety | Runtime connection-level FK enforcement unchanged by Phase 4 (`PRAGMA foreign_keys = 0`) | Pragma verification test |
| **P4-AC-30** | Diag/UX/safety | Existing Phase 2/3 read paths show no material regression under representative fixture | Performance benchmark |
| **P4-AC-31** | Validation | Full backend pytest suite PASS | Pytest execution |
| **P4-AC-32** | Validation | Full frontend Vitest suite, TypeScript typecheck, and lint pass | Vitest, tsc, lint execution |
| **P4-AC-33** | Validation | Next.js production build and standard healthcheck pass | Build & healthcheck |
| **P4-AC-34** | Validation | Required isolated backup/restore/recovery & historical streaming pass without touching real DB | Isolated harness test |
| **P4-AC-35** | Validation | Documentation covers supported operator workflow and required architecture invariants | Documentation review |

