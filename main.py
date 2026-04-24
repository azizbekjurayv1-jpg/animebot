import telebot
import json
import os

# --- BAZA BILAN ISHLASH ---
def load_data():
    if os.path.exists('storage.json'):
        with open('storage.json', 'r') as f:
            try: 
                return json.load(f)
            except: 
                return {}
    return {}

def save_data(data):
    with open('storage.json', 'w') as f:
        json.dump(data, f, indent=4)

storage = load_data()

# --- SOZLAMALAR ---
# Yangi tokeningizni joylashtirdim
API_TOKEN = '8523975201:AAHrN7IRjCFx2j33v2kEQY2Ku1qIaPg9IHY'
bot = telebot.TeleBot(API_TOKEN)
ADMIN_ID = 46456266 

@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, "👋 Salom! Kino kodini yuboring yoki admin bo'lsangiz video yuklang.")

@bot.message_handler(content_types=['video', 'document'])
def add_kino(msg):
    if msg.from_user.id == ADMIN_ID:
        m = bot.send_message(msg.chat.id, "🎬 Bu kino uchun kod kiriting:")
        bot.register_next_step_handler(m, save_kino, msg)

def save_kino(msg, original):
    code = msg.text
    # Video yoki fayl ekanligini aniqlash
    if original.content_type == 'video':
        f_id = original.video.file_id
        f_type = 'v'
    else:
        f_id = original.document.file_id
        f_type = 'd'
        
    storage[code] = {'t': f_type, 'id': f_id}
    save_data(storage)
    bot.send_message(msg.chat.id, f"✅ Saqlandi! Kino kodi: {code}")

@bot.message_handler(func=lambda m: True)
def get_kino(msg):
    code = msg.text
    if code in storage:
        k = storage[code]
        if k['t'] == 'v':
            bot.send_video(msg.chat.id, k['id'], caption=f"Kino kodi: {code}")
        else:
            bot.send_document(msg.chat.id, k['id'], caption=f"Kino kodi: {code}")
    else:
        bot.send_message(msg.chat.id, "❌ Bunday kodli kino topilmadi.")

print("Bot Renderda ishlashga tayyor...")
bot.infinity_polling()
