# Operational Validation — 2026-11-09

## Scope

Validate the supported Windows/local/source runtime after the release closeout. The validation used three sequential manual crawl cycles against one previously verified TikTok Shop VN product URL. Broad discovery and CAPTCHA/security-check bypass were not attempted.

## Results

| Check | Result | Evidence |
|---|---|---|
| Backend health | PASS | HTTP 200; `status=ok`; database `connected`; region `VN` |
| Frontend health | PASS | HTTP 200 on port 3000 |
| Backend tests | PASS | `227 passed`, 5 existing deprecation warnings, 41.45s |
| Frontend tests | PASS | Vitest `53/53` across 10 files |
| Manual crawl cycle 1 | PASS | Run 108, `completed`, 9 products found, 9 updated, 9 snapshots |
| Manual crawl cycle 2 | PASS | Run 109, `completed`, 9 products found, 9 updated, 9 snapshots |
| Manual crawl cycle 3 | PASS | Run 110, `completed`, 9 products found, 9 updated, 9 snapshots |
| Concurrent-run residue | PASS | `0` crawl runs left in `running` state |
| Trend API smoke check | PASS / no current signals | HTTP 200; returned 0 trend items because no measurable sales delta appeared during the short validation window |
| Database persistence | PASS | 38 products, 510 snapshots, 110 crawl runs after validation |

## Runtime note

The preflight found two project-owned uvicorn processes. `RESTART.bat backend` was run using the documented project script; the duplicate was removed and the replacement backend passed health verification. One project-owned backend process remains active.

## Assessment

The core operational path is healthy: manual crawl requests are accepted, runs complete, product history is appended, and no abandoned run remains. This short validation does not establish useful trend ranking quality because the three cycles did not produce an observable sales delta. Continue passive observation across the normal schedule before opening a new product phase.

## Follow-up

- Observe at least one longer interval, preferably 24–48 hours and multiple scheduled cycles.
- Confirm non-zero measured sales/review deltas and meaningful Rising/Trending results when source data changes.
- Keep P7-AC-19, broad discovery bypass, and executable packaging deferred.
