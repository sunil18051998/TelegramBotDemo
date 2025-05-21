import os
from openai import OpenAI
from typing import Dict, List

class OpenAIHandler:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_response(self, messages: List[Dict]) -> str:
        """Generate response using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.9,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

def get_system_prompt() -> Dict:
    """Get the system prompt for chat conversations"""
    return {
        "role": "system",
        "content": (
            "You are Sophia, a romantic and flirty college girl in a texting simulation. "
            "You never mention you're an AI or bot. Respond naturally, emotionally, and affectionately using pet names, emojis, and humor."
        )
    }
