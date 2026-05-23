import os
import time
import telebot

# 🛑 SIZNING TOKENINGIZ
BOT_TOKEN = "8779270757:AAF_L1Z4rTTWskj0Yt0VPxpsHUnU7jSznPM"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Xavfsiz xotira (Railway uchun eng zo'r yengil variant)
DB = {
    "target_usernames": [],
    "users": {},
    "media_filters": {},
    "active_members": []
}

def is_admin(chat_id, user_id):
    if chat_id == user_id: return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except: return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Salom! Railway'da bot daxshatli tezlikda ishlamoqda. Guruhga qo'shing!")

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    adder_id = str(message.from_user.id)
    if adder_id not in DB["users"]:
        DB["users"][adder_id] = {"added_count": 0, "expires_at": 0, "is_unlimited": False}
        
    for member in message.new_chat_members:
        if member.username:
            formatted_username = f"@{member.username}"
            if formatted_username in DB["target_usernames"]:
                DB["target_usernames"].remove(formatted_username)
                DB["users"][adder_id]["added_count"] += 1
                
                now = int(time.time())
                current_expire = DB["users"][adder_id]["expires_at"]
                start_time = current_expire if current_expire > now else now
                
                count = DB["users"][adder_id]["added_count"]
                if count == 1:
                    DB["users"][adder_id]["expires_at"] = start_time + (24 * 60 * 60)
                elif count == 2:
                    DB["users"][adder_id]["expires_at"] = start_time + (2 * 24 * 60 * 60)
                elif count >= 5:
                    DB["users"][adder_id]["is_unlimited"] = True

@bot.message_handler(commands=['addtarget'])
def add_target_username(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('@'):
        if args[1] not in DB["target_usernames"]:
            DB["target_usernames"].append(args[1])
            bot.reply_to(message, f"✅ {args[1]} ro'yxatga qo'shildi.")
    else:
        bot.reply_to(message, "⚠️ Format: `/addtarget @username`")

@bot.message_handler(commands=['filter'])
def save_media_filter(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    reply = message.reply_to_message
    args = message.text.split()
    
    if not reply or len(args) < 2:
        bot.reply_to(message, "⚠️ Reply qilib, `/filter kalit` deb yozing.")
        return
        
    keyword = args[1].lower()
    filter_data = {"type": "text", "file_id": None, "caption": reply.text or reply.caption or ""}
    
    if reply.video: filter_data.update({"type": "video", "file_id": reply.video.file_id})
    elif reply.photo: filter_data.update({"type": "photo", "file_id": reply.photo[-1].file_id})
    elif reply.voice: filter_data.update({"type": "voice", "file_id": reply.voice.file_id})
    elif reply.audio: filter_data.update({"type": "audio", "file_id": reply.audio.file_id})
    elif reply.document: filter_data.update({"type": "document", "file_id": reply.document.file_id})
    elif reply.sticker: filter_data.update({"type": "sticker", "file_id": reply.sticker.file_id})
        
    DB["media_filters"][keyword] = filter_data
    bot.reply_to(message, f"✅ \"{keyword}\" filtri saqlandi!")

@bot.message_handler(commands=['tagall'])
def tag_all_members(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not DB["active_members"]:
        bot.reply_to(message, "⚠️ Guruhda faol a'zolar yo'q.")
        return
    msg_text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else "Diqqat!"
    for i in range(0, len(DB["active_members"]), 5):
        chunk = DB["active_members"][i:i+5]
        mention_text = f"{msg_text}\n\n"
        for user_id in chunk:
            mention_text += f"[Foydalanuvchi](tg://user?id={user_id}) "
        bot.send_message(message.chat.id, mention_text, parse_mode="Markdown")
        time.sleep(0.5)

@bot.message_handler(func=lambda msg: True, content_types=['text', 'photo', 'video', 'voice', 'audio', 'document', 'sticker'])
def monitor_group_messages(message):
    if message.chat.type == "private": return
    user_id = message.from_user.id
    
    if not message.from_user.is_bot and user_id not in DB["active_members"]:
        DB["active_members"].append(user_id)
        
    if message.text and message.text.lower() in DB["media_filters"]:
        f = DB["media_filters"][message.text.lower()]
        if f["type"] == "text": bot.reply_to(message, f["caption"])
        elif f["type"] == "video": bot.send_video(message.chat.id, f["file_id"], caption=f["caption"])
        elif f["type"] == "photo": bot.send_photo(message.chat.id, f["file_id"], caption=f["caption"])
        elif f["type"] == "voice": bot.send_voice(message.chat.id, f["file_id"])
        elif f["type"] == "sticker": bot.send_sticker(message.chat.id, f["file_id"])
        return

    if not is_admin(message.chat.id, user_id):
        user_data = DB["users"].get(str(user_id))
        now = int(time.time())
        has_access = user_data and (user_data["is_unlimited"] or user_data["expires_at"] > now)
                
        if not has_access:
            try: bot.delete_message(message.chat.id, message.message_id)
            except: pass
            count = user_data["added_count"] if user_data else 0
            bot.send_message(message.chat.id, f"⚠️ Guruhga odam qo'shing! Siz qo'shgan odamlar: {count}")

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)
    print("Railway Polling boshlandi...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
