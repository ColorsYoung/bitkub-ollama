import os
import sys
import logging
from dotenv import load_dotenv

# Ensure we can import from the root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.binance_api import BinanceAPI

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_binance():
    print("==================================================")
    print("Testing Binance API integration via CCXT...")
    print("==================================================")
    
    # Initialize with credentials to test private endpoints
    from config.settings import settings
    api = BinanceAPI(settings.BINANCE_API_KEY, settings.BINANCE_API_SECRET)
    
    # Test candlestick fetching
    test_symbol = settings.TRADING_SYMBOL
    test_timeframe = settings.TIMEFRAME
    print(f"\n1. Fetching OHLCV candles for {test_symbol} on {test_timeframe} timeframe...")
    response = api.get_candles(test_symbol, test_timeframe, limit=5)
    
    if response and response.get('error') == 0:
        candles = response.get('result', [])
        print(f"✅ Successfully fetched {len(candles)} candles.")
        print("First 2 candles details:")
        for idx, candle in enumerate(candles[:2]):
            print(f"  Candle {idx + 1}: Timestamp (sec)={candle[0]}, Open={candle[1]}, High={candle[2]}, Low={candle[3]}, Close={candle[4]}, Volume={candle[5]}")
    else:
        print(f"❌ Failed to fetch candles: {response}")
        
    # Test leverage for Futures
    if settings.BINANCE_TRADE_MODE == 'futures':
        print(f"\n1.5 Testing set_leverage to {settings.LEVERAGE}x for {test_symbol}...")
        api.set_leverage(test_symbol, settings.LEVERAGE)
        
    # Test private endpoints (wallet)
    print("\n2. Testing get_wallet() behavior with your credentials...")
    try:
        wallet = api.get_wallet()
        if wallet:
            print(f"✅ Successfully fetched wallet balance!")
            positive_assets = {k: v for k, v in wallet.items() if v > 0}
            print(f"Balances > 0: {positive_assets}")
            print(f"USDT Balance: {wallet.get('USDT', 0.0)}")
        else:
            print("❌ Failed to fetch wallet: Result is None")
    except Exception as e:
        print(f"❌ Received exception: {e}")

if __name__ == "__main__":
    test_binance()
