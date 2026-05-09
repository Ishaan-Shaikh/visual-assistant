# 🦯 Visual Assistant

> AI-powered screen description tool for visually impaired users — with support for both **cloud** (Groq API) and **fully offline** (local GPU) vision backends.

---

## What it does

Visual Assistant captures your screen (or any image), generates a natural language description using an AI vision model, and reads it aloud. Designed to help visually impaired users understand what's on their screen with a simple keyboard-driven interface.

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

---

## Two backends, one interface

| | ☁️ Groq (cloud) | 🖥️ Local (LLaVA) |
|---|---|---|
| **Model** | Llama 4 Scout | LLaVA-1.5-7b |
| **Speed** | ~1–2s | ~17–21s |
| **Internet** | Required | Not required after download |
| **GPU** | Not required | ~6 GB VRAM |
| **API key** | Required | Not required |
| **Best for** | Daily use | Privacy, offline, research |

---

## Features

- 🖥️ **Screen capture** — captures your full screen on demand
- 🖼️ **Image file mode** — describe any image file with `--image`
- 🔍 **Short & detailed modes** — quick one-liner or full scene breakdown
- 🔁 **Repeat** — replay the last description without a new API call
- 🐢 **Slow speech mode** — slows down TTS for better clarity
- 👁️ **Auto-watch** — monitors screen every 5 seconds, speaks only when something changes
- 🔒 **Privacy-friendly** — Piper TTS runs fully offline; local backend needs no internet at all
- 📊 **Benchmarking** — measure and compare backend latency on your hardware

---

## Project structure

```
visual-assistant/
│
├── backends/
│   ├── __init__.py          # Factory: load_backend('groq' | 'local')
│   ├── base.py              # Abstract BaseBackend interface
│   ├── groq_backend.py      # ☁️  Groq API + Llama 4 Scout
│   └── llava_backend.py     # 🖥️  LLaVA-1.5-7b, 4-bit NF4 quantized
│
├── tts/
│   ├── __init__.py          # Factory: load_tts('piper' | 'gtts')
│   ├── piper_tts.py         # Offline TTS (Piper, high quality, Linux)
│   └── gtts_speaker.py      # Online TTS fallback (gTTS, cross-platform)
│
├── visual_assistant.py      # Main app & interactive REPL
├── image_handler.py         # Screen capture, image loading, change detection
├── benchmark.py             # Latency measurement for any backend
│
├── requirements.txt         # Core + Groq deps
├── requirements-local.txt   # Extra deps for --backend local
├── .env.example             # API key template
└── final_FYP.ipynb          # Original research notebook (Colab)
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Ishaan-Shaikh/visual-assistant.git
cd visual-assistant
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

**For the Groq (cloud) backend:**
```bash
pip install -r requirements.txt
```

**For the local LLaVA backend (needs CUDA GPU):**
```bash
pip install -r requirements.txt
pip install -r requirements-local.txt
```

### 4. Set up Piper TTS (for offline speech)

```bash
pip install piper-tts
mkdir voices
```

Download these two files from [Piper releases](https://github.com/rhasspy/piper/releases) into `voices/`:
- `en_US-ljspeech-high.onnx`
- `en_US-ljspeech-high.onnx.json`

> **Alternative:** Use `--tts gtts` to skip Piper and use Google TTS instead (requires internet).

### 5. Add your Groq API key (cloud backend only)

```bash
cp .env.example .env
# Edit .env and add your key from https://console.groq.com
```

---

## Usage

### Interactive screen description (cloud)
```bash
python visual_assistant.py --backend groq
```

### Interactive screen description (offline)
```bash
python visual_assistant.py --backend local
```

### Describe a specific image file
```bash
python visual_assistant.py --backend groq --image photo.jpg
python visual_assistant.py --backend local --image photo.jpg --tts gtts
```

### Use gTTS instead of Piper
```bash
python visual_assistant.py --backend groq --tts gtts
```

### Benchmark backend speed on your images
```bash
python visual_assistant.py --backend local --benchmark --image-dir ./images
```

---

## Benchmark results

> Tested on Google Colab T4 GPU (local backend) and Groq free tier (cloud backend).

| Metric | Groq (cloud) | LLaVA local |
|--------|-------------|-------------|
| Mean   | ~1.5s       | ~19s        |
| Min    | ~1.1s       | ~17s        |
| Max    | ~2.0s       | ~21s        |

*256 max new tokens, detailed mode. Your results will vary by hardware and network.*

---

## Dependencies

| Library | Purpose |
|---------|---------|
| `groq` | Groq API client (cloud backend) |
| `transformers` | LLaVA model loading (local backend) |
| `bitsandbytes` | 4-bit NF4 quantization (local backend) |
| `piper-tts` | Offline speech synthesis |
| `gTTS` | Online TTS fallback |
| `mss` | Fast cross-platform screen capture |
| `Pillow` | Image processing |
| `python-dotenv` | Load API key from `.env` |

---

## License

MIT