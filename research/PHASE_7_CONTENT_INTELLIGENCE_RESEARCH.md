# Phase 7 Research — TikTok Content Intelligence & Video Signals

- **Date:** 2026-10-07
- **Authority / Role:** `01 — Architecture & Repo Research`
- **Task Type:** Technical & Architectural Research Only
- **Implementation Authorization:** **NOT AUTHORIZED**
- **Product Recommendation:** **RECOMMEND WITH PHASED SCOPE (HTTP-First, User-Assisted Linking, Orthogonal Velocity Analytics)**
- **Research Gate Status:** **RESEARCH COMPLETE / READY FOR PROJECT CONTROL REVIEW**

---

## 1. Executive Conclusion & Product Recommendation

### 1.1 Executive Conclusion
In accordance with the foundational architecture defined in [`Project.md`](Project.md) (Sections 1, 22–24), the long-term mission of TinixTikTrend is to answer:
> **“Which TikTok Shop products should I consider promoting as an affiliate today?”**
> 
> ```text
> TikTok Shop Product Data (Phases 1–5: Ingestion, Quality, Alerts, Workspace)
>         +
> Affiliate Economics (Phase 6: VND Manual Scenarios & Break-Even Intelligence)
>         +
> TikTok Content Data (Phase 7: Video & Creator Signals)
>         ↓
> Composite Trend & Opportunity Intelligence
>         ↓
> "What should I promote today?"
> ```

Phases 1 through 6 have successfully delivered and qualified a robust local-first platform:
- Product catalog and verified PDP crawling (Phases 1–2);
- Authoritative Trend Score, sales velocity, and sales acceleration (Phase 2);
- Monitoring watchlists and background alerts (Phase 3);
- CSV export streaming, disaster-recovery backup/restore, and system diagnostics (Phase 4);
- Decision workspace with Collections, Saved Views, and transient Compare (Phase 5);
- Manual-first VND Affiliate Economics scenarios, rational integer rounding, and ceiling break-even calculations (Phase 6).

The critical missing dimension is **Content Signals**: identifying whether a product is gaining traction across TikTok creators and viral videos *before* market sales plateau or become oversaturated.

### 1.2 Authoritative Product Recommendation
We recommend **Phase 7 — Content Intelligence & Video Signals** with a focused, resilient architecture:
1. **User-Assisted & PDP Anchor Linking (Hybrid Source):**
   - Provide direct user-assisted entry of TikTok video URLs (`https://www.tiktok.com/@username/video/{video_id}`) associated with a tracked Product;
   - Provide automated harvesting of creator showcase video links when present on the product's PDP or shop page;
   - Strictly prohibit broad keyword/hashtag scraping without anti-bot solvers.
2. **HTTP-First Extraction via SSR Embedded JSON (`__UNIVERSAL_DATA_FOR_REHYDRATION__`):**
   - Replicate the proven, lightweight HTTP-first parser architecture established in Phase 1;
   - Extract video statistics (`playCount`, `diggCount`, `commentCount`, `shareCount`) directly from the server-rendered `<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">` tag;
   - Fall back to headless Playwright session reuse only when WAF challenges occur.
3. **Orthogonal Content Velocity Engine:**
   - Compute `views_velocity_24h` and `likes_velocity_24h` independently of the Phase 2 product `Trend Score`;
   - Enforce identical temporal bounding invariants ($24\text{h} \pm 4\text{h}$ window, minimum 20h observation, null propagation for insufficient history);
   - Prohibit blending video velocity into the core product Trend Score within Phase 7 to prevent score contamination.
4. **Zero Media Binary Storage:**
   - Strictly exclude video file downloading, audio stripping, re-encoding, or local MP4 storage;
   - Only lightweight metadata (video ID, author handle, nickname, avatar thumbnail URL, caption, view/like metrics) is persisted.
5. **Additive Database Schema & Compatibility Advance to `"4"`:**
   - Introduce additive tables: `product_videos` and `video_snapshots`;
   - Maintain strict same-version backup/restore semantics under ADR-004, advancing `portable_backup_compatibility_version` from `"3"` to `"4"`.

---

## 2. Repository Verification & Baseline State

