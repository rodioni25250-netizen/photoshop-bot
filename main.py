import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Веб-сервер для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8705425815:AAETJ22L8ORvjxVXqu_VP_wUzodbY122-10"
ADMIN_ID = 8129509696
AVITO_REVIEWS_URL = "https://www.avito.ru/user/0fbd712dacdb0ef3d63451ac32d33597/profile?src=sharing"
# ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Отзывы на Авито", url=AVITO_REVIEWS_URL)],
        [InlineKeyboardButton("📸 Заказать обработку", callback_data="make_order")]
    ])
    await update.message.reply_text(
        "Привет! Я помогу вам сделать заказ на обработку и редактирование фото.\n\n"
        "Вы можете посмотреть отзывы наших клиентов на Авито или оформить заказ прямо здесь:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "make_order":
        context.user_data['awaiting_order'] = True
        await query.message.reply_text(
            "Отправьте фотографию и напишите в описании (или отдельным сообщением), что именно нужно сделать."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""

    # Если пользователь нажала кнопку меню "Отзывы"
    if "Отзывы" in text:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ Перейти к отзывам на Авито", url=AVITO_REVIEWS_URL)]
        ])
        await update.message.reply_text(
            "Нажмите на кнопку ниже, чтобы посмотреть отзывы реальных клиентов на Авито:",
            reply_markup=reply_markup
        )
        return

    # Если пользователь оформляет заказ
    if context.user_data.get('awaiting_order'):
        caption = update.message.caption or update.message.text or "Без описания"
        text_for_admin = (
            f"📥 **Новый заказ!**\n\n"
            f"👤 **От:** {user.full_name} (@{user.username if user.username else 'нет_юзернейма'})\n"
            f"🆔 **ID:** `{user.id}`\n\n"
            f"📝 **Текст/Описание:** {caption}"
        )

        if update.message.photo:
            photo_file_id = update.message.photo[-1].file_id
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file_id, caption=text_for_admin, parse_mode="Markdown")
        else:
            await context.bot.send_message(chat_id=ADMIN_ID, text=text_for_admin, parse_mode="Markdown")
        
        await update.message.reply_text("Спасибо! Ваш заказ принят и отправлен мастеру. Скоро с вами свяжутся!")
        context.user_data['awaiting_order'] = False
    else:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ Посмотреть отзывы на Авито", url=AVITO_REVIEWS_URL)],
            [InlineKeyboardButton("📸 Заказать обработку", callback_data="make_order")]
        ])
        await update.message.reply_text(
            "Для оформления заказа или просмотра отзывов воспользуйтесь кнопками ниже или нажмите /start:",
            reply_markup=reply_markup
        )

def main():
    threading.Thread(target=run_web, daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
    
