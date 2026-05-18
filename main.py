i  import os
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ⚠️ SOZLAMALAR
BOT_TOKEN = "8779270757:AAFvfedtmOlXGLsjcbcH89wVlSl4F59XYtg"
ADMIN_ID = 86254345482  # Sizning ID raqamingiz

# 📢 MAJBURIY OBUNA SOZLAMALARI (Bot kanalda va guruhda ADMIN bo'lishi shart!)
KANAL_ID = "@psjfkspjsl"       
GURUH_ID = "@jrywnzmch"       
KANAL_LINK = "https://t.me/psjfkspjsl" 
GURUH_LINK = "https://t.me/jrywnzmch" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BAZA_FILE = os.path.join(BASE_DIR, "baza.json")
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

baza = load_json(BAZA_FILE, {})
users = load_json(USERS_FILE, [])

# Obunani tekshirish funksiyasi
async def check_subscription(user_id: int) -> bool:
    # Kanalni tekshirish
    try:
        member = await bot.get_chat_member(chat_id=KANAL_ID, user_id=user_id)
        if member.status in ["left", "kicked"]:
            return False
    except Exception:
        print(f"Xatolik: Bot {KANAL_ID} kanalida admin emas yoki kanal topilmadi.")
        return False

    # Guruhni tekshirish
    try:
        member_group = await bot.get_chat_member(chat_id=GURUH_ID, user_id=user_id)
        if member_group.status in ["left", "kicked"]:
            return False
    except Exception:
        print(f"Xatolik: Bot {GURUH_ID} guruhida admin emas yoki guruh topilmadi.")
        return False

    return True

# Obuna bo'lish tugmalari
def get_subscription_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=KANAL_LINK)],
        [InlineKeyboardButton(text="💬 Guruhga a'zo bo'lish", url=GURUH_LINK)],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_query_data="check_sub")]
    ])

# /start komandasi
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users:
        users.append(user_id)
        save_json(USERS_FILE, users)
    
    if not await check_subscription(user_id):
        await message.answer(
            "❌ Botdan foydalanish uchun quyidagi kanal va guruhimizga a'zo bo'lishingiz majburiy!",
            reply_markup=get_subscription_keyboard()
        )
        return

    await message.answer(
        f"👋 Salom, {message.from_user.full_name}!\nMusiqa nomini yoki ijrochini yozib yuboring."
    )

# /panel komandasi (Admin)
@dp.message(Command("panel"))
async def panel_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎵 Musiqa qo'shish", callback_query_data="add_music")],
            [InlineKeyboardButton(text="📢 Reklama jo'natish", callback_query_data="send_ad")],
            [InlineKeyboardButton(text="📊 Statistika", callback_query_data="stat")]
        ])
        await message.answer("🔧 Admin panelga xush kelibsiz:", reply_markup=kb)

# Callback handler
@dp.callback_query()
async def callback_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if callback.data == "check_sub":
        if await check_subscription(user_id):
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer("✅ Rahmat! Obuna tasdiqlandi. Endi musiqalarni qidirishingiz mumkin.")
        else:
            await callback.answer("❌ Hali ham hamma kanallarga a'zo bo'lmadingiz!", show_alert=True)
            
    elif callback.data == "stat" and user_id == ADMIN_ID:
        await callback.message.answer(f"📊 Bot foydalanuvchilari soni: {len(users)} ta")
        await callback.answer()
        
    elif callback.data == "add_music" and user_id == ADMIN_ID:
        await callback.message.answer("📥 Musiqani menga Audio formatida yuboring (fayl emas, oddiy muzika qilib).")
        await callback.answer()
        
    elif callback.data == "send_ad" and user_id == ADMIN_ID:
        await callback.message.answer("📝 Reklama xabaringizni (matn, rasm yoki video) menga shunchaki yuboring (forward qilmang).")
        await callback.answer()

# Admin reklama yuborganda
@dp.message(lambda msg: msg.from_user.id == ADMIN_ID and (msg.text and msg.text.startswith('/') is False or msg.photo or msg.video or msg.animation))
async def send_advertisement(message: types.Message):
    success_count = 0
    await message.answer("🚀 Reklama tarqatilmoqda, kuting...")
    
    for u_id in users:
        try:
            await bot.copy_message(chat_id=u_id, from_chat_id=message.chat.id, message_id=message.message_id)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            continue

    await message.answer(f"✅ Reklama yakunlandi!\n👥 {success_count} ta foydalanuvchiga yetkazildi.")

# Admin audioni bazaga qo'shishi
@dp.message(lambda msg: msg.audio is not None)
async def handle_audio(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    audio = message.audio
    search_key = f"{audio.performer or 'Nomalum'} {audio.title or 'Nomalum'}".lower().strip()
    baza[search_key] = {"file_id": audio.file_id, "title": audio.title or "Nomalum", "performer": audio.performer or "Nomalum"}
    save_json(BAZA_FILE, baza)
    await message.answer(f"✅ Saqlandi: {audio.performer} - {audio.title}")

# Oddiy foydalanuvchilar musiqa qidirganda
@dp.message()
async def search_music(message: types.Message):
    user_id = message.from_user.id
    if not await check_subscription(user_id):
        await message.answer("❌ Botdan foydalanish uchun kanal va guruhimizga a'zo bo'ling!", reply_markup=get_subscription_keyboard())
        return

    query = message.text.lower().strip()
    found = False
    for key, music_data in baza.items():
        if query in key:
            await message.answer_audio(audio=music_data["file_id"], caption=f"🎵 {music_data['performer']} - {music_data['title']}")
            found = True
    if not found:
        await message.answer("😔 Kechirasiz, bunday musiqa topilmadi.")

async def main():
    print("🤖 Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
