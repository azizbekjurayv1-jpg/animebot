import os
import time
import subprocess
import json
import telebot
import yt_dlp

# 🛑 TOKENINGIZNI YOZING
BOT_TOKEN = "8300065405:AAF06AxjTEny7zfQxVEFk38Cw3hGCIijxb8"
bot = telebot.TeleBot(BOT_TOKEN)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

DB_FILE = "music_cache.json"

# 📂 BAZANI YUKLASH FUNKSIYASI
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

# 💾 BAZAGA SAQLASH FUNKSIYASI
def save_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Bazaga saqlashda xato: {e}")

# Musiqa bazasini xotiraga yuklaymiz
MUSIC_DB = load_db()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 **Salom! Men tezkor va aqlli musiqa yuklovchi botman!**\n\n"
        "🎵 Menga shunchaki **qo'shiq nomini** yoki ijrochini yozib yuboring (Masalan: `Billionera`), "
        "men uni qidirib topaman va sizga qo'shiqdan parcha kesib tashlab beraman!\n\n"
        "⚡️ _Bot xotira bazasiga ega. Bir marta topilgan qo'shiqlar keyingi safar daxshatli tezlikda yuboriladi!_"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# Qo'shiq qidirish matnli xabarlarni ushlash
@bot.message_handler(func=lambda message: not message.text.startswith("http") and not message.text.startswith("/"))
def handle_song_search(message):
    query = message.text.strip().lower() # Bazada qidirish oson bo'lishi uchun kichik harfga o'giramiz
    
    # 🔍 1-QADAM: BAZADAN TEKSHIRISH (Agar bu qo'shiq oldin yuklangan bo'lsa)
    if query in MUSIC_DB:
        file_id = MUSIC_DB[query]["file_id"]
        song_title = MUSIC_DB[query]["title"]
        
        # Hech narsani yuklamasdan, Telegram serveridagi tayyor faylni srazu yuboramiz
        try:
            bot.send_audio(
                chat_id=message.chat.id,
                audio=file_id,
                caption=f"🎵 **{song_title}** (Parcha)\n\n⚡️ _Bazadan daxshatli tezlikda topildi!_\n📥 @{bot.get_me().username}",
                reply_to_message_id=message.message_id
            )
            return # Kodni shu yerda to'xtatamiz, YouTube'ga borishga hojat yo'q!
        except Exception as e:
            # Agar file_id eskirgan yoki xato bo'lsa, pastdagi yuklash qismiga o'tib ketaveradi
            pass

    # 📥 2-QADAM: AGAR BAZADA YO'Q BO'LSA, YOUTUBE'DAN YUKLASH
    status_msg = bot.reply_to(message, f"🔍 **'{message.text}'** qo'shig'i qidirilmoqda...\n_Iltimos, biroz kuting..._", parse_mode="Markdown")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message.text, download=True)
            if 'entries' in info:
                video_info = info['entries'][0]
            else:
                video_info = info
                
            downloaded_file = ydl.prepare_filename(video_info)
            song_title = video_info.get('title', 'Qo\'shiq')
            
            # Fayl formatini aniqlash
            base, ext = os.path.splitext(downloaded_file)
            if not os.path.exists(downloaded_file):
                for e in ['.m4a', '.webm', '.mp3', '.ogg']:
                    if os.path.exists(base + e):
                        downloaded_file = base + e
                        break

            # FFmpeg orqali qo'shiqdan 30 soniyalik parcha kesish
            output_cut_file = f"{DOWNLOAD_DIR}/{video_info['id']}_cut.mp3"
            
            ffmpeg_cmd = [
                'ffmpeg', '-y', 
                '-ss', '00:00:30', 
                '-i', downloaded_file, 
                '-t', '30', 
                '-b:a', '128k', 
                output_cut_file
            ]
            
            duration = video_info.get('duration', 0)
            if duration < 40:
                ffmpeg_cmd[2] = '00:00:00'
            
            subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            bot.edit_message_text("🚀 **Parcha tayyor! Telegramga yuklanmoqda...**", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")
            
            # Parchani yuboramiz va Telegram qaytargan fayl ma'lumotlarini olamiz
            with open(output_cut_file, 'rb') as audio_file:
                sent_audio = bot.send_audio(
                    chat_id=message.chat.id,
                    audio=audio_file,
                    caption=f"🎵 **{song_title}** (Parcha)\n\n📥 @{bot.get_me().username} orqali topildi.",
                    title=f"{song_title} (Parcha)",
                    performer="SongFast Bot",
                    duration=30,
                    reply_to_message_id=message.message_id
                )
            
            # 💾 3-QADAM: YANGA FAYLNI BAZAGA QO'SHISH
            # Telegram bergan file_id ni bazaga saqlab qo'yamiz
            MUSIC_DB[query] = {
                "file_id": sent_audio.audio.file_id,
                "title": song_title
            }
            save_db(MUSIC_DB) # Faylga yozish
            
            # Vaqtincha fayllarni o'chirish
            if os.path.exists(downloaded_file): os.remove(downloaded_file)
            if os.path.exists(output_cut_file): os.remove(output_cut_file)
            bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
            
    except Exception as e:
        print(f"Xato yuz berdi: {e}")
        bot.edit_message_text("❌ **Kechirasiz, qo'shiq topilmadi!**\n\nIltimos, nomini to'g'riroq yozib qayta urinib ko'ring.", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")

if __name__ == '__main__':
    print("Baza tizimli musiqa bot ishga tushdi...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)

