import os
import json
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ⚠️ SOZLAMALAR
BOT_TOKEN = "8779270757:AAFvfedtmOlXGLsjcbcH89wVlSl4F59XYtg"
ADMIN_ID = 86254345482  # Sizning ID raqamingiz

# 📢 MAJBURIY OBUNA SOZLAMALARI
KANAL_ID = "@psjfkspjsl"       
GURUH_ID = "@jrywnzmch"       
KANAL_LINK = "https://t.me/psjfkspjsl" 
GURUH_LINK = "https://t.me/jrywnzmch" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")

def load_json(file_path, default_value):
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_value, f, ensure_ascii=False, indent=4)
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

users = load_json(USERS_FILE, [])

async def check_subscription(user_id: int) -> bool:
    for chat in [KANAL_ID, GURUH_ID]:
        try:
            member = await bot.get_chat_member(chat_id=chat, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True

def get_subscription_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=KANAL_LINK)],
        [InlineKeyboardButton(text="💬 Guruhga a'zo bo'lish", url=GURUH_LINK)],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_query_data="check_sub")]
    ])

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users:
        users.append(user_id)
        save_json(USERS_FILE, users)
    
    if not await check_subscription(user_id):
        await message.answer("🔥 Assalomu alaykum. Botdan foydalanish uchun kanallarga a'zo bo'ling:", reply_markup=get_subscription_keyboard())
        return

    await message.answer(
        f"👋 Salom, {message.from_user.full_name}!\n"
        f"Musiqa va Video yuklovchi botga xush kelibsiz.\n\n"
        f"Qo'shiq nomini yozing yoki ssilka (Instagram, YouTube, TikTok) yuboring!"
    )

# Eng kuchli va barqaror yuklovchi API (All-in-One)
def fetch_media(url: str):
    api_url = "https://social-download-all-in-one.p.rapidapi.com/v1/social/autolink"
    payload = {"url": url}
    headers = {
        "x-rapidapi-key": "6882fbd72fmsh4b3e8c9c037ce69p137f81jsn7b41dfd16f7f",
        "x-rapidapi-host": "social-download-all-in-one.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=15)
        if response.status == 200:
            data = response.json()
            # API turli xil formatda qaytarishi mumkin, asosiylarini ajratib olamiz
            video_url = None
            audio_url = None
            title = "Yuklangan Media"

            if "medias" in data:
                for media in data["medias"]:
                    if media.get("type") == "video" and not video_url:
                        video_url = media.get("url")
                    if media.get("type") == "audio" and not audio_url:
                        audio_url = media.get("url")
            
            # Agar alohida audio bo'lmasa, videoning o'zini audio o'rnida ham ishlatsa bo'ladi
            if video_url and not audio_url:
                audio_url = video_url
                
            title = data.get("title", "Media Fayl")
            return {"video": video_url, "audio": audio_url, "title": title}
    except Exception:
        pass
    return None

@dp.message()
async def main_handler(message: types.Message):
    user_id = message.from_user.id
    if not await check_subscription(user_id):
        await message.answer("❌ Botdan foydalanish uchun kanal va guruhimizga a'zo bo'ling!", reply_markup=get_subscription_keyboard())
        return

    text = message.text or ""

    # 1. SSILKA KELGANDA
    if text.startswith("http://") or text.startswith("https://"):
        msg = await message.answer("⏳ Havola tekshirilmoqda, iltimos kuting...")
        
        res = fetch_media(text.strip())
        
        if res and (res.get("video") or res.get("audio")):
            kb = InlineKeyboardMarkup(inline_keyboard=[])
            
            # Foydalanuvchiga ssilkani ochuvchi tugmalar ko'rinishida taqdim etamiz
            if res.get("video"):
                kb.inline_keyboard.append([InlineKeyboardButton(text="📹 Videoni yuklash (Klip)", url=res["video"])])
            if res.get("audio"):
                kb.inline_keyboard.append([InlineKeyboardButton(text="🎵 Musiqasini yuklash (MP3)", url=res["audio"])])
                
            await message.answer(
                f"📦 **{res['title']}** tayyor!\n\n"
                f"Yuklab olish uchun quyidagi tugmalardan birini bosing:", 
                reply_markup=kb
            )
            await msg.delete()
        else:
            await msg.edit_text("😔 Kechirasiz, ushbu ssilkadan media topilmadi yoki havola xato. Boshqa ssilka yuborib ko'ring.")
        return

    # 2. ODDIY MATN KELGANDA (NOM BILAN MUSIQA QIDIRISH)
    msg = await message.answer("🔍 Musiqa qidirilmoqda...")
    search_url = f"https://api.deezer.com/search?q={text}&limit=1"
    try:
        response = requests.get(search_url, timeout=10)
        if response.status == 200:
            data = response.json()
            tracks = data.get("data", [])
            if tracks:
                track = tracks[0]
                await message.answer_audio(
                    audio=track['preview'],
                    caption=f"🎵 {track['artist']['name']} - {track['title']}\n\n🤖 @psjfkspjsl"
                )
                await msg.delete()
                return
    except Exception:
        pass
    await msg.edit_text("😔 Kechirasiz, bunday musiqa topilmadi.")

@dp.callback_query()
async def callback_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if callback.data == "check_sub":
        if await check_subscription(user_id):
            try: await callback.message.delete()
            except Exception: pass
            await callback.message.answer("✅ Obuna tasdiqlandi! Endi ssilka yuborishingiz mumkin.")
        else:
            await callback.answer("❌ Hali ham hamma kanallarga a'zo bo'lmadingiz!", show_alert=True)
    await callback.answer()

async def main():
    print("🤖 Professional yuklovchi bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
