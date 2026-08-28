# tests/test_suites/ — folder-defined test types

A test's **test type** (Smoke / Regression / End-to-End / Sanity) can be defined
two ways. Both are honoured when a run is started with a test-type selected in the
UI; they are designed to stay **consistent** with each other, not to conflict.

## The two mechanisms

1. **Folder location (authoritative for anything placed here).**
   Any test file under `tests/test_suites/<type>/` belongs to that type — full stop.
   No DB tag is required, and the DB is **not** consulted for these files.

   ```
   tests/test_suites/
     smoke/        regression/     end_to_end/     sanity/
       regular_farmer/   regular_client/   state_farmer/   state_client/   common/
   ```

   The per-app subfolders mirror `tests/test_cases/` and `tests/pages/` so the code
   architecture stays consistent (one place per app). Put an app-specific smoke test
   in `tests/test_suites/smoke/<app>/`; put a shared one in `.../smoke/common/`.

2. **DB `test_types` tag (for shared/common tests that span multiple types).**
   A test that lives in an existing shared location — e.g.
   `tests/test_cases/common_test_cases/test_login_pytest.py` — and can belong to
   *more than one* type is tagged via the `test_cases.test_types` JSON column in the
   catalog (Add Test Case UI). It is matched to its source function by `testcase_key`
   (prefix-normalised, see `discovery.normalize_match_key`).

## Which one do I use?

- **Put a test in `tests/test_suites/<type>/`** if it only ever belongs to that one
  type. The folder is the single source of truth — no catalog step needed.
- **Leave a test in its shared/common location and tag it via `test_types` in the DB
  catalog** if it can belong to multiple types (e.g. login is both Smoke and
  Regression) or needs to be picked through the existing catalog UI.

## Precedence rule (how a run decides)

When a run is started with one or more types selected, `conftest.py`'s
`pytest_collection_modifyitems`:

- For a collected test **whose file is under `test_suites/<type>/`** → keep it iff
  that folder's type is in the requested set. **The DB is skipped for it.**
- For every **other** test → fall back to the DB `test_types` intersection check.

And `tests/test_runner.py` adds each selected type's `test_suites/<type>/` folder as
a pytest collection target, so folder tests are collected wholesale (no DB tag
needed) alongside whatever module files were selected.

The folder→type mapping lives in exactly one place: **`tests/test_type_config.py`**
(`TEST_TYPE_FOLDERS`). Both `conftest.py` and `test_runner.py` import it, so the
convention is defined once.
