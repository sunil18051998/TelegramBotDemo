import logging
from typing import List, Dict
from openai import OpenAI, OpenAIError
from config import OPENAI_API_KEY
import asyncio

logger = logging.getLogger(__name__)

class OpenAIHandler:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = "gpt-4o-mini"  # Default model
        self.max_retries = 3
        self.timeout = 30  # seconds

    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate response using OpenAI API"""
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=150,
                    timeout=self.timeout
                )
                return response.choices[0].message.content.strip()
            except OpenAIError as e:
                logger.error(f"OpenAI API error (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Failed to generate response after {self.max_retries} attempts")
                await asyncio.sleep(1)  # Wait before retrying
            except Exception as e:
                logger.error(f"Unexpected error in OpenAI handler: {str(e)}")
                raise Exception("An unexpected error occurred while generating the response")

    def set_model(self, model: str):
        """Set the model to use for generation"""
        self.model = model

# Initialize the handler once
openai_handler = OpenAIHandler()
