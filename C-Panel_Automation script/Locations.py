from playwright.sync_api import sync_playwright, expect, TimeoutError as PlaywrightTimeoutError
import random
import string
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
LOG_PATH = BASE_DIR / "locations_create_stable.log"

BASE_URL = "https://afm2020.com/"
CORPORATE_ID = "AFMDEMO"
USERNAME = "Asharma"
PASSWORD = "Avaal@123"

GLOBAL_TIMEOUT = 20000
NAV_TIMEOUT = 60000
RETRY_ATTEMPTS = 4
RETRY_DELAY_SEC = 1.5


SELECTORS = {
    "login": {
        "corporate_id": ["#txtCorporateId"],
        "username": ["#txtUserName"],
        "password": ["#txtPassword"],
        "sign_in": [
            "#signin",
            "button:has-text('Sign In')",
            "text=Sign In",
        ],
    },
    "menu": {
        "c_panel": [
            "a[data-id='#MNU00005']",
            "a:has-text('C-PANEL')",
            "a:has-text('C Panel')",
        ],
        "locations": [
            "#MNU00005 a:has-text('Locations')",
            "a[href*='Location']",
            "a[href*='Locations']",
            "a[href*='LocationList']",
            "a:has-text('Locations')",
            "text=Locations",
        ],
    },
    "locations": {
        "new_button": [
            "#btnAddLocation",
            "#btnAddCustomerCarrierLocation",
            "button:has-text('New')",
            "button:has-text('Add')",
            "a:has-text('New')",
            "a:has-text('Add')",
            "text=New",
            "text=Add",
        ],
        "form_anchor": [
            "#txtLocationName",
            "#txtPrimaryCCLInfoName",
            "input[name='LocationName']",
            "input[id*='LocationName']",
            "input[placeholder*='Location']",
        ],
        "name": [
            "#txtLocationName",
            "#txtPrimaryCCLInfoName",
            "input[name='LocationName']",
            "input[id*='LocationName']",
            "input[placeholder*='Location Name']",
            "input[placeholder*='Name']",
        ],
        "address1": [
            "#txtLocationAddressOne",
            "#txtPrimaryCCLInfoAddressOne",
            "input[name='Address1']",
            "input[id*='AddressOne']",
            "input[id*='Address1']",
            "textarea[id*='Address']",
            "input[placeholder*='Address']",
        ],
        "postal_code": [
            "#txtLocationPostalCode",
            "#txtPrimaryCCLInfoPostalCode",
            "input[name='PostalCode']",
            "input[id*='PostalCode']",
            "input[id*='Zip']",
            "input[placeholder*='Postal']",
            "input[placeholder*='Zip']",
        ],
        "location_code": [
            "#txtLocationCode",
            "input[name='LocationCode']",
            "input[id*='LocationCode']",
        ],
        "description": [
            "#txtLocationDescription",
            "textarea[name='Description']",
            "textarea[id*='Description']",
            "input[id*='Description']",
        ],
        "state_select2": [
            "#select2-ddlLocationState-container",
            "#select2-ddlPrimaryCCLInfoState-container",
            "#select2-ddlState-container",
        ],
        "city_select2": [
            "#select2-ddlLocationCity-container",
            "#select2-ddlCCLinfoCities-container",
            "#select2-ddlCity-container",
        ],
        "save": [
            "#btnLocationSubmit",
            "#btnCustomerSubmit",
            "button:has-text('Save & Close')",
            "button:has-text('Save')",
            "input[value='Save & Close']",
            "input[value='Save']",
            "text=Save & Close",
            "text=Save",
        ],
        "success_indicators": [
            "text=successfully",
            "text=Saved successfully",
            "text=updated successfully",
            "text=created successfully",
            "text=Location List",
            "text=Locations",
        ],
    },
}


def _log(msg: str):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def random_alpha(n: int) -> str:
    return "".join(random.choices(string.ascii_letters, k=n))


def random_alphanum(n: int) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def take_screenshot(page, file_name: str):
    path = BASE_DIR / file_name
    try:
        page.screenshot(path=str(path), full_page=True)
        _log(f"Screenshot saved: {path}")
    except Exception as e:
        _log(f"Screenshot failed: {e}")


def retry_action(action_name, fn, attempts=RETRY_ATTEMPTS, delay=RETRY_DELAY_SEC):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            if fn():
                _log(f"{action_name} succeeded on attempt {attempt}")
                return True
        except Exception as e:
            last_error = e
            _log(f"{action_name} failed on attempt {attempt}: {e}")
        if attempt < attempts:
            time.sleep(delay)

    if last_error:
        _log(f"{action_name} exhausted retries. Last error: {last_error}")
    else:
        _log(f"{action_name} exhausted retries.")
    return False


