from pathlib import Path
import random
import string
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://afm2020.com/"
CORPORATE_ID = "AFMDEMO"
USERNAME = "Asharma"
PASSWORD = "Avaal@123"

LOG_PATH = Path(__file__).parent / "truck_owners.log"
SCREENSHOT_DIR = Path(__file__).parent
GLOBAL_TIMEOUT = 20000
RETRY_ATTEMPTS = 5
RETRY_DELAY = 2


def _log(message: str) -> None:
    print(message)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as file:
            file.write(message + "\n")
    except Exception:
        pass


def random_alpha(length: int) -> str:
    return "".join(random.choices(string.ascii_letters, k=length))


def random_alphanum(length: int) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def random_digits(length: int) -> str:
    return "".join(random.choices(string.digits, k=length))


def screenshot(page, name: str) -> None:
    path = SCREENSHOT_DIR / name
    try:
        page.screenshot(path=str(path), full_page=True)
        _log(f"Screenshot saved: {path}")
    except Exception as exc:
        _log(f"Screenshot failed for {name}: {exc}")


def safe_wait(page, ms: int) -> None:
    try:
        page.wait_for_timeout(ms)
    except Exception as exc:
        _log(f"safe_wait ignored error: {exc}")


def click_if_exists(page, selector: str, timeout: int = 3000) -> bool:
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.click(selector)
        _log(f"Clicked {selector} on main page")
        return True
    except Exception:
        pass

    try:
        for frame in page.frames:
            try:
                frame.wait_for_selector(selector, timeout=timeout)
                frame.click(selector)
                _log(f"Clicked {selector} in frame {frame.name}")
                return True
            except Exception:
                continue
    except Exception as exc:
        _log(f"click_if_exists frame scan failed: {exc}")

    _log(f"click_if_exists: {selector} not found on page or frames")
    return False


def fill_if_exists(page, selector: str, text: str, timeout: int = 3000) -> bool:
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.fill(selector, text)
        _log(f"Filled {selector} with {text} on main page")
        return True
    except Exception:
        pass

    try:
        for frame in page.frames:
            try:
                frame.wait_for_selector(selector, timeout=timeout)
                frame.fill(selector, text)
                _log(f"Filled {selector} with {text} in frame {frame.name}")
                return True
            except Exception:
                continue
    except Exception as exc:
        _log(f"fill_if_exists frame scan failed: {exc}")

    _log(f"fill_if_exists: {selector} not found on page or frames")
    return False


def retry_action(fn, attempts=RETRY_ATTEMPTS, delay=RETRY_DELAY, *args, **kwargs) -> bool:
    for attempt in range(attempts):
        try:
            ok = fn(*args, **kwargs)
            if ok:
                return True
        except Exception as exc:
            _log(f"retry_action caught exception: {exc}")
        if attempt < attempts - 1:
            time.sleep(delay)
    return False


def retry_select(page, selector: str, **kwargs) -> bool:
    for attempt in range(RETRY_ATTEMPTS):
        try:
            page.wait_for_selector(selector, timeout=GLOBAL_TIMEOUT)
            page.select_option(selector, **kwargs)
            _log(f"Selected option on {selector} {kwargs}")
            return True
        except Exception as exc:
            _log(f"retry_select attempt {attempt + 1} failed for {selector}: {exc}")
            time.sleep(RETRY_DELAY)
    return False


def choose_first_select_option(page, selector: str) -> bool:
    try:
        page.wait_for_selector(selector, timeout=3000)
        options = page.eval_on_selector_all(
            selector + " option",
            "els => els.map(e => ({v: e.value, t: e.textContent, d: e.disabled}))",
        )
        for option in options:
            value = option.get("v")
            if value and str(value).strip() not in ["", "0", "-1"] and not option.get("d"):
                page.select_option(selector, value=value)
                _log(f"Selected first usable option on {selector}: {value}")
                return True
    except Exception as exc:
        _log(f"choose_first_select_option failed for {selector}: {exc}")
    return False


