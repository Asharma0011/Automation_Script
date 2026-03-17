from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from pathlib import Path
import time
import random
import string
from playwright._impl._errors import Error as PWError

LOG = Path(__file__).parent / 'run_truck_flow.log'


def log(msg):
    t = time.strftime('%Y-%m-%d %H:%M:%S')
    s = f"{t} {msg}"
    print(s)
    try:
        LOG.write_text((LOG.read_text() + '\n' + s) if LOG.exists() else s)
    except Exception:
        pass


def random_alphanum(n=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))


def run_once():
    with sync_playwright() as p:
        # Try to launch browser with retries in case of transient crashes
        browser = None
        for attempt in range(1, 4):
            try:
                browser = p.chromium.launch(headless=False, slow_mo=100)
                break
            except Exception as e:
                log(f'Browser launch attempt {attempt} failed: {e}')
                time.sleep(2)
        if not browser:
            log('Browser failed to launch after retries')
            return False
        page = browser.new_page()
        try:
            log('Navigating to https://afm2020.com/')
            # set safe defaults
            page.set_default_navigation_timeout(90000)
            page.set_default_timeout(90000)
            nav_ok = False
            try:
                # try a standard navigation waiting for network idle
                page.goto('https://afm2020.com/', timeout=60000, wait_until='networkidle')
                nav_ok = True
            except Exception as e:
                log(f'Initial goto failed: {e}; trying domcontentloaded fallback')
                try:
                    page.goto('https://afm2020.com/', timeout=60000, wait_until='domcontentloaded')
                    nav_ok = True
                except Exception as e2:
                    log(f'domcontentloaded goto failed: {e2}; trying simple goto fallback')
                    try:
                        page.goto('https://afm2020.com/', timeout=60000)
                        nav_ok = True
                    except Exception as e3:
                        log(f'Final goto fallback failed: {e3}')
            if not nav_ok:
                # give up this attempt
                raise Exception('Navigation to site failed after fallbacks')
            page.wait_for_timeout(2000)

            log('Filling login')
            page.fill('#txtCorporateId', 'AFMDEMO')
            page.fill('#txtUserName', 'Asharma')
            page.fill('#txtPassword', 'Avaal@123')
            # click sign in
            for sel in ['#signin', "button:has-text('Sign In')", 'text=Sign In']:
                try:
                    page.click(sel, timeout=5000)
                    break
                except Exception:
                    continue
            page.wait_for_timeout(4000)

            # Open C-Panel
            for sel in ["a[data-id='#MNU00005']", "a:has-text('C-PANEL')", "a:has-text('C Panel')"]:
                try:
                    page.click(sel, timeout=8000)
                    break
                except Exception:
                    continue
            page.wait_for_timeout(2000)

            # Open Trucks
            for sel in ["#MNU00005 a:has-text('Trucks')", "a[href*='Masters/Truck/TruckList']", "a:has-text('Trucks')"]:
                try:
                    page.click(sel, timeout=8000)
                    break
                except Exception:
                    continue
            page.wait_for_timeout(2000)

            # Click Add Truck
            add_ok = False
            for sel in ['#btnAddTruck', '#btnAddNewTruck', "button:has-text('Add Truck')", "text=Add Truck"]:
                try:
                    page.click(sel, timeout=8000)
                    add_ok = True
                    break
                except Exception:
                    continue
            if not add_ok:
                log('Add Truck button not found')
                page.screenshot(path=str(Path(__file__).parent / 'run_truck_no_add.png'))
                browser.close()
                return False
            page.wait_for_timeout(1500)

            # Wait for modal
            try:
                page.wait_for_selector('#myTruckModal', timeout=15000)
            except PWTimeoutError:
                log('Modal did not appear; saving HTML')
                Path(__file__).parent.joinpath('run_truck_after_add.html').write_text(page.content(), encoding='utf-8')
                page.screenshot(path=str(Path(__file__).parent / 'run_truck_modal_missing.png'))
                browser.close()
                return False

            # Fill fields
            truck_no = 'AUTO' + random_alphanum(4)
            plate_no = random_alphanum(6)
            page.fill('#txtTruckNumber', truck_no)
            page.fill('#txtTruckPlateNumber', plate_no)
            try:
                page.select_option('select#ddlTruckVehcileSubType', value='19')
            except Exception:
                pass
            try:
                page.select_option('select#ddlTruckFuelType', value='SpecialDiesel')
            except Exception:
                pass

            # Submit
            submitted = False
            for sel in ['#btnTruckSubmit', '#btnSaveTruck', "button:has-text('Submit')", "button:has-text('Save')"]:
                try:
                    page.click(sel, timeout=8000)
                    submitted = True
                    break
                except Exception:
                    continue
            if not submitted:
                log('Could not find submit button')
                page.screenshot(path=str(Path(__file__).parent / 'run_truck_no_submit.png'))
                browser.close()
                return False

            page.wait_for_timeout(3000)
            page.screenshot(path=str(Path(__file__).parent / 'run_truck_created.png'))
            log('Truck creation attempted and screenshot saved')
            browser.close()
            return True
        except Exception as e:
            log(f'Exception during run_once: {e}')
            try:
                page.screenshot(path=str(Path(__file__).parent / 'run_truck_error.png'))
            except Exception:
                pass
            browser.close()
            return False


if __name__ == '__main__':
    attempts = 3
    success = False
    for i in range(attempts):
        log(f'Starting attempt {i+1}/{attempts}')
        ok = run_once()
        if ok:
            log(f'Attempt {i+1} succeeded')
            success = True
            break
        else:
            log(f'Attempt {i+1} failed, retrying...')
            time.sleep(2)
    if not success:
        log('All attempts failed')
    else:
        log('Flow succeeded')
