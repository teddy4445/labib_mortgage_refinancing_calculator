# Labib Mortgage Monitoring Platform

RTL-first, multi-page front-end for a mortgage monitoring and refinance recommendation product built with:

- HTML5
- Tailwind CSS
- Vanilla JavaScript
- jQuery

The repository now contains:

- The original front-end
- A new FastAPI backend scaffold under [backend](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/backend)

The UI still runs on mock data, but the backend package now includes the first service layer for email, database, calculations, market-data gathering, analytics, and security.

## Run locally

### Front-end

1. Start a local static server from [C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator):

```powershell
node server.js
```

2. Open [http://localhost:8000](http://localhost:8000) in a browser.
3. Navigate through the public, user, status, and admin pages from the UI.
4. For auth demo flows:
   - User/admin login success password: `Secure123!`
   - Locked login example email: `locked@example.com`
   - Unknown forgot-password email: `unknown@example.com`
   - Expired reset token example: open `pages/reset-password.html?token=expired`

Notes:

- Tailwind and jQuery are loaded from CDN, so the browser needs internet access to render the UI as designed.
- Language bundles are loaded from [assets/i18n](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/assets/i18n), so opening pages directly with `file://` will not reliably load translations. Use a local server.
- A minimal local dev server is included in [server.js](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/server.js).

### Back-end

1. Create a virtual environment and install dependencies:

```powershell
cd C:\Users\lazeb\Desktop\labib_mortgage_refinancing_calculator
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

2. Copy [.env.example](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/.env.example) to `.env`. By default it uses SQLite for local dev. If you want PostgreSQL, set:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/labib_mortgage
```

3. Start the API (use port `8001` so the front-end can stay on `8000`):

```powershell
uvicorn backend.app.main:app --reload --port 8001
```

4. Open the API docs at [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs).

Notes:

- The front-end now calls the API directly. By default it targets `http://localhost:8001/api/v1`.
- You can override the API base by setting `localStorage["labib-api-base"]` in the browser or by adding `data-api-base` to the `<body>` tag on any page.

### Phase 1 calculation engine

The backend now includes a dedicated pure-domain mortgage engine under `backend/app/domain` for current mortgage calculations.

Implemented in Phase 1:

- compound annual-to-monthly rate conversion:
  - `r_monthly = (1 + r_annual/100)^(1/12) - 1`
- standard amortization using the converted monthly rate
- current-payment support for:
  - `fixed_non_linked`
  - `fixed_linked`
  - `prime_floating`
  - `adjustable_non_linked`
  - `adjustable_linked`
- total current monthly payment aggregation with track-level breakdown

Important notes:

- The domain layer is intentionally pure and does not depend on FastAPI or SQLAlchemy.
- Market inputs are still injected explicitly for now:
  - `boi_base_rate` is required for prime tracks
  - `current_cpi` is required for CPI-linked tracks
- Phase 2+ items are intentionally deferred:
  - advisor fees
  - bank fees
  - Regulation 116 penalty engine
  - scenario generation
  - recommendation ranking
  - market-data connectors
- Monetary values are calculated at higher precision internally and rounded only at output boundaries.

### Phase 3 scenario and recommendation engine

The backend now also includes a dedicated scenario-analysis layer for comparing mortgage options without embedding UI copy in the domain logic.

Implemented in Phase 3:

- canonical scenario support for:
  - `status_quo`
  - `full_refinance`
  - `partial_refinance`
- reusable break-even analysis:
  - `break_even_months = refinance_costs / monthly_savings`
  - only considered viable when monthly savings are positive
- reusable NPV analysis:
  - uses compound annual-to-monthly discount conversion
  - default annual discount rate is configurable and defaults to `4.0%`
- prime robustness analysis with two Bank of Israel paths:
  - stable base rate
  - modest annual increase
- machine-readable recommendation output:
  - ranked scenario list
  - recommendation code
  - explanation tokens
  - risk flags
  - human-follow-up eligibility flag
- serializable scenario output that can later be stored in `analysis_runs`

Important notes:

- Phase 3 does not auto-trigger any refinance or follow-up workflow.
- Recommendation text in the domain layer is token/code-based so the frontend can localize it later.
- Phase 2 cost/penalty inputs are still using a documented legacy fallback when detailed structured cost engines are unavailable in the repo:
  - `prepayment_fee`
  - `advisor_cost`
  - `bank_cost`
  - `appraisal_cost`
  - `upfront_costs`
- Partial-refinance scenario generation is bounded and pruned when combinations exceed the configured safe threshold.
- Market data is still injected as request inputs or recovered from stored payloads until Phase 4 ingestion is implemented.

### Phase 4 market-data ingestion and snapshot layer

The backend now includes a dedicated market-data ingestion and query layer for persisted external inputs. Calculation engines still do not fetch remote sources directly; they consume normalized snapshots or route-level resolved `MarketInputs`.

Implemented in Phase 4:

- centralized source catalog for:
  - `boi_base_rate`
  - `boi_mortgage_rate_buckets`
  - `cpi_series`
  - `inflation_expectations`
- connector/adapters with configurable endpoints and local static fallbacks for development/test
- canonical normalization for:
  - BoI base rate
  - mortgage-rate buckets by remaining-duration bucket
  - CPI series
  - inflation expectations
- immutable snapshot envelopes stored in `market_data_snapshots`
  - raw payload preserved
  - normalized payload preserved
  - schema version
  - connector version
  - warning/anomaly flags
  - idempotency key
- deterministic query services for:
  - latest BoI base rate
  - latest CPI
  - CPI by period
  - mortgage-rate bucket lookup by remaining months
  - latest inflation expectations
- status/freshness layer for admin/technical use
- manual refresh support:
  - `POST /api/v1/admin/data-refresh`
  - `POST /api/v1/admin/data-refresh/{source_key}`

Important notes:

- Snapshot rows are treated as immutable; repeated fetches of the same normalized snapshot are deduplicated by idempotency key rather than overwriting history.
- Source typing, refresh cadence, and enable/disable controls are centralized in the source catalog and config.
- When request-level `market_inputs` are missing, mortgage calculation routes now try to enrich them from the latest persisted valid snapshots.
- Market-data fetching still supports static fallback payloads for local development until production upstream URLs/formats are finalized.
- Real scheduler/queue deployment is intentionally deferred; Phase 4 provides the service/job runner foundation and admin/manual refresh integration.

### Phase 5 API contract stabilization

The backend now exposes additive, frontend-oriented response contracts for the currently connected product flows.

Implemented in Phase 5:

- request metadata on frontend-facing responses:
  - `meta.request_id`
  - `meta.timestamp`
  - `meta.contract_version`
- consistent error envelope:
  - top-level `detail`
  - structured `error.code`
  - optional field-level validation items under `error.fields`
- stabilized DTOs for:
  - auth
  - latest mortgage / workspace payload
  - dashboard payload
  - refinance analysis responses
  - alerts
  - admin overview and refresh responses
  - customer interest request flow
- recommendation payloads remain locale-neutral:
  - explanation tokens
  - risk flags
  - recommendation codes
  - structured scenarios
- request-ID propagation through response headers via `X-Request-ID`

Important notes:

- The existing frontend-compatible top-level fields are intentionally preserved where they were already in use:
  - `response.dashboard`
  - `response.mortgage`
  - auth fields like `role`, `email`, `user_id`
  - alerts collections like `active`, `history`, `dismissed`
- The customer-interest endpoint still does not trigger any refinance or external CRM flow.
- When the current frontend omits `mortgage_id` / `analysis_run_id` in the interest flow, the backend now links the request to the latest mortgage and latest analysis run when available.
- The backend still avoids localized recommendation prose; rendering remains the frontend’s responsibility.

### One-command start (front + back)

From the project root:

```powershell
.\start-dev.ps1
```

Or in Command Prompt:

```bat
start-dev.bat
```

## Structure

- [index.html](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/index.html)
- [pages](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/pages)
- [pages/admin](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/pages/admin)
- [pages/status](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/pages/status)
- [assets/css/app.css](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/assets/css/app.css)
- [assets/js/tailwind-config.js](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/assets/js/tailwind-config.js)
- [assets/js/components](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/assets/js/components)
- [assets/js/pages](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/assets/js/pages)
- [assets/js/services/mock-api.js](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/assets/js/services/mock-api.js)
- [assets/js/utils](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/assets/js/utils)
- [assets/i18n](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/assets/i18n)
- [mock-data/app-data.js](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/mock-data/app-data.js)
- [backend/app/main.py](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/backend/app/main.py)
- [backend/app/models.py](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/backend/app/models.py)
- [backend/app/schemas.py](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/backend/app/schemas.py)
- [backend/app/managers](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/backend/app/managers)
- [backend/app/api](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/backend/app/api)
- [backend/app/templates/email](C:/Users/lazeb/Desktop/labib_mortgage_refinancing_calculator/backend/app/templates/email)

## Architecture

- `layout.js` injects the shared public, app, auth, and admin shells.
- `i18n.js` loads JSON language bundles, persists the selected language, applies `lang` / `dir`, and translates rendered DOM content.
- `ui.js` provides reusable tabs, tables, accordion, metric cards, modals, and page headers.
- `mock-api.js` centralizes all data access behind promise-based service methods.
- `mock-data/app-data.js` holds realistic mortgage, analysis, alerts, scenarios, expert, and admin datasets.
- `state.js` stores local demo state in `localStorage`, including onboarding data, dismissed alerts, notifications, and profile updates.
- Page modules are grouped by concern:
  - `public-pages.js`
  - `auth-pages.js`
  - `onboarding-page.js`
  - `product-pages.js`
  - `status-pages.js`
  - `admin-pages.js`

## Included screens

- Public: landing, consent/disclaimer
- Auth: signup, login, forgot password, reset password
- Product: onboarding wizard, dashboard, mortgage workspace, analysis center, partial refinance, scenarios, alerts, settings, expert next steps
- Technical status: email verification, session expired, 404, 500, maintenance, access denied
- Admin: login, dashboard, market data, policy thresholds, users, mortgage review, legal content, audit logs

## Verification

JavaScript syntax was checked locally with:

```powershell
Get-ChildItem -Recurse -Filter *.js | ForEach-Object { node --check $_.FullName }
```

## Backend handoff notes

- Replace `App.MockApi.*` methods with real REST calls when Python endpoints are ready.
- Keep response shapes aligned with `mock-data/app-data.js` to minimize UI rewrites.
- Layouts, tabs, tables, and modal interactions are already separated from page data assembly.
- Current backend foundations:
  - `EmailManager` for templated SendGrid email delivery
  - `DataBaseManager` for PostgreSQL-backed CRUD, search, filtering, analytics, and admin summaries
  - `CalculatorManager` for current mortgage aggregation, scenario evaluation, break-even, NPV, robustness, and recommendation ranking
  - `DataGatheringManager` for market-data refresh orchestration
  - `MarketDataService` for ingestion, normalization, persistence, retry handling, and batch refresh
  - `MarketSnapshotService` for calculator-facing market-data lookup
  - `MarketStatusService` for freshness/anomaly/admin status views
  - `AnalyticsManager` for drop-off, conversion, email failure, and API failure tracking
  - `CaptchaManager`, `ValidationManager`, and `RateLimitManager` for core security controls
