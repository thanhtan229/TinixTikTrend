# Project Final Release and Lifecycle Closeout

- **Updated:** 2026-10-30
- **Lifecycle decision:** `PROJECT LIFECYCLE CLOSED FOR THE SUPPORTED LOCAL SOURCE RUNTIME`
- **Release assessment:** `READY WITH DOCUMENTED LIMITATIONS`
- **Supported boundary:** Windows / local / source-based development runtime
- **Phase 7 implementation revision:** `072f186430f60b33c8df99ba1236be1bdd31e838`
- **Validation baseline at closeout:** `main` / `origin/main` synchronized at `e7fc13f` before the local test and documentation updates in this closeout
- **Remote publication:** No push was performed during this closeout; the closeout changes remain local

## Qualification evidence

- Phase 7 is accepted and closed; its 28 acceptance criteria are classified in [`PHASE_7_COMPLETION_REPORT.md`](PHASE_7_COMPLETION_REPORT.md). P7-AC-19 remains deferred because the validated TikTok oEmbed response does not supply public engagement counters.
- **Clean-machine setup smoke test (2026-10-30):** `scripts/setup.ps1` completed in an isolated scratch copy made from tracked setup and dependency files. Python 3.11 and Node v24.18.0 were detected; backend dependencies installed from `requirements.lock.txt`; Playwright Chromium installed; frontend `npm ci` completed. npm reported 0 vulnerabilities across 418 audited packages. The backend `pip check` was clean, Chromium's executable was present, and all 37 backend lockfile versions matched the active project environment.
- **Backend tests:** `pytest -q` — 227 passed, with five Starlette deprecation warnings and a pytest-asyncio fixture-scope deprecation notice. The historical streaming test used a fixed October 5, 2026 timestamp that aged outside its 30-day query window; its fixture now uses the current UTC time.
- **Frontend evidence:** Vitest 53/53, TypeScript, ESLint, and Next.js build passed in the 2026-10-27 frontend checkpoint. No frontend source or dependencies changed in this closeout.
- Additive v3-to-v4 compatibility, v4 backup/restore, and older backup rejection remain covered by the previously accepted Phase 7 evidence. Live SQLite had `integrity_check=ok` and zero foreign-key violations at that qualification.
- **Runtime after closeout restart:** `RESTART.bat backend` replaced the project-owned backend process. `/api/health` returned HTTP 200 with `status=ok`, `database=connected`, and revision `d4cb99376205fa38`; frontend root returned HTTP 200. The frontend did not require a restart.
- **Dependency audit limitation:** A local `pip-audit` run reported 9 advisory rows (5 distinct IDs) for `setuptools==65.5.0`, which is present in the development virtualenv but not pinned in `requirements.lock.txt`. This was not represented as a clean Python audit; no exploitability assessment was performed. The clean setup does not install `pip-audit`.

## Accepted limitations

- Public engagement-observation ingestion remains deferred (P7-AC-19); missing metrics stay unavailable/null.
- The current Python audit identified an out-of-lock development-tool finding in `setuptools==65.5.0`; update the Python toolchain/seed package and repeat the audit before claiming a clean Python dependency scan.
- Executable and installer packaging remain deferred. No `.exe` or release package was generated.
- TikTok broad discovery, challenge bypass, private dashboard scraping, and unapproved external APIs remain out of scope.
- No remote push or production deployment was performed during this closeout.

## Final state

All selected roadmap phases are closed for the supported local source runtime. Phase 8 remains unopened because no new product outcome was selected; see [`PROJECT_CONTROL_PHASE8_SELECTION.md`](PROJECT_CONTROL_PHASE8_SELECTION.md). The application is running locally and passed the required health checks. The closeout test and documentation changes are committed locally and were not pushed.
