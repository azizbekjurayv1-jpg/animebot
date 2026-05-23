import os
import time
import telebot

# 🛑 TOKENINGIZ
BOT_TOKEN = "8300065405:AAF06AxjTEny7zfQxVEFk38Cw3hGCIijxb8"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Ma'lumotlar Bazasi
DB = {
    "temp_usernames": [],  # /odam bilan vaqtincha kelganlar
    "saved_usernames": [], # /save qilingan asosiy ba'za
    "allowed_users": []    # Guruhda yozishga ruxsat berilganlar ro'yxati
}

def is_admin(chat_id, user_id):
    if chat_id == user_id: return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except: return False

# ==========================================
# 🤖 YANGI ODAM KIRGANDA TUGMALI TARIF CHIQARISH
# ==========================================

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    for member in message.new_chat_members:
        if member.is_bot: continue
        
        # Yangi foydalanuvchiga tugmali xabar yuborish
        mention = f"[{member.first_name}](tg://user?id={member.id})"
        welcome_text = (
            f"👋 **Salom {mention}! Guruhimizga xush kelibsiz!**\n\n"
            "🔒 Hozircha siz guruhda xabar yoza olmaysiz.\n"
            "🔓 Guruhda yozish huquqini faollashtirish uchun pastdagi tariflardan birini tanlang va foydalanuvchi (username) oling:"
        )
        
        # Tugmalarni sozlash
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        btn1 = telebot.types.InlineKeyboardButton(text="💎 VIP Tarif (Username olish & Aktivlash)", callback_data=f"activate_{member.id}")
        btn2 = telebot.types.InlineKeyboardButton(text="⚡️ Oddiy Tarif (Profilni ochish)", callback_data=f"activate_{member.id}")
        markup.add(btn1, btn2)
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# ==========================================
# 🔄 TUGMA BOSILGANDA USERNAMENI BERISH VA RUXSAT OCHISH
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("activate_"))
def process_activation(call):
    # Tugmani bosgan odamning ID sini tekshiramiz
    target_user_id = int(call.data.split("_")[1])
    clicker_id = call.from_user.id
    
    # Faqat yangi kirgan odam o'z tugmasini bosa oladi
    if clicker_id != target_user_id:
        bot.answer_callback_query(call.id, text="⚠️ Bu tarif tugmasi siz uchun emas!", show_alert=True)
        return
        
    # Uni ruxsat etilganlar ro'yxatiga qo'shamiz
    if clicker_id not in DB["allowed_users"]:
        DB["allowed_users"].append(clicker_id)
        
    # Ba'zadagi usernamelarni tayyorlash
    if DB["saved_usernames"]:
        user_list = "\n".join([f"• {u}" for u in DB["saved_usernames"]])
        response_text = (
            f"✅ **Tabriklayman! Tarif muvaffaqiyatli tanlandi.**\n\n"
            f"🎁 Sizga taqdim etilgan maxsus foydalanuvchilar (usernamelar):\n{user_list}\n\n"
            f"🔓 Guruhda yozish huquqingiz ochildi. Bemalol yozavering!"
        )
    else:
        response_text = "✅ **Tarif tanlandi!** Guruhda yozish huquqingiz ochildi. Bemalol yozavering! (Hozircha ba'zada username yo'q)"
        
    # Xabarni yangilab foydalanuvchiga ruxsat berilganini ko'rsatamiz
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=response_text)
    bot.answer_callback_query(call.id, text="🚀 Guruh faollashtirildi!")

# ==========================================
# 👑 ADMIN BUYRUQLARI (/odam VA /save)
# ==========================================

@bot.message_handler(commands=['odam'])
def collect_usernames(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    args = message.text.split()[1:]
    if not args:
        bot.reply_to(message, "⚠️ Format: `/odam @user1 @user2`")
        return
        
    added_now = []
    for item in args:
        if not item.startswith('@'): item = f"@{item}"
        if item not in DB["temp_usernames"] and item not in DB["saved_usernames"]:
            DB["temp_usernames"].append(item)
            added_now.append(item)
            
    if added_now:
        bot.reply_to(message, f"📝 Vaqtincha qo'shildi:\n" + ", ".join(added_now) + "\n\n💾 Saqlash uchun `/save` deb yozing.")

@bot.message_handler(commands=['save'])
def save_to_database(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    if not DB["temp_usernames"]:
        bot.reply_to(message, "⚠️ Saqlash uchun vaqtincha ro'yxat bo'sh.")
        return
    DB["saved_usernames"].extend(DB["temp_usernames"])
    DB["temp_usernames"] = []
    bot.reply_to(message, f"💾 Saqlandi! Yangi usernamelar yangi a'zolar tarif tanlaganda ularga yuboriladi.")

@bot.message_handler(commands=['clearusers'])
def clear_usernames(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    DB["saved_usernames"] = []
    DB["temp_usernames"] = []
    bot.reply_to(message, "🗑 Barcha saqlangan foydalanuvchilar o'chirildi.")

# ==========================================
# 🛡 GURUH MONITORINGI (YANGILARNI BLOKLASH)
# ==========================================

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video', 'voice', 'sticker'])
def check_group_access(message):
    if message.chat.type == "private": return
    uid = message.from_user.id
    
    # Agar admin bo'lsa, xabarga tegmaymiz
    if is_admin(message.chat.id, uid): return
    
    # Agar tarif tanlab, ro'yxatdan o'tmagan bo'lsa xabarini o'chiramiz
    if uid not in DB["allowed_users"]:
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except: pass

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)
    print("Tarifli Kirish Boti yoqildi...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
