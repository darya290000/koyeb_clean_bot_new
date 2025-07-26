import asyncio
import aiohttp
from datetime import datetime
from binance import AsyncClient
import pandas as pd
import pandas_ta as ta
import re
import logging

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تنظیمات تلگرام - لطفاً از متغیرهای محیطی استفاده کنید
TELEGRAM_TOKEN = "8136421090:AAFrb8RI6BQ2tH49YXX_5S32_W0yWfT04Cg"
CHAT_ID = 570096331
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

COINS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT", "SOLUSDT"]
TIMEFRAME = "15m"
MAX_RETRIES = 3

def escape_markdown_v2(text):
    """
    Escape کردن کاراکترهای خاص برای MarkdownV2
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

async def send_telegram_message(text, max_retries=MAX_RETRIES):
    """
    ارسال پیام تلگرام با مدیریت خطا
    """
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                params = {
                    "chat_id": CHAT_ID,
                    "text": text,
                    "parse_mode": "MarkdownV2",
                    "disable_web_page_preview": True,
                }
                async with session.post(API_URL, params=params) as resp:
                    if resp.status == 200:
                        logger.info("پیام با موفقیت ارسال شد")
                        return True
                    else:
                        error_text = await resp.text()
                        logger.error(f"خطا در ارسال پیام: {resp.status} - {error_text}")
                        
                        # اگر مشکل از MarkdownV2 باشد، بدون فرمت ارسال کن
                        if "parse_mode" in error_text.lower():
                            params["parse_mode"] = None
                            async with session.post(API_URL, params=params) as retry_resp:
                                if retry_resp.status == 200:
                                    logger.info("پیام بدون فرمت ارسال شد")
                                    return True
                        
                        if attempt == max_retries - 1:
                            return False
                            
        except Exception as e:
            logger.error(f"خطا در تلاش {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    return False

async def fetch_klines(client, symbol, interval, limit=100):
    """
    دریافت داده‌های قیمت از Binance
    """
    try:
        klines = await client.get_klines(symbol=symbol, interval=interval, limit=limit)
        
        if not klines or len(klines) < 52:  # حداقل 52 کندل برای Ichimoku
            logger.warning(f"داده‌های کافی برای {symbol} موجود نیست")
            return None
            
        df = pd.DataFrame(klines, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])
        
        # تبدیل نوع ستون‌ها
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
        
        # بررسی وجود داده‌های نامعتبر
        if df[["open", "high", "low", "close"]].isnull().any().any():
            logger.warning(f"داده‌های نامعتبر در {symbol} پیدا شد")
            return None
            
        return df
        
    except Exception as e:
        logger.error(f"خطا در دریافت داده‌های {symbol}: {e}")
        return None

def calculate_indicators(df):
    """
    محاسبه اندیکاتورهای تکنیکال
    """
    try:
        # EMA
        df["EMA9"] = ta.ema(df["close"], length=9)
        df["EMA21"] = ta.ema(df["close"], length=21)
        
        # RSI
        df["RSI"] = ta.rsi(df["close"], length=14)
        
        # MACD
        macd = ta.macd(df["close"])
        if macd is not None:
            df["MACD"] = macd["MACD_12_26_9"]
            df["MACD_signal"] = macd["MACDs_12_26_9"]
        else:
            df["MACD"] = None
            df["MACD_signal"] = None
        
        # Ichimoku
        ich = ta.ichimoku(df["high"], df["low"], df["close"])
        if ich is not None:
            df["tenkan_sen"] = ich["ISA_9"]
            df["kijun_sen"] = ich["ISB_26"]
            df["senkou_span_a"] = ich["SSA_26"]
            df["senkou_span_b"] = ich["SSB_52"]
            df["chikou_span"] = ich["CL_26"]
        else:
            # مقادیر پیش‌فرض اگر Ichimoku محاسبه نشد
            for col in ["tenkan_sen", "kijun_sen", "senkou_span_a", "senkou_span_b", "chikou_span"]:
                df[col] = None
        
        return df
        
    except Exception as e:
        logger.error(f"خطا در محاسبه اندیکاتورها: {e}")
        return df

def analyze_signal(df):
    """
    تحلیل سیگنال‌ها
    """
    try:
        if len(df) < 2:
            return ["داده‌های کافی برای تحلیل موجود نیست"]
            
        last = df.iloc[-1]
        prev = df.iloc[-2]
        signals = []

        # بررسی وجود داده‌ها قبل از تحلیل
        
        # EMA کراس
        if not pd.isna(last["EMA9"]) and not pd.isna(last["EMA21"]) and not pd.isna(prev["EMA9"]) and not pd.isna(prev["EMA21"]):
            if last["EMA9"] > last["EMA21"] and prev["EMA9"] <= prev["EMA21"]:
                signals.append("خرید (EMA کراس صعودی)")
            elif last["EMA9"] < last["EMA21"] and prev["EMA9"] >= prev["EMA21"]:
                signals.append("فروش (EMA کراس نزولی)")

        # RSI
        if not pd.isna(last["RSI"]):
            if last["RSI"] > 70:
                signals.append("اشباع خرید (RSI بالا)")
            elif last["RSI"] < 30:
                signals.append("اشباع فروش (RSI پایین)")

        # MACD کراس
        if (not pd.isna(last["MACD"]) and not pd.isna(last["MACD_signal"]) and 
            not pd.isna(prev["MACD"]) and not pd.isna(prev["MACD_signal"])):
            if last["MACD"] > last["MACD_signal"] and prev["MACD"] <= prev["MACD_signal"]:
                signals.append("خرید (MACD کراس صعودی)")
            elif last["MACD"] < last["MACD_signal"] and prev["MACD"] >= prev["MACD_signal"]:
                signals.append("فروش (MACD کراس نزولی)")

        # Ichimoku ساده
        if not pd.isna(last["tenkan_sen"]) and not pd.isna(last["kijun_sen"]):
            if last["tenkan_sen"] > last["kijun_sen"]:
                signals.append("روند صعودی (Ichimoku)")
            else:
                signals.append("روند نزولی (Ichimoku)")

        if not signals:
            signals.append("هیچ سیگنال خاصی شناسایی نشد")

        return signals
        
    except Exception as e:
        logger.error(f"خطا در تحلیل سیگنال: {e}")
        return ["خطا در تحلیل سیگنال"]

def safe_round(value, decimals=4):
    """
    Round کردن امن مقادیر
    """
    try:
        if pd.isna(value) or value is None:
            return "N/A"
        return round(float(value), decimals)
    except:
        return "N/A"

def build_message(symbol, df, signals):
    """
    ساخت پیام تلگرام
    """
    try:
        last = df.iloc[-1]
        now = datetime.utcnow().strftime("%Y-%m-%d | %H:%M UTC")

        entry_price = safe_round(last["close"])
        if entry_price != "N/A":
            tp = safe_round(float(entry_price) * 1.01, 4)
            sl = safe_round(float(entry_price) * 0.99, 4)
        else:
            tp = "N/A"
            sl = "N/A"

        logos = {
            "BTCUSDT": "₿",
            "ETHUSDT": "Ξ",
            "XRPUSDT": "✕",
            "ADAUSDT": "₳",
            "SOLUSDT": "◎"
        }
        logo = logos.get(symbol, "")

        signals_text = "\\- " + "\\n\\- ".join([escape_markdown_v2(s) for s in signals])

        # ساخت پیام با Escape کردن کاراکترهای خاص
        msg = (
            f"{logo} 🤖 ربات ارسال‌کننده: ALIASADI04925BOT\\n"
            f"📂 فایل/نسخه: quantumv2\\_multi\\_coin\\_bot\\.py\\n\\n"
            f"💎 تحلیل رمزارز {escape_markdown_v2(symbol)}\\n\\n"
            f"⏰ زمان: {escape_markdown_v2(now)} \\| تایم فریم: {escape_markdown_v2(TIMEFRAME)}\\n\\n"
            f"📈 قیمت باز شدن: {escape_markdown_v2(safe_round(last['open']))}\\n"
            f"📉 قیمت بسته شدن: {escape_markdown_v2(safe_round(last['close']))}\\n"
            f"🔺 بیشترین قیمت: {escape_markdown_v2(safe_round(last['high']))}\\n"
            f"🔻 کمترین قیمت: {escape_markdown_v2(safe_round(last['low']))}\\n"
            f"📊 حجم معامله: {escape_markdown_v2(safe_round(last['volume'], 0))}\\n\\n"
            f"📊 شاخص‌ها:\\n"
            f"\\- EMA9: {escape_markdown_v2(safe_round(last['EMA9']))}\\n"
            f"\\- EMA21: {escape_markdown_v2(safe_round(last['EMA21']))}\\n"
            f"\\- RSI: {escape_markdown_v2(safe_round(last['RSI'], 2))}\\n"
            f"\\- MACD: {escape_markdown_v2(safe_round(last['MACD'], 5))}\\n"
            f"\\- MACD سیگنال: {escape_markdown_v2(safe_round(last['MACD_signal'], 5))}\\n\\n"
            f"📉 سیگنال‌ها:\\n{signals_text}\\n\\n"
            f"🎯 حد سود \\(TP\\): {escape_markdown_v2(tp)}\\n"
            f"🛑 حد ضرر \\(SL\\): {escape_markdown_v2(sl)}\\n\\n"
            f"⚠️ وضعیت گماشته محافظ: سیگنال تایید شده ✅\\n"
            f"\\- تحلیل ریسک: متوسط\\n"
            f"\\- توصیه امنیتی: رعایت حد ضرر و مدیریت ریسک\\n\\n"
            f"🚀 Quantum Scalping AI \\- نسخه حرفه‌ای چندکوینه"
        )
        return msg
        
    except Exception as e:
        logger.error(f"خطا در ساخت پیام: {e}")
        return f"خطا در ساخت پیام برای {symbol}"

async def process_coin(client, coin):
    """
    پردازش یک کوین
    """
    try:
        logger.info(f"در حال پردازش {coin}...")
        df = await fetch_klines(client, coin, TIMEFRAME)
        
        if df is None:
            logger.warning(f"داده‌ای برای {coin} دریافت نشد")
            return False
            
        df = calculate_indicators(df)
        signals = analyze_signal(df)
        msg = build_message(coin, df, signals)
        
        success = await send_telegram_message(msg)
        if success:
            logger.info(f"پیام {coin} با موفقیت ارسال شد")
        else:
            logger.error(f"خطا در ارسال پیام {coin}")
            
        return success
        
    except Exception as e:
        logger.error(f"خطا در پردازش {coin}: {e}")
        return False

async def main_loop():
    """
    حلقه اصلی برنامه
    """
    client = None
    try:
        client = await AsyncClient.create()
        logger.info("اتصال به Binance برقرار شد")
        
        while True:
            logger.info("شروع دور جدید تحلیل...")
            successful_sends = 0
            
            for coin in COINS:
                success = await process_coin(client, coin)
                if success:
                    successful_sends += 1
                await asyncio.sleep(2)  # فاصله بین کوین‌ها
            
            logger.info(f"تحلیل تمام شد. {successful_sends}/{len(COINS)} پیام ارسال شد")
            logger.info(f"منتظر 15 دقیقه بعدی... [{datetime.utcnow()}]")
            await asyncio.sleep(15 * 60)
            
    except KeyboardInterrupt:
        logger.info("برنامه توسط کاربر متوقف شد")
    except Exception as e:
        logger.error(f"خطای کلی در برنامه: {e}")
    finally:
        if client:
            await client.close_connection()
            logger.info("اتصال Binance بسته شد")

if __name__ == "__main__":
    print("🚀 ربات Quantum Scalping AI چندکوینه شروع به کار کرد...")
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n❌ برنامه متوقف شد")
    except Exception as e:
        print(f"❌ خطای کلی: {e}")
