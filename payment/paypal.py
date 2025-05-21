import os
from paypalrestsdk import Api, Order
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

# Initialize PayPal API
api = Api({
    'mode': os.getenv('PAYPAL_ENVIRONMENT', 'sandbox'),
    'client_id': os.getenv('PAYPAL_CLIENT_ID'),
    'client_secret': os.getenv('PAYPAL_CLIENT_SECRET')
})

class PayPalPayment:
    def __init__(self):
        self.api = api

    def create_order(self, plan_id: str, user_id: str) -> Dict:
        """Create a PayPal order for a subscription plan"""
        from config import SUBSCRIPTION_PLANS
        
        plan = SUBSCRIPTION_PLANS[plan_id]
        
        order = Order({
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": plan["currency"],
                    "value": str(plan["price"])
                },
                "description": f"{plan_id.title()} subscription"
            }],
            "application_context": {
                "brand_name": "LoveBot",
                "user_action": "PAY_NOW",
                "return_url": f"https://yourwebsite.com/success?user_id={user_id}",
                "cancel_url": f"https://yourwebsite.com/cancel?user_id={user_id}"
            }
        })

        if order.create():
            return {
                "status": "success",
                "order_id": order.id,
                "approve_link": order.links[1].href
            }
        else:
            raise Exception(f"Order creation failed: {order.error}")

    def capture_order(self, order_id: str) -> Dict:
        """Capture payment for an order"""
        order = Order.find(order_id)
        
        if order.capture():
            return {
                "status": "success",
                "capture_id": order.purchase_units[0].payments.captures[0].id
            }
        else:
            raise Exception(f"Order capture failed: {order.error}")

    def get_subscription_plans(self) -> List[Dict]:
        """Get available subscription plans"""
        from config import SUBSCRIPTION_PLANS
        return list(SUBSCRIPTION_PLANS.values())
