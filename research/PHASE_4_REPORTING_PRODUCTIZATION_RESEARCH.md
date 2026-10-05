# Research — Phase 4: Reporting & Productization

**Date:** 2026-10-05  
**Role:** `01 — Architecture & Repo Research`  
**Status:** **RESEARCH COMPLETED & FULLY RECONCILED AGAINST SOURCE VERIFICATION**  
**Phase Target:** `Phase 4 — Reporting & Productization`  
**Classification:** **`RESEARCH READY FOR PHASE PLANNING`**

---

## Executive Summary

Phase 1 established verified multi-product ingestion, resilient Playwright crawling, SQLite snapshot persistence, and restart recovery. Phase 2 established orthogonal trend evidence/confidence, deterministic scoring and reasons, zero N+1 query performance, and user-facing filtering/sorting. Phase 3 delivered curated watchlists, deterministic alert rules, deduplicated alert events, and startup catch-up reconciliation.

Phase 4 addresses the transition from an interactive operational tool into a **durable, exportable, and operator-ready system**. Users scouting high-velocity TikTok Shop affiliate products require:
1. **Deterministic Data Portability & Reporting:** Clean, standards-compliant CSV exports of market trends, curated watchlists, chronological product price/velocity snapshots, and historical alert events for offline analysis, spreadsheet modeling, and cross-tool sharing.
2. **Reliable Local Backup & Recovery:** Point-in-time snapshotting of the complete application state, safe offline restoration without data corruption or Windows file-locking failures, and verified safety fallbacks.
3. **Transparent System Diagnostics:** Clear operational visibility into background scheduler cadence, database footprint, crawl status, and storage integrity without exposing private tokens or system credentials.
4. **Pragmatic Onboarding & Documentation:** Clear, maintainable guidance for operators running the system locally.

Following the completion of repository source verification (`SOURCE VERIFICATION PASS`), this document resolves all prior source-access assumptions with exact repository paths, symbols, runtime facts, and engineering constraints. It establishes the smallest coherent Phase 4 MVP, classifies repository risks (including SQLite foreign key enforcement), clarifies prior terminology, and defines the prerequisite architecture decisions for Phase 4 planning.

---

## 1. Verified Repository Evidence & Source Reality

Exhaustive repository inspection of the local checkout confirms the following concrete facts across all architectural dimensions:

