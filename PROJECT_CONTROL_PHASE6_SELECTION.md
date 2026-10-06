# Project Control Phase 6 Selection Record

- **Date:** 2026-10-06
- **Selected Phase:** Phase 6 — Affiliate Economics & Profitability Intelligence
- **Phase 6 Status:** `SELECTED / RESEARCH REQUIRED`
- **Research Gate:** `OPEN / RESEARCH REQUIRED`
- **Research Status:** `NOT YET COMPLETE`
- **Phase Plan Status:** `NOT STARTED`
- **Implementation Status:** `NOT AUTHORIZED`
- **Acceptance Criteria:** `NONE DEFINED YET` (no Phase 6 acceptance criteria exist yet)
- **Previous Release State:** Phase 5 release qualification remains **READY WITH DOCUMENTED NON-BLOCKING ISSUES** for the supported **Windows / local / source-based runtime** (qualified repository revision: `6e218929e3ff3ae091da1582de48fa0582802d8a`; qualified product-code revision: `5db2e0e5e6c405bb2b42c78dc1759a60a4e8de98`; latest release-state reconciliation commit: `ef09b710bebc21df4cb64ff89a31a95a6ec46dbb`). Selection of Phase 6 does not invalidate the qualified Phase 5 release.

---

## Selection Decision & Intent

Project Control has formally selected **Phase 6 — Affiliate Economics & Profitability Intelligence** as the next product development phase.

### Selection Intent
Extend the current decision workflow from:
`organize → review → compare → decide`
toward:
`evaluate economics → compare commercial attractiveness → prioritize affiliate opportunities`
without changing existing Trend Score, Watchlist monitoring semantics, crawler behavior, or Phase 5 Collection/Compare authority.

---

## Research Gate & Planning Policy

- **Phase 6 Status:** `SELECTED / RESEARCH REQUIRED`
- **Research:** `NOT YET COMPLETE`
- **Plan:** `NOT STARTED`
- **Implementation:** `NOT AUTHORIZED`
- **Policy:** Research must precede planning. **Phase 6 planning is blocked on completion and Project Control review of research.**
- **Research Location:** Substantial research should occur in `01 — Architecture & Repo Research`.

---

## Expected Research Questions (Research Gate Rationale)

The following research questions are recorded as the research gate rationale (not answered during selection/reconciliation):

Research must determine at least:
1. **Authoritative data sources:** Authoritative commission/affiliate data sources available to this local product.
2. **Regional commission/fee semantics:** VN-specific commission and fee semantics where relevant.
3. **Extraction vs. manual entry:** Whether commission data can be reliably extracted, entered manually, or both.
4. **Terminology and formulas:** Revenue and profitability terminology and calculation formulas.
5. **Economic distinction:** Clear architectural and calculation distinction between:
   - Product selling price;
   - Gross merchandise value (GMV) / revenue proxies;
   - Affiliate commission rate;
   - Estimated affiliate earnings;
   - User-entered product/sample/content/ad costs;
   - Contribution/profit estimates.
6. **False-precision avoidance:** Missing/null/estimated economics semantics and strict avoidance of false precision.
7. **Temporal dynamics:** Time-varying price and commission semantics.
8. **Entity ownership & modeling:** Whether economics state belongs to `Product`, `CollectionItem`, or a separate scenario/assumption entity.
9. **Scenarios:** Whether multiple economic scenarios per Product are required.
10. **Persistence & history:** Persistence and history requirements for economic assumptions and metrics.
11. **Backup / restore compatibility:** Backup/restore compatibility consequences.
12. **Database bootstrap:** Schema and bootstrap implications.
13. **Compatibility marker:** Effect on the current portable backup compatibility version (`"2"`).
14. **Workspace integration:** Integration with Collections, Saved Views, and Compare.
15. **Comparison surface:** Whether Compare should display economics or a separate economics comparison surface is preferable.
16. **Performance & query budgets:** Performance and query constraints (preserving Zero N+1 budgets).
17. **Frontend UX:** Frontend UX interaction patterns, modal/tray components, and inputs.
18. **Security & privacy:** Security and privacy implications (local data boundaries, financial privacy).
19. **External dependencies:** External-network and runtime dependency implications.
20. **ADR requirement:** Whether a dedicated Architectural Decision Record (ADR) is required.
21. **Out-of-scope boundaries:** Explicit out-of-scope boundaries.

---

## Preserved Architectural Boundaries

The following architecture principles and invariants must not be changed or weakened:
- `Watchlist = monitoring`;
- `Collections = decision organization`;
- `WatchlistItem.notes` provenance ownership;
- `CollectionItem.notes` decision-note ownership;
- Phase 2 authoritative Trend Score and evidence semantics (economics data must NOT modify or contaminate Trend Score);
- Phase 3 alert semantics;
- Phase 4 same-version backup policy;
- Phase 5 Saved View contracts;
- Transient Compare semantics;
- Shared Compare `as_of_utc`;
- Compatibility version `"2"` remains active until research/planning explicitly determines otherwise.

---

## Preserved Technical Debt & Deferred Scope

The following accepted non-blocking debt and deferred scope items are preserved unchanged:
- 1 High `source-map-js` advisory in the production dependency graph (`GHSA-68fv-2mgg-jv7q`), presently assessed build-time-only / non-runtime-reachable;
- Development-only `braces` advisory (`GHSA-vfj7-8cjw-p6xm`) in devDependencies;
- `StarletteDeprecationWarning` during test runs;
- Runtime `PRAGMA foreign_keys = 0` (`OFF`);
- Broad discovery and CAPTCHA bypass limitations deferred;
- Standalone executable packaging deferred;
- Cloud synchronization and multi-user capabilities deferred;
- Previous Phase 5 out-of-scope items unless Phase 6 later explicitly selects one through approved scope.

---

## Next Steps

1. Open `01 — Architecture & Repo Research` for Phase 6 Affiliate Economics & Profitability Intelligence.
2. Complete research and submit findings for Project Control review.
3. Only upon Project Control acceptance of research may planning commence in `PHASE_6_PLAN.md`.
4. Implementation remains strictly unauthorized.
