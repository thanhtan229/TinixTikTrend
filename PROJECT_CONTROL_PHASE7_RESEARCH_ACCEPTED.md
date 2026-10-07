# Project Control Phase 7 Research Acceptance Record

- **Date:** 2026-10-07
- **Authority / Role:** `00 — Project Control & Roadmap`
- **Selected Phase:** Phase 7 — Content Intelligence & Video Signals
- **Phase 7 Status:** `SELECTED / RESEARCH COMPLETE / ADR REQUIRED`
- **Research Gate:** `CLOSED / ACCEPTED`
- **Research Status:** `CLOSED / ACCEPTED` (authoritative research artifact: [`research/PHASE_7_CONTENT_INTELLIGENCE_RESEARCH.md`](research/PHASE_7_CONTENT_INTELLIGENCE_RESEARCH.md))
- **Product Recommendation:** `RECOMMEND WITH PHASED SCOPE (HTTP-First, User-Assisted Linking, Orthogonal Velocity Analytics) — ACCEPTED`
- **Architecture Gate:** `ADR-006 REQUIRED BEFORE PHASE 7 PLAN APPROVAL`
- **Phase Plan Status:** `NOT STARTED`
- **Implementation Status:** `NOT AUTHORIZED`
- **Authoritative Selection Commit:** `5beb082` (`docs(governance): select Phase 7 Content Intelligence and open research gate`)
- **Previous Release State:** Phase 6 release qualification remains **`READY WITH DOCUMENTED NON-BLOCKING ISSUES`** for the supported **Windows / local / source-based runtime** (qualified repository revision: `ed442bf3c9bfaabaef01c054d2df9e9771c47bc2`; qualified product-code revision: `2f3e4b4783307bdfa5e5ffbc7cfd49576572eb0f`). Acceptance of Phase 7 research does not invalidate the qualified Phase 6 release.

---

## 1. Project Control Acceptance Decision

Project Control has reviewed the research findings presented in [`research/PHASE_7_CONTENT_INTELLIGENCE_RESEARCH.md`](research/PHASE_7_CONTENT_INTELLIGENCE_RESEARCH.md).

**Decision:** **`ACCEPTED`**

1. **Research Gate Closed:** The Phase 7 research gate is closed as **`CLOSED / ACCEPTED`**.
2. **Product Direction Accepted:** Project Control accepts the phased architecture:
   - User-assisted TikTok video URL input + PDP anchor harvesting as the primary association modalities;
   - HTTP-first extraction parsing SSR JSON hydration (`__UNIVERSAL_DATA_FOR_REHYDRATION__` / `SIGI_STATE`);
   - Headless Playwright fallback for WAF challenges;
   - Orthogonal content velocity analytics (`views_velocity_24h`, `likes_velocity_24h`, `engagement_growth`) decoupled from Phase 2 Trend Score;
   - Zero media binary downloads/storage (only metadata and metrics persisted);
   - Additive schema (`product_videos`, `video_snapshots`) with portable backup compatibility marker advancing to `"4"`.
3. **Architecture Gate Opened:** In accordance with repository standards, **`ADR-006: TikTok Content Intelligence & Video Signals Architecture`** is required and must be accepted before Phase 7 plan approval.
4. **Implementation Remains NOT AUTHORIZED:** No production code or tests may be modified until the plan is approved.

---

## 2. Binding Architecture & Governance Directives

Project Control establishes the following mandatory constraints for Phase 7:

1. **Strict Score Independence:**
   - Content velocity metrics must NOT modify, weigh into, or contaminate the Phase 2 `Trend Score`, trend confidence, trend state, or Why Trending explanations.
   - Any composite opportunity scoring combining Market Demand (Phase 2), Economics (Phase 6), and Content Momentum (Phase 7) is deferred to a future phase.
2. **Attribution & Truth Invariant:**
   - Video views and likes represent public content engagement, not attributable product sales. Marketing disclaimers must be prominently displayed on UI surfaces.
3. **Storage Hygiene & Security:**
   - Video media files (MP4, WebM, MP3) must NEVER be saved to disk.
   - Video thumbnail URLs must point to public HTTPS sources without local caching.
4. **Disaster Recovery & Backup Compatibility:**
   - Additive bootstrap dynamically creates `product_videos` and `video_snapshots`.
   - `portable_backup_compatibility_version` must advance from `"3"` to `"4"` upon schema implementation under unchanged same-version restore semantics (ADR-004).
5. **Query Budget Gate:**
   - Product Detail view must execute $\le 3$ SQL queries.
   - Zero N+1 query regression across all endpoints.

---

## 3. Next Lifecycle State

- **Current State:** Research Accepted (`CLOSED / ACCEPTED`).
- **Next Required Gate:** `01 — Architecture & Repo Research` must draft **`docs/architecture/ADR-006.md`**.
- **Followed by:** Project Control review and acceptance of ADR-006 (`PROJECT_CONTROL_ADR006_ACCEPTED.md`), followed by `PHASE_7_PLAN.md` drafting.
