# MASTER BUILD PROMPT — TikTok Shop Affiliate Trend Hunter

You are acting as a Senior Full-Stack Engineer, Data Engineer, Product Architect, and Technical Researcher.

Your task is to build a local-first application that helps identify promising TikTok Shop products for affiliate marketing.

IMPORTANT COMMUNICATION RULE:

- All technical planning, explanations, progress updates, tradeoffs, questions, summaries, and final responses to me MUST be written in Vietnamese.
- Source code, variable names, function names, database fields, commit messages, file names, comments, and technical identifiers SHOULD remain in English unless Vietnamese is explicitly more appropriate.
- Do not reply to me in English unless I explicitly request English.

---

# 1. Product Goal

Build an application that answers this core question:

**“Which TikTok Shop products should I consider promoting as an affiliate today?”**

The application is not intended to become a general-purpose web scraper.

The application should focus on discovering useful signals such as:

- Newly detected products
- Products with rapidly increasing sales
- Best-selling products
- Products with increasing review activity
- Products showing early trend signals
- Products with increasing creator/video activity
- Products with strong affiliate commission potential
- Products that may be becoming viral before they become saturated

The long-term product vision is:

```text
TikTok Shop Product Data
        +
TikTok Content Data
        +
Affiliate Data
        ↓
Trend Intelligence
        ↓
Affiliate Opportunity Score
        ↓
"What should I promote today?"
```

---

# 2. Core Product Principles

Always prioritize:

```text
useful signal > raw data volume
```

Do not optimize for collecting millions of products.

The product is successful if it can surface a small number of genuinely useful opportunities.

For example:

```text
Top Rising Products
Top New Products
Top Best Sellers
Top Affiliate Opportunities
```

The goal is decision support, not data hoarding.

---

# 3. Build Strategy

Build the application from scratch.

Do NOT fork an external repository and turn it into the application.

External repositories may be researched and selectively adapted, but:

- application architecture must remain ours
- database schema must remain ours
- analytics logic must remain ours
- APIs must remain ours
- frontend must remain ours
- collector interfaces must remain ours

External repositories are technical references only.

---

# 4. Reference Repository #1 — TikTok Shop Product Intelligence

Primary research repository:

```text
https://github.com/MisterSeitz/TikTok-Shop-Product-and-Creator-Tracker
```

This repository is the main technical reference for:

**Phase 1 — TikTok Shop Product Intelligence**

Research it for:

- Playwright architecture
- Browser startup and shutdown
- Browser context reuse
- Session reuse
- Cookie handling
- Region handling
- TikTok Shop VN compatibility
- Product discovery
- Product detail extraction
- Product ID extraction
- Seller/shop extraction
- Price extraction
- Rating extraction
- Review extraction
- Stock/availability extraction if available
- Creator-related product data
- Product-linked videos if available
- Snapshot/change detection
- Retry logic
- Error handling
- Proxy abstraction if present
- Request patterns
- Network/XHR behavior

Before reusing any concept, determine how the repository actually obtains data.

Specifically determine whether it relies on:

```text
DOM scraping

OR

Network/XHR interception

OR

JSON endpoints

OR

TikTok web/internal endpoints

OR

a combination of them
```

Do not blindly reproduce browser automation.

If the repository loads a TikTok Shop page in Playwright but the actual product data is returned by JSON/XHR requests, investigate whether our implementation can instead use:

```text
Playwright
    ↓
bootstrap browser session
    ↓
cookies / tokens
    ↓
httpx
    ↓
JSON endpoint
```

This is preferred when technically viable.

The goal is to minimize:

- CPU usage
- RAM usage
- browser rendering
- unnecessary page navigation
- crawler runtime

---

# 5. Reference Repository #2 — TikTok Content Intelligence

Secondary research repository:

```text
https://github.com/davidteather/TikTok-Api
```

This repository is for:

**Phase 2 — TikTok Content Intelligence**

Do NOT use it as the primary TikTok Shop product collector.

Research it for:

- TikTok video retrieval
- TikTok creator/user retrieval
- video statistics
- views
- likes
- comments
- shares
- video creation timestamp
- hashtags
- trending/discovery methods if currently usable
- session architecture
- Playwright usage
- TikTok web requests
- pagination
- creator metrics
- video metrics

