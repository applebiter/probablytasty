"""
Configuration management for ProbablyTasty.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Settings file
SETTINGS_FILE = Path.home() / ".probablytasty" / "settings.json"

# Load user settings
def load_user_settings():
    """Load user settings from file."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load user settings: {e}")
    return {}

USER_SETTINGS = load_user_settings()

# Database
DATABASE_URL = f"sqlite:///{DATA_DIR / 'recipes.db'}"

# API Keys (prioritize user settings, fall back to .env)
OPENAI_API_KEY = USER_SETTINGS.get("openai_key") or os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = USER_SETTINGS.get("anthropic_key") or os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = USER_SETTINGS.get("google_key") or os.getenv("GOOGLE_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

# Ollama Configuration (prioritize user settings, fall back to .env)
OLLAMA_BASE_URL = USER_SETTINGS.get("ollama_url") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = USER_SETTINGS.get("ollama_model") or os.getenv("OLLAMA_MODEL", "llama2")
OLLAMA_VISION_MODEL = USER_SETTINGS.get("ollama_vision_model") or os.getenv("OLLAMA_VISION_MODEL", "")
OLLAMA_CONTEXT_LENGTH = USER_SETTINGS.get("ollama_context_length") or int(os.getenv("OLLAMA_CONTEXT_LENGTH", "8192"))

# Application settings
DEFAULT_UNIT_SYSTEM = "metric"  # or "imperial"
DEFAULT_LLM_PROVIDER = USER_SETTINGS.get("provider") or os.getenv("DEFAULT_LLM_PROVIDER", "ollama")  # "openai", "anthropic", "google", "ollama", or "none"

# LLM Configuration
LLM_CONFIG = {
    "openai": {
        "chat_model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000,
    },
    "anthropic": {
        "chat_model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
        "max_tokens": 1000,
    },
    "google": {
        "chat_model": "gemini-1.5-flash",
        "temperature": 0.7,
        "max_tokens": 1000,
    },
    "ollama": {
        "chat_model": OLLAMA_MODEL,
        "temperature": 0.7,
        "max_tokens": 1000,
    },
}
