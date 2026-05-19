import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    EXCHANGE = os.getenv("EXCHANGE", "bitkub").lower()
    BITKUB_API_KEY = os.getenv("BITKUB_API_KEY")
    BITKUB_API_SECRET = os.getenv("BITKUB_API_SECRET")
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    TRADING_SYMBOL = os.getenv("TRADING_SYMBOL", "BTC/THB")
    TIMEFRAME = os.getenv("TIMEFRAME", "1h")
    TRADE_AMOUNT_THB = float(os.getenv("TRADE_AMOUNT_THB", 100))
    TRADE_AMOUNT = float(os.getenv("TRADE_AMOUNT", os.getenv("TRADE_AMOUNT_THB", 100)))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.getenv("LINE_USER_ID")
    BINANCE_TRADE_MODE = os.getenv("BINANCE_TRADE_MODE", "spot").lower()
    LEVERAGE = int(os.getenv("LEVERAGE", "1"))

settings = Settings()
