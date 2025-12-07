"""
Configuration management for ProbablyTasty.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database
DATABASE_URL = f"sqlite:///{DATA_DIR / 'recipes.db'}"

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

# Application settings
DEFAULT_UNIT_SYSTEM = "metric"  # or "imperial"
DEFAULT_LLM_PROVIDER = "openai"  # "openai", "anthropic", "google", or "none"

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
}
