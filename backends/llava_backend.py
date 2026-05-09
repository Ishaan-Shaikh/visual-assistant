"""
backends/llava_backend.py
-------------------------
Local backend: runs LLaVA-1.5-7b on-device using 4-bit NF4 quantization.

Requirements: torch, transformers, accelerate, bitsandbytes
Needs a CUDA GPU with ~6 GB VRAM (e.g. Colab T4, RTX 3060+).
"""

import torch
from PIL import Image
from transformers import (
    AutoProcessor,
    BitsAndBytesConfig,
    LlavaForConditionalGeneration,
)

from .base import BaseBackend

MODEL_ID = "llava-hf/llava-1.5-7b-hf"
MAX_NEW_TOKENS = {"short": 80, "detailed": 250}


class LlavaBackend(BaseBackend):
    """
    Uses LLaVA-1.5-7b loaded locally with 4-bit NF4 quantization.
    Fully offline after the first model download — no API key needed.
    """

    def __init__(self, model_id: str = MODEL_ID):
        print(f"Loading {model_id} in 4-bit mode … (first run takes a few minutes)")

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )

        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = LlavaForConditionalGeneration.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto",
        )
        self.model.eval()

        device = next(self.model.parameters()).device
        print(f"✅ LLaVA backend ready on: {device}")

    def describe(self, image: Image.Image, mode: str = "short") -> str:
        """Run local inference and return the caption."""
        if mode not in self.PROMPTS:
            raise ValueError(f"mode must be 'short' or 'detailed', got: {mode!r}")

        llava_prompt = (
            f"USER: <image>\nQuestion: {self.PROMPTS[mode]} Answer:\nASSISTANT:"
        )

        inputs = self.processor(
            text=llava_prompt,
            images=image.convert("RGB"),
            return_tensors="pt",
        ).to("cuda")

        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS[mode],
                do_sample=False,
                temperature=None,
                top_p=None,
                repetition_penalty=1.4,
            )

        new_tokens = output[0][inputs["input_ids"].shape[1]:]
        return self.processor.tokenizer.decode(
            new_tokens, skip_special_tokens=True
        ).strip()