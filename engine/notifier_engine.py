import requests
import logging

class LINEPusher:
    def __init__(self, channel_access_token, user_id):
        self.url = "https://api.line.me/v2/bot/message/push"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {channel_access_token}"
        }
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)

    def send_notification(self, action, price, confidence, reasoning):
        if action.upper() not in ["BUY", "SELL"]:
            return

        emoji = "🚀" if action.upper() == "BUY" else "⚠️"
        color_emoji = "🟢" if action.upper() == "BUY" else "🔴"
        
        message = (
            f"{color_emoji} *AI TRADING SIGNAL: {action.upper()}* {emoji}\n\n"
            f"💰 Price: {price:,.2f} THB\n"
            f"🎯 Confidence: {confidence}%\n"
            f"📝 Reason: {reasoning}\n\n"
            f"🕒 Time: {self._get_now_str()}"
        )

        payload = {
            "to": self.user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }

        try:
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            self.logger.info(f"LINE Notification sent: {action} at {price}")
        except Exception as e:
            self.logger.error(f"Failed to send LINE notification: {e}")

    def _get_now_str(self):
        from datetime import datetime
        import pytz
        tz = pytz.timezone('Asia/Bangkok')
        return datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
