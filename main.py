import os
import time
import telebot

# 🛑 TOKENINGIZ
BOT_TOKEN = "8300065405:AAF06AxjTEny7zfQxVEFk38Cw3hGCIijxb8"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Ma'lumotlar Bazasi
DB = {
    "target_usernames": [],
    "users": {},
    "media_filters": {},
    "active_members": [],
    "warns": {},
    "welcome_msg": "👋 Salom [user]! Guruhimizga xush kelibsiz!",
    "anti_link": False,
    "anti_bot": False
}

def is_admin(chat_id, user_id):
    if chat_id == user_id: return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except: return False

# ==========================================
# 🚀 START VA HELP MENYULARI (BOSILADIGAN)
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 **Salom! Men guruhni to'liq nazorat qiluvchi maxsus botman.**\n\n"
        "Guruh xavfsizligi, a'zolarni faollashtirish, reklama himoyasi va media-filtrlar tizimi menda mujassam.\n\n"
        "👇 Bot imkoniyatlarini ko'rish uchun pastdagi tugmani bosing:"
    )
    
    markup = telebot.types.InlineKeyboardMarkup()
    help_button = telebot.types.InlineKeyboardButton(text="📚 Buyruqlar ro'yxati", callback_data="show_help")
    markup.add(help_button)
    
    bot.reply_to(message, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['help'])
def send_help(message):
    show_full_help(message.chat.id, message.message_id, message.from_user.id)

def show_full_help(chat_id, message_id, user_id, is_callback=False):
    if not is_admin(chat_id, user_id): return
    
    help_text = (
        "📚 **Bot buyruqlari ro'yxati (Ustiga bosing):**\n\n"
        "🛡 **1. Admin Buyruqlari (Xabarga javob bering - Reply):**\n"
        "• /ban — Guruhdan haydash\n"
        "• /unban — Bandan chiqarish\n"
        "• /mute — Yozishni cheklash\n"
        "• /unmute — Blokdan ochish\n"
        "• /warn — Ogohlantirish berish (3/3 avto-mute)\n"
        "• /unwarn — Ogohlantirishni kamaytirish\n"
        "• /del — Xabarni o'chirish\n"
        "• /pin — Xabarni yuqoriga qadash\n\n"
        "⚙️ **2. Guruh Himoya Sozlamalari:**\n"
        "• `/antilink on` — Reklama (link) taqiqlash\n"
        "• `/antilink off` — Reklamaga ruxsat berish\n"
        "• `/antibot on` — Begona botlarni taqiqlash\n"
        "• `/antibot off` — Botlarga ruxsat berish\n"
        "• `/targets` — Nishon kanallar ro'yxati\n\n"
        "👥 **3. Aktivlik va Odam Qo'shish:**\n"
        "• `/addtarget @username` — Majburiy kanal qo'shish\n"
        "• `/tagall` — Guruhdagilarni ommaviy chaqirish\n\n"
        "📝 **4. Avto-Javob (Media Filtr):**\n"
        "• `/filter kalit_soz` — Xabarga reply qilib yozilsa, avto-javob saqlaydi\n"
        "• `/stop kalit_soz` — Avto-javobni o'chiradi"
    )
    
    if is_callback:
        try: bot.edit_message_text(text=help_text, chat_id=chat_id, message_id=message_id, parse_mode="Markdown")
        except: pass
    else:
        bot.send_message(chat_id, help_text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "show_help")
def callback_help(call):
    show_full_help(call.message.chat.id, call.message.message_id, call.from_user.id, is_callback=True)
    bot.answer_callback_query(call.id)

# ==========================================
# 🛡 ADMIN PANEL (BAN, MUTE, WARN, PIN, DEL)
# ==========================================

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.ban_chat_member(message.chat.id, uid)
        bot.reply_to(message, f"❌ Foydalanuvchi guruhdan chetlashtirildi.")
    except: bot.reply_to(message, "⚠️ Botda huquq yetarli emas.")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.unban_chat_member(message.chat.id, uid, only_if_banned=True)
        bot.reply_to(message, "✅ Foydalanuvchi guruhga qaytishi mumkin.")
    except: pass

