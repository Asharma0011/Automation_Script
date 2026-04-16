from playwright.sync_api import sync_playwright
import random
import string
import time
from pathlib import Path

LOG_PATH = Path(__file__).parent / "custom_broker_create.log"
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


def random_num(n):
    return ''.join(random.choices(string.digits, k=n))


def _screenshot(page, name):
    path = Path(__file__).parent / name
    _log(f"Saving screenshot to {path}")
    try:
        page.screenshot(path=str(path), full_page=True)
        _log("Screenshot saved")
    except Exception as e:
        _log(f"Screenshot failed: {e}")


def safe_wait(page, ms: int):
    try:
        page.wait_for_timeout(ms)
    except Exception as e:
        _log(f"safe_wait ignored error: {e}")


def click_if_exists(page, selector: str, timeout: int = 3000):
    try:
        page.wait_for_selector(selector, timeout=timeout, state="visible")
        page.locator(selector).first.click()
        _log(f"Clicked {selector} on main page")
        return True
    except Exception:
        pass

    try:
        for f in page.frames:
            try:
                f.wait_for_selector(selector, timeout=timeout, state="visible")
                f.locator(selector).first.click()
                _log(f"Clicked {selector} in frame {f.name}")
                return True
            except Exception:
                continue
    except Exception as e:
        _log(f"click_if_exists frame scan failed: {e}")

    _log(f"click_if_exists: {selector} not found")
    return False