Repository inspection confirms:
- **Active Branch:** `main`
- **Qualified Release State:** Phase 6 Source-Release Qualified (`READY WITH DOCUMENTED NON-BLOCKING ISSUES`, commit `8e36d7732a39a7751963283259687e174b88e146`)
- **Current Selection Commit:** `5beb082` (`docs(governance): select Phase 7 Content Intelligence and open research gate`)
- **Working Tree:** Clean (0 uncommitted changes)
- **Active Test Suites:** 218 backend pytest tests passing, 52 frontend Vitest tests passing, 0 TypeScript errors, 0 ESLint warnings, production build clean
- **Active Backup Compatibility:** `"3"` (`tinix-affiliate-v3-*.sqlite3`)
- **Live Database State:** 28 products, 100 product snapshots, 20 quarantined legacy rows, 46 crawl runs, SQLite integrity `ok`, foreign key check clean (`[]`)

---

## 3. Reference Implementation Analysis

### 3.1 Reference 1: `davidteather/TikTok-Api` (Python Unofficial Wrapper)
- **Architecture:** Reverse-engineered unofficial Python wrapper utilizing Playwright to intercept internal web endpoints (`/api/item/detail/`, `/api/recommend/item_list/`).
- **Research Findings & Failure Modes:**
  1. High fragility: TikTok frequently updates internal API signatures (`_signature`, `msToken`, `X-Bogus`), causing intermittent breakage and maintenance churn.
  2. Inconsistent metrics: Recent GitHub issues (e.g., issues #1024, #1085) report that `play_count` and `digg_count` frequently return empty or 0 due to API response obfuscation.
  3. Heavyweight runtime: Spawns multiple ephemeral browser contexts, conflicting with our local-first resource budget.
- **Architectural Decision:** **Do NOT import or depend on `TikTok-Api`.** Direct dependency would introduce unacceptable operational instability and third-party supply chain risk.

### 3.2 Reference 2: `MisterSeitz/TikTok-Shop-Product-and-Creator-Tracker`
- **Architecture:** Apify Python Actor combining Playwright crawling of TikTok Shop product detail pages and creator showcase video links.
- **Key Extraction Mechanism:**
  - Scans anchor elements (`<a href="...">`) on product listings and PDPs for patterns matching `/video/` and `tiktok.com/@`.
  - Captures `creators[]` array with `video_url`, `likes`, `comments`.
  - Relies on full Playwright page scrolling (`auto_scroll_page`), consuming excessive CPU/RAM.
- **Architectural Decision:** **Adapt the URL matching patterns and creator link harvesting**, but replace the heavy Apify/Playwright execution with our project's native HTTP-first collector and SQLite relational storage.

---

## 4. TikTok Web & Extraction Mechanics

### 4.1 Server-Side Rendered (SSR) JSON Hydration
Modern TikTok web video pages (`https://www.tiktok.com/@{username}/video/{video_id}`) render complete metadata within an HTML `<script>` tag:
```html
<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">
{
  "__DEFAULT_SCOPE__": {
    "webapp.video-detail": {
      "itemInfo": {
        "itemStruct": {
          "id": "7123456789012345678",
          "desc": "Review sản phẩm siêu hot...",
          "createTime": 1696123456,
          "author": {
            "uniqueId": "bangbangfood",
            "nickname": "BĂNG BĂNG FOOD",
            "avatarThumb": "https://..."
          },
          "stats": {
            "diggCount": 24500,
            "shareCount": 1200,
            "commentCount": 450,
            "playCount": 580000,
            "collectCount": 3100
          }
        }
      }
    }
  }
}
</script>
```

### 4.2 Fallback Structure: `SIGI_STATE`
Older or alternate regional responses place video details under:
```javascript
window['SIGI_STATE'] = {
  "ItemModule": {
    "7123456789012345678": {
      "id": "7123456789012345678",
      "desc": "...",
      "stats": { "playCount": 580000, "diggCount": 24500, ... },
      "author": "bangbangfood"
    }
  }
}
```

### 4.3 Proven Extraction Strategy
1. **HTTP GET with Browser Headers:**
   - Make an asynchronous HTTP request using `httpx.AsyncClient` with standard desktop/mobile User-Agent and `Accept-Language: vi-VN,vi;q=0.9`.
   - Pass existing user-operated session cookies (`tiktok-session.json`) if available to minimize captcha frequency.
2. **Regex Script Tag Parsing:**
   - Extract `<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">` content.
   - Navigate JSON dictionary: `__DEFAULT_SCOPE__` → `webapp.video-detail` → `itemInfo` → `itemStruct`.
3. **Graceful Degeneration & Playwright Fallback:**
   - If the HTTP response contains a `Security Check` challenge or missing SSR script, fall back to headless Playwright browser session to retrieve page content.
   - If the video has been deleted, marked private, or region-blocked, mark the snapshot as `is_unavailable = True` without deleting historical observations.

---

## 5. Product-to-Video Association Architecture

### 5.1 The Association Challenge
TikTok Shop does not provide an open public reverse-index mapping from a `product_id` to all public TikTok videos tagged with that product. Broad search on TikTok web requires anti-bot bypass and is prone to rate-limiting blocks.

### 5.2 Supported Association Modalities
To maintain 100% reliability without fragile scraping hacks, Phase 7 should support three complementary association modalities:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   Product-Video Association Channels                   │
└────────────────────────────────────────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┼───────────────────────────────┐
    ▼                               ▼                               ▼
[1. User-Assisted Entry]   [2. PDP Showcase Harvesting]   [3. Seller Video Match]
User pastes video URL      Crawler detects creator         Videos from seller's
directly on Product page   videos embedded in PDP DOM      linked TikTok handle
    │                               │                               │
    └───────────────────────────────┴───────────────────────────────┘
                                    │
                                    ▼
                     [Normalized ProductVideo Record]
                     UNIQUE(product_id, video_id)
```

1. **User-Assisted URL Entry (Primary / Deterministic):**
   - User inputs one or more TikTok video URLs (`https://www.tiktok.com/@creator/video/{video_id}`) directly on the Product Detail page.
   - System validates URL syntax, canonicalizes video ID, ingests creator and initial snapshot, and attaches the video to the Product.
2. **PDP Showcase Harvesting (Automated Proxy):**
   - When crawling a TikTok Shop PDP via Playwright or SSR HTML, the collector parses any creator showcase video anchors (`/video/`) rendered in the product's review or showcase modules.
   - Detected videos are automatically upserted into `product_videos` for that `product_id`.
3. **Seller Linked Handle Ingestion (Optional Secondary):**
   - If a product's seller handle (`Shop.name` or `Shop.url`) is known, videos explicitly published by that creator handle can be associated.

---

## 6. Content Velocity & Growth Mathematical Formulation

### 6.1 Raw Metrics Tracked per Snapshot
Each observation records:
- $P(t)$: `play_count` (views)
- $D(t)$: `digg_count` (likes)
- $C(t)$: `comment_count` (comments)
- $S(t)$: `share_count` (shares)
- $B(t)$: `collect_count` (bookmarks)
- $t$: `captured_at` (UTC timestamp)

### 6.2 24h Views Velocity Formula ($V_{\text{views}}$)
Following the exact, proven Phase 2 temporal bounding principles:
Let $S_{\text{latest}}$ be the latest snapshot at $t_{\text{latest}}$.
Find candidate prior snapshot $S_{\text{prior}}$ at $t_{\text{prior}}$ within the bounded candidate window:
$$t_{\text{prior}} \in [t_{\text{latest}} - 28\text{h},\, t_{\text{latest}} - 20\text{h}]$$
If an exact or candidate snapshot exists:
$$\Delta t = \frac{t_{\text{latest}} - t_{\text{prior}}}{86,400\text{ seconds}}$$
$$\Delta \text{views} = P(t_{\text{latest}}) - P(t_{\text{prior}})$$
$$V_{\text{views}} = \frac{\Delta \text{views}}{\Delta t}$$

### 6.3 24h Likes Velocity Formula ($V_{\text{likes}}$)
$$\Delta \text{likes} = D(t_{\text{latest}}) - D(t_{\text{prior}})$$
$$V_{\text{likes}} = \frac{\Delta \text{likes}}{\Delta t}$$

### 6.4 Engagement Rate & Engagement Velocity
Engagement total $E(t) = D(t) + C(t) + S(t) + B(t)$.
$$V_{\text{engagement}} = \frac{E(t_{\text{latest}}) - E(t_{\text{prior}})}{\Delta t}$$
$$\text{Engagement Rate} = \begin{cases} 
\frac{E(t_{\text{latest}})}{P(t_{\text{latest}})} & \text{if } P(t_{\text{latest}}) > 0 \\
\text{null} & \text{otherwise}
\end{cases}$$

### 6.5 Invariants & Guardrails
- **Null ≠ Zero:** Missing snapshots or history $< 20\text{h}$ evaluates strictly to `null`.
- **Negative Delta Protection:** If a creator deletes views/likes or TikTok prunes fake engagement, resulting in $\Delta < 0$, velocity is clamped to $0$ with an explanatory flag `anomaly_detected = True`.
- **Integer Rounding Authority:** Display rounded whole numbers; backend retains exact rational representations.

---

## 7. Domain Separation & Composite Index Invariants

### 7.1 Strict Independence from Phase 2 Trend Score
A fundamental invariant of TinixTikTrend is that **market evidence, user assumptions, and content signals must remain conceptually distinct**:
- **Phase 2 Trend Score:** Measures *market sales velocity and acceleration* of the product on TikTok Shop.
- **Phase 6 Economics:** Models *user commercial unit economics and break-even orders*.
- **Phase 7 Content Signals:** Measures *creator video engagement and view momentum*.

**Rule:** Content velocity must NOT modify or contaminate the Phase 2 `Trend Score`, trend confidence, trend state, or "Why Trending" reasons. They are displayed side-by-side as distinct evidence pillars.

### 7.2 Future Composite Scoring (Deferred to Later Phase)
A combined "Affiliate Opportunity Priority" score that blends Market Momentum (Phase 2), Commercial Economics (Phase 6), and Content Momentum (Phase 7) is preserved as future decision intelligence, strictly outside Phase 7 MVP.

---

## 8. Entity Modeling & Database Schema Design

### 8.1 Required Application Tables
Phase 7 requires exactly two new additive tables:
1. `product_videos`: Master registry of TikTok videos associated with a product.
2. `video_snapshots`: Time-series observations of video engagement statistics.

### 8.2 Table: `product_videos`
```sql
CREATE TABLE product_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    video_id VARCHAR(64) NOT NULL,
    video_url VARCHAR(512) NOT NULL,
    creator_handle VARCHAR(128) NULL,
    creator_nickname VARCHAR(256) NULL,
    creator_avatar_url VARCHAR(512) NULL,
    description TEXT NULL,
    thumbnail_url VARCHAR(512) NULL,
    published_at TIMESTAMP NULL,
    source_type VARCHAR(32) NOT NULL DEFAULT 'user_entry', -- 'user_entry', 'pdp_showcase'
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT uq_product_videos_product_video UNIQUE (product_id, video_id)
);

CREATE INDEX ix_product_videos_product_id ON product_videos (product_id);
CREATE INDEX ix_product_videos_video_id ON product_videos (video_id);
```

### 8.3 Table: `video_snapshots`
```sql
CREATE TABLE video_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL REFERENCES product_videos(id) ON DELETE CASCADE,
    play_count BIGINT NULL,
    digg_count BIGINT NULL,
    comment_count BIGINT NULL,
    share_count BIGINT NULL,
    collect_count BIGINT NULL,
    captured_at TIMESTAMP NOT NULL,
    source_channel VARCHAR(32) NOT NULL DEFAULT 'http', -- 'http', 'playwright'
    is_available BOOLEAN NOT NULL DEFAULT 1
);

CREATE INDEX ix_video_snapshots_video_captured ON video_snapshots (video_id, captured_at DESC);
```

### 8.4 Additive Bootstrap & Migration Safety
- Table creation proceeds additively via SQLAlchemy `Base.metadata.create_all(bind=engine)`.
- No Alembic dependency is introduced.
- Existing historical products, product snapshots, collections, watchlist items, and economics scenarios remain completely untouched.

---

## 9. Disaster Recovery & Backup Compatibility Version `"4"`

### 9.1 Compatibility Version Advancement
Following the strict ADR-004 same-version restore invariant:
- Current product compatibility: `"3"`
- Phase 7 target compatibility: `"4"`
- When Phase 7 schema is implemented, `system_metadata` will advance `portable_backup_compatibility_version = "4"`.

### 9.2 Restore Rejection & Isolation
- Restoring a `v1`, `v2`, or `v3` backup into a `v4` runtime will be deterministically rejected with structured HTTP 400.
- `BACKUP.bat` will produce `tinix-affiliate-v4-*.sqlite3` online backups.
- Host-bound TikTok credentials (`tiktok-session.json`) remain strictly excluded from all backups and exports.

---

## 10. Query Budgets & Zero N+1 Performance Strategy

### 10.1 Query Budgets
- **Product Detail Page (with Videos tab):**
  - Query 1: Fetch `Product` + snapshots (existing Phase 2 budget).
  - Query 2: Fetch `EconomicsScenario` (existing Phase 6 budget).
  - Query 3: Fetch `ProductVideo` items with joined latest snapshots.
  - Total queries for Product Detail: $\le 3$ SQL queries.
- **Collections Workspace / Compare Modal:**
  - If video metrics are displayed in comparison: Batched query using `WHERE product_id IN (...)` with composite index.
  - Zero N+1 queries across all endpoints.

### 10.2 Benchmark Target
- Representative 200-product dataset with 1,000 associated videos and 10,000 video snapshots must execute detail queries in $< 15\text{ms}$ and compare queries in $< 50\text{ms}$ (hard gate: $< 200\text{ms}$).

---

## 11. Frontend Workspace Integration

### 11.1 Product Detail Page: "Video & Content Intelligence" Section
A dedicated content section beneath Product Details and Economics:
- **Video Cards / Carousel:** Displays video thumbnails, creator avatars, handles, and captions.
- **Velocity Metrics:** Badges for `Lượt xem 24h (+X%)`, `Lượt thích 24h (+Y%)`, and `Tỷ lệ tương tác`.
- **Add Video Action:** Simple modal allowing operator to paste TikTok video URLs to track.
- **Refresh Action:** On-demand button to trigger immediate video metrics re-scrape.

### 11.2 Transparency & Commercial Disclaimers
A visible metadata disclosure banner:
> *"Dữ liệu video được thu thập công khai từ TikTok. Tốc độ xem và tương tác phản ánh mức độ lan tỏa nội dung, không đại diện trực tiếp cho doanh số thực tế của nhà sáng tạo."*

---

## 12. Security, Privacy & Storage Boundaries

1. **Zero Media Binaries:** No video files (.mp4, .webm) or raw audio streams will ever be downloaded or written to disk. Only numeric statistics and public HTTPS image URLs are stored.
2. **Local Financial & Content Privacy:** All video URLs and associations remain 100% local in SQLite. No telemetries or third-party cloud analytics are invoked.
3. **Session Quarantine:** Video requests reuse public read-only headers. If TikTok session cookies are utilized, they are read-only from `backend/.local/tiktok-session.json`.

---

## 13. Architectural Decision Record (`ADR-006`) Recommendation

Project Control should require and accept **`ADR-006: TikTok Content Intelligence & Video Signals Architecture`** prior to Phase 7 planning.

ADR-006 must formally codify:
1. Orthogonal separation between content velocity and product Trend Score;
2. HTTP-first SSR JSON extraction via `__UNIVERSAL_DATA_FOR_REHYDRATION__`;
3. Two-table schema (`product_videos`, `video_snapshots`);
4. Advance of portable backup compatibility marker to `"4"`;
5. Strict prohibition of video media binary downloads.

---

## 14. Preserved Deferred Scope & Non-Blocking Debt

### 14.1 Preserved Deferred Scope
- Broad automatic TikTok hashtag / search scraping without anti-bot solvers;
- Automatic creator commission payout tracking;
- Video media downloading, storage, or AI video transcription;
- Cross-version database migration scripts (same-version restore enforced);
- Standalone `.exe` packaging (supported boundary remains Windows source runtime).

### 14.2 Preserved Non-Blocking Debt
- 1 High `source-map-js` advisory in production graph (`GHSA-68fv-2mgg-jv7q`), build-time-only;
- Development-only `braces` and `postcss-selector-parser` advisories in devDependencies;
- `StarletteDeprecationWarning` in test runner;
- Runtime `PRAGMA foreign_keys = 0` (`OFF`) on live SQLite connection pool.

---

## 15. Research Gate Conclusion & Next Lifecycle Steps

### 15.1 Summary Assessment
Phase 7 ("TikTok Content Intelligence & Video Signals") is technically sound, architecturally coherent with `Project.md`, and completely viable under our established HTTP-first, local-first paradigm.

### 15.2 Transition back to `00 — Project Control & Roadmap`
The research gate is complete. Project Control may now:
1. Review and accept this research document (`PROJECT_CONTROL_PHASE7_RESEARCH_ACCEPTED.md`);
2. Authorize and accept `ADR-006`;
3. Authorize drafting of `PHASE_7_PLAN.md`.