def all_contexts(page):
    contexts = [("main", page)]
    try:
        for idx, frame in enumerate(page.frames):
            contexts.append((f"frame[{idx}]({frame.name or 'no-name'})", frame))
    except Exception as e:
        _log(f"Unable to enumerate frames: {e}")
    return contexts


def first_visible_locator(page, selectors, timeout=2500):
    for selector in selectors:
        for ctx_name, ctx in all_contexts(page):
            try:
                locator = ctx.locator(selector).first
                locator.wait_for(state="visible", timeout=timeout)
                _log(f"Found visible selector '{selector}' in {ctx_name}")
                return ctx, locator, selector
            except Exception:
                continue
    return None, None, None


def click_first(page, selectors, timeout=5000, force=False):
    ctx, locator, selector = first_visible_locator(page, selectors, timeout=timeout)
    if locator is None:
        return False

    expect(locator).to_be_visible(timeout=timeout)
    expect(locator).to_be_enabled(timeout=timeout)
    locator.scroll_into_view_if_needed()
    locator.click(force=force, timeout=timeout)
    _log(f"Clicked selector: {selector}")
    return True


def fill_first(page, selectors, value, timeout=5000):
    ctx, locator, selector = first_visible_locator(page, selectors, timeout=timeout)
    if locator is None:
        return False

    expect(locator).to_be_visible(timeout=timeout)
    locator.scroll_into_view_if_needed()
    locator.click(timeout=timeout)
    locator.fill("")
    locator.fill(value)
    expect(locator).to_have_value(value, timeout=timeout)
    _log(f"Filled selector: {selector} with value: {value}")
    return True


def select2_choose_first(page, container_selectors, label, timeout=5000):
    ctx, locator, selector = first_visible_locator(page, container_selectors, timeout=timeout)
    if locator is None:
        _log(f"{label}: select2 container not found")
        return False

    locator.scroll_into_view_if_needed()
    locator.click(timeout=timeout)
    _log(f"{label}: opened select2 using {selector}")

    option_selectors = [
        ".select2-results__option:not([aria-disabled='true'])",
        ".select2-results li",
    ]

    for option_selector in option_selectors:
        for ctx_name, search_ctx in all_contexts(page):
            try:
                options = search_ctx.locator(option_selector)
                options.first.wait_for(state="visible", timeout=3000)
                count = options.count()
                for i in range(count):
                    opt = options.nth(i)
                    txt = opt.inner_text().strip()
                    if txt and txt.lower() not in {"select", "searching...", "no results found"}:
                        opt.click(timeout=3000)
                        _log(f"{label}: selected option '{txt}' from {ctx_name}")
                        return True
            except Exception:
                continue

    try:
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
        _log(f"{label}: selected first option using keyboard fallback")
        return True
    except Exception as e:
        _log(f"{label}: keyboard fallback failed: {e}")
        return False


def wait_for_any_visible(page, selectors, timeout=7000):
    end = time.time() + (timeout / 1000)
    while time.time() < end:
        ctx, locator, selector = first_visible_locator(page, selectors, timeout=800)
        if locator is not None:
            return True, selector
    return False, None


def wait_for_load_settle(page, short_ms=1200):
    try:
        page.wait_for_load_state("domcontentloaded", timeout=GLOBAL_TIMEOUT)
    except Exception:
        pass
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass
    page.wait_for_timeout(short_ms)


def login(page):
    _log("Opening site")
    page.goto(BASE_URL, timeout=NAV_TIMEOUT, wait_until="load")
    wait_for_load_settle(page, 2000)

    assert retry_action(
        "Fill Corporate ID",
        lambda: fill_first(page, SELECTORS["login"]["corporate_id"], CORPORATE_ID, timeout=GLOBAL_TIMEOUT),
    ), "Corporate ID field not found"

    assert retry_action(
        "Fill Username",
        lambda: fill_first(page, SELECTORS["login"]["username"], USERNAME, timeout=GLOBAL_TIMEOUT),
    ), "Username field not found"

    assert retry_action(
        "Fill Password",
        lambda: fill_first(page, SELECTORS["login"]["password"], PASSWORD, timeout=GLOBAL_TIMEOUT),
    ), "Password field not found"

    assert retry_action(
        "Click Sign In",
        lambda: click_first(page, SELECTORS["login"]["sign_in"], timeout=GLOBAL_TIMEOUT),
    ), "Sign In button not found"

    wait_for_load_settle(page, 3000)
    _log("Login flow completed")


