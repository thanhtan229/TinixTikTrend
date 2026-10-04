# Project status

Updated: 2026-10-03 19:18 UTC+7. Phase: production review remediation / live development validation.

Production acceptance remains **NOT READY**. Broad TikTok Shop VN discovery is still blocked by Security Check on home/category routes; only one user-provided PDP has been verified, with about two hours of history. The production dependency audit still reports seven high findings in development dependencies. No executable has been packaged.

## Implemented and validated

- Review findings C1, H1–H8 and M1–M3 have been addressed. See `FIX_REPORT.md` and the preserved original `FINAL_REVIEW.md`.
- Live VN PDP parsing, identifier matching, repeated upsert, tracked refresh, persistence across restart, real-snapshot charts/history filters, retry, zero-value display and conservative trend evidence are verified.
- Fixed Vietnamese number formatting for estimated sales velocity. A real rate of 176.0005 units/day now displays as **+176,0**, instead of the ambiguous **+176,001**.
- Signed metrics now show a plus only for positive changes, use a minus for declines, and format large negative/positive values symmetrically. Labels distinguish daily pace from 24h changes.
- Dashboard accepts up to100 distinct product URLs, one per line. Exact duplicate links are removed, and the run button is blocked with an accessible message above the backend limit.
- Trend score and Trending results require recent observed momentum. Product21 currently has score55.6 after sold count rose from12808 to12823 over about2.04 hours; the displayed daily pace is explicitly estimated. Review count stayed730, rating4.6, latest shown price43,797 VND, commission unknown.
- Live database: **21 products / 54 product snapshots / 20 quarantined legacy rows**, SQLite integrity `ok`, and no crawl left running. Original20 products /50 snapshots remain intact.

## Validation and runtime

- Backend: **91 pytest PASS**, compileall PASS at prior full validation checkpoint. Backend code was not changed in these UI iterations.
- Frontend: **11 tests PASS**, including signed negative/zero values and URL-list deduplication/limit; ESLint PASS, TypeScript `--noEmit` PASS, production build PASS.
- Frontend was restarted with `RESTART.bat frontend`; latest project Next.js wrapper74492 / listener85860 replaced the previous frontend. Browser verified the `+176,0` daily estimate, corrected delta labels, and the 2/100 URL counter. Backend wrapper88276 / listener103988 remained healthy.
- Standard `healthcheck.bat`: backend HTTP200, status `ok`, database `connected`; frontend HTTP200. Backend revision `9870cbdee0f5c21c`.
- Browser history filter, charts and four real snapshot rows remain visible; responsive layout previously passed at390px without horizontal overflow.
- Dependency review rechecked: production npm audit has **0 vulnerabilities**; the full development tree has **7 high** findings under the `braces`/`micromatch`/`fast-glob` toolchain. `npm audit fix --dry-run` proposes a Tailwind4 major migration and an `eslint-config-next` downgrade to14.2.35 while the app runs Next15.5.27. Neither was applied; no patched `braces`3.0.4 exists in the registry. These need a deliberate toolchain migration with browser/build validation, rather than an automatic downgrade.
- Latest standard healthcheck: backend HTTP200 / status `ok` / database `connected`; frontend HTTP200. Database still has21 products,54 snapshots,20 quarantined rows, integrity `ok`, and no active crawl.

## Remaining release gates

Verified product discovery through VN Shop home/category; 24h/7d history across multiple live products; production dependency review for seven development audit findings; and long-duration/restart soak testing. To continue live-data acceptance, the user should paste3–5 distinct, normally accessible VN PDP URLs into the new multi-line field and leave the local services running through their scheduled crawls. Continue only with real observations; do not fabricate history or attempt to bypass TikTok challenges.
