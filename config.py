import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# Payment Configuration
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_ENVIRONMENT = os.getenv("PAYPAL_ENVIRONMENT", "sandbox")  # sandbox or live

# Subscription Plans
SUBSCRIPTION_PLANS = {
    "monthly": {
        "price": 9.99,
        "currency": "USD",
        "features": [
            "Unlimited messages",
            "Priority response",
            "Custom emojis",
            "No cooldowns"
        ]
    },
    "yearly": {
        "price": 99.99,
        "currency": "USD",
        "features": [
            "Everything in Monthly",
            "20% discount",
            "Exclusive content",
            "Priority support"
        ]
    }
}

# Message Limits
FREE_MESSAGE_LIMIT = 4
MIN_SECONDS_BETWEEN_MESSAGES = 3

# Webhook Configuration
WEBHOOK_PATH = f"/webhook/{WEBHOOK_SECRET}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"
