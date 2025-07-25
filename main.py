import time
import requests
from telegram import Bot

BOT_TOKEN = "8136421090:AAFrb8RI6BQ2tH49YXX_5S32_W0yWfT04Cg"
CHAT_ID = "570096331"

bot = Bot(token=BOT_TOKEN)

def get_data():
    url = 'https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=3m&limit=1'
    data = requests.get(url).json()[0]
    return {
        "open": data[1],
        "high": data[2],
        "low": data[3],
        "close": data[4],
        "volume": data[5]
    }

while True:
    d = get_data()
    msg = f"""💎 BTCUSDT تحلیل ۳ دقیقه‌ای:

⏰ زمان: {time.strftime('%Y-%m-%d | %H:%M:%S')}
📈 قیمت باز شدن: {d['open']}
📉 قیمت بسته شدن: {d['close']}
🔺 بیشترین قیمت: {d['high']}
🔻 کمترین قیمت: {d['low']}
📊 حجم معامله: {d['volume']}"""
    bot.send_message(chat_id=CHAT_ID, text=msg)
    time.sleep(180)
    def analyze_market(self, data, symbol="XRPUSDT"):
        """تحلیل بازار"""
        closes = data['closes']
        
        if len(closes) < 30:
            return None
            
        # محاسبه اندیکاتورها
        ema_fast = self.calculate_ema(closes, self.ema_fast)
        ema_slow = self.calculate_ema(closes, self.ema_slow)
        rsi = self.calculate_rsi(closes)
        macd_line, macd_signal = self.calculate_macd(closes)
        
        # شرایط سیگنال
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
        """ایجاد پیام سیگنال زیبا"""
        current_time = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")
        
        # تعیین وضعیت RSI
        if analysis['rsi'] > 70:
            rsi_status = "⚠️ اشباع خرید"
            rsi_emoji = "🔴"
        elif analysis['rsi'] < 30:
            rsi_status = "💎 اشباع فروش"
            rsi_emoji = "🟢"
        else:
            rsi_status = "⚖️ خنثی"
            rsi_emoji = "🟡"
            
        # تعیین وضعیت MACD
        if analysis['macd_line'] > analysis['macd_signal']:
            macd_status = "📈 صعودی"
            macd_emoji = "🟢"
        else:
            macd_status = "📉 نزولی"
            macd_emoji = "🔴"
            
        # تعیین سیگنال
        if signal_type == 'LONG':
            signal_emoji = "🚀"
            signal_text = "خرید (LONG)"
        elif signal_type == 'SHORT':
            signal_emoji = "📉"
            signal_text = "فروش (SHORT)"
        else:
            signal_emoji = "⏸️"
            signal_text = "نگهداری (HOLD)"
            
        # روند کلی
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
        """ارسال پیام به تلگرام"""
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
        """اجرای استراتژی"""
        logger.info("🚀 Quantum Scalping AI شروع شد...")
        
        # ارسال پیام شروع
        start_message = "✅ ربات Quantum Scalping AI فعال شد و در حال اجراست..."
        await self.send_telegram_message(start_message)
        
        while True:
            try:
                # دریافت داده‌ها
                data = self.get_market_data(symbol)
                if data is None:
                    logger.warning("داده دریافت نشد، تلاش مجدد...")
                    await asyncio.sleep(60)
                    continue
                
                # تحلیل بازار
                analysis = self.analyze_market(data, symbol)
                if analysis is None:
                    logger.warning("تحلیل ناموفق، تلاش مجدد...")
                    await asyncio.sleep(60)
                    continue
                
                current_time = datetime.now()
                signal_sent = False
                
                # بررسی سیگنال‌های جدید
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
                
                # ارسال آپدیت هر 30 دقیقه
                elif (self.last_signal_time is None or 
                      (current_time - self.last_signal_time).seconds > 1800):
                    message = self.create_signal_message(analysis, 'HOLD')
                    if await self.send_telegram_message(message):
                        self.last_signal_time = current_time
                        signal_sent = True
                
                if signal_sent:
                    logger.info(f"سیگنال ارسال شد - {symbol} - {self.position}")
                
                # صبر 1 دقیقه
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"خطا در اجرا: {e}")
                await asyncio.sleep(60)

# اجرای ربات
async def main():
    bot = QuantumScalpingAI()
    await bot.run_strategy("XRPUSDT")

if __name__ == "__main__":
    asyncio.run(main())
