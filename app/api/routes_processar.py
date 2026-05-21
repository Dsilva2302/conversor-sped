"""Explicit /processar endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["processar"])


@router.post("/processar")
def processar():
    return {"detail": "Use POST /upload com empresa_id e arquivo TXT; nesta versão o upload já processa o arquivo imediatamente."}
