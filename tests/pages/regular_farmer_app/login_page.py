import time
import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.wait_utils import smart_click
import json
import os
import sys
import re
sys.dont_write_bytecode = True

def load_locators_once(self, request):
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    locators_path = os.path.join(project_root, "locators", "unified_app.json")
    with open(locators_path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    raw = re.sub(r'\\u(?![0-9a-fA-F]{4})', r'\\\\u', raw)
    xpaths = json.loads(raw)

    # ── Login ───────────────────────────────────────
    login_screen_xpaths = xpaths.get("login_screen", {})

    #login_screen
    request.cls.language_next_xpath = login_screen_xpaths.get("next_button_language_login")
    request.cls.allow_picture_button_xpath = login_screen_xpaths.get("allow_picture_button")
    request.cls.allow_location_button_xpath = login_screen_xpaths.get("allow_location_button")
    request.cls.allow_audio_button_xpath = login_screen_xpaths.get("allow_audio_button")    
    request.cls.allow_notifications_button_xpath = login_screen_xpaths.get("allow_notifications_button")
    request.cls.phone_number_input_xpath = login_screen_xpaths.get("phone_number_input")
    request.cls.next_button_login_xpath = login_screen_xpaths.get("next_button_login")
    request.cls.verify_button_login_xpath = login_screen_xpaths.get("verify_button_login")
    request.cls.change_mobile_number_xpath = login_screen_xpaths.get("change_mobile_number")
    request.cls.resend_otp_button_xpath = login_screen_xpaths.get("resend_otp_button")
    request.cls.mpin_input_xpath = login_screen_xpaths.get("mpin_input")
    request.cls.reset_mpin_button_xpath = login_screen_xpaths.get("reset_mpin_button")
    request.cls.switch_toggle_button_xpath = login_screen_xpaths.get("switch_toggle_button")
    request.cls.mpin_input_0_xpath = login_screen_xpaths.get("mpin_input_0")
    request.cls.mpin_input_1_xpath = login_screen_xpaths.get("mpin_input_1")
    request.cls.mpin_input_2_xpath = login_screen_xpaths.get("mpin_input_2")
    request.cls.mpin_input_3_xpath = login_screen_xpaths.get("mpin_input_3")

####Login flow test cases
def language_next(driver, obj, test_flow_steps):
    with allure.step("1. Next button on language selection screen"):
        # Use smart_click for robust finding (XPath -> DOM Text -> OCR)
        if not smart_click(driver, "Next Button (Language)", obj.language_next_xpath, "Next"):
            pytest.fail("Could not find or click the 'Next button on language selection' button.")
        test_flow_steps.append({"step": "Click Next button on language selection", "status": "Success"})

def picture_permissions(driver, obj, test_flow_steps):      
    with allure.step("2. Allow picture"):
        if not smart_click(driver, "While using the app (allow picture)", obj.allow_picture_button_xpath, "While using the app"):
            pytest.fail("Could not find or click the 'Allow picture' button.")
        test_flow_steps.append({"step": "Allow picture permission", "status": "Success"})

def login_permissions_location(driver, obj, test_flow_steps):   
    with allure.step("3. Allow location"):
        if not smart_click(driver, "While using (allow location)", obj.allow_location_button_xpath, "While using"):
            pytest.fail("Could not find or click the 'Allow location' button.")
        test_flow_steps.append({"step": "Allow location permission", "status": "Success"})

def login_permissions_audio(driver, obj, test_flow_steps):
    with allure.step("4. Allow audio"):
        if not smart_click(driver, "While using the app (allow audio)", obj.allow_audio_button_xpath, "While using the app"):
            pytest.fail("Could not find or click the 'Allow audio' button.")
        test_flow_steps.append({"step": "Allow audio permission", "status": "Success"})

def login_permissions_notifications(driver, obj, test_flow_steps):
    with allure.step("5. Allow notifications"):
        if not smart_click(driver, "Allow notifications", obj.allow_notifications_button_xpath, "Allow"):
            pytest.fail("Could not find or click the 'Allow notifications' button.")
        test_flow_steps.append({"step": "Allow notifications permission", "status": "Success"})

def login_enter_phone(driver, obj, test_flow_steps):
    with allure.step("6. Enter phone number"):
        phone_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((AppiumBy.XPATH, obj.phone_number_input_xpath))
        )
        phone_input.clear()
        phone_input.send_keys("7660852538")
        test_flow_steps.append({"step": "Enter valid phone number", "status": "Success", "value": "7660852538"})

