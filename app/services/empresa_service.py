"""Company service."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.models import Empresa
from app.core.formatadores import somente_digitos


def criar_empresa(db: Session, usuario_id: int, dados) -> Empresa:
    empresa = Empresa(
        usuario_id=usuario_id,
        razao_social=dados.razao_social,
        nome_fantasia=dados.nome_fantasia,
        cnpj=somente_digitos(dados.cnpj),
        email_financeiro=dados.email_financeiro,
        telefone=dados.telefone,
    )
    db.add(empresa)
    db.commit()
    db.refresh(empresa)
    return empresa


def listar_empresas_usuario(db: Session, usuario_id: int) -> list[Empresa]:
    return db.query(Empresa).filter(Empresa.usuario_id == usuario_id).order_by(Empresa.id.desc()).all()


def obter_empresa_usuario(db: Session, usuario_id: int, empresa_id: int) -> Empresa:
    empresa = db.get(Empresa, empresa_id)
    if not empresa or empresa.usuario_id != usuario_id:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return empresa
