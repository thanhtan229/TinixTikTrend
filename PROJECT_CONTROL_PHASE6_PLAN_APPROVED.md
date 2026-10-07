# Project Control Phase 6 Plan Approval Record

- **Date:** 2026-10-07
- **Role:** `00 — Project Control & Roadmap`
- **Decision:** `PHASE 6 PLAN APPROVED & IMPLEMENTATION AUTHORIZED`
- **Phase:** Phase 6 — Affiliate Economics & Profitability Intelligence
- **Scope:** VND-only, manual-first Product Economics Scenarios
- **Authoritative Plan:** [`PHASE_6_PLAN.md`](PHASE_6_PLAN.md)
- **Approved Plan Revision Commit:** `4713fa422eb7f407b78995a9d453711910efc354`
- **Authoritative Acceptance Criteria:** `P6-AC-01` through `P6-AC-42` (42 criteria authoritative)
- **Accepted Research Artifact:** [`research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md`](research/PHASE_6_AFFILIATE_ECONOMICS_RESEARCH.md) (accepted under `8c3f8949b8c9e61691c2e2756557e9abadc035b5`)
- **Accepted Architecture Decision:** [`docs/architecture/ADR-005.md`](docs/architecture/ADR-005.md) (accepted under `d5fc2519abc8c67cc3751d62939fd7213b9794a6`)
- **Research Gate:** `CLOSED / ACCEPTED`
- **Architecture Gate:** `CLOSED / ACCEPTED`
- **Plan Gate:** `APPROVED`
- **Implementation Status:** `AUTHORIZED`
- **Current Product Compatibility:** `"2"` (Phase 5 product state unchanged until schema implementation)
- **Target Phase 6 Compatibility:** `"3"` (upon additive schema implementation)
- **Previous Release State:** Phase 5 source-release qualification remains **READY WITH DOCUMENTED NON-BLOCKING ISSUES** for the supported **Windows / local / source-based runtime** (qualified repository revision: `6e218929e3ff3ae091da1582de48fa0582802d8a`, qualified product-code revision: `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98`). Approving Phase 6 plan and authorizing implementation does not invalidate the qualified Phase 5 release.

---

## 1. Approval Decision

Project Control has formally reviewed the revised Phase 6 implementation plan [`PHASE_6_PLAN.md`](PHASE_6_PLAN.md) against Project Control Findings A–N and all accepted research and architectural constraints.

1. **Findings Remediated:** All 14 findings (A through N) have been thoroughly addressed and durably frozen:
   - **Finding A:** Integer ratio rounding $(2N + D) // (2D)$ and integer ceiling division $(A + B - 1) // B$; no binary float division.
   - **Finding B:** Safe-integer bounds guaranteeing lossless JSON/TS representations within `Number.MAX_SAFE_INTEGER`; percentage to bps conversion precision (max 2 decimal places, fractional bps rejected).
   - **Finding C:** Deterministic SQLite concurrency contract (`BEGIN IMMEDIATE`), bounded retries, error mapping to HTTP 409, and 8 deterministic barrier test cases.
   - **Finding D:** Strict provenance mutation contract preventing client forgery of proxy sources/timestamps.
   - **Finding E:** Deterministic duplicate semantics requiring unique caller-supplied name.
   - **Finding F:** Clarified product economics query budget ($\le 1$ scenario query, $\le 2$ total SQL queries).
   - **Finding G:** Authoritative offline launcher-owned restore (`RESTORE.bat`) acceptance under ADR-004.
   - **Finding H:** Safe diagnostics reporting row count only; zero sensitive financial data leakage.
   - **Finding I:** Operator documentation deliverables (`ARCHITECTURE.md`, `README.md`).
   - **Finding J:** Comprehensive automated frontend integration test specifications.
   - **Finding K:** Mandatory 12-step manual QA matrix.
   - **Finding L:** Performance benchmark methodology on 200-product/5,000-snapshot fixture with max/worst $<200\text{ms}$ hard gate.
   - **Finding M:** Explicit repository virtual environment interpreter invocation (`backend\.venv\Scripts\python.exe`).
   - **Finding N:** Full 42-item acceptance criteria matrix (`P6-AC-01` to `P6-AC-42`).
2. **Plan Gate Updated:** `APPROVED`.
3. **Implementation Authorized:** Phase 6 implementation is formally **AUTHORIZED** to proceed strictly in accordance with [`PHASE_6_PLAN.md`](PHASE_6_PLAN.md).

---

## 2. Authoritative Acceptance Criteria Surface

The 42 criteria defined in [`PHASE_6_PLAN.md`](PHASE_6_PLAN.md) are frozen and authoritative:
- **P6-AC-01 through P6-AC-03:** Domain separation, attribution inference prohibition, and manual-first source baseline.
- **P6-AC-04 through P6-AC-08:** Single table persistence, safe-integer bounds validation, null preservation (unknown $\ne$ 0), unique scenario name, and quarantine exclusion.
- **P6-AC-09 through P6-AC-19:** Default scenario invariants, atomic switching, deterministic promotion on delete, partial unique index enforcement, and deterministic concurrency race test matrix (Cases 1–8).
- **P6-AC-20 through P6-AC-26:** Exact integer ratio rounding, pure calculation formulas, fixed campaign cost null propagation, unit contribution margin, break-even integer ceiling division, expected campaign metrics, and zero persisted derived calculations.
- **P6-AC-27 through P6-AC-31:** Frozen observed-price proxy validation, proxy immutability against crawlers, provenance reset on manual base edit, duplicate semantics, and explicit price rebase.
- **P6-AC-32 through P6-AC-35:** Product Detail UX, Collections integration ($\le 3$ SQL queries), Compare integration ($\le 4$ SQL queries), and sub-200ms performance benchmark gate.
- **P6-AC-36 through P6-AC-39:** Additive bootstrap `"2" \to "3"`, rejection of version-2 backups, pre-restore safety backup/atomic replacement/rollback, and version-3 backup round-trip integrity.
- **P6-AC-40 through P6-AC-42:** Safe diagnostics privacy, operator documentation deliverables, and full test/health/integrity clean execution.

---

## 3. Implementation Guardrails

1. **No Scope Creep:** Coding agents must not invent unapproved features (e.g. Creator Center scraping, multi-currency, accounting/taxes, automatic crawler rate ingestion, economics alerts).
2. **Preserve Phase 1–5 Invariants:** Trend Score, evidence confidence, Watchlist monitoring, post-commit alert evaluation, same-version restore, and Saved Views V1 schemas remain completely untouched.
3. **Isolated Test Execution:** All destructive bootstrap, upgrade, and restore tests must execute against isolated file-backed SQLite instances (`tmp_path`), NEVER against `backend/affiliate.db`.
