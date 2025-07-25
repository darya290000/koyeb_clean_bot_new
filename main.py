import pandas as pd
import numpy as np
import requests
import asyncio
from datetime import datetime
import logging

# تنظیم لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuantumScalpingAI:
    def __init__(self):
        self.telegram_token = "8136421090:AAFrb8RI6BQ2tH49YXX_5S32_W0yWfT04Cg"
        self.chat_id = "570096331"
        self.ema_fast = 9
        self.ema_slow = 21
        self.rsi_period = 14
        self.position = None
        self.last_signal_time = None

    def calculate_ema(self, prices, period):
        prices = np.array(prices)
        alpha = 2 / (period + 1)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        return ema

    def calculate_rsi(self, prices, period=14):
        prices = np.array(prices)
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        if len(gains) < period:
            return 50
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, prices):
        if len(prices) < 26:
            return 0, 0
        ema12 = self.calculate_ema(prices, 12)
        ema26 = self.calculate_ema(prices, 26)
        macd_line = ema12[-1] - ema26[-1]
        macd_values = ema12[-9:] - ema26[-9:] if len(prices) >= 35 else [macd_line]
        macd_signal = self.calculate_ema(macd_values, 9)[-1] if len(macd_values) >= 9 else macd_line
        return macd_line, macd_signal

    def get_market_data(self, symbol="XRPUSDT"):
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': '1m',
                'limit': 100
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            if not data:
                return None
            closes = [float(candle[4]) for candle in data]
            volumes = [float(candle[5]) for candle in data]
            highs = [float(candle[2]) for candle in data]
            lows = [float(candle[3]) for candle in data]
            opens = [float(candle[1]) for candle in data]
            return {
                'opens': opens,
                'highs': highs,
                'lows': lows,
                'closes': closes,
                'volumes': volumes,
                'current_price': closes[-1],
                'volume_24h': sum(volumes)
            }
        except Exception as e:
            logger.error(f"خطا در دریافت داده: {e}")
            return None

    def analyze_market(self, data, symbol="XRPUSDT"):
        closes = data['closes']
        if len(closes) < 30:
            return None
        ema_fast = self.calculate_ema(closes, self.ema_fast)
        ema_slow = self.calculate_ema(closes, self.ema_slow)
        rsi = self.calculate_rsi(closes)
        macd_line, macd_signal = self.calculate_macd(closes)
        trend_up = ema_fast[-1] > ema_slow[-1]
        long_signal = trend_up and rsi < 70
        short_signal = not trend_up and rsi > 30
        return {
            'symbol': symbol,
            'open': data['opens'][-1],
            'high': data['highs'][-1],
            'low': data['lows'][-1],
            'close': data['closes'][-1],
            'volume': data['volumes'][-1],
            'ema_fast': ema_fast[-1],
            'ema_slow': ema_slow[-1],
            'rsi': rsi,
            'macd_line': macd_line,
            'macd_signal': macd_signal,
            'trend_up': trend_up,
            'long_signal': long_signal,
            'short_signal': short_signal
        }

    def create_signal_message(self, analysis, signal_type):
        current_time = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")
        if analysis['rsi'] > 70:
            rsi_status = "⚠️ اشباع خرید"
            rsi_emoji = "🔴"
        elif analysis['rsi'] < 30:
            rsi_status = "💎 اشباع فروش"
            rsi_emoji = "🟢"
        else:
            rsi_status = "⚖️ خنثی"
            rsi_emoji = "🟡"
        if analysis['macd_line'] > analysis['macd_signal']:
            macd_status = "📈 صعودی"
            macd_emoji = "🟢"
        else:
            macd_status = "📉 نزولی"
            macd_emoji = "🔴"
        if signal_type == 'LONG':
            signal_emoji = "🚀"
            signal_text = "خرید (LONG)"
        elif signal_type == 'SHORT':
            signal_emoji = "📉"
            signal_text = "فروش (SHORT)"
        else:
            signal_emoji = "⏸️"
            signal_text = "نگهداری (HOLD)"
        trend_text = "📈 صعودی" if analysis['trend_up'] else "📉 نزولی"
        message = f"""💎 تحلیل رمزارز {analysis['symbol']}

⏰ زمان: {current_time}
📈 قیمت باز شدن: {analysis['open']:.4f}
📉 قیمت بسته شدن: {analysis['close']:.4f}
🔺 بیشترین قیمت: {analysis['high']:.4f}
🔻 کمترین قیمت: {analysis['low']:.4f}
📊 حجم معامله: {analysis['volume']:.2f}

📊 شاخص‌ها:
- EMA9: {analysis['ema_fast']:.4f}
- EMA21: {analysis['ema_slow']:.4f}
- RSI: {analysis['rsi']:.2f} {rsi_emoji}
- MACD: {analysis['macd_line']:.4f} {macd_emoji}
- MACD سیگنال: {analysis['macd_signal']:.4f}

{signal_emoji} سیگنال: {signal_text} | روند: {trend_text}

📊 وضعیت‌ها:
- RSI: {rsi_status}
- MACD: {macd_status}

🚀 Quantum Scalping AI - نسخه حرفه‌ای"""
        return message

    async def send_telegram_message(self, message):
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("✅ سیگنال ارسال شد")
                return True
            else:
                logger.error(f"❌ خطا در ارسال: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ خطا در ارسال: {e}")
            return False

    async def run_strategy(self, symbol="XRPUSDT"):
        logger.info("🚀 Quantum Scalping AI شروع شد...")
        start_message = "✅ ربات Quantum Scalping AI فعال شد و در حال اجراست..."
        await self.send_telegram_message(start_message)
        while True:
            try:
                data = self.get_market_data(symbol)
                if data is None:
                    logger.warning("داده دریافت نشد، تلاش مجدد...")
                    await asyncio.sleep(60)
                    continue
                analysis = self.analyze_market(data, symbol)
                if analysis is None:
                    logger.warning("تحلیل ناموفق، تلاش مجدد...")
                    await asyncio.sleep(60)
                    continue
                current_time = datetime.now()
                signal_sent = False
                if analysis['long_signal'] and self.position != 'LONG':
                    message = self.create_signal_message(analysis, 'LONG')
                    if await self.send_telegram_message(message):
                        self.position = 'LONG'
                        self.last_signal_time = current_time
                        signal_sent = True
                elif analysis['short_signal'] and self.position != 'SHORT':
                    message = self.create_signal_message(analysis, 'SHORT')
                    if await self.send_telegram_message(message):
                        self.position = 'SHORT'
                        self.last_signal_time = current_time
                        signal_sent = True
                elif (self.last_signal_time is None or 
                      (current_time - self.last_signal_time).seconds > 1800):
                    message = self.create_signal_message(analysis, 'HOLD')
                    if await self.send_telegram_message(message):
                        self.last_signal_time = current_time
                        signal_sent = True
                if signal_sent:
                    logger.info(f"سیگنال ارسال شد - {symbol} - {self.position}")
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"خطا در اجرا: {e}")
                await asyncio.sleep(60)

async def main():
    bot = QuantumScalpingAI()
    await bot.run_strategy("XRPUSDT")

if __name__ == "__main__":
    asyncio.run(main())
