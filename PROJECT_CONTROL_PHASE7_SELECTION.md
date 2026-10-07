# Project Control Phase 7 Selection Record

- **Date:** 2026-10-07
- **Authority:** `00 — Project Control & Roadmap`
- **Selected Phase:** Phase 7 — Content Intelligence & Video Signals
- **Phase 7 Status:** `SELECTED / RESEARCH REQUIRED`
- **Research Gate:** `OPEN / RESEARCH REQUIRED`
- **Research Status:** `NOT YET STARTED`
- **Phase Plan Status:** `NOT STARTED`
- **Implementation Status:** `NOT AUTHORIZED`
- **Acceptance Criteria:** `NONE DEFINED YET` (no Phase 7 acceptance criteria exist yet)
- **Previous Release State:** Phase 6 source-release qualification remains **`READY WITH DOCUMENTED NON-BLOCKING ISSUES`** for the supported **Windows / local / source-based runtime** (qualified repository revision: `ed442bf3c9bfaabaef01c054d2df9e9771c47bc2`; qualified product-code revision: `2f3e4b4783307bdfa5e5ffbc7cfd49576572eb0f`; latest release-state reconciliation commit: `8e36d7732a39a7751963283259687e174b88e146`). Selection of Phase 7 does not invalidate the qualified Phase 6 release.

---

## 1. Selection Decision & Strategic Intent

Project Control has formally selected **Phase 7 — Content Intelligence & Video Signals** as the next product development phase.

### Strategic Rationale
In accordance with the foundational architecture outlined in [`Project.md`](Project.md) (Sections 1, 22–24):
```text
TikTok Shop Product Data (Phases 1–5)
        +
Affiliate Economics (Phase 6)
        +
TikTok Content Data (Phase 7: Video & Creator Signals)
        ↓
Composite Trend & Opportunity Intelligence
        ↓
"Which TikTok Shop products should I promote today?"
```
Phases 1 through 6 have established a hardened, release-qualified foundation covering product data ingestion, trend analytics, monitoring & alerts, disaster-recovery backup/restore, decision workspace collections, and transparent manual-first affiliate economics.

The next critical missing dimension is **Content Signals**: identifying whether a product is gaining traction across TikTok videos and creators before market saturation occurs. Phase 7 will introduce structured, local-first content intelligence linking TikTok videos and creators to tracked TikTok Shop products.

---

## 2. Research Gate & Planning Policy

- **Phase 7 Status:** `SELECTED / RESEARCH REQUIRED`
- **Research Status:** `NOT YET STARTED`
- **Plan Status:** `NOT STARTED`
- **Implementation Status:** `NOT AUTHORIZED`
- **Mandatory Policy:** Research must precede planning. **Phase 7 planning is strictly blocked until comprehensive research is completed, documented, and formally accepted by Project Control.**
- **Active Role for Next Step:** `01 — Architecture & Repo Research`.

---

## 3. Expected Research Questions (Research Gate Agenda)

The research gate must investigate and answer the following authoritative questions:

1. **Product-to-Content Association Mechanisms:**
   - How can TikTok videos be reliably linked to a tracked TikTok Shop product?
   - Can anchor links (`product_id`), product titles, seller handles, specific campaign hashtags, or sound IDs be resolved from public video metadata?
   - How does manual video URL entry compare to automated discovery of associated videos?
