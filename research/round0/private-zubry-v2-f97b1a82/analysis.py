"""Audit user-supplied private execution logs and preserve a partial leaderboard."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import math
import re
import stat
import sys
import zipfile
from collections import Counter
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path, PurePosixPath

from tools.common import ROOT, inside, now, read_json, sha256, write_once
from tools.compare import numeric

MEMBERS = {
    "metadata.json",
    "result.json",
    "pnl.csv",
    "trades.csv",
    "events.csv",
    "book_deltas.csv",
    "run.jsonl",
}
SECRET_PATTERN = re.compile(
    rb"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|"
    rb"AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    rb'"(?:access_token|api_key|client_secret|password)"\s*:\s*"[^"]+"'
)


def object_json(data: bytes) -> dict[str, object]:
    value: object = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return {str(key): item for key, item in value.items()}


def text(record: dict[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Missing string: {key}")
    return value


def strings(record: dict[str, object], key: str) -> list[str]:
    value = record.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Missing string list: {key}")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"Non-string row in {key}")
        result.append(item)
    return result


def rows(archive: zipfile.ZipFile, name: str) -> Iterator[dict[str, str]]:
    with archive.open(name) as binary, io.TextIOWrapper(binary, encoding="utf-8") as source:
        reader = csv.DictReader(source)
        for row in reader:
            clean: dict[str, str] = {}
            for key, value in row.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError(f"Malformed CSV row: {name}")
                clean[key] = value
            yield clean


def scan_archive(archive: zipfile.ZipFile) -> list[dict[str, object]]:
    names = archive.namelist()
    for member in archive.infolist():
        name = PurePosixPath(member.filename)
        if name.is_absolute() or ".." in name.parts or stat.S_ISLNK(member.external_attr >> 16):
            raise ValueError(f"Unsafe archive member: {member.filename}")
        if name.name.startswith(".env") or member.flag_bits & 1:
            raise ValueError(f"Credential/encrypted member cannot be shared: {member.filename}")
        if member.filename in ("metadata.json", "result.json") and member.file_size > 1 << 20:
            raise ValueError(f"Oversized JSON member: {member.filename}")
    if len(names) != len(set(names)) or set(names) != MEMBERS:
        raise ValueError("Archive must contain exactly the seven unique simulator log files")
    inventory: list[dict[str, object]] = []
    for member in archive.infolist():
        digest = hashlib.sha256()
        overlap = b""
        with archive.open(member) as source:
            while block := source.read(1 << 20):
                if SECRET_PATTERN.search(overlap + block):
                    raise ValueError(f"Potential credential in {member.filename}; not shared")
                digest.update(block)
                overlap = block[-256:]
        inventory.append(
            {
                "name": member.filename,
                "bytes": member.file_size,
                "compressed_bytes": member.compress_size,
                "sha256": digest.hexdigest(),
                "crc32": f"{member.CRC:08x}",
            }
        )
    return inventory


def audit_archive(path: Path) -> dict[str, object]:
    before = sha256(path)
    with zipfile.ZipFile(path) as archive:
        members = scan_archive(archive)
        metadata = object_json(archive.read("metadata.json"))
        result = object_json(archive.read("result.json"))
        inventory = cash = volume = 0
        min_inventory = max_inventory = 0
        fill_ids: set[str] = set()
        mix: Counter[str] = Counter()
        buy_value = sell_value = buy_volume = sell_volume = 0
        for row in rows(archive, "trades.csv"):
            taker, maker = row["taker_owner"], row["maker_owner"]
            if taker not in ("market", "user") or maker not in ("market", "user"):
                raise ValueError("Unknown trade ownership")
            if taker == maker == "user":
                raise ValueError("Unexpected self-trade")
            if "user" not in (taker, maker):
                continue
            price, quantity = int(row["price"]), int(row["quantity"])
            if price <= 0 or quantity <= 0 or row["taker_side"] not in ("B", "A"):
                raise ValueError("Invalid private fill")
            user_taker = taker == "user"
            buy = (row["taker_side"] == "B") == user_taker
            sign = 1 if buy else -1
            inventory += sign * quantity
            cash -= sign * quantity * price
            volume += quantity
            min_inventory = min(min_inventory, inventory)
            max_inventory = max(max_inventory, inventory)
            fill_ids.add(row["taker_order_id"] if user_taker else row["maker_order_id"])
            mode = "taker" if user_taker else "maker"
            mix[f"{mode}_matches"] += 1
            mix[f"{mode}_volume"] += quantity
            if buy:
                buy_value += price * quantity
                buy_volume += quantity
            else:
                sell_value += price * quantity
                sell_volume += quantity
        for key, actual in (
            ("cash", cash),
            ("inventory", inventory),
            ("traded_volume", volume),
            ("fills", len(fill_ids)),
        ):
            if numeric(result, key) != actual:
                raise ValueError(f"Result/trade ledger mismatch: {key}")
        markout = inventory * numeric(result, "mark_price")
        reconstructed_pnl = cash + markout - numeric(result, "breach_penalty")
        if not math.isclose(reconstructed_pnl, numeric(result, "pnl"), abs_tol=1e-8):
            raise ValueError("Cash/liquidation/penalty PnL mismatch")
        curve: list[tuple[float, float]] = []
        peak = drawdown = 0.0
        for row in rows(archive, "pnl.csv"):
            timestamp, pnl = float(row["elapsed_s"]), float(row["pnl"])
            if not math.isfinite(timestamp) or not math.isfinite(pnl):
                raise ValueError("Non-finite PnL curve")
            if curve and timestamp <= curve[-1][0]:
                raise ValueError("Non-chronological PnL curve")
            curve.append((timestamp, pnl))
            peak = max(peak, pnl)
            drawdown = max(drawdown, peak - pnl)
        if not curve or curve[-1][1] != numeric(result, "pnl"):
            raise ValueError("PnL curve and final result differ")
        events: Counter[str] = Counter()
        for row in rows(archive, "events.csv"):
            events[f"{row['source']}:{row['operation']}"] += 1
        order_types: Counter[str] = Counter()
        submitted_quantities: Counter[str] = Counter()
        delays: Counter[int] = Counter()
        completed = False
        with archive.open("run.jsonl") as source:
            for line in source:
                record = object_json(line)
                kind = text(record, "kind")
                payload = record.get("payload")
                if not isinstance(payload, dict):
                    raise ValueError("Malformed run payload")
                payload_object = {str(key): item for key, item in payload.items()}
                if kind == "strategy_order_submitted":
                    request = payload_object.get("request")
                    if not isinstance(request, dict):
                        raise ValueError("Missing submitted request")
                    order_types[str(request["order_type"])] += 1
                    submitted_quantities[str(request["quantity"])] += 1
                    delays[
                        int(numeric(payload_object, "ready_at_us"))
                        - int(numeric(record, "timestamp_us"))
                    ] += 1
                elif kind == "run_completed":
                    if payload_object != result:
                        raise ValueError("Run completion payload and result differ")
                    completed = True
        if not completed:
            raise ValueError("Missing completed run record")
    if sha256(path) != before:
        raise ValueError("Archive changed during analysis")
    return {
        "archive_sha256": before,
        "archive_bytes": path.stat().st_size,
        "members": members,
        "metadata": metadata,
        "result": result,
        "audit": {
            "ledger_cash": cash,
            "ledger_inventory": inventory,
            "ledger_traded_volume": volume,
            "ledger_filled_orders": len(fill_ids),
            "min_inventory": min_inventory,
            "max_inventory": max_inventory,
            "final_inventory_markout": markout,
            "reconstructed_pnl": reconstructed_pnl,
            "maker_volume_fraction": mix["maker_volume"] / volume if volume else None,
            "liquidity_execution_mix": dict(mix),
            "buy_vwap": buy_value / buy_volume if buy_volume else None,
            "sell_vwap": sell_value / sell_volume if sell_volume else None,
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "pnl_per_traded_lot": reconstructed_pnl / volume if volume else None,
            "pnl_elapsed_seconds": curve[-1][0],
            "pnl_points": len(curve),
            "max_drawdown": drawdown,
            "event_counts": dict(events),
            "submitted_order_types": dict(order_types),
            "submitted_quantity_counts": dict(submitted_quantities),
            "recorded_submit_delays_us": {str(key): count for key, count in delays.items()},
            "credential_scan": "No configured credential pattern found in all seven members.",
            "integrity": "All members read through CRC verification; ledgers and PnL reconciled.",
        },
        "curve": curve,
    }


def amount(value: str) -> float:
    number = Decimal(value.replace(",", "").replace("\u2212", "-"))
    if not number.is_finite():
        raise ValueError("Non-finite leaderboard amount")
    return float(number)


def parse_leaderboard(source: dict[str, object]) -> dict[str, object]:
    hover: list[dict[str, object]] = []
    for raw in strings(source, "hover_rows_raw"):
        team, value = raw.split("\t")
        hover.append({"team": team, "pnl": amount(value)})
    known_names = {text(row, "team") for row in hover}
    ranking: list[dict[str, object]] = []
    ambiguous: list[dict[str, object]] = []
    rank_counts: Counter[int] = Counter()
    for raw in strings(source, "ranking_rows_raw"):
        parts = raw.split("\t")
        tied = "Tie" in parts
        parts = [part for part in parts if part not in ("Tie", "Your team")]
        if len(parts) != 3:
            raise ValueError(f"Malformed clipboard row: {raw}")
        rank, team, value = parts
        number = int(rank)
        rank_counts[number] += 1
        if team not in known_names:
            ambiguous.append({"raw": raw, "reason": "Team text does not match any hover label."})
        else:
            ranking.append({"rank": number, "team": team, "pnl": amount(value), "tied": tied})
    missing: list[int] = []
    ordered = sorted(rank_counts)
    for first, second in zip(ordered, ordered[1:], strict=False):
        missing.extend(range(first + rank_counts[first], second))
    return {
        "source": source,
        "hover": hover,
        "ranking": ranking,
        "ambiguous_rows": ambiguous,
        "missing_rank_tokens": missing,
        "scope": "User-supplied clipboard snapshot; ambiguous/missing rows are not invented.",
    }


def save_analysis(archive_path: Path, leaderboard_path: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError("Analysis already exists; preserve it and choose a new output path")
    report = audit_archive(archive_path)
    curve_data = report.pop("curve")
    if not isinstance(curve_data, list):
        raise ValueError("Missing internal PnL curve")
    leaderboard = parse_leaderboard(read_json(leaderboard_path))
    source = read_json(leaderboard_path)
    own = text(source, "own_team")
    ranking_value = leaderboard["ranking"]
    if not isinstance(ranking_value, list):
        raise ValueError("Missing ranking")
    own_row = next(row for row in ranking_value if row["team"] == own)
    result_value = report["result"]
    if not isinstance(result_value, dict):
        raise ValueError("Missing result")
    result = {str(key): value for key, value in result_value.items()}
    leaderboard["own_final_matches_archive"] = own_row["pnl"] == numeric(result, "pnl")
    hover_time = numeric(source, "hover_time_seconds")
    nearest = min(curve_data, key=lambda point: abs(point[0] - hover_time))
    leaderboard["archive_pnl_at_nearest_hover_sample"] = {
        "elapsed_s": nearest[0],
        "pnl": nearest[1],
    }
    candidate = inside("strategies/zubry_v2.py")
    receipt_path = inside("submissions/playground/cae618bb5b61/receipt.json")
    receipt = read_json(receipt_path)
    classes = [
        node.name
        for node in ast.parse(candidate.read_text()).body
        if isinstance(node, ast.ClassDef)
    ]
    report.update(
        {
            "created_utc": now(),
            "archive": str(archive_path.relative_to(ROOT)),
            "analysis_script_sha256": sha256(Path(__file__)),
            "fit_window": None,
            "scope": "Descriptive audit of user-supplied private R0 execution logs; no fitting.",
            "leaderboard_input": str(leaderboard_path.relative_to(ROOT)),
            "leaderboard_input_sha256": sha256(leaderboard_path),
            "strategy_context": {
                "current_candidate": str(candidate.relative_to(ROOT)),
                "candidate_sha256": sha256(candidate),
                "candidate_matches_frozen_receipt": (
                    sha256(candidate) == text(receipt, "strategy_sha256")
                ),
                "candidate_classes": classes,
                "server_source_hash_available": False,
                "identity_limit": "Archive names the class but contains no submitted source bytes.",
            },
            "public_counterpart": read_json(
                inside("research/experiments/r0-v2-mm-final/result.json")
            ),
            "interpretation": [
                "This archive identifies ZubryV2Strategy, not the earlier one-lot ZubryStrategy.",
                "The earlier -14125 public result is not a same-policy private comparison.",
                "Maker/taker volume is execution mix, not separate profit attribution.",
                "The archive contains execution logs, not a fully specified replay input tape.",
                "Reported single-run pnl_se is not a paired difference SE or P(win).",
                "Other paused experiments remain unpromoted; this audit does not resume them.",
                "Leaderboard ranks do not reveal competing strategies or justify curve fitting.",
            ],
        }
    )
    write_once(output / "report.json", report)
    write_once(output / "leaderboard.json", leaderboard)
    with (output / "analysis.py").open("xb") as destination:
        destination.write(Path(__file__).read_bytes())
    warnings = leaderboard["ambiguous_rows"]
    if not isinstance(warnings, list):
        raise ValueError("Missing clipboard warnings")
    for warning in warnings:
        print(f"Clipboard warning: {warning}")
    print(f"Saved private archive audit and leaderboard at {output}")
    print(f"Private PnL={numeric(result, 'pnl')}; rank={own_row['rank']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", default="rounds/r0/results.zip")
    parser.add_argument(
        "--leaderboard", default="research/round0/leaderboard-2026-11-07-input.json"
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        save_analysis(inside(args.archive), inside(args.leaderboard), inside(args.output))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, StopIteration) as error:
        print(f"Private R0 analysis failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
