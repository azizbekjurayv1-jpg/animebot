import os
import json
import urllib.parse
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

BOT_TOKEN = "8779270757:AAFvfedtmOlXGLsjcbcH89wVlSl4F59XYtg"
ADMIN_ID = 86254345482

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

    await message.answer(f"👋 Salom, {message.from_user.full_name}!\nQo'shiq nomini yozing yoki ssilka yuboring.")

# 🎵 UNIVERSAL YOUTUBE VA SILLKA BILAN ISHLOVCHI KAFOLATLI API
async def fetch_youtube_media(query: str):
    encoded_query = urllib.parse.quote(query)
    api_url = f"https://api.vreden.web.id/api/ytdl?url={encoded_query}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == 200 and "result" in data:
                        res = data["result"]
                        return {
                            "audio": res.get("audio") or res.get("mp3") or res.get("url"),
                            "video": res.get("video"),
                            "title": res.get("title", "Musiqa")
                        }
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
    msg = await message.answer("🔍 Qidirilmoqda, iltimos kuting...")

    # Ssilka bo'lsa ham, qo'shiq nomi bo'lsa ham to'g'ridan-to'g'ri universal tizimga yuboriladi
    media = await fetch_youtube_media(text.strip())

    if media and (media.get("audio") or media.get("video")):
        try:
            # Faylni URL manzilidan to'g'ridan-to'g'ri foydalanuvchiga yuborish
            if media.get("audio"):
                await message.answer_audio(audio=media["audio"], caption=f"🎵 {media['title']}\n\n🤖 @psjfkspjsl")
                await msg.delete()
                return
            elif media.get("video"):
                await message.answer_video(video=media["video"], caption=f"📹 {media['title']}\n\n🤖 @psjfkspjsl")
                await msg.delete()
                return
        except Exception:
            # Agar fayl hajmi juda katta bo'lsa, yuklab olish tugmasini ko'rsatadi
            kb = InlineKeyboardMarkup(inline_keyboard=[])
            if media.get("audio"):
                kb.inline_keyboard.append([InlineKeyboardButton(text="🎵 Musiqani yuklab olish", url=media["audio"])])
            if media.get("video"):
                kb.inline_keyboard.append([InlineKeyboardButton(text="📹 Videoni yuklab olish", url=media["video"])])
            
            await msg.edit_text(f"📦 **{media['title']}** topildi!\nTelegram yuklash cheklovi sababli quyidagi tugma orqali yuklab oling:", reply_markup=kb)
            return
    else:
        await msg.edit_text("😔 Kechirasiz, hech narsa topilmadi. Qo'shiq nomini boshqacha yozib ko'ring yoki havola yuboring.")

@dp.callback_query()
async def callback_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if callback.data == "check_sub":
        if await check_subscription(user_id):
            try: await callback.message.delete()
            except Exception: pass
            await callback.message.answer("✅ Obuna tasdiqlandi!")
        else:
            await callback.answer("❌ Obuna bo'ling!", show_alert=True)
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
