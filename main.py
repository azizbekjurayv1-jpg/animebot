import os
import time
import json
import telebot

# 🛑 TOKENINGIZ
BOT_TOKEN = "8300065405:AAF06AxjTEny7zfQxVEFk38Cw3hGCIijxb8"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# 🎯 GURUHGA NAVBAT BILAN QO'SHILISHI KERAK BO'LGAN USERNAMELAR
TOTAL_USERNAMES = [
    "@YUSE0L",
    "@Loves5743",
    "@Dilsora_Dil",
    "@daniyarovna_o1",
    "@Seyaxon"
]

DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "active_list" not in data:
                    data["active_list"] = TOTAL_USERNAMES.copy()
                data["all_members"] = set(data.get("all_members", []))
                if "warns" not in data:
                    data["warns"] = {}
                return data
        except:
            pass
    return {"user_adds": {}, "active_list": TOTAL_USERNAMES.copy(), "all_members": set(), "assigned": {}, "warns": {}}

def save_db():
    try:
        data_to_save = {
            "user_adds": DB["user_adds"],
            "active_list": DB["active_list"],
            "assigned": DB["assigned"],
            "all_members": list(DB["all_members"]),
            "warns": DB.get("warns", {})
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"JSONga saqlashda xato: {e}")

DB = load_db()

