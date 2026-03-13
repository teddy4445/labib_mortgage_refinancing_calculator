# Labib Mortgage Monitoring Front-End

RTL-first, multi-page front-end for a mortgage monitoring and refinance recommendation product built with:

- HTML5
- Tailwind CSS
- Vanilla JavaScript
- jQuery

The project is front-end only. All business data is mocked through client-side service modules so a later Python REST backend can replace the mock layer without rewriting the UI.

## Run locally

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
