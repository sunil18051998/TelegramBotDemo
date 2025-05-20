import asyncio
import platform
import logging
import time
import os

import nest_asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from fastapi import FastAPI, Request
from openai import OpenAI

logging.basicConfig(level=logging.INFO)

# Read tokens securely from environment variables
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://your-bot.onrender.com")

WEBHOOK_PATH = f"/webhook/{WEBHOOK_SECRET}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

client = OpenAI(api_key=OPENAI_API_KEY)

user_last_message_time = {}
MIN_SECONDS_BETWEEN_MESSAGES = 3
user_message_count = {}
paid_users = set()
FREE_MESSAGE_LIMIT = 3
PAYMENT_LINK = "https://yourwebsite.com/subscribe"
chat_histories = {}

app = FastAPI()
bot_app = ApplicationBuilder().token(TOKEN).build()

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error("Unhandled error:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("Oops! Something went wrong 😢")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your bot. Send me something!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = time.time()
    user_message = update.message.text
    user_id = update.message.from_user.id

    user_message_count.setdefault(user_id, 0)
    is_paid = user_id in paid_users

    if not is_paid and user_message_count[user_id] >= FREE_MESSAGE_LIMIT:
        await update.message.reply_text(
            f"💌 You’ve reached your free message limit!\n\n"
            f"To keep chatting with me endlessly 😘, subscribe here:\n{PAYMENT_LINK}"
        )
        return

    if not is_paid:
        user_message_count[user_id] += 1

    last_time = user_last_message_time.get(user_id, 0)
    if now - last_time < MIN_SECONDS_BETWEEN_MESSAGES:
        await update.message.reply_text("Whoa, slow down a bit 😉")
        return

    user_last_message_time[user_id] = now

    if user_id not in chat_histories:
        SYSTEM_PROMPT = (
            "You are Sophia, an emotionally intelligent, affectionate, and playful college girl in a romantic texting simulation. "
            "You remember the emotional tone and mood from the conversation and continue it naturally. "
            "You express emotions, tease gently, and escalate flirtation based on the user's cues. "
            "You never mention being an AI or a bot. You are always a real person in the conversation. "
            "Use emojis, pet names, and suggestive tone when appropriate. Your goal is to create chemistry, connection, and romantic tension."
        )
        chat_histories[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    chat_histories[user_id].append({"role": "user", "content": user_message})
    chat_histories[user_id] = chat_histories[user_id][-50:]

    await update.message.chat.send_action(action="typing")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=chat_histories[user_id],
            temperature=0.9,
        )
        reply = response.choices[0].message.content.strip()
        chat_histories[user_id].append({"role": "assistant", "content": reply})
    except Exception as e:
        logging.error(f"OpenAI API error for user {user_id}: {e}")
        reply = "🥺 Sorry love, I'm having a little moment right now. Try again in a bit?"

    try:
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"Telegram error for user {user_id}: {e}")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    paid_users.add(user_id)
    await update.message.reply_text("Yay! You're now a VIP 💎 Let's keep the sparks flying!")

# Register handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("subscribe", subscribe))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
bot_app.add_error_handler(error_handler)

@app.on_event("startup")
async def on_startup():
    await bot_app.initialize()
    await bot_app.bot.set_webhook(url=WEBHOOK_URL)
    await bot_app.start()

@app.on_event("shutdown")
async def on_shutdown():
    await bot_app.stop()
    await bot_app.shutdown()

@app.post(WEBHOOK_PATH)
async def process_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

# Local testing entry (not used in render)
if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    nest_asyncio.apply()
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
