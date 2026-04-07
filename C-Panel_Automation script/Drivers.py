from playwright.sync_api import sync_playwright, expect
import random
import string
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
LOG_PATH = BASE_DIR / "drivers_create_stable.log"

BASE_URL = "https://afm2020.com/"
CORPORATE_ID = "AFMDEMO"
USERNAME = "Asharma"
PASSWORD = "Avaal@123"

CITY_NAME = "Acme"

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
        "drivers": [
            "#MNU00005 a:has-text('Drivers')",
            "a[href*='Driver']",
            "a[href*='Drivers']",
            "a[href*='DriverList']",
            "a:has-text('Drivers')",
            "text=Drivers",
        ],
    },
    "drivers": {
        "new_button": [
            "#btnAddDriver",
            "#btnAddNewDriver",
            "button:has-text('New')",
            "button:has-text('Add')",
            "a:has-text('New')",
            "a:has-text('Add')",
            "text=New",
            "text=Add",
        ],
        "form_anchor": [
            "#txtDriverFirstName",
            "#txtFirstName",
            "input[name='FirstName']",
            "input[id*='DriverFirstName']",
            "input[id*='FirstName']",
            "text=Create Driver",
        ],
        "first_name": [
            "#txtDriverFirstName",
            "#txtFirstName",
            "input[name='FirstName']",
            "input[id*='DriverFirstName']",
            "input[id*='FirstName']",
            "input[placeholder*='First Name']",
        ],
        "last_name": [
            "#txtDriverLastName",
            "#txtLastName",
            "input[name='LastName']",
            "input[id*='DriverLastName']",
            "input[id*='LastName']",
            "input[placeholder*='Last Name']",
        ],
        "address1": [
            "#txtAddressOne",
            "#txtDriverAddressOne",
            "input[name='Address1']",
            "input[id*='AddressOne']",
            "input[id*='Address1']",
            "input[placeholder*='First Line of Address']",
            "textarea[id*='Address']",
            "input[placeholder*='Address']",
        ],
        "country": [
            "#ddlCountry",
            "select[id*='Country']",
            "select[name*='Country']",
        ],
        "state": [
            "#ddlState",
            "#ddlProvince",
            "select[id*='State']",
            "select[id*='Province']",
            "select[name*='State']",
            "select[name*='Province']",
        ],
        "city": [
            "#select2-ddlDriverCities-container",
            "span#select2-ddlDriverCities-container",
            "span[aria-labelledby='select2-ddlDriverCities-container']",
            "span.select2-selection__rendered[id='select2-ddlDriverCities-container']",
        ],
        "postal_code": [
            "#txtPostalCode",
            "#txtZipCode",
            "input[name='PostalCode']",
            "input[id*='PostalCode']",
            "input[id*='Zip']",
            "input[placeholder*='Postal']",
            "input[placeholder*='Zip']",
        ],
        "phone": [
            "#txtDriverCell1",
            "#txtPhoneNo",
            "#txtMobileNo",
            "input[name='PhoneNo']",
            "input[name='MobileNo']",
            "input[id*='Phone']",
            "input[id*='Mobile']",
            "input[placeholder*='Phone']",
            "input[placeholder*='Mobile']",
        ],
        "remark": [
            "#txtRemark",
            "textarea[id*='Remark']",
            "textarea[name*='Remark']",
        ],
        "document_no": [
            "#txtDriverDocument",
            "#txtDocumentNo",
            "#txtLicenseDocumentNo",
            "input[name*='DocumentNo']",
            "input[id*='DocumentNo']",
            "input[placeholder*='Document No']",
        ],
        "issuing_country": [
            "#ddlIssuingCountry",
            "select[id*='IssuingCountry']",
            "select[name*='IssuingCountry']",
        ],
        "issuing_state": [
            "#ddlIssuingState",
            "#ddlIssuingStateProvince",
            "select[id*='IssuingState']",
            "select[id*='IssuingStateProvince']",
            "select[name*='IssuingState']",
        ],
        "issue_date": [
            "#txtDriverIssueDate",
            "#txtIssueDate",
            "#txtLicenseIssueDate",
            "input[name*='IssueDate']",
            "input[id*='IssueDate']",
            "input[placeholder*='Issue Date']",
        ],
        "expiry_date": [
            "#txtDriverExpiryDate",
            "#txtExpiryDate",
            "#txtLicenseExpiryDate",
            "input[name*='ExpiryDate']",
            "input[id*='ExpiryDate']",
            "input[placeholder*='Expiry Date']",
        ],
        "save": [
            "#btnDriverSubmit",
            "#btnSubmit",
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
            "text=Driver List",
            "text=Drivers",
        ],
        "modal_scroll": [
            ".modal-body",
            ".modal-content",
            ".modal-dialog",
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


def random_digits(n: int) -> str:
    return "".join(random.choices(string.digits, k=n))


def random_canadian_postal_code() -> str:
    valid_letters = "ABCEGHJKLMNPRSTVXY"
    return (
        random.choice(valid_letters)
        + random.choice(string.digits)
        + random.choice(valid_letters)
        + random.choice(string.digits)
        + random.choice(valid_letters)
        + random.choice(string.digits)
    )


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
    _log(f"Filled selector: {selector} with value: {value}")
    return True


def select_first_non_default_option(page, selectors, label, timeout=5000):
    ctx, locator, selector = first_visible_locator(page, selectors, timeout=timeout)
    if locator is None:
        _log(f"{label}: dropdown not found")
        return False

    locator.scroll_into_view_if_needed()

    try:
        options = locator.locator("option")
        count = options.count()
        for i in range(count):
            text = options.nth(i).inner_text().strip()
            value = options.nth(i).get_attribute("value")
            if text and text.lower() != "select" and value not in (None, "", "0"):
                locator.select_option(index=i)
                _log(f"{label}: selected option '{text}' using {selector}")
                return True
    except Exception as e:
        _log(f"{label}: failed to select option from {selector}: {e}")

    return False


def select_select2_option(page, selectors, option_text, timeout=10000):
    ctx, locator, selector = first_visible_locator(page, selectors, timeout=timeout)
    if locator is None:
        _log("City Select2 rendered container not found")
        return False

    try:
        locator.scroll_into_view_if_needed()
        locator.click(timeout=timeout, force=True)
        _log(f"Clicked city dropdown using: {selector}")
        page.wait_for_timeout(1200)

        search_box = None
        for s in [
            "span.select2-container--open input.select2-search__field",
            ".select2-dropdown input.select2-search__field",
            "input.select2-search__field",
        ]:
            try:
                candidate = page.locator(s).last
                candidate.wait_for(state="visible", timeout=2500)
                search_box = candidate
                _log(f"City search box found using: {s}")
                break
            except Exception:
                pass

        if search_box:
            search_box.click(timeout=2000, force=True)
            search_box.fill("")
            if option_text:
                search_box.type(option_text, delay=120)
                _log(f"Typed city text: {option_text}")
                page.wait_for_timeout(1500)

        options = page.locator(
            "//li[contains(@class,'select2-results__option') "
            "and not(contains(@class,'loading-results')) "
            "and not(contains(@class,'select2-results__message'))]"
        )

        try:
            option_count = options.count()
            visible_results = []
            for i in range(option_count):
                txt = options.nth(i).inner_text().strip()
                if txt and txt.lower() != "no results found":
                    visible_results.append(txt)
            _log(f"Visible city results: {visible_results}")
        except Exception as e:
            _log(f"Could not read city results: {e}")

        if option_text:
            try:
                for i in range(options.count()):
                    item = options.nth(i)
                    txt = item.inner_text().strip()
                    if txt.lower() == option_text.strip().lower():
                        item.scroll_into_view_if_needed()
                        item.click(timeout=3000, force=True)
                        page.wait_for_timeout(1200)

                        selected_text = page.locator("#select2-ddlDriverCities-container").inner_text().strip()
                        _log(f"Selected text after exact click: {selected_text}")
                        if selected_text and selected_text.lower() != "select":
                            return True
            except Exception as e:
                _log(f"Exact city click failed: {e}")

        if option_text:
            try:
                for i in range(options.count()):
                    item = options.nth(i)
                    txt = item.inner_text().strip()
                    if option_text.strip().lower() in txt.lower():
                        item.scroll_into_view_if_needed()
                        item.click(timeout=3000, force=True)
                        page.wait_for_timeout(1200)

                        selected_text = page.locator("#select2-ddlDriverCities-container").inner_text().strip()
                        _log(f"Selected text after partial click: {selected_text}")
                        if selected_text and selected_text.lower() != "select":
                            return True
            except Exception as e:
                _log(f"Partial city click failed: {e}")

        try:
            if options.count() > 0:
                first_option = options.first
                first_text = first_option.inner_text().strip()
                _log(f"Trying first available city option: {first_text}")
                first_option.scroll_into_view_if_needed()
                first_option.click(timeout=3000, force=True)
                page.wait_for_timeout(1200)

                selected_text = page.locator("#select2-ddlDriverCities-container").inner_text().strip()
                _log(f"Selected text after first option click: {selected_text}")
                if selected_text and selected_text.lower() != "select":
                    return True
        except Exception as e:
            _log(f"First option click failed: {e}")

        try:
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1200)

            selected_text = page.locator("#select2-ddlDriverCities-container").inner_text().strip()
            _log(f"Selected text after keyboard fallback: {selected_text}")
            if selected_text and selected_text.lower() != "select":
                return True
        except Exception as e:
            _log(f"Keyboard fallback failed: {e}")

        _log("City selection failed: value still not selected")
        return False

    except Exception as e:
        _log(f"Failed Select2 city selection for '{option_text}': {e}")
        return False


def fill_date_field(page, selectors, value, timeout=5000):
    ctx, locator, selector = first_visible_locator(page, selectors, timeout=timeout)
    if locator is None:
        return False

    expect(locator).to_be_visible(timeout=timeout)
    locator.scroll_into_view_if_needed()
    locator.click(timeout=timeout)
    locator.fill("")
    locator.type(value, delay=50)
    locator.press("Tab")
    _log(f"Filled date selector: {selector} with value: {value}")
    return True


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


def scroll_modal_down(page):
    for selector in SELECTORS["drivers"]["modal_scroll"]:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=2000)
            locator.evaluate("(el) => { el.scrollTop = el.scrollHeight; }")
            page.wait_for_timeout(1000)
            _log(f"Scrolled modal using selector: {selector}")
            return True
        except Exception:
            continue

    try:
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(1000)
        _log("Scrolled page using mouse wheel fallback")
        return True
    except Exception as e:
        _log(f"Scroll fallback failed: {e}")
        return False


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


