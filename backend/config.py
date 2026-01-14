"""Configuration settings for AutoCaption backend."""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
PROJECTS_DIR = BASE_DIR / "projects"
MODELS_DIR = BASE_DIR / "models"
TEMP_DIR = BASE_DIR / "temp"

# Create directories if they don't exist
PROJECTS_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# GGUF Translation model file name
TRANSLATION_MODEL_GGUF = "hunyuan-mt-chimera-7b-q4_k_m.gguf"

# CPU thread settings
CPU_COUNT = os.cpu_count() or 4
HALF_CPU_COUNT = max(CPU_COUNT // 2, 1)
