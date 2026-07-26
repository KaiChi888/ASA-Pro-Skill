# Safe operations with `aads`

Examples use placeholders. Inspect `--help` for the installed alpha CLI before writes.

## Inventory

```bash
aads campaigns list --all -o json
aads adgroups find-all --all -o json
aads keywords list --campaign-id "$CID" --adgroup-id "$AID" --all -o json
aads negatives adgroup-list --campaign-id "$CID" --adgroup-id "$BROAD_AID" --all -o json
```

## One-country campaign and paired groups

```bash
aads campaigns create --name "MyApp - US" --adam-id "$ADAM_ID" \
  --countries "US" --daily-budget "20" --status ENABLED

aads adgroups create --campaign-id "$CID" --name "Broad Discovery" \
  --default-bid "1.00" --search-match=false

aads adgroups create --campaign-id "$CID" --name "Exact Match" \
  --default-bid "1.00" --search-match=false
```

Prefer New Users targeting in creation JSON:

```json
{"targetingDimensions":{"appDownloaders":{"excluded":["<ADAM_ID>"]}}}
```

Some API updates require complete `targetingDimensions`. GET first and preserve every dimension. New Users can trigger `PENDING_AUDIENCE_VERIFICATION`; verify serving after each change.

## Seed and promote

```bash
aads keywords create --campaign-id "$CID" --adgroup-id "$BROAD_AID" \
  --text "example keyword" --match-type BROAD --bid "1.00"

aads reports searchterms --campaign-id "$CID" --adgroup-id "$BROAD_AID" \
  --start-time YYYY-MM-DD --end-time YYYY-MM-DD -o json
```

Apple may hide low-volume text as `searchTermText: null`; skip hidden rows. Before any Exact write, research the term's country-specific App Store results:

```bash
python3 scripts/app_store_relevance.py \
  --keyword "$TERM" --app-id "$ADAM_ID" --country "$COUNTRY" --limit 10

aads apps search --query "$TERM" -o json
```

Compare the advertised app with the top 5–10 apps' use cases, descriptions, genres, and product pages. Record an evidence-backed `related`, `ambiguous`, or `irrelevant` verdict as described in `references/competitor-relevance.md`. Do not continue unless a current `related` approval matches the campaign ID, country, and Adam ID.

Create Exact first:

```bash
aads keywords create --campaign-id "$CID" --adgroup-id "$EXACT_AID" \
  --text "$TERM" --match-type EXACT --bid "1.00"
```

Then route Broad traffic:

```bash
aads negatives adgroup-create --campaign-id "$CID" --adgroup-id "$BROAD_AID" \
  --text "$TERM" --match-type EXACT
```

Re-list both resources.

## Update bid

```bash
aads keywords update --campaign-id "$CID" --adgroup-id "$EXACT_AID" \
  --from-json '[{"id":123456,"bidAmount":{"amount":"0.85","currency":"USD"}}]'
```

Batch by campaign/ad group; re-list and verify ACTIVE status and bid.

## Reports

```bash
aads reports campaigns --start-time YYYY-MM-DD --end-time YYYY-MM-DD --granularity DAILY -o json
aads reports adgroups --campaign-id "$CID" --start-time YYYY-MM-DD --end-time YYYY-MM-DD -o json
aads reports keywords --campaign-id "$CID" --adgroup-id "$EXACT_AID" \
  --start-time YYYY-MM-DD --end-time YYYY-MM-DD --granularity DAILY -o json
```

Use one campaign-report call and map locally where possible. Per-campaign loops can exceed scheduler timeouts.

## Negative policy

- Promoted term: Exact negative in source Broad.
- Clearly irrelevant: Exact negative; if active as Exact, pause only after verification.
- Relevant but poor: lower bid or recommend pause; do not negative automatically.
- Ambiguous: human review.

Always list with `--all`; treat null list payload as empty, not an iterable error.
