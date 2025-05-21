import asyncio
import logging
import platform
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import (
    WEBHOOK_PATH, WEBHOOK_URL, WEBHOOK_SECRET, BOT_TOKEN,
    FREE_MESSAGE_LIMIT, MIN_SECONDS_BETWEEN_MESSAGES
)
from handlers.bot_handlers import start, subscribe, echo, error_handler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Initialize bot
bot_app = ApplicationBuilder().token(BOT_TOKEN).build()

# Register handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("subscribe", subscribe))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
bot_app.add_error_handler(error_handler)

# Health check
@app.api_route("/healthz", methods=["GET", "HEAD"])
async def health_check(request: Request):
    return JSONResponse(content={"status": "ok"}, status_code=200)

# Webhook handler
@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        # Initialize the application if not already initialized
        if not bot_app.running:
            await bot_app.initialize()
            await bot_app.start()
            await bot_app.updater.start_polling()

        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return JSONResponse(content={"status": "ok"}, status_code=200)
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return JSONResponse(
            content={"error": "Internal server error", "details": str(e)},
            status_code=500
        )

# Lifecycle hooks
@app.on_event("startup")
async def on_startup():
    try:
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling()
        await bot_app.bot.set_webhook(WEBHOOK_URL)
        logger.info("Bot started and webhook set")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def on_shutdown():
    try:
        await bot_app.bot.delete_webhook()
        await bot_app.stop()
        await bot_app.shutdown()
        logger.info("Bot shutdown and webhook removed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
        raise

# Local dev entry point
if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
