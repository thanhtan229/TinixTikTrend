# Phase 2 Plan — Trend Quality & Decision Support

- **Phase:** Phase 2 — Trend Quality & Decision Support
- **Date:** 2026-10-05
- **Status:** Candidate Implementation Reconciled & Accepted
- **Reference Research:** [`research/PHASE_2_TREND_QUALITY_RESEARCH.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/research/PHASE_2_TREND_QUALITY_RESEARCH.md)
- **Target Architecture:** [`ARCHITECTURE.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/ARCHITECTURE.md)

---

## 1. Process Deviation Record

> [!IMPORTANT]
> **Process Deviation Notice:**
> Implementation of Phase 2 began and was substantially produced before the formal phase plan and acceptance gate were reviewed and approved by Project Control. In response to Project Control classifying the phase as `INCOMPLETE`, this plan formalizes the exact scope, invariants, and acceptance criteria of the candidate implementation that was produced. This document does NOT pretend to have existed prior to code creation; rather, it accurately describes the candidate implementation, evaluates it against the accepted research direction, establishes strict acceptance criteria, and documents complete verification.

---

## 2. Objective & Scope Boundaries

### Core Objective
Transform raw trend calculations into trustworthy, actionable decision support for TikTok Shop VN affiliate scouting by separating **trend strength** (momentum score) from **evidence quality** (confidence & observation sufficiency), providing deterministic explanations ("Why trending?"), and offering additive filtering and sorting controls without introducing fragile category normalizations or database migrations.

### In-Scope Acceptance Items
1. **Preserve Existing Trend Score:** Retain the authoritative 5-component weighted Trend Score (40% sales velocity 24h, 25% sales acceleration, 15% review velocity, 10% freshness, 10% rating) without unapproved score reweighting or modifications.
2. **Trend Evidence & Confidence Model:** Compute deterministic data quality metrics (`observation_count`, `observation_span_hours`, `latest_observation_age_hours`, `ranking_state`, `confidence`: low/medium/high, `signals`: measured/estimated/missing) orthogonal to trend score.
3. **Deterministic "Why Trending?" Reasons:** Structured backend reason codes (`sales_velocity_up`, `sales_acceleration_up`, `review_velocity_up`) ordered descending by mathematical contribution with deterministic tie-breaks.
4. **Category Filter:** Additive category filtering in backend query, API parameters, and frontend UI without category-relative score distortion.
5. **Eligibility & Evidence Filters:** Filter by `trend_state` (`eligible`, `all`, `stale`, `insufficient_signal`), `confidence` (`high`, `medium_or_high`), and `evidence` (`measured_only`).
6. **Multi-attribute Deterministic Sorting:** Support sorting by `trend_score`, `sales_velocity`, `sales_delta`, `review_delta`, and `freshness` with deterministic null-last ordering and primary tie-breaking on `product_id`.
7. **Explicit UI States:** Visual representations for stale observations (>8h) and insufficient-signal products rather than silent exclusion.
8. **Deterministic Test Suites:** Comprehensive backend (`test_trend_quality.py`) and frontend (`phase2-trend-quality.test.tsx`) test suites.
9. **Zero Schema Migrations:** All evidence, confidence, and reason fields are derived at read time from existing `products` and `product_snapshots` tables.
10. **Zero N+1 Query Regressions:** Bulk-load product snapshots via single eager `joinedload` query utilizing SQLite composite index `ix_product_snapshots_product_captured`.
11. **Durable Architecture Reconciliation:** Update [`ARCHITECTURE.md`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/ARCHITECTURE.md) with durable Phase 2 analytics invariants.

### Explicitly Out-of-Scope / Deferred Items
- **Automatic broad discovery / anti-bot bypass:** Preserved as deferred from Phase 1.
- **Category-relative score normalization (percentiles/z-scores):** Prohibited due to sparse tracked cohorts.
- **LLM-generated trend explanations:** Prohibited; all explanations must remain deterministic.
- **Real 7-day field observation closure:** Preserved as operational validation.

---

## 3. Candidate Implementation Architecture & Components

