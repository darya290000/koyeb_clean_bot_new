import requests
import time
import pandas as pd
import json

# بارگذاری تنظیمات از فایل config.json
with open("config.json", "r") as f:
    config = json.load(f)

BOT_TOKEN = "8136421090:AAFrb8RI6BQ2tH49YXX_5S32_W0yWfT04Cg"
CHAT_ID = "570096331"

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def get_klines(symbol=None, interval=None, limit=50):
    symbol = symbol or config["symbol"]
    interval = interval or config["interval"]
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    # تبدیل ستون‌ها به نوع عددی
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col])
    return df

def calculate_indicators(df):
    # EMA
    df["EMA9"] = df["close"].ewm(span=config["ema_fast"], adjust=False).mean()
    df["EMA21"] = df["close"].ewm(span=config["ema_slow"], adjust=False).mean()

    # RSI
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=config["rsi_period"]).mean()
    avg_loss = loss.rolling(window=config["rsi_period"]).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df["close"].ewm(span=config["macd_fast"], adjust=False).mean()
    exp2 = df["close"].ewm(span=config["macd_slow"], adjust=False).mean()
    df["MACD"] = exp1 - exp2
    df["MACD_signal"] = df["MACD"].ewm(span=config["macd_signal"], adjust=False).mean()

    # Ichimoku
    tenkan = config["ichimoku"]["tenkan_period"]
    kijun = config["ichimoku"]["kijun_period"]
    span_b = config["ichimoku"]["senkou_span_b_period"]
    disp = config["ichimoku"]["displacement"]

    high_tenkan = df["high"].rolling(window=tenkan).max()
    low_tenkan = df["low"].rolling(window=tenkan).min()
    df["tenkan_sen"] = (high_tenkan + low_tenkan) / 2

    high_kijun = df["high"].rolling(window=kijun).max()
    low_kijun = df["low"].rolling(window=kijun).min()
    df["kijun_sen"] = (high_kijun + low_kijun) / 2

    df["senkou_span_a"] = ((df["tenkan_sen"] + df["kijun_sen"]) / 2).shift(disp)

    high_span_b = df["high"].rolling(window=span_b).max()
    low_span_b = df["low"].rolling(window=span_b).min()
    df["senkou_span_b"] = ((high_span_b + low_span_b) / 2).shift(disp)

    return df

def generate_signal(df):
    last = df.iloc[-1]
    price = last["close"]

    # سیگنال EMA + RSI + MACD قبلی
    ema_rsi_signal = None
    if last["EMA9"] > last["EMA21"] and last["RSI"] < 70:
        ema_rsi_signal = "📈 سیگنال خرید (Buy)"
    elif last["EMA9"] < last["EMA21"] and last["RSI"] > 30:
        ema_rsi_signal = "📉 سیگنال فروش (Sell)"
    else:
        ema_rsi_signal = "⏸️ بدون سیگنال مشخص (Hold)"

    # سیگنال ایچیموکو (قیمت نسبت به سنکوها)
    if price > last["senkou_span_a"] and price > last["senkou_span_b"]:
        ichimoku_signal = "✅ روند صعودی (Bullish)"
    elif price < last["senkou_span_a"] and price < last["senkou_span_b"]:
        ichimoku_signal = "❌ روند نزولی (Bearish)"
    else:
        ichimoku_signal = "⚠️ روند خنثی (Neutral)"

    # تلفیق سیگنال‌ها
    combined_signal = f"{ema_rsi_signal} | Ichimoku: {ichimoku_signal}"

    return combined_signal

def main_loop():
    while True:
        df = get_klines()
        df = calculate_indicators(df)
        signal = generate_signal(df)
        last = df.iloc[-1]

        message = f"""💎 تحلیل رمزارز {config['symbol']}

⏰ زمان: {time.strftime('%Y-%m-%d | %H:%M:%S')}
📈 قیمت باز شدن: {last['open']}
📉 قیمت بسته شدن: {last['close']}
🔺 بیشترین قیمت: {last['high']}
🔻 کمترین قیمت: {last['low']}
📊 حجم معامله: {last['volume']} BTC

📊 شاخص‌ها:
- EMA9: {last['EMA9']:.2f}
- EMA21: {last['EMA21']:.2f}
- RSI: {last['RSI']:.2f}
- MACD: {last['MACD']:.4f}
- MACD سیگنال: {last['MACD_signal']:.4f}

{signal}
"""

        send_message(message)
        print("📤 پیام ارسال شد.")
        time.sleep(config["message_interval_sec"])

if __name__ == "__main__":
    main_loop()