def wait_for_any_selector(page, selectors: list[str], timeout: int = 5000) -> str | None:
    for selector in selectors:
        try:
            page.wait_for_selector(selector, timeout=timeout)
            _log(f"Selector became visible: {selector}")
            return selector
        except Exception:
            continue
    return None


def login(page) -> None:
    _log("Navigating to site...")
    try:
        page.goto(BASE_URL, timeout=60000, wait_until="load")
    except Exception as exc:
        _log(f"Initial goto failed: {exc}; retrying once")
        page.goto(BASE_URL, timeout=60000)

    safe_wait(page, 4000)

    _log("Filling login form...")
    if not retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtCorporateId", text=CORPORATE_ID, timeout=GLOBAL_TIMEOUT):
        raise RuntimeError("Corporate ID field not found")
    if not retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtUserName", text=USERNAME, timeout=GLOBAL_TIMEOUT):
        raise RuntimeError("Username field not found")
    if not retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtPassword", text=PASSWORD, timeout=GLOBAL_TIMEOUT):
        raise RuntimeError("Password field not found")

    clicked = False
    for selector in ["#signin", "button:has-text('Sign In')", "text=Sign In"]:
        if retry_action(click_if_exists, attempts=3, delay=1, page=page, selector=selector, timeout=GLOBAL_TIMEOUT):
            clicked = True
            break

    if not clicked:
        raise RuntimeError("Could not click any sign-in selector")

    safe_wait(page, 5000)
    screenshot(page, "owner_after_login.png")
    _log("Login step completed")


def open_truck_owners_page(page) -> None:
    _log("Opening C-Panel")
    if not retry_action(click_if_exists, attempts=3, delay=1, page=page, selector="a[data-id='#MNU00005']", timeout=GLOBAL_TIMEOUT):
        _log("C-Panel click failed; trying text fallbacks")
        if not retry_action(click_if_exists, attempts=3, delay=1, page=page, selector="a:has-text('C-PANEL')", timeout=GLOBAL_TIMEOUT):
            if not retry_action(click_if_exists, attempts=3, delay=1, page=page, selector="a:has-text('C Panel')", timeout=GLOBAL_TIMEOUT):
                raise RuntimeError("Could not open C-Panel")

    safe_wait(page, 2000)

    _log("Opening Truck Owners page")
    owner_menu_clicked = False
    for selector in [
        "#MNU00005 a:has-text('Truck Owners')",
        "#MNU00005 a:has-text('Truck Owner')",
        "a[href*='TruckOwner']",
        "a[href*='OwnerList']",
        "a:has-text('Truck Owners')",
        "a:has-text('Truck Owner')",
        "text=Truck Owners",
        "text=Truck Owner",
    ]:
        if retry_action(click_if_exists, attempts=3, delay=1, page=page, selector=selector, timeout=GLOBAL_TIMEOUT):
            owner_menu_clicked = True
            break

    if not owner_menu_clicked:
        screenshot(page, "truck_owners_menu_not_found.png")
        raise RuntimeError("Could not open Truck Owners page")

    safe_wait(page, 3000)
    screenshot(page, "truck_owners_page.png")


def open_add_owner_form(page) -> None:
    _log("Opening Add Truck Owner form")
    add_clicked = False

    if retry_action(
        click_if_exists,
        attempts=3,
        delay=1,
        page=page,
        selector="#btnAddNewOwner",
        timeout=GLOBAL_TIMEOUT,
    ):
        _log("Clicked New (Truck Owner) using #btnAddNewOwner")
        add_clicked = True
    else:
        _log("Primary selector failed, trying fallbacks")
        for selector in [
            "#btnAddOwner",
            "button:has-text('New')",
            "button.btn-new",
            "button:has-text('Add Owner')",
            "button:has-text('Add Truck Owner')",
            "text=New",
            "text=Add Owner",
            "text=Add Truck Owner",
        ]:
            if retry_action(click_if_exists, attempts=2, delay=1, page=page, selector=selector, timeout=GLOBAL_TIMEOUT):
                add_clicked = True
                break

    safe_wait(page, 1500)
    screenshot(page, "owner_after_new_click.png")

    if not add_clicked:
        screenshot(page, "add_truck_owner_not_found.png")
        raise RuntimeError("Add Truck Owner button not found")

    form_selector = wait_for_any_selector(
        page,
        [
            "#myTruckOwnerModal",
            "#myOwnerModal",
            "#txtTruckOwnerName",
            "#txtOwnerName",
            "input[name='OwnerName']",
            "text=Truck Owner Details",
            "text=Owner Details",
        ],
        timeout=5000,
    )

    if not form_selector:
        screenshot(page, "owner_form_not_open.png")
        raise RuntimeError("Truck Owner form did not open after clicking New")

    _log(f"Truck Owner form opened via {form_selector}")


