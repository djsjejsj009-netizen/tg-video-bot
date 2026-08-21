import os
import json
import threading
import telebot
from telebot import types
from flask import Flask

# ==================== НАСТРОЙКИ ====================
TOKEN = "8853016629:AAHZ2sXg5jHuynIcbskyMHFB9q6LNiAX41g"
ADMIN_ID = 7796991089
CHANNEL_RULES = "https://t.me/lolurent"  # Ссылка на канал с мануалами/правилами
SUPPORT_USERNAME = "@admin_support"      # Ссылка на саппорт / админа для связи

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "Work Bot is running 24/7!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ==================== БАЗЫ ДАННЫХ (JSON) ====================
USERS_FILE = 'workers.json'       # Все воркеры {user_id: {name, username, balance, total_profit, wallet, status}}
PROFITS_FILE = 'profits.json'     # История профитов
WITHDRAW_FILE = 'withdraws.json'  # Заявки на вывод

def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return {} if filename == USERS_FILE else []
    return {} if filename == USERS_FILE else []

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==================== КЛАВИАТУРЫ ====================
def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💼 Мой профиль", "📊 Статистика команды")
    markup.row("📖 Мануалы", "⚙️ Настроить кошелек")
    markup.row("💸 Запросить выплату", "💬 Поддержка")
    return markup

# ==================== ОБРАБОТЧИК /START ====================
@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = str(message.from_user.id)
    users = load_data(USERS_FILE)
    
    # Регистрация воркера
    if user_id not in users:
        users[user_id] = {
            "name": message.from_user.first_name,
            "username": message.from_user.username or "нет",
            "balance": 0.0,
            "total_profit": 0.0,
            "wallet": "Не указан",
            "banned": False
        }
        save_data(USERS_FILE, users)
        
        # Уведомление админу о новом воркере
        try:
            bot.send_message(
                ADMIN_ID,
                f"🆕 **Новый воркер в команде!**\n\n"
                f"👤 Имя: {message.from_user.first_name}\n"
                f"🔗 Юзернейм: @{message.from_user.username or 'отсутствует'}\n"
                f"🆔 ID: `{user_id}`",
                parse_mode="Markdown"
            )
        except:
            pass

    if users[user_id].get("banned", False):
        bot.reply_to(message, "🚫 Вы заблокированы в этой системе.")
        return

    bot.send_message(
        message.chat.id,
        f"👋 Добро пожаловать в ворк-панель, **{message.from_user.first_name}**!\n\n"
        "Используй меню ниже для работы, проверки баланса и вывода средств.",
        reply_markup=main_menu_markup(),
        parse_mode="Markdown"
    )

# ==================== ПРОФИЛЬ И КОШЕЛЕК ====================
@bot.message_handler(func=lambda m: m.text == "💼 Мой профиль")
def profile_handler(message):
    user_id = str(message.from_user.id)
    users = load_data(USERS_FILE)
    if user_id not in users:
        return cmd_start(message)
    
    u = users[user_id]
    text = (
        f"👤 **Твой профиль воркера:**\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"💰 Баланс: **{u['balance']} $**\n"
        f"🏆 Всего заработано: **{u['total_profit']} $**\n"
        f"💳 Кошелек/Реквизиты: `{u['wallet']}`\n"
        f"📊 Статус: {'🔴 Заблокирован' if u['banned'] else '🟢 Активен'}"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "⚙️ Настроить кошелек")
def set_wallet_start(message):
    msg = bot.reply_to(message, "✍️ Отправь в ответном сообщении свои реквизиты (USDT TRC20, USDT TON, банковская карта и т.д.):")
    bot.register_next_step_handler(msg, save_wallet_process)

def save_wallet_process(message):
    user_id = str(message.from_user.id)
    wallet_text = message.text.strip()
    users = load_data(USERS_FILE)
    
    if user_id in users:
        users[user_id]["wallet"] = wallet_text
        save_data(USERS_FILE, users)
        bot.reply_to(message, f"✅ Кошелек успешно сохранен:\n`{wallet_text}`", parse_mode="Markdown", reply_markup=main_menu_markup())