### 1.1 Database Ownership, Location, Engine & Connection Model
- **Configuration & Constant:** Defined in [`backend/app/core/config.py:17`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/core/config.py#L17) as `database_url: str = "sqlite:///./affiliate.db"`. Overridable via `.env` / `../.env` through `pydantic_settings.BaseSettings` ([`backend/app/core/config.py:32-37`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/core/config.py#L32-L37)).
- **Authoritative SQLite File Path:** Resolves deterministically to `backend/affiliate.db` under the project root (`d:\___TOOLS\__TINIX\02-Tinix-Tiktok Trend Hunter\backend\affiliate.db`). In service execution scripts ([`scripts/start_services.ps1:24,43`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/scripts/start_services.ps1#L24-L43)), WMI launches Uvicorn with `CurrentDirectory = <projectRoot>\backend`, making `./affiliate.db` authoritative.
- **Engine & Session Factory:** Configured in [`backend/app/db/session.py:7-22`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/db/session.py#L7-L22):
  ```python
  engine = create_engine(
      settings.database_url,
      connect_args={"check_same_thread": False},
      echo=False,
  )
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  ```
  FastAPI route dependencies acquire sessions via `get_db()` ([`backend/app/db/session.py:24-32`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/db/session.py#L24-L32)), releasing connections cleanly in a `finally` block.
- **Connection Pool & Observed Pragmas:**
  - SQLAlchemy uses its default `QueuePool` for file-backed SQLite URLs (`size=5, max_overflow=10, timeout=30.0`).
  - Active runtime pragmas verified on `backend/affiliate.db`:
    - `PRAGMA journal_mode;` = `delete` (standard rollback journal; WAL is not enabled).
    - `PRAGMA synchronous;` = `2` (`FULL`).
    - `PRAGMA busy_timeout;` = `5000` (5.0s).
    - `PRAGMA foreign_keys;` = `0` (`OFF` by default on standard SQLite connections; no event listener sets it to `ON`).

### 1.2 Bootstrap, Metadata & Version Compatibility
- **Bootstrap Lifecycle:** Located in [`backend/app/db/init_db.py:21-85`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/db/init_db.py#L21-L85). Runs idempotently on application startup: calls `Base.metadata.create_all()`, quarantines legacy contaminated records, executes one-time legacy watchlist backfill if uncompleted, reconciles interrupted crawl runs (`running` $\to$ `partial`/`failed`), and seeds default categories.
- **`SystemMetadata` Structure:** Defined in [`backend/app/models/system_metadata.py:12-21`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/models/system_metadata.py#L12-L21) with fields:
  - `key: Mapped[str] = mapped_column(String(100), primary_key=True)`
  - `value: Mapped[str] = mapped_column(String(255), nullable=False)`
  - `created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)`
  Live database currently contains: `('legacy_tracked_backfill_completed', 'true', ...)` ([`backend/app/db/init_db.py:44-62`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/db/init_db.py#L44-L62)).
- **Suitability for Backup Compatibility Marker:** `SystemMetadata` is fully capable of storing compatibility version markers (e.g., `backup_compatibility_version = "1.0.0"`) without requiring any schema migrations or new tables.
- **Absence of Migration Framework:** There is no Alembic or database migration tool installed in `backend/requirements.txt`. Therefore, multi-version cross-schema migrations cannot be automated in Phase 4. **Phase 4 MVP must enforce same-version restore compatibility.**

### 1.3 Persistent-Data Boundary & Session Isolation
- **10 Authoritative SQLite Tables:**
  1. `products` ([`backend/app/models/product.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/models/product.py))
  2. `product_snapshots` ([`backend/app/models/product_snapshot.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/models/product_snapshot.py))
  3. `crawl_runs` ([`backend/app/models/crawl_run.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/models/crawl_run.py))
  4. `categories` ([`backend/app/models/category.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/models/category.py))
  5. `product_video_links` ([`backend/app/models/product_video_link.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/models/product_video_link.py))
  6. `quarantined_products` ([`backend/app/models/quarantine.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/models/quarantine.py))
  7. `watchlist_items` ([`backend/app/models/watchlist.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/models/watchlist.py))
  8. `system_metadata` ([`backend/app/models/system_metadata.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/models/system_metadata.py))
  9. `alert_rules` ([`backend/app/models/alert_rule.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/models/alert_rule.py))
  10. `alert_events` ([`backend/app/models/alert_event.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/models/alert_event.py))
  Together, these 10 tables hold 100% of the portable application and user state.
- **TikTok Local Session Boundary:**
  - Stored exclusively in `backend/.local/tiktok-session.json` ([`backend/app/collectors/tiktok_shop/session.py:13`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/collectors/tiktok_shop/session.py#L13)).
  - Ignored in `.gitignore:61` (`backend/.local/`).
  - Contains ephemeral, host-bound browser authentication cookies, session headers, and localStorage tokens.
  - **Invariant:** TikTok session state must remain strictly outside the portable database backup boundary to prevent credential leakage and cross-workstation session corruption.

### 1.4 Export & Query Seams
- **Current Export Capability:** Zero CSV/export/report implementations currently exist in the codebase. All occurrences of `export` are TypeScript module exports.
- **Authoritative Query Seams to Reuse:**
  1. **Trends Export:** [`TrendService.get_trending_products(...)`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/services/trend_service.py#L17-L106) (`backend/app/services/trend_service.py`). Encapsulates category filtering, confidence scoring, evidence requirements, and deterministic multi-tier sorting with nulls-last and stable `product_id` tie-breaking.
  2. **Watchlist Export:** [`WatchlistService.get_watched_products(...)`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/services/watchlist_service.py#L50-L155) (`backend/app/services/watchlist_service.py`). Preserves identical scoring, filtering, and sorting invariants for watched items.
  3. **Product History Export:** Raw `ProductSnapshot` records ordered by `captured_at ASC` ([`backend/app/models/product_snapshot.py:30-58`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/models/product_snapshot.py#L30-L58)). Preserves exact recorded metrics without fabrication or zero-coercion.
  4. **Alert History Export:** Querying `AlertEvent` with eager-loaded `product` title/URL via `joinedload(AlertEvent.product)` ordered by `AlertEvent.created_at.desc(), AlertEvent.id.desc()` ([`backend/app/models/alert_event.py:16-51`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/models/alert_event.py#L16-L51)). Historical actual values and directions remain immutable.

### 1.5 Process Lifecycles & Windows File Locking
- **Windows File Locking (`WinError 32`):** In Python on Windows, opening a SQLite database file locks the file handle. Because SQLAlchemy's `QueuePool` maintains active connection handles in worker threads, attempting in-process file replacement (`shutil.copyfile` or `os.replace` targeting `affiliate.db`) will fail immediately with `WinError 32: The process cannot access the file because it is being used by another process`.
- **Existing Process Lifecycle Tooling:**
  - Launch scripts [`start.bat`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/start.bat) and [`RESTART.bat`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/RESTART.bat) rely on [`scripts/start_services.ps1`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/scripts/start_services.ps1).
  - Stop scripts [`stop.bat`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/stop.bat) rely on [`scripts/stop_services.ps1`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/scripts/stop_services.ps1).
  - Process ownership and port cleanup are managed via [`scripts/service_common.ps1`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/scripts/service_common.ps1) with PID tracking in `logs/backend.pid.json` and `logs/frontend.pid.json`.
- **Offline Maintenance Restore:** The launcher scripts can host an offline restore command (`RESTORE.bat` / PowerShell helper) that stops services, validates the candidate SQLite file, creates a safety backup, swaps the file, and restarts services. This requires zero redesign of process ownership.

### 1.6 Missing FastAPI Multipart Dependency
- Inspection of `backend/requirements.txt` reveals:
  ```text
  fastapi>=0.110.0
  uvicorn[standard]>=0.28.0
  pydantic>=2.6.0
  pydantic-settings>=2.2.0
  sqlalchemy>=2.0.28
  httpx>=0.27.0
  playwright>=1.42.0
  apscheduler>=3.10.4
  pytest>=8.0.0
  pytest-asyncio>=0.23.5
  ```
  `python-multipart` is **NOT installed** in the virtual environment. Any attempt to define a FastAPI route accepting `UploadFile` or `Form(...)` will raise a runtime exception. This strongly reinforces that in-process browser file upload should not be part of the Phase 4 MVP.

### 1.7 Packaging & Deployment Constraints
- **Next.js Frontend:** [`frontend/next.config.mjs`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/frontend/next.config.mjs) does not enable `output: 'standalone'`. Compiling into an executable would require embedding Node.js, static assets, and dev/prod runtime wrappers.
- **Playwright Chromium:** Playwright depends on external browser binaries (~150MB+) located in `%USERPROFILE%\AppData\Local\ms-playwright`.
- **Python Backend:** Compiled C-extensions (greenlet, httptools, watchfiles, websockets) and relative SQLite/session paths introduce packaging fragility.
- Packaging remains complex, fragile, and high overhead. In accordance with project rules, **development runtime from source remains authoritative; packaging `.exe` is strictly deferred.**

### 1.8 Existing Test Harness Suitability
- [`backend/tests/test_performance_and_queries.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/tests/test_performance_and_queries.py) provides benchmark fixtures (`test_200_products_5000_snapshots_performance_benchmark`) and zero-N+1 query assertions that can be directly adapted to benchmark CSV streaming export and hot backup performance.
- [`backend/tests/test_phase3_file_recovery.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/tests/test_phase3_file_recovery.py) provides isolated file-backed SQLite lifecycle patterns (`tmp_path`, engine disposal, multi-session restart) that can validate backup creation, corrupted file rejection, rollback guarantees, and version checking.

---

## 2. Clarification & Reconciliation of Prior Terminology

Earlier exploratory reviews used shorthand terms that do not accurately reflect the prior durable research records. To maintain rigorous architectural continuity, the following points are formally reconciled:

1. **SQLite WAL Mode (`journal_mode=delete`):**
   - *Clarification:* WAL mode was previously an unresolved question subject to runtime source verification, not an accepted baseline assumption.
   - *Reconciled Fact:* Live runtime operates in standard rollback journal mode (`journal_mode=delete`). This does not prevent online backup; Python's `sqlite3.Connection.backup` works safely with delete journal mode, though quiescing write transactions guarantees zero lock contention.
2. **FastAPI Multipart & Browser File Upload:**
   - *Clarification:* Browser file upload was previously identified as a potential interface candidate requiring dependency verification, not an approved specification.
   - *Reconciled Fact:* The verified absence of `python-multipart` confirms that in-process browser upload would require introducing new dependencies or custom byte-streaming parsers. This fact narrows the MVP toward an offline/operator-driven restore workflow.
3. **In-Process Database File Replacement:**
   - *Clarification:* The durable research already rejected live in-place database replacement due to Windows file-locking concerns and preferred an offline/quiesced lifecycle.
   - *Reconciled Fact:* Source verification completely reinforces and concretizes this decision: Windows file locking prevents live swapping, while existing launcher scripts (`stop_services.ps1`, `start_services.ps1`) already provide the necessary process lifecycle management.

---

## 3. Explicit Classification of Repository Risk: `PRAGMA foreign_keys = 0`

### 3.1 Observed Runtime Fact
Source verification observed that standard database connections created via SQLAlchemy yield:
```text
PRAGMA foreign_keys = 0
```
This occurs because SQLite defaults to disabling foreign key enforcement on new connections unless an explicit connection listener executes `PRAGMA foreign_keys = ON;`. In [`backend/app/db/session.py:7-15`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/db/session.py#L7-L15), no such listener is registered.

### 3.2 Integrity Assessment of Current Database
An exhaustive check against the live database (`backend/affiliate.db`) confirms:
- `PRAGMA integrity_check;` $\to$ `[('ok',)]`
- `PRAGMA foreign_key_check;` $\to$ `[]` (zero violations across all 10 tables)

All existing foreign key constraints across the models (`ProductSnapshot.product_id`, `WatchlistItem.product_id`, `AlertRule.product_id`, `AlertEvent.rule_id`, etc.) are completely valid. Referential integrity has been preserved throughout Phases 1–3 by SQLAlchemy ORM relationships and service-level transaction boundaries.

### 3.3 Formal Risk Classification
This finding is formally classified as:
> **`NON-BLOCKING PRE-EXISTING TECHNICAL DEBT / CROSS-PHASE OBSERVATION`**

**Rationale:**
1. **Not a Phase 4 Blocker:** Phase 4 scope is Reporting & Productization (CSV export, backup/restore, health/diagnostics). It does not introduce new entity relationships or alter crawl transaction paths.
2. **Do NOT Silently Enable in Phase 4:** Enabling `PRAGMA foreign_keys = ON` on live connections changes connection-level semantics across all Phase 1–3 crawler upserts and background tasks. If any legacy code relies on transient unordered flushes or deferred constraint validation, enabling FK enforcement globally could introduce regressions outside Phase 4 scope.
3. **Phase 4 Validation Invariant:** While runtime connection settings remain untouched in Phase 4, the **Phase 4 backup and restore engine must strictly enforce foreign key validity**:
   - Every backup candidate file and staged restore database **must** pass `PRAGMA integrity_check` and `PRAGMA foreign_key_check` before being accepted for replacement.
   - Restored databases must be verified clean before services are brought back online.
4. **Project Routing:** If runtime FK enforcement should be turned on at the engine level for live application connections, that decision must be routed back to **Project Control / `BUG — Cross-phase Bugs`** as an explicit cross-phase task with dedicated regression testing, rather than silently absorbed into Phase 4.

---

## 4. Architectural Analysis for Phase 4

### 4.1 Export Architecture: Deterministic Backend Streaming
- **Why Backend-Generated:**
  Generating CSVs in the backend ensures 100% adherence to authoritative business logic. Calling `TrendService` or `WatchlistService` directly guarantees that scoring equations, time-window bounding (e.g. 172h snapshot cutoff), null-value handling, and tie-breaking remain perfectly synchronized with the user interface.
- **Vietnamese Language Support (`utf-8-sig`):**
  Exported CSVs contain Vietnamese product titles (e.g., "Chuối Sấy Mè", "Bịch khăn giấy Sipiao"). To ensure Microsoft Excel on Windows opens CSV files without garbling diacritics, all exports must be prefixed with the UTF-8 Byte Order Mark (`\ufeff` / `utf-8-sig`).
- **Memory Efficiency via Streaming:**
  FastAPI's `StreamingResponse` wrapping a Python generator using `csv.writer` / `io.StringIO` allows rows to be yielded incrementally, maintaining low memory consumption even when exporting large snapshot histories.

### 4.2 Backup Architecture: Hot SQLite Online Backup API
- **Mechanism:**
  Python's built-in `sqlite3` module provides native support for the SQLite Online Backup API:
  ```python
  def perform_hot_backup(source_db_path: Path, target_backup_path: Path) -> None:
      with sqlite3.connect(source_db_path) as src, sqlite3.connect(target_backup_path) as dst:
          src.backup(dst, pages=250, sleep=0.005)
  ```
- **Benefits:**
  - Operates safely while the database is open by reading consistent pages under shared locks.
  - Generates a standalone, byte-complete copy of `backend/affiliate.db` in a dedicated directory (`backups/`).
  - Does not require third-party binaries or shell utilities.

### 4.3 Restore Architecture: Offline Launcher-Owned Lifecycle
- **Lifecycle Flow:**
  ```
  [Operator / RESTORE.bat]
         │
         ▼
  1. Stop Services (scripts/stop_services.ps1 -Target All)
         │  (Ports 8000 & 3000 released; open file handles closed)
         ▼
  2. Validate Candidate Backup File (Python helper)
         │  - File existence & SQLite header check
         │  - PRAGMA integrity_check == 'ok'
         │  - PRAGMA foreign_key_check == []
         │  - Check SystemMetadata for backup_compatibility_version
         ▼
  3. Safety Backup of Current State
         │  (Copy affiliate.db -> backups/pre_restore_safety_backup_<timestamp>.db)
         ▼
  4. Replace Database File
         │  (Atomically replace backend/affiliate.db with candidate)
         │  [On failure: restore pre_restore_safety_backup and abort]
         ▼
  5. Restart Services (scripts/start_services.ps1 -Target All)
         │  - FastAPI lifespan executes init_db()
         │  - Reconciles abandoned crawls (running -> partial)
         │  - AlertService.catch_up_alerts() synchronizes state
         ▼
  6. Health Check Verification (healthcheck.bat)
  ```
- **Guarantees:**
  - Eliminates Windows file-locking collisions (`WinError 32`).
  - Guarantees that corrupted, incompatible, or foreign-key-violating backup files never replace the live database.
  - Automatically executes standard Phase 1–3 startup reconciliation and alert catch-up upon restart.

### 4.4 System Diagnostics Architecture
- **Scope of Diagnostics:**
  - System health, environment, region, and Git/code revision ([`backend/app/api/health.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/api/health.py)).
  - Crawler state: active run status, last run timestamp, quarantine count ([`backend/app/api/crawler.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/api/crawler.py)).
  - Local session availability: enum status only (`available`, `missing`, `invalid`), redacting all token data.
  - Storage & scheduler stats: database file size, row counts per table, and active scheduler cron jobs.
- **Presentation:**
  - Accessible via a clean Diagnostics/Status modal or drawer in the UI header ([`frontend/src/components/Header.tsx`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/frontend/src/components/Header.tsx)).

---

## 5. Scope Recommendation: Smallest Coherent Phase 4 MVP

### 5.1 Recommended Phase 4 MVP
1. **Deterministic Backend-Generated CSV Exports:**
   - **Trends Export:** CSV download based on active table filters (category, state, confidence, evidence) and deterministic sorting via `TrendService`.
   - **Watchlist Export:** CSV download of watched products via `WatchlistService`.
   - **Product Snapshot History Export:** Bounded chronological history (`24h`, `7d`, `30d`, `all`) of raw price, sold count, reviews, and rating snapshots for a given product.
   - **Alert History Export:** CSV download of historical alert events with timestamps, triggering snapshots, thresholds, actual values, and resolved messages.
   - All CSVs formatted with `utf-8-sig` (Vietnamese Excel compatibility) and streamed via standard `StreamingResponse`.
2. **Minimal Accessible Frontend Export UI:**
   - "Xuất CSV" action buttons placed non-intrusively in:
     - Trends toolbar ([`frontend/src/app/page.tsx`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/frontend/src/app/page.tsx));
     - Watchlist toolbar;
     - Product History header ([`frontend/src/components/ProductHistory.tsx`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/frontend/src/components/ProductHistory.tsx));
     - Alert Center ([`frontend/src/components/AlertCenter.tsx`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/frontend/src/components/AlertCenter.tsx)).
3. **SQLite Hot Backup Engine:**
   - Dedicated Python backup service using native `sqlite3.Connection.backup`.
   - Generates timestamped backup files into project-local `backups/` directory (e.g., `backups/trendhunter_backup_YYYYMMDD_HHMMSS.db`).
   - Triggerable via backend API endpoint and optional CLI helper.
4. **Offline Launcher-Owned Restore Lifecycle:**
   - Dedicated operator launcher script ([`RESTORE.bat`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/RESTORE.bat) / `scripts/restore.ps1`).
   - Quiesces services using `scripts/stop_services.ps1`.
   - Validates candidate file: SQLite file header check, `PRAGMA integrity_check`, `PRAGMA foreign_key_check`, and `SystemMetadata` version marker check.
   - Creates automatic pre-restore safety copy (`backups/pre_restore_safety_backup_<timestamp>.db`).
   - Atomically replaces `backend/affiliate.db` with rollback on failure.
   - Restarts services via `scripts/start_services.ps1` and runs standard startup reconciliation.
5. **Backup Compatibility Anchor:**
   - Seed `backup_compatibility_version = "1.0.0"` in `SystemMetadata` during startup bootstrap.
   - Enforce same-version restore compatibility in the restore validator.
6. **Strict Security & Portable Boundaries:**
   - The 10 SQLite application tables define 100% of portable application state.
   - TikTok session credentials (`backend/.local/tiktok-session.json`) are strictly excluded from backup archives.
   - Strict basename validation on all file paths; reject arbitrary directory traversal.
7. **System Diagnostics & Diagnostics Modal:**
   - Consolidated status API reporting revision, DB size, row counts, crawler status, scheduler next-run times, and session enum status.
   - Surfaced in a clean Header modal/popover in the frontend.
8. **Targeted Operator & Onboarding Documentation:**
   - Update `README.md` with operational guidance for CSV exports, hot backups, and `RESTORE.bat` execution.

### 5.2 Conditional Scope (If Justified During Planning)
- **Browser-Initiated Backup Download:** A `GET /api/backup/download/{filename}` endpoint allowing operators to download pre-generated backups directly from the `backups/` folder via the browser, protected by strict filename whitelist/basename checks.

### 5.3 Strictly Deferred Scope
The following items are outside Phase 4 MVP and remain strictly deferred:
- **Multi-Version Cross-Schema Migrations:** No migration framework exists; restoring across major structural schema differences is deferred until a formal migration tool is adopted.
- **Browser-Upload In-Process Restore:** Excluded due to absence of `python-multipart` and Windows file-locking constraints.
- **Arbitrary Filesystem Export Paths:** Excluded to prevent path traversal risks; exports are browser downloads or restricted to `backups/`.
- **Session/Cookie Portability:** Excluded to prevent credential leakage.
- **Generic Report Builder / Custom Query Engines:** Pre-canned, deterministic domain CSVs satisfy all affiliate operational requirements.
- **AI-Generated Summary Reports:** External LLM integration is outside local decision support scope.
- **Executable/Installer Packaging (`.exe`):** In accordance with project rules, packaging Next.js, Python C-extensions, and Playwright binaries into an installer remains deferred.
- **Automated Anti-Bot / CAPTCHA Bypass:** Broad TikTok scraping bypass remains outside architecture scope.
- **Unrelated Refactorings:** Phase 1–3 crawl ingestion, trend scoring, and alert evaluation paths remain intact.

---

## 6. Remaining Unknowns (Reduced to Planning Decisions)

All architectural and source-level blockers are resolved. Only two tactical implementation details remain to be decided during Phase 4 planning:

1. **Streaming Batch Granularity for Large History Exports:**
   - *Question:* When exporting snapshot histories with $>50{,}000$ rows, should the generator yield row-by-row or in batches of 500–1,000 rows?
   - *Status:* Can be safely decided during planning and validated via the existing `test_200_products_5000_snapshots_performance_benchmark` test fixture.
2. **Operator UX Integration for Restore:**
   - *Question:* Should the frontend UI provide an instructional card with copyable commands for `RESTORE.bat`, or should it also display a list of local backups available in the `backups/` folder?
   - *Status:* Purely a frontend presentation decision that can be finalized in `PHASE_4_PLAN.md` without additional architectural research.

Both items can be safely resolved during planning without further research gates.

---

## 7. Architecture Decision Record (ADR) Requirement

### ADR-004: Local Backup/Restore Integrity and Compatibility Semantics
- **Assessment:** **STRONGLY WARRANTED & REQUIRED**
- **Trigger:** Required immediately upon Project Control approval of Phase 4 planning.
- **Core Principles to be Formalized in ADR-004:**
  1. Defining the 10-table SQLite boundary as the sole portable application state.
  2. Strict exclusion of local TikTok authentication tokens from backup files.
  3. Enforcing same-version restore compatibility via `SystemMetadata`.
  4. Mandatory pre-restore offline validation (`PRAGMA integrity_check`, `PRAGMA foreign_key_check`).
  5. The offline maintenance lifecycle to prevent Windows file-locking corruption.
  6. Automated pre-restore safety backups and rollback guarantees.

*(Note: In accordance with instructions, ADR-004 will be drafted during planning, not during this research update).*

---

## 8. Planning Constraints for Phase 4

Any plan generated for Phase 4 must strictly adhere to the following constraints:
1. **Zero New Dependencies:** Do not add `python-multipart`, external backup binaries, or migration tools to `requirements.txt` or `package.json`.
2. **Preserve Development Mode:** Do not generate `.exe` packages, MSI installers, or standalone bundling scripts.
3. **No In-Process File Swaps on Windows:** Database restoration must execute while services are stopped.
4. **Mandatory UTF-8-SIG for CSV Exports:** All CSV files must include the UTF-8 BOM for Excel compatibility with Vietnamese text.
5. **Strict Query Reuse:** CSV generation must directly call `TrendService`, `WatchlistService`, and authoritative snapshot/alert models to prevent scoring drift.
6. **Isolated Test Fixtures:** All Phase 4 automated tests must use temporary file-backed databases (`tmp_path`) and never mutate the live `backend/affiliate.db`.
7. **Offline Validation Invariant:** Restore procedures must execute both `PRAGMA integrity_check` and `PRAGMA foreign_key_check` before replacing the active database file.

---

## 9. Research Gate Conclusion & Project Control Handoff

- **Gate Status:** **RESEARCH COMPLETED & SOURCE-VERIFIED**
- **Classification:** **`RESEARCH READY FOR PHASE PLANNING`**
- **Status of Implementation:** **NOT AUTHORIZED (Research-only work complete; no production code written; no plan created; no ADR created).**

### Concise Handoff for `00 — Project Control & Roadmap`

| Dimension | Project Control Summary |
|---|---|
| **Final Classification** | **`RESEARCH READY FOR PHASE PLANNING`** |
| **Recommended MVP** | 1. Backend streaming CSV exports (`TrendService`, `WatchlistService`, `ProductSnapshot`, `AlertEvent`) with `utf-8-sig`.<br>2. Hot SQLite online backup (`backups/trendhunter_backup_*.db`).<br>3. Offline launcher-owned restore (`RESTORE.bat`) with integrity/FK checks, safety backup, and restart reconciliation.<br>4. Compatibility marker in `SystemMetadata` (same-version restore).<br>5. System diagnostics API & Header modal.<br>6. Targeted operator docs in `README.md`. |
| **ADR Requirement** | `ADR-004 — Local backup/restore integrity and compatibility semantics` is required prior to Phase 4 implementation. |
| **Key Planning Constraints** | Zero new dependencies (no `python-multipart`); no `.exe` packaging; no in-process file replacement on Windows; UTF-8 BOM on CSV exports; reuse Phase 2/3 query seams. |
| **Known Technical Debt / Risk** | `PRAGMA foreign_keys = 0` on live connections classified as non-blocking pre-existing debt. Offline restore validator will enforce `PRAGMA foreign_key_check`. Runtime connection FK changes routed to Project Control cross-phase backlog. |
| **Deferred Scope** | Cross-version schema migrations, browser-upload restore, arbitrary path exports, session portability, generic report builder, AI reporting, standalone desktop `.exe` packaging. |
| **Project State Note** | Phase 4 selected; research gate formally ready to close; Phase 4 planning remains `NOT STARTED`; Phase 4 implementation remains `NOT AUTHORIZED`. |
