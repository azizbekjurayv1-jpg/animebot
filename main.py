import os
import json
import time
import threading
from flask import Flask
import telebot

# 🛑 TOKENINGIZ KOD ICHIGA JOYLASHTIRILDI
BOT_TOKEN = "8779270757:AAHd8EHjlXLi0cNWYpkKWQwmDhj18AUfP_4"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

DB_PATH = "baza.json"
active_members = set()  # TagAll uchun vaqtinchalik faol a'zolar ro'yxati

# JSON bazani o'qish
def read_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({"target_usernames": [], "users": {}, "media_filters": {}}, f, ensure_ascii=False, indent=2)
    try:
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Bazani o'qishda xatolik: {e}")
        return {"target_usernames": [], "users": {}, "media_filters": {}}

# JSON bazaga yozish
def write_db(data):
    try:
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Bazaga yozishda xatolik: {e}")

# Adminlikni tekshirish
def is_admin(chat_id, user_id):
    if chat_id == user_id:  # Shaxsiy chat bo'lsa
        return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except:
        return False

# ==========================================
# 1. GURUHGA ODAM QO'SHISH VA TARIFLAR
# ==========================================
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    db = read_db()
    adder_id = str(message.from_user.id)
    
    if adder_id not in db["users"]:
        db["users"][adder_id] = {"added_count": 0, "expires_at": 0, "is_unlimited": False}
        
    for member in message.new_chat_members:
        if member.username:
            formatted_username = f"@{member.username}"
            # Agar qo'shilgan odam admin bergan bazada bo'lsa
            if formatted_username in db["target_usernames"]:
                db["target_usernames"].remove(formatted_username) # Bazadan o'chirish (bitta odam faqat bir marta ishlasin)
                db["users"][adder_id]["added_count"] += 1
                
                now = int(time.time())
                current_expire = db["users"][adder_id]["expires_at"]
                start_time = current_expire if current_expire > now else now
                
                # Kunlik tariflarni hisoblash
                count = db["users"][adder_id]["added_count"]
                if count == 1:
                    db["users"][adder_id]["expires_at"] = start_time + (24 * 60 * 60) # +1 kun
                elif count == 2:
                    db["users"][adder_id]["expires_at"] = start_time + (2 * 24 * 60 * 60) # +2 kun
                elif count >= 5:
                    db["users"][adder_id]["is_unlimited"] = True # Cheksiz
                    
    write_db(db)

