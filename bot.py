import os
import logging
import asyncio
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
TELEGRAM_BOT_TOKEN = "7912406574:AAGpFKhg4mOBOhM8VxVfPiVTLhlBiNYc84Q"  # Token bot Telegram
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzpBF-a36aPqnqkcDPi-zLDHyn2N6lKClDKbvKZjmZzeI0X9leiLmk145fukf5Aohwl6g/exec"  # Google Script URL

# Inisialisasi Bot
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Fungsi Start
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[KeyboardButton("📍 Kirim Lokasi", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "Klik tombol di bawah untuk check-in:",
        reply_markup=reply_markup
    )

# Fungsi untuk menerima lokasi user
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

# Tambahkan handler ke bot
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.LOCATION, location))

# Run bot dengan polling (TANPA Flask)
if __name__ == "__main__":
    logger.info("Bot Telegram mulai berjalan...")
    application.run_polling()