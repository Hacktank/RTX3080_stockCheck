import urllib3
from urllib3.exceptions import InsecureRequestWarning
import requests
import json
import re
import time
from fake_useragent import UserAgent
from twilio.rest import Client

import threading
import types
from dataclasses import dataclass

#disable annoying warnings
urllib3.disable_warnings(InsecureRequestWarning)

twi_realPhoneNumber = "xxxxxx"
twi_twilio_account_sid = 'xxxxxx'
twi_twilio_auth_token = 'xxxxxx'
twi_twilio_virtualPhoneNumber = "xxxxxx"
twi_client = Client(twi_twilio_account_sid, twi_twilio_auth_token)

def sendTextMesage(messageBody):
    print("Text message sent: '" + messageBody + "'")
    twi_client.messages.create(body=messageBody, from_=twi_twilio_virtualPhoneNumber, to=twi_realPhoneNumber)

continuePolling = True

@dataclass
class PollingTarget:
    name: str
    pollUrl: str
    interval: int
    purchaseUrl: str
    pollFunc: types.FunctionType
    threadHandle: threading.Thread = None

    def pollingLoop(self) -> None :
        http = urllib3.PoolManager(cert_reqs="CERT_NONE")

        while continuePolling:
            try:
                siteData = http.request('GET', self.pollUrl,headers={"User-Agent": UserAgent().random}).data.decode('utf-8')
                isInStock = self.pollFunc(siteData)
            except:
                print("An error occured while parsing " + self.name + ", trying again in a moment.")
                time.sleep(2)
                continue
            if isInStock:
                print(self.name + " IN STOCK!")
                sendTextMesage(self.name + " IN STOCK. Purchase link:\n" + self.purchaseUrl)
                break
            else:
                print(self.name + " out of stock, sleeping for " + str(self.interval) + " seconds.")
                time.sleep(self.interval)

allPollingTargets = [
    PollingTarget(
        name = "[NVIDIA] FE",
        pollUrl = "https://in-and-ru-store-api.uk-e1.cloudhub.io/DR/products/en_us/USD/5438481700",
        interval = 10,
        purchaseUrl = "https://store.nvidia.com/store/nvidia/en_US/buy/productID.5438481700/clearCart.yes/nextPage.QuickBuyCartPage",
        pollFunc = lambda data : re.search('OUT_OF_STOCK', json.loads(data)["products"]["product"][0]["inventoryStatus"]["status"], re.IGNORECASE) == None
    ),
    PollingTarget(
        name = "[AMAZON] EVGA FTW3",
        pollUrl = "https://www.amazon.com/gp/aws/cart/add.html?ASIN.2=B08HR3DPGW&Quantity.2=1&ref_=nav_custrec_signin&confirmPage=confirm",
        interval = 10,
        purchaseUrl = "https://www.amazon.com/gp/aws/cart/add.html?ASIN.2=B08HR3DPGW&Quantity.2=1&ref_=nav_custrec_signin&confirmPage=confirm",
        pollFunc = lambda data : re.search('currently unavailable', data, re.IGNORECASE) == None
    ),
    PollingTarget(
        name = "[AMAZON] EVGA FTW3 ULTRA",
        pollUrl = "https://www.amazon.com/gp/aws/cart/add.html?ASIN.2=B08HR3Y5GQ&Quantity.2=1&ref_=nav_custrec_signin&confirmPage=confirm",
        interval = 10,
        purchaseUrl = "https://www.amazon.com/gp/aws/cart/add.html?ASIN.2=B08HR3Y5GQ&Quantity.2=1&ref_=nav_custrec_signin&confirmPage=confirm",
        pollFunc = lambda data : re.search('currently unavailable', data, re.IGNORECASE) == None
    ),
    PollingTarget(
        name = "[EVGA  ] EVGA FTW3",
        pollUrl = "https://www.evga.com/products/product.aspx?pn=10G-P5-3897-KR",
        interval = 10,
        purchaseUrl = "https://www.evga.com/products/product.aspx?pn=10G-P5-3897-KR",
        pollFunc = lambda data : re.search('out of stock', data, re.IGNORECASE) == None
    )
]

try:
    for pt in allPollingTargets:
        pt.threadHandle = threading.Thread(target=pt.pollingLoop)
        pt.threadHandle.start()

    while continuePolling:
        time.sleep(10)
except (KeyboardInterrupt, SystemExit):
    print("KeyboardInterrupt triggered, program will exit after all polling threads tick again.")
    continuePolling = False

for pt in allPollingTargets:
    pt.threadHandle.join()
