"""
tts/piper_tts.py
----------------
Offline TTS using Piper — fast, no internet needed.
Voice model files must be present in the voices/ folder.

Download from: https://github.com/rhasspy/piper/releases
  voices/en_US-ljspeech-high.onnx
  voices/en_US-ljspeech-high.onnx.json
"""

import subprocess
import tempfile
import os


VOICE_MODEL = os.path.join(
    os.path.dirname(__file__), "..", "voices", "en_US-ljspeech-high.onnx"
)


class PiperTTS:
    """
    Wraps the Piper TTS CLI for offline, privacy-friendly speech synthesis.
    Uses aplay for audio playback (Linux).
    """

    def __init__(self, voice_model: str = VOICE_MODEL, slow: bool = False):
        model_path = os.path.abspath(voice_model)
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Piper voice model not found at: {model_path}\n"
                "Download it from https://github.com/rhasspy/piper/releases "
                "and place it in the voices/ folder."
            )
        self.voice_model = model_path
        self.slow = slow

    def speak(self, text: str) -> None:
        """Synthesize text and play it with aplay."""
        if not text or not text.strip():
            print("⚠️  Nothing to speak.")
            return

        speed = "0.75" if self.slow else "1.0"
        print(f"🔊 Speaking: {text}")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            subprocess.run(
                ["piper", "--model", self.voice_model,
                 "--output_file", tmp_path, "--length_scale", speed],
                input=text.encode(),
                check=True,
                capture_output=True,
            )
            subprocess.run(["aplay", "-q", tmp_path], check=True)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def set_slow(self, slow: bool) -> None:
        self.slow = slow