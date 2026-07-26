# App Store competitor relevance gate

A Broad search term must not move to Exact solely because it produced a download. First inspect the keyword's storefront search results and confirm that their dominant intent is relevant to the advertised app.

## Why this gate exists

Broad can match semantically loose or misleading queries. One accidental download is not enough evidence that the query belongs in the Exact portfolio. Search-result apps reveal what users and the App Store likely mean by the keyword.

## Evidence sources available in this skill

1. **iTunes Search API** — country-specific App Store software results; names, descriptions, genres, ratings, seller, and App Store URLs.
2. **iTunes Lookup API** — advertised app metadata by Adam ID and storefront.
3. **`aads apps search --query`** — Apple Ads app discovery when additional account-side inspection is useful.
4. **App Store product pages** — screenshots, subtitle, description, IAP, positioning, and user-facing intent.
5. **Sensor Tower public overview** — optional directional download/revenue/ranking evidence for important competitors. Never invent unavailable figures.

The included `scripts/app_store_relevance.py` uses the first two sources and produces a review packet. It does **not** auto-approve.

## Research command

```bash
python3 scripts/app_store_relevance.py \
  --keyword "photo cleaner" \
  --app-id 1234567890 \
  --country US \
  --limit 10 \
  --output /tmp/photo-cleaner-us.json
```

Optional secondary checks:

```bash
aads apps search --query "photo cleaner" -o json
```

For strategically important competitors, open:

```text
https://app.sensortower.com/overview/<APP_ID>?country=US
```

Sensor Tower values are estimates and should not determine keyword relevance by themselves.

## Review rubric

Review the top 5–10 storefront results. Compare the advertised app with result names, subtitles/sellers, primary genres, descriptions, screenshots, and use cases.

### `related`

Approve only when the dominant search-result intent matches a real feature, problem, category, or audience served by the advertised app. Signals include:

- the advertised app itself ranks for the query;
- most top apps solve the same core job;
- result descriptions and screenshots express the same user intent;
- category overlap is supported by product-function overlap, not genre alone.

### `ambiguous`

Hold for human review when results mix multiple intents, the term is a broad brand/common word, or only a minority of apps match. Do not promote or negative automatically.

### `irrelevant`

Do not promote when dominant results solve a different job or target a different category/audience. Add a negative only if irrelevance is clear and the app owner permits the negative-keyword policy.

## Required review record

Store approvals outside the repository, for example `~/.aads/asa-pro-relevance.json`:

```json
{
  "schema_version": 1,
  "approvals": {
    "2144289621|keyword": {
      "verdict": "related",
      "reviewed_at": "2026-07-27T07:00:00+08:00",
      "country": "US",
      "app_id": "1234567890",
      "evidence": "Top results are keyword, EMF, spirit-box, and paranormal tools; intent matches the advertised app.",
      "competitor_ids": ["111111111", "222222222"]
    }
  }
}
```

Key format is `<campaign-id>|<normalized search term>`. Preserve original Unicode in evidence while using trimmed, whitespace-collapsed, case-folded text for the key.

`related` approval should expire after 30 days by default. Re-research sooner when App Store results shift, a term becomes a major spender, or the app positioning changes.

## Promotion sequence with relevance gate

1. Broad term meets install/tap performance gate.
2. Generate App Store research packet for the campaign country and advertised Adam ID.
3. Agent/human assigns `related`, `ambiguous`, or `irrelevant` with evidence.
4. Only a current `related` record unlocks mutation.
5. Create and verify Exact.
6. Create and verify Broad Exact negative.
7. Save mutation state and review evidence.

## Agent review requirements

- Do not use genre overlap alone; Utilities, Lifestyle, and Productivity are broad.
- Do not assume every competitor-brand keyword is relevant. Verify the competitor actually solves the same job.
- Preserve country specificity: US results cannot approve JP or DE automatically.
- Treat localized words and transliterations independently.
- Distinguish App Store organic result intent from Apple Ads auction volume; research proves relevance, not guaranteed exposure.
- If the API is unavailable or results are empty, verdict is `ambiguous`, not `related`.
- Never fabricate competitor names, ranks, downloads, revenue, ratings, or descriptions.
