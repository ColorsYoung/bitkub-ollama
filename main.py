import time
import logging
import sys
from config.settings import settings
from engine.market_engine import MarketEngine
from engine.ai_engine import AIEngine
from engine.execution_engine import ExecutionEngine

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

    logger.info(f"Bot started. Monitoring {settings.TRADING_SYMBOL} on {settings.TIMEFRAME} timeframe.")

    while True:
        try:
            logger.info("--- New Trading Cycle ---")
            
            # 1. Fetch market data and summary
            market_summary = market_engine.get_market_summary()
            logger.info(f"Market Summary Fetched:\n{market_summary}")

            # 2. Get AI Decision
            decision = ai_engine.get_decision(market_summary)
            logger.info(f"AI Decision: {decision['action']} (Confidence: {decision['confidence_score']}%)")
            logger.info(f"Reasoning: {decision['reasoning']}")

            # 3. Execute Trade
            if settings.BITKUB_API_KEY and settings.BITKUB_API_SECRET:
                order = execution_engine.execute_trade(decision, settings.TRADE_AMOUNT_THB)
                if order:
                    logger.info(f"Order Executed Successfully: {order['id']}")
            else:
                logger.warning("API Keys not set. Trade execution skipped (Dry Run Mode).")

            # 4. Wait for next cycle
            # Wait based on timeframe or a fixed interval
            logger.info(f"Cycle complete. Waiting for next run...")
            time.sleep(300) # Run every 5 minutes for demonstration

        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60) # Wait a bit before retrying

if __name__ == "__main__":
    run_bot()
