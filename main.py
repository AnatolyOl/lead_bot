import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from dotenv import load_dotenv
import os
from config.config import ADMIN_ID

# Подгружаем переменные из .env
load_dotenv()


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

FIRST_MESSAGE, GET_NAME, GET_NUMBER, GET_CONSENT, GET_LEAD, INLINE_BUTTON = range(6)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    keyboard = [["Да", "Нет"], ["Еще не знаю"]]
    markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=False,
        one_time_keyboard=True,
        input_field_placeholder="Выберите вариант ответа",
    )
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=f"Привет, {update.effective_user.first_name}, хотите гайд?",
        reply_markup=markup,
    )
    return FIRST_MESSAGE


async def get_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.effective_message.text
    keyboard = [[update.effective_user.first_name]]
    markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите имя или напишите",
    )
    context.user_data["answer"] = answer
    if answer == "Да":
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="Чтобы забрать гайд, напите свое имя",
            reply_markup=markup,
        )
        return GET_NAME
    else:
        keyboard = [[InlineKeyboardButton("Да", callback_data="yes")]]
        markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="Окей, тогда всё!",
            reply_markup=markup,
        )
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"[{update.effective_user.first_name}](tg://user?id={update.effective_user.id}), отказался от гайда",
        )
        return INLINE_BUTTON


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_message.text
    keyboard = [[KeyboardButton("Отправить номер телефона", request_contact=True)]]
    markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Нажми на кнопку",
    )
    context.user_data["name"] = name
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="Чтобы получить гайд, напишите номер телефона",
        reply_markup=markup,
    )
    return GET_NUMBER


async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.effective_message.contact.phone_number
    context.user_data["number"] = number
    print(context.user_data)
    keyboard = [["Да", "Нет"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="Согласны ли вы на обработку ваших данных?",
        reply_markup=markup,
    )
    
    return GET_CONSENT


async def get_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "yes":
        keyboard = [
            [
                InlineKeyboardButton("Да", callback_data="yes"),
                InlineKeyboardButton("Нет", callback_data="no"),
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Спасибо за ответ!", reply_markup=markup)


async def get_consent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Да", "Нет"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    consent = update.effective_message.text.strip().lower()
    context.user_data["consent"] = consent

    if consent == "да":
        await context.bot.send_message(
            chat_id=update.effective_user.id, text="Вот ваш гайд", reply_markup=markup
        )
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Новая заявка:\nИмя:{context.user_data['name']}\nТелефон:{context.user_data['number']}",
        )
        return GET_LEAD
    else:
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="Хотите получить гайд?",
            reply_markup=markup,
        )
        return FIRST_MESSAGE


async def get_lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lead = update.effective_message.text
    context.user_data["lead"] = lead
    await context.bot.send_message(
        chat_id=update.effective_user.id, text="Спасибо за ваш выбор!"
    )
    return FIRST_MESSAGE


if __name__ == "__main__":
    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FIRST_MESSAGE: [
                MessageHandler(
                    filters=filters.TEXT & ~filters.COMMAND,
                    callback=get_answer,
                )
            ],
            GET_NAME: [
                MessageHandler(
                    filters=filters.TEXT & ~filters.COMMAND,
                    callback=get_name,
                ),
            ],
            GET_NUMBER: [
                MessageHandler(
                    filters=filters.CONTACT & ~filters.COMMAND, callback=get_number
                ),
            ],
            INLINE_BUTTON: [
                CallbackQueryHandler(callback=get_inline_button, pattern="yes"),
                CallbackQueryHandler(callback=start, pattern="no"),
            ],
            GET_CONSENT: [
                MessageHandler(
                    filters=filters.TEXT & ~filters.COMMAND,
                    callback=get_consent,
                ),
            ],
            GET_LEAD: [
                MessageHandler(
                    filters=filters.TEXT & ~filters.COMMAND,
                    callback=get_lead,
                ),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    application.run_polling()
