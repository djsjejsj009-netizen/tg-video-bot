import os
import threading
from flask import Flask
import telebot
import yt_dlp

TOKEN = "8853016629:AAGuTwaErlD9vqE96tfuFeKmigT1SyxLU6Q"
ADMIN_ID = 7796991089

bot = telebot.TeleBot(TOKEN)

# Создаем простой веб-сервер для Render
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Пришли мне ссылку на видео, и я попробую его скачать.")
    
    try:
        user_info = (
            f"👤 Новый пользователь в боте!\n"
            f"Имя: {message.from_user.first_name}\n"
            f"Username: @{message.from_user.username or 'нет'}\n"
            f"ID: {message.from_user.id}"
        )
        bot.send_message(ADMIN_ID, user_info)
    except Exception as e:
        print(f"Ошибка отправки админу: {e}")

@bot.message_handler(commands=['status'])
def status(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, "✅ Бот работает!")

@bot.message_handler(commands=['stop'])
def stop_bot(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, "🛑 Остановка...")
        os._exit(0)

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()
    if not url.startswith("http"):
        return
    
    msg = bot.reply_to(message, "⏳ Скачиваю видео...")
    
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video.mp4',
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        if os.path.exists('video.mp4'):
            with open('video.mp4', 'rb') as video:
                bot.send_video(message.chat.id, video, caption="Готово! 🎥")
            os.remove('video.mp4')
        else:
            bot.edit_message_text("❌ Не удалось найти файл видео.", message.chat.id, msg.message_id)
            
        bot.delete_message(message.chat.id, msg.message_id)
        
    except Exception as e:
        error_text = str(e)
        if len(error_text) > 100:
            error_text = error_text[:100] + "..."
        bot.edit_message_text(f"❌ Ошибка: {error_text}", message.chat.id, msg.message_id)
        if os.path.exists('video.mp4'):
            os.remove('video.mp4')

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    print("Бот запущен!")
    bot.polling(none_stop=True, interval=1)
