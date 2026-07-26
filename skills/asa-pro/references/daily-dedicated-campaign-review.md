# Daily dedicated-campaign candidate review

Run this review **once per day** after Apple Ads and RevenueCat data collection. Its purpose is to surface Exact keywords that may benefit from their own single-country campaign. It is advisory only: never create, split, pause, move budgets, or add routing negatives until the user explicitly approves a named candidate.

## Data windows

Use an inclusive 30–60 day evidence window when available, plus recent 3/7/14-day trends and cohort maturity. Low-volume/new keywords can remain `monitor` until enough evidence exists.

Join by campaign ID, ad-group ID, and keyword ID wherever possible. Do not join only by keyword text.

### Apple Ads evidence

- campaign, country, current campaign/ad group, keyword ID/text, match type, status, current bid;
- impressions, taps, installs, spend, avgCPT, CPI, TTR, install rate;
- recent volume and cost trend;
- duplicate active targets and Broad routing negatives;
- campaign budget utilization and whether the keyword is constrained by shared budget/control.

### RevenueCat evidence

- ASA-attributed customers and attribution coverage;
- trials, actual paid customers, gross revenue, proceeds revenue, avg LTV;
- paid CPA, gross/proceeds ROAS, trial-to-paid maturity;
- whether data is fresh, cached, immature, missing, or unverified.

Revenue visibility without ASA campaign/keyword attribution is not candidate-level ROAS.

## Candidate verdicts

### `scale independently`

Show when there is credible paid revenue/LTV, meaningful repeatable volume, acceptable economics, sufficient attribution coverage, and a reason for dedicated bid/budget control.

### `isolate for cost control`

Show when the keyword is strategically relevant and has useful volume but needs independent bid/budget limits because it consumes disproportionate spend, has distinct CPI/ROAS, or obscures the rest of the Exact portfolio.

### `monitor`

Do not place in the user decision queue by default. Keep internally when volume, attribution, or cohort maturity is insufficient. Surface only if the user asks for all observations.

### `do not split`

Use when the keyword lacks meaningful volume, is not repeatable, has poor/unverified economics, is irrelevant/ambiguous, or would create unnecessary campaign fragmentation.

## No universal hard threshold

Derive minimum spend, installs, paid customers, ROAS, and payback thresholds from the app's approved economics. Never copy thresholds from another app. If targets are undefined, state that and use an evidence-ranked recommendation rather than pretending there is a precise pass/fail rule.

## Daily user decision queue

Show only actionable candidates (`scale independently` or `isolate for cost control`) in a compact table:

| # | Country | Keyword | Current location | Verdict | 30/60d spend / installs / CPI | Paid / revenue / ROAS | Attribution | Why split | Proposed campaign | Budget effect |
|---|---|---|---|---|---|---|---|---|---|---|

For every candidate, include:

- immutable candidate key: country + source campaign ID + keyword ID;
- proposed campaign name: `<App> - <CC> - <keyword>`;
- proposed seed bid and currency;
- whether budget is **redistribution** or **expansion**;
- explicit source of redistributed budget, if recommended;
- migration/overlap plan: destination created paused, verify, enable, pause source Exact, retain/add Broad Exact negative;
- 7-day stabilization and 7–14 day revenue-cohort evaluation plan;
- rollback plan.

Then ask the user to choose per candidate:

- `approve` — authorize a separately confirmed implementation step;
- `hold` — keep monitoring;
- `reject` — suppress unless material evidence changes.

Do not interpret silence as approval. Do not bundle all candidates into one mutation authorization unless the user explicitly approves all listed immutable candidate keys.

## Daily output behavior

- If candidates exist: show the ranked decision queue and await user choice.
- If none exist: report `No dedicated-campaign candidates today` with one short reason such as insufficient mature revenue, insufficient volume, or attribution unverified.
- Do not list every `monitor` keyword in routine reports.
- Preserve a decision ledger so rejected/held candidates are not repeatedly spammed without material change.
- Re-open a held/rejected candidate only when spend, installs, paid customers, ROAS, attribution coverage, or strategic control need changes materially.

## Safety after approval

Approval is not the mutation itself. Before implementation, re-read live campaign/ad-group/keyword/negative/budget state and present exact proposed changes. Never silently expand total daily budget. The safe split sequence remains in `references/bidding-and-splitting.md`.
