import os
import time
import telebot

# 🛑 TOKENINGIZ
BOT_TOKEN = "8300065405:AAF06AxjTEny7zfQxVEFk38Cw3hGCIijxb8"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Global Ma'lumotlar Bazasi
DB = {
    "target_usernames": [],
    "users": {},
    "media_filters": {},
    "active_members": [], # Skanerlangan a'zolar ro'yxati
    "warns": {},          # Ogohlantirishlar (Warn)
    "welcome_msg": "👋 Salom [user]! Guruhimizga xush kelibsiz!", # Group Help uslubida salomlashish
    "anti_link": False,   # Reklama himoyasi
    "anti_bot": False     # Guruhga begona bot qo'shishni taqiqlash
}

def is_admin(chat_id, user_id):
    if chat_id == user_id: return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except: return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 **Men universal guruh boshqaruvchisiman!**\n\n"
                          "Menda Group Help + Miss Rose + Odam qo'shuvchi + TagAll tizimlari birlashgan.\n"
                          "Buyruqlar ro'yxatini ko'rish uchun guruhda `/help` deb yozing.")

@bot.message_handler(commands=['help'])
def send_help(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    help_text = (
        "📚 **Botning barcha buyruqlari ro'yxati:**\n\n"
        "🛡 **1. Admin panel (Miss Rose & Group Help):**\n"
        "• `/ban` - Guruhdan butunlay haydash (reply)\n"
        "• `/unban` - Bandan chiqarish (reply)\n"
        "• `/mute` - Yozishni cheklash (reply)\n"
        "• `/unmute` - Blokdan chiqarish (reply)\n"
        "• `/warn` - Ogohlantirish berish (3/3 avto-mute) (reply)\n"
        "• `/unwarn` - Ogohlantirishni olib tashlash (reply)\n"
        "• `/del` - Guruhdagi xabarni o'chirish (reply)\n"
        "• `/pin` - Xabarni qadab qo'yish (reply)\n\n"
        "⚙️ **2. Guruh Sozlamalari:**\n"
        "• `/antilink on/off` - Reklama (link) himoyasi\n"
        "• `/antibot on/off` - Guruhga begona botlarni kiritmaslik\n"
        "• `/setwelcome [matn]` - Yangi kelganlarga salomlashish matni (`[user]` kalit so'zi bilan)\n\n"
        "👥 **3. Odam qo'shish tizimi:**\n"
        "• `/addtarget @username` - Qo'shilishi shart bo'lgan nishon kanal/guruh\n"
        "• `/targets` - Hozirgi nishonlar ro'yxati\n\n"
        "📢 **4. Odam belgilovchi (TagAll):**\n"
        "• `/tagall [matn]` - Guruh a'zolarini ommaviy chaqirish\n\n"
        "📝 **5. Media Filtrlar (Miss Rose):**\n"
        "• `/filter [kalit]` - Biror xabarga reply qilib yozilsa, avto-javob saqlaydi\n"
        "• `/stop [kalit]` - Filtrni o'chiradi"
    )
    bot.reply_to(message, help_text)

# ==========================================
# 🛡 1. ADMIN QOBILIYATLARI (BAN, MUTE, WARN, PIN, DEL)
# ==========================================

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.ban_chat_member(message.chat.id, uid)
        bot.reply_to(message, f"❌ Foydalanuvchi guruhdan haydaldi.")
    except: bot.reply_to(message, "⚠️ Huquq yetarli emas.")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.unban_chat_member(message.chat.id, uid, only_if_banned=True)
        bot.reply_to(message, "✅ Foydalanuvchi bandan chiqarildi.")
    except: pass

@bot.message_handler(commands=['mute'])
def mute_user(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(message.chat.id, uid, until_date=time.time()+86400, can_send_messages=False)
        bot.reply_to(message, "🔇 Foydalanuvchi yozishdan cheklandi.")
    except: pass

@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(message.chat.id, uid, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
        bot.reply_to(message, "🔊 Foydalanuvchi blokdan ochildi.")
    except: pass

@bot.message_handler(commands=['warn'])
def warn_user(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    uid = str(message.reply_to_message.from_user.id)
    DB["warns"][uid] = DB["warns"].get(uid, 0) + 1
    count = DB["warns"][uid]
    if count >= 3:
        try:
            bot.restrict_chat_member(message.chat.id, int(uid), until_date=time.time()+86400, can_send_messages=False)
            bot.reply_to(message, f"🔇 Foydalanuvchi 3 ta ogohlantirish bilan mute qilindi!")
            DB["warns"][uid] = 0
        except: pass
    else:
        bot.reply_to(message, f"⚠️ Ogohlantirish berildi: {count}/3")

@bot.message_handler(commands=['unwarn'])
def unwarn_user(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    uid = str(message.reply_to_message.from_user.id)
    DB["warns"][uid] = max(0, DB["warns"].get(uid, 0) - 1)
    bot.reply_to(message, f"✅ Ogohlantirish kamaytirildi: {DB["warns"][uid]}/3")

@bot.message_handler(commands=['del'])
def delete_msg(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if message.reply_to_message:
        try:
            bot.delete_message(message.chat.id, message.reply_to_message.message_id)
            bot.delete_message(message.chat.id, message.message_id)
        except: pass

@bot.message_handler(commands=['pin'])
def pin_msg(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if message.reply_to_message:
        try: bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        except: pass

# ==========================================
# ⚙️ 2. GURUH SOZLAMALARI (ANTI-LINK, ANTI-BOT, WELCOME)
# ==========================================

@bot.message_handler(commands=['antilink'])
def set_antilink(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split()
    if len(args) > 1:
        if args[1].lower() == "on":
            DB["anti_link"] = True
            bot.reply_to(message, "✅ Reklama (link) himoyasi yoqildi.")
        else:
            DB["anti_link"] = False
            bot.reply_to(message, "❌ Reklama (link) himoyasi o'chirildi.")

@bot.message_handler(commands=['antibot'])
def set_antibot(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split()
    if len(args) > 1:
        if args[1].lower() == "on":
            DB["anti_bot"] = True
            bot.reply_to(message, "✅ Anti-Bot tizimi yoqildi.")
        else:
            DB["anti_bot"] = False
            bot.reply_to(message, "❌ Anti-Bot tizimi o'chirildi.")

@bot.message_handler(commands=['setwelcome'])
def set_welcome(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        DB["welcome_msg"] = args[1]
        bot.reply_to(message, "✅ Yangi kelganlar uchun salomlashish matni o'zgartirildi.")

# ==========================================
# 👥 3 & 4. ODAM QO'SHUVCHI + TAGALL TIZIMI
# ==========================================

@bot.message_handler(commands=['addtarget'])
def add_target(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('@'):
        if args[1] not in DB["target_usernames"]:
            DB["target_usernames"].append(args[1])
            bot.reply_to(message, f"✅ {args[1]} nishonga olindi.")
    else: bot.reply_to(message, "⚠️ Format: `/addtarget @username`")

@bot.message_handler(commands=['targets'])
def list_targets(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if DB["target_usernames"]:
        bot.reply_to(message, "🎯 **Hozirgi nishon kanallar:**\n" + "\n".join(DB["target_usernames"]))
    else: bot.reply_to(message, "🎯 Nishonlar ro'yxati bo'sh.")

@bot.message_handler(commands=['tagall'])
def tag_all(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not DB["active_members"]:
        bot.reply_to(message, "⚠️ Ro'yxatda a'zolar yo'q.")
        return
    msg_text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else "Diqqat e'lon!"
    bot.send_message(message.chat.id, "📢 Guruh a'zolarini chaqirish boshlandi...")
    
    for i in range(0, len(DB["active_members"]), 5):
        chunk = DB["active_members"][i:i+5]
        mention_text = f"📣 *{msg_text}*\n\n"
        for uid in chunk:
            mention_text += f"[A'zo](tg://user?id={uid}) "
        bot.send_message(message.chat.id, mention_text)
        time.sleep(0.5)

# ==========================================
# 📝 5. MEDIA FILTRLAR (MISS ROSE)
# ==========================================

@bot.message_handler(commands=['filter'])
def save_filter(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    reply = message.reply_to_message
    args = message.text.split()
    if not reply or len(args) < 2:
        bot.reply_to(message, "⚠️ Reply qilib, `/filter kalit` yozing.")
        return
    keyword = args[1].lower()
    filter_data = {"type": "text", "file_id": None, "caption": reply.text or reply.caption or ""}
    if reply.video: filter_data.update({"type": "video", "file_id": reply.video.file_id})
    elif reply.photo: filter_data.update({"type": "photo", "file_id": reply.photo[-1].file_id})
    elif reply.voice: filter_data.update({"type": "voice", "file_id": reply.voice.file_id})
    elif reply.sticker: filter_data.update({"type": "sticker", "file_id": reply.sticker.file_id})
    DB["media_filters"][keyword] = filter_data
    bot.reply_to(message, f"✅ '{keyword}' filtri saqlandi!")

@bot.message_handler(commands=['stop'])
def stop_filter(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split()
    if len(args) > 1:
        keyword = args[1].lower()
        if keyword in DB["media_filters"]:
            del DB["media_filters"][keyword]
            bot.reply_to(message, f"❌ '{keyword}' filtri o'chirildi.")

# ==========================================
# 🔄 6. SENSYUR VA MONITORING EVENTLAR
# ==========================================

@bot.message_handler(content_types=['new_chat_members'])
def new_member_handler(message):
    for member in message.new_chat_members:
        # Anti-Bot Tizimi
        if member.is_bot and DB["anti_bot"]:
            try: bot.ban_chat_member(message.chat.id, member.id)
            except: pass
            continue
            
        # TagAll uchun ro'yxatga olish
        if member.id not in DB["active_members"] and not member.is_bot:
            DB["active_members"].append(member.id)
            
        # Group Help uslubida salomlashish
        mention = f"[{member.first_name}](tg://user?id={member.id})"
        w_msg = DB["welcome_msg"].replace("[user]", mention)
        bot.send_message(message.chat.id, w_msg)

        # Odam qo'shuvchi hisob-kitobi
        adder_id = str(message.from_user.id)
        if adder_id not in DB["users"]:
            DB["users"][adder_id] = {"added_count": 0, "expires_at": 0, "is_unlimited": False}
        if member.username:
            user_tag = f"@{member.username}"
            if user_tag in DB["target_usernames"]:
                DB["target_usernames"].remove(user_tag)
                DB["users"][adder_id]["added_count"] += 1
                now = int(time.time())
                curr_exp = DB["users"][adder_id]["expires_at"]
                start = curr_exp if curr_exp > now else now
                cnt = DB["users"][adder_id]["added_count"]
                if cnt == 1: DB["users"][adder_id]["expires_at"] = start + 86400
                elif cnt == 2: DB["users"][adder_id]["expires_at"] = start + 172800
                elif cnt >= 5: DB["users"][adder_id]["is_unlimited"] = True

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video', 'voice', 'sticker'])
def global_monitor(message):
    if message.chat.type == "private": return
    uid = message.from_user.id
    
    # Har bir yozgan odamni TagAll uchun ro'yxatga qo'shish
    if not message.from_user.is_bot and uid not in DB["active_members"]:
        DB["active_members"].append(uid)

    # Anti-Link (Reklama himoyasi)
    if DB["anti_link"] and message.text and ("t.me" in message.text or "http" in message.text or "@" in message.text):
        if not is_admin(message.chat.id, uid):
            try: bot.delete_message(message.chat.id, message.message_id)
            except: pass
            return

    # Miss Rose Media Filtrlar
    if message.text and message.text.lower() in DB["media_filters"]:
        f = DB["media_filters"][message.text.lower()]
        if f["type"] == "text": bot.reply_to(message, f["caption"])
        elif f["type"] == "video": bot.send_video(message.chat.id, f["file_id"], caption=f["caption"])
        elif f["type"] == "photo": bot.send_photo(message.chat.id, f["file_id"], caption=f["caption"])
        elif f["type"] == "voice": bot.send_voice(message.chat.id, f["file_id"])
        elif f["type"] == "sticker": bot.send_sticker(message.chat.id, f["file_id"])
        return

    # Odam qo'shish majburiyati (Odam qo'shmaganlarni o'chirish)
    if not is_admin(message.chat.id, uid):
        user_data = DB["users"].get(str(uid))
        now = int(time.time())
        has_access = user_data and (user_data["is_unlimited"] or user_data["expires_at"] > now)
        if not has_access:
            try: bot.delete_message(message.chat.id, message.message_id)
            except: pass

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)
    print("Super Universal Bot yoqildi...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
