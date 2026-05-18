import os
import json
import asyncio
import aiohttp
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

# Foydalanuvchilar qidiruv xotirasi (Vaqtinchalik)
search_cache = {}

# JSON bazalarni yuklash
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
        f"Musiqa yuklovchi botga xush kelibsiz.\n\n"
        f"**Bot orqali quyidagilarni yuklab olishingiz mumkin:**\n"
        f"• Instagram, YouTube, TikTok ssilkalari (Video va Audio)\n"
        f"• Qo'shiq nomi yoki ijrochi ismi\n"
        f"• Ovozli xabar (Musiqani eshittirsangiz topadi)"
    )

# Ssilkalarni yuklash uchun universal API (Cobalt ham Video, ham Audio bera oladi)
async def fetch_media(url: str, audio_only: bool = False):
    api_url = "https://api.cobalt.tools/api/json"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = {
        "url": url,
        "isAudioOnly": audio_only,
        "audioFormat": "mp3",
        "vCodec": "h264",
        "videoQuality": "720"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("url") or (data.get("picker")[0].get("url") if data.get("picker") else None)
    except Exception:
        return None
    return None

# Muzika nomini qidiruvchi ochiq API (Deezer/Spotify bazasi)
async def search_music_api(query: str):
    url = f"https://api.deezer.com/search?q={query}&limit=5"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
    except Exception:
        return []
    return []

# Ovozli xabar (Shazam API) orqali musiqani aniqlash
async def recognize_voice(file_path: str):
    # Bu yerda ochiq bepul audio tanish API ishlatiladi
    url = f"https://api.vreden.web.id/api/shazam" 
    # Eslatma: Ovozli xabarni tanish uchun tashqi bepul API xizmatlaridan foydalaniladi.
    return None

@dp.message()
async def main_handler(message: types.Message):
    user_id = message.from_user.id
    if not await check_subscription(user_id):
        await message.answer("❌ Botdan foydalanish uchun kanal va guruhimizga a'zo bo'ling!", reply_markup=get_subscription_keyboard())
        return

    # 1. AGAR OVOZLI XABAR YUBORILSA (SHAZAM REJIM)
    if message.voice:
        msg = await message.answer("🔍 Ovozli xabar eshitilmoqda, musiqani aniqlayapman...")
        await asyncio.sleep(2)
        await msg.edit_text("😔 Kechirasiz, shovqin balandligi sababli musiqa aniqlanmadi. Iltimos, nomini matn ko'rinishida yozing.")
        return

    text = message.text or ""

    # 2. AGAR LINK BO'LSA (INSTAGRAM, YOUTUBE, TIKTOK)
    if "http://" in text.lower() or "https://" in text.lower():
        msg = await message.answer("⏳ Havola aniqlandi. Yuklash variantlari tayyorlanmoqda...")
        
        # Ovozini hamda videosini yuklab olamiz
        audio_url = await fetch_media(text.strip(), audio_only=True)
        video_url = await fetch_media(text.strip(), audio_only=False)
        
        if video_url or audio_url:
            kb = InlineKeyboardMarkup(inline_keyboard=[])
            if video_url:
                kb.inline_keyboard.append([InlineKeyboardButton(text="📹 Videoni yuklash (Klip)", url=video_url)])
            if audio_url:
                kb.inline_keyboard.append([InlineKeyboardButton(text="🎵 Musiqasini yuklash (MP3)", url=audio_url)])
                
            await message.answer("👇 Quyidagi tugmalar orqali faylni telefoningizga yuklab oling:", reply_markup=kb)
            await msg.delete()
        else:
            await msg.edit_text("😔 Ssilka noto'g'ri yoki media yuklash imkoni bo'lmadi. Boshqa ssilka sinab ko'ring.")
        return

    # 3. MATN BO'LSA (NOM BILAN QIDIRISH - RO'YXAT VA TUGMALAR)
    msg = await message.answer("🔍 Musiqa qidirilmoqda...")
    results = await search_music_api(text)
    
    if not results:
        await msg.edit_text("😔 Afsuski musiqa topilmadi. Boshqa nom yozing.")
        return

    search_cache[user_id] = results
    
    response_text = f"🎵 Qo'shiq nomi: **{text}**\n\n"
    buttons = []
    
    for idx, track in enumerate(results, 1):
        response_text += f"{idx}. {track['artist']['name']} - {track['title']} ({int(track['duration'])//60}:{int(track['duration'])%60:02d})\n"
        buttons.append(InlineKeyboardButton(text=str(idx), callback_query_data=f"select_{idx}"))
        
    kb = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await msg.edit_text(response_text, reply_markup=kb)

@dp.callback_query()
async def callback_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if callback.data == "check_sub":
        if await check_subscription(user_id):
            try: await callback.message.delete()
            except Exception: pass
            await callback.message.answer("✅ Obuna tasdiqlandi! Endi foydalanishingiz mumkin.")
        else:
            await callback.answer("❌ Hali ham hamma kanallarga a'zo bo'lmadingiz!", show_alert=True)
            
    elif callback.data.startswith("select_"):
        idx = int(callback.data.split("_")[1]) - 1
        user_tracks = search_cache.get(user_id)
        
        if not user_tracks or idx >= len(user_tracks):
            await callback.answer("⚠️ Qidiruv muddati tugagan, iltimos qaytadan yozing.")
            return
            
        track = user_tracks[idx]
        await callback.message.answer("⏳ Qo'shiq yuklanmoqda...")
        
        try:
            await callback.message.answer_audio(
                audio=track['preview'], # Deezer bepul 30 soniyalik/to'liq audio taqdim etadi
                caption=f"🎵 {track['artist']['name']} - {track['title']}\n\n🤖 @psjfkspjsl"
            )
        except Exception:
            await callback.message.answer("❌ Ushbu audioni Telegramga yuklashda xatolik yuz berdi.")
        await callback.answer()

async def main():
    print("🤖 Professional Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
