import hashlib
import hmac
import json
import time
import requests
import logging

class BitkubAPI:
    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitkub.com"
        self.logger = logging.getLogger(__name__)

    def _format_symbol(self, symbol, for_tv=False):
        if '/' in symbol:
            base, quote = symbol.split('/')
            if for_tv:
                return f"{base}_{quote}"
            else:
                return f"{quote}_{base}"
        return symbol

    def _generate_signature(self, timestamp, method, path, body, api_secret):
        # Bitkub v3: HMAC-SHA256(timestamp + method + path + body, secret)
        payload = str(timestamp) + method.upper() + path + (body or "")
        signature = hmac.new(
            api_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _request(self, method, endpoint, params=None, payload=None, private=False):
        url = f"{self.base_url}{endpoint}"
        
        if private:
            if not self.api_key or not self.api_secret:
                raise ValueError("API Key and Secret are required for private endpoints")
            
            timestamp = int(time.time() * 1000)
            body = json.dumps(payload, separators=(',', ':')) if payload else ""
            
            signature = self._generate_signature(timestamp, method, endpoint, body, self.api_secret)
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-BTK-APIKEY': self.api_key,
                'X-BTK-TIMESTAMP': str(timestamp),
                'X-BTK-SIGN': signature
            }
            
            if method.upper() == 'POST':
                response = requests.post(url, headers=headers, data=body)
            else:
                response = requests.get(url, headers=headers, params=params)
        else:
            response = requests.get(url, params=params)
            
        try:
            response.raise_for_status()
            result = response.json()
            
            if endpoint == '/tradingview/history':
                if result.get('s') != 'ok':
                    self.logger.error(f"Bitkub TV Error: {result}")
                    return None
                return result
            
            if result.get('error') != 0:
                self.logger.error(f"Bitkub Error ({endpoint}): {result}")
                return None
            return result.get('result')
        except Exception as e:
            self.logger.error(f"Request failed ({endpoint}): {e}")
            return None

    def get_ticker(self, symbol=None):
        params = {'sym': self._format_symbol(symbol)} if symbol else {}
        return self._request('GET', '/api/market/ticker', params=params)

    def get_candles(self, symbol, timeframe, limit=100):
        tf_map = {'1m': '1', '5m': '5', '15m': '15', '1h': '60', '4h': '240', '1d': '1D'}
        resolution = tf_map.get(timeframe, '60')
        end = int(time.time())
        minutes = int(resolution) if resolution != '1D' else 1440
        start = end - (limit * minutes * 60)
        
        params = {
            'symbol': self._format_symbol(symbol, for_tv=True),
            'resolution': resolution,
            'from': start,
            'to': end
        }
        
        data = self._request('GET', '/tradingview/history', params=params)
        if not data:
            return None
            
        ohlcv = []
        for i in range(len(data.get('t', []))):
            ohlcv.append([
                data['t'][i],
                data['o'][i],
                data['h'][i],
                data['l'][i],
                data['c'][i],
                data['v'][i]
            ])
        return {'error': 0, 'result': ohlcv}

    def get_wallet(self):
        # Use v3 endpoint
        return self._request('POST', '/api/v3/market/wallet', private=True)

    def place_bid(self, symbol, amount, rate, order_type='market'):
        # Use v3 endpoint
        payload = {
            'sym': self._format_symbol(symbol),
            'amt': float(amount),
            'rat': float(rate),
            'typ': order_type
        }
        return self._request('POST', '/api/v3/market/place-bid', payload=payload, private=True)

    def place_ask(self, symbol, amount, rate, order_type='market'):
        # Use v3 endpoint
        payload = {
            'sym': self._format_symbol(symbol),
            'amt': float(amount),
            'rat': float(rate),
            'typ': order_type
        }
        return self._request('POST', '/api/v3/market/place-ask', payload=payload, private=True)
