import asyncio
import logging
import platform
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram.error import TelegramError

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
        # Ensure application is initialized
        # if not bot_app.running:
        #     logger.info("Initializing bot application...")
        #     await bot_app.initialize()
        #     await bot_app.start()
        #     logger.info("Bot application initialized successfully")

        # Parse update
        try:
            data = await request.json()
            update = Update.de_json(data, bot_app.bot)
            logger.info("some updates...")
            await bot_app.process_update(update)
            return JSONResponse(content={"status": "ok"}, status_code=200)
        except TelegramError as e:
            logger.error(f"Telegram error while processing update: {str(e)}")
            return JSONResponse(
                content={"error": "Telegram error", "details": str(e)},
                status_code=500
            )
        except Exception as e:
            logger.error(f"Error processing update: {str(e)}")
            return JSONResponse(
                content={"error": "Update processing error", "details": str(e)},
                status_code=500
            )

    except Exception as e:
        logger.error(f"Critical webhook error: {str(e)}")
        return JSONResponse(
            content={"error": "Internal server error", "details": str(e)},
            status_code=500
        )

@app.post("/webhook/paypal")
async def paypal_webhook(request: Request):
    try:
        data = await request.json()
        event_type = data.get("event_type")
        logger.info(f"Received PayPal webhook: {event_type}")

        if event_type == "CHECKOUT.ORDER.APPROVED" or event_type == "PAYMENT.CAPTURE.COMPLETED":
            resource = data.get("resource", {})
            custom_id = resource.get("custom_id") or resource.get("purchase_units", [{}])[0].get("custom_id")

            if custom_id:
                telegram_user_id = int(custom_id)
                paid_users.add(telegram_user_id)
                logger.info(f"User {telegram_user_id} marked as paid via PayPal")

        return JSONResponse({"status": "ok"})

    except Exception as e:
        logger.error(f"Error in PayPal webhook: {str(e)}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


# Lifecycle hooks
@app.on_event("startup")
async def on_startup():
    try:
        logger.info("Starting bot application...")
        await bot_app.initialize()
        await bot_app.start()

        await asyncio.sleep(1)
        
        # Set webhook
        logger.info(f"Setting webhook to {WEBHOOK_URL}")
        result = await bot_app.bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook set result: {result}")

        logger.info("Bot started and webhook set ")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def on_shutdown():
    try:
        logger.info("Shutting down bot application...")
        #await bot_app.bot.delete_webhook()
        await bot_app.stop()
        await bot_app.shutdown()
        logger.info("Bot shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
        raise

# Local dev entry point
if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
