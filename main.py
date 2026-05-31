import telebot
import os
import subprocess
import json

# Telegram bot tokeningiz 🔑
TOKEN = "8300065405:AAF0hvjLSsnNrs8HhboGg8szFUDBLg03cko"

bot = telebot.TeleBot(TOKEN)
DB_FILE = "users_db.json"

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
        "🔥 Assalomu alaykum. Botimizga Xush kelibsiz.\n\n"
        "🎵 Qo'shiq qidirish:\n"
        "• Shaxsiyda (lichkada): Shunchaki qo'shiq nomini o'zini yozing!\n"
        "• Guruhlarda: /music buyrug'i bilan yozing (Masalan: /music Rugada)\n\n"
        "🚀 Yuklab olmoqchi bo'lgan videoga havolani (link) yuborsangiz ham to'liq audio formatda yuklab beriladi!"
    )
    bot.reply_to(message, start_text)

# Guruhda faqat /music buyrug'ini ushlab olish 👥
@bot.message_handler(commands=['music'])
def search_music_group(message):
    query = message.text.replace('/music', '').strip()
    query = query.replace(f'@{bot.get_me().username}', '').strip()
    
    if not query:
        bot.reply_to(message, "Qo'shiq nomini yozing. Masalan: /music Rugada")
        return
    
    process_search(message, query)

# Havolalar (linklar) uchun handler 🔗
@bot.message_handler(func=lambda message: message.text and message.text.startswith("https"))
def handle_links(message):
    url = message.text.strip()
    msg = bot.reply_to(message, "🔗 Link qabul qilindi! To'liq MP3 variant yuklanyapti...")
    download_and_send_audio(message.chat.id, url, message.message_id, msg.message_id)

# Lichkada (shaxsiyda) shunchaki nom yozilganda ishlaydigan handler 💬
@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text)
def handle_private_text(message):
    query = message.text.strip()
    process_search(message, query)

def process_search(message, query):
    save_user(message.from_user.id, message.from_user.username, message.from_user.first_name, last_query=query)
    msg = bot.reply_to(message, f"🎵 '{query}' qidirilmoqda...")
    download_and_send_audio(message.chat.id, f"ytsearch1:{query}", message.message_id, msg.message_id)

def download_and_send_audio(chat_id, search_query, reply_to_id, status_msg_id):
    output_filename = "track.mp3"
    try:
        # yt-dlp orqali audio yuklash va nomlash 📥
        subprocess.run([
            'yt-dlp', '--extract-audio', '--audio-format', 'mp3',
            '--audio-quality', '0', '-o', 'track.%(ext)s', search_query
        ], check=True)
        
        with open(output_filename, 'rb') as audio:
            bot.send_audio(chat_id, audio, reply_to_message_id=reply_to_id, caption="🎵 Qo'shiq tayyor!")
            
        if os.path.exists(output_filename):
            os.remove(output_filename)
        bot.delete_message(chat_id, status_msg_id)
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        bot.send_message(chat_id, "❌ Qo'shiqni yuklashda xatolik bo'ldi.", reply_to_message_id=reply_to_id)

print("Bot Render uchun tayyor holatda ishga tushdi...")
bot.infinity_polling()
