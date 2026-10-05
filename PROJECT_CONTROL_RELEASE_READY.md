# Project Control Release Qualification Record

- **Date:** 2026-10-05
- **Decision:** `READY WITH DOCUMENTED NON-BLOCKING ISSUES`
- **Qualified Source Revision:** `4bdc1bc842f7a4ab2ce671f2923f7d2dc4989936`
- **Phase 4 Completion State:** `COMPLETE / ACCEPTED`
- **Repository QA & Runtime Qualification:** `PASS`
- **Source-Control Handoff:** `COMPLETE`
- **Release Readiness:** `READY WITH DOCUMENTED NON-BLOCKING ISSUES`
- **Supported Release Boundary:** `Windows / local / source-based`
- **Release Blockers:** None
- **Remote Publication Status:** Qualified revision has not been pushed to `origin/main` (remote publication is a separate explicitly authorized action).
- **Phase 5 Status:** `NOT SELECTED / NOT STARTED`

---

## Accepted Non-Blocking Debt

1. **Development-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`):**
   - Transitive dependency of `tailwindcss@3.4.19` and `eslint-config-next@15.5.27` in `devDependencies`.
   - Production runtime reachability: 0 vulnerabilities (`npm audit --omit=dev` clean).
   - Classified as non-blocking development tooling debt awaiting upstream release.

2. **`StarletteDeprecationWarning`:**
   - Emitted during test execution for `httpx` integration with `starlette.testclient`.
   - Non-blocking test-runner warning; zero impact on runtime behavior.

3. **Runtime `PRAGMA foreign_keys = 0` (`OFF`):**
   - Preserved on live SQLite connection pool for cross-phase operational stability.
   - Offline restore validator enforces strict `PRAGMA foreign_key_check` cleanly before any candidate replacement.

---

## Accepted Deferred Scope

1. **Broad automatic discovery / CAPTCHA bypass:**
   - TikTok Shop VN home/category routes trigger TikTok Security Check challenges without anti-bot solvers.
   - CAPTCHA bypass and anti-bot circumvention remain strictly out of project architecture scope.
   - Primary supported ingestion workflow is user-provided PDP URL tracking.

2. **Real 7-day field observation:**
   - Multi-product collection and real 24h behavior validated; 7d analytics behavior proven via deterministic test fixtures.
   - Real 7-day field observation deferred as post-release operational validation.

3. **Browser DB transfer:**
   - Database backup/restore operations restricted to operator offline launcher scripts (`BACKUP.bat`, `RESTORE.bat`).

4. **Cross-version database migrations:**
   - Strict same-version restore enforced (`portable_backup_compatibility_version = "1"`).

5. **TikTok session portability:**
   - Session tokens and cookies host-bound (`backend/.local/tiktok-session.json`) and strictly excluded from backups/exports.

6. **Executable/installer packaging:**
   - Standalone `.exe` packaging deferred; supported deployment boundary is local Windows source-based runtime.

7. **All other previously documented deferred items.**
