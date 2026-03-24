import os
import time
import base64
import mss
import subprocess
import wave
import tempfile
from piper.voice import PiperVoice
from PIL import Image
from groq import Groq
from dotenv import load_dotenv
import io

import re

def clean_text(text):
    """Remove markdown formatting and fix punctuation for natural TTS."""
    # remove bold and italic markers
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    # remove headers
    text = re.sub(r'#{1,6}\s*', '', text)
    # remove inline code backticks
    text = re.sub(r'`([^`]*)`', r'\1', text)
    # remove triple backtick code blocks entirely
    text = re.sub(r'```.*?```', 'code block', text, flags=re.DOTALL)
    # remove URLs
    text = re.sub(r'http\S+', '', text)
    # remove bullet points
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    # replace multiple spaces
    text = re.sub(r' +', ' ', text)
    # replace long pauses at full stops — add comma instead for shorter pause
    text = re.sub(r'\.(\s)', r',\1', text)
    # strip leading/trailing whitespace
    return text.strip()

# --- Load API key ---
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file")

# --- Setup Groq client ---
client = Groq(api_key=API_KEY)
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# --- Setup Piper TTS (loaded once at startup) ---
print("Loading Piper voice model...")
VOICE = PiperVoice.load(
    "voices/en_US-ljspeech-high.onnx",
    config_path="voices/en_US-ljspeech-high.onnx.json"
)
print("✅ Voice model loaded")


# --- State ---
state = {
    "mode": "short",
    "slow": False,
    "running": True,
    "last_caption": None,
    "last_image_hash": None,
    "auto": False,
}

# ─────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────

def speak(text):
    """Speak text using preloaded Piper TTS voice."""
    if not text:
        return
    print(f"🔊 {text}")

    try:
        # write synthesized audio to a temp wav file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_path = f.name
            with wave.open(f, "wb") as wav_file:
                # length_scale: 1.0 = normal, 1.3 = slower
                length_scale = 1.3 if state["slow"] else 1.0
                VOICE.synthesize(
                    text,
                    wav_file,
                    length_scale=length_scale
                )

        # play with aplay (non-blocking check, clean output)
        subprocess.run(
            ["aplay", "-q", tmp_path],
            check=True
        )

        # cleanup temp file
        os.remove(tmp_path)

    except Exception as e:
        print(f"⚠️ TTS error: {e}")

def capture_screen():
    """Capture full screen and return as PIL Image."""
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img


def image_hash(img):
    """Simple hash to detect screen changes."""
    small = img.resize((32, 32)).convert("L")
    return hash(small.tobytes())


def image_to_base64(img):
    """Convert PIL image to base64 string for Groq API."""
    # resize if too large — keeps API calls fast
    max_size = (1280, 720)
    img.thumbnail(max_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def describe_image(img, mode="short"):
    """Send image to Groq and get description."""
    if mode == "short":
        prompt = "Describe this image in one or two sentences."
    else:
        prompt = (
            "Describe this image in detail. "
            "Include the main objects, any visible text or numbers, "
            "colors, setting, and what is happening in the scene."
        )

    image_data = image_to_base64(img)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        max_tokens=100 if mode == "short" else 300,
    )

    return response.choices[0].message.content.strip()


def do_describe(delay=5):
    """Capture screen after delay, describe it, and speak."""
    if delay > 0:
        print(f"⏱️ Capturing in {delay} seconds — switch to your window now...")
        for i in range(delay, 0, -1):
            print(f"  {i}...")
            time.sleep(1)

    print(">>>> Capturing screen...")
    img = capture_screen()
    label = "short" if state["mode"] == "short" else "detailed"
    print(f">>>> Generating {label} description...")
    try:
        caption = describe_image(img, mode=state["mode"])
        state["last_caption"] = caption
        state["last_image_hash"] = image_hash(img)
        print(f"\n>>>> → {caption}\n")
        speak(caption)
    except Exception as e:
        print(f">>>> API error: {e}")


def do_repeat():
    """Repeat last caption."""
    if state["last_caption"]:
        print(f">>>> → {state['last_caption']}\n")
        speak(state["last_caption"])
    else:
        print(">>>> Nothing to repeat yet.")


def do_toggle_mode():
    """Toggle between short and detailed mode."""
    state["mode"] = "detailed" if state["mode"] == "short" else "short"
    msg = f"Mode switched to {state['mode']}"
    print(f">>>> {msg}")
    speak(msg)


def do_toggle_slow():
    """Toggle slow/fast speech."""
    state["slow"] = not state["slow"]
    status = "slow" if state["slow"] else "normal"
    msg = f"Speech speed set to {status}"
    print(f">>>> {msg}")
    speak(msg)


def auto_watch(interval=5):
    """
    Continuously watch screen every interval seconds.
    Only describes if screen has changed.
    """
    print(f">>>> Auto watch active — checking every {interval}s.")
    print("Press Ctrl+C to stop auto watch.")
    while state["auto"]:
        try:
            img = capture_screen()
            current_hash = image_hash(img)

            if current_hash != state["last_image_hash"]:
                print("🔍 Screen change detected!")
                try:
                    caption = describe_image(img, mode=state["mode"])
                    state["last_caption"] = caption
                    state["last_image_hash"] = current_hash
                    print(f"📝 → {caption}\n")
                    speak(caption)
                except Exception as e:
                    print(f">>>> API error: {e}")
            else:
                print("⏸>>>> No change, skipping...")

            time.sleep(interval)

        except KeyboardInterrupt:
            state["auto"] = False
            print("\n>>>> Auto watch stopped.")
            break


# ─────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────

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

COMMANDS = {
    'd': do_describe,
    'r': do_repeat,
    'm': do_toggle_mode,
    'w': do_toggle_slow,
}

if __name__ == "__main__":
    print(MENU)
    speak("Visual Assistant ready. Press D to describe your screen.")

    while state["running"]:
        try:
            key = input("Command: ").strip().lower()

            if not key:
                continue
            elif key == 'a':
                do_toggle_auto = not state["auto"]
                state["auto"] = do_toggle_auto
                status = "ON" if state["auto"] else "OFF"
                msg = f"Auto watch {status}"
                print(f">>>> {msg}")
                speak(msg)
                if state["auto"]:
                    auto_watch(interval=5)
            elif key == 'q':
                speak("Goodbye")
                print(">>>> Goodbye!")
                state["running"] = False
            elif key in COMMANDS:
                COMMANDS[key]()
            else:
                print(f">>>> Unknown command '{key}'. Valid: D, R, M, W, A, Q")

        except KeyboardInterrupt:
            speak("Goodbye")
            print("\n>>>> Interrupted. Goodbye!")
            break