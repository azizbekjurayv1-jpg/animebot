import os
import time
import telebot

# 🛑 TOKENINGIZ
BOT_TOKEN = "8300065405:AAF06AxjTEny7zfQxVEFk38Cw3hGCIijxb8"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Ma'lumotlar Bazasi
DB = {
    "temp_usernames": [],   # /setuser bilan vaqtincha keladiganlar
    "saved_usernames": [],  # /save qilingan asosiy ba'za
    "user_adds": {},        # Kim qancha odam qo'shganini hisoblash
    "all_members": set()    # Guruhdagi hamma a'zolarni avtomat yig'ish joyi
}

def is_admin(chat_id, user_id):
    if chat_id == user_id: return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except: return False

def get_admin_instruction_text():
    if not DB["saved_usernames"]:
        return "🤖 Hozircha adminlik tarqatish uchun foydalanuvchilar ro'yxati bo'sh."
        
    user_list = "\n".join([f"👤 {u}" for u in DB["saved_usernames"]])
    return (
        "⚡️ **AVTOMATIK ADMIN OLISH TIZIMI!** ⚡️\n\n"
        "Do'stim, guruhimizda haqiqiy **ADMIN** bo'lishni xohlaysizmi? Buning yo'li juda oson! 👇\n\n"
        "📌 **NIMA QILISH KERAK?**\n"
        "Pastdagi ro'yxatda turgan foydalanuvchi nomlarini (usernamelarni) nusxalab oling va ularni bizning guruhga qo'shing (taklif qiling).\n\n"
        "🎯 **SHART:** Guruhga ro'yxatdagilardan kamida **10 ta odam** qo'shishingiz kerak!\n\n"
        "📜 **QO'SHISHINGIZ KERAK BO'LGAN ODAMLAR:**\n"
        f"{user_list}\n\n"
        "🚀 **Sizga beriladigan ADMINlik huquqlari:**\n"
        "1️⃣ Guruhdagi istalgan xabarlarni o'chirish (`/del`)\n"
        "2️⃣ Qoidabuzarlarni guruhdan haydash yoki cheklash (`/ban`, `/mute`)\n"
        "3️⃣ Guruhga yangi odamlarni taklif qilish va xabarlarni qadash\n\n"
        "✨ **Eslatma:** Aynan 10 ta odam to'lishi bilan bot sizga avtomat adminlik beradi!"
    )

def get_unique_members(chat_id):
    # Dublikatlarsiz a'zolar ro'yxatini shakllantirish
    members_to_tag = list(DB["all_members"])
    try:
        admins = bot.get_chat_administrators(chat_id)
        for admin in admins:
            if not admin.user.is_bot:
                members_to_tag.append(admin.user)
    except: pass
    
    seen_ids = set()
    unique_members = []
    for u in members_to_tag:
        if u.id not in seen_ids:
            seen_ids.add(u.id)
            unique_members.append(u)
    return unique_members

# ==========================================
# 📣 HAMMANI GURUHLAB CHAQIRISH (/call)
# ==========================================