# Admin ekanligini tekshirish funksiyasi
def is_user_admin(chat_id, user_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        return any(a.user.id == user_id for a in admins)
    except:
        return False

# Foydalanuvchi /odam buyrug'ini bossa, unga yangi user biriktirish
def get_task_text(user_id):
    user_str = str(user_id)
    if user_str in DB["assigned"]:
        assigned_user = DB["assigned"][user_str]
    else:
        if not DB["active_list"]:
            return "🎉 Hozircha hamma vazifalar bajarib bo'lindi! Ro'yxatda yangi userlar qolmadi."
        assigned_user = DB["active_list"][0]
        DB["assigned"][user_str] = assigned_user
        save_db()

    return (
        "⚡️ **AVTOMATIK ADMIN OLISH TIZIMI!** \n\n"
        "🛡 Guruhimizda admin bo'lishni xohlaysizmi? Unda pastdagi usernameni nusxalab oling va uni guruhga qo'shing:\n"
        f"👉 **{assigned_user}**\n\n"
        "🎯 **SHART:** Adminlik huquqini qo'lga kiritish uchun jami **10 ta** mana shunday sizga berilgan odamlarni guruhga qo'shishingiz kerak!\n"
        "✨ Odam qo'shilganidan keyin bot sizga yangi user taqdim etadi."
    )

# 📌 START & HELP BUYRUKLARI
@bot.message_handler(commands=['start', 'help'])
def send_start(message):
    help_text = (
        "🚀 **Bot guruhni boshqarish rejimida faol!**\n\n"
        "📊 **Foydalanuvchilar uchun buyruqlar:**\n"
        "🔹 `/odam` - Admin bo'lish uchun topshiriq olish\n"
        "🔹 `/rules` - Guruh qoidalari\n"
        "🔹 `/me` - Profilingiz haqida ma'lumot\n\n"
        "📢 **Chaqiruv buyruqlari:**\n"
        "🔹 `/call` - Guruh a'zolarini ommaviy chaqirish\n\n"
        "🛡 **Adminlar uchun Group Help buyruqlari:**\n"
        "🔥 `/admin` - Reply qilingan foydalanuvchini admin qilish!\n"
        "🔸 `/ban` - Guruhdan butunlay bloklash (reply qilib)\n"
        "🔸 `/unban` - Blokdan ochish\n"
        "🔸 `/mute` - Yozishni cheklash (reply qilib)\n"
        "🔸 `/unmute` - Cheklovni olish (reply qilib)\n"
        "🔸 `/kick` - Guruhdan chiqarib yuborish (reply qilib)\n"
        "🔸 `/warn` - Ogohlantirish berish (reply qilib)\n"
        "🔸 `/unwarn` - Ogohlantirishni olish (reply qilib)\n"
        "🔸 `/pin` - Xabarni qadash (reply qilib)\n"
        "🔸 `/unpin` - Xabarni qaddan olish"
    )
    bot.reply_to(message, help_text)

# 🛠 JAYAN MANA SHU SIZ AYTGAN REPLY QILIB ADMIN BERISH FUNKSIYASI
@bot.message_handler(commands=['admin'])
def give_admin_via_reply(message):
    # Buyruq bergan odam adminmi yoki yo'q tekshiramiz
    if not is_user_admin(message.chat.id, message.from_user.id):
        return
    
    # Reply qilingan xabar bormi?
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Kimnidir admin qilmoqchi bo'lsangiz, uning xabariga javob (reply) qilib `/admin` deb yozing!")
        return
    
    target_user = message.reply_to_message.from_user
    
    if target_user.is_bot:
        bot.reply_to(message, "⚠️ Botlarni admin qilib bo'lmaydi!")
        return

    try:
        # Unga asosiy adminlik huquqlarini taqdim etamiz
        bot.promote_chat_member(
            chat_id=message.chat.id, 
            user_id=target_user.id,
            can_delete_messages=True, 
            can_invite_users=True, 
            can_restrict_members=True, 
            can_pin_messages=True
        )
        mention = f"[{target_user.first_name}](tg://user?id={target_user.id})"
        bot.send_message(message.chat.id, f"🛡 **Muvaffaqiyatli!**\n{mention} admin tomonidan guruhimizga **ADMIN** qilib tayinlandi! 🎉")
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: Botda kimgadir adminlik berish uchun huquq yetarli emas! (Botni o'zi ham guruhda to'liq admin bo'lishi kerak).")

@bot.message_handler(commands=['odam'])
def show_odam(message):
    bot.reply_to(message, get_task_text(message.from_user.id))

@bot.message_handler(commands=['rules'])
def show_rules(message):
    bot.reply_to(message, "📜 **Guruh qoidalari:**\n\n1. Sokinlikni saqlang, reklama tarqatmang.\n2. Haqorat va so'kinganlar darhol guruhdan haydaladi.\n3. Admin bo'lish uchun `/odam` buyrug'ini ishlating.")

@bot.message_handler(commands=['me'])
def show_me(message):
    u_id = message.from_user.id
    adds = DB["user_adds"].get(str(u_id), 0)
    warn_count = DB.get("warns", {}).get(str(u_id), 0)
    bot.reply_to(message, f"👤 **Sizning profilingiz:**\n\n🆔 ID: `{u_id}`\n👤 Ism: {message.from_user.first_name}\n📈 Qo'shgan odamingiz: {adds}/10\n⚠️ Ogohlantirishlaringiz: {warn_count}/3")

# 📢 OMMAVIY CHAQIRUV
@bot.message_handler(commands=['call'])
def tag_all_call(message):
    unique_users = []
    seen_ids = set()
    try:
        admins = bot.get_chat_administrators(message.chat.id)
        for a in admins:
            if not a.user.is_bot:
                seen_ids.add(a.user.id)
                unique_users.append(a.user)
    except: pass

    for member_id in DB["all_members"]:
        if member_id not in seen_ids:
            seen_ids.add(member_id)
            try:
                chat_member = bot.get_chat_member(message.chat.id, member_id)
                if not chat_member.user.is_bot: unique_users.append(chat_member.user)
            except: pass

    if not unique_users:
        bot.reply_to(message, "⚠️ A'zolar ro'yxati bo'sh.")
        return

    bot.send_message(message.chat.id, "📢 **Chaqiruv boshlandi...**")
    chunk_size = 5
    text_chunk = ""
    for i, user in enumerate(unique_users, 1):
        name = user.first_name if user.first_name else "A'zo"
        text_chunk += f"[{name}](tg://user?id={user.id})  "
        if i % chunk_size == 0 or i == len(unique_users):
            bot.send_message(message.chat.id, f"📣 **Hamma qarasin:**\n\n{text_chunk}")
            text_chunk = ""
            time.sleep(1.5)

# 🛡 GROUP HELP MODERATSIYA BUYRUKLARI
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if not is_user_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Bu buyruqni biror xabarga javob (reply) qilib yozing!")
        return
    try:
        bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        bot.reply_to(message, f"🛑 Foydalanuvchi guruhdan butunlay ban qilindi!")
    except: bot.reply_to(message, "❌ Xatolik: Botda adminlik huquqi kam yoki foydalanuvchi admin.")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if not is_user_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id, only_if_banned=True)
        bot.reply_to(message, "✅ Foydalanuvchi blokdan chiqarildi!")
    except: pass

@bot.message_handler(commands=['mute'])
def mute_user(message):
    if not is_user_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
                                 can_send_messages=False, can_send_media_messages=False, 
                                 can_send_polls=False, can_send_other_messages=False)
        bot.reply_to(message, "🤫 Foydalanuvchi yozishdan cheklandi (Mute).")
    except: pass

