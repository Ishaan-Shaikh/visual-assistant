"""
benchmark.py
------------
Measures inference latency across a set of images for any backend.
Useful for comparing groq vs local speed on your hardware.
"""

import time

from PIL import Image


def measure_latency(
    image_paths: list[str],
    backend,
    mode: str = "detailed",
) -> dict:
    """
    Run inference on each image and collect timing stats.
    Each image gets one warm-up call (not counted) then one timed call.

    Args:
        image_paths: List of image file paths.
        backend:     Any loaded vision backend.
        mode:        Caption mode passed to backend.describe().

    Returns:
        Dict with keys: latencies, mean, min, max, std.
    """
    latencies = []
    n = len(image_paths)

    for idx, path in enumerate(image_paths, 1):
        image = Image.open(path).convert("RGB")

        # Warm-up (not timed)
        backend.describe(image, mode=mode)

        # Timed run
        t0 = time.perf_counter()
        backend.describe(image, mode=mode)
        elapsed = time.perf_counter() - t0

        latencies.append(elapsed)
        print(f"  [{idx}/{n}] {path}  →  {elapsed:.2f}s")

    mean = sum(latencies) / len(latencies)
    mn   = min(latencies)
    mx   = max(latencies)
    std  = (sum((x - mean) ** 2 for x in latencies) / len(latencies)) ** 0.5

    stats = {"latencies": latencies, "mean": mean, "min": mn, "max": mx, "std": std}

    print(f"\n  Mean : {mean:.2f}s")
    print(f"  Min  : {mn:.2f}s")
    print(f"  Max  : {mx:.2f}s")
    print(f"  Std  : {std:.2f}s")
    return stats