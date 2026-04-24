import telebot
from telebot import types
import threading
from flask import Flask

# --- RENDER SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"
def run_flask(): app.run(host='0.0.0.0', port=8080)

# --- SOZLAMALAR ---
API_TOKEN = '8523975201:AAHrN7IRjCFx2j33v2kEQY2Ku1qIaPg9IHY'
ADMIN_ID = 8625345482 
KANAL_ID = "@psjfkspjsl" 

bot = telebot.TeleBot(API_TOKEN)
storage = {} 

def check_sub(user_id):
    try:
        status = bot.get_chat_member(KANAL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

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
            bot.send_message(msg.chat.id, "❌ Kino topilmadi.")
    else:
        bot.send_message(msg.chat.id, "👋 Salom! Kino kodini yuboring.")

# --- ADMIN QISMI (ZANJIRLI) ---

@bot.message_handler(content_types=['photo'])
def handle_admin_photo(msg):
    if msg.from_user.id == ADMIN_ID:
        m = bot.send_message(msg.chat.id, "🎬 **1. Anime nomini kiriting:**")
        bot.register_next_step_handler(m, get_name, msg.photo[-1].file_id)

def get_name(msg, photo_id):
    name = msg.text
    m = bot.send_message(msg.chat.id, "🎭 **2. Janrini kiriting:**")
    bot.register_next_step_handler(m, get_janr, photo_id, name)

def get_janr(msg, photo_id, name):
    janr = msg.text
    m = bot.send_message(msg.chat.id, "🎞 **3. Qismlar sonini kiriting:**")
    bot.register_next_step_handler(m, get_parts, photo_id, name, janr)

def get_parts(msg, photo_id, name, janr):
    parts = msg.text
    m = bot.send_message(msg.chat.id, "🔢 **4. Ushbu anime uchun KOD kiriting:**")
    bot.register_next_step_handler(m, get_code, photo_id, name, janr, parts)

def get_code(msg, photo_id, name, janr, parts):
    code = msg.text
    m = bot.send_message(msg.chat.id, "📹 **5. ENDI VIDEONI YUBORING:**")
    bot.register_next_step_handler(m, finish_all, photo_id, name, janr, parts, code)

def finish_all(msg, photo_id, name, janr, parts, code):
    if msg.content_type == 'video':
        video_id = msg.video.file_id
        storage[code] = video_id # Kodni saqlash
        
        full_text = (
            f"📂 **Nomi:** {name}\n"
            f"🗡 **Janri:** {janr}\n"
            f"🎞 **Qismlar:** {parts}\n"
            f"🔢 **Kod:** `{code}`"
        )
        
        btn = types.InlineKeyboardMarkup()
        btn.add(types.InlineKeyboardButton("👁‍🗨 Tomosha qilish", url=f"https://t.me/{bot.get_me().username}?start={code}"))
        
        try:
            bot.send_photo(KANAL_ID, photo_id, caption=full_text, reply_markup=btn)
            bot.send_message(msg.chat.id, "✅ Kanalga muvaffaqiyatli joylandi!")
        except Exception as e:
            bot.send_message(msg.chat.id, f"❌ Kanalga yuborishda xato: {e}\nBot kanalga adminmi?")
    else:
        bot.send_message(msg.chat.id, "❌ Siz video yubormadingiz! Jarayon bekor qilindi.")

# --- KOD QIDIRISH ---
@bot.message_handler(func=lambda m: True)
def search_code(msg):
    if not check_sub(msg.from_user.id):
        bot.send_message(msg.chat.id, "❌ Kanalga obuna bo'ling!", reply_markup=sub_markup())
        return
        
    code = msg.text
    if code in storage:
        bot.send_video(msg.chat.id, storage[code], caption=f"🎬 Kod: {code}")
    else:
        bot.send_message(msg.chat.id, "❌ Bunday kodli anime topilmadi.")

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_callback(call):
    if check_sub(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ Rahmat! Endi kodni yuboring.")
    else:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmadingiz!", show_alert=True)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