2. **Data Ingestion & Reference Architecture:**
   - Evaluation of reference libraries: [`davidteather/TikTok-Api`](https://github.com/davidteather/TikTok-Api) and [`MisterSeitz/TikTok-Shop-Product-and-Creator-Tracker`](https://github.com/MisterSeitz/TikTok-Shop-Product-and-Creator-Tracker).
   - What APIs or DOM structures currently expose video views, likes, comments, and shares?
   - Can content metadata be retrieved via HTTP-first SSR JSON extraction (`SIGI_STATE`, `__UNIVERSAL_DATA_FOR_REHYDRATION__`) or is browser rendering required?
3. **Anti-Bot, Challenge & Session Constraints:**
   - How does TikTok's anti-bot posture (Security Check / WAF) affect video endpoint querying compared to shop PDPs?
   - Can the existing user-operated session (`backend/.local/tiktok-session.json`) be safely reused for video inspection without compromising security or invalidating PDP crawls?
4. **Content Velocity & Growth Analytics:**
   - Exact mathematical definitions for content velocity: `views_velocity_24h`, `likes_velocity_24h`, `engagement_growth`.
   - Handling bounded elapsed time, interval tolerances, and zero vs missing metrics without false precision.
   - Preserving orthogonal separation: content velocity must not silently contaminate Phase 2 Trend Score unless explicitly governed by a composite index.
5. **Entity Modeling & Database Schema:**
   - Conceptual entities: `ProductVideo`, `VideoSnapshot`, `Creator`.
   - What unique constraints and indices are required (e.g., `UNIQUE(product_id, video_id)`, `(video_id, captured_at)`)?
   - Additive schema creation via `Base.metadata.create_all()` without Alembic migrations.
   - Determining whether portable backup compatibility must advance (`"3" → "4"`).
6. **Query Budgets & Zero N+1 Enforcement:**
   - Query budget for Product Detail page rendering associated videos and velocity metrics.
   - Ensuring list and detail views do not trigger per-video N+1 database queries.
7. **Storage Boundaries & Media Hygiene:**
   - Explicit confirmation that video binary media (MP4 files, video streams) will NOT be stored locally. Only metadata, public thumbnails, and metrics are tracked.
8. **Frontend Workspace Integration:**
   - UI presentation on Product Detail page (Videos tab, engagement velocity sparklines, creator attribution cards).
   - Integration with Collections and Compare workspaces (optional default content highlights).
9. **ADR Requirement:**
   - Assess whether a dedicated Architectural Decision Record (`ADR-006`) is required to codify content signal invariants, velocity formulas, and schema boundaries.
10. **Out-of-Scope Boundaries:**
    - Explicitly exclude video downloading, re-encoding, automated video posting, CAPTCHA solving bypasses, and cloud storage dependencies.

---

## 4. Preserved Architectural Boundaries

The following architecture principles and invariants must remain strictly preserved throughout Phase 7:
- `Watchlist = monitoring authority`;
- `Collections = decision organization`;
- `WatchlistItem.notes` provenance ownership;
- `CollectionItem.notes` decision-note ownership;
- Phase 2 authoritative Trend Score and evidence semantics (market sales momentum remains distinct from content engagement);
- Phase 3 alert semantics (price, sales velocity, trend score);
- Phase 4 same-version backup/restore safety policies;
- Phase 5 Saved View contracts and transient Compare semantics;
- Phase 6 manual-first affiliate economics scenarios and integer ratio calculation engine;
- Backup compatibility version `"3"` remains active until Phase 7 schema implementation explicitly advances it to `"4"`.

---

## 5. Preserved Technical Debt & Deferred Scope

The following accepted non-blocking debt and deferred scope items are preserved unchanged:
- 1 High `source-map-js` advisory in the production dependency graph (`GHSA-68fv-2mgg-jv7q`), build-time-only / non-runtime-reachable;
- Development-only `braces` and `postcss-selector-parser` advisories in devDependencies;
- `StarletteDeprecationWarning` during test execution;
- Runtime `PRAGMA foreign_keys = 0` (`OFF`) on live SQLite connection pool;
- Broad automated home/category discovery deferred (TikTok Security Check challenge);
- Real 7-day field observation deferred (post-release operational validation);
- Standalone executable packaging deferred (supported boundary: Windows / local / source-based runtime);
- Cloud synchronization and multi-user capabilities deferred.

---

## 6. Next Immediate Action

- **Active Role:** `01 — Architecture & Repo Research`
- **Action:** Initiate comprehensive Phase 7 technical and architectural research, investigating product-video association, TikTok video metadata extraction, content velocity mathematics, and schema design.
