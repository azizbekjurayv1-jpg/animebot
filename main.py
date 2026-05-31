import telebot
import requests
import os
import json
from flask import Flask
from threading import Thread

# Telegram bot tokeningiz 🔑
TOKEN = "8300065405:AAF0hvjLSsnNrs8HhboGg8szFUDBLg03cko"
bot = telebot.TeleBot(TOKEN)

DB_FILE = "users_db.json"
app = Flask('')

@app.route('/')
def home():
    return "Bot muvaffaqiyatli ishlayapti!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user(user_id, username, first_name, last_query=None):
    db = load_db()
    uid = str(user_id)
    
    if uid not in db:
        db[uid] = {
            "username": username,
            "first_name": first_name,
            "history": []
        }
    
    if last_query:
        db[uid]["history"].append(last_query)
        if len(db[uid]["history"]) > 10:
            db[uid]["history"].pop(0)
            
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    save_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    start_text = (
        "🔥 Assalomu alaykum! Musiqa qidiruv botiga xush kelibsiz.\n\n"
        "🎵 Qo'shiq qidirish uchun nomini yoki ijrochini yozing.\n"
        "🔗 YouTube yoki Instagram havolasini yuborsangiz ham audio variantini yuklab beraman!"
    )
    bot.reply_to(message, start_text)

@bot.message_handler(func=lambda message: message.text)
def handle_message(message):
    query = message.text.strip()
    save_user(message.from_user.id, message.from_user.username, message.from_user.first_name, last_query=query)
    
    status_msg = bot.reply_to(message, f"🔍 '{query}' qidirilmoqda va yuklanmoqda...")
    
    try:
        # Tashqi bepul API orqali qidirish va yuklash havolasini olish 🌐
        api_url = f"https://api.vreden.my.id/api/ytmp3?url={query}"
        response = requests.get(api_url).json()
        
        if response.get("status") == 200 and "result" in response:
            audio_url = response["result"].get("download")
            title = response["result"].get("title", "music")
            
            # Tayyor audio faylni internetdan yuklab olib foydalanuvchiga yuborish 📥
            audio_data = requests.get(audio_url).content
            filename = f"{title}.mp3"
            
            with open(filename, "wb") as f:
                f.write(audio_data)
                
            with open(filename, "rb") as audio_file:
                bot.send_audio(message.chat.id, audio_file, reply_to_message_id=message.message_id, caption="🎵 Qo'shiq tayyor!")
                
            if os.path.exists(filename):
                os.remove(filename)
            bot.delete_message(message.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text("❌ Qo'shiq topilmadi yoki yuklashda xatolik yuz berdi.", message.chat.id, status_msg.message_id)
            
    except Exception as e:
        print(f"Xatolik: {e}")
        bot.edit_message_text("❌ Tizimda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring.", message.chat.id, status_msg.message_id)

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    print("Bot Render Web Service rejimida ishlamoqda...")
    bot.infinity_polling()
