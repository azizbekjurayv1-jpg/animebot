import os
import re
import random
import urllib.request
import urllib.parse
import asyncio
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from shazamio import Shazam

# 🔐 Yangi xavfsiz tokeningiz muvaffaqiyatli ulandi
BOT_TOKEN = "8300065405:AAHYQg291ZdtJADxTRFdniqhq-altqjVqtQ"

try:
    bot = telebot.TeleBot(BOT_TOKEN)
    bot_info = bot.get_me()
    print(f"🔥 Bloklanmas va o'chmas bot yangi token bilan ishga tushdi: @{bot_info.username}")
except Exception as e:
    print(f"❌ Botni ulashda xatolik: {e}")

os.makedirs("downloads", exist_ok=True)
URL_REGEXP = r'(https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*))'

user_search_cache = {}

def search_youtube_html(query):
    """ YouTube sahifasini to'g'ridan-to'g'ri scraping qilib, linklarni topuvchi funksiya """
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            
        video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", html)
        if video_ids:
            seen = set()
            unique_ids = [x for x in video_ids if not (x in seen or seen.add(x))]
            return [f"https://www.youtube.com/watch?v={vid}" for vid in unique_ids[:5]]
    except Exception as e:
        print(f"Scraping xatosi: {e}")
    return []

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

def download_and_send_music(chat_id, user_id, direct_url, reply_to_id, custom_title=None):
    unique_id = f"{user_id}_{random.randint(100, 999)}"
    full_audio_path = f"downloads/track_{chat_id}_{unique_id}.mp3"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"downloads/track_{chat_id}_{unique_id}.%(ext)s",
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'quiet': True,
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(direct_url, download=True)
            title = custom_title if custom_title else info.get('title', 'Musiqa')
                
        if os.path.exists(full_audio_path):
            with open(full_audio_path, 'rb') as f:
                bot.send_audio(chat_id, f, reply_to_message_id=reply_to_id, caption=f"🎵 {title}\n\n🤖 Muammosiz yuklandi!")
            os.remove(full_audio_path)
            return True, None
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        return False, error_msg
    
    if os.path.exists(full_audio_path):
        os.remove(full_audio_path)
    return False, "Fayl yuklanmadi."

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    data = call.data
    
    try:
        bot.answer_callback_query(call.id, text="📥 Qo'shiq yuklanmoqda...")
    except:
        pass

    if data.startswith("music_"):
        try:
            index = int(data.split("_")[1])
            if user_id in user_search_cache and index < len(user_search_cache[user_id]):
                chosen_data = user_search_cache[user_id][index]
                chosen_url = chosen_data['url']
                chosen_title = chosen_data['title']
                
                msg = bot.send_message(chat_id, f"📥 **{chosen_title}** yuklanmoqda...")
                success, err = download_and_send_music(chat_id, user_id, chosen_url, call.message.message_id, custom_title=chosen_title)
                
                if success:
                    bot.delete_message(chat_id, msg.message_id)
                else:
                    bot.edit_message_text(f"❌ Yuklashda xato: {err}", chat_id, msg.message_id)
            else:
                bot.send_message(chat_id, "⚠️ Qidiruv muddati eskirgan, iltimos qaytadan yozing.")
        except Exception as e:
            print(f"Callback xatosi: {e}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        bot.reply_to(message, "🎤 Salom! Men hamma blokirovkalarni aylanib o'tuvchi aqlli musiqiy botman!\n\n"
                              "💬 **Lichkada:** Shunchaki qo'shiq nomini yozing.\n"
                              "👥 **Guruhda:** Qo'shiq qidirish uchun `/music qo'shiq_nomi` deb yozing.\n"
                              "🔗 **Link yuborilsa:** Uni to'g'ridan-to'g'ri MP3 qilib yuklab beraman!")
    except: pass

@bot.message_handler(func=lambda message: message.text is not None)
def handle_text_messages(message):
    text = message.text.strip()
    chat_id = message.chat.id
    user_id = message.from_user.id
    chat_type = message.chat.type
    
    if re.search(URL_REGEXP, text):
        try: msg = bot.reply_to(message, "📥 Havola qabul qilindi, yuklanmoqda...")
        except: return
        
        success, err = download_and_send_music(chat_id, user_id, text, message.message_id)
        if success:
            try: bot.delete_message(chat_id, msg.message_id)
            except: pass
        else:
            bot.edit_message_text(f"❌ Linkdan yuklab bo'lmadi: {err}", chat_id, msg.message_id)

    elif text.startswith("/music") or (chat_type == 'private' and not text.startswith("/")):
        query = text.replace("/music", "").strip() if text.startswith("/music") else text
        if not query:
            bot.reply_to(message, "⚠️ Qo'shiq nomini yozing.")
            return
            
        try: msg = bot.reply_to(message, "🔍 Qo'shiq qidirilmoqda...")
        except: return
        
        links = search_youtube_html(query)
        
        if links:
            tracks = []
            text_res = "🎵 **Siz uchun topilgan musiqalar ro'yxati:**\n\n"
            keyboard = types.InlineKeyboardMarkup(row_width=5)
            buttons = []
            
            for i, link in enumerate(links):
                title = f"Musiqa variant №{i+1} ({query})"
                tracks.append({'url': link, 'title': title})
                text_res += f"{i+1}. 🔊 {title}\n"
                buttons.append(types.InlineKeyboardButton(text=str(i+1), callback_query_data=f"music_{i}"))
            
            user_search_cache[user_id] = tracks
            keyboard.add(*buttons)
            
            bot.edit_message_text(text_res, chat_id, msg.message_id, reply_markup=keyboard)
        else:
            bot.edit_message_text("❌ Hech narsa topilmadi. Iltimos, boshqacha nom yozib ko'ring.", chat_id, msg.message_id)

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
                
                links = search_youtube_html(song_name)
                if links:
                    success, err = download_and_send_music(chat_id, user_id, links[0], message.message_id, custom_title=song_name)
                    if success:
                        try: bot.delete_message(chat_id, msg.message_id)
                        except: pass
                    else:
                        bot.edit_message_text(f"❌ Xato: {err}", chat_id, msg.message_id)
                else:
                    bot.edit_message_text("❌ Ohang aniqlandi, lekin yuklash uchun havola topilmadi.", chat_id, msg.message_id)
            else:
                bot.edit_message_text("❌ Musiqa topilmadi.", chat_id, msg.message_id)
    except Exception as e:
        try: bot.edit_message_text(f"❌ Mediani tahlil qilib bo'lmadi: {e}", chat_id, msg.message_id)
        except: pass

if __name__ == '__main__':
    bot.infinity_polling()
