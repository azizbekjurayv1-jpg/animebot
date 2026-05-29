import os
import re
import random
import asyncio
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from shazamio import Shazam

# Botingiz tokeni
BOT_TOKEN = "8300065405:AAE6MOr5EhoPmGujdvx11yPPNZ2lHR0gdRk"

try:
    bot = telebot.TeleBot(BOT_TOKEN)
    bot_info = bot.get_me()
    print(f"🔥 Mukammal universal bot ishga tushdi: @{bot_info.username}")
except Exception as e:
    print(f"❌ Xatolik: {e}")

os.makedirs("downloads", exist_ok=True)
URL_REGEXP = r'(https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*))'

# Qidiruv natijalarini vaqtincha saqlash xotirasi (Tugmalar ishlashi uchun)
user_search_cache = {}

async def recognize_audio(file_path):
    shazam = Shazam()
    try:
        out = await shazam.recognize_song(file_path)
        if out and 'track' in out:
            title = out['track'].get('title')
            subtitle = out['track'].get('subtitle')
            return f"{subtitle} {title}"
    except:
        pass
    return None

def download_and_send_music(chat_id, user_id, query, reply_to_id):
    unique_id = f"{user_id}_{random.randint(100, 999)}"
    full_audio_path = f"downloads/track_{chat_id}_{unique_id}.mp3"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
        'outtmpl': f"downloads/track_{chat_id}_{unique_id}.%(ext)s",
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'quiet': True,
        'nocheckcertificate': True
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info and len(info['entries']) > 0:
                title = info['entries'][0].get('title', 'Musiqa')
            else:
                title = info.get('title', 'Musiqa')
                
        if os.path.exists(full_audio_path):
            with open(full_audio_path, 'rb') as f:
                bot.send_audio(chat_id, f, reply_to_message_id=reply_to_id, caption=f"🎵 {title}\n\n🤖 Srazu yuklab berildi!")
            os.remove(full_audio_path)
            return True
    except Exception as e:
        print(f"Yuklashda xato: {e}")
    
    if os.path.exists(full_audio_path):
        os.remove(full_audio_path)
    return False

# ⚡️ O'SHA "XATO MA'LUMOT" CHIQISHINI DAVOLAYDIGAN ASOSIY QISM
@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    data = call.data
    
    # Telegram'ga so'rov yetib kelganini srazu bildiramiz (Ekrandagi yuklanish aylanasi to'xtaydi)
    try:
        bot.answer_callback_query(call.id, text="📥 Qo'shiq yuklanmoqda...")
    except:
        pass

    if data.startswith("music_"):
        try:
            index = int(data.split("_")[1])
            # Keshdan foydalanuvchining aynan o'sha qidiruv ro'yxatini olamiz
            if user_id in user_search_cache and index < len(user_search_cache[user_id]):
                chosen_track = user_search_cache[user_id][index]
                
                msg = bot.send_message(chat_id, f"📥 **{chosen_track}** yuklanmoqda...")
                success = download_and_send_music(chat_id, user_id, chosen_track, call.message.message_id)
                
                if success:
                    bot.delete_message(chat_id, msg.message_id)
                else:
                    bot.edit_message_text("❌ Yuklashda xatolik yuz berdi.", chat_id, msg.message_id)
            else:
                bot.send_message(chat_id, "⚠️ Qidiruv muddati eskirgan, iltimos qaytadan yozing.")
        except Exception as e:
            print(f"Callback xatosi: {e}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        bot.reply_to(message, "🎤 Salom! Men sizni ortiqcha tugmalar bilan charchatmaydigan botman!\n\n"
                              "💬 **Lichkada:** Shunchaki qo'shiq nomini yozing.\n"
                              "👥 **Guruhda:** Qo'shiq qidirish uchun `/music qo'shiq_nomi` deb yozing.\n"
                              "🔗 **Link yuborilsa:** Ham videoni, ham MP3 versiyasini birga beraman!")
    except: pass

