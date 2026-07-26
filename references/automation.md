# Automation and cron design

## Deterministic three-hour harvest

`scripts/broad_to_exact.py` discovers enabled one-country campaigns, pairs Broad/Exact groups, reads recent terms, defaults to at least one install, creates/verifies Exact before Broad Exact negative, saves state in `~/.aads/asa-pro-state.json`, and supports `--dry-run`.

```bash
python3 scripts/broad_to_exact.py --dry-run
python3 scripts/broad_to_exact.py --dry-run --campaign-name-prefix "MyApp -"
```

Test twice before scheduling. Example:

```cron
0 */3 * * * cd /absolute/path/to/ASA-Pro-Skill && /usr/bin/python3 scripts/broad_to_exact.py >> "$HOME/.aads/asa-pro-cron.log" 2>&1
```

Set explicit cwd/PATH/timeout and prevent overlap with scheduler locking or `flock`.

## State invariants

Complete means Exact exists and is ACTIVE, Exact negative exists in Broad, read-back confirms both, and state is atomically persisted. If Exact succeeds but negative fails, retry negative next run. If Exact fails, never negative.

## Reporting

Include window/timezone, eligible terms, created/skipped Exact and negatives, failures, campaign spend/install delta and interval CPI only for active campaigns, and attribution health. Omit no-data campaigns. Reset daily snapshot baseline at date change.

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

## Failures

- Timeout/rate limit: exponential backoff and `Retry-After`.
- Hidden term: skip.
- Null payload: empty list.
- Currency mismatch: stop mutation.
- Duplicate: re-list and verify.
- Audience hold: report and do not claim RUNNING.
- RevenueCat revenue but no ASA rows: attribution unverified.
