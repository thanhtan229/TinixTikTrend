# Phase 7 Plan — TikTok Content Signals

## Status

**COMPLETE / ACCEPTED WITH DOCUMENTED DEFERRED ITEM (2026-10-07).** This revised plan replaced the withdrawn 39-criterion proposal and authorized implementation. Project Control approval is recorded in [`PROJECT_CONTROL_PHASE7_PACKAGE_APPROVED.md`](PROJECT_CONTROL_PHASE7_PACKAGE_APPROVED.md); completion acceptance is recorded in [`PROJECT_CONTROL_PHASE7_COMPLETION_ACCEPTED.md`](PROJECT_CONTROL_PHASE7_COMPLETION_ACCEPTED.md). The 28 criteria are individually classified in [`PHASE_7_COMPLETION_REPORT.md`](PHASE_7_COMPLETION_REPORT.md). P7-AC-19 metric-observation ingestion remains deferred because no validated public metric source was available; missing metrics remain null.

## Goal and boundaries

Let an operator associate public TikTok videos with tracked products, inspect honestly sourced metadata and available public engagement observations, and refresh one video on demand. A link remains useful when no metric source is available.

In scope: manual URL entry, existing `ProductVideoLink` association, globally deduplicated video identity and observation history, safe best-effort retrieval, content-only velocity, API and product detail UI, v4 backup compatibility.

Out of scope: broad TikTok search, automatic PDP harvesting, inferred product attribution, scheduled/batch refresh, use of TikTok login cookies, browser fallback, challenge bypass, media downloads, external paid APIs, OAuth, research API integration, blended opportunity scoring, changes to Phase 2 scores or Phase 6 economics.

## Acceptance criteria

### Correctness and domain boundaries

- **P7-AC-01:** Video/content fields and calculations are separate from product market evidence and affiliate economics.
- **P7-AC-02:** No Phase 2 Trend Score, confidence, trend state, alert, or crawl scheduling result changes when video data is added, refreshed, or removed.
- **P7-AC-03:** The UI says operator association is not proof of product attribution, and engagement is not sales or payout.
- **P7-AC-04:** No media binary or raw page body is downloaded or persisted.
- **P7-AC-05:** Missing metadata/counters remain null; an old value is never copied into a new observation.
- **P7-AC-06:** For each metric independently, velocity uses two successful non-null observations whose prior timestamp is 20–28 hours before the latest timestamp, divided by actual elapsed time; otherwise it is null.
- **P7-AC-07:** Decreasing counters retain both raw observations and produce an explicit anomaly; they are not clamped or rewritten.
- **P7-AC-08:** Engagement rate is null when views are absent/zero or required engagement fields are missing.

### Persistence and recovery

- **P7-AC-09:** `tiktok_videos` uses canonical numeric `video_id` text as its primary key and stores shared metadata once per video, independent of product association.
- **P7-AC-10:** `ProductVideoLink` remains the sole product/video association; duplicate links for a product/video pair are rejected.
- **P7-AC-11:** `video_snapshots` has its own integer observation ID, references `tiktok_videos.video_id` with delete restriction, stores nullable counters and source/capture metadata, and indexes `(video_id, captured_at DESC)`.
- **P7-AC-12:** Detaching one product association preserves global video metadata and snapshots.
- **P7-AC-13:** Additive schema bootstrap leaves all Phase 1–6 tables and data intact and advances compatibility to `"4"` only after schema validation.
- **P7-AC-14:** v4 online backups include the new schema; v1–v3 candidates are rejected under ADR-004; session files remain excluded.

### Retrieval and API

- **P7-AC-15:** Accept only canonicalizable HTTPS TikTok video URLs on exact approved hosts and paths; invalid input returns a structured 422.
- **P7-AC-16:** All outbound requests and redirects use SSRF/public-destination validation and bounded timeout/response size.
- **P7-AC-17:** Refresh is explicit and single-video. It never reads session cookies, automatically retries a blocked request, launches a browser, or solves/bypasses a challenge.
- **P7-AC-18:** A 403/429, challenge, unsupported response, removed/private page, or unsafe redirect produces a clear bounded status and no metric snapshot.
- **P7-AC-19:** A successful response records only recognized available fields, source, and capture timestamp; parser failures do not create fabricated observations.
- **P7-AC-20:** Add, list, detach, and refresh APIs enforce product existence/quarantine rules and structured duplicate/not-found/error responses.
- **P7-AC-21:** API and service tests cover shared video identity across products and detachment with history preservation.

### Product experience and validation

- **P7-AC-22:** Product detail offers an add-video flow and displays associated videos, source, last refresh outcome, and unavailable/missing-metric states.
- **P7-AC-23:** Refresh is an explicit user action with loading and failure states; no background refresh is scheduled.
- **P7-AC-24:** Thumbnail URLs are constrained to public HTTPS destinations and UI fallbacks work without a thumbnail.
- **P7-AC-25:** Automated tests use sanitized fixtures and do not depend on live TikTok availability.
- **P7-AC-26:** Full backend/frontend tests, frontend typecheck/lint/build, migration/backup checks, and regression tests pass.
- **P7-AC-27:** Video API query count is bounded and does not grow per row. Benchmark 200 products, 1,000 global videos, and 10,000 snapshots; document median and p95, with a 200 ms hard limit for product detail data retrieval in the local test environment.
- **P7-AC-28:** Final QA verifies backend/frontend health after the mandatory local restart and confirms the running backend revision includes the change.

## Implementation sequence

1. Verify clean Phase 6 baseline and preserve a backup-safe test strategy.
2. Add pure content metric calculations and fixture-backed parsing contracts.
3. Add global video and snapshot models; reuse `ProductVideoLink`; implement additive bootstrap and v4 compatibility.
4. Add strict URL validation and bounded HTTP retrieval with no challenge fallback.
5. Add service/API workflows and tests for shared identity/history.
6. Add product detail video section and explicit add/refresh/remove actions with unavailable states and disclosure.
7. Verify backups, old-version rejection, query budgets, full suites and runtime health.

No `.exe`, installer, release artifact, remote push, or production deployment is in scope.
