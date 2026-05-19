import requests
import json
import logging
import os

class AIEngine:
    def __init__(self, ollama_url, model=None, timeout=30, temperature=0.6, top_p=0.9, num_predict=256):
        self.url = f"{ollama_url}/api/generate"
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
        self.timeout = timeout
        self.temperature = temperature
        self.top_p = top_p
        self.num_predict = num_predict
        self.logger = logging.getLogger(__name__)

    def get_decision(self, market_summary: str) -> dict:
        if not market_summary:
            raise ValueError("market_summary is empty or None")
            
        from config.settings import settings
        is_futures = (settings.EXCHANGE == 'binance' and settings.BINANCE_TRADE_MODE == 'futures')
        
        if is_futures:
            prompt = f"""
        [CONTEXT: QUANTITATIVE FUTURES TRADING ANALYSIS]
        TIME INTERVAL: 1-HOUR (1H)
        STRATEGY: DUAL-DIRECTIONAL SWING TRADING (LONG/SHORT)
        LEVERAGE MODE: LEVERAGED ({settings.LEVERAGE}x)
        
        [MARKET DATA INPUT]
        {market_summary}

        [ANALYSIS PROTOCOL]
        1. TREND IDENTIFICATION (SWING FOCUS):
           - STRONGLY BULLISH: Price > EMA 9 > EMA 21. Major trend is up.
           - STRONGLY BEARISH: Price < EMA 9 < EMA 21. Major trend is down.
           - CONSOLIDATION: Price oscillating between EMA 9 and 21. Range bound.

        2. MOMENTUM VERIFICATION (MACD):
           - BULLISH SWING: MACD > Signal + Histogram is positive and growing (Favors LONG).
           - BEARISH SWING: MACD < Signal + Histogram is negative and growing (Favors SHORT).
           - REVERSAL WATCH: Check if MACD histogram is starting to fade/shrink as an early sign of trend exhaustion.

        3. VOLATILITY & RISK ASSESSMENT:
           - RSI (14) OVERBOUGHT: RSI > 70. Warning: buying here might be opening a LONG at the peak.
           - RSI (14) OVERSOLD: RSI < 30. Warning: selling here might be opening a SHORT at the bottom.
           - VOLATILITY (ATR/Volume): Look for strong volume to confirm breakout momentum.

        [DECISION MATRIX (FUTURES LONG/SHORT)]
        - ACTION "BUY" (Represents going LONG or closing an active SHORT position):
            - Standard Long Entry: Trend is UP + MACD is Bullish + Price > EMA 9 (Strong confirmation).
            - Reversal Long Entry: RSI is oversold (< 35) + Volume is high + MACD histogram is turning upwards.
        - ACTION "SELL" (Represents going SHORT or closing an active LONG position):
            - Standard Short Entry: Trend is DOWN + MACD is Bearish + Price < EMA 9.
            - Reversal Short Entry: RSI is overbought (> 65) + Volume is high + MACD histogram is turning downwards.
        - ACTION "HOLD" (Represents maintaining the current position or staying flat):
            - Choose HOLD if indicators are flat, overlapping, or conflicting (e.g. Trend UP but MACD has dead crossed with high RSI).

        [OUTPUT SPECIFICATION]
        - You must output ONLY a valid JSON object.
        - confidence_score: (0-100). Assign >= 80 ONLY if Trend + Momentum + Volume align beautifully.
        - reasoning: Concise technical justification (max 12 words).

        {{
            "action": "BUY/SELL/HOLD",
            "confidence_score": integer,
            "reasoning": "string"
        }}
        """
        else:
            prompt = f"""
        [CONTEXT: QUANTITATIVE TRADING ANALYSIS]
        TIME INTERVAL: 5-MINUTE (M5)
        STRATEGY: SCALPING & QUICK MOMENTUM
        
        [MARKET DATA INPUT]
        {market_summary}

        [ANALYSIS PROTOCOL]
        1. TREND IDENTIFICATION:
           - BULLISH: Price > EMA 9 > EMA 21.
           - BEARISH: Price < EMA 9 < EMA 21.
           - CONSOLIDATION: Price oscillating between EMA 9 and EMA 21.

        2. MOMENTUM VERIFICATION (MACD):
           - STRONG BULLISH: MACD > Signal AND Histogram is positive and expanding.
           - BULLISH EXHAUSTION: MACD > Signal BUT Histogram is shrinking.
           - BEARISH REVERSAL: MACD crosses below Signal.

        3. VOLUME & PRICE ACTION:
           - VALIDATION: Price moves must be backed by 'High' Volume Status.
           - DIVERGENCE: Check if RSI is making lower highs while Price makes higher highs (Warning).

        4. RISK ASSESSMENT:
           - OVERBOUGHT: RSI > 70 (Exercise caution for BUY).
           - OVERSOLD: RSI < 30 (Exercise caution for SELL).
           - OVEREXTENDED: Price is > 1% away from EMA 21 (Reversion risk for M5).

        [DECISION MATRIX]
        - ACTION "BUY" (Must output exactly "BUY"): 
            - Condition 1: Trend Status is UP + MACD Bullish Crossover + Price > EMA 9.
            - Condition 2: RSI < 35 (Oversold) + High Volume + Histogram increasing (turning positive) even if Trend is still DOWN.
        - ACTION "SELL" (Must output exactly "SELL"):
            - Condition 1: Trend Status is DOWN + MACD Bearish Crossover + Current Price < EMA 9.
            - Condition 2 (STOP LOSS): If holding a position and price is dropping, prioritize capital preservation.
            - NOTE: A hard 5% Take Profit is also active in the system, so focus on entering high-momentum moves.
        - ACTION "HOLD" (Must output exactly "HOLD"):
            - Condition 1: Low Volume + Neutral MACD.
            - Condition 2: Price is overlapping EMA 9 and 21.

        [OUTPUT SPECIFICATION]
        - You must output ONLY a valid JSON object.
        - confidence_score: (0-100). Assign >= 70 ONLY if signals (Trend + Momentum + Volume) align well.
        - reasoning: Concise technical justification (max 12 words).

        {{
            "action": "BUY/SELL/HOLD",
            "confidence_score": integer,
            "reasoning": "string"
        }}
        """

        try:
            system_instruction = (
                "You are a conservative and disciplined Futures Swing Trader. You open LONG or SHORT positions only when market indicators (Trend + Momentum + Volume) show absolute clarity. You assign confidence >= 80 only for highest-probability setups. Otherwise, you assign low confidence and recommend HOLD."
                if is_futures else
                "You are an opportunistic but disciplined Scalping Specialist. You seek high-probability entry points. You are willing to trade on oversold reversals if volume is high. If signals are mixed, assign a low confidence score and recommend HOLD."
            )
            
            payload = {
                "model": self.model,
                "system": system_instruction,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "num_predict": self.num_predict
                }
            }
            response = requests.post(self.url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            decision_text = result.get("response", "")
            
            try:
                decision = json.loads(decision_text)
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse JSON decision. Raw text: {decision_text}")
                return {"action": "HOLD", "confidence_score": 0, "reasoning": "Failed to parse AI response."}

            # Validation
            action = str(decision.get("action", "")).upper()
            confidence = decision.get("confidence_score")
            reasoning = decision.get("reasoning", "")

            if action not in ["BUY", "SELL", "HOLD"] or not isinstance(confidence, int) or not (0 <= confidence <= 100):
                self.logger.warning(f"Invalid AI response format: {decision}")
                return {"action": "HOLD", "confidence_score": 0, "reasoning": "AI returned invalid response format or values."}

            self.logger.info(f"AI Decision: {action} (Confidence: {confidence}%) - Reasoning: {reasoning}")
            return decision

        except Exception as e:
            self.logger.error(f"Error calling Ollama: {e}")
            return {"action": "HOLD", "confidence_score": 0, "reasoning": f"AI Engine Error: {str(e)}"}