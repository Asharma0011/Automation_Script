from playwright.sync_api import sync_playwright
import random
import string
import time
from pathlib import Path

LOG_PATH = Path(__file__).parent / "trucks.log"
# Global timeouts and retry counts (increased to reduce flakiness)
GLOBAL_TIMEOUT = 20000  # ms for waiting selectors
RETRY_ATTEMPTS = 5
RETRY_DELAY = 2  # seconds


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
    """Wait for selector on page or any child frames and click if present."""
    # Try main page first
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.click(selector)
        _log(f"Clicked {selector} on main page")
        return True
    except Exception:
        pass

    # Try frames
    try:
        for f in page.frames:
            try:
                f.wait_for_selector(selector, timeout=timeout)
                f.click(selector)
                _log(f"Clicked {selector} in frame {f.name}")
                return True
            except Exception:
                continue
    except Exception as e:
        _log(f"click_if_exists frame scan failed: {e}")

    _log(f"click_if_exists: {selector} not found on page or frames")
    return False


def fill_if_exists(page, selector: str, text: str, timeout: int = 3000):
    # Try main page first
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.fill(selector, text)
        _log(f"Filled {selector} with {text} on main page")
        return True
    except Exception:
        pass

    # Try frames
    try:
        for f in page.frames:
            try:
                f.wait_for_selector(selector, timeout=timeout)
                f.fill(selector, text)
                _log(f"Filled {selector} with {text} in frame {f.name}")
                return True
            except Exception:
                continue
    except Exception as e:
        _log(f"fill_if_exists frame scan failed: {e}")

    _log(f"fill_if_exists: {selector} not found on page or frames")
    return False


# Retry helper to make actions robust
def retry_action(fn, attempts=RETRY_ATTEMPTS, delay=RETRY_DELAY, *args, **kwargs):
    for i in range(attempts):
        try:
            ok = fn(*args, **kwargs)
            if ok:
                return True
        except Exception as e:
            _log(f"retry_action caught exception: {e}")
        if i < attempts - 1:
            time.sleep(delay)
    return False


# Helper to retry select_option (returns True on success)
def retry_select(page, selector, **kwargs):
    for i in range(RETRY_ATTEMPTS):
        try:
            page.wait_for_selector(selector, timeout=GLOBAL_TIMEOUT)
            page.select_option(selector, **kwargs)
            _log(f"Selected option on {selector} {kwargs}")
            return True
        except Exception as e:
            _log(f"retry_select attempt {i+1} failed for {selector}: {e}")
            time.sleep(RETRY_DELAY)
    return False


