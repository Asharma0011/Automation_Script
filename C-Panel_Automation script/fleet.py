from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import random
import string
from pathlib import Path


# =========================
# CONFIG
# =========================
BASE_URL = "https://afm2020.com/"
CORPORATE_ID = "AFMDEMO"
USERNAME = "Asharma"
PASSWORD = "Avaal@123"

GLOBAL_TIMEOUT = 20000
LOG_PATH = Path(__file__).parent / "fleet_create.log"


# =========================
# UTILITIES
# =========================
def log(msg: str):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass
    print(msg)


def screenshot(page, name: str):
    try:
        path = Path(__file__).parent / name
        page.screenshot(path=str(path), full_page=True)
        log(f"Screenshot saved: {path}")
    except Exception as e:
        log(f"Screenshot failed: {e}")


def random_alpha(n: int) -> str:
    return "".join(random.choices(string.ascii_letters, k=n))


def random_alphanum(n: int) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


# =========================
# FRAMEWORK
# =========================
class UIActions:
    def __init__(self, page):
        self.page = page
        self.page.set_default_timeout(GLOBAL_TIMEOUT)

    # ---------- Generic ----------
    def wait_visible(self, selector: str, timeout: int = GLOBAL_TIMEOUT):
        self.page.locator(selector).first.wait_for(state="visible", timeout=timeout)
        return self.page.locator(selector).first

    def wait_hidden(self, selector: str, timeout: int = GLOBAL_TIMEOUT):
        self.page.locator(selector).first.wait_for(state="hidden", timeout=timeout)

    def is_visible(self, selector: str, timeout: int = 2000) -> bool:
        try:
            self.page.locator(selector).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def click(self, selector: str, timeout: int = GLOBAL_TIMEOUT):
        loc = self.wait_visible(selector, timeout)
        loc.scroll_into_view_if_needed()
        loc.click()
        log(f"Clicked: {selector}")

    def click_first_available(self, selectors, timeout: int = 5000):
        last_error = None
        for selector in selectors:
            try:
                self.click(selector, timeout)
                return selector
            except Exception as e:
                last_error = e
        raise Exception(f"Could not click any selector from list: {selectors}. Last error: {last_error}")

    def click_text_exact(self, text_value: str, timeout: int = 5000):
        loc = self.page.get_by_text(text_value, exact=True).first
        loc.wait_for(state="visible", timeout=timeout)
        loc.scroll_into_view_if_needed()
        loc.click()
        log(f"Clicked text: {text_value}")

    def fill(self, selector: str, value: str, timeout: int = GLOBAL_TIMEOUT):
        loc = self.wait_visible(selector, timeout)
        loc.scroll_into_view_if_needed()
        loc.click()
        loc.fill(value)
        log(f"Filled {selector} -> {value}")

    def fill_first_available(self, selectors, value: str, timeout: int = 5000):
        last_error = None
        for selector in selectors:
            try:
                self.fill(selector, value, timeout)
                return selector
            except Exception as e:
                last_error = e
        raise Exception(f"Could not fill any selector from list: {selectors}. Last error: {last_error}")

    def input_value(self, selector: str) -> str:
        return self.page.locator(selector).first.input_value().strip()

    def wait_until_enabled(self, selector: str, timeout: int = 5000):
        self.page.wait_for_function(
            """sel => {
                const el = document.querySelector(sel);
                return !!el && !el.disabled && !el.readOnly;
            }""",
            arg=selector,
            timeout=timeout
        )

    def blur(self, selector: str):
        loc = self.page.locator(selector).first
        loc.press("Tab")
        log(f"Blur triggered on: {selector}")

    # ---------- Smart field entry ----------
    def set_text_once(self, selector: str, value: str, timeout: int = 5000, verify: bool = True):
        self.wait_visible(selector, timeout)
        try:
            self.wait_until_enabled(selector, timeout=3000)
        except Exception:
            pass

        loc = self.page.locator(selector).first
        existing = loc.input_value().strip()
        if existing == value or value in existing:
            log(f"Already set {selector} -> {existing}")
            return True

        loc.scroll_into_view_if_needed()
        loc.click()
        loc.press("Control+A")
        loc.press("Backspace")
        loc.type(value, delay=80)

        if verify:
            entered = loc.input_value().strip()
            if entered != value and value not in entered:
                raise Exception(f"Value mismatch for {selector}. Expected '{value}', got '{entered}'")

        log(f"Set once {selector} -> {loc.input_value().strip()}")
        return True

    def set_text_with_blur(self, selector: str, value: str, timeout: int = 5000, digits_only_compare: bool = False):
        self.wait_visible(selector, timeout)
        try:
            self.wait_until_enabled(selector, timeout=3000)
        except Exception:
            pass

        loc = self.page.locator(selector).first
        existing = loc.input_value().strip()

        if digits_only_compare:
            existing_digits = "".join(ch for ch in existing if ch.isdigit())
            value_digits = "".join(ch for ch in value if ch.isdigit())
            if existing_digits == value_digits:
                log(f"Already set {selector} -> {existing}")
                return True
        else:
            if existing == value or value in existing:
                log(f"Already set {selector} -> {existing}")
                return True

        loc.scroll_into_view_if_needed()
        loc.click()
        loc.press("Control+A")
        loc.press("Backspace")
        loc.type(value, delay=100)
        loc.press("Tab")

        entered = loc.input_value().strip()

        if digits_only_compare:
            entered_digits = "".join(ch for ch in entered if ch.isdigit())
            value_digits = "".join(ch for ch in value if ch.isdigit())
            if entered_digits != value_digits:
                raise Exception(
                    f"Blur entry failed for {selector}. Expected digits '{value_digits}', got '{entered}'"
                )
        else:
            if entered != value and value not in entered:
                raise Exception(
                    f"Blur entry failed for {selector}. Expected '{value}', got '{entered}'"
                )

        log(f"Set with blur {selector} -> {entered}")
        return True

    # ---------- Select2 ----------
    def select2_choose_first(self, container_selector: str, label: str):
        self.click(container_selector)

        option_sets = [
            ".select2-results__option:not([aria-disabled='true'])",
            ".select2-results li"
        ]

        for option_selector in option_sets:
            try:
                self.page.locator(option_selector).first.wait_for(state="visible", timeout=4000)
                options = self.page.locator(option_selector)
                count = options.count()
                for i in range(count):
                    text = options.nth(i).inner_text().strip()
                    if text and text.lower() not in ["select", "searching..."]:
                        options.nth(i).click()
                        log(f"{label} selected: {text}")
                        return text
            except Exception:
                continue

        self.page.keyboard.press("ArrowDown")
        self.page.keyboard.press("Enter")
        log(f"{label} selected via keyboard")
        return True

    # ---------- Address autocomplete ----------
    def set_address_autocomplete(self, selector: str, address_text: str):
        self.wait_visible(selector)
        loc = self.page.locator(selector).first
        loc.scroll_into_view_if_needed()
        loc.click()
        loc.press("Control+A")
        loc.press("Backspace")
        loc.type(address_text, delay=120)

        suggestion_selectors = [
            ".pac-item",
            ".ui-menu-item",
            ".autocomplete-suggestion",
            "li[role='option']",
            ".tt-suggestion",
        ]

        for suggestion_selector in suggestion_selectors:
            try:
                self.page.locator(suggestion_selector).first.wait_for(state="visible", timeout=4000)
                first = self.page.locator(suggestion_selector).first
                text = first.inner_text().strip()
                first.click()
                log(f"Address selected from suggestions: {text}")
                return True
            except Exception:
                continue

        loc.press("ArrowDown")
        loc.press("Enter")
        log("Address selected by keyboard fallback")
        return True

    # ---------- Waiting helpers ----------
    def wait_for_page_ready(self):
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_load_state("networkidle")

    def wait_for_modal_open(self, modal_title_text: str = "Create Fleet"):
        self.page.get_by_text(modal_title_text, exact=True).first.wait_for(state="visible", timeout=10000)
        log(f"Modal visible: {modal_title_text}")

    def wait_for_success_or_stable(self):
        self.page.wait_for_load_state("networkidle")
        log("Page/network stabilized after action")


