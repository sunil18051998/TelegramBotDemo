import requests
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class PayPalPayment:
    def __init__(self):
        self.client_id = os.getenv("PAYPAL_CLIENT_ID")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
        self.env = os.getenv("PAYPAL_ENVIRONMENT")
        self.base_url = "https://api-m.sandbox.paypal.com" if self.env == "sandbox" else "https://api-m.paypal.com"
        self.access_token = self.get_access_token()

    def get_access_token(self) -> str:
        response = requests.post(
            f"{self.base_url}/v1/oauth2/token",
            auth=(self.client_id, self.client_secret),
            data={"grant_type": "client_credentials"},
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def create_payment_link(self, amount: float, currency: str, return_url: str, cancel_url: str, telegram_user_id: int) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency,
                    "value": str(amount)
                },
                "custom_id": str(telegram_user_id)
            }],
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url
            }
        }

        response = requests.post(f"{self.base_url}/v2/checkout/orders", json=payload, headers=headers)
        response.raise_for_status()
        links = response.json()["links"]
        for link in links:
            if link["rel"] == "approve":
                return link["href"]  # This is the PayPal payment link

        return None
