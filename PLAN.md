# Production review remediation plan

Updated: 2026-10-03. Scope: C1, H1–H8, M1–M3 in FINAL_REVIEW.md.

- [x] Back up SQLite and quarantine contaminated legacy products without deleting history.
- [x] Upgrade patched Next.js; validate dependency compatibility and production build.
- [x] Enforce verified Shop identity, nullable metrics, public HTTPS destinations and loopback runtime.
- [x] Correct time coverage, stale metrics and scheduled tracked-product refresh.
- [x] Correct keyword routing, partial/failed runs, transaction rollback and restart recovery.
- [x] Repair UI polling, visible errors, stale-response handling and UTC serialization.
- [x] Replace broad process termination with project ownership checks and hidden standard launcher.
- [x] Run targeted backend/frontend tests, lint, typecheck and build.
- [x] Add user-operated local session setup and scoped reuse, with availability UI and security tests.
- [ ] Validate several live cycles on verified TikTok Shop VN products with real sales history.
- [x] Collect user-provided VN PDP, validate identity/metrics, repeated upsert, tracked refresh, charts and restart persistence.
- [x] Filter history by real timestamp ranges, explain empty ranges, preserve zero values, add detail retry.
- [x] Exclude cumulative-only products from trend momentum score/rank until a recent measured sales/review signal exists.

Three real snapshots for one VN PDP were verified (runs18–20). Release acceptance remains open: current VN Shop home/category routes return Security Check, and observations span minutes rather than the required sales windows. Do not fill this gap with fabricated history. No executable packaging is requested.
