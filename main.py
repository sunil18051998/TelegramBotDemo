import asyncio
import logging
import os
import platform
import time

import nest_asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Environment variables
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

WEBHOOK_PATH = f"/webhook/{WEBHOOK_SECRET}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

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
FREE_MESSAGE_LIMIT = 3
PAYMENT_LINK = "https://yourwebsite.com/subscribe"

# Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey there! ❤️ Text me something sweet!")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    paid_users.add(user_id)
    await update.message.reply_text("You're now a VIP 💖 Enjoy unlimited love!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    message = update.message.text
    now = time.time()

    if user_id not in paid_users:
        count = user_message_count.get(user_id, 0)
        if count >= FREE_MESSAGE_LIMIT:
            await update.message.reply_text(f"💕 You've reached your free limit. Subscribe here:\n{PAYMENT_LINK}")
            return
        user_message_count[user_id] = count + 1

    if now - user_last_message_time.get(user_id, 0) < MIN_SECONDS_BETWEEN_MESSAGES:
        await update.message.reply_text("Slow down baby 😘")
        return

    user_last_message_time[user_id] = now
    chat_histories.setdefault(user_id, [
        {"role": "system", "content": (
            "You are Sophia, a romantic and flirty college girl in a texting simulation. "
            "You never mention you're an AI or bot. Respond naturally, emotionally, and affectionately using pet names, emojis, and humor."
        )}
    ])
    chat_histories[user_id].append({"role": "user", "content": message})
    chat_histories[user_id] = chat_histories[user_id][-50:]

    try:
        await update.message.chat.send_action("typing")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=chat_histories[user_id],
            temperature=0.9,
        )
        reply = response.choices[0].message.content.strip()
        chat_histories[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("Oops! I'm having a moment. Try again later 💔")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Unhandled error:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("Something went wrong 😔")

# Register handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("subscribe", subscribe))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
bot_app.add_error_handler(error_handler)

# Webhook endpoint
@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

# Lifecycle hooks
@app.on_event("startup")
async def on_startup():
    await bot_app.initialize()
    await bot_app.bot.set_webhook(url=WEBHOOK_URL)
    await bot_app.start()

@app.on_event("shutdown")
async def on_shutdown():
    await bot_app.stop()
    await bot_app.shutdown()

# Local dev entry point
if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    nest_asyncio.apply()
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
