#!/usr/bin/env python3
"""Collect App Store search-result evidence for an ASA keyword relevance review.

This tool does not auto-approve a keyword. It returns storefront-specific app
results and comparison signals so an agent or human can classify the keyword as
related, ambiguous, or irrelevant before Broad -> Exact promotion.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

STOPWORDS = {
    "a", "an", "and", "app", "apps", "for", "free", "in", "of", "on", "or",
    "the", "to", "with", "your", "you", "best", "ios", "iphone", "ipad",
}


def tokens(value: str) -> set[str]:
    return {
        part for part in re.findall(r"[a-z0-9]+", value.casefold())
        if len(part) > 1 and part not in STOPWORDS
    }


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ASA-Pro-Skill/1.1 (+https://github.com/KaiChi888/ASA-Pro-Skill)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def compact_app(raw: dict[str, Any], advertised: dict[str, Any], query_tokens: set[str]) -> dict[str, Any]:
    description = str(raw.get("description") or "")
    name = str(raw.get("trackName") or "")
    subtitle = str(raw.get("sellerName") or raw.get("artistName") or "")
    text_tokens = tokens(" ".join((name, subtitle, description[:3000])))
    advertised_genres = set(advertised.get("genreIds") or [])
    result_genres = set(raw.get("genreIds") or [])
    query_hits = sorted(query_tokens & text_tokens)
    return {
        "rank": 0,
        "track_id": raw.get("trackId"),
        "name": name,
        "seller": raw.get("sellerName") or raw.get("artistName"),
        "primary_genre": raw.get("primaryGenreName"),
        "genres": raw.get("genres") or [],
        "rating": raw.get("averageUserRating"),
        "rating_count": raw.get("userRatingCount"),
        "price": raw.get("formattedPrice"),
        "url": raw.get("trackViewUrl"),
        "is_advertised_app": str(raw.get("trackId")) == str(advertised.get("trackId")),
        "same_genre": bool(advertised_genres & result_genres),
        "query_token_hits": query_hits,
        "query_token_coverage": round(len(query_hits) / max(len(query_tokens), 1), 3),
        "description_excerpt": re.sub(r"\s+", " ", description[:500]).strip(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--app-id", required=True, help="Advertised App Store Adam ID")
    parser.add_argument("--country", required=True, help="Two-letter storefront country code")
    parser.add_argument("--limit", type=int, default=10, choices=range(5, 31), metavar="5-30")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    country = args.country.lower()
    lookup_url = "https://itunes.apple.com/lookup?" + urllib.parse.urlencode(
        {"id": args.app_id, "country": country, "entity": "software"}
    )
    search_url = "https://itunes.apple.com/search?" + urllib.parse.urlencode(
        {"term": args.keyword, "country": country, "entity": "software", "limit": args.limit}
    )

    advertised_results = fetch_json(lookup_url).get("results") or []
    if not advertised_results:
        raise RuntimeError(f"Advertised app {args.app_id} was not found in storefront {country.upper()}")
    advertised = advertised_results[0]
    query_tokens = tokens(args.keyword)
    raw_results = fetch_json(search_url).get("results") or []
    results = [compact_app(item, advertised, query_tokens) for item in raw_results]
    for index, result in enumerate(results, 1):
        result["rank"] = index

    genre_matches = sum(bool(result["same_genre"]) for result in results)
    direct_app_rank = next((result["rank"] for result in results if result["is_advertised_app"]), None)
    covered_results = sum(result["query_token_coverage"] >= 0.5 for result in results)
    common_genres = Counter(
        genre for item in raw_results for genre in (item.get("genres") or [])
    ).most_common(8)

    if direct_app_rank is not None or (genre_matches >= max(3, len(results) // 2) and covered_results >= 3):
        suggestion = "related"
    elif genre_matches == 0 and direct_app_rank is None:
        suggestion = "irrelevant"
    else:
        suggestion = "ambiguous"

    payload = {
        "schema_version": 1,
        "keyword": args.keyword,
        "country": country.upper(),
        "advertised_app": {
            "track_id": advertised.get("trackId"),
            "name": advertised.get("trackName"),
            "seller": advertised.get("sellerName") or advertised.get("artistName"),
            "primary_genre": advertised.get("primaryGenreName"),
            "genres": advertised.get("genres") or [],
            "url": advertised.get("trackViewUrl"),
        },
        "signals": {
            "direct_app_rank": direct_app_rank,
            "same_genre_results": genre_matches,
            "query_covered_results": covered_results,
            "result_count": len(results),
            "common_result_genres": [{"genre": g, "count": n} for g, n in common_genres],
            "suggested_verdict": suggestion,
        },
        "results": results,
        "review": {
            "required": True,
            "allowed_verdicts": ["related", "ambiguous", "irrelevant"],
            "warning": "Heuristics are evidence only. An agent or human must inspect result intent before approval.",
        },
    }
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
