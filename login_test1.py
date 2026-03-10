import re
import time
from pathlib import Path
from playwright.sync_api import Page, expect


def _screenshot_on_failure(page: Page, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    try:
        page.screenshot(path=path, full_page=True)
    except Exception:
        pass


def test_login_shows_dashboard(page: Page):
    """Playwright + pytest test: navigate to AFM site, perform login, and verify Dashboard is visible."""
    url = "https://afm2020.com/"

    # Navigate to the site
    page.goto(url)
    page.wait_for_load_state("networkidle")

    # Fill login form
    page.locator("#txtCorporateId").fill("AFMDEMO")
    page.locator("#txtUserName").fill("Asharma")
    page.locator("#txtPassword").fill("Avaal@123")

    # Click the sign in button - try a few robust locator strategies
    try:
        # Prefer role-based locator (button with text containing sign in)
        page.get_by_role("button", name=re.compile(r"sign\s*in", re.I)).click()
    except Exception:
        try:
            # Fallback: button with exact text
            page.locator("button:has-text('Sign In')").click()
        except Exception:
            # Final fallback: any input[type=submit] or button
            page.locator("input[type=submit], button[type=submit], button").first.click()

    # Wait for navigation/network to settle
    page.wait_for_load_state("networkidle")

    # Small pause to let the UI update (helps with flaky apps)
    time.sleep(2)

    # Assert that the Dashboard text is visible
    try:
        # Use exact match to avoid multiple matches (strict mode violation)
        expect(page.get_by_text("Dashboard", exact=True)).to_be_visible(timeout=20000)
    except Exception:
        _screenshot_on_failure(page, "ai/test_failure_screenshot.png")
        raise
