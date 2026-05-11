import time
import logging
import sys
from config.settings import settings
from engine.market_engine import MarketEngine
from engine.ai_engine import AIEngine
from engine.execution_engine import ExecutionEngine
from engine.notifier_engine import LINEPusher

# Setup Logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("TradingBot")

def run_bot():
    logger.info("Initializing Bitkub AI Trading Bot...")
    
    # Initialize Engines
    market_engine = MarketEngine(settings.TRADING_SYMBOL, settings.TIMEFRAME)
    ai_engine = AIEngine(settings.OLLAMA_URL)
    execution_engine = ExecutionEngine(
        settings.BITKUB_API_KEY, 
        settings.BITKUB_API_SECRET, 
        settings.TRADING_SYMBOL
    )
    
    # Initialize Notifier
    notifier = None
    if settings.LINE_CHANNEL_ACCESS_TOKEN and settings.LINE_USER_ID:
        notifier = LINEPusher(settings.LINE_CHANNEL_ACCESS_TOKEN, settings.LINE_USER_ID)
        logger.info("LINE Notifier initialized.")

    logger.info(f"Bot started. Monitoring {settings.TRADING_SYMBOL} on {settings.TIMEFRAME} timeframe.")

    while True:
        try:
            logger.info("--- New Trading Cycle ---")
            
            # 1. Fetch market data and summary
            # We'll fetch OHLCV first to get the latest price easily
            df = market_engine.fetch_ohlcv()
            if df is None or df.empty:
                logger.error("Failed to fetch market data.")
                time.sleep(60)
                continue
                
            latest_price = df.iloc[-1]['close']
            market_summary = market_engine.get_market_summary()
            logger.info(f"Market Summary Fetched (Price: {latest_price}):\n{market_summary}")

            # 2. Get AI Decision
            decision = ai_engine.get_decision(market_summary)
            action = decision.get('action', 'HOLD').upper()
            confidence = decision.get('confidence_score', 0)
            reasoning = decision.get('reasoning', 'No reason provided.')
            
            logger.info(f"AI Decision: {action} (Confidence: {confidence}%)")
            logger.info(f"Reasoning: {reasoning}")

            # 3. Send Notification (Only for BUY/SELL)
            if notifier and action in ["BUY", "SELL"]:
                notifier.send_notification(action, latest_price, confidence, reasoning)

            # 4. Execute Trade
            if settings.BITKUB_API_KEY and settings.BITKUB_API_SECRET:
                order = execution_engine.execute_trade(decision, settings.TRADE_AMOUNT_THB, latest_price)
                if order:
                    logger.info(f"Order Executed Successfully: {order['id']}")
            else:
                logger.warning("API Keys not set. Trade execution skipped (Dry Run Mode).")

            # 5. Wait for next cycle
            logger.info(f"Cycle complete. Waiting for next run...")
            time.sleep(60) # Run every 1 minute for responsiveness on 5m timeframe

        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60) # Wait a bit before retrying

if __name__ == "__main__":
    run_bot()
