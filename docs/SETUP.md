# Setup

## Prerequisites

- Windows with ffmpeg already installed via `winget install Gyan.FFmpeg` (this
  machine has it at
  `C:\Users\<you>\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin`).
  The backend resolves ffmpeg/ffprobe automatically (PATH, then this winget
  install location, then `FFMPEG_BINARY`/`FFPROBE_BINARY` env vars), so you do
  not need to add it to PATH yourself.
- Python 3.13+
- Node.js 24+
- NVIDIA GPU + driver (optional, for NVENC encoding and CUDA faster-whisper)

## Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Git Bash on Windows
pip install -r requirements.txt

# GPU-accelerated faster-whisper needs these CUDA libraries:
pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"

# sanity-check ffmpeg/NVENC/libass/faster-whisper resolution
python ../scripts/check_env.py
```

Run the API:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/api/health` and `http://localhost:8000/api/env-check`.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`. The home page calls the backend health check
endpoint and displays the result.

## Environment variables

- `NEXT_PUBLIC_API_BASE_URL` (frontend, optional) - overrides the backend base
  URL, defaults to `http://localhost:8000`.
- `FFMPEG_BINARY` / `FFPROBE_BINARY` (backend, optional) - explicit paths to
  the ffmpeg/ffprobe executables, used only if PATH and the winget install
  location can't be resolved automatically.