def select_company(page) -> bool:
    for selector in [
        "#ddlTruckOwnerCompany",
        "#ddlCompany",
        "select[name='Company']",
    ]:
        try:
            page.wait_for_selector(selector, timeout=3000)
            options = page.eval_on_selector_all(
                selector + " option",
                "els => els.map(e => ({v: e.value, t: e.textContent?.trim(), d: e.disabled}))",
            )
            for option in options:
                value = option.get("v")
                text = option.get("t")
                disabled = option.get("d")
                if value and str(value).strip() not in ["", "0", "-1"] and not disabled:
                    page.select_option(selector, value=value)
                    _log(f"Selected company on {selector}: {text} ({value})")
                    return True
        except Exception as exc:
            _log(f"Company select failed for {selector}: {exc}")

    for selector in [
        "#select2-ddlTruckOwnerCompany-container",
        "#select2-ddlCompany-container",
    ]:
        try:
            if click_if_exists(page, selector, timeout=3000):
                page.wait_for_selector(".select2-results__option, .select2-results li", timeout=3000)
                if click_if_exists(page, ".select2-results__option", timeout=1000):
                    _log(f"Selected company using select2: {selector}")
                    return True
                if click_if_exists(page, ".select2-results li", timeout=1000):
                    _log(f"Selected company using select2 li: {selector}")
                    return True
                page.keyboard.press("ArrowDown")
                page.keyboard.press("Enter")
                _log(f"Selected company using keyboard: {selector}")
                return True
        except Exception as exc:
            _log(f"Company select2 failed for {selector}: {exc}")

    return False


def fill_owner_address(page) -> bool:
    selector = "#txtTruckOwnerAddress1"

    try:
        page.wait_for_selector(selector, timeout=GLOBAL_TIMEOUT)
        page.click(selector)
        page.fill(selector, "")
        page.type(selector, "123 Main Street, Toronto", delay=120)
        _log("Typed address in autocomplete field")

        try:
            page.wait_for_selector(
                ".pac-item, .ui-menu-item, li[role='option']",
                timeout=5000,
            )
            for suggestion_selector in [".pac-item", ".ui-menu-item", "li[role='option']"]:
                if click_if_exists(page, suggestion_selector, timeout=1500):
                    _log(f"Selected address using {suggestion_selector}")
                    return True
        except Exception:
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            _log("Selected address using keyboard fallback")
            return True

        return True
    except Exception as exc:
        _log(f"Address fill failed: {exc}")
        return False


