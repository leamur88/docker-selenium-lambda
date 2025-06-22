import time, random
import boto3
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import sys, os
sys.path.append(os.getcwd())


from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from tempfile import mkdtemp
from selenium.webdriver.common.by import By

courts = {
    1: "ZXhlcnA6MTc1YnI0NDAxOjcwMTU5MTE0MTUwOA==",
    2: "ZXhlcnA6MTc1YnI0NjAxOjcwMTU5MTE0MTUwOA==",
    3: "ZXhlcnA6MTc1YnI0NDAyOjcwMTU5MTE0MTUwOA==",
    4: "ZXhlcnA6MTc1YnI0ODAxOjcwMTU5MTE0MTUwOA=="
}

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
#driver = webdriver.Chrome(options=options)



def createDateTimeString(h, min, m, d):
    if m is None or d is None:
        desiredDate = datetime.today() + timedelta(days=8)
        desiredDate = desiredDate.replace(hour=h, minute=min, second=0)
    else:
        desiredDate = datetime(datetime.now().year, m, d, h, min, 0)
    timezone_offset = timedelta(hours=-5)  # Assuming -05:00 offset
    tz = timezone(timezone_offset)
    dt_with_offset = desiredDate.replace(tzinfo=tz)
    iso_format_str = dt_with_offset.strftime("%Y-%m-%dT%H:%M:%S%z")
    iso_format_str = iso_format_str[:-2] + ":00"
    return iso_format_str


def makeInitialReservation(startTime, headers, duration, court):
    if court is None:
        court = random.choice(list(courts.values()))

    url = "https://api.lifetimefitness.com/sys/registrations/V3/ux/resource"
    court_choices = list(courts.values())
    print(f"Attempting to make reservation for {startTime} for {duration} minutes")
    while len(court_choices) > 0:
        try:
            body_params = {
                "duration": f"{str(duration)}",
                "resourceId": court,
                "service": None,
                "start": startTime
            }
            response = requests.post(url, json=body_params, headers=headers)
            if response.status_code == 200:
                print("POST request successful!")
                resp = response.json()
                return resp['regId']
            else:
                print("POST request failed with status code:", response.status_code)
                print("Response:", response.text)
                court_choices.remove(court)
                court = random.choice(court_choices) if len(court_choices) > 0 else None

        except Exception as e:
            raise Exception("An error occurred while making an initial reservation", str(e))

    raise Exception("All Courts were reserved")
def confirmReservation(regId, headers):
    url = f"https://api.lifetimefitness.com/sys/registrations/V3/ux/resource/{regId}/complete"

    # Parameters for the request body
    body_params = {
        "acceptedDocuments": [67]
    }

    response = requests.put(url, json=body_params, headers=headers)

    if response.status_code == 200:
        print("PUT request successful!")
    else:
        print("Response:", response.text)
        raise Exception("PUT request failed with status code:", response.status_code)



def getHeaders():
    driver.get("https://my.lifetime.life/login.html?resource=%2Fclubs%2Fmn%2Feden-prairie-athletic.html")
    time.sleep(5)
    try:
        # Wait for and click the OneTrust "Accept All" or "Reject All" button if it's present
        consent_button = driver.find_element(By.ID, "onetrust-reject-all-handler")
        consent_button.click()
        print("Cookie consent dismissed.")
        time.sleep(1)  # wait a moment for the banner to disappear
    except:
        print("No cookie consent banner detected.")

    usernameInput = driver.find_element(By.ID, 'account-username')
    passwordInput = driver.find_element(By.ID, 'account-password')
    submitButton = driver.find_element(By.ID, 'login-btn')
    usernameInput.send_keys("leibovich.shai@gmail.com")
    password = os.getenv('PASS')
    if password is None:
        raise Exception("Password not provided!")
    passwordInput.send_keys(password)
    try:
        submitButton.click()
        print("Signing in!")
        time.sleep(3)
    except Exception as e:
        print("Error during submitButton.click():", e)
        with open("/tmp/pageFile.html", "w") as f:
            f.write(driver.page_source)
        upload_to_s3('/tmp/pageFile.html' , 'lifetimedebug', "debug/lifetime_debug.html")
        raise
    driver.get('https://my.lifetime.life/clubs/mn/eden-prairie-athletic/resource-booking.html')
    time.sleep(5)
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
                "Content-Type": "application/json",  # Specify content type as JSON
                'User-Agent': 'PostmanRuntime/7.36.1',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
    raise Exception("No ocp-apim-subscription-key found")

def upload_to_s3(file_path, bucket_name, key):
    s3 = boto3.client('s3')
    with open(file_path, "rb") as f:
        s3.upload_fileobj(f, bucket_name, key)
    print(f"Uploaded {file_path} to s3://{bucket_name}/{key}")

def handler(event=None, context=None):
    startTime = createDateTimeString(event.get('hr'), event.get('min'), event.get('month'), event.get('day'))
    load_dotenv(dotenv_path="./.envFile")
    print(startTime)
    headers = getHeaders()
    regId = makeInitialReservation(startTime, headers, event.get('duration'),
                                   courts.get(event.get('court')))
    confirmReservation(regId, headers)
    return True


# if __name__ == '__main__':
#     event = {
#         'hr': 20,
#         'min': 30,
#         'duration': 90,
#         'month': 6,
#         'day': 27
#     }
#
#     handler(event)