The future goal is to enrich TikTok Shop product data with content signals.

Example:

```text
TikTok Shop Product
        │
        ├── Video A
        │     ├── views
        │     ├── likes
        │     ├── comments
        │     └── shares
        │
        ├── Video B
        │
        └── Creator
              ├── followers
              └── engagement
```

This will allow us to calculate:

```text
views_velocity
video_growth
creator_growth
engagement_growth
```

Do not implement this phase before Product Intelligence V1 is stable.

---

# 6. Important Product ↔ Video Mapping Rule

Never assume that TikTok video data automatically identifies which TikTok Shop product a video is selling.

Treat this as a separate domain problem:

```text
Product
   ↕
Video
```

Create an abstraction for future mapping.

Suggested model:

```text
product_video_links
```

Potential fields:

```text
id
product_id
external_video_id
creator_id
source
confidence
first_seen_at
last_seen_at
```

Possible mapping sources may include:

- product-linked videos from TikTok Shop
- creator-linked products
- TikTok Shop product pages
- TikTok video metadata
- official affiliate/product relationships if available later

Do not map a product and video purely by keyword similarity unless it is explicitly treated as a heuristic.

If mapping confidence is uncertain, store a confidence score.

---

# 7. Cost Constraints

The MVP must be as close to zero-cost as possible.

It should run entirely on a local Windows PC.

Do NOT require:

- paid scraping APIs
- managed scraping platforms
- cloud servers
- cloud databases
- distributed queues
- external paid data providers

The MVP should work using:

```text
Local PC
+
Python
+
Playwright
+
HTTP client
+
SQLite
```

A proxy must NOT be required initially.

However, proxy support should be abstracted so it can be added later if necessary.

---

# 8. Technology Stack

Backend:

- Python 3.12+
- FastAPI
- SQLAlchemy
- Pydantic
- APScheduler
- httpx
- Playwright
- SQLite
- pytest

Frontend:

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

Charts:

- Recharts

Database:

- SQLite for MVP

The database layer must be designed cleanly enough to allow future migration without rewriting analytics.

---

# 9. High-Level Architecture

```text
                    TikTok Shop
                         │
                         ▼
                Collector Layer
                         │
              ┌──────────┴──────────┐
              │                     │
             HTTP               Playwright
          preferred              fallback
              │                     │
              └──────────┬──────────┘
                         ▼
                  Normalized Data
                         │
                         ▼
                      SQLite
                         │
                         ▼
                    Snapshots
                         │
             ┌───────────┼────────────┐
             ▼           ▼            ▼
          New        Rising      Best Sellers
                         │
                         ▼
                    Trend Score
                         │
                         ▼
                     FastAPI
                         │
                         ▼
                  Next.js Dashboard
```

Future:

```text
TikTok Shop Product Intelligence
              +
TikTok Content Intelligence
              +
Affiliate Data
              ↓
Affiliate Opportunity Engine
```

---

# 10. Project Structure

Use a structure similar to:

```text
tiktok-affiliate-trend-hunter/

backend/
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── products.py
│   │   ├── trends.py
│   │   ├── dashboard.py
│   │   └── crawler.py
│   │
│   ├── collectors/
│   │   └── tiktok_shop/
│   │       ├── client.py
│   │       ├── browser.py
│   │       ├── session.py
│   │       ├── discovery.py
│   │       ├── search.py
│   │       ├── product.py
│   │       ├── parser.py
│   │       ├── schemas.py
│   │       └── exceptions.py
│   │
│   ├── models/
│   │   ├── product.py
│   │   ├── product_snapshot.py
│   │   ├── crawl_run.py
│   │   ├── category.py
│   │   └── product_video_link.py
│   │
│   ├── services/
│   │   ├── product_service.py
│   │   ├── snapshot_service.py
│   │   ├── crawl_service.py
│   │   └── trend_service.py
│   │
│   ├── analytics/
│   │   ├── deltas.py
│   │   ├── new_products.py
│   │   ├── best_sellers.py
│   │   ├── rising_products.py
│   │   ├── scoring.py
│   │   └── normalization.py
│   │
│   ├── scheduler/
│   │   └── jobs.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── migrations/
│   │
│   └── core/
│       ├── config.py
│       ├── logging.py
│       └── exceptions.py
│
├── tests/
│   ├── fixtures/
│   ├── analytics/
│   ├── api/
│   └── collectors/
│
├── requirements.txt
├── .env.example
└── README.md

frontend/
├── app/
├── components/
├── lib/
├── hooks/
├── types/
└── package.json

docs/
├── architecture/
└── research/
    ├── misterseitz-analysis.md
    └── tiktok-api-analysis.md

research/
├── misterseitz/
└── tiktok-api/
```

