import os
import logging
from dotenv import load_dotenv
from engine.bitkub_api import BitkubAPI

# Setup logging
logging.basicConfig(level=logging.DEBUG)

load_dotenv()

api_key = os.getenv('BITKUB_API_KEY')
api_secret = os.getenv('BITKUB_API_SECRET')

api = BitkubAPI(api_key, api_secret)

print("Checking Market Order Placement (Market Buy BTC with 10 THB) with BTC_THB symbol...")
# Manual payload to test BTC_THB
payload = {
    'sym': 'BTC_THB',
    'amt': 10,
    'rat': 0,
    'typ': 'market'
}
result = api._request('POST', '/api/v3/market/place-bid', payload=payload, private=True)
print(f"Result: {result}")