@bot.message_handler(commands=['call'])
def tag_all_call(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    
    unique_members = get_unique_members(message.chat.id)
    if not unique_members:
        bot.reply_to(message, "⚠️ Chaqirish uchun a'zolar hali yig'ilmadi.")
        return

    bot.send_message(message.chat.id, "📢 **Guruh a'zolarini ommaviy chaqirish boshlandi...**")
    
    chunk_size = 5
    text_chunk = ""
    count = 0
    
    for user in unique_members:
        name = user.first_name if user.first_name else "A'zo"
        text_chunk += f"[{name}](tg://user?id={user.id})  "
        count += 1
        
        if count % chunk_size == 0:
            bot.send_message(message.chat.id, f"📣 **Diqqat, hamma qarasin!**\n\n{text_chunk}")
            text_chunk = ""
            time.sleep(1.5)
            
    if text_chunk:
        bot.send_message(message.chat.id, f"📣 **Diqqat, hamma qarasin!**\n\n{text_chunk}")

# ==========================================
# 👤 HAMMANI BITTALAB CHAQIRISH (/callone)
# ==========================================

@bot.message_handler(commands=['callone'])
def tag_one_by_one(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    
    unique_members = get_unique_members(message.chat.id)
    if not unique_members:
        bot.reply_to(message, "⚠️ Chaqirish uchun a'zolar hali yig'ilmadi.")
        return

    bot.send_message(message.chat.id, "🎯 **A'zolarni bittalab chaqirish boshlandi...**")
    
    for user in unique_members:
        name = user.first_name if user.first_name else "A'zo"
        # Har bir odamga alohida xabar yuboriladi
        bot.send_message(message.chat.id, f"🔔 [Do'stim {name}](tg://user?id={user.id}), guruhda sizni kutishyapti!")
        time.sleep(1.2) # Telegram spam blok bermasligi uchun pauza

# ==========================================
# 🛡 GURUH MONITORINGI VA AVTOMAT BAZA
# ==========================================

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video', 'sticker', 'voice'])
def collect_active_users(message):
    if message.chat.type != "private" and not message.from_user.is_bot:
        DB["all_members"].add(message.from_user)
        
    if message.text and message.text.startswith('/odam'):
        text = get_admin_instruction_text()
        bot.reply_to(message, text)

# ==========================================
# 🔄 YANGI ODAM KIRGANDA VA O'SHA 10 TA ODAMNI TEKSHIRISH
# ==========================================

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    adder_id = message.from_user.id
    adder_str = str(adder_id)

    for member in message.new_chat_members:
        if not member.is_bot:
            DB["all_members"].add(member)
            text = get_admin_instruction_text()
            bot.send_message(message.chat.id, f"👋 Salom! Guruhimizga xush kelibsiz!\n\n{text}")
            break

    if is_admin(message.chat.id, adder_id): return

    for member in message.new_chat_members:
        if member.is_bot: continue
        if member.username:
            user_tag = f"@{member.username}"
            if user_tag in DB["saved_usernames"]:
                if adder_str not in DB["user_adds"]:
                    DB["user_adds"][adder_str] = 0
                
                DB["user_adds"][adder_str] += 1
                current_count = DB["user_adds"][adder_str]
                
                if current_count >= 10:
                    try:
                        bot.promote_chat_member(
                            chat_id=message.chat.id,
                            user_id=adder_id,
                            can_change_info=False,
                            can_post_messages=False,
                            can_edit_messages=False,
                            can_delete_messages=True,   # Xabarlarni o'chirish
                            can_invite_users=True,      # Odam taklif qilish
                            can_restrict_members=True,  # Ban/Mute qilish
                            can_pin_messages=True,
                            can_promote_members=False
                        )
                        mention = f"[{message.from_user.first_name}](tg://user?id={adder_id})"
                        bot.send_message(message.chat.id, f"🎉 **URAA! {mention}!**\nSiz ro'yxatdan jami **10 ta odam** qo'shdingiz va shartni bajardingiz!\n\n🛡 Siz endi guruhimizda **3 ta asosiy huquqqa ega rasmiy ADMIN**siz!")
                        DB["user_adds"][adder_str] = 0
                    except Exception as e:
                        print(e)
                else:
                    mention = f"[{message.from_user.first_name}](tg://user?id={adder_id})"
                    bot.send_message(message.chat.id, f"📈 {mention}, hisobingizga odam qo'shildi!\n📊 **Hozirgi natijangiz:** {current_count}/10\n🎯 Admin bo'lish uchun yana {10 - current_count} ta odam qo'shishingiz kerak.")

# ==========================================
# 👑 ADMIN BUYRUQLARI
# ==========================================

@bot.message_handler(commands=['setuser'])
def collect_usernames(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split()[1:]
    if not args:
        bot.reply_to(message, "⚠️ Format: `/setuser @user1 @user2`")
        return
    added_now = []
    for item in args:
        if not item.startswith('@'): item = f"@{item}"
        if item not in DB["temp_usernames"] and item not in DB["saved_usernames"]:
            DB["temp_usernames"].append(item)
            added_now.append(item)
    if added_now:
        bot.reply_to(message, f"📝 Vaqtincha ro'yxatga olindi:\n" + ", ".join(added_now) + "\n\n💾 Saqlash uchun endi `/save` yuboring.")

@bot.message_handler(commands=['save'])
def save_to_database(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not DB["temp_usernames"]:
        bot.reply_to(message, "⚠️ Saqlash uchun vaqtincha ro'yxat bo'sh.")
        return
    DB["saved_usernames"].extend(DB["temp_usernames"])
    DB["temp_usernames"] = []
    bot.reply_to(message, f"💾 Saqlandi! Endi odamlar kamida 10 ta odam qo'shishi kerak.")

@bot.message_handler(commands=['clearusers'])
def clear_usernames(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    DB["saved_usernames"] = []
    DB["temp_usernames"] = []
    bot.reply_to(message, "🗑 Ro'yxatlar butunlay tozalandi.")

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)
    print("Call va CallOne tizimli bot yoqildi...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
