"""
tts/gtts_speaker.py
-------------------
Cloud TTS fallback using Google Text-to-Speech (gTTS).
Requires internet. Used when Piper is not available or --tts gtts is passed.
"""

import os
import subprocess
import tempfile

from gtts import gTTS


class GTTSSpeaker:
    """Wraps gTTS for cross-platform speech synthesis."""

    def __init__(self, slow: bool = False):
        self.slow = slow

    def speak(self, text: str) -> None:
        """Synthesize text with gTTS and play via system audio."""
        if not text or not text.strip():
            print("⚠️  Nothing to speak.")
            return

        print(f"🔊 Speaking: {text}")
        tts = gTTS(text=text, lang="en", slow=self.slow)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            tts.save(tmp_path)
            _play(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def set_slow(self, slow: bool) -> None:
        self.slow = slow


def _play(path: str) -> None:
    """Play an audio file using the best available system command."""
    if os.name == "nt":
        os.startfile(path)
    elif subprocess.run(["which", "aplay"], capture_output=True).returncode == 0:
        subprocess.run(["aplay", "-q", path])
    elif subprocess.run(["which", "afplay"], capture_output=True).returncode == 0:
        subprocess.run(["afplay", path])
    else:
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]
        )