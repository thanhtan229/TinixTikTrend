# Project Control Phase 7 Plan Approval Record

> **Approval withdrawn 2026-10-07.** The plan was based on unsupported collection assumptions and a per-association snapshot schema. It is replaced by the draft [`PHASE_7_PLAN.md`](PHASE_7_PLAN.md); implementation is **NOT AUTHORIZED** pending independent review and a new durable approval. See [`PROJECT_CONTROL_PHASE7_PACKAGE_REVIEW.md`](PROJECT_CONTROL_PHASE7_PACKAGE_REVIEW.md).

- **Date:** 2026-10-07
- **Authority / Role:** `00 — Project Control & Roadmap`
- **Decision:** `PHASE 7 PLAN APPROVED & IMPLEMENTATION AUTHORIZED`
- **Phase:** Phase 7 — TikTok Content Intelligence & Video Signals
- **Scope:** HTTP-First, User-Assisted Linking, Orthogonal Content Velocity Analytics
- **Authoritative Plan:** [`PHASE_7_PLAN.md`](PHASE_7_PLAN.md)
- **Authoritative Acceptance Criteria:** `P7-AC-01` through `P7-AC-39` (39 authoritative criteria)
- **Accepted Research Artifact:** [`research/PHASE_7_CONTENT_INTELLIGENCE_RESEARCH.md`](research/PHASE_7_CONTENT_INTELLIGENCE_RESEARCH.md) (accepted under [`PROJECT_CONTROL_PHASE7_RESEARCH_ACCEPTED.md`](PROJECT_CONTROL_PHASE7_RESEARCH_ACCEPTED.md))
- **Accepted Architecture Decision:** [`docs/architecture/ADR-006.md`](docs/architecture/ADR-006.md) (accepted under [`PROJECT_CONTROL_ADR006_ACCEPTED.md`](PROJECT_CONTROL_ADR006_ACCEPTED.md))
- **Research Gate:** `CLOSED / ACCEPTED`
- **Architecture Gate:** `CLOSED / ACCEPTED`
- **Plan Gate:** `APPROVED`
- **Implementation Status:** `AUTHORIZED`
- **Current Product Compatibility:** `"3"` (Phase 6 product state unchanged until schema implementation)
- **Target Phase 7 Compatibility:** `"4"` (upon additive schema implementation)
- **Previous Release State:** Phase 6 source-release qualification remains **`READY WITH DOCUMENTED NON-BLOCKING ISSUES`** for the supported **Windows / local / source-based runtime** (qualified repository revision: `ed442bf3c9bfaabaef01c054d2df9e9771c47bc2`, qualified product-code revision: `2f3e4b4783307bdfa5e5ffbc7cfd49576572eb0f`). Approving Phase 7 plan and authorizing implementation does not invalidate the qualified Phase 6 release.

---

## 1. Approval Decision

Project Control has formally reviewed the Phase 7 implementation plan [`PHASE_7_PLAN.md`](PHASE_7_PLAN.md) against all accepted research conclusions, ADR-006 architectural invariants, and repository standards.

1. **Plan Thoroughness & Compliance:**
   - Strict metric independence: Content velocity metrics do NOT modify or contaminate Phase 2 Trend Score or confidence.
   - Attribution boundary: Clear disclaimers that video views/likes represent public social reach, not creator sales or guaranteed affiliate payout.
   - Zero media binary downloads/storage: No local MP4/WebM/audio files are created or cached.
   - Mathematical precision: 24h candidate window bounded to $[20\text{h}, 28\text{h}]$, non-negative clamping with anomaly flag, exact rational rounding $(2N + D) // (2D)$.
   - Additive database schema: `product_videos` and `video_snapshots` with foreign key cascades, unique constraints, and composite indices.
   - Disaster recovery safety: Advance of compatibility marker `"3" → "4"` with deterministic rejection of v1–v3 backups under ADR-004 same-version restore rules.
   - Query budget: Product detail view executes $\le 3$ SQL queries; zero N+1 queries.
   - Workstreams: 10 structured workstreams (WS-0 to WS-9) with comprehensive test matrix.
2. **Plan Gate Updated:** `APPROVED`.
3. **Implementation Authorized:** Phase 7 implementation is formally **AUTHORIZED** to proceed strictly in accordance with [`PHASE_7_PLAN.md`](PHASE_7_PLAN.md).

---

## 2. Authoritative Acceptance Criteria Matrix

All 39 acceptance criteria defined in [`PHASE_7_PLAN.md`](PHASE_7_PLAN.md) are frozen and authoritative:
- **P7-AC-01 to P7-AC-03:** Domain separation, attribution disclosure, and zero media binary storage.
- **P7-AC-04 to P7-AC-09:** Exact 24h views/likes/engagement velocity mathematics, null-safety ($< 20\text{h}$ evaluates to null), non-negative clamping, and integer ratio rounding.
- **P7-AC-10 to P7-AC-15:** Model definitions (`ProductVideo`, `VideoSnapshot`), unique constraints `UNIQUE(product_id, video_id)`, composite index `(video_id, captured_at DESC)`, cascading deletes, and additive schema bootstrap.
- **P7-AC-16 to P7-AC-21:** TikTok video URL validation, HTTP-first SSR JSON extraction (`__UNIVERSAL_DATA_FOR_REHYDRATION__`), Playwright fallback, unavailable handling, PDP showcase harvesting, and on-demand refresh.
- **P7-AC-22 to P7-AC-27:** REST API endpoints (`GET/POST/DELETE/refresh`), 409 duplicate rejection, and quarantine protection.
- **P7-AC-28 to P7-AC-31:** Disaster recovery compatibility version `"4"`, v1–v3 rejection, v4 hot backups, and host-bound session isolation.
- **P7-AC-32 to P7-AC-34:** Performance query budgets ($\le 3$ SQL queries on detail), zero N+1 queries, and sub-20ms benchmark latency.
- **P7-AC-35 to P7-AC-39:** Frontend Product Videos section, responsive card layout, velocity badges, Add Video modal, and transparency disclaimer banner.

---

## 3. Next Lifecycle State

- **Current State:** Phase 7 Plan Approved (`PLAN APPROVED / IMPLEMENTATION AUTHORIZED`).
- **Active Role for Next Step:** `PHASE IMPLEMENTATION`.
- **Implementation Strategy:** Execute Workstreams WS-0 through WS-9 in strict dependency order without skipping validation steps.
