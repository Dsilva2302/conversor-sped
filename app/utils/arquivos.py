"""Safe file path helpers."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import settings


def storage_usuario(usuario_id: int, subpasta: str) -> Path:
    caminho = settings.STORAGE_ROOT / "usuarios" / str(usuario_id) / subpasta
    caminho.mkdir(parents=True, exist_ok=True)
    return caminho


def validar_txt_upload(arquivo: UploadFile) -> None:
    if not arquivo.filename or not arquivo.filename.lower().endswith(".txt"):
        raise ValueError("O arquivo enviado não parece ser um TXT válido do SPED.")


def nome_interno_seguro(nome_original: str) -> str:
    extensao = Path(nome_original).suffix.lower()
    return f"{uuid4().hex}{extensao}"
