from datetime import datetime
import pytz
import os
import asyncio
from flask import Flask, request
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import requests

# Ambil variabel lingkungan
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://telegram-bot-5iyf.onrender.com")
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzpBF-a36aPqnqkcDPi-zLDHyn2N6lKClDKbvKZjmZzeI0X9leiLmk145fukf5Aohwl6g/exec"

# Inisialisasi Flask & Bot
app = Flask(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Inisialisasi Telegram Bot (Application)
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Fungsi Start
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[KeyboardButton("📍 Kirim Lokasi", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text("Klik tombol di bawah untuk check-in:", reply_markup=reply_markup)

# Fungsi Terima Lokasi
async def location(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    location = update.message.location

    # Konversi waktu UTC ke WIB
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
    print(f"[DEBUG] Response Google Sheets: {response.status_code}, {response.text}")

    if response.status_code == 200:
        await update.message.reply_text("✅ Check-in sukses! Data telah disimpan.")
    else:
        await update.message.reply_text(f"⚠️ Gagal check-in! Error: {response.text}")

# Tambahkan handler
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.LOCATION, location))

# Fungsi untuk menangani Webhook dari Telegram
@app.route("/webhook", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(), bot)
    await application.process_update(update)  # Proses update tanpa threading
    return "OK", 200

# Fungsi root untuk cek apakah bot aktif
@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

# Fungsi untuk Set Webhook
async def set_webhook():
    if WEBHOOK_URL:
        print(f"Setting webhook ke {WEBHOOK_URL}/webhook")
        await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    else:
        print("ERROR: WEBHOOK_URL tidak ditemukan.")

# Jalankan bot
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Port wajib ada di Render

    # Pastikan async function dipanggil dengan benar
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(set_webhook())

    # Jalankan Flask untuk menangani webhook
    app.run(debug=True, host="0.0.0.0", port=port)