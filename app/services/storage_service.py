"""Local storage service."""

from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.utils.arquivos import nome_interno_seguro, storage_usuario, validar_txt_upload


async def salvar_upload(usuario_id: int, arquivo: UploadFile) -> Path:
    validar_txt_upload(arquivo)
    destino = storage_usuario(usuario_id, "uploads") / nome_interno_seguro(arquivo.filename)
    total = 0
    limite = settings.MAX_UPLOAD_MB * 1024 * 1024
    with open(destino, "wb") as out:
        while chunk := await arquivo.read(1024 * 1024):
            total += len(chunk)
            if total > limite:
                out.close()
                destino.unlink(missing_ok=True)
                raise ValueError(f"Arquivo excede o limite de {settings.MAX_UPLOAD_MB} MB.")
            out.write(chunk)
    return destino


def pasta_saida_usuario(usuario_id: int) -> Path:
    return storage_usuario(usuario_id, "outputs")
