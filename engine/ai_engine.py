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
            
        prompt = f"""
        [CONTEXT: QUANTITATIVE TRADING ANALYSIS]
        TIME INTERVAL: 1-HOUR (H1)
        STRATEGY: MOMENTUM & TREND SWING TRADING
        
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
           - OVEREXTENDED: Price is > 5% away from EMA 21 (Reversion risk).

        [DECISION MATRIX]
        - ACTION "BUY": 
            - Trend Status is UP + MACD Bullish Crossover + Current Price > EMA 9.
            - OR: Trend reversal from DOWN to UP confirmed by High Volume and MACD.
        - ACTION "SELL":
            - Trend Status is DOWN + MACD Bearish Crossover + Current Price < EMA 9.
            - OR: Price breaks below EMA 21 (Stop loss condition).
            - OR: RSI > 75 with Bearish MACD Histogram (Take profit condition).
        - ACTION "HOLD":
            - Low Volume + Neutral MACD.
            - RSI in 45-55 zone without clear EMA direction.
            - Price is in 'No Man's Land' (between EMA 9 and 21).

        [OUTPUT SPECIFICATION]
        - You must output ONLY a valid JSON object.
        - confidence_score: (0-100) based on how many criteria are met.
        - reasoning: Concise technical justification (max 15 words).

        {{
            "action": "BUY/SELL/HOLD",
            "confidence_score": integer,
            "reasoning": "string"
        }}
        """

        try:
            payload = {
                "model": self.model,
                "system": "You are a Senior Quantitative Trader specializing in H1 momentum strategies. You are precise, clinical, and data-driven. You prioritize trend alignment and volume confirmation. You never provide advice, only execution decisions based on the provided matrix.",
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