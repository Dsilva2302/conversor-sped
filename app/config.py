"""Application settings."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME = "SPED Excel SaaS"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sped_saas.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    STORAGE_ROOT = Path(os.getenv("STORAGE_ROOT", "storage"))
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "80"))
    DIAS_RETENCAO_UPLOADS = int(os.getenv("DIAS_RETENCAO_UPLOADS", "7"))
    DIAS_RETENCAO_OUTPUTS = int(os.getenv("DIAS_RETENCAO_OUTPUTS", "30"))
    ASAAS_API_KEY = os.getenv("ASAAS_API_KEY", "")
    ASAAS_BASE_URL = os.getenv("ASAAS_BASE_URL", "https://sandbox.asaas.com/api/v3")
    ASAAS_WEBHOOK_TOKEN = os.getenv("ASAAS_WEBHOOK_TOKEN", "")
    ASAAS_WALLET_ID = os.getenv("ASAAS_WALLET_ID", "")


settings = Settings()
