import os
import json
import threading
import telebot
from telebot import types
import yt_dlp
from flask import Flask

# Настройки бота и администратора
TOKEN = "ТВОЙ_ТОКЕН_БОТА"
ADMIN_ID = 7796991089

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Базы данных в JSON
USERS_FILE = 'users.json'
BANNED_FILE = 'banned.json'

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_user(user_id):
    users = load_json(USERS_FILE)
    if user_id not in users:
        users.append(user_id)
        save_json(USERS_FILE, users)

def is_banned(user_id):
    banned = load_json(BANNED_FILE)
    return user_id in banned

# Временное хранение ссылок пользователей
user_links = {}

@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "🚫 Вы заблокированы в этом боте.")
        return
    
    # Проверка на нового пользователя для уведомления админа
    users = load_json(USERS_FILE)
    if user_id not in users:
        add_user(user_id)
        # Уведомление администратору
        username = message.from_user.username
        name = message.from_user.first_name
        mention = f"@{username}" if username else "без юзернейма"
        try:
            bot.send_message(ADMIN_ID, f"🆕 Новый пользователь!\n👤 Имя: {name}\n🔗 Юзернейм: {mention}\n🆔 ID: {user_id}")
        except:
            pass # Если бот не может написать админу, просто пропускаем
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Наш канал", url="https://t.me/lolurent"))
    
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я твой супер-бот для скачивания медиа.\n\n"
        "📥 Отправь мне ссылку на видео (TikTok, YouTube, Instagram и др.), "
        "и я предложу выбрать формат (Видео HD или аудио MP3)!",
        reply_markup=markup
    )

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    users = load_json(USERS_FILE)
    banned = load_json(BANNED_FILE)
    bot.reply_to(
        message,
        f"📊 **Статистика бота:**\n\n"
        f"👥 Всего пользователей: {len(users)}\n"
        f"🚫 Заблокировано: {len(banned)}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['ban'])
def cmd_ban(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Укажи ID. Пример: `/ban 123456789`", parse_mode="Markdown")
        return
    try:
        target_id = int(args[1])
        banned = load_json(BANNED_FILE)
        if target_id not in banned:
            banned.append(target_id)
            save_json(BANNED_FILE, banned)
        bot.reply_to(message, f"✅ Пользователь `{target_id}` заблокирован.", parse_mode="Markdown")
    except ValueError:
        bot.reply_to(message, "❌ Неверный ID.")

@bot.message_handler(commands=['unban'])
def cmd_unban(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Укажи ID. Пример: `/unban 123456789`", parse_mode="Markdown")
        return
    try:
        target_id = int(args[1])
        banned = load_json(BANNED_FILE)
        if target_id in banned:
            banned.remove(target_id)
            save_json(BANNED_FILE, banned)
        bot.reply_to(message, f"✅ Пользователь `{target_id}` разблокирован.", parse_mode="Markdown")
    except ValueError:
        bot.reply_to(message, "❌ Неверный ID.")

@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace('/broadcast', '').strip()
    if not text:
        bot.reply_to(message, "⚠️ Напиши текст для рассылки после команды.")
        return
    
    users = load_json(USERS_FILE)
    success = 0
    failed = 0
    
    status_msg = bot.reply_to(message, "🚀 Рассылка началась...")
    
    for user_id in users:
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✨ Открыть бота", url="https://t.me/viddownload2026_bot"))
            bot.send_message(user_id, text, reply_markup=markup)
            success += 1
        except:
            failed += 1
            
    bot.edit_message_text(
        f"✅ **Рассылка завершена!**\n\n"
        f"📤 Успешно доставлено: {success}\n"
        f"❌ Ошибок (заблокировали): {failed}",
        message.chat.id,
        status_msg.message_id,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        return
        
    text = message.text.strip()
    if text.startswith("http://") or text.startswith("https://"):
        user_links[user_id] = text
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📥 Видео (HD)", callback_data="dl_video"),
            types.InlineKeyboardButton("🎵 Аудио (MP3)", callback_data="dl_audio")
        )
        
        bot.reply_to(
            message,
            "🔗 Ссылка принята! Выбери формат для скачивания:",
            reply_markup=markup
        )
    else:
        bot.reply_to(message, "⚠️ Пожалуйста, отправь корректную ссылку на видео.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    if is_banned(user_id):
        return
        
    if user_id not in user_links:
        bot.answer_callback_query(call.id, "⚠️ Ссылка устарела. Отправь её заново.")
        return
        
    url = user_links[user_id]
    is_audio = call.data == "dl_audio"
    
    bot.edit_message_text(
        "⏳ **Скачиваем файл с сервера... Пожалуйста, подожди.**",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )
    
    filename = f"media_{user_id}"
    ydl_opts = {
        'outtmpl': filename + '.%(ext)s',
        'format': 'bestaudio/best' if is_audio else 'best',
    }
    
    if is_audio:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            real_filename = ydl.prepare_filename(info)
            if is_audio:
                real_filename = os.path.splitext(real_filename)[0] + '.mp3'
            else:
                real_filename = os.path.splitext(real_filename)[0] + '.mp4'
            
        bot.edit_message_text(
            "📤 **Отправляю файл в чат...**",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        
        with open(real_filename, 'rb') as f:
            if is_audio:
                bot.send_audio(call.message.chat.id, f, caption="🎧 Твое аудио готово!")
            else:
                bot.send_video(call.message.chat.id, f, caption="🎬 Твое видео готово!")
                
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
    except Exception as e:
        bot.edit_message_text(
            f"❌ **Ошибка при скачивании:**\n`{str(e)}`",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    finally:
        # Автоочистка всех временных файлов пользователя
        for ext in ['.mp4', '.mp3', '.webm', '.m4a', '.part']:
            f_path = f"media_{user_id}{ext}"
            if os.path.exists(f_path):
                os.remove(f_path)

if __name__ == '__main__':
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("Бот запущен!")
    bot.infinity_polling()
        
