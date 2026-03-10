from playwright.sync_api import sync_playwright
import random
import string
import time

def random_alpha(n):
    return ''.join(random.choices(string.ascii_letters, k=n))

def random_alphanum(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # OPEN URL
    page.goto("https://afm2020.com/")
    page.wait_for_timeout(5000)

    # LOGIN
    page.fill("#txtCorporateId","AFMDEMO")
    page.fill("#txtUserName","Asharma")
    page.fill("#txtPassword","Avaal@123")

    page.click("#signin")

    page.wait_for_timeout(5000)

    print("Login Successful")

    # OPEN C PANEL
    page.click('xpath=//*[@id="divMenuHTML"]/div[1]/ul/li[5]/a/span')

    # OPEN FLEET
    page.click('xpath=//*[@id="MNU00005"]/ul/li[2]/a')

    page.wait_for_timeout(5000)

    page.click("#btnAddFleet")

    page.fill("#txtFleetName", random_alpha(4))
    page.fill("#txtFleetFirstAddress", random_alphanum(8))
    page.fill("#txtFleetPhone","8025496734")

    page.click("#select2-ddlFleetStates-container")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")

    page.click("#select2-ddlFleetCities-container")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")

    page.fill("#txtFleetZip","12345")

    page.click("#btnFleetSubmit")

    page.wait_for_timeout(5000)

    page.screenshot(path="fleet.png")

    print("Fleet Created")

    browser.close()