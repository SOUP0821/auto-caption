# AutoCaption

A modern video captioning application powered by OpenAI Whisper and Hunyuan MT Chimera for transcription and translation.

![AutoCaption](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Node](https://img.shields.io/badge/node-18+-green)

## Features

- 🎬 **Video Upload**: Drag & drop or browse for video files
- 🎤 **AI Transcription**: OpenAI Whisper (Tiny to Large V3 Turbo)
- 🌍 **Translation**: 18+ languages via Hunyuan MT Chimera
- ✏️ **Caption Editor**: Edit text and timing inline
- 📺 **Live Preview**: Captions displayed on video in real-time
- 💾 **SRT Export**: Download subtitles in standard format
- 🎨 **Modern UI**: Dark theme with turquoise accents
- ⚡ **GPU Acceleration**: CUDA support for fast processing
- 🚀 **Easy Setup**: Interactive installer handles all dependencies

## Quick Start

### Windows (Recommended)
1. Double-click `start.bat`
2. Follow the prompts to install any missing dependencies
3. The app will open at http://localhost:5173

### Alternative: PowerShell
```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

## What Gets Installed

When you first run the application, you'll be prompted to install:

| Component | Size | Required | Description |
|-----------|------|----------|-------------|
| Python packages | ~2GB | Yes | FastAPI, Transformers, PyTorch |
| FFmpeg | ~85MB | Yes | Video/audio processing |
| PyTorch CUDA | ~2.5GB | Optional | GPU acceleration (NVIDIA) |
| Whisper Model | ~3GB | Auto | Downloaded on first transcription |
| Translation Model | ~4.4GB | Auto | Downloaded on first translation |

**Note**: Whisper and Translation models download automatically when first used, or you can pre-download them from the Installer page.

## Requirements

- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **NVIDIA GPU** (optional, but recommended for faster processing)

## Manual Setup

If you prefer manual installation:

### 1. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# For GPU support (NVIDIA):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 2. Frontend
```bash
cd frontend
npm install
```

### 3. FFmpeg
- **Windows**: The setup script can install it for you, or download from https://ffmpeg.org/download.html
- **Mac**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

## Running

### Start Backend
```bash
cd backend
venv\Scripts\activate
python main.py
```

### Start Frontend
```bash
cd frontend
npm run dev
```

Open http://localhost:5173

## Usage

1. **Setup**: Complete the Installer if prompted
2. **Upload**: Drag & drop a video or click to browse
3. **Transcribe**: Select Whisper model and click "Transcribe"
4. **Edit**: Click any caption to edit the text
5. **Translate** (optional): Select languages and click "Translate"
6. **Export**: Download as SRT file

## Models

### Whisper (Transcription)
| Model | Parameters | Speed | Use Case |
|-------|------------|-------|----------|
| tiny | 39M | ⚡⚡⚡⚡ | Quick drafts |
| base | 74M | ⚡⚡⚡ | Basic accuracy |
| small | 244M | ⚡⚡ | Good balance |
| medium | 769M | ⚡ | High accuracy |
| large-v3-turbo | 809M | ⚡⚡ | Best speed/accuracy |
| large-v3 | 1550M | 🐢 | Maximum accuracy |

### Hunyuan MT Chimera (Translation)
- 7B parameters, Q4_K_M quantized
- Supports 33+ languages
- ~4.4GB model file

## Troubleshooting

### "Backend Not Available"
Start the backend server first:
```bash
cd backend && venv\Scripts\activate && python main.py
```

### "No GPU detected"
1. Click "Install CUDA PyTorch" in the Installer
2. Restart the application

### "FFmpeg not found"
Click "Install FFmpeg" in the Installer, or install manually

### Model download fails
- Check internet connection
- Ensure 10GB+ free disk space
- Try again later (HuggingFace servers may be busy)

## Project Structure

```
AutoCaption/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── config.py            # Configuration
│   ├── services/
│   │   ├── transcribe.py    # Whisper service
│   │   ├── translate.py     # Translation service
│   │   ├── installer.py     # Dependency manager
│   │   ├── projects.py      # Project storage
│   │   └── video.py         # FFmpeg service
│   ├── models/              # Downloaded models
│   └── projects/            # Saved projects
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Installer.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── Editor.jsx
│   │   ├── App.jsx
│   │   └── index.css
│   └── package.json
├── start.bat                # Windows launcher
├── setup.ps1                # PowerShell setup
└── README.md
```

## License

MIT
