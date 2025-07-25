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
