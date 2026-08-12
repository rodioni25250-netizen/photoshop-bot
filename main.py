import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI

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
OPENAI_API_KEY = "Sk-proj-K_LRtzYFSCakoFfzB6QZ4Cp78JgcGww_horpAUu0BFLd3NYb4q18De37yNrAGjmZ_KMp9mXI9FT3BlbkFJvOIyaG7PGpGn4gZ_XfFA3w5Ss0FRvcKhHYPH1diNhdky7f81KSfztDTqCxpBd69XIVMrDgZ9kA"
# ------------------

client = OpenAI(api_key=OPENAI_API_KEY)

# Функция обращения к ChatGPT
def ask_ai(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI Error: {e}")
        return "Извините, произошла ошибка при обращении к ИИ. Попробуйте позже."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Отзывы на Авито", url=AVITO_REVIEWS_URL)],
        [InlineKeyboardButton("📸 Заказать обработку", callback_data="make_order")],
        [InlineKeyboardButton("🤖 Задать вопрос ИИ", callback_data="ask_ai")]
    ])
    await update.message.reply_text(
        "Привет! Я помогу вам сделать заказ на обработку фото, посмотреть отзывы или пообщаться с ИИ.\n\n"
        "Выберите нужное действие ниже:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "make_order":
        context.user_data['state'] = 'awaiting_order'
        await query.message.reply_text(
            "Отправьте фотографию и напишите в описании (или отдельным сообщением), что именно нужно сделать."
        )
    elif query.data == "ask_ai":
        context.user_data['state'] = 'awaiting_ai_question'
        await query.message.reply_text(
            "🤖 **Режим ИИ активирован!**\n\nНапишите ваш текстовый вопрос или задачу для нейросети:"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""
    state = context.user_data.get('state')

    # Режим ИИ (ответ на тексты)
    if state == 'awaiting_ai_question':
        if not update.message.text:
            await update.message.reply_text("Пожалуйста, отправьте текстовый вопрос для ИИ.")
            return
            
        wait_msg = await update.message.reply_text("🤔 ИИ генерирует ответ...")
        ai_response = ask_ai(text)
        await wait_msg.delete()
        await update.message.reply_text(f"🤖 **Ответ ИИ:**\n\n{ai_response}")
        context.user_data['state'] = None
        return

    # Режим оформления заказа
    if state == 'awaiting_order':
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
        context.user_data['state'] = None
        return

    # Главное меню
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Посмотреть отзывы на Авито", url=AVITO_REVIEWS_URL)],
        [InlineKeyboardButton("📸 Заказать обработку", callback_data="make_order")],
        [InlineKeyboardButton("🤖 Задать вопрос ИИ", callback_data="ask_ai")]
    ])
    await update.message.reply_text(
        "Воспользуйтесь кнопками ниже или нажмите /start:",
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
    