Do not put external repository source directly inside production application modules.

---

# 11. Collector Design

The collector must be isolated from:

- analytics
- API routes
- UI
- business scoring
- database internals

Business logic must never directly depend on Playwright.

Define an internal normalized collector interface.

Example concept:

```python
class TikTokShopCollector:
    async def discover_products(...):
        ...

    async def get_product(...):
        ...

    async def close(...):
        ...
```

The implementation may change later without affecting analytics.

---

# 12. HTTP First, Playwright Fallback

Do not assume every product requires browser rendering.

Use this strategy whenever technically possible:

```text
HTTP
 ↓
JSON/data available?
 ↓ yes
Parse directly

 ↓ no
Playwright fallback
```

Playwright should primarily be used for:

- browser session initialization
- cookies
- tokens
- JavaScript-required pages
- network inspection
- fallback crawling

Do NOT design:

```text
1 product
=
1 browser launch
```

Reuse:

- browser instance
- browser context
- cookies
- sessions

Avoid opening excessive tabs.

---

# 13. Product Model

Create a `products` table.

Minimum fields:

```text
id
platform
external_product_id

title
url
image_url

shop_id
shop_name

category

first_seen_at
last_seen_at

created_at
updated_at
```

`platform` should currently be:

```text
tiktok_shop
```

Use a unique constraint on the appropriate external product identity.

---

# 14. Product Snapshot Model

This is the most important table.

Create:

```text
product_snapshots
```

Fields should include:

```text
id
product_id
captured_at

price
original_price

sold_count
review_count
rating

stock_count
rank_position

creator_count
video_count

commission_rate
```

All unavailable metrics must be nullable.

Never fabricate missing data.

Do not overwrite historical snapshots.

---

# 15. Crawl Run Model

Create:

```text
crawl_runs
```

Suggested fields:

```text
id

started_at
finished_at

source
status

products_found
products_created
products_updated
snapshots_created

error_message
```

Possible status values:

```text
running
completed
partial
failed
```

---

# 16. Snapshot Philosophy

Each crawl should:

1. Discover products.
2. Normalize product data.
3. Upsert the product record.
4. Create a new snapshot.
5. Keep all previous snapshots.
6. Use snapshot differences for analytics.

Example:

```text
09:00 sold = 1,200
15:00 sold = 1,450
21:00 sold = 1,810
```

From this data calculate:

```text
6h sales delta
12h sales delta
24h sales delta
7d sales delta
```

Trend analysis must not depend only on lifetime sold count.

---

# 17. First Seen Semantics

`first_seen_at` means:

```text
the first time our system detected the product
```

It does NOT automatically mean:

```text
product published date
```

Never display:

```text
Published today
```

unless an actual product publication timestamp exists.

Use UI wording such as:

```text
First detected
```

---

# 18. Analytics V1

Implement these four primary views.

## 18.1 New Products

Based on:

```text
first_seen_at
```

Filters:

```text
last 24 hours
last 3 days
last 7 days
```

---

## 18.2 Best Sellers

Support ranking by:

```text
total sold
sold delta 24h
sold delta 7d
```

Do not confuse lifetime best sellers with currently rising products.

---

## 18.3 Rising Products

This is one of the most important analytics modules.

Calculate when data is available:

```text
sold_delta_6h
sold_delta_24h
sold_delta_7d

review_delta_24h
review_delta_7d
```

Also calculate sales acceleration when enough history exists.

Conceptually:

```text
previous period velocity
      ↓
current period velocity
      ↓
acceleration
```

Example:

```text
Previous 6h: +100 sold
Current 6h:  +600 sold

Strong acceleration
```

Avoid divide-by-zero.

Handle incomplete historical windows gracefully.

---

# 19. Trend Score V1

Create a normalized:

```text
Trend Score
0 → 100
```

The MVP score should consider:

```text
sales velocity
sales acceleration
review velocity
freshness
rating
```