# =========================
# BUSINESS FLOW
# =========================
class FleetCreator:
    def __init__(self, page):
        self.page = page
        self.ui = UIActions(page)

    def login(self):
        log("Opening site")
        self.page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        self.ui.wait_for_page_ready()

        log("Logging in")
        self.ui.set_text_once("#txtCorporateId", CORPORATE_ID)
        self.ui.set_text_once("#txtUserName", USERNAME)
        self.ui.set_text_with_blur("#txtPassword", PASSWORD)

        self.ui.click_first_available([
            "#signin",
            "button:has-text('Sign In')",
            "text=Sign In",
        ])
        self.ui.wait_for_page_ready()

    def open_cpanel(self):
        log("Opening C-PANEL")
        try:
            self.ui.click("a[data-id='#MNU00005']")
        except Exception:
            self.ui.click_first_available([
                "a:has-text('C-PANEL')",
                "a:has-text('C Panel')",
            ])
        self.ui.wait_for_page_ready()

    def open_fleet_page(self):
        log("Opening Fleet page")
        try:
            self.ui.click_text_exact("Fleet")
        except Exception:
            self.ui.click_first_available([
                "a:has-text('Fleet')",
                "text=Fleet",
                "li:has-text('Fleet')",
                "a[href*='Fleet']",
                "a[href*='fleet']",
            ])
        self.ui.wait_for_page_ready()

    def open_new_fleet_modal(self):
        log("Opening New Fleet modal")
        self.ui.click_first_available([
            "#btnAddFleet",
            "button:has-text('New')",
            "a:has-text('New')",
            "text=New",
        ])
        self.ui.wait_for_modal_open("Create Fleet")

    def fill_fleet_form(self):
        fleet_name = "AUTO_FLEET_" + random_alpha(4)
        address_value = "Toronto"
        phone_no = "9876543210"
        fax_no = "1234567890"
        email_id = f"fleet_{random_alphanum(4).lower()}@mail.com"
        postal_code = "L6T4V2"
        remarks = "Fleet created through Playwright automation"

        log("Filling Fleet form")

        try:
            log("STEP 1: Name")
            self.ui.fill_first_available(
                ["input[name='Name']", "#txtName", "#txtFleetName"],
                fleet_name
            )
            log("STEP 1 DONE: Name filled")

            log("STEP 2: Company")
            if self.ui.is_visible("#select2-ddlCompany-container", timeout=3000):
                self.ui.select2_choose_first("#select2-ddlCompany-container", "Company")
                log("STEP 2 DONE: Company selected")
            else:
                log("STEP 2 SKIPPED: Company selector not visible")

            log("STEP 3: Address")
            address_selector = None
            for sel in [
                "input[placeholder*='Search By Address']",
                "#txtAddress1",
                "input[name='FirstLineOfAddress']",
            ]:
                if self.ui.is_visible(sel, timeout=2000):
                    address_selector = sel
                    break

            if not address_selector:
                raise Exception("STEP 3 FAILED: Address field not found")

            self.ui.set_address_autocomplete(address_selector, address_value)
            log(f"STEP 3 DONE: Address filled using {address_selector}")

            log("STEP 4: Phone")
            self.ui.set_text_with_blur("#txtFleetPhone", phone_no, digits_only_compare=True)
            log("STEP 4 DONE: Phone filled")

            log("STEP 5: Fax")
            fax_done = False
            for selector in ["#txtFleetFax", "#txtFax"]:
                if self.ui.is_visible(selector, timeout=1000):
                    try:
                        self.ui.set_text_once(selector, fax_no)
                        log(f"STEP 5 DONE: Fax filled using {selector}")
                        fax_done = True
                        break
                    except Exception as e:
                        log(f"STEP 5 WARNING: Fax failed on {selector}: {e}")
            if not fax_done:
                log("STEP 5 SKIPPED: Fax field not available")

            log("STEP 6: Email")
            email_done = False
            for selector in ["#txtFleetEmail", "#txtEmail"]:
                if self.ui.is_visible(selector, timeout=1000):
                    try:
                        self.ui.set_text_once(selector, email_id)
                        log(f"STEP 6 DONE: Email filled using {selector}")
                        email_done = True
                        break
                    except Exception as e:
                        log(f"STEP 6 WARNING: Email failed on {selector}: {e}")
            if not email_done:
                log("STEP 6 SKIPPED: Email field not available")

            log("STEP 7: Country")
            if self.ui.is_visible("#select2-ddlCountry-container", timeout=3000):
                self.ui.select2_choose_first("#select2-ddlCountry-container", "Country")
                log("STEP 7 DONE: Country selected")
            else:
                log("STEP 7 SKIPPED: Country selector not visible")

            log("STEP 8: State")
            if self.ui.is_visible("#select2-ddlState-container", timeout=3000):
                self.ui.select2_choose_first("#select2-ddlState-container", "State/Province")
                log("STEP 8 DONE: State selected")
            else:
                log("STEP 8 SKIPPED: State selector not visible")

            log("STEP 9: City")
            if self.ui.is_visible("#select2-ddlCity-container", timeout=3000):
                self.ui.select2_choose_first("#select2-ddlCity-container", "City")
                log("STEP 9 DONE: City selected")
            else:
                log("STEP 9 SKIPPED: City selector not visible")

            log("STEP 10: Postal Code")
            self.ui.set_text_with_blur("#txtFleetZip", postal_code)
            log("STEP 10 DONE: Postal Code filled")

            log("STEP 11: Remarks")
            remarks_done = False
            for sel in ["textarea[name='Remarks']", "#txtRemarks"]:
                if self.ui.is_visible(sel, timeout=1000):
                    self.ui.set_text_once(sel, remarks)
                    log(f"STEP 11 DONE: Remarks filled using {sel}")
                    remarks_done = True
                    break
            if not remarks_done:
                log("STEP 11 SKIPPED: Remarks field not available")

            try:
                log(f"DEBUG Phone value: {self.ui.input_value('#txtFleetPhone')}")
            except Exception as e:
                log(f"DEBUG Phone read failed: {e}")

            try:
                log(f"DEBUG Postal value: {self.ui.input_value('#txtFleetZip')}")
            except Exception as e:
                log(f"DEBUG Postal read failed: {e}")

        except Exception as e:
            screenshot(self.page, "fill_fleet_form_failed.png")
            raise Exception(f"fill_fleet_form failed: {e}")

    def save(self):
        log("Saving Fleet")
        self.ui.click_first_available([
            "#btnFleetSubmit",
            "#btnSave",
            "button:has-text('Save')",
            "text=Save",
        ], timeout=5000)
        self.ui.wait_for_success_or_stable()

    def run(self):
        try:
            self.login()
            screenshot(self.page, "01_after_login.png")

            self.open_cpanel()
            screenshot(self.page, "02_cpanel_opened.png")

            self.open_fleet_page()
            screenshot(self.page, "03_fleet_page_opened.png")

            self.open_new_fleet_modal()
            screenshot(self.page, "04_fleet_modal_opened.png")

            self.fill_fleet_form()
            screenshot(self.page, "05_fleet_form_filled.png")

            self.save()
            screenshot(self.page, "06_fleet_saved.png")

            log("Fleet creation attempted successfully")

        except Exception as e:
            log(f"Unhandled error: {e}")
            screenshot(self.page, "fleet_create_error.png")
            try:
                html_path = Path(__file__).parent / "fleet_create_error.html"
                html_path.write_text(self.page.content(), encoding="utf-8")
                log(f"Saved page HTML to: {html_path}")
            except Exception as html_err:
                log(f"Failed to save HTML snapshot: {html_err}")
            raise


# =========================
# MAIN
# =========================
def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=120,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )

        context = browser.new_context()
        page = context.new_page()

        try:
            FleetCreator(page).run()
        finally:
            browser.close()


if __name__ == "__main__":
    main()