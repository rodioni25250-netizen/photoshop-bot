import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from groq import Groq

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8705425815:AAFrl0KCx8qtxOUHRgvOUCNtrnAJCxCybyI"
ADMIN_ID = 8129509696
AVITO_REVIEWS_URL = "https://www.avito.ru/user/0fbd712dacdb0ef3d63451ac32d33597/profile?src=sharing"

GROQ_API_KEY = "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"
# ------------------

client = Groq(api_key=GROQ_API_KEY)

def ask_ai(prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024,
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Groq Error: {e}")
        return "Произошла ошибка при обращении к ИИ. Попробуйте чуть позже."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Отзывы на Авито", url=AVITO_REVIEWS_URL)],
        [InlineKeyboardButton("📸 Заказать обработку", callback_data="make_order")],
        [InlineKeyboardButton("🤖 Задать вопрос ИИ", callback_data="ask_ai")]
    ])
    await update.message.reply_text("Привет! Выберите нужное действие ниже:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "make_order":
        context.user_data['state'] = 'awaiting_order'
        await query.message.reply_text("Отправьте фото и напишите, что нужно сделать.")
    elif query.data == "ask_ai":
        context.user_data['state'] = 'awaiting_ai_question'
        await query.message.reply_text("🤖 **Режим ИИ активирован!**\n\nНапишите ваш вопрос:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""
    state = context.user_data.get('state')

    if state == 'awaiting_ai_question':
        if not update.message.text:
            await update.message.reply_text("Отправьте текстовый вопрос для ИИ.")
            return
            
        wait_msg = await update.message.reply_text("🤔 ИИ генерирует ответ...")
        ai_response = ask_ai(text)
        await wait_msg.delete()
        await update.message.reply_text(f"🤖 **Ответ ИИ:**\n\n{ai_response}")
        context.user_data['state'] = None
        return

    if state == 'awaiting_order':
        caption = update.message.caption or update.message.text or "Без описания"
        text_for_admin = (
            f"📥 **Новый заказ!**\n\n"
            f"👤 **От:** {user.full_name} (@{user.username if user.username else 'нет_юзернейма'})\n"
            f"🆔 **ID:** `{user.id}`\n\n"
            f"📝 **Текст:** {caption}"
        )

        if update.message.photo:
            photo_file_id = update.message.photo[-1].file_id
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file_id, caption=text_for_admin, parse_mode="Markdown")
        else:
            await context.bot.send_message(chat_id=ADMIN_ID, text=text_for_admin, parse_mode="Markdown")
        
        await update.message.reply_text("Спасибо! Ваш заказ принят и отправлен мастеру.")
        context.user_data['state'] = None
        return

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Посмотреть отзывы на Авито", url=AVITO_REVIEWS_URL)],
        [InlineKeyboardButton("📸 Заказать обработку", callback_data="make_order")],
        [InlineKeyboardButton("🤖 Задать вопрос ИИ", callback_data="ask_ai")]
    ])
    await update.message.reply_text("Воспользуйтесь кнопками ниже или нажмите /start:", reply_markup=reply_markup)

def main():
    threading.Thread(target=run_web, daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
    
