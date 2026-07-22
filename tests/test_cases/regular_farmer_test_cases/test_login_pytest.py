"""
Regular Farmer — Login (unified app).

Vertical slice of the new architecture:
  shared login (pages/common/login_page)  →  land by priority  →
  switch to the target role (pages/common/switch_page)  →  assert on target home.

The target role comes from the UI selection via the `--target-role` pytest option
(exposed as the `target_role` fixture in conftest.py); it defaults to
'regular_farmer' for direct/local runs.
"""
import os
import json
import allure
import pytest

from pages.common.login_page import load_locators_once, do_login
from pages.common.switch_page import detect_landed_app, switch_to_app, assert_on_app

import sys
sys.dont_write_bytecode = True

ROLE = "regular_farmer"


def _account_for(role):
    """Return (phone, mpin) for a single-role account from test_data/accounts.json."""
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "test_data", "accounts.json",
    )
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            accounts = json.load(f)
        acct = accounts.get("single_role", {}).get(role, {})
        return acct.get("phone") or "7660852538", acct.get("mpin") or "1234"
    except Exception as e:
        print(f"[data] Could not load accounts.json ({e}); using defaults.")
        return "7660852538", "1234"


@allure.epic("Login Flow")
@allure.feature("Authentication")
class TestLogin:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self, request):
        load_locators_once(self, request)

    @allure.story("Successful Login")
    @allure.title("Verify user can login with valid credentials")
    def test_loginpos_001(self, driver, target_role):
        test_flow_steps = []
        # Fall back to this suite's own role for direct/local runs (no UI selection).
        role = target_role or ROLE
        phone, mpin = _account_for(role)

        try:
            # 1. Shared login — lands on whichever home the number resolves to by priority.
            do_login(driver, self, test_flow_steps, phone_number=phone, mpin=mpin)

            # 2. Detect where we landed (logged for visibility).
            landed = detect_landed_app(driver, self)
            print(f"[test] Selected/target role = {role}; landed on = {landed}")

            # 3. Switch to the intended app if the landed app differs.
            switch_to_app(driver, self, role, test_flow_steps)

            # 4. Confirm we're on the target app's home.
            assert_on_app(driver, self, role, test_flow_steps)

        finally:
            os.makedirs("test-flows", exist_ok=True)
            with open("test-flows/login_flow_success.json", "w") as f:
                json.dump(test_flow_steps, f, indent=4)
