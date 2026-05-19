from config.settings import settings
from engine.bitkub_api import BitkubAPI
from engine.binance_api import BinanceAPI
import logging

class ExecutionEngine:
    def __init__(self, api_key, api_secret, symbol):
        self.symbol = symbol # e.g. BTC/THB
        if settings.EXCHANGE == 'binance':
            self.api = BinanceAPI(api_key, api_secret)
        else:
            self.api = BitkubAPI(api_key, api_secret)
        self.logger = logging.getLogger(__name__)
        
        # Determine exchange-specific state file to avoid pollution
        if settings.EXCHANGE == 'bitkub':
            self.state_file = "trade_state.json"
        else:
            self.state_file = f"trade_state_{settings.EXCHANGE}_{settings.BINANCE_TRADE_MODE}.json"
            
        self.state = self._load_state()
        
        # Set leverage if trading futures
        if settings.EXCHANGE == 'binance' and settings.BINANCE_TRADE_MODE == 'futures':
            self.api.set_leverage(self.symbol, settings.LEVERAGE)
 
    def _load_state(self):
        import json
        import os
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "last_buy_price": 0, 
            "in_position": False,
            "position_type": None,   # "LONG" or "SHORT" or None
            "position_size": 0.0,    # Quantity in base asset
            "entry_price": 0.0       # Entry price
        }

    def _save_state(self):
        import json
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f)

    def execute_trade(self, decision, amount_quote, current_price):
        action = decision.get("action").upper()
        confidence = decision.get("confidence_score")
        
        is_futures = (settings.EXCHANGE == 'binance' and settings.BINANCE_TRADE_MODE == 'futures')
        
        # 1. Dynamic Take Profit & Stop Loss
        if self.state["in_position"]:
            entry_price = self.state.get("entry_price", self.state.get("last_buy_price", 0))
            if entry_price > 0:
                pos_type = self.state.get("position_type", "LONG")
                
                # Calculate profit percentage based on direction
                if pos_type == "SHORT":
                    profit_pct = ((entry_price - current_price) / entry_price) * 100
                else:
                    profit_pct = ((current_price - entry_price) / entry_price) * 100
                    
                # If we hit the 5% profit target
                if profit_pct >= 5.0:
                    if action == ("SELL" if pos_type == "LONG" else "BUY"):
                        self.logger.info(f"💰 PROFIT TARGET MET & REVERSAL SIGNAL: Profit {profit_pct:.2f}% | Executing Exit.")
                        if is_futures:
                            return self.close_position(current_price)
                        else:
                            return self.sell_market()
                    elif action == "HOLD":
                        self.logger.info(f"⚖️ PROFIT TARGET MET & MOMENTUM NEUTRAL: Profit {profit_pct:.2f}% | Locking in gains.")
                        if is_futures:
                            return self.close_position(current_price)
                        else:
                            return self.sell_market()
                    else:
                        self.logger.info(f"🚀 PROFIT TARGET MET ({profit_pct:.2f}%) but AI is BULLISH in direction. Trailing for more...")
                
                # Check for Stop Loss (Hard Logic: -2.5% Loss)
                elif profit_pct <= -2.5:
                    self.logger.warning(f"🚨 STOP LOSS TRIGGERED! Loss: {profit_pct:.2f}% | Entry: {entry_price} | Current: {current_price}")
                    if is_futures:
                        return self.close_position(current_price)
                    else:
                        return self.sell_market()

        # 2. Entry / Swing Execution
        if is_futures:
            if action == "BUY": # AI wants to go LONG
                if confidence < 80:
                    self.logger.info(f"LONG Entry Signal Ignored: BUY confidence ({confidence}%) < 80 threshold.")
                    return None
                
                # If already LONG, do nothing
                if self.state["in_position"] and self.state.get("position_type") == "LONG":
                    self.logger.info("Already in LONG position. Monitoring...")
                    return None
                    
                # If SHORT, close it first
                if self.state["in_position"] and self.state.get("position_type") == "SHORT":
                    self.logger.info("Reversal signal: Closing active SHORT before opening LONG.")
                    self.close_position(current_price)
                    
                return self.open_position("LONG", amount_quote, current_price)
                
            elif action == "SELL": # AI wants to go SHORT
                if confidence < 80:
                    self.logger.info(f"SHORT Entry Signal Ignored: SELL confidence ({confidence}%) < 80 threshold.")
                    return None
                    
                # If already SHORT, do nothing
                if self.state["in_position"] and self.state.get("position_type") == "SHORT":
                    self.logger.info("Already in SHORT position. Monitoring...")
                    return None
                    
                # If LONG, close it first
                if self.state["in_position"] and self.state.get("position_type") == "LONG":
                    self.logger.info("Reversal signal: Closing active LONG before opening SHORT.")
                    self.close_position(current_price)
                    
                return self.open_position("SHORT", amount_quote, current_price)
            else:
                self.logger.info("Decision is HOLD. Monitoring Futures market...")
                return None
        else:
            # Original Spot Logic (Bitkub / Binance Spot)
            if action == "BUY":
                if confidence < 70:
                    self.logger.info(f"Entry Signal Ignored: BUY confidence ({confidence}%) < 70 threshold.")
                    return None
                return self.buy_market(amount_quote, current_price)
                
            elif action == "SELL":
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
                quote = self.symbol.split('/')[1].upper()
                quote_balance = balances.get(quote, 0)
                self.logger.info(f"Balance Check: {quote_balance} {quote} available.")
                return balances
            self.logger.error(f"Failed to fetch balance from {settings.EXCHANGE.upper()}.")
            return None
        except Exception as e:
            self.logger.error(f"Exception during balance check: {e}")
            return None

    def buy_market(self, amount_quote, current_price):
        try:
            balance = self.get_balance()
            if balance is None: return None
            
            quote = self.symbol.split('/')[1].upper()
            quote_balance = balance.get(quote, 0)
            if quote_balance < amount_quote:
                self.logger.warning(f"Insufficient {quote} balance ({quote_balance}) to buy {amount_quote} {quote}.")
                return None

            self.logger.info(f"Executing BUY Market Order for {amount_quote} {quote} of {self.symbol}")
            order = self.api.place_bid(self.symbol, amount_quote, 0, 'market')
            
            if order:
                self.state["last_buy_price"] = current_price
                self.state["entry_price"] = current_price
                self.state["in_position"] = True
                self.state["position_type"] = "LONG"
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
                self.state["entry_price"] = 0
                self.state["in_position"] = False
                self.state["position_type"] = None
                self._save_state()
            return order
        except Exception as e:
            self.logger.error(f"Error executing SELL order: {e}")
            return None

    # Futures Specific Methods
    def open_position(self, direction, amount_quote, current_price):
        try:
            balance = self.get_balance()
            if balance is None: return None
            
            quote = self.symbol.split('/')[1].upper()
            # If using leverage, check if margin balance is sufficient
            quote_balance = balance.get(quote, 0)
            if quote_balance < amount_quote:
                self.logger.warning(f"Insufficient {quote} margin balance ({quote_balance}) to open {direction} position with {amount_quote} {quote}.")
                return None
            
            # Calculate quantity in base asset (Binance Futures requires base quantity e.g. BTC)
            leverage = settings.LEVERAGE
            # Total notional position value = margin * leverage
            position_value = amount_quote * leverage
            qty = position_value / current_price
            
            self.logger.info(f"Opening Futures {direction} (Margin={amount_quote} USDT, Leverage={leverage}x, Value={position_value} USDT, Qty={qty:.6f})")
            
            if direction == "LONG":
                order = self.api.place_bid(self.symbol, qty, 0, 'market', current_price)
            else:
                order = self.api.place_ask(self.symbol, qty, 0, 'market', current_price)
                
            if order:
                self.state["in_position"] = True
                self.state["position_type"] = direction
                self.state["entry_price"] = current_price
                self.state["last_buy_price"] = current_price
                
                # CCXT order response usually provides actual filled quantity under 'amount' or 'filled'
                filled_qty = float(order.get('filled', order.get('amount', qty)))
                if filled_qty == 0:
                    filled_qty = qty
                self.state["position_size"] = filled_qty
                
                self._save_state()
                self.logger.info(f"✅ Successfully opened {direction} position. Size: {filled_qty:.6f}")
            return order
        except Exception as e:
            self.logger.error(f"Error opening Futures position: {e}")
            return None

    def close_position(self, current_price):
        try:
            if not self.state["in_position"]:
                self.logger.warning("No active Futures position to close.")
                return None
                
            direction = self.state.get("position_type", "LONG")
            qty = self.state.get("position_size", 0.0)
            
            if qty <= 0:
                # Fallback calculation
                leverage = settings.LEVERAGE
                qty = (settings.TRADE_AMOUNT * leverage) / self.state.get("entry_price", current_price)
                
            self.logger.info(f"Closing Futures {direction} position (Size={qty:.6f} at Market Price {current_price})")
            
            if direction == "LONG":
                # Close LONG by selling with reduceOnly=True
                order = self.api.place_ask(self.symbol, qty, 0, 'market', current_price, reduce_only=True)
            else:
                # Close SHORT by buying with reduceOnly=True
                order = self.api.place_bid(self.symbol, qty, 0, 'market', current_price, reduce_only=True)
                
            if order:
                self.state["in_position"] = False
                self.state["position_type"] = None
                self.state["entry_price"] = 0.0
                self.state["last_buy_price"] = 0.0
                self.state["position_size"] = 0.0
                self._save_state()
                self.logger.info(f"✅ Successfully closed {direction} position.")
            return order
        except Exception as e:
            self.logger.error(f"Error closing Futures position: {e}")
            return None
