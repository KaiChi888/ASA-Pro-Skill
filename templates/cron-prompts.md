# Scheduler-neutral automation briefs

## Every three hours

Run `scripts/broad_to_exact.py` with the approved campaign prefix and a non-overlap lock. Default eligibility is visible Broad search terms with at least one Apple Ads install in three days. Create/verify Exact first, then Broad Exact negative. Report actions, failures, or metric deltas only. Never change campaign budgets.

## Daily Exact bid review

Review RUNNING Search Results Exact groups. Join keywords with 3/7-day reports by ID. Read RevenueCat overview, keyword revenue, and campaign ROI; state attribution health. Maintain revenue winners. Lower excess headroom by 5–15% in stages. Raise only relevant terms with <20 impressions/3d by 5–10%, no more than every 48h, stopping after two failed raises. Do not change a keyword twice in 24h. Do not mutate campaign budgets. Re-read each change and report old → new bid.
