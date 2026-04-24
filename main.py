import telebot
from telebot import types
import json
import os

# --- SOZLAMALAR ---
API_TOKEN = '8523975201:AAHrN7IRjCFx2j33v2kEQY2Ku1qIaPg9IHY'
ADMIN_ID = 46456266
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

# ADMIN RASM YUBORSA BOSHLANADI
@bot.message_handler(content_types=['photo'])
def handle_admin_post(msg):
    if msg.from_user.id == ADMIN_ID:
        m = bot.send_message(msg.chat.id, "🎬 **Anime/Kino nomini kiriting:**", parse_mode="Markdown")
        bot.register_next_step_handler(m, get_janr, msg.photo[-1].file_id)

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

        # Rasmda ko'rsatilgan chiroyli format:
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
        
        bot.send_photo(KANAL_USERNAME, photo_id, caption=full_text, parse_mode="Markdown", reply_markup=btn)
        bot.send_message(msg.chat.id, "✅ Post kanalga muvaffaqiyatli joylandi!")
    else:
        bot.send_message(msg.chat.id, "❌ Video yubormadingiz, jarayon bekor qilindi.")

@bot.message_handler(func=lambda m: True)
def send_kino(msg):
    code = msg.text
    if code in storage:
        bot.send_video(msg.chat.id, storage[code]['id'], caption=f"🎬 Kino kodi: {code}")
    else:
        bot.send_message(msg.chat.id, "❌ Bunday kodli kino topilmadi.")

bot.infinity_polling()