# Admin buyrug'i: Target foydalanuvchi nomini qo'shish
@bot.message_handler(commands=['addtarget'])
def add_target_username(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('@'):
        db = read_db()
        if args[1] not in db["target_usernames"]:
            db["target_usernames"].append(args[1])
            write_db(db)
            bot.reply_to(message, f"✅ {args[1]} ro'yxatga qo'shildi.")
    else:
        bot.reply_to(message, "⚠️ Ishlatish: `/addtarget @username`")

# ==========================================
# 2. MISS ROSE USLUBIDAGI MEDIA FILTER
# ==========================================
@bot.message_handler(commands=['filter'])
def save_media_filter(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    reply = message.reply_to_message
    args = message.text.split()
    
    if not reply or len(args) < 2:
        bot.reply_to(message, "⚠️ Ishlatish: Biror xabarga reply qilib, `/filter kalit_soz` deb yozing.")
        return
        
    keyword = args[1].lower()
    db = read_db()
    
    filter_data = {"type": "text", "file_id": None, "caption": reply.text or reply.caption or ""}
    
    if reply.video:
        filter_data.update({"type": "video", "file_id": reply.video.file_id})
    elif reply.photo:
        filter_data.update({"type": "photo", "file_id": reply.photo[-1].file_id})
    elif reply.voice:
        filter_data.update({"type": "voice", "file_id": reply.voice.file_id})
    elif reply.audio:
        filter_data.update({"type": "audio", "file_id": reply.audio.file_id})
    elif reply.document:
        filter_data.update({"type": "document", "file_id": reply.document.file_id})
    elif reply.sticker:
        filter_data.update({"type": "sticker", "file_id": reply.sticker.file_id})
        
    db["media_filters"][keyword] = filter_data
    write_db(db)
    bot.reply_to(message, f"✅ \"{keyword}\" kalit so'zi uchun media filtr saqlandi!")

@bot.message_handler(commands=['stop'])
def stop_media_filter(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "⚠️ Ishlatish: `/stop kalit_soz`")
        
    keyword = args[1].lower()
    db = read_db()
    if keyword in db["media_filters"]:
        del db["media_filters"][keyword]
        write_db(db)
        bot.reply_to(message, f"🛑 \"{keyword}\" filtri o'chirildi.")
    else:
        bot.reply_to(message, "❌ Bunday filtr topilmadi.")

# ==========================================
# 3. TAGALL (HAMMANI CHAQIRISH)
# ==========================================
@bot.message_handler(commands=['tagall'])
def tag_all_members(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not active_members:
        bot.reply_to(message, "Hozircha faol a'zolar aniqlanmadi.")
        return
        
    msg_text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else "Diqqat e'lon!"
    bot.send_message(message.chat.id, "📢 Guruh a'zolarini chaqirish boshlandi...")
    
    members_list = list(active_members)
    # 5 tadan bo'lib chaqirish (Telegram flood-chekloviga tushmaslik uchun)
    for i in range(0, len(members_list), 5):
        chunk = members_list[i:i+5]
        mention_text = f"{msg_text}\n\n"
        for user_id in chunk:
            mention_text += f"[Foydalanuvchi](tg://user?id={user_id}) "
        bot.send_message(message.chat.id, mention_text, parse_mode="Markdown")
        time.sleep(0.5)

# ==========================================
# GURUH FILTR TRIGGERS VA RUXSATLAR NAZORATI
# ==========================================
@bot.message_handler(func=lambda msg: True, content_types=['text', 'photo', 'video', 'voice', 'audio', 'document', 'sticker'])
def monitor_group_messages(message):
    if message.chat.type == "private":
        return
        
    user_id = message.from_user.id
    user_id_str = str(user_id)
    
    # Faol a'zolar ro'yxatiga qo'shish (TagAll ishlashi uchun)
    if not message.from_user.is_bot:
        active_members.add(user_id)
        
    # 1. Media filtrlarni tekshirish (Agar matn kalit so'zga mos kelsa)
    if message.text:
        text_lower = message.text.lower()
        db = read_db()
        if text_lower in db["media_filters"]:
            f = db["media_filters"][text_lower]
            if f["type"] == "text": bot.reply_to(message, f["caption"])
            elif f["type"] == "video": bot.send_video(message.chat.id, f["file_id"], caption=f["caption"])
            elif f["type"] == "photo": bot.send_photo(message.chat.id, f["file_id"], caption=f["caption"])
            elif f["type"] == "voice": bot.send_voice(message.chat.id, f["file_id"])
            elif f["type"] == "audio": bot.send_audio(message.chat.id, f["file_id"], caption=f["caption"])
            elif f["type"] == "document": bot.send_document(message.chat.id, f["file_id"], caption=f["caption"])
            elif f["type"] == "sticker": bot.send_sticker(message.chat.id, f["file_id"])
            return

    # 2. Odam qo'shish ruxsatnomasini tekshirish (Adminlarga cheklov qo'yilmaydi)
    if not is_admin(message.chat.id, user_id):
        db = read_db()
        user_data = db["users"].get(user_id_str)
        now = int(time.time())
        
        has_access = False
        if user_data:
            if user_data["is_unlimited"] or user_data["expires_at"] > now:
                has_access = True
                
        if not has_access:
            # Ruxsatsiz xabarni darhol guruhdan o'chirish
            try: bot.delete_message(message.chat.id, message.message_id)
            except: pass
            
            count = user_data["added_count"] if user_data else 0
            warn = bot.send_message(
                message.chat.id, 
                f"⚠️ @{message.from_user.username or message.from_user.first_name} guruhga xabar yozish uchun admin belgilangan odamlarni qo'shishingiz kerak!\n\n"
                f"Siz qo'shgan odamlar soni: {count}\n"
                f"1 ta odam = 1 kun yozish ruxsati\n"
                f"2 ta odam = 2 kun yozish ruxsati\n"
                f"5 ta odam = Umrbod cheksiz yozish\n"
                f"10+ odam = Adminlik taklifi! 👑"
            )
            # 8 soniyadan keyin ogohlantirishni o'chirib yuborish
            threading.Thread(target=lambda: (time.sleep(8), bot.delete_message(message.chat.id, warn.message_id))).start()
            return
            
        # 10+ odam qo'shganda adminlik taklifi (Faqat 1 marta chiqadi)
        if user_data and user_data["added_count"] == 10:
            bot.send_message(message.chat.id, f"🎉 Rahmat @{message.from_user.username or message.from_user.first_name}! Siz 10 tadan ko'p odam qo'shdingiz. Admin sifatida xabar yozishni xohlaysizmi? Biz bilan bog'laning.")
            user_data["added_count"] = 11  # Qayta chiqmasligi uchun statusni o'zgartirish
            write_db(db)

# ==========================================
# RENDER UCHUN FLASK WEB SERVER (24/7 MAJBURIY)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7 natively on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Web serverni orqa fonda yoqish (Render o'chib qolmasligi uchun)
    t = threading.Thread(target=run_flask)
    t.start()
    print("Bot ishga tushdi...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

