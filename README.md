# Visual Assistant

A voice-guided screen description tool designed to help visually impaired users understand what is on their screen. It captures the screen, sends it to an AI vision model, and reads the description aloud using a local text-to-speech engine.

---

## How It Works

1. Captures a screenshot of your screen
2. Sends it to **Llama 4 Scout** (via Groq API) for visual description
3. Speaks the description aloud using **Piper TTS** (offline, runs locally)

---

## Features

- 🖥️ **Screen capture** — captures your full screen on demand
- 🔍 **Short & detailed modes** — quick one-liner or full scene breakdown
- 🔁 **Repeat** — replay the last description without a new API call
- 🐢 **Slow speech mode** — slows down TTS for better clarity
- 👁️ **Auto watch** — monitors screen every 5 seconds and speaks only when something changes
- 🔒 **Privacy-friendly** — TTS runs fully offline via Piper

---

## Requirements

- Python 3.8+
- Linux (uses `aplay` for audio playback)
- A [Groq](https://console.groq.com) account and API key

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/Ishaan-Shaikh/visual-assistant.git
cd visual-assistant
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download the Piper voice model

Create a `voices/` folder and download the voice model files into it:

```bash
mkdir voices
```

Download these two files from [Piper's releases](https://github.com/rhasspy/piper/releases) and place them in the `voices/` folder:
- `en_US-ljspeech-high.onnx`
- `en_US-ljspeech-high.onnx.json`

### 5. Set up environment variables

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get your free API key at [console.groq.com](https://console.groq.com).

### 6. Run the assistant
```bash
python visual_assistant.py
```

---

## Usage

Once running, you will see this menu:

```
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
```

| Key | Action |
|-----|--------|
| `D` | Capture and describe the current screen |
| `R` | Repeat the last description |
| `M` | Toggle between short and detailed description |
| `W` | Toggle between normal and slow speech speed |
| `A` | Start/stop auto watch mode |
| `Q` | Quit the program |

> **Tip:** When you press `D`, you get a 5-second countdown so you can switch to the window you want described.

---

## Project Structure

```
visual-assistant/
│
├── visual_assistant.py     # Main application
├── requirements.txt        # Python dependencies
├── .env                    # Your API key (not tracked by git)
├── .env.example            # Example env file (safe to share)
└── voices/                 # Piper TTS model files (not tracked by git)
    ├── en_US-ljspeech-high.onnx
    └── en_US-ljspeech-high.onnx.json
```

---

## Dependencies

| Library | Purpose |
|--------|---------|
| `groq` | Groq API client for Llama 4 vision model |
| `piper-tts` | Offline text-to-speech engine |
| `mss` | Fast cross-platform screen capture |
| `Pillow` | Image processing and resizing |
| `python-dotenv` | Load API key from `.env` file |

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
