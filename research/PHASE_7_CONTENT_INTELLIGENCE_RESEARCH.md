# Phase 7 Research — TikTok Content Signals

Updated 2026-10-07. This revision supersedes the original claims that internal page JSON and Playwright challenge fallback provide a stable collection path. Research accepted as part of the independently reviewed Phase 7 package in [`PROJECT_CONTROL_PHASE7_PACKAGE_APPROVED.md`](../PROJECT_CONTROL_PHASE7_PACKAGE_APPROVED.md).

## Question and conclusion

Can this local application reliably collect arbitrary public TikTok video metrics using a supported, general-purpose interface?

**No supported unrestricted metrics interface was found.** Phase 7 can safely provide curated product-video associations, metadata where documented, and optional best-effort observations from ordinary public responses. Metrics availability is not guaranteed, so the feature must explicitly support links with no metrics and must never turn an unavailable value into zero or reuse stale data as a new observation.

## Official interfaces

- TikTok [oEmbed documentation](https://developers.tiktok.com/doc/embed-videos/) describes metadata and embed markup for a public video URL. It is useful for presentation metadata, not a documented recurring metrics/history feed.
- TikTok [Research API eligibility](https://developers.tiktok.com/products/research-api/) limits access to approved qualified research contexts. Its [video query](https://developers.tiktok.com/doc/research-api-specs-query-videos/) is not an assumed production dependency for this local affiliate tool.
- TikTok [Display API overview](https://developers.tiktok.com/doc/display-api-overview/) and [video query](https://developers.tiktok.com/doc/tiktok-api-v2-video-query/) describe user-authorized access to videos belonging to an authorized account. This does not provide arbitrary-creator lookup.
- Therefore none of these is a drop-in public commercial API for arbitrary videos.

## Internal/public-page behavior

The former research described `__UNIVERSAL_DATA_FOR_REHYDRATION__`, `SIGI_STATE`, nested JSON paths and metric names as if they were a documented stable interface. They are not established by TikTok's public API contract. Presence, semantics, and response fields can vary by page, region, login state and time. A successful HTML response may contain no parseable video data; a challenge response is not a video record.

Any optional page parser must be treated as a best-effort adapter:

- accept only an expected TikTok video URL and a normal successful response;
- parse only recognized fields, preserving missing fields as null;
- reject challenge/interstitial and unsupported shapes without a snapshot;
- record source/status and capture time;
- never persist raw HTML, cookies, or tokens;
- use sanitized, versioned fixtures; do not claim live reliability based on a single response.

This review did not treat internal field names as guaranteed or infer access to a supported metrics endpoint from them. Availability remains an implementation-time feasibility test. If no safe fixture-backed parser can be validated, ship association and documented metadata behavior with metrics unavailable rather than circumventing platform controls.

## Repository findings

- Existing `TikTokHttpClient` validates TikTok destinations and has retry/backoff behavior for shop collection. Phase 7 must use a dedicated conservative policy: no retry for 403/429 or challenge results, no Playwright escalation, no use of the stored operator session.
- The product collector's Playwright path can fail with `BlockedError` on Security Check. Architecture documentation prohibits challenge solving or bypass. Phase 7 inherits this boundary.
- `ProductVideoLink` already stores product association, external video ID, creator, source, confidence and timestamps. It must be reused; adding another association table would duplicate the domain.
- No Phase 7-specific model, endpoint, collector, UI, schema table or runtime test existed at the verified Phase 6 baseline.
- Project instructions require local Windows runtime, SQLite, no paid service, no broad scraping, and no fabricated data.

## Data and association design implications

A single TikTok video may be linked to multiple products. Store one global video identity and one observation history per TikTok video ID; associate products through `ProductVideoLink`. Detaching a link must not erase shared history. Restrict metadata to the fields needed by the UI and analysis. Never download media binaries.

Collection is operator initiated and one video at a time. PDP showcase harvesting, broad search, scheduled/batch refresh, automatic product attribution, cookies, and browser fallback are deferred. An operator-supplied link means “associated by operator,” not verified evidence that the video sells that product.

## Metrics semantics

For a metric `m`, calculate velocity only when two successful observations with non-null values exist and the elapsed time falls within a declared comparison window. Preserve actual elapsed seconds. Missing observations or metrics yield null. If a source metric decreases, retain the raw observations and mark the derived result anomalous; do not silently clamp and discard the decrease. A single capture has no velocity.

Engagement rate is available only when the response supplies the necessary counts and a positive view count. Values are platform-reported public counters, not sales, conversions, creator payout, or verified product attribution.

## Security, privacy, and reliability

- Validate `https` URLs and exact TikTok host/path forms; reject credentials, unexpected ports, malformed IDs, and non-TikTok destinations.
- Revalidate every redirect and public network destination using existing URL safety utilities.
- Do not read `backend/.local/tiktok-session.json` for video retrieval.
- Stop on 403, 429, challenge/interstitial, unsupported content, or unsafe redirect. No automatic retries, CAPTCHA handling, stealth, signature generation, or challenge-solving.
- Bound time, response size, and request frequency. Do not store raw response bodies.
- Allow only safe public HTTPS image URLs and render them through the application's established safe image/link behavior.
- Keep user-visible source, last attempt, and unavailable reason distinct from metric values.

## Decision and remaining validation

Recommend a narrow Phase 7: manual association, explicit single-video refresh, best-effort metadata/counters, shared identity/history, clear unavailable states, and no score integration. This aligns with the product vision without making a platform reliability claim the repository cannot support.

Before implementation, the independent architecture and plan reviews must confirm this boundary. During implementation, verify parser behavior only against sanitized fixtures and an ordinary public response if safely available; do not make successful live scraping a release prerequisite. If the optional parser cannot be validated, disable it and retain the association workflow.
