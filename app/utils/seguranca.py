"""Authentication helpers."""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def _senha_bytes(senha: str) -> bytes:
    return hashlib.sha256(senha.encode("utf-8")).digest()


def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(_senha_bytes(senha), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(_senha_bytes(senha), senha_hash.encode("utf-8"))


def criar_token_acesso(subject: str) -> str:
    expira = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": subject, "exp": expira}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        subject = payload.get("sub")
        if not subject:
            raise ValueError("Token inválido")
        return str(subject)
    except JWTError as exc:
        raise ValueError("Token inválido") from exc
