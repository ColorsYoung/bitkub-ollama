import ccxt
import logging
from config.settings import settings

class BinanceAPI:
    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logging.getLogger(__name__)
        
        # Initialize CCXT Binance instance
        config = {
            'enableRateLimit': True
        }
        if api_key and api_secret:
            config['apiKey'] = api_key
            config['secret'] = api_secret
            
        # Configure for Spot or Futures
        if settings.BINANCE_TRADE_MODE == 'futures':
            config['options'] = {'defaultType': 'future'}
            self.logger.info("Configuring CCXT Binance for USDⓈ-M Futures trading.")
            
        self.exchange = ccxt.binance(config)
        self.logger.info("Binance API (CCXT) initialized.")

    def set_leverage(self, symbol, leverage):
        try:
            if settings.BINANCE_TRADE_MODE == 'futures':
                self.exchange.set_leverage(leverage, symbol)
                self.logger.info(f"Set leverage to {leverage}x for {symbol} on Binance Futures.")
        except Exception as e:
            self.logger.error(f"Error setting leverage for {symbol}: {e}")

    def get_candles(self, symbol, timeframe, limit=100):
        try:
            # CCXT expects standard symbols like BTC/USDT.
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Format to match Bitkub's get_candles response structure:
            # Bitkub expects timestamp in SECONDS: [timestamp_seconds, o, h, l, c, v]
            # CCXT returns timestamp in MILLISECONDS.
            formatted_ohlcv = []
            for candle in ohlcv:
                formatted_ohlcv.append([
                    int(candle[0] / 1000), # Convert millisecond timestamp to seconds
                    float(candle[1]),      # open
                    float(candle[2]),      # high
                    float(candle[3]),      # low
                    float(candle[4]),      # close
                    float(candle[5])       # volume
                ])
            
            return {
                'error': 0,
                'result': formatted_ohlcv
            }
        except Exception as e:
            self.logger.error(f"Binance fetch_ohlcv error for {symbol}: {e}")
            return {'error': 1, 'message': str(e)}
            
    def get_wallet(self):
        try:
            if not self.exchange.apiKey or not self.exchange.secret:
                raise ValueError("Binance API Key and Secret are required for private endpoints (wallet check).")
                
            balance = self.exchange.fetch_balance()
            # Returns free balances mapped to their uppercase asset names
            free_balances = balance.get('free', {})
            return {asset.upper(): float(qty) for asset, qty in free_balances.items()}
        except Exception as e:
            self.logger.error(f"Binance fetch_balance error: {e}")
            return None
            
    def place_bid(self, symbol, amount, rate, order_type='market', price=None, reduce_only=False):
        """
        Executes a BUY order.
        - For Spot: amount represents the quote currency to spend (e.g., USDT).
        - For Futures: amount represents the base currency quantity to buy.
        """
        try:
            if not self.exchange.apiKey or not self.exchange.secret:
                raise ValueError("Binance API Key and Secret are required for private endpoints.")
                
            params = {}
            if reduce_only:
                params['reduceOnly'] = True
                
            if settings.BINANCE_TRADE_MODE == 'futures':
                qty = self.exchange.amount_to_precision(symbol, amount)
                self.logger.info(f"Placing Binance Futures BUY ({'Close SHORT' if reduce_only else 'Open LONG'}) Market Order for {qty} of {symbol}")
                
                if order_type.lower() == 'market':
                    order = self.exchange.create_order(symbol, 'market', 'buy', qty, None, params)
                else:
                    order = self.exchange.create_order(symbol, 'limit', 'buy', qty, rate, params)
                return order
            else:
                # Spot Mode (Original)
                if order_type.lower() == 'market':
                    params['quoteOrderQty'] = self.exchange.amount_to_precision(symbol, amount) if hasattr(self.exchange, 'amount_to_precision') else amount
                    self.logger.info(f"Placing Binance Spot Market BUY order for {amount} quote value of {symbol}")
                    order = self.exchange.create_order(symbol, 'market', 'buy', None, None, params)
                    return order
                else:
                    self.logger.info(f"Placing Binance Spot Limit BUY order for {amount} on {symbol} at rate {rate}")
                    order = self.exchange.create_limit_buy_order(symbol, amount, rate)
                    return order
        except Exception as e:
            self.logger.error(f"Binance place_bid (BUY) error: {e}")
            return None
            
    def place_ask(self, symbol, amount, rate, order_type='market', price=None, reduce_only=False):
        """
        Executes a SELL order.
        - For both Spot/Futures: amount represents the base currency quantity to sell (e.g., BTC).
        """
        try:
            if not self.exchange.apiKey or not self.exchange.secret:
                raise ValueError("Binance API Key and Secret are required for private endpoints.")
                
            params = {}
            if reduce_only:
                params['reduceOnly'] = True
                
            qty = self.exchange.amount_to_precision(symbol, amount)
            
            if settings.BINANCE_TRADE_MODE == 'futures':
                self.logger.info(f"Placing Binance Futures SELL ({'Close LONG' if reduce_only else 'Open SHORT'}) Market Order for {qty} of {symbol}")
                if order_type.lower() == 'market':
                    order = self.exchange.create_order(symbol, 'market', 'sell', qty, None, params)
                else:
                    order = self.exchange.create_order(symbol, 'limit', 'sell', qty, rate, params)
                return order
            else:
                self.logger.info(f"Placing Binance Spot Market SELL order for {qty} of {symbol}")
                if order_type.lower() == 'market':
                    order = self.exchange.create_market_sell_order(symbol, qty)
                else:
                    order = self.exchange.create_limit_sell_order(symbol, qty, rate)
                return order
        except Exception as e:
            self.logger.error(f"Binance place_ask (SELL) error: {e}")
            return None
