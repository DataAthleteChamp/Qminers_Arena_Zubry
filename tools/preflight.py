"""Conservative published-rule checks, NOT the unpublished server validator."""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

MAX_BYTES = 1_048_576
FORBIDDEN_MODULES = {
    "os",
    "sys",
    "io",
    "pathlib",
    "socket",
    "subprocess",
    "threading",
    "multiprocessing",
    "importlib",
    "inspect",
    "gc",
    "ctypes",
    "resource",
}
FORBIDDEN_CALLS = {
    "open",
    "eval",
    "exec",
    "getattr",
    "setattr",
    "delattr",
    "type",
    "vars",
    "globals",
    "locals",
    "__import__",
    "compile",
    "breakpoint",
    "input",
}
SCIENTIFIC = {"numpy", "pandas", "scipy", "sklearn"}


def inspect_source(path: Path) -> list[str]:
    errors: list[str] = []
    data = path.read_bytes()
    if path.suffix != ".py" or not data or len(data) > MAX_BYTES:
        return ["A submission must be one non-empty .py of at most 1 MiB."]
    try:
        tree = ast.parse(data.decode("utf-8"), feature_version=(3, 13))
    except (SyntaxError, UnicodeError, ValueError) as error:
        return [f"Invalid Python 3.13 syntax: {error}"]
    base_names = {"BaseStrategy"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if (
                    root in FORBIDDEN_MODULES
                    or root == "simulator"
                    or (root not in sys.stdlib_module_names and root not in SCIENTIFIC)
                ):
                    errors.append(f"Line {node.lineno}: forbidden/unapproved import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".")[0]
            if module == "simulator.strategy":
                if any(alias.name != "BaseStrategy" for alias in node.names):
                    errors.append(f"Line {node.lineno}: only BaseStrategy may be imported here")
                base_names.update(alias.asname or alias.name for alias in node.names)
            elif module not in ("simulator.models", "__future__") and (
                node.level
                or root in FORBIDDEN_MODULES
                or root == "simulator"
                or (root not in sys.stdlib_module_names and root not in SCIENTIFIC)
                or any(part.startswith("_") for part in module.split("."))
            ):
                errors.append(f"Line {node.lineno}: forbidden/unapproved import {module}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                errors.append(f"Line {node.lineno}: forbidden builtin {node.func.id}")
        elif isinstance(node, ast.Attribute):
            if (node.attr.startswith("__") and node.attr != "__init__") or node.attr == "format":
                errors.append(f"Line {node.lineno}: forbidden attribute {node.attr}")
    subclasses = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and any(isinstance(base, ast.Name) and base.id in base_names for base in node.bases)
    ]
    if len(subclasses) != 1:
        errors.append("Define exactly one direct BaseStrategy subclass.")
    for node in subclasses:
        for member in node.body:
            if isinstance(member, ast.FunctionDef) and member.name == "__init__":
                arguments = member.args
                if (
                    len(arguments.posonlyargs + arguments.args) != 1
                    or arguments.vararg
                    or arguments.kwarg
                    or arguments.kwonlyargs
                ):
                    errors.append("BaseStrategy subclass must be constructible without arguments.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("strategy", type=Path)
    args = parser.parse_args()
    try:
        issues = inspect_source(args.strategy)
    except (OSError, ValueError) as error:
        print(f"Preflight error: {error}", file=sys.stderr)
        return 2
    if issues:
        print("\n".join(issues), file=sys.stderr)
        return 1
    print("Local conservative preflight passed; server sandbox validation is still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
