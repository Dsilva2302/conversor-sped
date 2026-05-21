"""Subscription and usage limit rules."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.models import Assinatura, Plano, UsoMensal
from app.utils.datas import mes_referencia_atual

STATUS_LIBERADOS = {"TESTE_ATIVO", "ATIVA"}

PLANOS_INICIAIS = [
    ("Teste grátis", "Teste por 7 dias", 0, 3, 7),
    ("Básico", "Até 30 arquivos por mês", 197, 30, 0),
    ("Profissional", "Até 150 arquivos por mês", 497, 150, 0),
    ("Consultoria", "Até 700 arquivos por mês", 1497, 700, 0),
]


def garantir_planos(db: Session) -> None:
    for nome, descricao, valor, limite, dias_teste in PLANOS_INICIAIS:
        if not db.query(Plano).filter(Plano.nome == nome).first():
            db.add(Plano(nome=nome, descricao=descricao, valor_mensal=valor, limite_arquivos_mes=limite, dias_teste=dias_teste, ativo=True))
    db.commit()


def criar_assinatura_local(db: Session, usuario_id: int, empresa_id: int, plano_id: int) -> Assinatura:
    plano = db.get(Plano, plano_id)
    if not plano or not plano.ativo:
        raise HTTPException(status_code=400, detail="Plano inválido.")
    status = "TESTE_ATIVO" if plano.dias_teste else "PENDENTE"
    hoje = date.today()
    assinatura = Assinatura(
        usuario_id=usuario_id,
        empresa_id=empresa_id,
        plano_id=plano_id,
        status=status,
        data_inicio=hoje,
        data_fim=hoje + timedelta(days=plano.dias_teste) if plano.dias_teste else None,
        data_vencimento=hoje + timedelta(days=plano.dias_teste or 30),
        mes_referencia_uso=mes_referencia_atual(),
    )
    db.add(assinatura)
    db.commit()
    db.refresh(assinatura)
    return assinatura


def buscar_assinatura_usuario(db: Session, usuario_id: int, empresa_id: int | None = None) -> Assinatura | None:
    query = db.query(Assinatura).filter(Assinatura.usuario_id == usuario_id)
    if empresa_id is not None:
        query = query.filter(Assinatura.empresa_id == empresa_id)
    return query.order_by(Assinatura.id.desc()).first()


def buscar_ou_criar_uso_mensal(db: Session, assinatura: Assinatura) -> UsoMensal:
    mes = mes_referencia_atual()
    uso = db.query(UsoMensal).filter(UsoMensal.usuario_id == assinatura.usuario_id, UsoMensal.mes_referencia == mes).first()
    if uso:
        return uso
    uso = UsoMensal(
        usuario_id=assinatura.usuario_id,
        empresa_id=assinatura.empresa_id,
        plano_id=assinatura.plano_id,
        mes_referencia=mes,
        limite_arquivos=assinatura.plano.limite_arquivos_mes,
        arquivos_processados=0,
    )
    db.add(uso)
    db.commit()
    db.refresh(uso)
    return uso


def validar_permissao_processamento(db: Session, usuario_id: int, empresa_id: int | None = None) -> Assinatura:
    assinatura = buscar_assinatura_usuario(db, usuario_id, empresa_id)
    if not assinatura:
        raise HTTPException(status_code=403, detail="Usuário sem assinatura.")
    if assinatura.status not in STATUS_LIBERADOS:
        raise HTTPException(status_code=403, detail="Sua assinatura não está ativa.")
    uso = buscar_ou_criar_uso_mensal(db, assinatura)
    if uso.arquivos_processados >= assinatura.plano.limite_arquivos_mes:
        raise HTTPException(status_code=403, detail="Seu limite mensal de arquivos foi atingido.")
    return assinatura


def incrementar_uso(db: Session, assinatura: Assinatura) -> None:
    uso = buscar_ou_criar_uso_mensal(db, assinatura)
    uso.arquivos_processados += 1
    assinatura.arquivos_processados_mes = uso.arquivos_processados
    assinatura.mes_referencia_uso = uso.mes_referencia
    db.commit()
