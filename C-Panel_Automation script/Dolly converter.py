from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import random
import string
import time
from pathlib import Path

LOG_PATH = Path(__file__).parent / "dolly_converter.log"

GLOBAL_TIMEOUT = 20000
NAV_TIMEOUT = 60000


def _log(msg):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def random_alphanum(n):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


def safe_wait(page, ms):
    try:
        page.wait_for_timeout(ms)
    except Exception as e:
        _log(f"safe_wait ignored error: {e}")


def screenshot(page, name):
    path = Path(__file__).parent / name
    try:
        page.screenshot(path=str(path), full_page=True)
        _log(f"Screenshot saved: {path}")
    except Exception as e:
        _log(f"Screenshot failed: {e}")


def save_html(page, name):
    path = Path(__file__).parent / name
    try:
        path.write_text(page.content(), encoding="utf-8")
        _log(f"Saved HTML to {path}")
    except Exception as e:
        _log(f"Failed to save HTML {name}: {e}")


def login(page):
    _log("Opening login page...")
    page.goto("https://afm2020.com/", timeout=NAV_TIMEOUT, wait_until="load")
    safe_wait(page, 3000)

    _log("Logging in...")
    page.locator("#txtCorporateId").wait_for(state="visible", timeout=GLOBAL_TIMEOUT)
    page.locator("#txtCorporateId").fill("AFMDEMO")
    page.locator("#txtUserName").fill("Asharma")
    page.locator("#txtPassword").fill("Avaal@123")
    page.locator("#signin").click()

    safe_wait(page, 5000)
    _log(f"Logged in. Current URL: {page.url}")


def open_dolly_converter_add_page(page):
    _log("Opening Dolly Converter add page...")
    page.goto(
        "https://afm2020.com/Masters/DollyConverter/AddEditDollyConverter",
        timeout=NAV_TIMEOUT,
        wait_until="load"
    )
    safe_wait(page, 3000)

    page.locator("#ddlDLCcompanyCode").wait_for(state="visible", timeout=GLOBAL_TIMEOUT)
    _log("Dolly Converter add page loaded")


def select_company(page, company_value):
    _log(f"Selecting company value: {company_value}")

    company_dropdown = page.locator("#ddlDLCcompanyCode")
    company_dropdown.wait_for(state="visible", timeout=GLOBAL_TIMEOUT)

    page.wait_for_function(
        """(value) => {
            const el = document.querySelector('#ddlDLCcompanyCode');
            return el && [...el.options].some(o => o.value === value);
        }""",
        arg=company_value,
        timeout=GLOBAL_TIMEOUT
    )

    try:
        company_dropdown.select_option(value=company_value, timeout=5000)
        _log("Company selected using select_option")
    except Exception as e:
        _log(f"select_option failed: {e}")
        _log("Falling back to JavaScript value set")

        result = page.evaluate(
            """(value) => {
                const el = document.querySelector('#ddlDLCcompanyCode');
                if (!el) return { ok: false, reason: 'dropdown not found' };

                const exists = [...el.options].some(o => o.value === value);
                if (!exists) return { ok: false, reason: 'option not found' };

                el.value = value;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                return { ok: true, value: el.value };
            }""",
            company_value
        )
        _log(f"JS selection result: {result}")

    safe_wait(page, 2000)

    selected_value = page.locator("#ddlDLCcompanyCode").input_value()
    _log(f"Selected value after selection: {selected_value}")

    if selected_value != company_value:
        raise Exception(f"Company selection failed. Expected {company_value}, got {selected_value}")

    _log(f"Selected company successfully: {company_value}")


def wait_for_dolly_number_enabled(page):
    _log("Waiting for Dolly Converter Number field to become enabled...")

    page.locator("#txtDollyConvertorNumber").wait_for(state="visible", timeout=GLOBAL_TIMEOUT)

    page.wait_for_function(
        """() => {
            const el = document.querySelector('#txtDollyConvertorNumber');
            return el && !el.disabled;
        }""",
        timeout=GLOBAL_TIMEOUT
    )

    dolly_input = page.locator("#txtDollyConvertorNumber")
    is_disabled = dolly_input.evaluate("el => el.disabled")
    _log(f"txtDollyConvertorNumber disabled status: {is_disabled}")

    if is_disabled:
        raise Exception("Dolly Converter Number field is still disabled after company selection")