Initial configurable weights may be:

```text
sales_velocity       40%
sales_acceleration   25%
review_velocity      15%
freshness            10%
rating               10%
```

These weights are only MVP heuristics.

Do not bury them inside application code.

Store scoring settings in a configuration module.

The scoring system must be easy to change later.

---

# 20. Trend Scoring Principle

Do not assume:

```text
high lifetime sales = trending
```

Example:

Product A:

```text
100,000 lifetime sold
+50 today
```

Product B:

```text
5,000 lifetime sold
+1,500 today
```

Product B should generally rank much higher in `Rising`.

Velocity and acceleration matter more than historical totals for trend discovery.

---

# 21. Future Content Intelligence Fields

Design models so these fields can be added later:

```text
video_count
creator_count

total_views
total_likes
total_comments
total_shares

video_count_delta
creator_count_delta

views_delta
likes_delta
comments_delta
shares_delta
```

Do not block V1 because these values are unavailable.

---

# 22. Phase 2 — Content Intelligence

Only start this after Product Intelligence V1 works reliably.

At that time, research:

```text
https://github.com/davidteather/TikTok-Api
```

Investigate:

- current working APIs
- video data retrieval
- creator data retrieval
- views
- likes
- comments
- shares
- timestamps
- hashtags
- trending methods
- session handling
- browser requirements
- pagination
- reliability
- limitations

Then build an internal content collector abstraction.

Do not allow core application logic to depend directly on TikTok-Api.

---

# 23. Content Velocity

Once video snapshots exist, calculate:

```text
views_velocity
likes_velocity
comments_velocity
shares_velocity

video_growth
creator_growth
```

Example:

```text
10:00 views = 100,000
16:00 views = 250,000
22:00 views = 600,000
```

The important signal is:

```text
rate of change
```

not just total views.

---

# 24. Combined Trend Intelligence

Long-term trend intelligence should combine:

```text
PRODUCT SIGNALS

sales velocity
sales acceleration
review velocity
freshness
```

with:

```text
CONTENT SIGNALS

video growth
creator growth
views velocity
engagement velocity
```

Concept:

```text
Product selling faster
        +
More creators promoting it
        +
Video views accelerating
        ↓
Potential early viral product
```

---

# 25. Phase 3 — Affiliate Intelligence

After reliable product and content signals exist, add affiliate metrics.

Potential inputs:

```text
commission_rate
affiliate availability
trend score
creator growth
video growth
competition
freshness
```

Create:

```text
Affiliate Opportunity Score
0 → 100
```

Conceptually:

```text
Opportunity Score
=
Trend Potential
×
Commission Potential
×
Competition Adjustment
```

Do not hard-code the final formula.

All weights must be configurable.

---

# 26. Dashboard

Primary route:

```text
/dashboard
```

Main sections:

```text
🔥 Trending
🚀 Rising
🆕 New Products
🏆 Best Sellers
```

Each product row/card should ideally show:

```text
image
title
shop
price

lifetime sold
sold 24h
sold 7d

review delta
trend score

first detected
last detected
```

Make the interface scan-friendly.

The user should be able to identify interesting products within seconds.

---

# 27. Product Detail Page

Route:

```text
/products/[id]
```

Display:

```text
Product information
Shop information

Trend Score
Sales metrics
Review metrics

First detected
Last detected

Sales history chart
Review history chart

Snapshot history
```

Time ranges:

```text
24h
7d
30d
```

Later add:

```text
Video activity
Creator activity
Affiliate metrics
```

---

# 28. Dashboard Filters

Support:

```text
time range
category
price range
minimum rating
minimum sales velocity
minimum trend score
```

Later:

```text
commission range
creator growth
video growth
views velocity
```

---

# 29. Scheduler

The app runs locally.

Default crawl schedule:

```text
08:00
12:00
16:00
20:00
00:00
```

The schedule must be configurable.

Support manual execution:

```text
Run crawler now
```

Prevent duplicate concurrent crawler runs.

If a crawl is already active:

```text
reject
OR
skip
```

with a clear status response.

---

# 30. Crawler Reliability

Implement:

- request timeout
- conservative rate limiting
- small random jitter
- exponential backoff
- retries
- session reuse
- structured logging
- graceful failure
- controlled concurrency

Configuration should include:

