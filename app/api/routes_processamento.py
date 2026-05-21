"""Processing history routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.models import Processamento
from app.database.session import get_db
from app.schemas.processamento_schema import ProcessamentoOut
from app.services.usuario_service import obter_usuario_atual

router = APIRouter(prefix="/processamentos", tags=["processamentos"])


@router.get("", response_model=list[ProcessamentoOut])
def listar(usuario=Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    return db.query(Processamento).filter(Processamento.usuario_id == usuario.id).order_by(Processamento.id.desc()).all()


@router.get("/{processamento_id}", response_model=ProcessamentoOut)
def obter(processamento_id: int, usuario=Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    proc = db.get(Processamento, processamento_id)
    if not proc or proc.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Processamento não encontrado.")
    return proc


@router.post("/processar")
def processar_stub():
    return {"detail": "Use POST /upload para enviar e processar o TXT nesta versão inicial."}
