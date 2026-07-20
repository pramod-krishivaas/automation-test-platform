"""
test_management/discovery.py
───────────────────────────────
Parses automation source files under tests/ to find test functions tagged
with an @allure.title("ID -- description") decorator, so DB test cases
(testcase_key) can be matched against real, currently-active automation code.

AST-based, not regex-over-raw-text: ast.walk() only visits real parsed
nodes, so commented-out @allure.title(...) lines are excluded automatically.
"""

import ast
import re
from pathlib import Path

from fastapi import HTTPException

# repo root = parents[3] from this file's location:
# new_backend/modules/test_management/discovery.py -> test_management -> modules -> new_backend -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_TESTS_DIR = _REPO_ROOT / "tests"

_ID_PATTERN = re.compile(r"^\s*([A-Za-z]{1,4}_\d{2,4})\s*--?\s*(.*)$")


def _resolve_safe_path(relative_path: str) -> Path:
    """Resolve a repo-relative path, rejecting anything outside tests/."""
    candidate = (_REPO_ROOT / relative_path).resolve()
    if candidate.suffix != ".py":
        raise HTTPException(400, "Only .py files can be inspected")
    if not candidate.is_relative_to(_TESTS_DIR):
        raise HTTPException(400, "Path must be inside tests/")
    if not candidate.is_file():
        raise HTTPException(404, f"File not found: {relative_path}")
    return candidate


def _extract_allure_title(decorator_list: list[ast.expr]) -> str | None:
    for dec in decorator_list:
        if (
            isinstance(dec, ast.Call)
            and isinstance(dec.func, ast.Attribute)
            and dec.func.attr == "title"
            and isinstance(dec.func.value, ast.Name)
            and dec.func.value.id == "allure"
            and dec.args
            and isinstance(dec.args[0], ast.Constant)
            and isinstance(dec.args[0].value, str)
        ):
            return dec.args[0].value
    return None


def discover_automation_tests(relative_path: str) -> list[dict]:
    """Given a repo-relative .py path under tests/, return every ID-tagged,
    currently-active test function as {id, title, function_name, line}."""
    absolute_path = _resolve_safe_path(relative_path)
    source = absolute_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(absolute_path))

    results: list[dict] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test"):
            continue
        title = _extract_allure_title(node.decorator_list)
        if not title:
            continue
        match = _ID_PATTERN.match(title)
        if not match:
            continue
        results.append({
            "id": match.group(1).upper(),
            "title": match.group(2).strip(),
            "function_name": node.name,
            "line": node.lineno,
        })
    return results
