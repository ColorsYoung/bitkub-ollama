from engine.bitkub_api import BitkubAPI
import logging

class ExecutionEngine:
    def __init__(self, api_key, api_secret, symbol):
        self.symbol = symbol # e.g. BTC/THB
        self.api = BitkubAPI(api_key, api_secret)
        self.logger = logging.getLogger(__name__)

    def get_balance(self):
        try:
            # BitkubAPI._request already returns the 'result' part (the balances)
            # or None if an error occurred.
            balances = self.api.get_wallet()
            if balances:
                thb = balances.get('THB', 0)
                self.logger.info(f"Balance Check: {thb} THB available.")
                return balances
            
            self.logger.error("Failed to fetch balance from Bitkub.")
            return None
        except Exception as e:
            self.logger.error(f"Exception during balance check: {e}")
            return None

    def execute_trade(self, decision, amount_thb):
        action = decision.get("action").upper()
        confidence = decision.get("confidence_score")
        
        # Asymmetrical Thresholds: Be picky with BUY (80%), but quick with SELL (50%).
        if action == "BUY":
            if confidence < 80:
                self.logger.info(f"Entry Signal Ignored: BUY confidence ({confidence}%) < 80 threshold.")
                return None
            return self.buy_market(amount_thb)
            
        elif action == "SELL":
            if confidence < 50:
                self.logger.info(f"Exit Signal Ignored: SELL confidence ({confidence}%) < 50 threshold.")
                return None
            return self.sell_market()
            
        else:
            self.logger.info("Decision is HOLD. Monitoring market...")
            return None

    def buy_market(self, amount_thb):
        try:
            balance = self.get_balance()
            if balance is None: return None
            
            thb_balance = balance.get('THB', 0)
            if thb_balance < amount_thb:
                self.logger.warning(f"Insufficient THB balance ({thb_balance}) to buy {amount_thb} THB.")
                return None

            self.logger.info(f"Executing BUY Market Order for {amount_thb} THB of {self.symbol}")
            # Bitkub market buy: amt is THB
            order = self.api.place_bid(self.symbol, amount_thb, 0, 'market')
            return order
        except Exception as e:
            self.logger.error(f"Error executing BUY order: {e}")
            return None

    def sell_market(self):
        try:
            # Extract coin symbol from TRADING_SYMBOL (e.g., BTC/THB -> BTC)
            coin = self.symbol.split('/')[0]
            balance = self.get_balance()
            if balance is None: return None

            coin_balance = balance.get(coin, 0)
            if coin_balance <= 0:
                self.logger.warning(f"No {coin} balance to sell.")
                return None

            self.logger.info(f"Executing SELL Market Order for {coin_balance} {coin}")
            # Bitkub market sell: amt is coin amount
            order = self.api.place_ask(self.symbol, coin_balance, 0, 'market')
            return order
        except Exception as e:
            self.logger.error(f"Error executing SELL order: {e}")
            return None
