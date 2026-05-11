import os
import logging
from dotenv import load_dotenv
from engine.bitkub_api import BitkubAPI

# Setup logging
logging.basicConfig(level=logging.INFO)

load_dotenv()

api_key = os.getenv('BITKUB_API_KEY')
api_secret = os.getenv('BITKUB_API_SECRET')

api = BitkubAPI(api_key, api_secret)

print("Checking Wallet...")
wallet = api.get_wallet()
print(f"Wallet Result: {wallet}")
