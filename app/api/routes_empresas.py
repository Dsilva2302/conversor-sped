"""Company routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.empresa_schema import EmpresaCreate, EmpresaOut
from app.services.empresa_service import criar_empresa, listar_empresas_usuario, obter_empresa_usuario
from app.services.usuario_service import obter_usuario_atual

router = APIRouter(prefix="/empresas", tags=["empresas"])


@router.post("", response_model=EmpresaOut)
def cadastrar_empresa(dados: EmpresaCreate, usuario=Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    return criar_empresa(db, usuario.id, dados)


@router.get("", response_model=list[EmpresaOut])
def listar_empresas(usuario=Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    return listar_empresas_usuario(db, usuario.id)


@router.get("/{empresa_id}", response_model=EmpresaOut)
def obter_empresa(empresa_id: int, usuario=Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    return obter_empresa_usuario(db, usuario.id, empresa_id)