with sync_playwright() as p:
    browser = None
    try:
        # Launch browser with reduced automation flags and a slight slowdown to improve stability
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"], ignore_default_args=["--enable-automation"], slow_mo=100)
        page = browser.new_page()

        # OPEN URL (retrying navigation)
        _log("Navigating to site...")
        print("Navigating to site...")
        try:
            page.goto("https://afm2020.com/", timeout=60000, wait_until='load')
        except Exception as e:
            _log(f"Initial goto failed: {e}; retrying once")
            try:
                page.goto("https://afm2020.com/", timeout=60000)
            except Exception as e2:
                raise
        safe_wait(page, 4000)

        # LOGIN
        _log("Filling login form...")
        print("Filling login form...")
        retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtCorporateId", text="AFMDEMO", timeout=GLOBAL_TIMEOUT)
        retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtUserName", text="Asharma", timeout=GLOBAL_TIMEOUT)
        retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector="#txtPassword", text="Avaal@123", timeout=GLOBAL_TIMEOUT)

        # Click sign in (multiple strategies)
        clicked = False
        for sel in ["#signin", "button:has-text('Sign In')", "text=Sign In"]:
            if retry_action(click_if_exists, attempts=3, delay=1, page=page, selector=sel, timeout=GLOBAL_TIMEOUT):
                clicked = True
                break
        if not clicked:
            _log("Could not click any sign-in selector")
            print("Could not click sign-in selector")

        safe_wait(page, 5000)
        _log("Login step completed")
        print("Login step completed")

        # OPEN C PANEL
        # Prefer data-id based locator for C-Panel, then fallbacks
        if not retry_action(click_if_exists, attempts=3, delay=1, page=page, selector="a[data-id='#MNU00005']", timeout=GLOBAL_TIMEOUT):
            _log("C-Panel click failed; trying text fallbacks")
            retry_action(click_if_exists, attempts=3, delay=1, page=page, selector="a:has-text('C-PANEL')", timeout=GLOBAL_TIMEOUT)
            retry_action(click_if_exists, attempts=3, delay=1, page=page, selector="a:has-text('C Panel')", timeout=GLOBAL_TIMEOUT)

        safe_wait(page, 2000)

        # OPEN TRUCKS - try several menu variants
        if not retry_action(click_if_exists, attempts=3, delay=1, page=page, selector="#MNU00005 a:has-text('Trucks')", timeout=GLOBAL_TIMEOUT):
            _log("Trucks menu click failed; trying href/text fallbacks")
            retry_action(click_if_exists, attempts=3, delay=1, page=page, selector="a[href*='Masters/Truck/TruckList']", timeout=GLOBAL_TIMEOUT)
            retry_action(click_if_exists, attempts=3, delay=1, page=page, selector="a:has-text('Trucks')", timeout=GLOBAL_TIMEOUT)

        safe_wait(page, 2000)

        # Click Add Truck
        add_clicked = False
        if retry_action(click_if_exists, attempts=3, delay=1, page=page, selector='#btnAddTruck', timeout=GLOBAL_TIMEOUT):
            add_clicked = True
        else:
            _log('btnAddTruck not found; trying fallbacks')
            if retry_action(click_if_exists, attempts=2, delay=1, page=page, selector='#btnAddNewTruck', timeout=GLOBAL_TIMEOUT):
                add_clicked = True
            elif retry_action(click_if_exists, attempts=2, delay=1, page=page, selector="button:has-text('Add Truck')", timeout=GLOBAL_TIMEOUT):
                add_clicked = True
            elif retry_action(click_if_exists, attempts=2, delay=1, page=page, selector="text=Add Truck", timeout=GLOBAL_TIMEOUT):
                add_clicked = True

        safe_wait(page, 1500)

        # If Add Truck was clicked, wait for the modal and fill required fields using exact IDs
        if add_clicked:
            try:
                page.wait_for_selector('#myTruckModal', timeout=GLOBAL_TIMEOUT)
                _log('Truck modal visible')
            except Exception:
                _log('Truck modal did not appear; saving page for inspection')
                try:
                    inspect_path = Path(__file__).parent / 'truck_after_add.html'
                    inspect_path.write_text(page.content(), encoding='utf-8')
                    _log(f'Saved page HTML after Add Truck to {inspect_path}')
                except Exception as e:
                    _log(f'Failed to save truck_after_add.html: {e}')

            # Fill the actual truck form fields found in the modal
            truck_no = 'AUTO' + random_alphanum(4)
            plate_no = random_alphanum(6).upper()
            retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector='#txtTruckNumber', text=truck_no, timeout=GLOBAL_TIMEOUT)
            retry_action(fill_if_exists, attempts=3, delay=1, page=page, selector='#txtTruckPlateNumber', text=plate_no, timeout=GLOBAL_TIMEOUT)

            # Try to select Registration State / Province (select2 or plain select fallbacks)
            try:
                state_selected = False
                # First, try to select from an actual <select> element by picking the first usable option
                def choose_first_select_option(sel):
                    try:
                        # retrieve options via JS and pick first with a non-empty value
                        opts = page.eval_on_selector_all(sel + ' option', 'els => els.map(e => ({v: e.value, t: e.textContent, d: e.disabled}))')
                        for o in opts:
                            v = o.get('v')
                            if v and str(v).strip() not in ['', '0', '-1'] and not o.get('d'):
                                page.select_option(sel, value=v)
                                return v
                    except Exception:
                        return None
                    return None

                v = choose_first_select_option('select#ddlTruckStates')
                if v:
                    _log(f'Selected Registration State via select#ddlTruckStates value={v}')
                    state_selected = True
                else:
                    v2 = choose_first_select_option('select#ddlFleetStates')
                    if v2:
                        _log(f'Selected Registration State via select#ddlFleetStates value={v2}')
                        state_selected = True
                # correct selectors (page uses ddlTruckState singular) - try them as well
                if not state_selected:
                    # Prefer explicit known value (Ontario) for reliability in many test environments
                    try:
                        page.wait_for_selector('select#ddlTruckState', timeout=3000)
                        page.select_option('select#ddlTruckState', value='ON')
                        _log("Selected Registration State 'ON' for select#ddlTruckState")
                        state_selected = True
                    except Exception:
                        v3 = choose_first_select_option('select#ddlTruckState')
                        if v3:
                            _log(f'Selected Registration State via select#ddlTruckState value={v3}')
                            state_selected = True
                        else:
                            v4 = choose_first_select_option('select#ddlFleetState')
                            if v4:
                                _log(f'Selected Registration State via select#ddlFleetState value={v4}')
                                state_selected = True
                # If no select found or no usable options, try select2 containers (click and choose first result)
                if not state_selected:
                    if click_if_exists(page, '#select2-ddlTruckStates-container', timeout=3000):
                        # try to click first result in select2 dropdown
                        try:
                            page.wait_for_selector('.select2-results__option, .select2-results li', timeout=3000)
                            # prefer .select2-results__option
                            if click_if_exists(page, '.select2-results__option', timeout=1000):
                                _log('Selected Registration State via select2 results (truck)')
                                state_selected = True
                            elif click_if_exists(page, '.select2-results li', timeout=1000):
                                _log('Selected Registration State via select2 results li (truck)')
                                state_selected = True
                        except Exception:
                            # fallback to keyboard navigation
                            page.keyboard.press('ArrowDown')
                            page.keyboard.press('Enter')
                            _log('Selected Registration State via select2 keyboard (truck)')
                            state_selected = True
                    elif click_if_exists(page, '#select2-ddlFleetStates-container', timeout=3000):
                        try:
                            page.wait_for_selector('.select2-results__option, .select2-results li', timeout=3000)
                            if click_if_exists(page, '.select2-results__option', timeout=1000):
                                _log('Selected Registration State via select2 results (fleet)')
                                state_selected = True
                            elif click_if_exists(page, '.select2-results li', timeout=1000):
                                _log('Selected Registration State via select2 results li (fleet)')
                                state_selected = True
                        except Exception:
                            page.keyboard.press('ArrowDown')
                            page.keyboard.press('Enter')
                            _log('Selected Registration State via select2 keyboard (fleet)')
                            state_selected = True
                if not state_selected:
                    _log('Registration State selector not found; skipping state selection')
            except Exception as e:
                _log(f'Error while selecting Registration State: {e}')

            # Select Truck Type (Tractor (semi) has value '19' in the page snapshot)
            if not retry_select(page, 'select#ddlTruckVehcileSubType', value='19'):
                _log('Could not reliably set truck type to 19')

            # Ensure a fuel type is selected - choose SpecialDiesel or fallback index 1
            if not retry_select(page, 'select#ddlTruckFuelType', value='SpecialDiesel'):
                retry_select(page, 'select#ddlTruckFuelType', index=1)

        safe_wait(page, 1500)

        # Submit with multiple conservative fallbacks
        submitted = False
        for sel in ['#btnTruckSubmit', '#btnSaveTruck', "button:has-text('Submit')", "button:has-text('Save')", 'text=Save']:
            if retry_action(click_if_exists, attempts=3, delay=1, page=page, selector=sel, timeout=GLOBAL_TIMEOUT):
                submitted = True
                break
        if not submitted:
            _log('Could not find submit button for Truck')
            print('Could not find submit button for Truck')

        safe_wait(page, 2000)

        # Screenshot and finish
        _screenshot(page, 'truck_created.png')
        _log('Truck Created (or attempted)')
        print('Truck Created (or attempted)')

    except Exception as e:
        _log(f"Unhandled error during Trucks script: {e}")
        print("Unhandled error during Trucks script:", e)
        try:
            if 'page' in locals():
                _screenshot(page, 'truck_error.png')
        except Exception:
            pass
    finally:
        try:
            if browser:
                browser.close()
        except Exception:
            pass
