import asyncio
import logging
import time
from typing import Set, Dict, List
from telegram import Update
from telegram.ext import ContextTypes
from config import FREE_MESSAGE_LIMIT, MIN_SECONDS_BETWEEN_MESSAGES
from payment.paypal import PayPalPayment

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize PayPal payment handler
payment_handler = PayPalPayment()

# User tracking
user_last_message_time: Dict[int, float] = {}
user_message_count: Dict[int, int] = {}
chat_histories: Dict[int, List[Dict]] = {}
paid_users: Set[int] = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "Hey there! ❤️ Text me something sweet!\n\n"
        "You can upgrade to VIP for unlimited messages and special features!"
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribe command"""
    user_id = update.message.from_user.id
    
    # Get available plans
    plans = payment_handler.get_subscription_plans()
    plan_text = "\n".join([
        f"{i+1}. {plan['currency']} {plan['price']} - Monthly"
        for i, plan in enumerate(plans)
    ])
    
    await update.message.reply_text(
        f"Choose your subscription plan:\n\n{plan_text}\n\n"
        "Reply with the number of your choice to subscribe!"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    user_id = update.message.from_user.id
    message = update.message.text
    now = time.time()

    # Check if user is paid
    if user_id not in paid_users:
        count = user_message_count.get(user_id, 0)
        if count >= FREE_MESSAGE_LIMIT:
            await update.message.reply_text(
                "💕 You've reached your free limit. Subscribe to continue!"
            )
            return
        user_message_count[user_id] = count + 1

    # Check message rate limit
    if now - user_last_message_time.get(user_id, 0) < MIN_SECONDS_BETWEEN_MESSAGES:
        await update.message.reply_text("Slow down baby 😘")
        return

    user_last_message_time[user_id] = now

    # Process message with OpenAI (to be implemented)
    await update.message.reply_text("Processing your message...")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error("Unhandled error:", exc_info=context.error)
    if update and hasattr(update, 'message'):
        await update.message.reply_text("Oops! I'm having a moment. Try again later 💔")
