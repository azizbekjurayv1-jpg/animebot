import telebot
from telebot import types
import json
import os
import threading
from flask import Flask

# --- RENDER UCHUN SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"
def run_flask(): app.run(host='0.0.0.0', port=8080)

# --- SOZLAMALAR ---
API_TOKEN = '8523975201:AAHrN7IRjCFx2j33v2kEQY2Ku1qIaPg9IHY'
ADMIN_ID = 8625345482 
KANAL_ID = "@psjfkspjsl" # Kanal username (@ bilan)

bot = telebot.TeleBot(API_TOKEN)
storage = {} # Kinolarni vaqtinchalik saqlash

# Obunani tekshirish funksiyasi
def check_sub(user_id):
    try:
        status = bot.get_chat_member(KANAL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

# Obuna bo'lish tugmasi
def sub_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Obuna bo'lish", url=f"https://t.me/{KANAL_ID[1:]}"))
    markup.add(types.InlineKeyboardButton("Tekshirish ✅", callback_data="check"))
    return markup

@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id
    if not check_sub(user_id):
        bot.send_message(user_id, f"❌ Botdan foydalanish uchun kanalimizga obuna bo'ling!", reply_markup=sub_markup())
        return

    args = msg.text.split()
    if len(args) > 1:
        code = args[1]
        if code in storage:
            bot.send_video(msg.chat.id, storage[code], caption=f"🎬 Kod: {code}\n\n@psjfkspjsl")
        else:
            bot.send_message(msg.chat.id, "❌ Bu kino kodi topilmadi yoki bot yangilanganda o'chib ketgan.")
    else:
        bot.send_message(msg.chat.id, "👋 Salom! Kino kodini yuboring.")

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_callback(call):
    if check_sub(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ Rahmat! Endi kodni yuborishingiz mumkin.")
    else:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmadingiz!", show_alert=True)

@bot.message_handler(content_types=['photo'])
def handle_admin_photo(msg):
    if msg.from_user.id == ADMIN_ID:
        m = bot.send_message(msg.chat.id, "🎬 **Nomi:**")
        bot.register_next_step_handler(m, get_janr, msg.photo[-1].file_id)

def get_janr(msg, photo_id):
    bot.register_next_step_handler(bot.send_message(msg.chat.id, "🎭 **Janri:**"), get_qismlar, photo_id, msg.text)

def get_qismlar(msg, photo_id, name):
    bot.register_next_step_handler(bot.send_message(msg.chat.id, "🎞 **Qismlar:**"), get_code, photo_id, name, msg.text)

def get_code(msg, photo_id, name, janr):
    bot.register_next_step_handler(bot.send_message(msg.chat.id, "🔢 **KOD:**"), get_video, photo_id, name, janr, msg.text)

def get_video(msg, photo_id, name, janr, qismlar, code):
    bot.register_next_step_handler(bot.send_message(msg.chat.id, "📹 **Video yuboring:**"), finish_post, photo_id, name, janr, qismlar, code)

def finish_post(msg, photo_id, name, janr, qismlar, code):
    if msg.content_type == 'video':
        storage[code] = msg.video.file_id # Kodni saqlash
        
        full_text = f"📂 **Nomi:** {name}\n🗡 **Janri:** {janr}\n🎞 **Qismlar:** {qismlar}\n🔢 **Kod:** `{code}`"
        
        btn = types.InlineKeyboardMarkup()
        btn.add(types.InlineKeyboardButton("👁‍🗨 Tomosha qilish", url=f"https://t.me/{bot.get_me().username}?start={code}"))
        
        bot.send_photo(KANAL_ID, photo_id, caption=full_text, reply_markup=btn)
        bot.send_message(msg.chat.id, "✅ Kanalga joylandi!")
    else:
        bot.send_message(msg.chat.id, "❌ Xato! Video yuboring.")

@bot.message_handler(func=lambda m: True)
def send_kino_by_code(msg):
    if not check_sub(msg.from_user.id):
        bot.send_message(msg.chat.id, "❌ Kanalga obuna bo'ling!", reply_markup=sub_markup())
        return
        
    code = msg.text
    if code in storage:
        bot.send_video(msg.chat.id, storage[code], caption=f"🎬 Kino kodi: {code}")
    else:
        bot.send_message(msg.chat.id, "❌ Topilmadi.")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
