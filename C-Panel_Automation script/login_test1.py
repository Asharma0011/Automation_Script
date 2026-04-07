from playwright.sync_api import sync_playwright
import time
from pathlib import Path

LOG_PATH = Path(__file__).parent / "login_test.log"
GLOBAL_TIMEOUT = 20000
RETRY_ATTEMPTS = 5
RETRY_DELAY = 2


def _log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def _screenshot(page, name):
    path = Path(__file__).parent / name
    try:
        page.screenshot(path=str(path), full_page=True)
        _log(f"Screenshot saved: {path}")
    except Exception as e:
        _log(f"Screenshot failed: {e}")


def safe_wait(page, ms: int):
    try:
        page.wait_for_timeout(ms)
    except Exception:
        pass


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
        _log(f"Fill failed for {selector}: {e}")
        return False


def click_if_exists(page, selector: str, timeout: int = 3000):
    try:
        page.wait_for_selector(selector, timeout=timeout, state="visible")
        page.locator(selector).first.click()
        _log(f"Clicked {selector}")
        return True
    except Exception:
        return False


def retry_action(fn, attempts=RETRY_ATTEMPTS, delay=RETRY_DELAY, *args, **kwargs):
    for i in range(attempts):
        try:
            if fn(*args, **kwargs):
                return True
        except Exception as e:
            _log(f"Retry error: {e}")
        if i < attempts - 1:
            time.sleep(delay)
    return False


# ================= LOGIN TEST ================= #

with sync_playwright() as p:
    browser = None
    try:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=150
        )
        page = browser.new_page()

        # OPEN WEBSITE
        page.goto("https://afm2020.com/", timeout=60000)
        safe_wait(page, 4000)

        # LOGIN FIELDS
        retry_action(fill_if_exists, page=page, selector="#txtCorporateId", text="AFMDEMO")
        retry_action(fill_if_exists, page=page, selector="#txtUserName", text="Asharma")
        retry_action(fill_if_exists, page=page, selector="#txtPassword", text="Avaal@123")

        # CLICK SIGN IN
        for sel in ["#signin", "button:has-text('Sign In')", "text=Sign In"]:
            if retry_action(click_if_exists, page=page, selector=sel):
                break

        safe_wait(page, 5000)

        # VALIDATION (Dashboard / URL / Element)
        if "dashboard" in page.url.lower() or page.locator("text=Dashboard").count() > 0:
            _log("Login successful")
            print("✅ Login Successful")
        else:
            _log("Login might have failed")
            print("❌ Login Failed")

        # SCREENSHOT
        _screenshot(page, "login_result.png")

    except Exception as e:
        _log(f"Error during login test: {e}")
        print("Error:", e)
        if "page" in locals():
            _screenshot(page, "login_error.png")

    finally:
        if browser:
            browser.close()