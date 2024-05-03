import time
import requests
from datetime import datetime, timedelta, timezone
import sys,os
sys.path.append(os.getcwd())

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

chromeOptions = Options()
chromeOptions.add_experimental_option("detach", True)

court1 = "ZXhlcnA6MTc1YnI0NDAxOjcwMTU5MTE0MTUwOA=="
court2 = "ZXhlcnA6MTc1YnI0NjAxOjcwMTU5MTE0MTUwOA=="
court3 = "ZXhlcnA6MTc1YnI0NDAyOjcwMTU5MTE0MTUwOA=="
court4 = "ZXhlcnA6MTc1YnI0ODAxOjcwMTU5MTE0MTUwOA=="

# chromeOptions.binary_location = '/opt/headless-chromium'
driver = webdriver.Chrome(options=chromeOptions)

def createDateTimeString(yr, m, d, h, min):
    dt_obj = datetime(yr, m, d, h, min, 0)
    timezone_offset = timedelta(hours=-5)  # Assuming -05:00 offset
    tz = timezone(timezone_offset)
    dt_with_offset = dt_obj.replace(tzinfo=tz)
    iso_format_str = dt_with_offset.strftime("%Y-%m-%dT%H:%M:%S%z")
    iso_format_str = iso_format_str[:-2] + ":00"
    return iso_format_str

def makeInitialReservation(time, headers):
    url = "https://api.lifetimefitness.com/sys/registrations/V3/ux/resource"
    print(time)
    print(court3)
    # Parameters for the request body
    body_params = {
        "duration": "60",
        "resourceId": court3,
        "service": None,
        "start": time
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
    time.sleep(1)
    usernameInput = driver.find_element(By.ID, 'account-username')
    passwordInput = driver.find_element(By.ID, 'account-password')
    submitButton = driver.find_element(By.ID, 'login-btn')
    usernameInput.send_keys("leibovich.shai@gmail.com")
    password = os.environ['PASS']
    if password is None:
        raise Exception("Password not provided!")
    passwordInput.send_keys(password)
    submitButton.click()
    time.sleep(1)
    driver.get('https://my.lifetime.life/clubs/mn/eden-prairie-athletic/resource-booking.html')
    time.sleep(2)
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


if __name__ == '__main__':
    startTime = createDateTimeString(2024, 4, 26, 22, 0)
    headers = getHeaders()
    # regId = makeInitialReservation(startTime, headers)
    # confirmReservation(regId, headers)