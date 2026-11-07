from pathlib import Path

from tools.preflight import inspect_source

ROOT = Path(__file__).resolve().parents[1]


def test_team_submission_passes_published_rule_preflight() -> None:
    assert inspect_source(ROOT / "strategies/zubry.py") == []


def test_forbidden_import_is_not_confused_with_local_runtime_success(tmp_path: Path) -> None:
    file = tmp_path / "bad.py"
    file.write_text(
        "import pathlib\nfrom simulator.strategy import BaseStrategy\n"
        "class S(BaseStrategy):\n    pass\n"
    )
    assert any("pathlib" in error for error in inspect_source(file))


def test_forbidden_getattr_and_multiple_strategy_classes_are_rejected(tmp_path: Path) -> None:
    file = tmp_path / "bad.py"
    file.write_text(
        "from simulator.strategy import BaseStrategy\n"
        "class A(BaseStrategy):\n    pass\nclass B(BaseStrategy):\n    pass\n"
        "getattr(A, 'x')\n"
    )
    errors = inspect_source(file)
    assert any("getattr" in error for error in errors)
    assert any("exactly one" in error for error in errors)