@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    if not is_user_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
                                 can_send_messages=True, can_send_media_messages=True, 
                                 can_send_polls=True, can_send_other_messages=True)
        bot.reply_to(message, "🔊 Foydalanuvchidan cheklov olindi, endi yozishi mumkin.")
    except: pass

@bot.message_handler(commands=['kick'])
def kick_user(message):
    if not is_user_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        bot.reply_to(message, "chaqaloq guruhdan haydaldi (Kick).")
    except: pass

@bot.message_handler(commands=['warn'])
def warn_user(message):
    if not is_user_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    t_id = str(message.reply_to_message.from_user.id)
    if "warns" not in DB: DB["warns"] = {}
    DB["warns"][t_id] = DB["warns"].get(t_id, 0) + 1
    count = DB["warns"][t_id]
    save_db()
    
    if count >= 3:
        try:
            bot.ban_chat_member(message.chat.id, int(t_id))
            bot.reply_to(message, "⚠️ Ogohlantirishlar soni 3 taga yetdi. Foydalanuvchi BAN qilindi!")
            DB["warns"][t_id] = 0
            save_db()
        except: pass
    else:
        bot.reply_to(message, f"⚠️ Ogohlantirish berildi! Jami ogohlantirishlar: {count}/3")

@bot.message_handler(commands=['unwarn'])
def unwarn_user(message):
    if not is_user_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    t_id = str(message.reply_to_message.from_user.id)
    if "warns" in DB and t_id in DB["warns"] and DB["warns"][t_id] > 0:
        DB["warns"][t_id] -= 1
        save_db()
        bot.reply_to(message, f"✅ Bitta ogohlantirish olib tashlandi. Hozirgi holat: {DB['warns'][t_id]}/3")
    else:
        bot.reply_to(message, "🔄 Foydalanuvchida ogohlantirishlar yo'q.")

@bot.message_handler(commands=['pin'])
def pin_msg(message):
    if not is_user_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        bot.reply_to(message, "📌 Xabar yuqoriga qadaldi.")
    except: pass

@bot.message_handler(commands=['unpin'])
def unpin_msg(message):
    if not is_user_admin(message.chat.id, message.from_user.id): return
    try:
        bot.unpin_chat_message(message.chat.id)
        bot.reply_to(message, "🔓 Xabar qaddan olindi.")
    except: pass

# 🔄 BAZA VA YANGI KELGANLAR TIZIMI
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

    for member in message.new_chat_members:
        if member.is_bot: continue
        if member.username:
            user_tag = f"@{member.username}"
            if user_tag in DB["active_list"]:
                DB["active_list"].remove(user_tag)
                for key, val in list(DB["assigned"].items()):
                    if val == user_tag: del DB["assigned"][key]
                
                if adder_str not in DB["user_adds"]: DB["user_adds"][adder_str] = 0
                DB["user_adds"][adder_str] += 1
                current_count = DB["user_adds"][adder_str]
                save_db()
                
                mention = f"[{message.from_user.first_name}](tg://user?id={adder_id})"
                if current_count >= 10:
                    try:
                        bot.promote_chat_member(
                            chat_id=message.chat.id, user_id=adder_id,
                            can_delete_messages=True, can_invite_users=True, 
                            can_restrict_members=True, can_pin_messages=True
                        )
                        bot.send_message(message.chat.id, f"🎉 **URAA! {mention}!**\nSiz 10 ta odam qo'shib shartni bajardingiz va ADMIN bo'ldingiz!")
                        DB["user_adds"][adder_str] = 0
                        save_db()
                    except: pass
                else:
                    bot.send_message(message.chat.id, f"📈 {mention}, vazifa miqyosida {user_tag} guruhga qo'shildi!\n📊 **Sizning ballingiz:** {current_count}/10\n🔄 Keyingi user nomini olish uchun `/odam` buyrug'ini bosing.")

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)
    print("Reply admin funksiyali bot yoqildi...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
