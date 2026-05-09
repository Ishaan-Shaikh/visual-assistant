"""
backends/base.py
----------------
Abstract interface that every vision backend must implement.
Adding a new model = subclassing this and implementing describe().
"""

from abc import ABC, abstractmethod
from PIL import Image


class BaseBackend(ABC):
    """Common interface for all vision backends."""

    @abstractmethod
    def describe(self, image: Image.Image, mode: str = "short") -> str:
        """
        Generate a text description of the given image.

        Args:
            image: PIL Image in RGB mode.
            mode:  'short'    → 1-2 sentence summary.
                   'detailed' → full scene breakdown.

        Returns:
            Caption string.
        """

    # ── Shared prompt templates ───────────────────────────────────────────
    PROMPTS = {
        "short": "Describe this image in one or two sentences.",
        "detailed": (
            "Describe this image in detail. "
            "Include the main objects, any visible text or numbers, "
            "colors, setting, and what is happening in the scene."
        ),
    }