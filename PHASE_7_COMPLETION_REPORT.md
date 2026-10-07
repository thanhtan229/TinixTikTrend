# Phase 7 Completion Report — TikTok Content Signals

- **Date:** 2026-10-07
- **Implementation revision:** `072f186430f60b33c8df99ba1236be1bdd31e838` (`feat(phase7): add curated TikTok video signals`)
- **Approved scope:** [`PHASE_7_PLAN.md`](PHASE_7_PLAN.md), P7-AC-01 through P7-AC-28
- **Completion classification:** `COMPLETE WITH DEFERRED ITEM`
- **Database compatibility:** `"4"`
- **Release boundary:** Windows / local / source-based development runtime
- **Remote publication:** Not pushed

Phase 7 adds operator-curated TikTok video associations, globally shared video identity and observation history, safe on-demand metadata refresh, content-only velocity calculations, product-detail controls, and v4 backup compatibility. It does not change market trend scoring or affiliate economics. TikTok's documented oEmbed response supplies metadata but not public engagement counters; therefore, metric-snapshot ingestion remains unavailable and is explicitly deferred. Missing values remain null.

## Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| P7-AC-01 | PASS | Video entities, snapshots, and calculations are separate from market evidence and affiliate economics. |
| P7-AC-02 | PASS | Regression suite preserves Phase 2 score, trend, alert, and scheduling behavior when video associations change. |
| P7-AC-03 | PASS | Product UI explains operator association is not proof of attribution and engagement is not sales or payout. |
| P7-AC-04 | PASS | Retrieval persists recognized metadata only; no media binary or raw page body is downloaded or stored. |
| P7-AC-05 | PASS | Missing counters remain null; refresh failure does not create a metric observation or copy older values. |
| P7-AC-06 | PASS | Per-metric velocity uses two valid non-null observations in the 20–28 hour window and actual elapsed time; otherwise it is null. |
| P7-AC-07 | PASS | Decreasing counters preserve both observations and expose an anomaly. |
| P7-AC-08 | PASS | Engagement rate remains null when views or required engagement fields are absent or views are zero. |
| P7-AC-09 | PASS | `tiktok_videos` stores one shared record keyed by canonical numeric video ID text. |
| P7-AC-10 | PASS | Existing `ProductVideoLink` is the sole association; duplicate product/video links are rejected. |
| P7-AC-11 | PASS | `video_snapshots` has an integer key, restricted video FK, nullable counters, source/capture fields, and descending video/time index. |
| P7-AC-12 | PASS | Detaching one product association retains global video identity and snapshots. |
| P7-AC-13 | PASS | Additive bootstrap preserves prior schema and data and promotes compatibility to `"4"` only after required-schema validation. |
| P7-AC-14 | PASS | v4 backups include the new schema; v1–v3 candidates are rejected and session files remain excluded. |
| P7-AC-15 | PASS | URL tests enforce HTTPS, canonicalizable URLs, exact TikTok hosts/paths, and structured 422 errors for invalid input. |
| P7-AC-16 | PASS | Outbound metadata retrieval validates public destinations and bounds redirects, timeout, and response size. |
| P7-AC-17 | PASS | Refresh is explicit and single-video; it does not use session cookies, retry challenges, launch a browser, or bypass challenges. |
| P7-AC-18 | PASS | Blocked, challenged, unsupported, private/removed, and unsafe-redirect responses yield bounded status and no metric snapshot. |
| P7-AC-19 | DEFERRED | Successful oEmbed metadata records its source and last-attempt time. No supported public metric source was validated, so metric observations cannot yet be ingested with source/capture metadata. No values are fabricated. |
| P7-AC-20 | PASS | Add/list/detach/refresh APIs enforce product availability and return structured duplicate, invalid-input, and not-found results. |
| P7-AC-21 | PASS | Tests verify cross-product global identity and history retention after detachment. |
| P7-AC-22 | PASS | Product detail supports add, list, detach, source/refresh visibility, and explicit unavailable/missing-metric states. |
| P7-AC-23 | PASS | Refresh requires an explicit user action and shows loading/failure states; no refresh scheduler was added. |
| P7-AC-24 | PASS | Thumbnail URLs are restricted to public HTTPS destinations and the UI has a no-thumbnail fallback. |
| P7-AC-25 | PASS | Automated coverage uses sanitized fixtures without depending on live TikTok availability. |
| P7-AC-26 | PASS | Backend, frontend, type, lint, build, migration, backup/restore, and regression checks passed. |
| P7-AC-27 | PASS | Product video retrieval uses a fixed four-query path regardless of returned row count. Fixture benchmark (200 products, 1,000 videos, 10,000 snapshots; 100 measured iterations): median 5.034 ms, p95 6.957 ms, worst 36.883 ms, below 200 ms. |
| P7-AC-28 | PASS | After restart, backend health returned HTTP 200, `status=ok`, `database=connected`, revision `d4cb99376205fa38`; frontend returned HTTP 200. |

## Validation and runtime evidence

- Backend: `pytest -q` — **227 passed**, with five existing Starlette deprecation warnings.
- Frontend: Vitest — **53 passed** across 10 files.
- Frontend ESLint: clean.
- Frontend TypeScript: `tsc --noEmit` clean.
- Frontend production build: Next.js build completed; no executable or installer was packaged.
- Compatibility and recovery: isolated v3-to-v4 additive bootstrap passed; old-version backup rejection and v4 backup/restore lifecycle passed.
- Live SQLite: compatibility marker `"4"`, `integrity_check=ok`, and no `foreign_key_check` violations.
- Server: project-owned backend and frontend restarted using `RESTART.bat`; backend and frontend health checks passed. Backend's loaded source revision matches current Python sources.
- Working tree at implementation close: clean. Current implementation commit is local and has not been pushed.

## Deferred item and boundary

`P7-AC-19` remains deferred until an approved, reliable public metric source is identified and validated. The live schema contains zero video records and zero video snapshots, so no live counter history is claimed. TikTok oEmbed metadata refresh, user-curated linking, and explicit unavailable states remain usable. Do not infer product attribution, sales, or payout from content engagement.

No additional Phase 7 blocker was identified. Project-wide release qualification and final closeout are recorded separately.
