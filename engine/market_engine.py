from config.settings import settings
from engine.bitkub_api import BitkubAPI
from engine.binance_api import BinanceAPI
import pandas as pd
import pandas_ta as ta
import logging

class MarketEngine:
    def __init__(self, symbol, timeframe):
        self.symbol = symbol # e.g. BTC/THB
        self.timeframe = timeframe
        if settings.EXCHANGE == 'binance':
            self.api = BinanceAPI()
        else:
            self.api = BitkubAPI()
        self.logger = logging.getLogger(__name__)

    def fetch_ohlcv(self, limit=100):
        try:
            response = self.api.get_candles(self.symbol, self.timeframe, limit=limit)
            if not response or response.get('error') != 0:
                return None
            
            ohlcv = response.get('result', [])
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s') # Bitkub uses seconds
            df = df.astype({'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'})
            return df
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV: {e}")
            return None

    def add_indicators(self, df):
        if df is None or df.empty:
            return None
        
        # Add RSI
        df['rsi'] = ta.rsi(df['close'], length=14)
        
        # Add EMA
        df['ema_9'] = ta.ema(df['close'], length=9)
        df['ema_21'] = ta.ema(df['close'], length=21)
        
        # Add MACD
        macd = ta.macd(df['close'])
        df = pd.concat([df, macd], axis=1)
        
        return df

    def get_market_summary(self):
        df = self.fetch_ohlcv()
        df = self.add_indicators(df)
        
        if df is None:
            return "Unable to fetch market data."

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        avg_volume = df['volume'].tail(24).mean() # 24h average volume
        
        # MACD Column names from pandas_ta
        macd_col = 'MACD_12_26_9'
        signal_col = 'MACDs_12_26_9'
        hist_col = 'MACDh_12_26_9'

        summary = (
            f"Market Summary for {self.symbol} ({self.timeframe}):\n"
            f"Current Price: {latest['close']}\n"
            f"Previous Close: {prev['close']}\n"
            f"Price Change: {latest['close'] - prev['close']:.2f}\n"
            f"RSI (14): {latest['rsi']:.2f} (Previous: {prev['rsi']:.2f})\n"
            f"EMA 9: {latest['ema_9']:.2f}, EMA 21: {latest['ema_21']:.2f}\n"
            f"Trend Status: {'UP' if latest['ema_9'] > latest['ema_21'] else 'DOWN'}\n"
            f"MACD: {latest[macd_col]:.2f}, Signal: {latest[signal_col]:.2f}\n"
            f"Histogram: {latest[hist_col]:.2f} (Prev Hist: {prev[hist_col]:.2f})\n"
            f"Momentum: {'Increasing' if latest[hist_col] > prev[hist_col] else 'Decreasing'}\n"
            f"Current Volume: {latest['volume']:.4f}, 24h Avg Volume: {avg_volume:.4f}\n"
            f"Volume Status: {'High' if latest['volume'] > avg_volume * 1.5 else 'Normal'}\n"
        )
        return summary
