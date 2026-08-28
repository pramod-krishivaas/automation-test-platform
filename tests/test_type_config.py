"""
tests/test_type_config.py
─────────────────────────────
Single source of truth for the PHYSICAL-FOLDER side of test-type membership.

A test's type can be defined two ways, and the run pipeline honours BOTH:

  • FOLDER  — any test file placed under tests/test_suites/<type>/ belongs to that
              type. The folder location IS the authority; no DB tag is required or
              even consulted for these files (see the precedence rule below).
  • DB TAG  — tests that live in shared / common locations (e.g.
              tests/test_cases/common_test_cases/) are tagged via the
              test_cases.test_types JSON column and matched by testcase_key. Use
              this for a test that can belong to MORE THAN ONE type.

PRECEDENCE (implemented in conftest.py + test_runner.py):
  If a collected test's file path is under one of the test_suites/<type>/ folders,
  inclusion is decided purely by folder-path match against the requested type(s) —
  the DB is NOT queried for it. Only tests that are NOT under any type folder fall
  back to the DB test_types lookup. This keeps the two mechanisms from conflicting
  or double-deselecting each other.

Both conftest.py (path-precedence check) and tests/test_runner.py (adding folder
paths as pytest collection targets) import TEST_TYPE_FOLDERS from HERE, so the
folder convention is defined in exactly one place. Path handling mirrors the
tests/-relative resolution used elsewhere (discovery.py / test_runner.py).
"""
import os

# This file lives directly in tests/, so its dir IS the tests/ root.
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_SUITES_DIR = os.path.join(_TESTS_DIR, "test_suites")

# UI-facing label -> absolute folder path. Everything under a type folder — including
# its per-app subfolders (regular_farmer/ regular_client/ state_farmer/ state_client/
# common/) — belongs to that type. Keep the labels identical to the frontend's
# AVAILABLE_TEST_TYPES (TestScreen.jsx) and the DB test_types tag values.
TEST_TYPE_FOLDERS = {
    "Smoke":      os.path.join(_SUITES_DIR, "smoke"),
    "Regression": os.path.join(_SUITES_DIR, "regression"),
    "End-to-End": os.path.join(_SUITES_DIR, "end_to_end"),
    "Sanity":     os.path.join(_SUITES_DIR, "sanity"),
}


def _canon(label: str) -> str:
    """Fold a type string to a comparison key (case / space / underscore / dash-insensitive)."""
    return str(label or "").strip().lower().replace("_", "-").replace(" ", "-")


def normalize_type_label(label: str):
    """Return the canonical TEST_TYPE_FOLDERS key matching `label`, or None.

    Tolerates the variants that reach us from different places: the UI label
    ("End-to-End"), the folder name ("end_to_end"), or loose user input
    ("end to end", "SMOKE")."""
    if not label:
        return None
    key = _canon(label)
    for canon in TEST_TYPE_FOLDERS:
        if _canon(canon) == key:
            return canon
    return None


def folder_for_type(label: str):
    """Absolute folder path for a requested type label, or None if it's unknown."""
    canon = normalize_type_label(label)
    return TEST_TYPE_FOLDERS.get(canon) if canon else None


def type_folder_for_path(file_path: str):
    """The folder-PRECEDENCE check.

    If `file_path` (absolute or repo-relative) lives under one of the known
    test_suites/<type>/ folders, return that type's canonical label; otherwise
    None. A non-None result means folder location — not the DB tag — decides this
    test's type membership.
    """
    if not file_path:
        return None
    abspath = os.path.abspath(file_path)
    for label, folder in TEST_TYPE_FOLDERS.items():
        folder_abs = os.path.abspath(folder)
        try:
            # commonpath (not str.startswith) so 'test_suites/smoke2' can't be
            # mistaken for a child of 'test_suites/smoke'.
            if os.path.commonpath([abspath, folder_abs]) == folder_abs:
                return label
        except ValueError:
            continue  # different drives on Windows → not under this folder
    return None