def fill_owner_form(page) -> None:
    owner_name = "AUTO_OWNER_" + random_alpha(5)
    email = f"owner_{random_alphanum(5).lower()}@mailinator.com"

    _log("Filling Truck Owner form with mandatory fields only")

    owner_name_filled = (
        retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtTruckOwnerName", text=owner_name, timeout=GLOBAL_TIMEOUT)
        or retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtOwnerName", text=owner_name, timeout=GLOBAL_TIMEOUT)
        or retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="input[name='OwnerName']", text=owner_name, timeout=GLOBAL_TIMEOUT)
    )
    if not owner_name_filled:
        raise RuntimeError("Owner Name field not found")

    if not select_company(page):
        raise RuntimeError("Company dropdown not found or no option could be selected")

    if not fill_owner_address(page):
        raise RuntimeError("First Line of Address field could not be filled")

    state_selected = False
    for selector in [
        "select#ddlTruckOwnerStates",
        "select#ddlOwnerState",
        "select#ddlTruckOwnerState",
        "select#ddlState",
    ]:
        if choose_first_select_option(page, selector):
            state_selected = True
            break

    if not state_selected:
        for selector in [
            "#select2-ddlTruckOwnerStates-container",
            "#select2-ddlOwnerState-container",
            "#select2-ddlTruckOwnerState-container",
            "#select2-ddlState-container",
        ]:
            if click_if_exists(page, selector, timeout=3000):
                try:
                    page.wait_for_selector(".select2-results__option, .select2-results li", timeout=3000)
                    if click_if_exists(page, ".select2-results__option", timeout=1000) or click_if_exists(page, ".select2-results li", timeout=1000):
                        _log("Selected owner state via select2")
                        state_selected = True
                        break
                except Exception:
                    try:
                        page.keyboard.press("ArrowDown")
                        page.keyboard.press("Enter")
                        _log("Selected owner state via keyboard")
                        state_selected = True
                        break
                    except Exception:
                        pass

    if not state_selected:
        raise RuntimeError("State / Province dropdown not found or no option could be selected")

    city_selected = False
    for selector in [
        "select#ddltruckownerCities",
        "select#ddlOwnerCity",
        "select#ddlTruckOwnerCity",
        "select#ddlCity",
    ]:
        if choose_first_select_option(page, selector):
            city_selected = True
            break

    if not city_selected:
        for selector in [
            "#select2-ddltruckownerCities-container",
            "#select2-ddlOwnerCity-container",
            "#select2-ddlTruckOwnerCity-container",
            "#select2-ddlCity-container",
        ]:
            if click_if_exists(page, selector, timeout=3000):
                try:
                    page.wait_for_selector(".select2-results__option, .select2-results li", timeout=3000)
                    if click_if_exists(page, ".select2-results__option", timeout=1000) or click_if_exists(page, ".select2-results li", timeout=1000):
                        _log("Selected owner city via select2")
                        city_selected = True
                        break
                except Exception:
                    try:
                        page.keyboard.press("ArrowDown")
                        page.keyboard.press("Enter")
                        _log("Selected owner city via keyboard")
                        city_selected = True
                        break
                    except Exception:
                        pass

    if not city_selected:
        raise RuntimeError("City dropdown not found or no option could be selected")
    screenshot(page, "truck_owner_form_filled.png")


def submit_owner_form(page) -> None:
    _log("Submitting Truck Owner form using Save & Close")
    submitted = False
    for selector in [
        "button:has-text('Save & Close')",
        "#btnSaveClose",
        "#btnSaveAndClose",
        "input[value='Save & Close']",
        "text=Save & Close",
    ]:
        if retry_action(click_if_exists, attempts=3, delay=1, page=page, selector=selector, timeout=GLOBAL_TIMEOUT):
            submitted = True
            break

    if not submitted:
        screenshot(page, "truck_owner_submit_not_found.png")
        raise RuntimeError("Could not click Save & Close for Truck Owner form")

    safe_wait(page, 3000)
    screenshot(page, "truck_owner_created.png")
    _log("Truck Owner Save & Close clicked")


def main() -> None:
    browser = None
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
                slow_mo=100,
            )
            page = browser.new_page(viewport={"width": 1440, "height": 900})

            login(page)
            open_truck_owners_page(page)
            open_add_owner_form(page)
            fill_owner_form(page)
            submit_owner_form(page)

            _log("Truck Owner creation flow completed")

        except PlaywrightTimeoutError as exc:
            _log(f"Playwright timeout: {exc}")
            try:
                screenshot(page, "truck_owner_timeout_error.png")
            except Exception:
                pass
            raise
        except Exception as exc:
            _log(f"Unhandled error during Truck Owner script: {exc}")
            try:
                screenshot(page, "truck_owner_error.png")
            except Exception:
                pass
            raise
        finally:
            if browser:
                browser.close()


if __name__ == "__main__":
    main()