def open_drivers_module(page):
    assert retry_action(
        "Open C-PANEL",
        lambda: click_first(page, SELECTORS["menu"]["c_panel"], timeout=GLOBAL_TIMEOUT),
    ), "C-PANEL menu not found"

    page.wait_for_timeout(1500)

    assert retry_action(
        "Open Drivers Menu",
        lambda: click_first(page, SELECTORS["menu"]["drivers"], timeout=GLOBAL_TIMEOUT),
    ), "Drivers menu not found"

    wait_for_load_settle(page, 2500)
    _log("Drivers module opened")


def click_new_driver(page):
    assert retry_action(
        "Click New Driver",
        lambda: click_first(page, SELECTORS["drivers"]["new_button"], timeout=7000),
    ), "New Driver button not found"

    ready, selector = wait_for_any_visible(page, SELECTORS["drivers"]["form_anchor"], timeout=10000)
    assert ready, "Driver create form did not open"
    _log(f"Driver create form detected using selector: {selector}")


def fill_driver_form(page, data):
    assert retry_action(
        "Fill First Name",
        lambda: fill_first(page, SELECTORS["drivers"]["first_name"], data["first_name"], timeout=5000),
    ), "First Name field not found"

    assert retry_action(
        "Fill Last Name",
        lambda: fill_first(page, SELECTORS["drivers"]["last_name"], data["last_name"], timeout=5000),
    ), "Last Name field not found"

    assert retry_action(
        "Fill Address 1",
        lambda: fill_first(page, SELECTORS["drivers"]["address1"], data["address1"], timeout=5000),
    ), "Address field not found"

    retry_action(
        "Select Country",
        lambda: select_first_non_default_option(page, SELECTORS["drivers"]["country"], "Country", timeout=5000),
        attempts=2,
    )

    retry_action(
        "Select State",
        lambda: select_first_non_default_option(page, SELECTORS["drivers"]["state"], "State", timeout=5000),
        attempts=2,
    )

    page.wait_for_timeout(1500)

    city_selected = retry_action(
        "Select City",
        lambda: select_select2_option(page, SELECTORS["drivers"]["city"], data["city"], timeout=10000),
        attempts=3,
    )

    if not city_selected:
        raise AssertionError("City not selected. Check log for 'Visible city results'.")

    retry_action(
        "Fill Postal Code",
        lambda: fill_first(page, SELECTORS["drivers"]["postal_code"], data["postal_code"], timeout=5000),
        attempts=3,
    )

    retry_action(
        "Fill Phone",
        lambda: fill_first(page, SELECTORS["drivers"]["phone"], data["phone"], timeout=3000),
        attempts=2,
    )

    retry_action(
        "Fill Remark",
        lambda: fill_first(page, SELECTORS["drivers"]["remark"], data["remark"], timeout=3000),
        attempts=2,
    )

    scroll_modal_down(page)

    retry_action(
        "Fill Document No",
        lambda: fill_first(page, SELECTORS["drivers"]["document_no"], data["document_no"], timeout=5000),
        attempts=3,
    )

    retry_action(
        "Select Issuing Country",
        lambda: select_first_non_default_option(
            page, SELECTORS["drivers"]["issuing_country"], "Issuing Country", timeout=5000
        ),
        attempts=2,
    )

    retry_action(
        "Select Issuing State",
        lambda: select_first_non_default_option(
            page, SELECTORS["drivers"]["issuing_state"], "Issuing State", timeout=5000
        ),
        attempts=2,
    )

    retry_action(
        "Fill Issue Date",
        lambda: fill_date_field(page, SELECTORS["drivers"]["issue_date"], data["issue_date"], timeout=5000),
        attempts=3,
    )

    retry_action(
        "Fill Expiry Date",
        lambda: fill_date_field(page, SELECTORS["drivers"]["expiry_date"], data["expiry_date"], timeout=5000),
        attempts=3,
    )

    _log("Driver form fill completed")


