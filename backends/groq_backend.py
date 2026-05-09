"""
backends/groq_backend.py
------------------------
Cloud backend: sends images to Llama 4 Scout via the Groq API.

Requirements: groq, python-dotenv
Set GROQ_API_KEY in your .env file or environment.
"""

import base64
import io
import os

from dotenv import load_dotenv
from PIL import Image

from .base import BaseBackend

load_dotenv()

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_TOKENS = {"short": 80, "detailed": 300}


class GroqBackend(BaseBackend):
    """
    Uses the Groq API (Llama 4 Scout) for vision inference.
    Fast, no local GPU required — needs an internet connection and API key.
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY not found. "
                "Add it to your .env file or set it as an environment variable.\n"
                "Get a free key at https://console.groq.com"
            )
        from groq import Groq
        self.client = Groq(api_key=api_key)
        print("✅ Groq backend ready (Llama 4 Scout)")

    def describe(self, image: Image.Image, mode: str = "short") -> str:
        """Send image to Groq API and return the caption."""
        if mode not in self.PROMPTS:
            raise ValueError(f"mode must be 'short' or 'detailed', got: {mode!r}")

        image_b64 = self._encode(image)
        response = self.client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS[mode],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                        {"type": "text", "text": self.PROMPTS[mode]},
                    ],
                }
            ],
        )
        return response.choices[0].message.content.strip()

    @staticmethod
    def _encode(image: Image.Image) -> str:
        """Encode a PIL Image to a base64 JPEG string."""
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode("utf-8")