### 3.1 Analytics & Math Layer
- **[`backend/app/analytics/scoring.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/analytics/scoring.py):** Authoritative `calculate_trend_score` preserving exact weights and 8h stale / measured evidence requirements.
- **[`backend/app/analytics/evidence.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/analytics/evidence.py):** Implements `calculate_trend_evidence` and `calculate_trend_reasons`. Enforces that estimated intervals can never escalate confidence to HIGH.
- **[`backend/app/analytics/deltas.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/analytics/deltas.py):** Tracks `primary_elapsed_hours`, `has_24h_window`, and `has_7d_window`.
- **[`backend/app/analytics/rising_products.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/analytics/rising_products.py):** Adds evidence and reasons to `AnalyzedProduct` schema with stable `-product_id` tie-breaking.

### 3.2 Service & API Layer
- **[`backend/app/services/product_service.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/services/product_service.py):** Single bulk query with `joinedload(Product.snapshots)` excluding quarantined products and applying optional `category` filter.
- **[`backend/app/services/trend_service.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/services/trend_service.py):** Implements multi-attribute filtering (`trend_state`, `confidence`, `evidence`, `category`) and deterministic multi-key sorting with nulls-last semantics.
- **[`backend/app/api/trends.py`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/backend/app/api/trends.py):** Exposes query parameters `category`, `trend_state`, `confidence`, `evidence`, `sort_by`, `order`, and `limit`.

### 3.3 Frontend Layer
- **[`frontend/src/components/EvidenceBadge.tsx`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/frontend/src/components/EvidenceBadge.tsx):** Renders confidence badges (High, Medium, Low), observation metrics, and stale/insufficient status banners.
- **[`frontend/src/components/ProductCard.tsx`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/frontend/src/components/ProductCard.tsx):** Displays top deterministic reasons and embeds `EvidenceBadge`.
- **[`frontend/src/app/page.tsx`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/frontend/src/app/page.tsx):** Interactive controls for Category, Trend State, Confidence/Evidence filters, Sort Attribute, and Order toggle.
- **[`frontend/src/lib/api.ts`](file:///d:/___TOOLS/__TINIX/02-Tinix-Tiktok%20Trend%20Hunter/frontend/src/lib/api.ts):** URL query parameter serializer supporting all Phase 2 filtering and sorting options.

---

## 4. Acceptance Criteria & Verification Matrix

| # | Acceptance Criterion | Verification Method | Result |
|---|----------------------|---------------------|:------:|
| 1 | Existing Trend Score preserved (40/25/15/10/10) | Source inspection of `scoring.py` & `config.py` | PASS |
| 2 | Evidence & Confidence orthogonal to Score | Unit tests in `test_trend_quality.py` | PASS |
| 3 | Estimated intervals cannot escalate to High confidence | Unit test `test_estimated_intervals_cannot_escalate_confidence_to_high` | PASS |
| 4 | Deterministic Why Trending reasons ordered by contribution | Unit test `test_trend_reasons_deterministic_selection` | PASS |
| 5 | Empty reasons for ineligible or zero-score products | Unit test `test_trend_reasons_empty_for_ineligible_or_zero` | PASS |
| 6 | Category filter in backend service & API | Tests in `test_trend_quality.py` & live API QA | PASS |
| 7 | Category filter in frontend UI & API client | Tests in `phase2-trend-quality.test.tsx` & page inspection | PASS |
| 8 | Null-last sorting across all metric sort options | Verification in `test_trend_service_filters_and_sorts` | PASS |
| 9 | Stable tie-break ordering on `product_id` | Tested in `test_trend_service_filters_and_sorts` | PASS |
| 10 | Zero schema migration (tables unchanged) | SQLite PRAGMA check on live database | PASS |
| 11 | Zero N+1 query regression (single bulk query) | SQL listener profiling & EXPLAIN QUERY PLAN | PASS |
| 12 | Query latency < 200ms on live & 200-product synthetic DB | Benchmark script: ~16.9ms live, ~150.3ms synthetic | PASS |
| 13 | Full suite validation clean (backend pytest, Vitest, tsc, lint, build) | Automated verification suite | PASS |
| 14 | Durable architecture updated with Phase 2 invariants | Inspection of `ARCHITECTURE.md` | PASS |
