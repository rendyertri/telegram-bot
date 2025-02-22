import os
import logging
import requests
import asyncio
from datetime import datetime
import pytz
from flask import Flask, request
from telegram import Update, Bot, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name_)

# Ambil TOKEN dari environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://telegram-bot-5iyf.onrender.com")
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/YOUR_SCRIPT_URL/exec"

# Inisialisasi Flask
app = Flask(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Inisialisasi Telegram Bot
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# ✅ Fungsi Start
async def start(update: Update, context: CallbackContext) -> None:
    logger.info(f"User {update.message.from_user.username} menekan /start")
    keyboard = [[KeyboardButton("📍 Kirim Lokasi", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "Klik tombol di bawah untuk check-in:",
        reply_markup=reply_markup
    )

# ✅ Fungsi untuk menerima lokasi user
async def location(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    location = update.message.location

    # Konversi waktu dari UTC ke WIB
    utc_now = datetime.utcnow()
    wib = pytz.timezone("Asia/Jakarta")
    wib_now = utc_now.replace(tzinfo=pytz.utc).astimezone(wib)
    formatted_time = wib_now.strftime("%H:%M:%S")

    data = {
        "username": user.username if user.username else user.first_name,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "time": formatted_time
    }

    # Kirim data ke Google Sheets
    response = requests.post(GOOGLE_SCRIPT_URL, json=data)
    logger.info(f"Google Sheets Response: {response.status_code}, {response.text}")

    if response.status_code == 200:
        await update.message.reply_text("✅ Check-in sukses! Data telah disimpan.")
    else:
        await update.message.reply_text(f"⚠️ Gagal check-in! Error: {response.text}")

# Tambahkan handler ke bot
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.LOCATION, location))

# ✅ Fungsi untuk menangani Webhook dari Telegram
@app.route("/webhook", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(), bot)
    logger.info(f"Webhook menerima update: {update}")

    await application.process_update(update)
    return "OK", 200

# ✅ Fungsi root untuk cek bot jalan
@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

# ✅ Fungsi untuk set webhook
async def set_webhook():
    if WEBHOOK_URL:
        logger.info(f"Setting webhook ke {WEBHOOK_URL}/webhook")
        await bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    else:
        logger.error("ERROR: WEBHOOK_URL tidak ditemukan!")

# ✅ Run bot
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    # Set Webhook sebelum Flask jalan
    asyncio.run(set_webhook())

    # Jalankan Flask
    app.run(debug=True, host="0.0.0.0", port=port)