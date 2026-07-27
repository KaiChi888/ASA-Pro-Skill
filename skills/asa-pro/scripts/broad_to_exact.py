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
import tempfile
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # Windows fallback below
    fcntl = None

CENT = Decimal("0.01")
DEFAULT_STATE = Path.home() / ".aads" / "asa-pro-state.json"
DEFAULT_LOCK = Path.home() / ".aads" / "asa-pro-broad-to-exact.lock"

SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.DOTALL),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\bSEARCHADS\.[A-Za-z0-9-]{16,}\b"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)[^\r\n,;]+"),
    re.compile(r"(?i)((?:client[_ -]?id|team[_ -]?id|key[_ -]?id|organization[_ -]?id|private[_ -]?key(?:[_ -]?path)?)\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)((?:api[_ -]?key|token|password|secret)\s*[:=]\s*)[^\s,;]+"),
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).casefold()


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: (match.group(1) if match.lastindex else "") + "[REDACTED]", redacted)
    return redacted[:4000]


def secure_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def acquire_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    os.fchmod(fd, 0o600)
    handle = os.fdopen(fd, "a+")
    try:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:  # pragma: no cover - exercised on Windows
            import msvcrt

            handle.seek(0)
            if not handle.read(1):
                handle.write("0")
                handle.flush()
            handle.seek(0)
            getattr(msvcrt, "locking")(
                handle.fileno(), getattr(msvcrt, "LK_NBLCK"), 1
            )
    except (BlockingIOError, OSError) as exc:
        handle.close()
        raise RuntimeError(f"another broad-to-exact process holds {path}") from exc
    return handle


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
                f"aads {redact_secrets(' '.join(args))} failed ({proc.returncode}): "
                f"{redact_secrets(proc.stderr.strip() or proc.stdout.strip())}"
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


def load_approvals(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    payload = json.loads(path.read_text())
    if payload.get("schema_version") != 1 or not isinstance(payload.get("approvals"), dict):
        raise ValueError("relevance file must use schema_version 1 with an approvals object")
    return payload["approvals"]


def relevance_approved(
    approvals: dict[str, Any], key: str, country: str, app_id: Any, max_age_days: int
) -> tuple[bool, str]:
    review = approvals.get(key)
    if not isinstance(review, dict):
        return False, "missing competitor relevance review"
    verdict = str(review.get("verdict") or "").casefold()
    if verdict != "related":
        return False, f"competitor relevance verdict is {verdict or 'missing'}"
    if str(review.get("country") or "").upper() != country.upper():
        return False, "review country does not match campaign country"
    if str(review.get("app_id") or "") != str(app_id):
        return False, "review app_id does not match campaign adamId"
    if not str(review.get("evidence") or "").strip():
        return False, "review evidence is empty"
    try:
        reviewed_at = datetime.fromisoformat(str(review.get("reviewed_at") or ""))
        if reviewed_at.tzinfo is None:
            return False, "reviewed_at must include timezone"
        age = datetime.now(timezone.utc) - reviewed_at.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return False, "reviewed_at is invalid"
    if age < timedelta(0) or age > timedelta(days=max_age_days):
        return False, "competitor relevance review is expired or future-dated"
    return True, "current related review"


def save_state(path: Path, state: dict[str, Any]) -> None:
    secure_write_text(path, json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


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
    parser.add_argument("--relevance-file", type=Path, help="JSON approvals produced after App Store competitor review")
    parser.add_argument("--max-relevance-age-days", type=int, default=30)
    parser.add_argument("--lookback-days", type=int, default=3)
    parser.add_argument("--signal", choices=("installs", "taps"), default="installs")
    parser.add_argument("--minimum", type=int, default=1)
    parser.add_argument("--seed-floor", type=Decimal, default=Decimal("1.00"))
    parser.add_argument("--avg-cpt-buffer", type=Decimal, default=Decimal("0.05"))
    parser.add_argument("--bid-ceiling", type=Decimal, default=Decimal("2.00"))
    parser.add_argument("--deny-pattern", action="append", default=[], help="Regex for terms to skip; repeatable")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--lock-file", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--aads-bin", default=shutil.which("aads"))
    args = parser.parse_args()
    if not args.aads_bin:
        parser.error("aads not found; use --aads-bin")
    if args.lookback_days < 1 or args.minimum < 1:
        parser.error("lookback-days and minimum must be positive")
    if args.max_relevance_age_days < 1:
        parser.error("max-relevance-age-days must be positive")
    if args.apply and args.relevance_file is None:
        parser.error("--apply requires --relevance-file; research storefront competitors before promotion")
    if not (Decimal("0") < args.seed_floor <= args.bid_ceiling):
        parser.error("require 0 < seed-floor <= bid-ceiling")
    return args


def run(args: argparse.Namespace) -> int:
    api = Aads(args.aads_bin)
    state = load_state(args.state)
    approvals = load_approvals(args.relevance_file)
    end = date.today()
    start = end - timedelta(days=args.lookback_days - 1)
    denied = [re.compile(pattern, re.IGNORECASE) for pattern in args.deny_pattern]
    summary: dict[str, Any] = {
        "mode": "apply" if args.apply else "dry-run",
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "campaigns": [], "created_exact": 0, "created_negative": 0,
        "already_complete": 0, "research_required": [], "skipped": [], "errors": [],
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

                app_id = campaign.get("adamId")
                approved, review_reason = relevance_approved(
                    approvals, key, str(countries[0]), app_id, args.max_relevance_age_days
                )
                if not approved:
                    summary["research_required"].append({
                        "campaign": name,
                        "campaign_id": cid,
                        "country": countries[0],
                        "app_id": app_id,
                        "term": term,
                        "reason": review_reason,
                        "research_argv": [
                            "python3", "scripts/app_store_relevance.py",
                            "--keyword", term, "--app-id", str(app_id),
                            "--country", str(countries[0]), "--limit", "10",
                        ],
                    })
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
                    summary["errors"].append({"campaign": name, "term": term, "error": redact_secrets(str(exc))})
            summary["campaigns"].append(campaign_result)
        except Exception as exc:
            summary["errors"].append({"campaign": name, "error": redact_secrets(str(exc))})

    if args.apply:
        save_state(args.state, state)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 1 if summary["errors"] else 0


def main() -> int:
    args = parse_args()
    lock_handle = acquire_lock(args.lock_file)
    try:
        return run(args)
    finally:
        lock_handle.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({"error": redact_secrets(str(exc))}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
