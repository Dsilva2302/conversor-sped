"""Download route."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.models import Processamento
from app.database.session import get_db
from app.services.usuario_service import obter_usuario_atual

router = APIRouter(prefix="/download", tags=["download"])


@router.get("/{processamento_id}")
def download(processamento_id: int, usuario=Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    proc = db.get(Processamento, processamento_id)
    if not proc or proc.usuario_id != usuario.id or proc.status != "CONCLUIDO":
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    caminho = Path(proc.arquivo_excel_path or "")
    if not caminho.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no storage.")
    return FileResponse(caminho, filename=proc.arquivo_excel_nome)
