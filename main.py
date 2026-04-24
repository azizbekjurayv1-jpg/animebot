import telebot
from telebot import types
import json
import os
import threading
from flask import Flask

# --- RENDER UCHUN KICHIK SERVER (UXLAB QOLMASLIGI UCHUN) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- BOT SOZLAMALARI ---
API_TOKEN = '8523975201:AAHrN7IRjCFx2j33v2kEQY2Ku1qIaPg9IHY'
ADMIN_ID = 8625345482 
KANAL_USERNAME = "@psjfkspjsl" 

bot = telebot.TeleBot(API_TOKEN)

def load_data():
    if os.path.exists('storage.json'):
        with open('storage.json', 'r') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_data(data):
    with open('storage.json', 'w') as f:
        json.dump(data, f, indent=4)

storage = load_data()

@bot.message_handler(commands=['start'])
def start(msg):
    args = msg.text.split()
    if len(args) > 1:
        code = args[1]
        if code in storage:
            bot.send_video(msg.chat.id, storage[code]['id'], caption=f"🎬 Kod: {code}")
            return
    bot.send_message(msg.chat.id, "👋 Salom! Kino kodini yuboring.")

@bot.message_handler(content_types=['photo'])
def handle_admin_photo(msg):
    if msg.from_user.id == ADMIN_ID:
        m = bot.send_message(msg.chat.id, "🎬 **Anime/Kino nomini kiriting:**", parse_mode="Markdown")
        bot.register_next_step_handler(m, get_janr, msg.photo[-1].file_id)
    else:
        bot.send_message(msg.chat.id, f"Siz admin emassiz! Sizning ID: {msg.from_user.id}")

def get_janr(msg, photo_id):
    name = msg.text
    m = bot.send_message(msg.chat.id, "🎭 **Janrini kiriting:**", parse_mode="Markdown")
    bot.register_next_step_handler(m, get_qismlar, photo_id, name)

def get_qismlar(msg, photo_id, name):
    janr = msg.text
    m = bot.send_message(msg.chat.id, "🎞 **Qismlar sonini kiriting:**", parse_mode="Markdown")
    bot.register_next_step_handler(m, get_code, photo_id, name, janr)

def get_code(msg, photo_id, name, janr):
    qismlar = msg.text
    m = bot.send_message(msg.chat.id, "🔢 **Ushbu kino uchun KOD kiriting:**", parse_mode="Markdown")
    bot.register_next_step_handler(m, get_video, photo_id, name, janr, qismlar)

def get_video(msg, photo_id, name, janr, qismlar):
    code = msg.text
    m = bot.send_message(msg.chat.id, "📹 **Kinoning o'zini (video) yuboring:**", parse_mode="Markdown")
    bot.register_next_step_handler(m, finish_post, photo_id, name, janr, qismlar, code)

def finish_post(msg, photo_id, name, janr, qismlar, code):
    if msg.content_type == 'video':
        video_id = msg.video.file_id
        storage[code] = {'id': video_id}
        save_data(storage)

        full_text = (
            f"＊ ─── ─── ﾟ⛩️ ﾟ─── ─── ┐\n"
            f"📂 **Anime nomi :** {name}\n"
            f"．．．─── ．．．．．．．．．．───\n"
            f"🗡 **Janri :** {janr}\n"
            f"．．．─── ．．．．．．．．．．───\n"
            f"🎞 **Qismlar soni :** {qismlar}\n"
            f"．．．─── ．．．．．．．．．．───\n"
            f"🎙 **Ovoz berdi :** Uz-Anime\n"
            f"💭 **Tili :** Uzbek tilida\n"
            f"🔢 **Kino kodi :** `{code}`"
        )

        btn = types.InlineKeyboardMarkup()
        btn.add(types.InlineKeyboardButton("👁‍🗨 Tomosha qilish", url=f"https://t.me/{bot.get_me().username}?start={code}"))
        
        try:
            bot.send_photo(KANAL_USERNAME, photo_id, caption=full_text, parse_mode="Markdown", reply_markup=btn)
            bot.send_message(msg.chat.id, "✅ Post kanalga muvaffaqiyatli joylandi!")
        except Exception as e:
            bot.send_message(msg.chat.id, f"❌ Xato: {e}\nBot kanalga adminmi?")
    else:
        bot.send_message(msg.chat.id, "❌ Video yubormadingiz.")

@bot.message_handler(func=lambda m: True)
def send_kino(msg):
    code = msg.text
    if code in storage:
        bot.send_video(msg.chat.id, storage[code]['id'], caption=f"🎬 Kino kodi: {code}")
    else:
        bot.send_message(msg.chat.id, "❌ Bunday kodli kino topilmadi.")

if __name__ == "__main__":
    # Serverni alohida oqimda ishga tushirish
    threading.Thread(target=run_flask).start()
    print("Bot va Server ishga tushdi...")
    bot.infinity_polling()
