# Project Control — Phase 7 Package Review

- **Date:** 2026-10-07
- **Role:** `00 — Project Control & Roadmap`
- **Review basis:** Clean `main` at `5d7d4752e7344005cd4da13a0d36524ed064f3c0`; 31 local commits ahead of `origin/main`, none behind.
- **Phase 6:** Remains closed and release-qualified as recorded at the verified baseline. Compatibility remains `"3"`.
- **Phase 7 implementation at review:** No Phase 7 production implementation, runtime tests, or schema additions found. The pre-existing `ProductVideoLink` model is legacy association scaffolding and is not Phase 7 functionality.
- **Decision:** Earlier Phase 7 research, ADR and plan acceptance records are **SUPERSEDED / WITHDRAWN PENDING CORRECTION**. Phase 7 remains selected, but implementation is **NOT AUTHORIZED** until corrected research, ADR and plan are independently reviewed and their gates reconciled below.

## Repository and implementation verification

The worktree was clean. `HEAD` is the stated Phase 6 final release-state reconciliation and is a descendant of all three Phase 6 acceptance/qualification commits. The Phase 6 product state and compatibility marker match `PROJECT_STATUS.md`.

`ProductVideoLink` already exists as a Phase 1 mapping table with `product_id`, `external_video_id`, creator/source/confidence fields and timestamps. It has no video metadata registry or metric snapshots. Phase 7 must reuse the mapping concept rather than add a second product-video association table.

## Findings against the provisional package

1. **Approval state conflicts.** `PROJECT_STATUS.md` and its top-level next action say Phase 7 is provisional and unauthorized, while the plan and acceptance records claim research, ADR and implementation plan approval. The latest reconciled Phase 6 status is the controlling state; the inconsistent Phase 7 approvals are not accepted as authority.
2. **External data capability is overstated.** TikTok's documented oEmbed endpoint provides embed-oriented public metadata, not a documented historical or recurring engagement-metrics API. Research API access is restricted to approved, qualified research use. Display API video queries require user authorization and apply to the authorized user's videos. None is a generally available commercial source for arbitrary creators' metrics.
3. **Internal web payload assumptions are unsupported.** `__UNIVERSAL_DATA_FOR_REHYDRATION__`, `SIGI_STATE`, the proposed JSON paths and their metric fields are undocumented implementation details. They can change or be absent; the existing research presents them as stable facts without reproducible fixtures or a versioned public contract.
4. **Challenge fallback violates the established boundary.** Retrying a Security Check with Playwright and claiming session reuse as a mitigation is not evidence that the challenge can be served safely. The project architecture says a challenge fails the crawl without solving or bypassing it. Phase 7 must stop on 403/429, challenge pages and non-video responses, with no solver, stealth, challenge retry or automatic browser fallback.
5. **Association schema duplicates video identity.** `UNIQUE(product_id, video_id)` makes `product_videos` a per-product association, yet `video_snapshots` references that row. The same public video linked to two products would have duplicated metadata and histories. Reuse existing `ProductVideoLink` and keep one globally keyed video entity and its snapshots.
6. **Removal semantics conflict with history retention.** Cascading from an association to snapshots would erase global video history when a product link is detached. Detaching a product association must preserve video metadata and snapshots.
7. **Acceptance and performance requirements need correction.** The plan mixes a `<20 ms` target with a `<200 ms` hard gate and alternates data sizes. Define one repeatable representative benchmark and distinguish target from hard limit.
8. **Collection scope is unsupported.** Automatic PDP harvesting and scheduled refresh are asserted without verified source availability or evidence that product pages expose stable video links. Keep Phase 7 user-assisted linking and on-demand refresh; defer harvesting and background collection unless a later research pass proves a stable, permitted source.

## Corrected product decision

Keep Phase 7 selected because product-linked content signals are part of the approved product vision. Limit collection to an operator-entered public TikTok video URL and explicit on-demand refresh. Use only documented public metadata sources where they provide supported fields. An optional best-effort public-page parser may extract fields only from a normal, successful video response and must treat every field as nullable and schema-variant; it is not a guaranteed metric provider. No returned metric is fabricated or carried forward as a new observation. Challenges, access-denied responses, unavailable pages and unsupported payloads produce an explicit unavailable/blocked result and no metric snapshot.

Implement a global video identity keyed by canonical TikTok video ID, a separate product association (reusing `ProductVideoLink`), and snapshots tied to the global identity. Link removal preserves global snapshots. Content metrics remain orthogonal to product market scores and affiliate-economics assumptions. The feature must remain useful when TikTok exposes no metrics: retain the validated link and show metadata/availability honestly.

Official capability references:

- TikTok oEmbed: https://developers.tiktok.com/doc/embed-videos/
- Research API eligibility: https://developers.tiktok.com/products/research-api/
- Research API video query: https://developers.tiktok.com/doc/research-api-specs-query-videos/
- Display API overview: https://developers.tiktok.com/doc/display-api-overview/
- Display API video query: https://developers.tiktok.com/doc/tiktok-api-v2-video-query/

## Gate reconciliation

- **Selection gate:** `SELECTED / RESEARCH REQUIRED` remains valid; its next-action text is stale and will be reconciled.
- **Research gate:** Reopen. Replace unsupported guarantees with official capability evidence, explicit unknowns, and a fixture-backed feasibility boundary. Independent review is required before closure.
- **Architecture gate:** ADR-006 remains provisional and must be rewritten to match the corrected data source, challenge boundary, global video identity, and removal semantics. Independent review is required.
- **Plan gate:** Withdraw the existing approval. Replace its criteria and scope; conduct a separate plan-review pass. Implementation remains unauthorized until the review and approval are durably recorded.
- **Runtime:** Documentation-only review does not change code or runtime. No server restart is applicable at this gate.

This record supersedes conflicting Phase 7 status statements in earlier acceptance documents. Those historical records remain in Git for auditability.

## Final disposition

The corrected research, ADR-006, and plan were subsequently reviewed in a separate Project Control pass and approved for implementation. See [`PROJECT_CONTROL_PHASE7_PACKAGE_APPROVED.md`](PROJECT_CONTROL_PHASE7_PACKAGE_APPROVED.md); that record closes the pending gates above and authorizes implementation under `P7-AC-01` through `P7-AC-28`.
