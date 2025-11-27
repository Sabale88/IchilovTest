"""Application configuration."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

DOTENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=DOTENV_PATH, override=False)


class Settings:
    """Application settings."""

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Patient Monitoring System"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]


settings = Settings()