def open_locations_module(page):
    assert retry_action(
        "Open C-PANEL",
        lambda: click_first(page, SELECTORS["menu"]["c_panel"], timeout=GLOBAL_TIMEOUT),
    ), "C-PANEL menu not found"

    page.wait_for_timeout(1500)

    assert retry_action(
        "Open Locations Menu",
        lambda: click_first(page, SELECTORS["menu"]["locations"], timeout=GLOBAL_TIMEOUT),
    ), "Locations menu not found"

    wait_for_load_settle(page, 2500)
    _log("Locations module opened")


def click_new_location(page):
    assert retry_action(
        "Click New Location",
        lambda: click_first(page, SELECTORS["locations"]["new_button"], timeout=7000),
    ), "New Location button not found"

    ready, selector = wait_for_any_visible(page, SELECTORS["locations"]["form_anchor"], timeout=10000)
    assert ready, "Location create form did not open"
    _log(f"Location create form detected using selector: {selector}")


def fill_location_form(page, data):
    assert retry_action(
        "Fill Location Name",
        lambda: fill_first(page, SELECTORS["locations"]["name"], data["location_name"], timeout=5000),
    ), "Location Name field not found"

    assert retry_action(
        "Fill Address 1",
        lambda: fill_first(page, SELECTORS["locations"]["address1"], data["address1"], timeout=5000),
    ), "Address field not found"

    retry_action(
        "Select State",
        lambda: select2_choose_first(page, SELECTORS["locations"]["state_select2"], "State", timeout=5000),
        attempts=3,
    )

    retry_action(
        "Select City",
        lambda: select2_choose_first(page, SELECTORS["locations"]["city_select2"], "City", timeout=5000),
        attempts=3,
    )

    retry_action(
        "Fill Postal Code",
        lambda: fill_first(page, SELECTORS["locations"]["postal_code"], data["postal_code"], timeout=5000),
        attempts=3,
    )

    retry_action(
        "Fill Location Code",
        lambda: fill_first(page, SELECTORS["locations"]["location_code"], data["location_code"], timeout=3000),
        attempts=2,
    )

    retry_action(
        "Fill Description",
        lambda: fill_first(page, SELECTORS["locations"]["description"], data["description"], timeout=3000),
        attempts=2,
    )

    _log("Location form fill completed")


def save_location(page):
    assert retry_action(
        "Click Save",
        lambda: click_first(page, SELECTORS["locations"]["save"], timeout=7000),
    ), "Save button not found"

    wait_for_load_settle(page, 3000)

    success, selector = wait_for_any_visible(page, SELECTORS["locations"]["success_indicators"], timeout=10000)
    if success:
        _log(f"Save validation passed with indicator: {selector}")
        return True

    _log("Save validation indicator not found. Checking whether form closed.")
    form_still_visible, form_selector = wait_for_any_visible(page, SELECTORS["locations"]["form_anchor"], timeout=2500)
    if form_still_visible:
        raise AssertionError(f"Form still visible after save. Selector: {form_selector}")

    _log("Form is no longer visible after save; treating as probable success")
    return True


def build_test_data():
    return {
        "location_name": "AUTO_LOC_" + random_alpha(5),
        "address1": "Toronto Location Address " + random_alphanum(5),
        "postal_code": "M5V2T6",
        "location_code": "LOC" + random_alphanum(4),
        "description": "Auto created location",
    }


def main():
    browser = None
    page = None

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=False,
                slow_mo=100,
                args=["--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
            )

            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()
            page.set_default_timeout(GLOBAL_TIMEOUT)

            test_data = build_test_data()
            _log(f"Test data: {test_data}")

            login(page)
            open_locations_module(page)
            click_new_location(page)
            fill_location_form(page, test_data)
            save_location(page)

            take_screenshot(page, "location_created_stable.png")
            _log("Location creation completed successfully")

        except Exception as e:
            _log(f"Unhandled error: {e}")
            if page:
                take_screenshot(page, "location_create_stable_error.png")
                try:
                    html_path = BASE_DIR / "location_create_stable_error.html"
                    html_path.write_text(page.content(), encoding="utf-8")
                    _log(f"Saved page HTML: {html_path}")
                except Exception as html_err:
                    _log(f"Failed to save page HTML: {html_err}")
            raise

        finally:
            try:
                if browser:
                    browser.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()