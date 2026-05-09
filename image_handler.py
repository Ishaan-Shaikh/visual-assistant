"""
image_handler.py
----------------
Shared image utilities: load from disk or capture the screen.
"""

import os
import time

from PIL import Image

SUPPORTED = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def load_image(path: str) -> Image.Image:
    """Load an image from disk and return as RGB PIL Image."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image not found: {path}")
    if not path.lower().endswith(SUPPORTED):
        raise ValueError(f"Unsupported format. Supported: {SUPPORTED}")
    return Image.open(path).convert("RGB")


def find_images(directory: str) -> list[str]:
    """Return sorted list of supported image paths in a directory."""
    return [
        os.path.join(directory, f)
        for f in sorted(os.listdir(directory))
        if f.lower().endswith(SUPPORTED)
    ]


def capture_screen(countdown: int = 0) -> Image.Image:
    """
    Capture the full screen using mss.

    Args:
        countdown: Seconds to wait before capturing (lets user switch windows).

    Returns:
        PIL Image of the screen in RGB mode.
    """
    if countdown > 0:
        for i in range(countdown, 0, -1):
            print(f"  Capturing in {i}s …", end="\r", flush=True)
            time.sleep(1)
        print(" " * 30, end="\r")  # clear line

    import mss

    with mss.mss() as sct:
        raw = sct.grab(sct.monitors[0])
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


def image_changed(
    img_a: Image.Image, img_b: Image.Image, threshold: float = 0.02
) -> bool:
    """
    Returns True if two screen captures differ meaningfully.
    Compares downscaled pixel means — cheap but effective for UI changes.

    Args:
        img_a, img_b: Two PIL Images to compare.
        threshold:    Fraction of max pixel value (0–1) considered a change.
    """
    import numpy as np

    small_a = img_a.resize((128, 72)).convert("L")
    small_b = img_b.resize((128, 72)).convert("L")
    diff = abs(
        sum(sum(row) for row in list(small_a.getdata()))
        - sum(sum(row) for row in list(small_b.getdata()))
    ) / (128 * 72 * 255)
    return diff > threshold