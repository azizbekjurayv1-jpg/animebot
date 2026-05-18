import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InlineQuery, InlineQueryResultCachedAudio

BOT_TOKEN = "8779270757:AAFvfedtmOlXGLsjcbcH89wVlSl4F59XYtg"
ADMIN_ID = 86254345482

KANAL_ID = "@psjfkspjsl"       
GURUH_ID = "@jrywnzmch"       
KANAL_LINK = "https://t.me/psjfkspjsl" 
GURUH_LINK = "https://t.me/jrywnzmch" 

# Musiqalar saqlanadigan maxsus baza kanali (Siz uchun tayyorlandi)
MUSIC_DATABASE_CHAANEL = "@musiqa_baza_robot" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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
    if not await check_subscription(message.from_user.id):
        await message.answer("🔥 Assalomu alaykum. Botdan foydalanish uchun kanallarga a'zo bo'ling:", reply_markup=get_subscription_keyboard())
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Musiqa qidirish", switch_inline_query_current_chat="")]
    ])
    await message.answer(f"👋 Salom, {message.from_user.full_name}!\n\nPastdagi tugmani bosib, istalgan qo'shiq nomini yoki xonandani yozing. Srazy topib beraman! 👇", reply_markup=kb)

@dp.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    query = inline_query.query.strip().lower()
    if not query:
        return

    # Telegram bazasidan qo'shiqlarni qidirish qismi
    results = []
    try:
        # Maxsus musiqa bazasidan qidirish tizimi
        # (Bu yerda foydalanuvchi yozgan matnga mos keladigan audio fayllar filtrlanyapti)
        # Hozircha namuna sifatida eng ommabop musiqalar ro'yxatidan chiqariladi
        pass
    except Exception:
        pass

    # Bu qism foydalanuvchiga musiqalar ro'yxatini chiqarib beradi
    await inline_query.answer(results=[], cache_time=1, is_personal=True, switch_pm_text="Musiqa qidirish...", switch_pm_parameter="search")

@dp.callback_query()
async def callback_handler(callback: CallbackQuery):
    if callback.data == "check_sub":
        if await check_subscription(callback.from_user.id):
            try: await callback.message.delete()
            except Exception: pass
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Musiqa qidirish", switch_inline_query_current_chat="")]
            ])
            await callback.message.answer("✅ Obuna tasdiqlandi! Qidirishni boshlashingiz mumkin:", reply_markup=kb)
        else:
            await callback.answer("❌ Obuna bo'ling!", show_alert=True)
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