def save_driver(page):
    assert retry_action(
        "Click Save",
        lambda: click_first(page, SELECTORS["drivers"]["save"], timeout=7000),
    ), "Save button not found"

    wait_for_load_settle(page, 3000)

    success, selector = wait_for_any_visible(page, SELECTORS["drivers"]["success_indicators"], timeout=10000)
    if success:
        _log(f"Save validation passed with indicator: {selector}")
        return True

    _log("Save validation indicator not found. Checking whether form closed.")
    form_still_visible, form_selector = wait_for_any_visible(page, SELECTORS["drivers"]["form_anchor"], timeout=2500)
    if form_still_visible:
        raise AssertionError(f"Form still visible after save. Selector: {form_selector}")

    _log("Form is no longer visible after save; treating as probable success")
    return True


def build_test_data():
    return {
        "first_name": "AUTOFN" + random_alpha(4),
        "last_name": "AUTOLN" + random_alpha(4),
        "address1": "Driver Address " + random_alphanum(5),
        "city": CITY_NAME,
        "postal_code": random_canadian_postal_code(),
        "phone": "98" + random_digits(8),
        "remark": "Auto created driver",
        "document_no": "DOC" + random_alphanum(6),
        "issue_date": "01/01/2025",
        "expiry_date": "01/01/2027",
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
            open_drivers_module(page)
            click_new_driver(page)
            fill_driver_form(page, test_data)
            save_driver(page)

            take_screenshot(page, "driver_created_stable.png")
            _log("Driver creation completed successfully")

        except Exception as e:
            _log(f"Unhandled error: {e}")
            if page:
                take_screenshot(page, "driver_create_stable_error.png")
                try:
                    html_path = BASE_DIR / "driver_create_stable_error.html"
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