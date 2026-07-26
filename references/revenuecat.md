# RevenueCat analysis and attribution

## Configure and verify

Use a RevenueCat v2 secret with read-only access to metrics, customers/attributes, apps, subscriptions, and purchases.

```bash
rc configure
rc config show
rc metrics overview -o json
rc apps list -o table
```

## Attribution health check

```bash
rc keyword-revenue --limit 100 -o json
rc campaign-roi --limit 100 -o json
```

These commands iterate customers and may be slow. Start with 50–100. An empty result can mean ASA attribution is absent, not that revenue is zero. `keyword-revenue` and `campaign-roi` cache full results for about one hour; use `--refresh` only when needed.

RevenueCat must receive AdServices attribution from the iOS app and have Apple Ads Services integration enabled. Until attributed rows appear:

- use RevenueCat totals only as whole-app context;
- do not join totals to campaigns or keywords;
- label attribution coverage unverified;
- do not claim ROAS.

## Useful reports

```bash
rc metrics overview -o json
rc metrics chart --name revenue --currency USD -o json
rc metrics chart --name trials_new --start-date YYYY-MM-DD --end-date YYYY-MM-DD --resolution 0 -o json
rc metrics chart --name actives_new --start-date YYYY-MM-DD --end-date YYYY-MM-DD --resolution 0 -o json
rc keyword-revenue --sort subscribers --top 20 -o table
rc campaign-roi --sort avg_ltv -o table
```

RevenueCat chart dates are UTC calendar dates. Do not label them as a precise local-time day. Trials can convert after the observation window, so do not kill a keyword immediately when it has trials but no paid revenue.

## Revenue definitions

RevenueCat money objects can expose `gross`, `proceeds`, `commission`, and `tax`. State which measure is used. For actual paid-customer counts, require positive revenue; subscription existence alone can represent a zero-revenue expired trial.

Join Apple Ads and RevenueCat primarily on campaign ID, ad-group ID, keyword ID/text, and country/window. Report attribution coverage with every ROAS conclusion.
