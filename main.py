import os
import json
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from flask import Flask
from threading import Thread

# 1. RENDER UCHUN VEB-SERVER QISMI (PORT XATOSINI OLISH UCHUN)
app = Flask('')

@app.route('/')
def home():
    return "Bot tirik!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Veb-serverni orqa fonda ishga tushirish
Thread(target=run_flask).start()

# 2. TELEGRAM BOT QISMI
BOT_TOKEN = "8300065405:AAFzGAtlEIKGviHuLKc9teihXm4KduOwzQY"

session = requests.Session()
retry = Retry(connect=5, read=5, status_forcelist=[500, 502, 503, 504], backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
session.mount('http://', adapter)

telebot.apihelper.CUSTOM_REQUEST_SENDER = lambda method, url, **kwargs: session.request(method, url, **kwargs)
telebot.apihelper.CONNECT_TIMEOUT = 90
telebot.apihelper.READ_TIMEOUT = 90

try:
    bot = telebot.TeleBot(BOT_TOKEN)
except Exception as e:
    print(f"Token xatosi: {e}")

os.makedirs("downloads", exist_ok=True)
DB_FILE = "users.json"

def load_db():
    if not os.path.exists(DB_FILE): return {"users": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {"users": {}}

def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(db, f, indent=4, ensure_ascii=False)
    except: pass

def register_user(message):
    try:
        db = load_db()
        chat_id = str(message.chat.id)
        username = message.from_user.username or "Yashirin"
        first_name = message.from_user.first_name or "User"
        if chat_id not in db["users"]:
            db["users"][chat_id] = {"username": username, "name": first_name, "downloads_count": 0}
            save_db(db)
    except: pass

def increment_download(chat_id):
    try:
        db = load_db()
        cid = str(chat_id)
        if cid in db["users"]:
            db["users"][cid]["downloads_count"] += 1
            save_db(db)
    except: pass

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    register_user(message)
    try:
        bot.reply_to(message, "🎶 **Salom! Men tezyurar musiqa va video yuklovchiman!**\n\n"
                              "👉 Menga YouTube/Instagram linki tashlang yoki shunchaki **qo'shiq nomini** yozib yuboring, darrov topib beraman!")
    except: pass

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    register_user(message)
    text = message.text.strip()
    chat_id = message.chat.id
    
    if text.startswith("http://") or text.startswith("https://"):
        try:
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton(text="🎵 MP3 (Musiqasi)", callback_data=f"mp3_{text}"), 
                InlineKeyboardButton(text="🎬 MP4 (Videosi)", callback_data=f"mp4_{text}")
            )
            bot.reply_to(message, "📥 Havola aniqlandi. Sizga nima kerak? Formatni tanlang:", reply_markup=markup)
        except:
            pass
            
    elif not text.startswith("/"):
        try: 
            msg = bot.reply_to(message, f"🔍 `{text}` — YouTube'dan qidirilmoqda...")
        except: 
            return
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'default_search': 'ytsearch1',
            'outtmpl': f"downloads/%(title)s_{chat_id}.%(ext)s",
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                if 'entries' in info and len(info['entries']) > 0: video_info = info['entries'][0]
                else: video_info = info
                title = video_info.get('title', 'Musiqa')
                filename = ydl.prepare_filename(video_info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            
            if os.path.exists(filename):
                with open(filename, 'rb') as audio:
                    bot.send_audio(chat_id, audio, caption=f"🎵 {title}\n\n🤖 @musiqa_bot")
                increment_download(chat_id)
                try: bot.delete_message(chat_id, msg.message_id)
                except: pass
                os.remove(filename)
            else:
                bot.edit_message_text("❌ Musiqa fayli topilmadi.", chat_id, msg.message_id)
        except:
            try: bot.edit_message_text("❌ Kechirasiz, qo'shiq topilmadi.", chat_id, msg.message_id)
        
        except: pass

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data.startswith('mp3_'):
        url = data.replace('mp3_', '')
        try: msg = bot.send_message(chat_id, "📥 MP3 (Audio) tayyorlanmoqda, kuting...")
        except: return
        ydl_opts = {
            'format': 'bestaudio/best', 
            'outtmpl': f"downloads/%(title)s_{chat_id}.%(ext)s",
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 
            'quiet': True, 'ignoreerrors': True
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if 'entries' in info: video_info = info['entries'][0]
                else: video_info = info
                filename = ydl.prepare_filename(video_info).rsplit('.', 1)[0] + ".mp3"
                
            with open(filename, 'rb') as audio: 
                bot.send_audio(chat_id, audio, caption="🎵 @musiqa_bot")
            increment_download(chat_id)
            try: bot.delete_message(chat_id, msg.message_id)
            except: pass
            if os.path.exists(filename): os.remove(filename)
        except: 
            try: bot.send_message(chat_id, "❌ Musiqasini ajratib bo'lmadi.")
            except: pass

    elif data.startswith('mp4_'):
        url = data.replace('mp4_', '')
        try: msg = bot.send_message(chat_id, "📥 MP4 (Video) yuklanmoqda, kuting...")
        except: return
        ydl_opts = {
            'format': 'best[ext=mp4]/best', 'outtmpl': f"downloads/%(title)s_{chat_id}.%(ext)s", 
            'quiet': True, 'ignoreerrors': True
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if 'entries' in info: video_info = info['entries'][0]
                else: video_info = info
                filename = ydl.prepare_filename(video_info)
                if not os.path.exists(filename): filename = filename.rsplit('.', 1)[0] + ".mp4"
                
            with open(filename, 'rb') as video: 
                bot.send_video(chat_id, video, caption="🎬 @musiqa_bot")
            increment_download(chat_id)
            try: bot.delete_message(chat_id, msg.message_id)
            except: pass
            if os.path.exists(filename): os.remove(filename)
        except: 
            try: bot.send_message(chat_id, "❌ Videoni yuklashda xatolik yuz berdi.")
            except: pass

if __name__ == '__main__':
    try:
        bot.infinity_polling(timeout=90, long_polling_timeout=30)
    except:
        pass
