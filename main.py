import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ВАШ ТОКЕН УЖЕ ВСТАВЛЕН
BOT_TOKEN = "8705425815:AAETJ22L8ORvjxVXqu_VP_wUzodbY122-10"

# ⚠️ ВСТАВЬТЕ СЮДА ВАШ TELEGRAM ID (число из бота @userinfobot)
# Пример: ADMIN_ID = 123456789
ADMIN_ID = 8705425815  

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# =========================
# НАСТРОЙКИ БОТА
# =========================

SERVICES = {
    "retouch": {
        "name": "✨ Ретушь фотографии",
        "price": "от 300 ₽",
        "description": "Удаление недостатков кожи, коррекция лица, цвета и света."
    },
    "restore": {
        "name": "♻️ Реставрация фото",
        "price": "от 500 ₽",
        "description": "Восстановление старых, повреждённых и выцветших фотографий."
    },
    "background": {
        "name": "🎨 Замена фона",
        "price": "от 300 ₽",
        "description": "Удаление старого фона и создание нового."
    },
    "remove": {
        "name": "🧹 Удаление объектов",
        "price": "от 300 ₽",
        "description": "Удаление людей, предметов, проводов и других объектов."
    },
    "quality": {
        "name": "🔍 Улучшение качества",
        "price": "от 300 ₽",
        "description": "Улучшение резкости, цвета и общего качества изображения."
    },
}

# =========================
# КЛАВИАТУРА
# =========================

def main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🖼 Заказать обработку", callback_data="services")
        ],
        [
            InlineKeyboardButton("💰 Прайс", callback_data="price"),
            InlineKeyboardButton("💬 Консультация", callback_data="ai")
        ],
        [
            InlineKeyboardButton("⭐ Отзывы", callback_data="reviews")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def services_keyboard():
    keyboard = []
    for service_id, service in SERVICES.items():
        keyboard.append([
            InlineKeyboardButton(service["name"], callback_data=f"service:{service_id}")
        ])
    keyboard.append([
        InlineKeyboardButton("⬅️ Назад", callback_data="back")
    ])
    return InlineKeyboardMarkup(keyboard)

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    text = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Я помогу оформить заказ на обработку фотографии в Photoshop.\n\n"
        "📸 Ретушь\n"
        "♻️ Реставрация\n"
        "🎨 Замена фона\n"
        "🧹 Удаление объектов\n"
        "🔍 Улучшение качества\n\n"
        "Выберите нужный раздел:"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )

# =========================
# КНОПКИ
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back":
        await query.edit_message_text("Главное меню:", reply_markup=main_keyboard())
        return

    if data == "services":
        await query.edit_message_text(
            "🖼 <b>Выберите услугу:</b>",
            parse_mode="HTML",
            reply_markup=services_keyboard()
        )
        return

    if data == "price":
        text = "💰 <b>Прайс на услуги:</b>\n\n"
        for service in SERVICES.values():
            text += (
                f"{service['name']}\n"
                f"Стоимость: {service['price']}\n"
                f"{service['description']}\n\n"
            )
        text += (
            "💡 Точная стоимость зависит от сложности фотографии.\n"
            "Пришлите фото — я помогу определить примерную цену."
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🖼 Отправить фото", callback_data="services")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
            ])
        )
        return

    if data == "reviews":
        await query.edit_message_text(
            "⭐ <b>Отзывы клиентов</b>\n\n"
            "Здесь будут размещаться отзывы и примеры работ.\n"
            "После выполнения заказа вы также сможете оставить отзыв!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
            ])
        )
        return

    if data == "ai":
        await query.edit_message_text(
            "💬 <b>Консультация с мастером</b>\n\n"
            "Просто отправьте фотографию с описанием того, что хотите сделать, и мастер свяжется с вами напрямую!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🖼 Выбрать услугу и фото", callback_data="services")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
            ])
        )
        return

    if data.startswith("service:"):
        service_id = data.split(":")[1]
        service = SERVICES.get(service_id)

        if not service:
            return

        context.user_data["service"] = service["name"]

        await query.edit_message_text(
            f"✅ <b>{service['name']}</b>\n\n"
            f"{service['description']}\n\n"
            f"💰 Цена: {service['price']}\n\n"
            "📸 Теперь отправьте фотографию, которую нужно обработать.",
            parse_mode="HTML"
        )
        return

# =========================
# ФОТО
# =========================

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    service = context.user_data.get("service", "Не выбрана")

    caption = (
        "📥 <b>НОВАЯ ЗАЯВКА</b>\n\n"
        f"👤 Клиент: {update.effective_user.full_name}\n"
        f"🆔 Telegram ID: {update.effective_user.id}\n"
        f"🔗 Юзернейм: @{update.effective_user.username or 'нет_юзернейма'}\n"
        f"🔧 Услуга: {service}\n\n"
        "Фото прикреплено выше."
    )

    if ADMIN_ID and ADMIN_ID != 0:
        try:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo.file_id,
                caption=caption,
                parse_mode="HTML"
            )
        except Exception as e:
            print("Ошибка отправки админу:", e)

    context.user_data["waiting_description"] = True

    await update.message.reply_text(
        "📸 Фото получил!\n\n"
        "Теперь напишите, что именно нужно сделать с фотографией.\n\n"
        "Например:\n"
        "«Убрать человека справа, сделать фон белым и немного улучшить качество»"
    )

# =========================
# ТЕКСТ
# =========================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if context.user_data.get("waiting_description"):
        service = context.user_data.get("service", "Не указана")
        user = update.effective_user

        admin_text = (
            "📝 <b>ДОПОЛНЕНИЕ К ЗАКАЗУ</b>\n\n"
            f"👤 Клиент: {user.full_name}\n"
            f"🆔 ID: {user.id}\n"
            f"🔧 Услуга: {service}\n\n"
            f"💬 Задание:\n{text}"
        )

        if ADMIN_ID and ADMIN_ID != 0:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=admin_text,
                    parse_mode="HTML"
                )
            except Exception as e:
                print("Ошибка отправки админу:", e)

        context.user_data["waiting_description"] = False

        await update.message.reply_text(
            "✅ <b>Заявка отправлена мастеру!</b>\n\n"
            "Я передал фотографию и ваше описание.\n"
            "Мастер свяжется с вами для уточнения деталей.",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )
        return

    await update.message.reply_text(
        "Выберите услугу в меню:",
        reply_markup=main_keyboard()
    )

# =========================
# ЗАПУСК
# =========================

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Бот успешно запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
      
