from engine.bitkub_api import BitkubAPI
import logging

class ExecutionEngine:
    def __init__(self, api_key, api_secret, symbol):
        self.symbol = symbol # e.g. BTC/THB
        self.api = BitkubAPI(api_key, api_secret)
        self.logger = logging.getLogger(__name__)
        self.state_file = "trade_state.json"
        self.state = self._load_state()

    def _load_state(self):
        import json
        import os
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {"last_buy_price": 0, "in_position": False}

    def _save_state(self):
        import json
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f)

    def execute_trade(self, decision, amount_thb, current_price):
        action = decision.get("action").upper()
        confidence = decision.get("confidence_score")
        
        # 1. Dynamic Take Profit (Trailing 5%+)
        if self.state["in_position"] and self.state["last_buy_price"] > 0:
            profit_pct = ((current_price - self.state["last_buy_price"]) / self.state["last_buy_price"]) * 100
            
            # If we hit the 5% target
            if profit_pct >= 5.0:
                # Check if we should exit now or Let Profit Run
                # Exit if: AI says SELL OR (AI says HOLD and confidence is low/mixed)
                if action == "SELL":
                    self.logger.info(f"💰 PROFIT TARGET MET & SELL SIGNAL: Profit {profit_pct:.2f}% | Executing Exit.")
                    return self.sell_market()
                elif action == "HOLD":
                    # If AI is uncertain at 5%+, we take the profit to be safe
                    self.logger.info(f"⚖️ PROFIT TARGET MET & MOMENTUM NEUTRAL: Profit {profit_pct:.2f}% | Locking in gains.")
                    return self.sell_market()
                else:
                    # action is BUY (meaning AI is still very bullish)
                    self.logger.info(f"🚀 PROFIT TARGET MET ({profit_pct:.2f}%) but AI is BULLISH. Trailing for more gains...")
                    # We continue to HOLD
                    
            # Check for Stop Loss (Hard Logic: -2.5% Loss)
            elif profit_pct <= -2.5:
                self.logger.warning(f"🚨 STOP LOSS TRIGGERED! Loss: {profit_pct:.2f}% | Entry: {self.state['last_buy_price']} | Current: {current_price}")
                return self.sell_market()

        # 2. Asymmetrical Thresholds for AI Signals
        if action == "BUY":
            if confidence < 70:
                self.logger.info(f"Entry Signal Ignored: BUY confidence ({confidence}%) < 70 threshold.")
                return None
            return self.buy_market(amount_thb, current_price)
            
        elif action == "SELL":
            # Normal exit signal from AI (even if profit < 5% or it's a loss)
            if confidence < 50:
                self.logger.info(f"Exit Signal Ignored: SELL confidence ({confidence}%) < 50 threshold.")
                return None
            return self.sell_market()
            
        else:
            self.logger.info("Decision is HOLD. Monitoring market...")
            return None

    def get_balance(self):
        try:
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

    def buy_market(self, amount_thb, current_price):
        try:
            balance = self.get_balance()
            if balance is None: return None
            
            thb_balance = balance.get('THB', 0)
            if thb_balance < amount_thb:
                self.logger.warning(f"Insufficient THB balance ({thb_balance}) to buy {amount_thb} THB.")
                return None

            self.logger.info(f"Executing BUY Market Order for {amount_thb} THB of {self.symbol}")
            order = self.api.place_bid(self.symbol, amount_thb, 0, 'market')
            
            if order:
                self.state["last_buy_price"] = current_price
                self.state["in_position"] = True
                self._save_state()
            return order
        except Exception as e:
            self.logger.error(f"Error executing BUY order: {e}")
            return None

    def sell_market(self):
        try:
            coin = self.symbol.split('/')[0]
            balance = self.get_balance()
            if balance is None: return None

            coin_balance = balance.get(coin, 0)
            if coin_balance <= 0:
                self.logger.warning(f"No {coin} balance to sell.")
                return None

            self.logger.info(f"Executing SELL Market Order for {coin_balance} {coin}")
            order = self.api.place_ask(self.symbol, coin_balance, 0, 'market')
            
            if order:
                self.state["last_buy_price"] = 0
                self.state["in_position"] = False
                self._save_state()
            return order
        except Exception as e:
            self.logger.error(f"Error executing SELL order: {e}")
            return None