```text
MAX_CONCURRENCY
MAX_RETRIES

REQUEST_TIMEOUT

REQUEST_DELAY_MIN
REQUEST_DELAY_MAX
```

Use conservative defaults.

---

# 31. Crawler Safety and Scope

Do not implement aggressive anti-bot circumvention in the MVP.

Do not implement automated CAPTCHA bypass.

If access fails:

```text
log the failure
mark crawl status
preserve already collected data
do not fabricate missing data
```

Collector failure must never crash the entire application.

---

# 32. Backend API

Minimum endpoints:

```text
GET /api/health

GET /api/products
GET /api/products/{id}

GET /api/trends
GET /api/trends/rising
GET /api/trends/new
GET /api/trends/best-sellers

GET /api/dashboard

POST /api/crawler/run
GET /api/crawler/status
```

Implement:

- pagination
- sorting
- filtering
- Pydantic validation
- useful error responses

Do not put analytics logic directly inside API routes.

---

# 33. Research Workflow — MisterSeitz

Before implementing the real TikTok Shop collector, research:

```text
https://github.com/MisterSeitz/TikTok-Shop-Product-and-Creator-Tracker
```

Create:

```text
docs/research/misterseitz-analysis.md
```

Document:

```text
repository purpose
entry point
dependencies

Playwright initialization
browser lifecycle
context/session reuse

VN region support

TikTok Shop URLs used

DOM selectors
network requests
XHR/JSON requests

product fields collected
seller fields collected
creator fields collected
video fields collected

state/change tracking
retry behavior
error handling

proxy behavior

limitations
fragile components
```

For every meaningful component classify it as:

```text
REUSE CONCEPT
ADAPT
REWRITE
IGNORE
```

Do not copy code blindly.

---

# 34. HTTP Optimization Research

During MisterSeitz research, explicitly investigate:

```text
Can Playwright be reduced?
```

Look for:

- XHR calls
- fetch requests
- JSON payloads
- API endpoints
- query parameters
- session cookies
- required headers
- tokens

If possible, build:

```text
Browser bootstrap
      ↓
session/cookies
      ↓
HTTP collector
      ↓
Playwright only when needed
```

This is strongly preferred over full browser crawling.

---

# 35. Research Workflow — TikTok-Api

Do not begin this until Phase 2.

When Phase 2 begins, research:

```text
https://github.com/davidteather/TikTok-Api
```

Create:

```text
docs/research/tiktok-api-analysis.md
```

Document:

```text
architecture
session management
Playwright requirements
video retrieval
creator retrieval
statistics fields
pagination
rate limitations
current working functionality
fragile functionality
known limitations
```

Classify components as:

```text
REUSE CONCEPT
ADAPT
REWRITE
IGNORE
```

Again, do not couple the application directly to that repository.

---

# 36. Development Milestones

Do not generate the entire application at once.

Work milestone by milestone.

For every milestone:

1. Briefly explain in Vietnamese what you are about to build.
2. Implement it.
3. Run tests where possible.
4. Fix errors.
5. Summarize results in Vietnamese.
6. Continue to the next milestone.

Do not ask me for confirmation after every tiny step unless a decision materially changes product direction.

---

# 37. Milestone 1 — Project Foundation

Build:

Backend:

```text
FastAPI
SQLite
SQLAlchemy
Pydantic settings
logging
health endpoint
pytest
```

Frontend:

```text
Next.js
TypeScript
Tailwind CSS
shadcn/ui
```

Also create:

```text
README
.env.example
project structure
```

Verify that backend and frontend can run locally.

Do not implement the TikTok collector yet.

---

# 38. Milestone 2 — Database and Models

Implement:

```text
Product
ProductSnapshot
CrawlRun
Category
```

Prepare future-compatible:

```text
ProductVideoLink
```

Create migrations.

Add development fixtures only for testing.

Development fixtures must never be treated as live TikTok data.

---

# 39. Milestone 3 — Analytics Engine

Before live crawling works, implement and test:

```text
snapshot delta calculations
new product detection
best seller ranking
rising product ranking
trend scoring
```

Use controlled fixture data.

Write unit tests for:

```text
delta windows
missing snapshots
zero values
negative anomalies
growth calculation
score normalization
```

Analytics should work independently from TikTok.

---

# 40. Milestone 4A — Research MisterSeitz

