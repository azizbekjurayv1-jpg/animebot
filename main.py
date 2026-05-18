import os
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp

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
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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
        f"Ssilka (Instagram, YouTube, TikTok) yuboring!"
    )

# Ssilkani yuklab olish funksiyasi (Klip yoki MP3)
def download_via_ytdlp(url: str, mode: str, output_path: str):
    ydl_opts = {
        'outtmpl': f'{output_path}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    if mode == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts.update({
            'format': 'best[ext=mp4]/best',
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'Media')
        ext = 'mp3' if mode == 'audio' else info.get('ext', 'mp4')
        return f"{output_path}.{ext}", title

@dp.message()
async def main_handler(message: types.Message):
    user_id = message.from_user.id
    if not await check_subscription(user_id):
        await message.answer("❌ Botdan foydalanish uchun kanal va guruhimizga a'zo bo'ling!", reply_markup=get_subscription_keyboard())
        return

    text = message.text or ""

    if "http://" in text.lower() or "https://" in text.lower():
        msg = await message.answer("⏳ Havola tekshirilmoqda, iltimos kuting...")
        
        # Klip va MP3 uchun tugmalar variantini chiqarish
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📹 Videoni yuklash (Klip)", callback_query_data=f"dl_video_{user_id}")],
            [InlineKeyboardButton(text="🎵 Musiqasini yuklash (MP3)", callback_query_data=f"dl_audio_{user_id}")]
        ])
        
        # Vaqtinchalik ssilkani saqlab turamiz
        global temp_url
        temp_url = text.strip()
        
        await msg.edit_text("👇 Nimaligini tanlang (Klip yoki Ovoz formatida):", reply_markup=kb)
        return

@dp.callback_query()
async def callback_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if callback.data == "check_sub":
        if await check_subscription(user_id):
            try: await callback.message.delete()
            except Exception: pass
            await callback.message.answer("✅ Obuna tasdiqlandi!")
        else:
            await callback.answer("❌ Hali ham hamma kanallarga a'zo bo'lmadingiz!", show_alert=True)
            
    elif callback.data.startswith("dl_"):
        mode = "video" if "video" in callback.data else "audio"
        await callback.message.edit_text("🚀 Serverga yuklab olinmoqda, biroz kuting...")
        
        output_file = os.path.join(DOWNLOAD_DIR, f"{user_id}_{mode}")
        
        try:
            # Ssilkani to'g'ridan-to'g'ri yuklaymiz
            loop = asyncio.get_event_loop()
            file_full_path, title = await loop.run_in_executor(None, download_via_ytdlp, temp_url, mode, output_file)
            
            await callback.message.edit_text("📤 Telegramga jo'natilmoqda...")
            
            if mode == 'audio':
                await callback.message.answer_audio(audio=types.FSInputFile(file_full_path), caption=f"🎵 {title}\n\n🤖 @psjfkspjsl")
            else:
                await callback.message.answer_video(video=types.FSInputFile(file_full_path), caption=f"📹 {title}\n\n🤖 @psjfkspjsl")
                
            await callback.message.delete()
            
            # Ishlatilgan faylni serverdan o'chirib tashlaymiz (joy to'lmasligi uchun)
            if os.path.exists(file_full_path):
                os.remove(file_full_path)
                
        except Exception as e:
            await callback.message.edit_text("⚠️ Kechirasiz, ushbu ssilkadan media yuklab bo'lmadi yoki fayl hajmi juda katta.")
        await callback.answer()

async def main():
    print("🤖 yt-dlp Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
