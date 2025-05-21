from openai import OpenAI
from config import OPENAI_API_KEY

class OpenAIHandler:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    async def generate_response(self, messages: list[dict]) -> str:
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

# Initialize the handler once
openai_handler = OpenAIHandler()
