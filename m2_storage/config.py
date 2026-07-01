"""Tracelog M2 - Config via python-dotenv"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=False)


class _Settings:
    DB_PATH: str = os.getenv("DB_PATH", "/data/tracelog.db")
    SERVICE_HOST: str = os.getenv("SERVICE_HOST", "0.0.0.0")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8765"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    API_SECRET: str = os.getenv("API_SECRET", "")


settings = _Settings()
