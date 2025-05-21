import asyncio
import logging
import os
import platform
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)

from config import WEBHOOK_PATH, WEBHOOK_URL, WEBHOOK_SECRET, BOT_TOKEN, OPENAI_API_KEY, RENDER_EXTERNAL_URL
from handlers.bot_handlers import start, subscribe, echo, error_handler
from utils.utils import OpenAIHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Initialize OpenAI handler
openai_handler = OpenAIHandler(api_key=OPENAI_API_KEY)

# FastAPI app and Telegram bot
app = FastAPI()
bot_app = ApplicationBuilder().token(TOKEN).build()

# Health check
@app.api_route("/healthz", methods=["GET", "HEAD"])
async def health_check(request: Request):
    return JSONResponse(content={"status": "ok"}, status_code=200)

# Message limits and user tracking
user_last_message_time = {}
user_message_count = {}
chat_histories = {}
paid_users = set()

MIN_SECONDS_BETWEEN_MESSAGES = 3
FREE_MESSAGE_LIMIT = 10000 # Reduce it later
PAYMENT_LINK = "https://yourwebsite.com/subscribe"

# Register handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("subscribe", subscribe))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
bot_app.add_error_handler(error_handler)

# Webhook handler
@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return JSONResponse(status_code=200)
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return JSONResponse(status_code=500)

# Lifecycle hooks
async def on_startup():
    await bot_app.bot.set_webhook(WEBHOOK_URL)
    logger.info("Bot started and webhook set")

async def on_shutdown():
    await bot_app.bot.delete_webhook()
    logger.info("Bot shutdown and webhook removed")

app.add_event_handler("startup", on_startup)
app.add_event_handler("shutdown", on_shutdown)

# Local dev entry point
if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
