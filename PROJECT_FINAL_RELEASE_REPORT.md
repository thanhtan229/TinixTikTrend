# Project Final Release and Lifecycle Closeout

- **Updated:** 2026-11-10
- **Lifecycle decision:** `PROJECT LIFECYCLE CLOSED FOR THE SUPPORTED LOCAL SOURCE RUNTIME`
- **Release assessment:** `READY WITH DOCUMENTED LIMITATIONS`
- **Supported boundary:** Windows / local / source-based development runtime
- **Phase 7 implementation revision:** `072f186430f60b33c8df99ba1236be1bdd31e838`
- **Validation baseline at closeout:** The Phase 7 qualification remains historical at `e7fc13f`; subsequent operational, anomaly-reporting, and challenge-diagnostics changes are recorded in later commits.
- **Repository reconciliation (2026-11-10):** Before this documentation update, the worktree was clean at `88d6dec` and local `main` was 9 commits ahead of `origin/main`. Fetch confirmed no remote-only commits, so no merge was needed. Backend tests passed 239/239 after the latest code changes; backend and frontend health checks passed after backend restart. This reconciliation commit publishes the complete local history to `origin/main`.

## Qualification evidence

- Phase 7 is accepted and closed; its 28 acceptance criteria are classified in [`PHASE_7_COMPLETION_REPORT.md`](PHASE_7_COMPLETION_REPORT.md). P7-AC-19 remains deferred because the validated TikTok oEmbed response does not supply public engagement counters.
- **Clean-machine setup smoke test (2026-10-30):** `scripts/setup.ps1` completed in an isolated scratch copy made from tracked setup and dependency files. Python 3.11 and Node v24.18.0 were detected; backend dependencies installed from `requirements.lock.txt`; Playwright Chromium installed; frontend `npm ci` completed. npm reported 0 vulnerabilities across 418 audited packages. The backend `pip check` was clean, Chromium's executable was present, and all 37 backend lockfile versions matched the active project environment.
- **Setuptools remediation (2026-10-30):** Added `setuptools==84.2.1` to `requirements.lock.txt`, bringing the lock to 38 pins and covering the Python venv seed package that the earlier default `pip freeze` audit omitted. Fresh isolated `scripts/setup.ps1 -SkipBrowser` installed setuptools 84.2.1 and completed frontend `npm ci` (418 packages, 0 vulnerabilities). `pip check` passed; `uvx --from pip-audit pip-audit --progress-spinner=off -r backend/requirements.lock.txt` reported no known vulnerabilities.
- **Backend tests:** `pytest -q` — 227 passed, with five Starlette deprecation warnings and a pytest-asyncio fixture-scope deprecation notice. The historical streaming test used a fixed October 5, 2026 timestamp that aged outside its 30-day query window; its fixture now uses the current UTC time.
- **Frontend evidence:** Vitest 53/53, TypeScript, ESLint, and Next.js build passed in the 2026-10-27 frontend checkpoint. No frontend source or dependencies changed in this closeout.
- Additive v3-to-v4 compatibility, v4 backup/restore, and older backup rejection remain covered by the previously accepted Phase 7 evidence. Live SQLite had `integrity_check=ok` and zero foreign-key violations at that qualification.
- **Runtime after closeout restart:** `RESTART.bat backend` replaced the project-owned backend process. `/api/health` returned HTTP 200 with `status=ok`, `database=connected`, and revision `d4cb99376205fa38`; frontend root returned HTTP 200. The frontend did not require a restart.
- **Current runtime health checked 2026-10-30:** `/api/health` returned HTTP 200 with `status=ok`, `database=connected`, and revision `d4cb99376205fa38`; frontend root returned HTTP 200. The backend command line was verified as project-owned. Process IDs are transient and intentionally omitted from this current summary.
- **Backend tests after the setuptools remediation:** `pytest -q backend/tests` — 227 passed in 42.32 seconds, with five Starlette deprecation warnings and a pytest-asyncio fixture-scope deprecation notice.

## Accepted limitations

- Public engagement-observation ingestion remains deferred (P7-AC-19); missing metrics stay unavailable/null.
- Executable and installer packaging remain deferred. No `.exe` or release package was generated.
- TikTok broad discovery, challenge bypass, private dashboard scraping, and unapproved external APIs remain out of scope.
- No production deployment was performed. The supported release remains Windows/local/source-based; broad discovery and P7-AC-19 remain deferred. Repository publication status is recorded in the reconciliation entry above.

## Final state

All selected roadmap phases are closed for the supported local source runtime. Phase 8 remains unopened because no new product outcome was selected; see [`PROJECT_CONTROL_PHASE8_SELECTION.md`](PROJECT_CONTROL_PHASE8_SELECTION.md). The application passed its 2026-11-10 backend and frontend health checks. The repository reconciliation and publication are recorded above; no production deployment or executable packaging was performed.
