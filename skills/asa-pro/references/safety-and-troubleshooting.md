# Safety, economics, and troubleshooting

## Business readiness gate

Before launch, confirm the app is active and eligible in each storefront, Apple Ads billing/tax details work, the product page and subscription funnel are production-ready, and the owner has defined:

- account currency and reporting timezone;
- attribution and cohort maturity windows;
- gross versus proceeds ROAS basis;
- target paid CPA, payback period, trial-to-paid expectation, refund/commission assumptions;
- approved countries, daily budgets, devices, and Custom Product Pages.

Provision new campaigns and ad groups **paused first** when the API permits it. Verify country, currency, New Users, Search Match, bid, CPP, and negatives before enabling.

Maintain a non-secret registry keyed by IDs—not names alone—with app/Adam ID, country, campaign ID, Broad and Exact ad-group IDs, RevenueCat project/app IDs, currency, and timezone. Names are discovery hints; IDs are mutation scope.

## Deterministic mutation guardrails

Place hard checks after any agent reasoning:

- maximum percentage and absolute bid change;
- minimum and maximum bid;
- no second keyword change inside 24 hours;
- no repeated same-direction increase inside 48 hours;
- maximum mutations and total bid delta per run;
- revenue-protected keyword flag;
- kill switch and explicit `--apply` mode;
- single-instance lock;
- stop on changed organization, app mapping, country, currency, stale/missing reports, or exceeded safety cap.

Keep an append-only ledger with timestamp, actor, data window/timezone, IDs, before/after values, rationale, API request ID when available, and read-back result. Local state accelerates work but never overrides live reconciliation.

Treat create timeouts as **unknown outcomes**: re-list before retrying. A timeout can occur after Apple has already created the object.

## Diagnostic ladder

### No impressions

Check, in order:

1. campaign, ad group, keyword, and ad/creative status and serving reasons;
2. billing/budget and schedule;
3. country, device, New Users audience hold, and storefront eligibility;
4. campaign/ad-group negatives for accidental blocking;
5. active duplicate Exact keywords and routing overlap;
6. bid competitiveness, relevance, product page, and actual search volume;
7. report freshness, timezone/day boundary, and Apple latency.

Do not conclude “low search volume” until status, negatives, duplicates, and reporting latency are excluded.

### Impressions but no taps

Review relevance, keyword intent, title/subtitle/screenshots, CPP mapping, competitor strength, and TTR. A larger budget does not fix low relevance.

### Taps but no downloads

Review product-page conversion, localization, rating/reviews, pricing/paywall expectation, device fit, and accidental broad intent. Separate TTR from install rate.

### Downloads but no RevenueCat attribution

Verify app-side AdServices token collection, RevenueCat Apple Ads Services integration, production attribution fields, bundle/project mapping, permissions, and cache age. Revenue totals do not prove ASA mapping.

### Trials but no paid conversions

Check cohort age versus trial length, cancellation/refund status, paywall promise, and product value. Label immature cohorts instead of zero-value cohorts.

### Revenue without ASA identifiers

Treat it as unattributed/organic context. Do not assign it to keywords or claim campaign ROAS.

### Partial Broad → Exact mutation

- Exact exists, negative missing: retry negative after fresh Exact verification.
- Negative exists, Exact missing: remove/disable the accidental negative or restore Exact immediately; the query may be black-holed.
- State says complete but API does not: live API wins; repair and re-verify.

## Reporting semantics

Always distinguish:

- true zero;
- unknown/missing report;
- privacy-suppressed search term;
- stale/report-lagged data;
- immature revenue cohort;
- broken or unverified attribution.

A three-hour scheduler does not guarantee three-hour-fresh Apple data. Use overlapping windows, ID-based de-duplication, data freshness labels, and day-rollover baselines.
