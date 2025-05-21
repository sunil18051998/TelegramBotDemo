import asyncio
import logging
import time
from typing import Set, Dict, List
from telegram import Update
from telegram.ext import ContextTypes
from config import FREE_MESSAGE_LIMIT, MIN_SECONDS_BETWEEN_MESSAGES
from payment.paypal import PayPalPayment
from utils.utils import get_system_prompt
from utils.ai_handler import openai_handler

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    try:
        user_id = update.effective_user.id
        # Initialize user tracking
        user_message_count[user_id] = 0
        chat_histories[user_id] = [get_system_prompt()]
        
        await update.message.reply_text(
            "Hey there! ❤️ Text me something sweet!\n\n"
            "You can upgrade to VIP for unlimited messages and special features!"
        )
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        await update.message.reply_text("Oops! Something went wrong. Please try again later.")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribe command"""
    try:
        user_id = update.message.from_user.id
        
        # Get available plans
        plans = payment_handler.get_subscription_plans()
        if not plans:
            await update.message.reply_text(
                "Sorry, subscription plans are currently unavailable. Please try again later."
            )
            return
            
        plan_text = "\n".join([
            f"{i+1}. {plan['currency']} {plan['price']} - Monthly"
            for i, plan in enumerate(plans)
        ])
        
        await update.message.reply_text(
            f"Choose your subscription plan:\n\n{plan_text}\n\n"
            "Reply with the number of your choice to subscribe!"
        )
    except Exception as e:
        logger.error(f"Error in subscribe command: {str(e)}")
        await update.message.reply_text("Sorry, there was an error processing your request. Please try again later.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    try:
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

        # Initialize chat history if needed
        if user_id not in chat_histories:
            chat_histories[user_id] = [get_system_prompt()]

        # Check message rate limit
        last_message_time = user_last_message_time.get(user_id, 0)
        if now - last_message_time < MIN_SECONDS_BETWEEN_MESSAGES:
            remaining_time = int(MIN_SECONDS_BETWEEN_MESSAGES - (now - last_message_time))
            await update.message.reply_text(
                f"Please wait {remaining_time} seconds before sending another message 😊"
            )
            return

        user_last_message_time[user_id] = now

        # Process message with OpenAI
        try:
            # Get chat history
            chat_history = chat_histories[user_id]
            
            # Add user message to history
            chat_history.append({"role": "user", "content": message})
            
            # Get response from OpenAI
            response = await openai_handler.generate_response(chat_history)
            
            # Add AI response to history
            chat_history.append({"role": "assistant", "content": response})
            
            # Update chat history (keep last 50 messages)
            chat_histories[user_id] = chat_history[-50:]
            
            # Send response
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Error processing OpenAI response: {str(e)}")
            await update.message.reply_text(
                "I'm having trouble processing your message right now. Please try again in a few moments."
            )
            
    except Exception as e:
        logger.error(f"Error in echo handler: {str(e)}")
        await update.message.reply_text("Oops! Something went wrong. Please try again later.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    try:
        logger.error("Unhandled error:", exc_info=context.error)
        if update and hasattr(update, 'message'):
            await update.message.reply_text(
                "I encountered an error processing your request. Please try again later."
            )
    except Exception as e:
        logger.error(f"Error in error handler: {str(e)}")

def cleanup_user_data(user_id: int):
    """Clean up user data when they stop using the bot"""
    if user_id in user_last_message_time:
        del user_last_message_time[user_id]
    if user_id in user_message_count:
        del user_message_count[user_id]
    if user_id in chat_histories:
        del chat_histories[user_id]
    if user_id in paid_users:
        paid_users.remove(user_id)
