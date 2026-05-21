"""Credit wallet service."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.models import CreditoTransacao

CUSTO_POR_RELATORIO = Decimal("1.00")


def saldo_creditos(db: Session, usuario_id: int) -> Decimal:
    total = (
        db.query(func.coalesce(func.sum(CreditoTransacao.quantidade), 0))
        .filter(CreditoTransacao.usuario_id == usuario_id, CreditoTransacao.status == "CONFIRMADO")
        .scalar()
    )
    return Decimal(str(total or 0))


def adicionar_creditos(db: Session, usuario_id: int, quantidade: Decimal, descricao: str, referencia: str = "") -> CreditoTransacao:
    transacao = CreditoTransacao(
        usuario_id=usuario_id,
        tipo="COMPRA",
        quantidade=quantidade,
        descricao=descricao,
        referencia=referencia,
        status="CONFIRMADO",
    )
    db.add(transacao)
    db.commit()
    db.refresh(transacao)
    return transacao


def consumir_creditos(db: Session, usuario_id: int, quantidade: Decimal, descricao: str, referencia: str = "") -> bool:
    if saldo_creditos(db, usuario_id) < quantidade:
        return False
    transacao = CreditoTransacao(
        usuario_id=usuario_id,
        tipo="USO",
        quantidade=-quantidade,
        descricao=descricao,
        referencia=referencia,
        status="CONFIRMADO",
    )
    db.add(transacao)
    db.commit()
    return True
