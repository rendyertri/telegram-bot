import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, CallbackContext
)
import requests
import pytz
from datetime import datetime

# Logging biar gampang debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ambil ENV variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://telegram-bot-5iyf.onrender.com")
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzpBF-a36aPqnqkcDPi-zLDHyn2N6lKClDKbvKZjmZzeI0X9leiLmk145fukf5Aohwl6g/exec"

# Inisialisasi Flask
app = Flask(__name__)

# Inisialisasi Bot
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# ✅ Harus panggil initialize()
async def init_application():
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

# ✅ Fungsi start
async def start(update: Update, context: CallbackContext) -> None:
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

    # Konversi waktu ke WIB
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

    response = requests.post(GOOGLE_SCRIPT_URL, json=data)

    if response.status_code == 200:
        await update.message.reply_text("✅ Check-in sukses! Data telah disimpan.")
    else:
        await update.message.reply_text(f"⚠️ Gagal check-in! Error: {response.text}")

# ✅ Tambahkan handler ke bot
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.LOCATION, location))

# ✅ Webhook endpoint buat handle update dari Telegram
@app.route("/webhook", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    await application.process_update(update)
    return "OK", 200

# ✅ Cek status bot
@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

# ✅ Set webhook
async def set_webhook():
    if WEBHOOK_URL:
        logger.info(f"Setting webhook to {WEBHOOK_URL}/webhook")
        await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    else:
        logger.error("ERROR: WEBHOOK_URL tidak ditemukan di environment variables.")

# ✅ Jalankan bot
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    # *WAJIB* inisialisasi bot sebelum Flask jalan
    asyncio.run(set_webhook())  
    asyncio.run(init_application())  

    # Gunakan Gunicorn buat Flask
    app.run(debug=True, host="0.0.0.0", port=port)