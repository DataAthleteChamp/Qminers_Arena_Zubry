from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from tools.analyze_private_round0 import audit_archive, parse_leaderboard


def fixture(path: Path, extra: dict[str, str] | None = None) -> Path:
    result = {
        "cash": -98,
        "inventory": 1,
        "mark_price": 101,
        "breach_penalty": 0,
        "pnl": 3,
        "fills": 2,
        "traded_volume": 3,
    }
    records = [
        {
            "kind": "strategy_order_submitted",
            "timestamp_us": 0,
            "payload": {
                "ready_at_us": 5000,
                "request": {"order_type": "limit", "quantity": 2},
            },
        },
        {"kind": "run_completed", "payload": result},
    ]
    files = {
        "metadata.json": json.dumps({"trader_class": "TestMaker"}),
        "result.json": json.dumps(result),
        "pnl.csv": "elapsed_s,pnl\n0,0\n1,5\n2,3\n",
        "trades.csv": (
            "timestamp_us,price,taker_side,quantity,taker_order_id,maker_order_id,"
            "taker_owner,maker_owner\n"
            "5000,100,A,2,m1,u1,market,user\n"
            "6000,102,B,1,m2,u2,market,user\n"
        ),
        "events.csv": "timestamp_us,source,operation,order_id,side,price,quantity\n",
        "book_deltas.csv": "timestamp_us,side,price,owner,qty_diff\n",
        "run.jsonl": "\n".join(json.dumps(record) for record in records) + "\n",
    }
    files.update(extra or {})
    with zipfile.ZipFile(path, "w") as archive:
        for name, value in files.items():
            archive.writestr(name, value)
    return path


def test_private_ledger_and_liquidation_reconcile(tmp_path: Path) -> None:
    report = audit_archive(fixture(tmp_path / "logs.zip"))
    audit = report["audit"]
    assert isinstance(audit, dict)
    assert audit["ledger_cash"] == -98
    assert audit["ledger_inventory"] == 1
    assert audit["reconstructed_pnl"] == 3
    assert audit["maker_volume_fraction"] == 1
    assert audit["max_drawdown"] == 2


def test_unsafe_archive_member_is_rejected_without_extraction(tmp_path: Path) -> None:
    path = fixture(tmp_path / "logs.zip", {"../outside.txt": "not extracted"})
    with pytest.raises(ValueError, match="Unsafe archive member"):
        audit_archive(path)
    assert not (tmp_path.parent / "outside.txt").exists()


def test_credential_field_blocks_sharing(tmp_path: Path) -> None:
    path = fixture(
        tmp_path / "logs.zip",
        {"metadata.json": json.dumps({"access_token": "fixture-value-not-a-real-token"})},
    )
    with pytest.raises(ValueError, match="Potential credential"):
        audit_archive(path)


def test_clipboard_gaps_and_hover_are_not_repaired_into_final_results() -> None:
    report = parse_leaderboard(
        {
            "hover_rows_raw": ["Zubry\t+5,380.00", "Known\t+100.00"],
            "ranking_rows_raw": [
                "14\tMerged label\t+45,415.00",
                "16\tKnown\t+200.00",
                "26\tZubry\tYour team\t+10,798.00",
            ],
        }
    )
    ambiguous = report["ambiguous_rows"]
    missing = report["missing_rank_tokens"]
    hover = report["hover"]
    ranking = report["ranking"]
    assert isinstance(ambiguous, list)
    assert isinstance(missing, list)
    assert isinstance(hover, list)
    assert isinstance(ranking, list)
    assert len(ambiguous) == 1
    assert 15 in missing
    assert hover[0]["pnl"] == 5380
    assert ranking[-1]["pnl"] == 10798
