import asyncio
import aiohttp
import datetime

# توکن و شناسه چت تلگرام (نسخه تستی)
TELEGRAM_TOKEN = "8136421090:AAFrb8RI6BQ2tH49YXX_5S32_W0yWfT04Cg"
CHAT_ID = 570096331

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# تابع ارسال پیام به تلگرام
async def send_telegram_message(text: str):
    async with aiohttp.ClientSession() as session:
        params = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": "true",  # تبدیل به رشته
        }
        async with session.post(API_URL, params=params) as resp:
            if resp.status != 200:
                print(f"❌ خطا در ارسال پیام: {resp.status}")
                print(await resp.text())
            else:
                print("✅ پیام با موفقیت ارسال شد.")

# تابع ساخت پیام تحلیل نمونه با قالب حرفه‌ای
def build_analysis_message():
    now = datetime.datetime.now().strftime("%Y-%m-%d | %H:%M:%S")
    symbol = "XRPUSDT"
    timeframe = "15m"
    open_price = 3.1565
    close_price = 3.1567
    high_price = 3.1567
    low_price = 3.1562
    volume = 2765.50
    ema9 = 3.1573
    ema21 = 3.1575
    rsi = 57.87
    macd = -0.0005
    macd_signal = -0.0008
    signal = "فروش (SHORT)"
    trend = "نزولی 📉"
    guardian_status = "سیگنال تایید شده ✅"
    risk_assessment = "ریسک متوسط"
    take_profit = "3.1450"
    stop_loss = "3.1650"
    previous_entry_price = "3.1600"
    previous_take_profit = "3.1700"
    previous_stop_loss = "3.1500"
    previous_order_status = "باز"
    previous_profit_loss = "-0.35%"
    previous_signal_notes = "سیگنال قبلی در سود نبود، مراقب باشید."
    
    message = (
        f"🤖 ربات ارسال‌کننده: ALIASADI04925BOT\n"
        f"📂 فایل/نسخه: quantumv1_scalping_test_bot.py\n\n"
        f"💎 تحلیل رمزارز {symbol}\n\n"
        f"⏰ زمان: {now} | تایم فریم: {timeframe}\n\n"
        f"📈 قیمت باز شدن: {open_price}\n"
        f"📉 قیمت بسته شدن: {close_price}\n"
        f"🔺 بیشترین قیمت: {high_price}\n"
        f"🔻 کمترین قیمت: {low_price}\n"
        f"📊 حجم معامله: {volume}\n\n"
        f"📊 شاخص‌ها:\n"
        f"- EMA9: {ema9} 🔻\n"
        f"- EMA21: {ema21} 🔻\n"
        f"- RSI: {rsi} 🟡\n"
        f"- MACD: {macd} 🟢\n"
        f"- MACD سیگنال: {macd_signal}\n\n"
        f"📉 سیگنال: {signal} | روند: {trend}\n\n"
        f"🎯 حد سود (TP): {take_profit}\n"
        f"🛑 حد ضرر (SL): {stop_loss}\n\n"
        f"🔄 گزارش عملکرد سیگنال قبلی:\n"
        f"- قیمت ورود: {previous_entry_price}\n"
        f"- حد سود تعیین شده: {previous_take_profit}\n"
        f"- حد ضرر تعیین شده: {previous_stop_loss}\n"
        f"- وضعیت سفارش: {previous_order_status}\n"
        f"- میزان سود/ضرر: {previous_profit_loss}\n"
        f"- توضیحات: {previous_signal_notes}\n\n"
        f"⚠️ وضعیت گماشته محافظ: {guardian_status}\n"
        f"- تحلیل ریسک: {risk_assessment}\n"
        f"- توصیه امنیتی: رعایت حد ضرر و مدیریت ریسک\n\n"
        f"🚀 Quantum Scalping AI - نسخه تستی حرفه‌ای"
    )
    return message

# تابع اصلی اجرای چرخه ارسال هر 15 دقیقه
async def main_loop():
    while True:
        msg = build_analysis_message()
        await send_telegram_message(msg)
        print(f"[{datetime.datetime.now()}] پیام ارسال شد، منتظر 15 دقیقه بعد...")
        await asyncio.sleep(15 * 60)  # هر 15 دقیقه

if __name__ == "__main__":
    print("🚀 ربات تستی Quantum Scalping AI شروع به کار کرد...")
    asyncio.run(main_loop())
