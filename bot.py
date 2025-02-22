from datetime import datetime
import pytz
import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import requests
from datetime import datetime

# Ganti dengan API Token dari @BotFather
TELEGRAM_BOT_TOKEN = "7912406574:AAGpFKhg4mOBOhM8VxVfPiVTLhlBiNYc84Q"
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzpBF-a36aPqnqkcDPi-zLDHyn2N6lKClDKbvKZjmZzeI0X9leiLmk145fukf5Aohwl6g/exec"  # Ganti dengan URL Web App dari Google Apps Script

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

# Main function
def main():
    print("Starting bot...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, location))

    print("Polling started...")
    app.run_polling(drop_pending_updates=True)

# Run bot
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Port wajib ada di Render
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )
    app.run(debug=True, host="0.0.0.0", port=port)
    main()