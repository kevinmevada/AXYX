"""Enforce rendering dependency / layering rules."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "src" / "motion_engine"

# (package relative to motion_engine, forbidden import prefixes)
FORBIDDEN_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "rendering/backend",
        ("motion_engine.studio", "PySide6", "PyQt5", "PyQt6"),
    ),
    (
        "rendering/avatar",
        ("motion_engine.studio", "PySide6", "PyQt5", "PyQt6"),
    ),
    (
        "rendering/scene",
        ("motion_engine.studio", "motion_engine.models", "PySide6"),
    ),
    (
        "rendering/resources",
        ("motion_engine.studio", "PySide6"),
    ),
    (
        "rendering/interfaces",
        ("motion_engine.studio", "PySide6"),
    ),
    (
        "api",
        ("motion_engine.studio", "PySide6"),
    ),
]


def _iter_py_files(package_rel: str) -> list[Path]:
    base = ROOT / package_rel
    if not base.exists():
        return []
    return sorted(base.rglob("*.py"))


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0] if alias.name.startswith("Py") else alias.name)
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
    return names


def _violates(imported: set[str], forbidden: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    for mod in imported:
        for rule in forbidden:
            if mod == rule or mod.startswith(rule + "."):
                hits.append(mod)
    return hits


@pytest.mark.parametrize("package,forbidden", FORBIDDEN_RULES)
def test_no_forbidden_imports(package: str, forbidden: tuple[str, ...]) -> None:
    violations: list[str] = []
    for path in _iter_py_files(package):
        hits = _violates(_imported_modules(path), forbidden)
        for hit in hits:
            violations.append(f"{path.relative_to(ROOT)} imports {hit}")
    assert not violations, "Layering violations:\n" + "\n".join(violations)
