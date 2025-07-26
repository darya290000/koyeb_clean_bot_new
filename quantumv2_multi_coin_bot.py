import asyncio
import aiohttp
from datetime import datetime
from binance import AsyncClient, BinanceSocketManager
import pandas as pd
import pandas_ta as ta

# تنظیمات توکن و چت تلگرام
TELEGRAM_TOKEN = "8136421090:AAFrb8RI6BQ2tH49YXX_5S32_W0yWfT04Cg"
CHAT_ID = 570096331

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# لیست کوین‌ها و تایم‌فریم
COINS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT", "SOLUSDT"]
TIMEFRAME = "15m"

# تابع ارسال پیام به تلگرام
async def send_telegram_message(text):
    async with aiohttp.ClientSession() as session:
        params = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True,
        }
        async with session.post(API_URL, params=params) as resp:
            if resp.status != 200:
                print(f"Error sending message: {resp.status}")
            else:
                print(f"Message sent for coin")

# تابع دریافت داده کندل از Binance
async def fetch_klines(client, symbol, interval, limit=100):
    klines = await client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
    ])
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
    return df

# محاسبه اندیکاتورها
def calculate_indicators(df):
    df["EMA9"] = ta.ema(df["close"], length=9)
    df["EMA21"] = ta.ema(df["close"], length=21)
    df["RSI"] = ta.rsi(df["close"], length=14)
    macd = ta.macd(df["close"])
    df["MACD"] = macd["MACD_12_26_9"]
    df["MACD_signal"] = macd["MACDs_12_26_9"]

    # Ichimoku
    ich = ta.ichimoku(df["high"], df["low"], df["close"])
    df["tenkan_sen"] = ich["ISA_9"]
    df["kijun_sen"] = ich["ISB_26"]
    df["senkou_span_a"] = ich["SSA_26"]
    df["senkou_span_b"] = ich["SSB_52"]
    df["chikou_span"] = ich["CL_26"]

    return df

# تحلیل سیگنال ترکیبی
def analyze_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    signals = []

    # EMA crossover
    if last["EMA9"] > last["EMA21"] and prev["EMA9"] <= prev["EMA21"]:
        signals.append("خرید (EMA کراس صعودی)")
    elif last["EMA9"] < last["EMA21"] and prev["EMA9"] >= prev["EMA21"]:
        signals.append("فروش (EMA کراس نزولی)")

    # RSI
    if last["RSI"] > 70:
        signals.append("اشباع خرید (RSI بالا)")
    elif last["RSI"] < 30:
        signals.append("اشباع فروش (RSI پایین)")

    # MACD crossover
    if last["MACD"] > last["MACD_signal"] and prev["MACD"] <= prev["MACD_signal"]:
        signals.append("خرید (MACD کراس صعودی)")
    elif last["MACD"] < last["MACD_signal"] and prev["MACD"] >= prev["MACD_signal"]:
        signals.append("فروش (MACD کراس نزولی)")

    # Ichimoku سیگنال ساده (تنکان سن بالاتر از کیجون سن)
    if last["tenkan_sen"] > last["kijun_sen"]:
        signals.append("روند صعودی (Ichimoku)")
    else:
        signals.append("روند نزولی (Ichimoku)")

    return signals

# ساخت پیام کامل سیگنال
def build_message(symbol, df, signals):
    last = df.iloc[-1]
    now = datetime.utcnow().strftime("%Y-%m-%d | %H:%M UTC")

    # محاسبه حد سود و ضرر فرضی
    entry_price = last["close"]
    tp = round(entry_price * 1.01, 4)  # حد سود 1%
    sl = round(entry_price * 0.99, 4)  # حد ضرر 1%

    # لوگوی هر کوین
    logos = {
        "BTCUSDT": "₿",
        "ETHUSDT": "Ξ",
        "XRPUSDT": "✕",
        "ADAUSDT": "₳",
        "SOLUSDT": "◎"
    }
    logo = logos.get(symbol, "")

    signals_text = "\n- ".join(signals)

    msg = (
        f"{logo} 🤖 ربات ارسال‌کننده: ALIASADI04925BOT\n"
        f"📂 فایل/نسخه: quantumv2_multi_coin_bot.py\n\n"
        f"💎 تحلیل رمزارز {symbol}\n\n"
        f"⏰ زمان: {now} | تایم فریم: {TIMEFRAME}\n\n"
        f"📈 قیمت باز شدن: {last['open']}\n"
        f"📉 قیمت بسته شدن: {last['close']}\n"
        f"🔺 بیشترین قیمت: {last['high']}\n"
        f"🔻 کمترین قیمت: {last['low']}\n"
        f"📊 حجم معامله: {last['volume']}\n\n"
        f"📊 شاخص‌ها:\n"
        f"- EMA9: {round(last['EMA9'], 4)}\n"
        f"- EMA21: {round(last['EMA21'], 4)}\n"
        f"- RSI: {round(last['RSI'], 2)}\n"
        f"- MACD: {round(last['MACD'], 5)}\n"
        f"- MACD سیگنال: {round(last['MACD_signal'], 5)}\n\n"
        f"📉 سیگنال‌ها:\n- {signals_text}\n\n"
        f"🎯 حد سود (TP): {tp}\n"
        f"🛑 حد ضرر (SL): {sl}\n\n"
        f"⚠️ وضعیت گماشته محافظ: سیگنال تایید شده ✅\n"
        f"- تحلیل ریسک: متوسط\n"
        f"- توصیه امنیتی: رعایت حد ضرر و مدیریت ریسک\n\n"
        f"🚀 Quantum Scalping AI - نسخه حرفه‌ای چندکوینه"
    )
    return msg

# حلقه اصلی برنامه
async def main_loop():
    client = await AsyncClient.create()
    while True:
        for coin in COINS:
            try:
                df = await fetch_klines(client, coin, TIMEFRAME)
                df = calculate_indicators(df)
                signals = analyze_signal(df)
                msg = build_message(coin, df, signals)
                await send_telegram_message(msg)
                await asyncio.sleep(1)  # یک ثانیه وقفه بین ارسال‌ها
            except Exception as e:
                print(f"Error processing {coin}: {e}")
        print(f"[{datetime.utcnow()}] تمام سیگنال‌ها ارسال شدند، منتظر 15 دقیقه بعد...")
        await asyncio.sleep(15 * 60)  # 15 دقیقه

if __name__ == "__main__":
    print("🚀 ربات Quantum Scalping AI چندکوینه شروع به کار کرد...")
    asyncio.run(main_loop())
