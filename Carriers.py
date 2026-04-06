from playwright.sync_api import sync_playwright
import random
import string
import time
from pathlib import Path

LOG_PATH = Path(__file__).parent / "carriers_create.log"
GLOBAL_TIMEOUT = 20000
RETRY_ATTEMPTS = 5
RETRY_DELAY = 2


def _log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def random_alpha(n):
    return ''.join(random.choices(string.ascii_letters, k=n))


def random_alphanum(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


def _screenshot(page, name):
    path = Path(__file__).parent / name
    _log(f"Saving screenshot to {path}")
    print(f"Saving screenshot to {path}")
    try:
        page.screenshot(path=str(path), full_page=True)
        _log("Screenshot saved")
        print("Screenshot saved")
    except Exception as e:
        _log(f"Screenshot failed: {e}")
        print("Screenshot failed:", e)


def safe_wait(page, ms: int):
    try:
        page.wait_for_timeout(ms)
    except Exception as e:
        _log(f"safe_wait ignored error: {e}")


def click_if_exists(page, selector: str, timeout: int = 3000):
    try:
        page.wait_for_selector(selector, timeout=timeout, state="visible")
        loc = page.locator(selector).first
        loc.scroll_into_view_if_needed()
        safe_wait(page, 300)
        loc.click()
        _log(f"Clicked {selector} on main page")
        return True
    except Exception as e:
        _log(f"Main page click failed for {selector}: {e}")

    try:
        for f in page.frames:
            try:
                f.wait_for_selector(selector, timeout=timeout, state="visible")
                loc = f.locator(selector).first
                loc.scroll_into_view_if_needed()
                safe_wait(page, 300)
                loc.click()
                _log(f"Clicked {selector} in frame {f.name}")
                return True
            except Exception:
                continue
    except Exception as e:
        _log(f"click_if_exists frame scan failed: {e}")

    _log(f"click_if_exists: {selector} not found")
    return False


def click_text_if_exists(page, text_value: str, timeout: int = 3000):
    try:
        loc = page.get_by_text(text_value, exact=True).first
        loc.wait_for(timeout=timeout, state="visible")
        loc.scroll_into_view_if_needed()
        safe_wait(page, 300)
        loc.click()
        _log(f"Clicked text: {text_value}")
        return True
    except Exception as e:
        _log(f"click_text_if_exists failed for {text_value}: {e}")

    try:
        for f in page.frames:
            try:
                loc = f.get_by_text(text_value, exact=True).first
                loc.wait_for(timeout=timeout, state="visible")
                loc.scroll_into_view_if_needed()
                safe_wait(page, 300)
                loc.click()
                _log(f"Clicked text in frame {f.name}: {text_value}")
                return True
            except Exception:
                continue
    except Exception as e:
        _log(f"click_text_if_exists frame scan failed: {e}")

    _log(f"click_text_if_exists: text not found -> {text_value}")
    return False


def fill_if_exists(page, selector: str, text: str, timeout: int = 3000):
    try:
        page.wait_for_selector(selector, timeout=timeout, state="visible")
        loc = page.locator(selector).first
        loc.scroll_into_view_if_needed()
        loc.click()
        safe_wait(page, 200)
        loc.fill(text)
        _log(f"Filled {selector} with {text}")
        return True
    except Exception as e:
        _log(f"fill_if_exists failed for {selector}: {e}")
    return False


def retry_action(fn, attempts=RETRY_ATTEMPTS, delay=RETRY_DELAY, *args, **kwargs):
    for i in range(attempts):
        try:
            ok = fn(*args, **kwargs)
            if ok:
                return True
        except Exception as e:
            _log(f"retry_action exception: {e}")
        if i < attempts - 1:
            time.sleep(delay)
    return False


def select2_choose_first(page, container_selector, label):
    try:
        page.wait_for_selector(container_selector, timeout=4000, state="visible")
        page.locator(container_selector).first.click()
        safe_wait(page, 1000)

        option_selectors = [
            ".select2-results__option:not([aria-disabled='true'])",
            ".select2-results li",
        ]

        for sel in option_selectors:
            try:
                page.wait_for_selector(sel, timeout=3000)
                opts = page.locator(sel)
                count = opts.count()
                for i in range(count):
                    txt = opts.nth(i).inner_text().strip()
                    if txt and txt.lower() not in ["select", "searching..."]:
                        opts.nth(i).click()
                        _log(f"{label} selected: {txt}")
                        return True
            except Exception:
                continue

        page.keyboard.press("ArrowDown")
        safe_wait(page, 300)
        page.keyboard.press("Enter")
        _log(f"{label} selected by keyboard")
        return True

    except Exception as e:
        _log(f"select2_choose_first failed for {label}: {e}")
        return False


with sync_playwright() as p:
    browser = None
    try:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
            slow_mo=150
        )
        page = browser.new_page()

        # OPEN SITE
        page.goto("https://afm2020.com/", timeout=60000, wait_until="load")
        safe_wait(page, 4000)

        # LOGIN
        retry_action(
            fill_if_exists,
            attempts=3,
            delay=1,
            page=page,
            selector="#txtCorporateId",
            text="AFMDEMO",
            timeout=GLOBAL_TIMEOUT
        )
        retry_action(
            fill_if_exists,
            attempts=3,
            delay=1,
            page=page,
            selector="#txtUserName",
            text="Asharma",
            timeout=GLOBAL_TIMEOUT
        )
        retry_action(
            fill_if_exists,
            attempts=3,
            delay=1,
            page=page,
            selector="#txtPassword",
            text="Avaal@123",
            timeout=GLOBAL_TIMEOUT
        )

        for sel in ["#signin", "button:has-text('Sign In')", "text=Sign In"]:
            if retry_action(
                click_if_exists,
                attempts=3,
                delay=1,
                page=page,
                selector=sel,
                timeout=GLOBAL_TIMEOUT
            ):
                break

        safe_wait(page, 5000)

        # OPEN C-PANEL
        _log("Trying to open C-PANEL")
        if not retry_action(
            click_if_exists,
            attempts=3,
            delay=1,
            page=page,
            selector="a[data-id='#MNU00005']",
            timeout=GLOBAL_TIMEOUT
        ):
            retry_action(
                click_if_exists,
                attempts=3,
                delay=1,
                page=page,
                selector="a:has-text('C-PANEL')",
                timeout=GLOBAL_TIMEOUT
            )
            retry_action(
                click_if_exists,
                attempts=3,
                delay=1,
                page=page,
                selector="a:has-text('C Panel')",
                timeout=GLOBAL_TIMEOUT
            )

        safe_wait(page, 3000)
        _screenshot(page, "cpanel_opened.png")

        # OPEN CARRIER (singular)
        _log("Trying to open Carrier menu")
        if not retry_action(
            click_text_if_exists,
            attempts=3,
            delay=2,
            page=page,
            text_value="Carrier",
            timeout=5000
        ):
            carrier_selectors = [
                "a:has-text('Carrier')",
                "text=Carrier",
                "li:has-text('Carrier')",
                "a[href*='Carrier']",
                "a[href*='carrier']",
            ]

            carrier_opened = False
            for sel in carrier_selectors:
                _log(f"Trying carrier selector: {sel}")
                if retry_action(
                    click_if_exists,
                    attempts=3,
                    delay=2,
                    page=page,
                    selector=sel,
                    timeout=5000
                ):
                    _log(f"Opened Carrier using selector: {sel}")
                    carrier_opened = True
                    break

            if not carrier_opened:
                _screenshot(page, "carrier_menu_not_found.png")
                html_path = Path(__file__).parent / "carrier_menu_not_found.html"
                html_path.write_text(page.content(), encoding="utf-8")
                raise Exception("Carrier menu not found after opening C-PANEL")

        safe_wait(page, 4000)
        _screenshot(page, "carrier_page_opened.png")

        # CLICK NEW
        # Update if carrier page uses a different new button selector
        if not retry_action(
            click_if_exists,
            attempts=3,
            delay=1,
            page=page,
            selector="#btnAddCustomerCarrierLocation",
            timeout=5000
        ):
            for sel in [
                "button:has-text('New')",
                "a:has-text('New')",
                "#btnAddCarrier",
                "#btnAddCustomerCarrierLocation",
                "text=New",
            ]:
                if retry_action(
                    click_if_exists,
                    attempts=3,
                    delay=1,
                    page=page,
                    selector=sel,
                    timeout=5000
                ):
                    _log(f"New button clicked using {sel}")
                    break
            else:
                raise Exception("New button not found on Carrier page")

        safe_wait(page, 2500)
        _screenshot(page, "carrier_form_opened.png")

        # WAIT FOR FORM
        # These fields are assumed similar to customer form; update if carrier form uses different IDs
        page.wait_for_selector("#txtPrimaryCCLInfoName", timeout=GLOBAL_TIMEOUT, state="visible")
        _log("Carrier create form opened")

        # TEST DATA
        carrier_name = "AUTO_CARRIER_" + random_alpha(5)
        address = "Toronto Carrier Address " + random_alphanum(5)
        postal_code = "M5V2T6"

        # NAME
        if not retry_action(
            fill_if_exists,
            attempts=3,
            delay=1,
            page=page,
            selector="#txtPrimaryCCLInfoName",
            text=carrier_name,
            timeout=5000
        ):
            raise Exception("Carrier name field not found")

        safe_wait(page, 500)
        page.keyboard.press("Tab")

        # ADDRESS
        if not retry_action(
            fill_if_exists,
            attempts=3,
            delay=1,
            page=page,
            selector="#txtPrimaryCCLInfoAddressOne",
            text=address,
            timeout=5000
        ):
            raise Exception("Address field not found")

        safe_wait(page, 800)
        page.keyboard.press("Tab")

        # STATE
        retry_action(
            select2_choose_first,
            attempts=3,
            delay=1,
            page=page,
            container_selector="#select2-ddlPrimaryCCLInfoState-container",
            label="State"
        )
        safe_wait(page, 1000)

        # CITY
        retry_action(
            select2_choose_first,
            attempts=3,
            delay=1,
            page=page,
            container_selector="#select2-ddlCCLinfoCities-container",
            label="City"
        )
        safe_wait(page, 1000)

        # POSTAL CODE
        retry_action(
            fill_if_exists,
            attempts=3,
            delay=1,
            page=page,
            selector="#txtPrimaryCCLInfoPostalCode",
            text=postal_code,
            timeout=5000
        )
        safe_wait(page, 500)
        page.keyboard.press("Tab")
        safe_wait(page, 1000)

        # OPTIONAL FIELDS - UNCOMMENT IF PRESENT
        # retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtCarrierCode", text="CR" + random_alphanum(4), timeout=5000)
        # retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtMCNumber", text=random_alphanum(6), timeout=5000)
        # retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtUSDOTNumber", text=random_alphanum(8), timeout=5000)
        # retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtEmail", text=f"carrier_{random_alphanum(5)}@mail.com", timeout=5000)
        # retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtPhone", text="1234567890", timeout=5000)

        # SAVE & CLOSE
        if not retry_action(
            click_if_exists,
            attempts=3,
            delay=1,
            page=page,
            selector="#btnCustomerSubmit",
            timeout=5000
        ):
            for sel in [
                "#btnCarrierSubmit",
                "#btnCustomerSubmit",
                "button:has-text('Save & Close')",
                "button:has-text('Save')",
                "text=Save & Close",
                "text=Save",
            ]:
                if retry_action(
                    click_if_exists,
                    attempts=3,
                    delay=1,
                    page=page,
                    selector=sel,
                    timeout=5000
                ):
                    _log(f"Save button clicked using {sel}")
                    break
            else:
                raise Exception("Save button not found")

        _log("Clicked Save & Close")
        safe_wait(page, 5000)

        _screenshot(page, "carrier_created.png")
        _log("Carrier creation attempted")
        print("Carrier creation attempted")

    except Exception as e:
        _log(f"Unhandled error during carrier create script: {e}")
        print("Unhandled error during carrier create script:", e)
        try:
            if "page" in locals():
                _screenshot(page, "carrier_create_error.png")
                html_path = Path(__file__).parent / "carrier_create_error.html"
                html_path.write_text(page.content(), encoding="utf-8")
        except Exception:
            pass
    finally:
        try:
            if browser:
                browser.close()
        except Exception:
            pass