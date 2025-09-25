import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
import os

# Подгружаем переменные из .env
load_dotenv()


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

FIRST_MESSAGE, GET_NAME, GET_NUMBER, GET_CONSENT, GET_LEAD = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Да", "Нет"], ["Еще не знаю"]]
    markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
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
        input_field_placeholder="Выберите свое имя или напишите",
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
        await context.bot.send_message(
            chat_id=update.effective_user.id, text="Хотите получить гайд?"
        )
        return FIRST_MESSAGE


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
    number = update.effective_message.text
    context.user_data["number"] = number
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="Согласны ли вы на обработку ваших данных?",
    )
    return GET_CONSENT


async def get_consent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    consent = update.effective_message.text.strip().lower()
    context.user_data["consent"] = consent

    if consent == "да":
        await context.bot.send_message(
            chat_id=update.effective_user.id, text="Вот ваш гайд"
        )
        return GET_LEAD
    else:
        await context.bot.send_message(
            chat_id=update.effective_user.id, text="Хотите получить гайд?"
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
                    filters=filters.CONTACT & ~filters.COMMAND, 
                    callback=get_number),
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
