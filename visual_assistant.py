"""
visual_assistant.py
-------------------
Main entry point for the Visual Assistant.

Usage:
  # Cloud backend (Groq API, fast, needs API key)
  python visual_assistant.py --backend groq

  # Local backend (LLaVA-1.5-7b, offline, needs GPU)
  python visual_assistant.py --backend local

  # Change TTS engine
  python visual_assistant.py --backend groq --tts gtts

  # Describe an image file instead of the screen
  python visual_assistant.py --backend groq --image photo.jpg

  # Run latency benchmark
  python visual_assistant.py --backend local --benchmark --image-dir ./images
"""

import argparse
import sys
import threading
import time

from image_handler import capture_screen, image_changed, load_image, find_images
from backends import load_backend
from tts import load_tts
from benchmark import measure_latency


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Visual Assistant — AI screen description for visually impaired users."
    )
    p.add_argument(
        "--backend", choices=["groq", "local"], default="groq",
        help="Vision backend: 'groq' (cloud, fast) or 'local' (offline LLaVA). Default: groq"
    )
    p.add_argument(
        "--tts", choices=["piper", "gtts"], default="piper",
        help="TTS engine: 'piper' (offline, Linux) or 'gtts' (online, cross-platform). Default: piper"
    )
    p.add_argument(
        "--image", type=str, default=None,
        help="Path to a single image file. If omitted, captures the screen."
    )
    p.add_argument(
        "--benchmark", action="store_true",
        help="Run latency benchmark and exit."
    )
    p.add_argument(
        "--image-dir", type=str, default=".",
        help="Image directory for --benchmark. Default: current directory."
    )
    return p.parse_args()


# ── UI ────────────────────────────────────────────────────────────────────────

MENU = """
╔══════════════════════════════════════════════════╗
║   🦯 Visual Assistant for Visually Impaired      ║
╠══════════════════════════════════════════════════╣
║  D + Enter  →  Describe current screen           ║
║  R + Enter  →  Repeat last caption               ║
║  M + Enter  →  Toggle short/detailed mode        ║
║  W + Enter  →  Toggle slow/fast speech           ║
║  A + Enter  →  Toggle auto watch (5s interval)   ║
║  Q + Enter  →  Quit                              ║
╚══════════════════════════════════════════════════╝
"""

BACKEND_INFO = {
    "groq":  "☁️  Groq API  (Llama 4 Scout)",
    "local": "🖥️  Local GPU (LLaVA-1.5-7b 4-bit)",
}


# ── Main loop ─────────────────────────────────────────────────────────────────

class VisualAssistant:
    def __init__(self, backend, tts_engine, image_path: str | None = None):
        self.backend      = backend
        self.tts          = tts_engine
        self.image_path   = image_path   # None → use screen capture
        self.mode         = "short"      # 'short' | 'detailed'
        self.last_caption = ""
        self.auto_watch   = False
        self._watch_thread: threading.Thread | None = None

    # ── Actions ───────────────────────────────────────────────────────────

    def _get_image(self):
        if self.image_path:
            return load_image(self.image_path)
        return capture_screen(countdown=5)

    def describe(self) -> None:
        print(f"\n⏳ Capturing and describing ({self.mode} mode) …")
        try:
            image   = self._get_image()
            caption = self.backend.describe(image, mode=self.mode)
            self.last_caption = caption
            print(f"\n📝 {caption}\n")
            self.tts.speak(caption)
        except Exception as e:
            print(f"❌ Error: {e}")

    def repeat(self) -> None:
        if not self.last_caption:
            print("⚠️  No previous caption to repeat.")
            return
        print(f"\n📝 {self.last_caption}\n")
        self.tts.speak(self.last_caption)

    def toggle_mode(self) -> None:
        self.mode = "detailed" if self.mode == "short" else "short"
        print(f"✅ Mode → {self.mode}")

    def toggle_slow(self) -> None:
        self.tts.slow = not self.tts.slow
        speed = "slow" if self.tts.slow else "normal"
        print(f"✅ Speech speed → {speed}")
        self.tts.set_slow(self.tts.slow)

    def toggle_auto_watch(self) -> None:
        self.auto_watch = not self.auto_watch
        if self.auto_watch:
            print("✅ Auto-watch ON — will describe when screen changes (every 5s)")
            self._watch_thread = threading.Thread(
                target=self._watch_loop, daemon=True
            )
            self._watch_thread.start()
        else:
            print("✅ Auto-watch OFF")

    def _watch_loop(self) -> None:
        prev = capture_screen()
        while self.auto_watch:
            time.sleep(5)
            if not self.auto_watch:
                break
            current = capture_screen()
            if image_changed(prev, current):
                print("\n🔄 Screen changed — describing …")
                try:
                    caption = self.backend.describe(current, mode=self.mode)
                    self.last_caption = caption
                    print(f"\n📝 {caption}\n")
                    self.tts.speak(caption)
                except Exception as e:
                    print(f"❌ Error: {e}")
                prev = current

    # ── REPL ──────────────────────────────────────────────────────────────

    def run(self) -> None:
        print(MENU)
        key_map = {
            "d": self.describe,
            "r": self.repeat,
            "m": self.toggle_mode,
            "w": self.toggle_slow,
            "a": self.toggle_auto_watch,
        }
        while True:
            try:
                key = input("› ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                sys.exit(0)

            if key == "q":
                print("Goodbye!")
                sys.exit(0)
            elif key in key_map:
                key_map[key]()
            elif key:
                print(f"  Unknown key '{key}'. Use D/R/M/W/A/Q.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    print(f"\n🔧 Backend : {BACKEND_INFO.get(args.backend, args.backend)}")
    print(f"🔧 TTS     : {args.tts}")
    print(f"🔧 Mode    : short (toggle with M)\n")

    backend = load_backend(args.backend)
    tts     = load_tts(args.tts)

    # ── Benchmark mode ────────────────────────────────────────────────────
    if args.benchmark:
        paths = find_images(args.image_dir)
        if not paths:
            print(f"No images found in '{args.image_dir}'.")
            sys.exit(1)
        print(f"Benchmarking {len(paths)} image(s) with {args.backend} backend …\n")
        measure_latency(paths, backend)
        return

    # ── Interactive mode ──────────────────────────────────────────────────
    assistant = VisualAssistant(backend, tts, image_path=args.image)
    assistant.run()


if __name__ == "__main__":
    main()