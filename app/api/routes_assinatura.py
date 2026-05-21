"""Plan and subscription routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.models import Plano
from app.database.session import get_db
from app.schemas.assinatura_schema import AssinaturaCreate
from app.config import settings
from app.services.assinatura_service import buscar_assinatura_usuario, criar_assinatura_local, garantir_planos
from app.services.empresa_service import obter_empresa_usuario
from app.services.pagamento_service import criar_assinatura_asaas, criar_cliente_asaas
from app.services.usuario_service import obter_usuario_atual

router = APIRouter(tags=["assinatura"])


@router.get("/planos")
def listar_planos(db: Session = Depends(get_db)):
    garantir_planos(db)
    return db.query(Plano).filter(Plano.ativo.is_(True)).all()


@router.get("/assinatura/status")
def status_assinatura(usuario=Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    assinatura = buscar_assinatura_usuario(db, usuario.id)
    if not assinatura:
        raise HTTPException(status_code=404, detail="Usuário sem assinatura.")
    return {
        "status": assinatura.status,
        "limite_arquivos_mes": assinatura.plano.limite_arquivos_mes,
        "arquivos_processados_mes": assinatura.arquivos_processados_mes,
    }


@router.post("/assinatura/criar")
def criar_assinatura(dados: AssinaturaCreate, usuario=Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    empresa = obter_empresa_usuario(db, usuario.id, dados.empresa_id)
    assinatura = criar_assinatura_local(db, usuario.id, empresa.id, dados.plano_id)
    if settings.ASAAS_API_KEY and assinatura.plano.valor_mensal:
        cliente = criar_cliente_asaas(usuario, empresa)
        cobranca = criar_assinatura_asaas(cliente["id"], assinatura.plano)
        assinatura.asaas_customer_id = cliente["id"]
        assinatura.asaas_subscription_id = cobranca["id"]
        db.commit()
        db.refresh(assinatura)
    return assinatura


@router.post("/assinatura/cancelar")
def cancelar_assinatura(usuario=Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    assinatura = buscar_assinatura_usuario(db, usuario.id)
    if not assinatura:
        raise HTTPException(status_code=404, detail="Usuário sem assinatura.")
    assinatura.status = "CANCELADA"
    db.commit()
    return {"status": assinatura.status}
