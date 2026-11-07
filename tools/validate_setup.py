"""Validate copied inputs, untouched upstream files and local documentation."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from tools.common import ROOT, inside, read_json, sha256


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    upstream = read_json(root / "research/upstream.json")
    files = upstream.get("untouched_files")
    if not isinstance(files, dict):
        return ["Missing upstream file fingerprint map."]
    for name, expected in files.items():
        path = inside(str(name), root)
        if not path.is_file() or sha256(path) != expected:
            errors.append(f"Original organiser file changed/missing: {name}")
    materials = read_json(root / "research/materials.json")
    records = materials.get("files")
    if not isinstance(records, list):
        return [*errors, "Missing material fingerprints."]
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            errors.append("Invalid material entry.")
            continue
        path = inside(record["path"], root)
        if not path.is_file() or sha256(path) != record.get("sha256"):
            errors.append(f"Provided material changed/missing: {record['path']}")
    markdown = list(root.glob("*.md"))
    for directory in ("docs", "knowledge", ".github", "rounds", "materials"):
        markdown.extend((root / directory).rglob("*.md"))
    for path in markdown:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            parsed = urlparse(target)
            if parsed.scheme or target.startswith("#"):
                continue
            destination = inside(path.parent / unquote(parsed.path), root)
            if not destination.exists():
                errors.append(f"Broken local link: {path.relative_to(root)} -> {target}")
    for name in ("zubry-researcher", "zubry-builder", "zubry-reviewer"):
        path = root / f".github/agents/{name}.agent.md"
        if not path.is_file() or "include-custom-instructions: true" not in path.read_text():
            errors.append(f"Missing role/instruction inheritance: {name}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("\n".join(errors))
        return 1
    print("Provided files, original simulator/explorer and local guide links passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