# ==================== МАНУАЛЫ И ПОДДЕРЖКА ====================
@bot.message_handler(func=lambda m: m.text == "📖 Мануалы")
def manuals_handler(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📚 Открыть канал с мануалами", url=CHANNEL_RULES))
    bot.reply_to(message, "📖 Все актуальные мануалы, схемы и гайды находятся в нашем канале:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "💬 Поддержка")
def support_handler(message):
    bot.reply_to(message, f"💬 По всем вопросам, за помощью или по поводу залетевших профитов пишите саппорту: {SUPPORT_USERNAME}")

@bot.message_handler(func=lambda m: m.text == "📊 Статистика команды")
def team_stats(message):
    users = load_data(USERS_FILE)
    profits = load_data(PROFITS_FILE)
    
    total_workers = len(users)
    all_time_money = sum(p.get('amount', 0) for p in profits)
    
    bot.reply_to(
        message,
        f"📊 **Общая статистика команды:**\n\n"
        f"👥 Всего воркеров: {total_workers}\n"
        f"💰 Суммарный профит команды: **{all_time_money} $**\n"
        f"🎯 Успешных профитов: {len(profits)}",
        parse_mode="Markdown"
    )

# ==================== ВЫПЛАТЫ ====================
@bot.message_handler(func=lambda m: m.text == "💸 Запросить выплату")
def request_withdraw(message):
    user_id = str(message.from_user.id)
    users = load_data(USERS_FILE)
    
    if user_id not in users:
        return
    
    balance = users[user_id]["balance"]
    wallet = users[user_id]["wallet"]
    
    if balance <= 0:
        bot.reply_to(message, "⚠️ У тебя нулевой баланс для вывода.")
        return
        
    if wallet == "Не указан":
        bot.reply_to(message, "⚠️ Сначала укажи свой кошелек через кнопку «⚙️ Настроить кошелек»!")
        return
        
    # Отправка заявки админу
    withdraws = load_data(WITHDRAW_FILE)
    req_id = str(len(withdraws) + 1)
    
    withdraw_data = {
        "req_id": req_id,
        "user_id": user_id,
        "amount": balance,
        "wallet": wallet
    }
    withdraws.append(withdraw_data)
    save_data(WITHDRAW_FILE, withdraws)
    
    # Сбрасываем баланс воркера до подтверждения (или замораживаем)
    users[user_id]["balance"] = 0.0
    save_data(USERS_FILE, users)
    
    # Кнопки для админа
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Выплачено", callback_data=f"wd_yes_{req_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"wd_no_{req_id}")
    )
    
    try:
        bot.send_message(
            ADMIN_ID,
            f"💸 **Новая заявка на вывод!**\n\n"
            f"👤 Воркер: ID `{user_id}` (@{users[user_id]['username']})\n"
            f"💵 Сумма: **{balance} $**\n"
            f"💳 Реквизиты: `{wallet}`",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    except:
        pass
        
    bot.reply_to(message, f"✅ Заявка на вывод **{balance} $** успешно отправлена администратору!", parse_mode="Markdown")

# ==================== АДМИН-ПАНЕЛЬ / КОМАНДЫ АДМИНА ====================
@bot.message_handler(commands=['admin'])
def cmd_admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    help_text = (
        "👑 **Админ-панель команды:**\n\n"
        "• `/addprofit [ID] [Сумма]` — Зачислить профит воркеру\n"
        "• `/balance [ID] [Сумма]` — Изменить баланс вручную\n"
        "• `/ban [ID]` — Заблокировать воркера\n"
        "• `/unban [ID]` — Разблокировать воркера\n"
        "• `/broadcast [Текст]` — Рассылка всем воркерам\n"
        "• `/users` — Список всех воркеров"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['addprofit'])
def cmd_addprofit(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "⚠️ Формат: `/addprofit ID СУММА`", parse_mode="Markdown")
        return
    
    target_id = args[1]
    try:
        amount = float(args[2])
    except ValueError:
        bot.reply_to(message, "❌ Неверная сумма.")
        return
        
    users = load_data(USERS_FILE)
    if target_id not in users:
        bot.reply_to(message, "❌ Воркер с таким ID не найден в базе.")
        return
        
    users[target_id]["balance"] += amount
    users[target_id]["total_profit"] += amount
    save_data(USERS_FILE, users)
    
    # Сохраняем в общую историю профитов
    profits = load_data(PROFITS_FILE)
    profits.append({"user_id": target_id, "amount": amount})
    save_data(PROFITS_FILE, profits)
    
    bot.reply_to(message, f"✅ Успешно зачислено `{amount}$` воркеру `{target_id}`!", parse_mode="Markdown")
    
    # Уведомление воркеру
    try:
        bot.send_message(target_id, f"🎉 **У тебя новый профит!**\n\n💰 Сумма: **{amount} $** зачислена на баланс!", parse_mode="Markdown")
    except:
        pass

@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace('/broadcast', '').strip()
    if not text:
        bot.reply_to(message, "⚠️ Напиши текст для рассылки.")
        return
    
    users = load_data(USERS_FILE)
    success = 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 **Рассылка от команды:**\n\n{text}", parse_mode="Markdown")
            success += 1
        except:
            pass
    bot.reply_to(message, f"✅ Рассылка завершена. Доставлено: {success}/{len(users)}")

@bot.message_handler(commands=['ban'])
def cmd_ban(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2: return
    uid = args[1]
    users = load_data(USERS_FILE)
    if uid in users:
        users[uid]["banned"] = True
        save_data(USERS_FILE, users)
        bot.reply_to(message, f"✅ Воркер `{uid}` заблокирован.", parse_mode="Markdown")

@bot.message_handler(commands=['unban'])
def cmd_unban(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2: return
    uid = args[1]
    users = load_data(USERS_FILE)
    if uid in users:
        users[uid]["banned"] = False
        save_data(USERS_FILE, users)
        bot.reply_to(message, f"✅ Воркер `{uid}` разблокирован.", parse_mode="Markdown")

# Обработка инлайн-кнопок вывода админом
@bot.callback_query_handler(func=lambda call: call.data.startswith('wd_'))
def withdraw_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
        
    action, _, req_id = call.data.split('_')
    withdraws = load_data(WITHDRAW_FILE)
    
    req = next((w for w in withdraws if w["req_id"] == req_id), None)
    if not req:
        bot.answer_callback_query(call.id, "⚠️ Заявка не найдена или уже обработана.")
        return
        
    target_id = req["user_id"]
    amount = req["amount"]
    
    if action == "yes":
        bot.edit_message_text(
            f"✅ **Заявка #{req_id} одобрена и выплачена!**\nСумма: {amount}$",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        try:
            bot.send_message(target_id, f"✅ Ваша заявка на вывод **{amount} $** успешно выплачена! Проверьте реквизиты.", parse_mode="Markdown")
        except:
            pass
    else:
        # Возвращаем баланс обратно воркеру при отказе
        users = load_data(USERS_FILE)
        if target_id in users:
            users[target_id]["balance"] += amount
            save_data(USERS_FILE, users)
            
        bot.edit_message_text(
            f"❌ **Заявка #{req_id} отклонена.** Средства возвращены на баланс воркера.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        try:
            bot.send_message(target_id, f"❌ Ваша заявка на вывод **{amount} $** была отклонена администратором. Средства возвращены на баланс.", parse_mode="Markdown")
        except:
            pass
            
    # Удаляем из активных заявок
    withdraws = [w for w in withdraws if w["req_id"] != req_id]
    save_data(WITHDRAW_FILE, withdraws)

# ==================== ЗАПУСК БОТА ====================
if __name__ == '__main__':
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("Ворк-бот успешно запущен!")
    bot.infinity_polling()
