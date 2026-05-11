import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BITKUB_API_KEY = os.getenv("BITKUB_API_KEY")
    BITKUB_API_SECRET = os.getenv("BITKUB_API_SECRET")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    TRADING_SYMBOL = os.getenv("TRADING_SYMBOL", "BTC/THB")
    TIMEFRAME = os.getenv("TIMEFRAME", "1h")
    TRADE_AMOUNT_THB = float(os.getenv("TRADE_AMOUNT_THB", 100))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.getenv("LINE_USER_ID")

settings = Settings()
