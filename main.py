import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler
from dotenv import load_dotenv
import os

# Подгружаем переменные из .env
load_dotenv()


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

FIRST_MASSAGE, GET_NAME = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_user.id, 
    text=f"Привет, {update.effective_user.first_name}, хочешь гайд!")
    return FIRST_MASSAGE



if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()
    conv_handler = ConversationHandler(entry_points=[CommandHandler('start', start)], states={FIRST_MASSAGE:}, fallbacks=[])
    
    application.add_handler(conv_handler)
    
    application.run_polling()