Clone/read:

```text
https://github.com/MisterSeitz/TikTok-Shop-Product-and-Creator-Tracker
```

Create:

```text
docs/research/misterseitz-analysis.md
```

Do not implement production crawler code until this research is complete.

---

# 41. Milestone 4B — Build Our TikTok Shop Collector

Implement:

```text
collectors/tiktok_shop/
```

Use our own abstraction.

Prioritize:

```text
HTTP
```

when feasible.

Use:

```text
Playwright fallback
```

only where required.

Normalize all returned data into our internal schemas.

---

# 42. Milestone 4C — Validate TikTok Shop VN

Run against real TikTok Shop VN data.

Evaluate:

```text
successful requests
failed requests
products discovered
data completeness

runtime
CPU usage
RAM usage

browser usage
HTTP usage
```

Document real-world limitations.

Do not fake unavailable fields.

---

# 43. Milestone 5 — Snapshot Pipeline

Connect:

```text
collector
   ↓
product upsert
   ↓
snapshot creation
   ↓
analytics
```

Confirm:

- old snapshots remain
- restart preserves history
- duplicate product handling works
- timestamp logic works

---

# 44. Milestone 6 — Scheduler

Implement local scheduling.

Default:

```text
08:00
12:00
16:00
20:00
00:00
```

Implement:

```text
manual run
status
duplicate-run prevention
```

---

# 45. Milestone 7 — Frontend Dashboard

Build:

```text
Dashboard
Trending
Rising
New Products
Best Sellers
Product Detail
```

Use a clean data-dense interface.

Avoid unnecessary animation.

The tool is primarily an operational research dashboard.

---

# 46. Milestone 8 — Real MVP Validation

Use actual collected data over multiple crawl cycles.

Evaluate whether the application can reliably identify:

```text
products newly detected
products accelerating in sales
products increasing in reviews
products rising faster than high-lifetime-sales products
```

This milestone is essential.

Do not proceed to advanced Content Intelligence until the Product Intelligence MVP provides useful signals.

---

# 47. Phase 2 Milestone — Content Intelligence

Only after V1 is useful.

Research:

```text
davidteather/TikTok-Api
```

Then implement internal abstractions for:

```text
videos
creators
video metrics
creator metrics
```

Build product ↔ video mapping separately.

Do not tightly couple Product Intelligence and Content Intelligence.

---

# 48. Testing Requirements

Implement:

- analytics unit tests
- database tests
- API tests
- parser tests
- collector normalization tests

Do not require live TikTok requests for unit tests.

Save sanitized local fixtures for parser tests.

Examples:

```text
tests/fixtures/product_page.html
tests/fixtures/product_response.json
tests/fixtures/search_response.json
```

Do not store sensitive cookies or credentials in fixtures.

---

# 49. Logging

Use structured logging.

Useful event names:

```text
crawler_started
crawler_finished
crawler_failed

product_discovered
product_created
product_updated

snapshot_created

request_started
request_failed

parser_failed
```

Do not dump full HTML into console logs.

Do not log sensitive cookies or tokens.

---

# 50. Configuration

Create `.env.example`.

Suggested variables:

```text
APP_ENV=development

DATABASE_URL=sqlite:///./affiliate.db

TIKTOK_REGION=VN

CRAWL_SCHEDULE=08:00,12:00,16:00,20:00,00:00

MAX_CONCURRENCY=2
MAX_RETRIES=3

REQUEST_TIMEOUT=30

REQUEST_DELAY_MIN=1
REQUEST_DELAY_MAX=3

HEADLESS=true
```

Future optional variables may include proxy configuration.

Do not require them initially.

---

# 51. Windows Support

The MVP must work well on Windows.

Document setup clearly.

Backend setup example:

```bash
cd backend

python -m venv .venv

.venv\Scripts\activate

pip install -r requirements.txt

playwright install chromium

uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend

npm install

npm run dev
```

---

# 52. Code Quality Rules

Require:

- Python type hints
- TypeScript strict typing where practical
- clear separation of concerns
- small focused modules
- dependency injection where appropriate
- no global database session
- no giant service files
- no hard-coded file paths
- no analytics logic inside route handlers
- no Playwright logic inside analytics
- no frontend-specific assumptions inside collector logic

---

# 53. Database Design Rules

