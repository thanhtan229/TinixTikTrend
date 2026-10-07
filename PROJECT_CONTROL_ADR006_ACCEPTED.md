# Project Control ADR-006 Acceptance Record

> **Historical decision superseded 2026-10-07.** ADR-006 was revised after package review. The prior acceptance does not apply to the revised ADR. See [`PROJECT_CONTROL_PHASE7_PACKAGE_REVIEW.md`](PROJECT_CONTROL_PHASE7_PACKAGE_REVIEW.md).

- **Date:** 2026-10-07
- **Authority / Role:** `00 — Project Control & Roadmap`
- **ADR Title:** [`ADR-006 — TikTok Content Intelligence & Video Signals Architecture`](docs/architecture/ADR-006.md)
- **Project Control Decision:** `ACCEPTED`
- **Accepted Research Baseline:** [`research/PHASE_7_CONTENT_INTELLIGENCE_RESEARCH.md`](research/PHASE_7_CONTENT_INTELLIGENCE_RESEARCH.md) (documented in [`PROJECT_CONTROL_PHASE7_RESEARCH_ACCEPTED.md`](PROJECT_CONTROL_PHASE7_RESEARCH_ACCEPTED.md))
- **Phase 7 Status:** `SELECTED / RESEARCH COMPLETE / ARCHITECTURE ACCEPTED`
- **Architecture Gate:** `CLOSED / ACCEPTED`
- **Phase Plan Status:** `AUTHORIZED TO BEGIN` (Phase 7 implementation planning is now authorized)
- **Implementation Status:** `NOT AUTHORIZED`
- **Acceptance Criteria:** `NONE DEFINED YET` (to be defined in `PHASE_7_PLAN.md`)
- **Current Product Compatibility:** `"3"` (Phase 6 qualified release state unchanged)
- **Target Phase 7 Compatibility:** `"4"` (upon future Phase 7 schema implementation)
- **Previous Release State:** Phase 6 source-release qualification remains **`READY WITH DOCUMENTED NON-BLOCKING ISSUES`** for the supported **Windows / local / source-based runtime** (qualified repository revision: `ed442bf3c9bfaabaef01c054d2df9e9771c47bc2`; qualified product-code revision: `2f3e4b4783307bdfa5e5ffbc7cfd49576572eb0f`). Acceptance of ADR-006 does not alter or invalidate the qualified Phase 6 release.

---

## 1. Project Control Decision

Project Control has formally reviewed and **ACCEPTED** [`ADR-006 — TikTok Content Intelligence & Video Signals Architecture`](docs/architecture/ADR-006.md).

1. **Architecture Gate Closed:** The Phase 7 architecture gate is formally **CLOSED / ACCEPTED**.
2. **Implementation Planning Authorized:** Phase 7 implementation planning is now **AUTHORIZED TO BEGIN**. Planning must strictly adhere to ADR-006 and the accepted Phase 7 research artifact.
3. **Implementation Not Authorized:** Phase 7 implementation remains strictly **NOT AUTHORIZED**. No production code, tests, or dependencies may be created or modified until the Phase 7 implementation plan is reviewed and approved by Project Control.
4. **Release State Preserved:** The running application remains on the Phase 6 qualified release state at compatibility version `"3"`.

---

## 2. Authoritative Frozen Architecture Invariants

All architectural decisions established in ADR-006 are frozen as authoritative constraints:

1. **Domain Separation & Metric Independence:**
   - Strict separation across Market Evidence (Phases 1–3), User Economics Assumptions (Phase 6), and Content Intelligence (Phase 7).
   - Content velocity metrics (`views_velocity_24h`, `likes_velocity_24h`, `engagement_velocity`) must **never** modify, weigh into, or alter the Phase 2 `Trend Score`, trend momentum, evidence confidence, or Why Trending explanations.
   - Blended composite scores are strictly deferred.
2. **Ingestion & Association Modalities:**
   - User-assisted TikTok video URL entry (`https://www.tiktok.com/@{username}/video/{video_id}`) on Product Detail page.
   - PDP showcase video link harvesting when crawling TikTok Shop product pages.
   - Broad hashtag/keyword scraping and CAPTCHA solving bypasses are strictly out of scope.
3. **HTTP-First SSR Extraction:**
   - Extract video metadata and stats directly from `<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">` (or `SIGI_STATE`).
   - Headless Playwright session reuse as fallback for WAF challenges.
   - Zero dependency on fragile unofficial wrappers (`davidteather/TikTok-Api`).
4. **Zero Media Binary Storage:**
   - Strictly prohibit downloading, saving, or transcoding video/audio media files (.mp4, .webm, .mp3).
   - Only scalar metadata, metrics, and public HTTPS thumbnail URLs are persisted.
5. **Exact Rational Math & Velocity Invariants:**
   - 24h velocity follows the bounded candidate window: $[t_{\text{latest}} - 28\text{h},\, t_{\text{latest}} - 20\text{h}]$.
   - Null-safety: missing history strictly produces `null`, never `0` (`null ≠ 0`).
   - Non-negative clamping: if platform metrics decrease, velocity clamps to `0` with `anomaly_detected = True`.
   - Exact integer ratio round-half-up $(2N + D) // (2D)$ for integer displays.
6. **Additive Schema & Concurrency:**
   - Two additive tables: `product_videos` (`UNIQUE(product_id, video_id)`) and `video_snapshots` (`(video_id, captured_at DESC)`).
   - Additive bootstrap via `Base.metadata.create_all()`.
7. **Disaster Recovery Compatibility Version `"4"`:**
   - Target compatibility marker advances from `"3"` to `"4"` upon Phase 7 schema implementation.
   - Same-version restore policy under ADR-004 is strictly preserved (v1, v2, v3 backups rejected with structured HTTP 400).
   - Hot backups via `BACKUP.bat` produce `tinix-affiliate-v4-*.sqlite3`.
   - TikTok session credentials isolated from all backups.
8. **Query Budgets & Zero N+1:**
   - Product detail page executes $\le 3$ SQL queries.
   - Zero N+1 queries across all endpoints.
9. **Commercial Disclaimers:**
   - Prominent transparency disclaimer displayed on all video velocity UI surfaces.

---

## 3. Next Lifecycle Action

- **Current State:** Architecture Accepted (`ADR-006 ACCEPTED`).
- **Next Required Gate:** Draft the authoritative implementation plan: **`PHASE_7_PLAN.md`**.
- **Planning Authority:** `00 — Project Control & Roadmap`.