def fill_if_exists(page, selector: str, text: str, timeout: int = 3000):
    try:
        page.wait_for_selector(selector, timeout=timeout, state="visible")
        loc = page.locator(selector).first
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
        page.set_default_timeout(GLOBAL_TIMEOUT)

        # OPEN SITE
        page.goto("https://afm2020.com/", timeout=60000, wait_until="load")
        safe_wait(page, 3000)

        # LOGIN
        retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtCorporateId", text="AFMDEMO", timeout=GLOBAL_TIMEOUT)
        retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtUserName", text="Asharma", timeout=GLOBAL_TIMEOUT)
        retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtPassword", text="Avaal@123", timeout=GLOBAL_TIMEOUT)

        for sel in ["#signin", "button:has-text('Sign In')", "text=Sign In"]:
            if retry_action(click_if_exists, attempts=3, delay=1, page=page, selector=sel, timeout=GLOBAL_TIMEOUT):
                break

        safe_wait(page, 5000)

        # OPEN C-PANEL
        if not retry_action(click_if_exists, attempts=3, delay=1, page=page, selector="a[data-id='#MNU00005']", timeout=GLOBAL_TIMEOUT):
            retry_action(click_if_exists, attempts=3, delay=1, page=page, selector="a:has-text('C-PANEL')", timeout=GLOBAL_TIMEOUT)
            retry_action(click_if_exists, attempts=3, delay=1, page=page, selector="a:has-text('C Panel')", timeout=GLOBAL_TIMEOUT)

        safe_wait(page, 2000)

        # OPEN CUSTOM BROKERS
        broker_menu_selectors = [
            "#MNU00005 a:has-text('Custom Brokers')",
            "a[href*='CustomBroker']",
            "a[href*='CustomBrokers']",
            "a:has-text('Custom Brokers')",
            "text=Custom Brokers"
        ]

        opened = False
        for sel in broker_menu_selectors:
            if retry_action(click_if_exists, attempts=3, delay=1, page=page, selector=sel, timeout=GLOBAL_TIMEOUT):
                _log(f"Opened Custom Brokers using {sel}")
                opened = True
                break

        if not opened:
            raise Exception("Custom Brokers menu not found")

        safe_wait(page, 3000)

        # CLICK NEW BUTTON
        new_button_selectors = [
            "#btnAddCustomBroker",
            "#btnAddBroker",
            "#btnAddCustomerCarrierLocation",
            "button:has-text('New')",
            "text=New"
        ]

        new_clicked = False
        for sel in new_button_selectors:
            if retry_action(click_if_exists, attempts=3, delay=1, page=page, selector=sel, timeout=5000):
                _log(f"Clicked New using {sel}")
                new_clicked = True
                break

        if not new_clicked:
            raise Exception("New button not found for Custom Broker")

        safe_wait(page, 2500)

        # TEST DATA
        broker_name = "AUTO_BROKER_" + random_alpha(5)
        address1 = "Toronto Broker Address " + random_alphanum(5)
        city_text = "Toronto"
        postal_code = "M5V2T6"
        phone = "647" + random_num(7)
        email = f"broker{random_num(4)}@mailinator.com"

        # FORM FILL
        # NOTE:
        # These selectors may need slight adjustment as per actual Custom Broker screen.
        possible_name_fields = [
            "#txtPrimaryCCLInfoName",
            "#txtBrokerName",
            "#txtCustomBrokerName",
            "input[name='Name']"
        ]

        name_filled = False
        for sel in possible_name_fields:
            if retry_action(fill_if_exists, attempts=2, delay=1, page=page, selector=sel, text=broker_name, timeout=5000):
                name_filled = True
                break

        if not name_filled:
            raise Exception("Custom Broker Name field not found")

        # Address
        for sel in [
            "#txtPrimaryCCLInfoAddressOne",
            "#txtAddress1",
            "#txtBrokerAddress1",
            "input[name='Address1']"
        ]:
            if retry_action(fill_if_exists, attempts=2, delay=1, page=page, selector=sel, text=address1, timeout=5000):
                break

        # State
        for sel in [
            "#select2-ddlPrimaryCCLInfoState-container",
            "#select2-ddlState-container",
            "#select2-ddlBrokerState-container"
        ]:
            if retry_action(select2_choose_first, attempts=2, delay=1, page=page, container_selector=sel, label="State"):
                break

        safe_wait(page, 1000)

        # City
        city_done = False
        for sel in [
            "#select2-ddlCCLinfoCities-container",
            "#select2-ddlCity-container",
            "#select2-ddlBrokerCity-container"
        ]:
            if retry_action(select2_choose_first, attempts=2, delay=1, page=page, container_selector=sel, label="City"):
                city_done = True
                break

        if not city_done:
            for sel in [
                "#txtCity",
                "#txtBrokerCity",
                "input[name='City']"
            ]:
                if retry_action(fill_if_exists, attempts=2, delay=1, page=page, selector=sel, text=city_text, timeout=5000):
                    break

        # Postal Code
        for sel in [
            "#txtPrimaryCCLInfoPostalCode",
            "#txtPostalCode",
            "#txtBrokerPostalCode",
            "input[name='PostalCode']"
        ]:
            if retry_action(fill_if_exists, attempts=2, delay=1, page=page, selector=sel, text=postal_code, timeout=5000):
                break

        # Phone
        for sel in [
            "#txtPhone",
            "#txtBrokerPhone",
            "#txtPrimaryCCLInfoPhone",
            "input[name='Phone']"
        ]:
            if retry_action(fill_if_exists, attempts=2, delay=1, page=page, selector=sel, text=phone, timeout=5000):
                break

        # Email
        for sel in [
            "#txtEmail",
            "#txtBrokerEmail",
            "#txtPrimaryCCLInfoEmail",
            "input[name='Email']"
        ]:
            if retry_action(fill_if_exists, attempts=2, delay=1, page=page, selector=sel, text=email, timeout=5000):
                break

        safe_wait(page, 1000)

        # SAVE
        save_selectors = [
            "#btnCustomBrokerSubmit",
            "#btnBrokerSubmit",
            "#btnCustomerSubmit",
            "button:has-text('Save & Close')",
            "button:has-text('Save')",
            "text=Save & Close",
            "text=Save"
        ]

        save_clicked = False
        for sel in save_selectors:
            if retry_action(click_if_exists, attempts=3, delay=1, page=page, selector=sel, timeout=5000):
                _log(f"Clicked Save using {sel}")
                save_clicked = True
                break

        if not save_clicked:
            raise Exception("Save button not found for Custom Broker")

        safe_wait(page, 5000)

        _screenshot(page, "custom_broker_created.png")
        _log("Custom Broker creation attempted successfully")
        print("Custom Broker creation attempted successfully")

    except Exception as e:
        _log(f"Unhandled error during Custom Broker create script: {e}")
        print("Unhandled error during Custom Broker create script:", e)
        try:
            if "page" in locals():
                _screenshot(page, "custom_broker_create_error.png")
                html_path = Path(__file__).parent / "custom_broker_create_error.html"
                html_path.write_text(page.content(), encoding="utf-8")
        except Exception:
            pass
    finally:
        try:
            if browser:
                browser.close()
        except Exception:
            pass