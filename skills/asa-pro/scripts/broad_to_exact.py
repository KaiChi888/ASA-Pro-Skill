#!/usr/bin/env python3
"""Promote successful Apple Ads Broad search terms into Exact safely.

Safety defaults:
- dry-run unless --apply is supplied
- requires --campaign-name-prefix or explicit --all-enabled
- creates/verifies Exact before creating the Broad Exact negative
- persists state only after fresh read-back confirms both objects
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

CENT = Decimal("0.01")
DEFAULT_STATE = Path.home() / ".aads" / "asa-pro-state.json"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).casefold()


def money(value: Any) -> Decimal:
    if isinstance(value, dict):
        value = value.get("amount")
    return Decimal(str(value or "0"))


def extract_list(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        data = payload.get("data")
        if data is None:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return data["items"]
    raise TypeError(f"Unexpected list payload: {type(payload).__name__}")


class Aads:
    def __init__(self, binary: str) -> None:
        self.binary = binary

    def run(self, *args: str) -> Any:
        proc = subprocess.run(
            [self.binary, *args], text=True, capture_output=True, timeout=120
        )
        if proc.returncode:
            raise RuntimeError(
                f"aads {' '.join(args)} failed ({proc.returncode}): "
                f"{proc.stderr.strip() or proc.stdout.strip()}"
            )
        text = proc.stdout.strip()
        return json.loads(text) if text else None

    def campaigns(self) -> list[dict[str, Any]]:
        return extract_list(self.run("campaigns", "list", "--all", "-o", "json"))

    def adgroups(self, campaign_id: int) -> list[dict[str, Any]]:
        return extract_list(
            self.run(
                "adgroups", "list", "--campaign-id", str(campaign_id),
                "--all", "-o", "json",
            )
        )

    def keywords(self, campaign_id: int, adgroup_id: int) -> list[dict[str, Any]]:
        return extract_list(
            self.run(
                "keywords", "list", "--campaign-id", str(campaign_id),
                "--adgroup-id", str(adgroup_id), "--all", "-o", "json",
            )
        )

    def negatives(self, campaign_id: int, adgroup_id: int) -> list[dict[str, Any]]:
        return extract_list(
            self.run(
                "negatives", "adgroup-list", "--campaign-id", str(campaign_id),
                "--adgroup-id", str(adgroup_id), "--all", "-o", "json",
            )
        )

    def searchterms(
        self, campaign_id: int, adgroup_id: int, start: date, end: date
    ) -> list[dict[str, Any]]:
        payload = self.run(
            "reports", "searchterms", "--campaign-id", str(campaign_id),
            "--adgroup-id", str(adgroup_id), "--start-time", start.isoformat(),
            "--end-time", end.isoformat(), "-o", "json",
        )
        return (
            (((payload or {}).get("data") or {}).get("reportingDataResponse") or {})
            .get("row") or []
        )

    def create_exact(
        self, campaign_id: int, adgroup_id: int, text: str, bid: Decimal
    ) -> None:
        self.run(
            "keywords", "create", "--campaign-id", str(campaign_id),
            "--adgroup-id", str(adgroup_id), "--text", text,
            "--match-type", "EXACT", "--bid", format(bid, "f"), "-o", "json",
        )

    def create_negative(self, campaign_id: int, adgroup_id: int, text: str) -> None:
        self.run(
            "negatives", "adgroup-create", "--campaign-id", str(campaign_id),
            "--adgroup-id", str(adgroup_id), "--text", text,
            "--match-type", "EXACT", "-o", "json",
        )


def find_pair(adgroups: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    enabled = [a for a in adgroups if a.get("status") == "ENABLED"]
    broad = [a for a in enabled if "broad" in str(a.get("name", "")).casefold()]
    exact = [a for a in enabled if "exact" in str(a.get("name", "")).casefold()]
    if len(broad) != 1 or len(exact) != 1:
        return None
    return broad[0], exact[0]


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"processed": {}}
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {"processed": {}}
    payload.setdefault("processed", {})
    return payload


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    os.chmod(tmp, 0o600)
    tmp.replace(path)


def calculate_bid(avg_cpt: Decimal, floor: Decimal, buffer: Decimal, ceiling: Decimal) -> Decimal:
    result = max(floor, avg_cpt + buffer)
    return min(result, ceiling).quantize(CENT, rounding=ROUND_HALF_UP)


def is_active_exact(items: list[dict[str, Any]], text: str) -> bool:
    wanted = normalize(text)
    return any(
        normalize(str(item.get("text", ""))) == wanted
        and item.get("matchType") == "EXACT"
        and item.get("status") == "ACTIVE"
        for item in items
    )


def has_active_exact_negative(items: list[dict[str, Any]], text: str) -> bool:
    wanted = normalize(text)
    return any(
        normalize(str(item.get("text", ""))) == wanted
        and item.get("matchType") == "EXACT"
        and item.get("status") == "ACTIVE"
        for item in items
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--campaign-name-prefix", help="Only campaigns with this prefix")
    scope.add_argument("--all-enabled", action="store_true", help="Explicitly process all enabled campaigns")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Perform writes")
    mode.add_argument("--dry-run", action="store_true", help="Explicit no-write mode (the default)")
    parser.add_argument("--lookback-days", type=int, default=3)
    parser.add_argument("--signal", choices=("installs", "taps"), default="installs")
    parser.add_argument("--minimum", type=int, default=1)
    parser.add_argument("--seed-floor", type=Decimal, default=Decimal("1.00"))
    parser.add_argument("--avg-cpt-buffer", type=Decimal, default=Decimal("0.05"))
    parser.add_argument("--bid-ceiling", type=Decimal, default=Decimal("2.00"))
    parser.add_argument("--deny-pattern", action="append", default=[], help="Regex for terms to skip; repeatable")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--aads-bin", default=shutil.which("aads"))
    args = parser.parse_args()
    if not args.aads_bin:
        parser.error("aads not found; use --aads-bin")
    if args.lookback_days < 1 or args.minimum < 1:
        parser.error("lookback-days and minimum must be positive")
    if not (Decimal("0") < args.seed_floor <= args.bid_ceiling):
        parser.error("require 0 < seed-floor <= bid-ceiling")
    return args


def main() -> int:
    args = parse_args()
    api = Aads(args.aads_bin)
    state = load_state(args.state)
    end = date.today()
    start = end - timedelta(days=args.lookback_days - 1)
    denied = [re.compile(pattern, re.IGNORECASE) for pattern in args.deny_pattern]
    summary: dict[str, Any] = {
        "mode": "apply" if args.apply else "dry-run",
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "campaigns": [], "created_exact": 0, "created_negative": 0,
        "already_complete": 0, "skipped": [], "errors": [],
    }

    campaigns = [c for c in api.campaigns() if c.get("status") == "ENABLED"]
    if args.campaign_name_prefix:
        campaigns = [c for c in campaigns if str(c.get("name", "")).startswith(args.campaign_name_prefix)]

    for campaign in campaigns:
        cid = int(campaign["id"])
        name = str(campaign.get("name") or cid)
        countries = campaign.get("countriesOrRegions") or []
        if len(countries) != 1:
            summary["skipped"].append({"campaign": name, "reason": "not one-country"})
            continue
        try:
            pair = find_pair(api.adgroups(cid))
            if pair is None:
                summary["skipped"].append({"campaign": name, "reason": "need exactly one enabled Broad and Exact group"})
                continue
            broad, exact = pair
            broad_id, exact_id = int(broad["id"]), int(exact["id"])
            exact_items = api.keywords(cid, exact_id)
            negative_items = api.negatives(cid, broad_id)
            rows = api.searchterms(cid, broad_id, start, end)
            campaign_result = {"campaign": name, "country": countries[0], "eligible": 0, "actions": []}

            for row in rows:
                metadata = row.get("metadata") or {}
                total = row.get("total") or {}
                term = str(metadata.get("searchTermText") or "").strip()
                if not term or row.get("other") is True or any(rx.search(term) for rx in denied):
                    continue
                metric = int(total.get("totalInstalls") or total.get("tapInstalls") or 0) if args.signal == "installs" else int(total.get("taps") or 0)
                if metric < args.minimum:
                    continue
                campaign_result["eligible"] += 1
                key = f"{cid}|{normalize(term)}"
                exact_ok = is_active_exact(exact_items, term)
                negative_ok = has_active_exact_negative(negative_items, term)
                if exact_ok and negative_ok:
                    summary["already_complete"] += 1
                    state["processed"][key] = {"text": term, "campaign": name, "verified": True}
                    continue

                avg_cpt = money(total.get("avgCPT"))
                currency = str((total.get("avgCPT") or {}).get("currency") or campaign.get("currency") or "USD")
                bid = calculate_bid(avg_cpt, args.seed_floor, args.avg_cpt_buffer, args.bid_ceiling)
                action = {"term": term, "signal": metric, "avg_cpt": format(avg_cpt, "f"), "currency": currency, "bid": format(bid, "f"), "exact": "exists" if exact_ok else "create", "negative": "exists" if negative_ok else "create"}
                campaign_result["actions"].append(action)
                if not args.apply:
                    continue
                try:
                    if not exact_ok:
                        api.create_exact(cid, exact_id, term, bid)
                        exact_items = api.keywords(cid, exact_id)
                        exact_ok = is_active_exact(exact_items, term)
                        if not exact_ok:
                            raise RuntimeError("Exact read-back verification failed")
                        summary["created_exact"] += 1
                    if not negative_ok:
                        api.create_negative(cid, broad_id, term)
                        negative_items = api.negatives(cid, broad_id)
                        negative_ok = has_active_exact_negative(negative_items, term)
                        if not negative_ok:
                            raise RuntimeError("negative read-back verification failed")
                        summary["created_negative"] += 1
                    state["processed"][key] = {"text": term, "campaign": name, "exact_adgroup_id": exact_id, "broad_adgroup_id": broad_id, "bid": format(bid, "f"), "currency": currency, "verified": True}
                    save_state(args.state, state)
                except Exception as exc:  # continue other terms while reporting exact scope
                    summary["errors"].append({"campaign": name, "term": term, "error": str(exc)})
            summary["campaigns"].append(campaign_result)
        except Exception as exc:
            summary["errors"].append({"campaign": name, "error": str(exc)})

    if args.apply:
        save_state(args.state, state)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
