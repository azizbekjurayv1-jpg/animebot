import telebot
import os
import subprocess
import json
from flask import Flask
from threading import Thread

# Telegram bot tokeningiz 🔑
TOKEN = "8300065405:AAF0hvjLSsnNrs8HhboGg8szFUDBLg03cko"
bot = telebot.TeleBot(TOKEN)

# Render bepul Web Service uxlab qolmasligi uchun Flask server 🌐
app = Flask('')

@app.route('/')
def home():
    return "Bot tirik va ishlayapti!"

def run_flask():
    # Render avtomatik taqdim etadigan portni tinglaymiz
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ... (Qolgan barcha funksiyalar va qidiruv tizimi o'zgarishsiz qoladi)

def start_bot():
    print("Bot Render Web Service rejimida ishga tushdi...")
    bot.infinity_polling()

if __name__ == "__main__":
    # Flask serverni alohida oqimda parallel yoqamiz ⚙️
    t = Thread(target=run_flask)
    t.start()
    
    # Botni ishga tushiramiz 🚀
    start_bot()
