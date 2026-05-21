"""Upload route."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.processamento_service import processar_txt_usuario
from app.services.empresa_service import obter_empresa_usuario
from app.services.storage_service import salvar_upload
from app.services.usuario_service import obter_usuario_atual

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("")
async def upload_e_processar(
    empresa_id: int = Form(...),
    arquivo: UploadFile = File(...),
    usuario=Depends(obter_usuario_atual),
    db: Session = Depends(get_db),
):
    obter_empresa_usuario(db, usuario.id, empresa_id)
    try:
        caminho = await salvar_upload(usuario.id, arquivo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return processar_txt_usuario(db, usuario.id, empresa_id, caminho, arquivo.filename or caminho.name)
