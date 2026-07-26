# Automation and cron design

## Deterministic three-hour harvest

`scripts/broad_to_exact.py` discovers enabled one-country campaigns, pairs Broad/Exact groups, reads recent terms, defaults to at least one install, enforces a current App Store competitor-relevance approval, creates/verifies Exact before Broad Exact negative, saves state in `~/.aads/asa-pro-state.json`, and supports `--dry-run`.

The included script uses strict name pairing as a portable starter. In production, maintain a reviewed app/country ID registry and validate those IDs before each mutation; names can be renamed or collide.

```bash
python3 scripts/broad_to_exact.py --dry-run --campaign-name-prefix "MyApp -"
python3 scripts/broad_to_exact.py --dry-run --campaign-name-prefix "MyApp -" \
  --relevance-file "$HOME/.aads/asa-pro-relevance.json"

# Writes are blocked unless the approval file is supplied.
python3 scripts/broad_to_exact.py --apply --campaign-name-prefix "MyApp -" \
  --relevance-file "$HOME/.aads/asa-pro-relevance.json"
```

The first dry run can omit the file to produce `research_required` candidates. For each candidate, run `scripts/app_store_relevance.py`, review the top results, and write a `related`, `ambiguous`, or `irrelevant` evidence record. Only `related` proceeds; approvals expire after 30 days by default.

Test twice before scheduling. Example:

```cron
0 */3 * * * cd /absolute/path/to/installed/asa-pro && /usr/bin/python3 scripts/broad_to_exact.py --apply --campaign-name-prefix "MyApp -" --relevance-file "$HOME/.aads/asa-pro-relevance.json" >> "$HOME/.aads/asa-pro-cron.log" 2>&1
```

Set explicit cwd/PATH/timeout and prevent overlap with scheduler locking or `flock`.

## State invariants

Complete means a current country/app-matched `related` review exists, Exact exists and is ACTIVE, Exact negative exists in Broad, read-back confirms both, and state is atomically persisted. If Exact succeeds but negative fails, retry negative next run. If Exact fails, never negative.

## Reporting

Include window/timezone, eligible terms, `research_required` terms and verdicts, competitor evidence summary, created/skipped Exact and negatives, failures, campaign spend/install delta and interval CPI only for active campaigns, and attribution health. Omit no-data campaigns. Reset daily snapshot baseline at date change.

## Daily reasoning-based bid review

Once daily:

1. inventory RUNNING Search Results campaigns and Exact groups;
2. join keyword lists with 3/7-day reports by keyword ID;
3. read RevenueCat overview, `keyword-revenue`, and `campaign-roi`;
4. preserve paid/revenue winners despite noisy CPI;
5. lower headroom in stages;
6. raise only relevant stuck terms, 48-hour spacing, two-raise cap;
7. avoid repeat changes within 24 hours;
8. save compact decision state;
9. recommend budgets but do not mutate without explicit delegation.

## Daily dedicated-campaign candidate review

Run once per day after Apple Ads and RevenueCat collection. Review Exact keywords with an inclusive 30–60-day window plus recent 3/7/14-day trends. Rank only actionable `scale independently` and `isolate for cost control` candidates; keep insufficient-data terms as internal `monitor` observations.

For each candidate, show country, keyword/ID, current campaign/ad group, spend, installs, CPI, paid customers, revenue, ROAS basis, attribution coverage, rationale, proposed campaign name, seed bid, and whether budget is redistribution or expansion. Include safe migration and rollback plans.

Present the ranked queue to the user for `approve`, `hold`, or `reject`. Silence is not approval. Do not create campaigns, change budgets, pause source keywords, or add routing changes until the user explicitly approves the immutable candidate key. If none qualify, report `No dedicated-campaign candidates today` with one short reason.

See `references/daily-dedicated-campaign-review.md`.

## Failures

- Timeout/rate limit: exponential backoff and `Retry-After`.
- Hidden term: skip.
- Null payload: empty list.
- Currency mismatch: stop mutation.
- Duplicate: re-list and verify.
- Audience hold: report and do not claim RUNNING.
- RevenueCat revenue but no ASA rows: attribution unverified.
