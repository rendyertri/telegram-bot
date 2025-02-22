from datetime import datetime
import pytz
import os
from flask import Flask, request
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import requests

# Ganti dengan API Token dari @BotFather
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Gunakan environment variable
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzpBF-a36aPqnqkcDPi-zLDHyn2N6lKClDKbvKZjmZzeI0X9leiLmk145fukf5Aohwl6g/exec"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # URL Webhook yang dikasih Render

# Inisialisasi Flask
app = Flask(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Inisialisasi Telegram Bot (Application)
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Fungsi start
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

    # Konversi waktu dari UTC ke WIB
    utc_now = datetime.utcnow()
    wib = pytz.timezone("Asia/Jakarta")
    wib_now = utc_now.replace(tzinfo=pytz.utc).astimezone(wib)
    formatted_time = wib_now.strftime("%H:%M:%S")  # Format jam WIB

    data = {
        "username": user.username if user.username else user.first_name,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "time": formatted_time  # Kirim waktu yang sudah dikonversi ke WIB
    }

    # Kirim data ke Google Sheets via Apps Script
    response = requests.post(GOOGLE_SCRIPT_URL, json=data)
    print(f"[DEBUG] Response dari Google Sheets: {response.status_code}, {response.text}")  # Debug log

    if response.status_code == 200:
        await update.message.reply_text("✅ Check-in sukses! Data telah disimpan.")
    else:
        await update.message.reply_text(f"⚠️ Gagal check-in! Error: {response.text}")

# Tambahkan handler ke bot
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.LOCATION, location))

# Fungsi untuk menangani Webhook dari Telegram
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot)
    application.update_queue.put(update)
    return "OK", 200

# Fungsi root untuk cek bot jalan
@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

# Run bot
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Port wajib ada di Render

    # Set Webhook untuk Telegram Bot
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )

    # Jalankan Flask untuk menjaga bot tetap hidup
    app.run(debug=True, host="0.0.0.0", port=port)