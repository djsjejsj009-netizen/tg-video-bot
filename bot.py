import os
import threading
import json
from flask import Flask
import telebot
import yt_dlp

TOKEN = "8853016629:AAGuTwaErlD9vqE96tfuFeKmigT1SyxLU6Q"
ADMIN_ID = 7796991089

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# --- Работа с базой пользователей ---
DATA_FILE = 'users.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "banned": []}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"users": [], "banned": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# --- Веб-сервер против засыпания ---
@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- Команды для пользователей ---
@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    user_id = message.chat.id
    
    if user_id in data["banned"]:
        bot.reply_to(message, "🚫 Доступ к боту ограничен.")
        return
        
    if user_id not in data["users"] and user_id != ADMIN_ID:
        data["users"].append(user_id)
        save_data(data)
        try:
            user_info = (
                f"👤 Новый пользователь!\n"
                f"Имя: {message.from_user.first_name}\n"
                f"Username: @{message.from_user.username or 'нет'}\n"
                f"ID: {user_id}"
            )
            bot.send_message(ADMIN_ID, user_info)
        except:
            pass

    bot.reply_to(message, "Привет! Пришли мне ссылку на видео, и я попробую его скачать. 🎥")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, "ℹ️ Просто отправь мне ссылку на видео, и я скачаю его для тебя.")

# --- Административные команды ---
@bot.message_handler(commands=['status'])
def status(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, "✅ Бот работает стабильно!")

@bot.message_handler(commands=['stats'])
def get_stats(message):
    if message.chat.id != ADMIN_ID:
        return
    data = load_data()
    count = len(data["users"])
    banned_count = len(data["banned"])
    bot.reply_to(message, f"📊 Статистика бота:\n👥 Пользователей в базе: {count}\n🚫 Заблокировано: {banned_count}")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.split()[1])
        data = load_data()
        if target_id not in data["banned"]:
            data["banned"].append(target_id)
            save_data(data)
            bot.reply_to(message, f"✅ Пользователь {target_id} заблокирован.")
        else:
            bot.reply_to(message, "⚠️ Пользователь уже находится в бане.")
    except IndexError:
        bot.reply_to(message, "❌ Укажи ID. Пример: /ban 123456789")
    except ValueError:
        bot.reply_to(message, "❌ Неверный формат ID.")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.split()[1])
        data = load_data()
        if target_id in data["banned"]:
            data["banned"].remove(target_id)
            save_data(data)
            bot.reply_to(message, f"✅ Пользователь {target_id} разблокирован.")
        else:
            bot.reply_to(message, "❌ Этот пользователь не найден в черном списке.")
    except IndexError:
        bot.reply_to(message, "❌ Укажи ID. Пример: /unban 123456789")
    except ValueError:
        bot.reply_to(message, "❌ Неверный формат ID.")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.chat.id != ADMIN_ID:
        return
    text = message.text.replace('/broadcast', '').strip()
    if not text:
        bot.reply_to(message, "❌ Напиши текст для рассылки после команды /broadcast")
        return
    
    data = load_data()
    success = 0
    blocked = 0
    
    for uid in data["users"]:
        try:
            bot.send_message(uid, text)
            success += 1
        except:
            blocked += 1
            
    bot.reply_to(message, f"📢 Рассылка завершена!\n✅ Доставлено: {success}\n❌ Не смогли получить: {blocked}")

@bot.message_handler(commands=['stop'])
def stop_bot(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, "🛑 Остановка сервера бота...")
        os._exit(0)

# --- Скачивание видео ---
@bot.message_handler(func=lambda message: True)
def download_video(message):
    if message.chat.id in load_data()["banned"]:
        return
        
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
        try:
            bot.edit_message_text(f"❌ Ошибка: {error_text}", message.chat.id, msg.message_id)
        except:
            bot.send_message(message.chat.id, "❌ Ошибка скачивания.")
            
        if os.path.exists('video.mp4'):
            os.remove('video.mp4')

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    print("Бот запущен!")
    bot.polling(none_stop=True, interval=1)
