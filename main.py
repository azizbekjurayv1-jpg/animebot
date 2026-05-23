import os
import time
import json
import telebot

# 🛑 TOKENINGIZ
BOT_TOKEN = "8300065405:AAF06AxjTEny7zfQxVEFk38Cw3hGCIijxb8"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# 🎯 SHU YERGA ODAM QO'SHISHI KERAK BO'LGAN USERNAMELARNI YOZING!
TARGET_USERNAMES = [
    "@YUSE0L",
]

DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["all_members"] = set(data.get("all_members", []))
                return data
        except:
            pass
    return {"user_adds": {}, "all_members": set()}

def save_db():
    try:
        data_to_save = {
            "user_adds": DB["user_adds"],
            "all_members": list(DB["all_members"])
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"JSONga saqlashda xato: {e}")

DB = load_db()

def get_admin_instruction_text():
    user_list = "\n".join([f"👤 {u}" for u in TARGET_USERNAMES])
    return (
        "⚡️ **AVTOMATIK ADMIN OLISH TIZIMI!** ⚡️\n\n"
        "Do'stim, guruhimizda haqiqiy **ADMIN** bo'lishni xohlaysizmi? Buning yo'li juda oson! 👇\n\n"
        "📌 **NIMA QILISH KERAK?**\n"
        "Pastdagi ro'yxatda turgan foydalanuvchi nomlarini nusxalab oling va ularni guruhga qo'shing.\n\n"
        "🎯 **SHART:** Ro'yxatdagilardan kamida **10 ta odam** qo'shishingiz kerak!\n\n"
        "📜 **QO'SHISHINGIZ KERAK BO'LGAN ODAMLAR:**\n"
        f"{user_list}\n\n"
        "🚀 **Sizga beriladigan ADMINlik huquqlari:**\n"
        "1️⃣ Xabarlarni o'chirish (`/del`)\n"
        "2️⃣ Qoidabuzarlarni bloklash (`/ban`, `/mute`)\n"
        "3️⃣ Yangi odamlarni taklif qilish va xabarlarni qadash\n\n"
        "✨ **Eslatma:** Aynan 10 ta odam to'lishi bilan bot sizga avtomat adminlik beradi!"
    )

@bot.message_handler(commands=['start'])
def send_start(message):
    bot.reply_to(message, "🚀 Bot faol va JSON bazasiga ulandi! Guruhda bemalol /call yoki /callone ishlating!")

@bot.message_handler(commands=['odam'])
def show_odam(message):
    bot.reply_to(message, get_admin_instruction_text())

@bot.message_handler(commands=['call'])
def tag_all_call(message):
    unique_users = []
    seen_ids = set()
    
    try:
        admins = bot.get_chat_administrators(message.chat.id)
        for a in admins:
            if not a.user.is_bot and a.user.id not in seen_ids:
                seen_ids.add(a.user.id)
                unique_users.append(a.user)
    except: pass

    for member_id in DB["all_members"]:
        if member_id not in seen_ids:
            seen_ids.add(member_id)
            try:
                chat_member = bot.get_chat_member(message.chat.id, member_id)
                if not chat_member.user.is_bot:
                    unique_users.append(chat_member.user)
            except: pass

    if not unique_users:
        bot.reply_to(message, "⚠️ Chaqirish uchun a'zolar ro'yxati hozircha bo'sh.")
        return

    bot.send_message(message.chat.id, "📢 **Ommaviy chaqiruv boshlandi...**")
    chunk_size = 5
    text_chunk = ""
    for i, user in enumerate(unique_users, 1):
        name = user.first_name if user.first_name else "A'zo"
        text_chunk += f"[{name}](tg://user?id={user.id})  "
        if i % chunk_size == 0 or i == len(unique_users):
            bot.send_message(message.chat.id, f"📣 **Hamma qarasin:**\n\n{text_chunk}")
            text_chunk = ""
            time.sleep(1.5)

@bot.message_handler(commands=['callone'])
def tag_call_one(message):
    unique_users = []
    seen_ids = set()
    
    for member_id in DB["all_members"]:
        if member_id not in seen_ids:
            seen_ids.add(member_id)
            try:
                chat_member = bot.get_chat_member(message.chat.id, member_id)
                if not chat_member.user.is_bot:
                    unique_users.append(chat_member.user)
            except: pass

    if not unique_users:
        bot.reply_to(message, "⚠️ A'zolar topilmadi.")
        return

    bot.send_message(message.chat.id, "🎯 **Bittalab chaqiruv boshlandi...**")
    for user in unique_users:
        name = user.first_name if user.first_name else "A'zo"
        bot.send_message(message.chat.id, f"🔔 [Do'stim {name}](tg://user?id={user.id}), kiring!")
        time.sleep(1.2)

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video', 'sticker', 'voice'])
def collect_active_users(message):
    if message.chat.type != "private" and not message.from_user.is_bot:
        if message.from_user.id not in DB["all_members"]:
            DB["all_members"].add(message.from_user.id)
            save_db()

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    adder_id = message.from_user.id
    adder_str = str(adder_id)

    for member in message.new_chat_members:
        if not member.is_bot:
            DB["all_members"].add(member.id)
            save_db()
            bot.send_message(message.chat.id, f"👋 Salom! Guruhimizga xush kelibsiz!\n\n{get_admin_instruction_text()}")
            break

    try:
        chat_member = bot.get_chat_member(message.chat.id, adder_id)
        if chat_member.status in ['creator', 'administrator']: return
    except: pass

    for member in message.new_chat_members:
        if member.is_bot: continue
        if member.username:
            user_tag = f"@{member.username}"
            
            if user_tag in TARGET_USERNAMES:
                if adder_str not in DB["user_adds"]: DB["user_adds"][adder_str] = 0
                DB["user_adds"][adder_str] += 1
                current_count = DB["user_adds"][adder_str]
                save_db()
                
                if current_count >= 10:
                    try:
                        # 🛠 XORALIK TUZATILDI: Ortiqcha cheklovlar olib tashlandi, faqat kerakli huquqlar beriladi!
                        bot.promote_chat_member(
                            chat_id=message.chat.id, 
                            user_id=adder_id,
                            can_delete_messages=True, 
                            can_invite_users=True, 
                            can_restrict_members=True,
                            can_pin_messages=True
                        )
                        mention = f"[{message.from_user.first_name}](tg://user?id={adder_id})"
                        bot.send_message(message.chat.id, f"🎉 **URAA! {mention}!**\nSiz ro'yxatdan jami **10 ta odam** qo'shdingiz va shartni bajardingiz!\n\n🛡 Siz endi guruhimizda **3 ta asosiy huquqqa ega rasmiy ADMIN**siz!")
                        DB["user_adds"][adder_str] = 0
                        save_db()
                    except Exception as e:
                        print(f"Admin qilishda xato: {e}")
                else:
                    mention = f"[{message.from_user.first_name}](tg://user?id={adder_id})"
                    bot.send_message(message.chat.id, f"📈 {mention}, hisobingizga odam qo'shildi!\n📊 **Hozirgi natijangiz:** {current_count}/10\n🎯 Admin bo'lish uchun yana {10 - current_count} ta odam qo'shishingiz kerak.")

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)
    print("Yangi qo'shilganlar yozish muammosi tuzatilgan bot yoqildi...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
