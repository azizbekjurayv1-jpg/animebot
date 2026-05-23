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
    "user_adds": {}         # Kim qancha odam qo'shganini hisoblash (User ID: soni)
}

def is_admin(chat_id, user_id):
    if chat_id == user_id: return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except: return False

def get_admin_instruction_text(current_user_adds=0):
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

# ==========================================
# 👥 ODDIY FOYDALANUVCHILAR UCHUN BUYRUQ (/odam)
# ==========================================

@bot.message_handler(commands=['odam'])
def show_usernames_list(message):
    text = get_admin_instruction_text()
    bot.reply_to(message, text)

# ==========================================
# 🔄 YANGI ODAM KIRGANDA VA QO'SHILGANDA
# ==========================================

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    adder_id = message.from_user.id
    adder_str = str(adder_id)

    # 1. YANGI ODAM KIRGANDA SHARTNI KO'RSATISH
    for member in message.new_chat_members:
        if not member.is_bot:
            text = get_admin_instruction_text()
            bot.send_message(message.chat.id, f"👋 Salom! Guruhimizga xush kelibsiz!\n\n{text}")
            break

    # 2. ODAM QO'SHGANDA HISOB-KITOB QILISH
    if is_admin(message.chat.id, adder_id): return

    for member in message.new_chat_members:
        if member.is_bot: continue
        
        if member.username:
            user_tag = f"@{member.username}"
            # Agar qo'shilgan odam bizning ro'yxatda bo'lsa
            if user_tag in DB["saved_usernames"]:
                
                if adder_str not in DB["user_adds"]:
                    DB["user_adds"][adder_str] = 0
                
                DB["user_adds"][adder_str] += 1
                current_count = DB["user_adds"][adder_str]
                
                # 10 TA BO'LGANINI TEKSHIRISH
                if current_count >= 10:
                    try:
                        bot.promote_chat_member(
                            chat_id=message.chat.id,
                            user_id=adder_id,
                            can_change_info=False,
                            can_post_messages=False,
                            can_edit_messages=False,
                            can_delete_messages=True,    # 1. Xabarlarni o'chirish
                            can_invite_users=True,       # 2. Odam taklif qilish
                            can_restrict_members=True,   # 3. Ban/Mute qilish
                            can_pin_messages=True,
                            can_promote_members=False
                        )
                        
                        mention = f"[{message.from_user.first_name}](tg://user?id={adder_id})"
                        bot.send_message(
                            message.chat.id, 
                            f"🎉 **URAA! DAXSHAT {mention}!**\n"
                            f"Siz ro'yxatdan jami **10 ta odam** qo'shdingiz va shartni bajardingiz!\n\n"
                            f"🛡 Siz endi guruhimizda **3 ta asosiy huquqqa ega rasmiy ADMIN**siz!"
                        )
                        DB["user_adds"][adder_str] = 0 # Hisobni nolga qaytaramiz
                    except Exception as e:
                        print(f"Admin qilishda xato: {e}")
                else:
                    # 10 taga yetmagan bo'lsa, nechta qo'shganini aytib turadi
                    mention = f"[{message.from_user.first_name}](tg://user?id={adder_id})"
                    bot.send_message(
                        message.chat.id,
                        f"📈 {mention}, hisobingizga yana bitta odam qo'shildi!\n"
                        f"📊 **Hozirgi natijangiz:** {current_count}/10\n"
                        f"🎯 Admin bo'lish uchun yana {10 - current_count} ta odam qo'shishingiz kerak."
                    )

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
    print("10 talik Avto-Admin boti yoqildi...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
