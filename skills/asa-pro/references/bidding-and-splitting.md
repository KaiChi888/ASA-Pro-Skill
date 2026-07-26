# Bidding and revenue-based splitting

## Seed bids

Default USD 1.00; up to USD 2.00 in expensive countries or highly relevant competitive terms. Use campaign currency when not USD. A high max CPT is not necessarily paid CPT, but can enter expensive auctions, so discovery must be followed by cost control.

## Cost control

Use 3/7-day data and 14/30-day data for volatile terms.

```text
target = max(avgCPT * 1.08, avgCPT + 0.03)
```

Reduce only when meaningfully below current bid. Typical step: 5–15%. Strong winners move in stages.

- Stable downloads + revenue + excess headroom → lower 5–15%.
- Stable downloads + bid near avgCPT → maintain.
- Relevant spend/no installs → lower 10–20% or suggest pause after enough data.
- Relevant <20 impressions/3d + low spend → raise 5–10%, wait 48h.
- Two raises and still stuck → stop; review relevance, volume, product page, or dedicated campaign.
- Paid revenue/high LTV → protect while conversion lag matures.
- Clearly irrelevant → negative and pause after verification.

## Revenue evidence

```text
CPI = spend / installs
Paid CPA = spend / actual paid customers
Gross ROAS = attributed gross revenue / spend
Proceeds ROAS = attributed proceeds / spend
Attribution coverage = RevenueCat ASA-attributed customers / Apple Ads installs
```

Subscription existence does not prove payment; require positive revenue. Gross ROAS near 100% is not necessarily profitable after commission, tax, and refunds.

Never mix currencies silently. Normalize spend and revenue using a recorded FX source/date. Compare acquisition cohorts at suitable maturity points (for example D1/D7/D14/D30/D90) rather than mixing current spend with lifetime account revenue.

## Dedicated campaign gate

Prefer 60 inclusive days plus 3/7/14-day trends. Qualify when there is meaningful spend/install volume, attributed paid revenue or LTV, a reason for independent control, and sufficient attribution coverage.

Verdicts: `scale independently`, `isolate for cost control`, or `insufficient data`.

## Safe split

1. Create new single-country campaign and Exact group.
2. Set New Users and Search Match off.
3. Create Exact with approved bid/budget.
4. Verify RUNNING/ACTIVE.
5. Pause old Exact.
6. Ensure source Broad has Exact negative.
7. Re-inventory active duplicates.
8. Confirm total daily budget before/after.
9. Wait roughly seven days unless spend runs away; evaluate 7–14 day lag before scaling.
