import telebot
from telebot import types
import threading
from flask import Flask
import time

app = Flask('')
@app.route('/')
def home(): return "Bot is running!"
def run_flask(): app.run(host='0.0.0.0', port=8080)

# --- SOZLAMALAR ---
API_TOKEN = '8523975201:AAHrN7IRjCFx2j33v2kEQY2Ku1qIaPg9IHY'
ADMIN_ID = 8625345482 
KANAL_ID = "@psjfkspjsl" 

bot = telebot.TeleBot(API_TOKEN)
storage = {} # Kinolar bazasi
admin_data = {} # Admin vaqtinchalik ma'lumotlari

def check_sub(user_id):
    try:
        status = bot.get_chat_member(KANAL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id
    if not check_sub(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Obuna bo'lish", url=f"https://t.me/{KANAL_ID[1:]}"))
        bot.send_message(user_id, "❌ Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=markup)
        return

    args = msg.text.split()
    if len(args) > 1:
        code = args[1]
        if code in storage:
            videos = storage[code]['videos']
            bot.send_message(user_id, f"🎬 **{storage[code]['name']}** barcha qismlari yuborilmoqda...")
            
            # Videolarni albom (media group) shaklida yuborish
            media = []
            for v_id in videos:
                media.append(types.InputMediaVideo(v_id))
            
            # Telegram bitta albomda max 10 ta video ruxsat beradi
            # Agar 10 tadan ko'p bo'lsa, bo'lib yuboradi
            for i in range(0, len(media), 10):
                bot.send_media_group(user_id, media[i:i+10])
        else:
            bot.send_message(user_id, "❌ Anime topilmadi.")
    else:
        bot.send_message(user_id, "👋 Salom! Anime kodini yuboring.")

# --- ADMIN QISMI ---
@bot.message_handler(content_types=['photo'])
def admin_photo(msg):
    if msg.from_user.id == ADMIN_ID:
        m = bot.send_message(msg.chat.id, "🎬 **Anime nomi:**")
        bot.register_next_step_handler(m, get_name, msg.photo[-1].file_id)

def get_name(msg, photo_id):
    name = msg.text
    m = bot.send_message(msg.chat.id, "🔢 **Kod kiriting:**")
    bot.register_next_step_handler(m, get_code, photo_id, name)

def get_code(msg, photo_id, name):
    code = msg.text
    admin_data[msg.from_user.id] = {'name': name, 'photo': photo_id, 'code': code, 'videos': []}
    bot.send_message(msg.chat.id, "📹 Endi barcha videolarni **birdaniga belgilab** yuboring. Yuklanib bo'lgach **/save** deb yozing.")

@bot.message_handler(content_types=['video'])
def collect_vids(msg):
    uid = msg.from_user.id
    if uid == ADMIN_ID and uid in admin_data:
        admin_data[uid]['videos'].append(msg.video.file_id)

@bot.message_handler(commands=['save'])
def save_anime(msg):
    uid = msg.from_user.id
    if uid == ADMIN_ID and uid in admin_data:
        data = admin_data[uid]
        storage[data['code']] = {'name': data['name'], 'videos': data['videos']}
        
        # Kanalga post
        btn = types.InlineKeyboardMarkup()
        btn.add(types.InlineKeyboardButton("👁‍🗨 Barcha qismlarni ko'rish", url=f"https://t.me/{bot.get_me().username}?start={data['code']}"))
        
        bot.send_photo(KANAL_ID, data['photo'], caption=f"📂 **Nomi:** {data['name']}\n🎞 **Qismlar:** {len(data['videos'])}\n🔢 **Kod:** `{data['code']}`", reply_markup=btn)
        bot.send_message(msg.chat.id, "✅ Kanalga joylandi va xotiraga saqlandi!")
        del admin_data[uid]

@bot.message_handler(func=lambda m: True)
def search_text(msg):
    code = msg.text
    if code in storage:
        # Kod yozilganda ham hammasini yuboradi
        media = [types.InputMediaVideo(v) for v in storage[code]['videos']]
        for i in range(0, len(media), 10):
            bot.send_media_group(msg.chat.id, media[i:i+10])
    else:
        bot.send_message(msg.chat.id, "❌ Topilmadi.")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