@bot.message_handler(func=lambda message: message.text is not None)
def handle_text_messages(message):
    text = message.text.strip()
    chat_id = message.chat.id
    user_id = message.from_user.id
    chat_type = message.chat.type
    
    # 1. Havolalar bilan ishlash qismi
    if re.search(URL_REGEXP, text):
        try: msg = bot.reply_to(message, "📥 Havola qabul qilindi, video yuklanmoqda...")
        except: return
        
        unique_id = f"{user_id}_{random.randint(100, 999)}"
        video_path = f"downloads/video_{chat_id}_{unique_id}.mp4"
        ydl_opts_video = {
            'format': 'best',
            'outtmpl': video_path,
            'quiet': True,
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }
        
        video_success = False
        try:
            with YoutubeDL(ydl_opts_video) as ydl:
                ydl.download([text])
            
            if os.path.exists(video_path):
                with open(video_path, 'rb') as v:
                    bot.send_video(chat_id, v, reply_to_message_id=message.message_id, caption="📹 Yuklab olindi.")
                video_success = True
                try: bot.edit_message_text("🎬 Video yuborildi! Endi ichidagi ohang aniqlanmoqda...", chat_id, msg.message_id)
                except: pass
        except:
            pass
            
        temp_audio = f"downloads/shazam_{chat_id}_{unique_id}.mp3"
        ydl_opts_audio = {
            'format': 'bestaudio/best',
            'outtmpl': f"downloads/shazam_{chat_id}_{unique_id}.%(ext)s",
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}],
            'quiet': True,
            'nocheckcertificate': True
        }
        
        try:
            with YoutubeDL(ydl_opts_audio) as ydl:
                ydl.download([text])
                
            if os.path.exists(temp_audio):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                song_name = loop.run_until_complete(recognize_audio(temp_audio))
                loop.close()
                os.remove(temp_audio)
                
                if song_name:
                    try: bot.edit_message_text(f"✨ Ohang: **{song_name}**\n📥 MP3 yuklanmoqda...", chat_id, msg.message_id)
                    except: pass
                    success = download_and_send_music(chat_id, user_id, song_name, message.message_id)
                    if success:
                        try: bot.delete_message(chat_id, msg.message_id)
                        except: pass
                else:
                    try: bot.edit_message_text("❌ Link ichidagi musiqa aniqlanmadi.", chat_id, msg.message_id)
                    except: pass
            else:
                if not video_success:
                    try: bot.edit_message_text("❌ Havolani yuklab bo'lmadi.", chat_id, msg.message_id)
                    except: pass
        except:
            pass
            
        if os.path.exists(video_path):
            try: os.remove(video_path)
            except: pass

    # 2. Matn orqali ro'yxat qidirish qismi (Guruhda /music, lichkada esa shunchaki matn)
    elif text.startswith("/music") or (chat_type == 'private' and not text.startswith("/")):
        query = text.replace("/music", "").strip() if text.startswith("/music") else text
        if not query:
            bot.reply_to(message, "⚠️ Qo'shiq nomini yozing.")
            return
            
        try: msg = bot.reply_to(message, "🔍 Qo'shiq qidirilmoqda...")
        except: return
        
        # 10 ta eng yaxshi natijani qidirish
        ydl_opts = {'format': 'bestaudio/best', 'default_search': 'ytsearch10', 'quiet': True}
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if 'entries' in info and len(info['entries']) > 0:
                    tracks = []
                    text_res = "🎵 **Topilgan to'liq versiyalar ro'yxati:**\n\n"
                    keyboard = types.InlineKeyboardMarkup(row_width=5)
                    buttons = []
                    
                    for i, entry in enumerate(info['entries'][:10]):
                        title = entry.get('title', 'Musiqa')
                        tracks.append(title)
                        text_res += f"{i+1}. {title}\n"
                        buttons.append(types.InlineKeyboardButton(text=str(i+1), callback_query_data=f"music_{i}"))
                    
                    user_search_cache[user_id] = tracks
                    keyboard.add(*buttons)
                    
                    bot.edit_message_text(text_res, chat_id, msg.message_id, reply_markup=keyboard)
                else:
                    bot.edit_message_text("❌ Hech narsa topilmadi.", chat_id, msg.message_id)
        except:
            # Agar qidiruv tizimida xato bo'lsa, to'g'ridan-to'g'ri birinchi natijani yuklab yuboraveradi
            success = download_and_send_music(chat_id, user_id, query, message.message_id)
            if success: bot.delete_message(chat_id, msg.message_id)
            else: bot.edit_message_text("❌ Topilmadi.", chat_id, msg.message_id)

@bot.message_handler(content_types=['voice', 'video', 'video_note', 'document'])
def handle_all_media(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        if message.content_type == 'voice':
            file_id = message.voice.file_id
        elif message.content_type == 'video':
            file_id = message.video.file_id
        elif message.content_type == 'video_note':
            file_id = message.video_note.file_id
        elif message.content_type == 'document' and message.document.mime_type and 'video' in message.document.mime_type:
            file_id = message.document.file_id
        else:
            return
            
        msg = bot.reply_to(message, "🎧 Media tahlil qilinmoqda...")
        unique_id = f"{user_id}_{random.randint(100, 999)}"
        local_file_path = f"downloads/media_{chat_id}_{unique_id}.mp3"
        
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(local_file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        if os.path.exists(local_file_path):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            song_name = loop.run_until_complete(recognize_audio(local_file_path))
            loop.close()
            os.remove(local_file_path)
            
            if song_name:
                try: bot.edit_message_text(f"✨ Ohang: **{song_name}**\n📥 MP3 yuklanmoqda...", chat_id, msg.message_id)
                except: pass
                success = download_and_send_music(chat_id, user_id, song_name, message.message_id)
                if success:
                    try: bot.delete_message(chat_id, msg.message_id)
                    except: pass
            else:
                try: bot.edit_message_text("❌ Musiqa topilmadi.", chat_id, msg.message_id)
                except: pass
    except:
        try: bot.edit_message_text("❌ Mediani tahlil qilib bo'lmadi.", chat_id, msg.message_id)
        except: pass

if __name__ == '__main__':
    bot.infinity_polling()
