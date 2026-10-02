"""Read the local settings from .env."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_FOLDER = Path(__file__).parent
load_dotenv(PROJECT_FOLDER / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1"

LAGO_API_URL = os.getenv("LAGO_API_URL", "http://127.0.0.1:3001/api/v1")
LAGO_API_KEY = os.getenv("LAGO_API_KEY", "")
LAGO_EXTERNAL_SUBSCRIPTION_ID = os.getenv("LAGO_EXTERNAL_SUBSCRIPTION_ID", "")
LAGO_EVENT_CODE = os.getenv("LAGO_EVENT_CODE", "ai_tokens")

DEMO_PRICE_PER_1000_TOKENS = float(
    os.getenv("DEMO_PRICE_PER_1000_TOKENS", "0.001")
)
