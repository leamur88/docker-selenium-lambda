import time
import requests
from datetime import datetime, timedelta, timezone
import os

from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from tempfile import mkdtemp
from selenium.webdriver.common.by import By

court1 = "ZXhlcnA6MTc1YnI0NDAxOjcwMTU5MTE0MTUwOA=="
court2 = "ZXhlcnA6MTc1YnI0NjAxOjcwMTU5MTE0MTUwOA=="
court3 = "ZXhlcnA6MTc1YnI0NDAyOjcwMTU5MTE0MTUwOA=="
court4 = "ZXhlcnA6MTc1YnI0ODAxOjcwMTU5MTE0MTUwOA=="

options = webdriver.ChromeOptions()
service = Service("/opt/chromedriver")

options.binary_location = '/opt/chrome/chrome'
options.add_argument("--headless=new")
options.add_argument('--no-sandbox')
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1280x1696")
options.add_argument("--single-process")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-dev-tools")
options.add_argument("--no-zygote")
options.add_argument(f"--user-data-dir={mkdtemp()}")
options.add_argument(f"--data-path={mkdtemp()}")
options.add_argument(f"--disk-cache-dir={mkdtemp()}")
options.add_argument("--remote-debugging-port=9222")

driver = webdriver.Chrome(options=options, service=service)


def createDateTimeString(yr, m, d, h, min):
    dt_obj = datetime(yr, m, d, h, min, 0)
    timezone_offset = timedelta(hours=-5)  # Assuming -05:00 offset
    tz = timezone(timezone_offset)
    dt_with_offset = dt_obj.replace(tzinfo=tz)
    iso_format_str = dt_with_offset.strftime("%Y-%m-%dT%H:%M:%S%z")
    iso_format_str = iso_format_str[:-2] + ":00"
    return iso_format_str


def makeInitialReservation(startTime, headers, duration, court):
    url = "https://api.lifetimefitness.com/sys/registrations/V3/ux/resource"
    print(startTime)
    print(court3)
    # Parameters for the request body
    body_params = {
        "duration": f"{str(duration)}",
        "resourceId": court,
        "service": None,
        "start": startTime
    }

    try:
        response = requests.post(url, json=body_params, headers=headers)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            print("POST request successful!")
            resp = response.json()

            print("Response:", resp)
            return resp['regId']
        else:
            print("POST request failed with status code:", response.status_code)
            print("Response:", response.text)
    except Exception as e:
        print("An error occurred:", str(e))

def confirmReservation(regId, headers):
    url = f"https://api.lifetimefitness.com/sys/registrations/V3/ux/resource/{regId}/complete"

    # Parameters for the request body
    body_params = {
        "acceptedDocuments": [67]
    }

    try:
        response = requests.put(url, json=body_params, headers=headers)

        if response.status_code == 200:
            print("PUT request successful!")

        else:
            print("PUT request failed with status code:", response.status_code)
            print("Response:", response.text)
    except Exception as e:
        print("An error occurred:", str(e))


def getHeaders():
    driver.get("https://my.lifetime.life/login.html?resource=%2Fclubs%2Fmn%2Feden-prairie-athletic.html")
    time.sleep(4)
    usernameInput = driver.find_element(By.ID, 'account-username')
    passwordInput = driver.find_element(By.ID, 'account-password')
    submitButton = driver.find_element(By.ID, 'login-btn')
    usernameInput.send_keys("leibovich.shai@gmail.com")
    password = os.environ['PASS']
    if password is None:
        raise Exception("Password not provided!")
    passwordInput.send_keys(password)
    submitButton.click()
    print("Signing in!")
    time.sleep(8)
    driver.get('https://my.lifetime.life/clubs/mn/eden-prairie-athletic/resource-booking.html')
    time.sleep(12)
    for request in driver.requests:
        if request.headers.__contains__('x-ltf-jwe') and request.headers.__contains__(
                'x-ltf-ssoid') and request.headers.__contains__('x-ltf-profile') and request.headers.__contains__(
            'ocp-apim-subscription-key'):
            print(request.url)
            print("YESSS")
            return {
                "x-ltf-profile": request.headers.get('x-ltf-profile'),
                "x-ltf-ssoid": request.headers.get('x-ltf-ssoid'),
                "x-ltf-jwe": request.headers.get('x-ltf-jwe'),
                "ocp-apim-subscription-key": request.headers.get('ocp-apim-subscription-key'),
                "Content-Type": "application/json"  # Specify content type as JSON
            }
    raise Exception("No ocp-apim-subscription-key found")


def handler(event=None, context=None):
    startTime = createDateTimeString(2024, 5, 8, 6, 0)
    headers = getHeaders()
    regId = makeInitialReservation(startTime, headers, 30, court4)
    confirmReservation(regId, headers)
