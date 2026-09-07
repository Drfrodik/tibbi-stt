"""Application configuration module.

Handles system paths, local FFmpeg, model parameters,
and output directories for the offline medical STT application.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Base directories
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

OUTPUT_DIR = BASE_DIR / "outputs"
SAMPLES_DIR = BASE_DIR / "samples"
MODELS_DIR = BASE_DIR / "models"

# Ensure runtime directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Register local FFmpeg & FFprobe if found on system
KNOWN_FFMPEG_PATHS = [
    r"C:\Users\frodo\AppData\Local\Programs\vidtsx-desktop\resources\ffmpeg",
    r"C:\Users\frodo\AppData\Local\Programs\vidtsx-desktop\resources\compositor",
    r"C:\Program Files\ffmpeg\bin",
    r"C:\ffmpeg\bin",
]

for p in KNOWN_FFMPEG_PATHS:
    if os.path.exists(p) and p not in os.environ.get("PATH", ""):
        os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")

# Default ASR settings
DEFAULT_MODEL_NAME = "small"  # Fast, accurate Azerbaijani medical speech on CPU
TARGET_LANGUAGE = "az"
TASK = "transcribe"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

# High-frequency universal medical seed prompt for initial Whisper conditioning
# NOTE: Must be a concise list of medical keywords/specialties, NOT full sentences,
# to prevent Whisper decoder from looping or echoing prompt tokens.
MEDICAL_SEED_PROMPT = (
    "Tibbi protokol. Revmatoloq, kardioloq, neyrocərrah, nevropatoloq, "
    "terapevt, cərrah, onkoloq, qastroenteroloq. Anamnez, laborator analizlər, USM, "
    "KT, MRT, rentgen, histologiya, diaqnoz, preoperativ hazırlıq, müalicə planı."
)