Analytics queries must not rely on collector-specific raw structures.

The flow should always be:

```text
External TikTok Data
      ↓
Collector
      ↓
Normalized Internal Schema
      ↓
Database
      ↓
Analytics
```

Never:

```text
Analytics
      ↓
TikTok HTML selectors
```

---

# 54. Data Quality Rules

Every metric should be treated carefully.

If TikTok returns ambiguous counts:

- document the meaning
- preserve raw value if useful
- do not silently reinterpret it

If a field disappears:

- store null
- log parser change
- do not reuse old value as if it were new

If sold count decreases unexpectedly:

- preserve snapshot
- flag anomaly
- do not automatically treat it as negative sales

---

# 55. Future Data Quality Layer

Prepare for future flags such as:

```text
is_partial
is_anomaly
source_confidence
parser_version
```

These do not need to be fully implemented in V1 unless useful.

---

# 56. Performance Philosophy

Optimize only where it matters.

Preferred:

```text
one long-lived browser
few contexts
few pages
session reuse
HTTP where possible
```

Avoid:

```text
thousands of browser launches
large uncontrolled concurrency
rendering pages unnecessarily
```

Measure before optimizing.

---

# 57. MVP Scope — Must Have

V1 is complete only when:

1. App runs entirely on local PC.
2. No paid API is required.
3. TikTok Shop VN real data can be collected.
4. Products are stored.
5. Every crawl creates snapshots.
6. Historical snapshots are preserved.
7. Sold deltas can be calculated.
8. Review deltas can be calculated.
9. New Products view works.
10. Best Sellers view works.
11. Rising view works.
12. Trend Score works.
13. Dashboard displays real collected data.
14. Product detail history works.
15. Scheduler works.
16. Manual crawler execution works.
17. App restart preserves history.
18. Collector failure does not crash the app.
19. Missing fields remain null rather than fabricated.
20. Research findings for MisterSeitz are documented.

---

# 58. Explicitly Out of Scope for V1

Do NOT implement:

- payment system
- authentication
- multi-user accounts
- mobile application
- cloud deployment
- distributed workers
- Redis
- Kafka
- Elasticsearch
- ClickHouse
- Kubernetes
- LLM integration
- AI chat
- automatic content generation
- advanced creator intelligence
- advanced video intelligence
- full affiliate scoring
- automated CAPTCHA solving

Keep V1 focused.

---

# 59. Product Success Metric

The MVP should eventually make this workflow possible:

```text
Open dashboard
      ↓
See Top Rising Products
      ↓
See New Products gaining traction
      ↓
Inspect sales/review velocity
      ↓
Select a few promising products
      ↓
Research them for affiliate promotion
```

Later:

```text
Product Trend
+
Content Trend
+
Affiliate Commission
      ↓
Top Affiliate Opportunities
```

---

# 60. Final Product Vision Example

A future result may look like:

```text
🔥 Product X

Trend Score: 92/100

First detected: 3 days ago

Sales
24h: +1,420
7d: +4,850
Acceleration: High

Reviews
24h: +210

Content
Videos 24h: +48
Creators 24h: +22
Views 24h: +3.8M

Affiliate
Commission: 18%

Opportunity Score: 89/100
```

The value of the system is not just knowing that the product sells.

The value is detecting:

```text
this product may be accelerating right now
```

early enough to act.

---

# 61. Working Style

Do not generate the entire repository in one uncontrolled batch.

Work systematically.

For each milestone:

- explain the plan in Vietnamese
- implement
- test
- fix errors
- report results in Vietnamese
- continue

When researching external repositories:

- inspect real source code
- do not rely only on README
- document findings
- distinguish reusable concepts from fragile implementation details

When an approach fails:

- investigate why
- inspect browser/network behavior
- try simpler legitimate alternatives
- do not immediately replace the solution with a paid service

---

# 62. Start Now

Begin with:

## Milestone 1 — Project Foundation

Create the project structure.

Set up:

Backend:

- FastAPI
- SQLite
- SQLAlchemy
- Pydantic configuration
- structured logging
- health endpoint
- pytest

Frontend:

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

Also create:

```text
README.md
.env.example
docs/
research/
```

Verify that both backend and frontend can run successfully.

Do not implement the TikTok Shop collector yet.

After Milestone 1 is working, continue to Milestone 2.