def login_submit_phone(driver, obj, test_flow_steps):
    with allure.step("7. Tap next button"):
        if not smart_click(driver, "Next (login)", obj.next_button_login_xpath, "Next"):
            pytest.fail("Could not find or click the 'Next' button after entering phone number.")
        test_flow_steps.append({"step": "Click Next after entering phone number", "status": "Success"})
    
# def login_verify_otp(driver, obj, test_flow_steps):
#     with allure.step("8. Wait for OTP and verify"):
#         time.sleep(20)
#         if not smart_click(driver, "Verify (login)", obj.verify_button_login_xpath, "Verify"):
#             pytest.fail("Could not find or click the 'Verify' button.")
#         test_flow_steps.append({"step": "Click Verify OTP", "status": "Success"})

def login_enter_mpin(driver, obj, test_flow_steps):
    with allure.step("9. Enter MPIN"):
        mpin_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((AppiumBy.XPATH, obj.mpin_input_xpath))
        )
        mpin_input.clear()
        mpin_input.send_keys("1234")
        test_flow_steps.append({"step": "Enter valid MPIN", "status": "Success", "value": "1234"})

def login_submit_mpin(driver, obj, test_flow_steps):
    with allure.step("10. Submit MPIN"):
        if not smart_click(driver, "Submit MPIN", obj.verify_button_login_xpath, "Verify"):
            pytest.fail("Could not find or click the 'Submit MPIN' button.")
        test_flow_steps.append({"step": "Click Submit MPIN", "status": "Success"})

def login_change_mobile_number(driver, obj, test_flow_steps):
    with allure.step("11. Change mobile number"):
        if not smart_click(driver, "Change Mobile Number", obj.change_mobile_number_xpath, "Change Mobile Number"):
            pytest.fail("Could not find or click the 'Change Mobile Number' button.")
        test_flow_steps.append({"step": "Click Change Mobile Number", "status": "Success"})

def login_resend_otp(driver, obj, test_flow_steps):
    with allure.step("12. Resend OTP"):
        if not smart_click(driver, "Resend OTP", obj.resend_otp_button_xpath, "Resend OTP"):
            pytest.fail("Could not find or click the 'Resend OTP' button.")
        test_flow_steps.append({"step": "Click Resend OTP", "status": "Success"})

def login_reset_mpin(driver, obj, test_flow_steps):
    with allure.step("13. Reset MPIN"):
        if not smart_click(driver, "Reset MPIN", obj.reset_mpin_button_xpath, "Reset MPIN"):
            pytest.fail("Could not find or click the 'Reset MPIN' button.")
        test_flow_steps.append({"step": "Click Reset MPIN", "status": "Success"})

def login_switch_toggle(driver, obj, test_flow_steps):
    with allure.step("14. Switch toggle"):
        if not smart_click(driver, "Switch Toggle", obj.switch_toggle_button_xpath, "Switch"):
            pytest.fail("Could not find or click the 'Switch Toggle' button.")
        test_flow_steps.append({"step": "Click Switch Toggle", "status": "Success"})

def login_enter_mpin_digits(driver, obj, test_flow_steps):
    with allure.step("15. Enter MPIN digits"):
        mpin_digits = ["1", "2", "3", "4"]
        mpin_input_xpaths = [
            obj.mpin_input_0_xpath,
            obj.mpin_input_1_xpath,
            obj.mpin_input_2_xpath,
            obj.mpin_input_3_xpath,
        ]
        
        for digit, xpath in zip(mpin_digits, mpin_input_xpaths):
            mpin_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath))
            )
            mpin_input.clear()
            mpin_input.send_keys(digit)
            test_flow_steps.append({"step": f"Enter MPIN digit {digit}", "status": "Success", "value": digit})