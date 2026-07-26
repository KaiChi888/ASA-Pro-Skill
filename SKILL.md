---
name: asa-pro
version: 1.0.0
description: Build and operate production Apple Search Ads Advanced campaigns with country-by-country Broad-to-Exact structure, New Users targeting, RevenueCat attribution, revenue-based keyword isolation, and CPT cost control using aads and rc CLI.
author: KaiChi888
license: MIT
metadata:
  tags: [apple-search-ads, asa, app-growth, revenuecat, roas, automation]
  homepage: https://github.com/KaiChi888/ASA-Pro-Skill
---

# ASA Pro

Use this skill when setting up, auditing, or operating Apple Search Ads Advanced with the `aads` and RevenueCat `rc` CLIs.

## Non-negotiable operating model

1. Use Apple Search Ads **Advanced**, Search Results placement, and manual CPT.
2. Use **one campaign per country**. Do not mix countries after exploration.
3. Every country campaign has two enabled ad groups:
   - `Broad Discovery`: BROAD keywords, Search Match off.
   - `Exact Match`: EXACT keywords, Search Match off.
4. Target **New Users** by excluding the advertised app's `adamId` in `appDownloaders.excluded`. Do not add age limits unless explicitly requested.
5. Promote a Broad search term after the configured success signal. Default: at least one attributed Apple Ads install.
6. Promotion is traffic routing:
   - create and verify the EXACT keyword in `Exact Match` first;
   - add the same text as an EXACT negative in `Broad Discovery` second;
   - verify both and record state. Never negative first, because failed Exact creation would block traffic.
7. Revenue—not CPI alone—decides whether an Exact winner deserves a dedicated campaign.
8. Seed new keywords at USD 1–2 (default USD 1.00; up to USD 2.00 in expensive markets), then lower bids gradually toward observed avgCPT while protecting volume.
9. Every mutation must be idempotent, scoped, freshly verified, and reported. Never store credentials in a repository or skill.

## Zero-to-running workflow

Read `references/setup.md` before mutations.

1. Install and configure `aads`.
2. Install and configure `rc` with a RevenueCat v2 read-only secret.
3. Verify AdServices attribution reaches RevenueCat; revenue without ASA attributes is not keyword ROAS.
4. Inventory apps, organization, campaigns, ad groups, keywords, negatives, targeting, budgets, and serving reasons.
5. Prepare a dry-run country blueprint. The owner must approve countries and daily budgets.
6. Create one campaign per country, then Broad and Exact ad groups.
7. Set New Users targeting at creation and verify no `PENDING_AUDIENCE_VERIFICATION` hold.
8. Seed localized Broad and Exact keywords at USD 1–2; keep active keyword intent non-overlapping.
9. Run `scripts/broad_to_exact.py --dry-run` until coverage and routing are correct.
10. Schedule deterministic harvesting every three hours and reasoning-based Exact bid review once daily.

## Blueprint

```text
<App> - <CC>
<App> - <CC> / Broad Discovery
<App> - <CC> / Exact Match
<App> - <CC> - <winning keyword>   # revenue-proven dedicated campaign
```

Required settings:

- exactly one country per campaign;
- App Store Search Results supply source;
- manual CPT and no end date unless time-limited;
- Search Match disabled in both ad groups;
- `targetingDimensions.appDownloaders.excluded = [campaign.adamId]`;
- no age/gender restriction by default;
- explicit owner-approved daily budget.

See `templates/campaign-blueprint.yaml` and `references/operations.md`.

## Broad → Exact harvesting

Use a three-calendar-day default lookback. Search-term reporting is not reliably hourly, and Apple can hide low-volume text behind privacy-threshold aggregate rows. Ignore rows with missing `searchTermText`.

Default eligibility:

```text
visible searchTermText AND totalInstalls >= 1 AND relevant to the app
```

A discovery-oriented account may explicitly override this to `taps >= 1`.

For every eligible term:

1. Normalize only for comparison; preserve original text for creation.
2. Skip if already routed.
3. Create or verify Exact in the paired Exact ad group.
4. Seed at `max(seed floor, avgCPT + buffer)`, capped by ceiling. Defaults: floor USD 1.00, buffer USD 0.05, ceiling USD 2.00.
5. Create or verify ad-group-level EXACT negative in Broad.
6. Re-list Exact keywords and Broad negatives.
7. Persist success only after both objects exist.

Use `scripts/broad_to_exact.py`; see `references/automation.md`.

## Bid strategy: start high enough, then find the clearing price

Daily Exact review uses 3-day and 7-day keyword reports plus RevenueCat evidence:

- **Maintain** when downloads and revenue/trials are healthy.
- **Lower 5–15%** when the bid has unnecessary headroom over avgCPT and volume is stable.
- Cost-control anchor: `max(avgCPT × 1.08, avgCPT + 0.03)`, rounded to cents.
- For strong high-volume winners, approach the anchor in stages; never jump directly to it.
- **Raise 5–10%** only for a relevant term with fewer than 20 impressions over three days and low spend. Wait 48 hours between raises; stop after two raises without exposure.
- Avoid changing a keyword twice within 24 hours.
- Relevant but costly terms get lower bids or pause recommendations—not negatives.
- Negative/pause automatically only for clearly irrelevant intent; ambiguous intent requires human review.

See `references/bidding-and-splitting.md`.

## Revenue-based dedicated campaigns

Do not isolate merely because CPI is low. Prefer an inclusive 60-day review:

- Apple Ads: spend, impressions, taps, installs, avgCPT, CPI, TTR, install rate;
- RevenueCat: attributed trials, paid customers, gross/proceeds revenue, LTV;
- derived: Gross ROAS, paid CPA, attribution coverage;
- recent 3/7/14-day trend versus the long window.

When splitting:

1. Create a dedicated single-country campaign and Exact ad group.
2. Keep New Users targeting and Search Match off.
3. Create and verify Exact in the new campaign.
4. Pause the old Exact only after the new one is RUNNING.
5. Add routing negatives wherever overlapping Broad traffic exists.
6. Confirm total daily budget is intentional redistribution, not accidental expansion.
7. Hold bids/budgets roughly seven days unless spend runs away; judge with a 7–14 day cohort because conversions lag.

## Automation split

- Every 3 hours: deterministic search-term harvest, Exact creation, Broad negative, delta report.
- Once daily: reasoning-based Exact bid review using 3/7-day Apple Ads and RevenueCat.
- Campaign budgets: recommendations only unless explicitly delegated.

Reports should omit no-data campaigns. The three-hour report includes actions, failures, spend/install deltas, interval CPI, and attribution health. The daily report includes bid changes, maintained winners, pause suggestions, questionable relevance, RevenueCat coverage, and budget recommendations.

## Safety and verification

Before writes, confirm organization, app `adamId`, country, IDs, currency, status, existing keywords/negatives (`--all`), and dry-run scope. Preserve a redacted JSON audit record.

After writes, re-list and verify status, match type, bid, New Users targeting, and serving reasons. If `PENDING_AUDIENCE_VERIFICATION` appears, report it and do not claim serving. Never claim ROAS when RevenueCat ASA attribution is missing or unverified.

## References

- `references/setup.md` — CLI, Apple credentials, RevenueCat, attribution.
- `references/operations.md` — safe `aads` recipes.
- `references/automation.md` — deterministic cron and state.
- `references/bidding-and-splitting.md` — cost control and dedicated campaigns.
- `references/revenuecat.md` — RevenueCat commands, attribution health, and revenue definitions.
- `templates/campaign-blueprint.yaml` — campaign checklist.
- `templates/cron-prompts.md` — scheduler briefs.