@bot.message_handler(commands=['mute'])
def mute_user(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(message.chat.id, uid, until_date=time.time()+86400, can_send_messages=False)
        bot.reply_to(message, "🔇 Foydalanuvchi yozish huquqidan mahrum qilindi.")
    except: pass

@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(message.chat.id, uid, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
        bot.reply_to(message, "🔊 Foydalanuvchiga yozishga ruxsat berildi.")
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
            bot.reply_to(message, f"🔇 Qoidabuzar 3 ta ogohlantirish to'plagani sababli bloklandi!")
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
    bot.reply_to(message, f"✅ Ogohlantirish olib tashlandi. Hozirgi holat: {DB['warns'][uid]}/3")

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
# ⚙️ GURUH SOZLAMALARI (HIMOYA)
# ==========================================

@bot.message_handler(commands=['antilink'])
def set_antilink(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split()
    if len(args) > 1:
        if args[1].lower() == "on":
            DB["anti_link"] = True
            bot.reply_to(message, "✅ Reklama va ssilkalar himoyasi yoqildi.")
        else:
            DB["anti_link"] = False
            bot.reply_to(message, "❌ Reklama himoyasi o'chirildi.")

@bot.message_handler(commands=['antibot'])
def set_antibot(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split()
    if len(args) > 1:
        if args[1].lower() == "on":
            DB["anti_bot"] = True
            bot.reply_to(message, "✅ Guruhga begona botlarni qo'shish bloklandi.")
        else:
            DB["anti_bot"] = False
            bot.reply_to(message, "❌ Botlar uchun taqiq olib tashlandi.")

@bot.message_handler(commands=['setwelcome'])
def set_welcome(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        DB["welcome_msg"] = args[1]
        bot.reply_to(message, "✅ Yangi kelganlar bilan salomlashish matni yangilandi.")

# ==========================================
# 👥 ODAM QO'SHISH VA MMOBILIY CHAQIRUV (TAGALL)
# ==========================================

@bot.message_handler(commands=['addtarget'])
def add_target(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('@'):
        if args[1] not in DB["target_usernames"]:
            DB["target_usernames"].append(args[1])
            bot.reply_to(message, f"✅ {args[1]} majburiy a'zolik ro'yxatiga olindi.")
    else: bot.reply_to(message, "⚠️ Format: `/addtarget @username`")

@bot.message_handler(commands=['targets'])
def list_targets(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if DB["target_usernames"]:
        bot.reply_to(message, "🎯 **Majburiy kanallar ro'yxati:**\n" + "\n".join(DB["target_usernames"]))
    else: bot.reply_to(message, "🎯 Ro'yxat hozircha bo'sh.")

@bot.message_handler(commands=['tagall'])
def tag_all(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not DB["active_members"]:
        bot.reply_to(message, "⚠️ Guruhda hali ro'yxatga olingan faol foydalanuvchilar yo'q.")
        return
    msg_text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else "Diqqat, muhim e'lon!"
    bot.send_message(message.chat.id, "📢 Guruh a'zolarini chaqirish boshlandi...")
    
    for i in range(0, len(DB["active_members"]), 5):
        chunk = DB["active_members"][i:i+5]
        mention_text = f"📣 *{msg_text}*\n\n"
        for uid in chunk:
            mention_text += f"[A'zo](tg://user?id={uid}) "
        bot.send_message(message.chat.id, mention_text)
        time.sleep(0.5)

# ==========================================
# 📝 AVTO-JAVOB FILTRLARI
# ==========================================

@bot.message_handler(commands=['filter'])
def save_filter(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    reply = message.reply_to_message
    args = message.text.split()
    if not reply or len(args) < 2:
        bot.reply_to(message, "⚠️ Format: Biror xabarga reply qilib, `/filter kalit` yozing.")
        return
    keyword = args[1].lower()
    filter_data = {"type": "text", "file_id": None, "caption": reply.text or reply.caption or ""}
    if reply.video: filter_data.update({"type": "video", "file_id": reply.video.file_id})
    elif reply.photo: filter_data.update({"type": "photo", "file_id": reply.photo[-1].file_id})
    elif reply.voice: filter_data.update({"type": "voice", "file_id": reply.voice.file_id})
    elif reply.sticker: filter_data.update({"type": "sticker", "file_id": reply.sticker.file_id})
    DB["media_filters"][keyword] = filter_data
    bot.reply_to(message, f"✅ '{keyword}' so'zi uchun avto-javob saqlandi!")

@bot.message_handler(commands=['stop'])
def stop_filter(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split()
    if len(args) > 1:
        keyword = args[1].lower()
        if keyword in DB["media_filters"]:
            del DB["media_filters"][keyword]
            bot.reply_to(message, f"❌ '{keyword}' uchun avto-javob o'chirildi.")

# ==========================================
# 🔄 MONITORING VA AUTOMATIK REAKSIYALAR
# ==========================================

@bot.message_handler(content_types=['new_chat_members'])
def new_member_handler(message):
    for member in message.new_chat_members:
        if member.is_bot and DB["anti_bot"]:
            try: bot.ban_chat_member(message.chat.id, member.id)
            except: pass
            continue
            
        if member.id not in DB["active_members"] and not member.is_bot:
            DB["active_members"].append(member.id)
            
        mention = f"[{member.first_name}](tg://user?id={member.id})"
        w_msg = DB["welcome_msg"].replace("[user]", mention)
        bot.send_message(message.chat.id, w_msg)

        # Odam qo'shish hisobi
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
    
    if not message.from_user.is_bot and uid not in DB["active_members"]:
        DB["active_members"].append(uid)

    # Anti-Link
    if DB["anti_link"] and message.text and ("t.me" in message.text or "http" in message.text or "@" in message.text):
        if not is_admin(message.chat.id, uid):
            try: bot.delete_message(message.chat.id, message.message_id)
            except: pass
            return

    # Avto-Javob Skanerlash
    if message.text and message.text.lower() in DB["media_filters"]:
        f = DB["media_filters"][message.text.lower()]
        if f["type"] == "text": bot.reply_to(message, f["caption"])
        elif f["type"] == "video": bot.send_video(message.chat.id, f["file_id"], caption=f["caption"])
        elif f["type"] == "photo": bot.send_photo(message.chat.id, f["file_id"], caption=f["caption"])
        elif f["type"] == "voice": bot.send_voice(message.chat.id, f["file_id"])
        elif f["type"] == "sticker": bot.send_sticker(message.chat.id, f["file_id"])
        return

    # Odam qo'shish majburiyati
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
    print("Bot muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
