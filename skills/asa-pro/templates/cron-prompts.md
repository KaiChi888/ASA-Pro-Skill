# Scheduler-neutral automation briefs

## Every three hours

Run `scripts/broad_to_exact.py` with the approved campaign prefix and a non-overlap lock. Default eligibility is visible Broad search terms with at least one Apple Ads install in three days. Treat these as research candidates: run `scripts/app_store_relevance.py` for the campaign country and advertised Adam ID, inspect the top 5–10 App Store competitors, and record `related`, `ambiguous`, or `irrelevant` with evidence. Only a current country/app-matched `related` approval may unlock mutation. Then create/verify Exact first and Broad Exact negative second. Report research-required terms, verdicts, actions, failures, or metric deltas only. Never change campaign budgets.

## Daily Exact bid review

Review RUNNING Search Results Exact groups. Join keywords with 3/7-day reports by ID. Read RevenueCat overview, keyword revenue, and campaign ROI; state attribution health. Maintain revenue winners. Lower excess headroom by 5–15% in stages. Raise only relevant terms with <20 impressions/3d by 5–10%, no more than every 48h, stopping after two failed raises. Do not change a keyword twice in 24h. Do not mutate campaign budgets. Re-read each change and report old → new bid.

## Daily dedicated-campaign candidate review

Once per day, evaluate Exact keywords using 30–60-day Apple Ads and RevenueCat evidence plus 3/7/14-day trends. Show only actionable `scale independently` or `isolate for cost control` candidates with country, immutable keyword/campaign IDs, spend, installs, CPI, paid customers, revenue, ROAS basis, attribution coverage, proposed campaign name/bid, budget redistribution versus expansion, migration plan, and rollback. Ask the user to choose `approve`, `hold`, or `reject` for each candidate. This review is advisory: never create/split a campaign, move budget, pause the source, or alter routing until explicit approval. If no candidate qualifies, say so briefly.