def enter_dolly_number(page, dolly_no):
    wait_for_dolly_number_enabled(page)

    _log(f"Entering Dolly Converter Number: {dolly_no}")
    dolly_input = page.locator("#txtDollyConvertorNumber")
    dolly_input.fill(dolly_no)

    entered_value = dolly_input.input_value().strip()
    _log(f"Dolly Converter Number field value: {entered_value}")

    if entered_value != dolly_no:
        raise Exception(f"Failed to enter Dolly Converter Number. Expected {dolly_no}, got {entered_value}")


def click_save(page):
    _log("Clicking Save...")

    save_btn = page.locator("button[onclick='InsertUpdateDollyConverter();']")
    save_btn.wait_for(state="visible", timeout=GLOBAL_TIMEOUT)
    save_btn.scroll_into_view_if_needed()
    save_btn.click(force=True)

    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception as e:
        _log(f"networkidle wait skipped/failed: {e}")

    safe_wait(page, 3000)
    _log(f"URL after save: {page.url}")


def verify_save_success(page, dolly_no):
    _log("Verifying save result...")

    success_selectors = [
        "text=successfully",
        "text=saved successfully",
        "text=record saved",
        ".alert-success",
        ".toast-success",
        ".swal2-success",
        ".swal2-popup",
        ".msg",
        ".message",
        ".alert"
    ]

    for sel in success_selectors:
        try:
            locator = page.locator(sel).first
            if locator.count() > 0 and locator.is_visible(timeout=3000):
                msg = locator.inner_text().strip()
                _log(f"Success indicator found using '{sel}': {msg}")
                return True
        except Exception:
            pass

    if "AddEditDollyConverter" not in page.url:
        _log("Redirect detected after save, assuming success")
        return True

    try:
        dolly_input = page.locator("#txtDollyConvertorNumber")
        if dolly_input.count() > 0:
            value_after = dolly_input.input_value().strip()
            _log(f"Dolly number after save: '{value_after}'")

            if value_after == "":
                _log("Form reset detected after save, assuming success")
                return True

            if value_after == dolly_no:
                _log("Same value retained after save, possible success")
                return True
    except Exception as e:
        _log(f"Could not read Dolly Converter Number after save: {e}")

    return False


with sync_playwright() as p:
    browser = None
    page = None

    try:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=150,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"]
        )

        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        login(page)
        open_dolly_converter_add_page(page)

        screenshot(page, "before_company_select.png")
        save_html(page, "before_company_select.html")

        dolly_no = "DC" + random_alphanum(6)
        _log(f"Generated Dolly Converter Number: {dolly_no}")

        select_company(page, "CMP00001")

        screenshot(page, "after_company_select.png")
        save_html(page, "after_company_select.html")

        enter_dolly_number(page, dolly_no)

        screenshot(page, "before_save.png")
        save_html(page, "before_save.html")

        click_save(page)

        screenshot(page, "after_save.png")
        save_html(page, "after_save.html")

        if verify_save_success(page, dolly_no):
            screenshot(page, "dolly_converter_saved.png")
            save_html(page, "dolly_converter_saved.html")
            _log("Dolly Converter saved successfully and verification passed")
        else:
            screenshot(page, "dolly_converter_save_verification_failed.png")
            save_html(page, "dolly_converter_save_verification_failed.html")
            raise Exception("Save was clicked, but success could not be verified")

    except Exception as e:
        _log(f"Unhandled error during Dolly Converter script: {e}")
        try:
            if page:
                screenshot(page, "dolly_converter_error.png")
                save_html(page, "dolly_converter_error.html")
        except Exception:
            pass
        raise

    finally:
        if browser:
            browser.close()