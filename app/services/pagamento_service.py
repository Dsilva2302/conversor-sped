"""Asaas payment integration service."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import json

import requests
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import Assinatura, CompraCredito, CreditoTransacao, Pagamento


def _headers() -> dict:
    return {"access_token": settings.ASAAS_API_KEY, "Content-Type": "application/json"}


def asaas_configurado() -> bool:
    return bool(settings.ASAAS_API_KEY)


def _asaas_post(path: str, payload: dict) -> dict:
    if not asaas_configurado():
        raise RuntimeError("ASAAS_API_KEY nao configurada.")
    response = requests.post(f"{settings.ASAAS_BASE_URL}{path}", headers=_headers(), json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def _asaas_get(path: str) -> dict:
    if not asaas_configurado():
        raise RuntimeError("ASAAS_API_KEY nao configurada.")
    response = requests.get(f"{settings.ASAAS_BASE_URL}{path}", headers=_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def criar_cliente_asaas(usuario, empresa) -> dict:
    payload = {"name": empresa.razao_social, "email": empresa.email_financeiro or usuario.email, "cpfCnpj": empresa.cnpj, "phone": empresa.telefone or usuario.telefone}
    return _asaas_post("/customers", payload)


def criar_assinatura_asaas(customer_id: str, plano) -> dict:
    payload = {"customer": customer_id, "billingType": "UNDEFINED", "value": float(plano.valor_mensal), "cycle": "MONTHLY", "description": plano.nome}
    return _asaas_post("/subscriptions", payload)


def cancelar_assinatura_asaas(subscription_id: str) -> dict:
    response = requests.delete(f"{settings.ASAAS_BASE_URL}/subscriptions/{subscription_id}", headers=_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def buscar_assinatura_asaas(subscription_id: str) -> dict:
    return _asaas_get(f"/subscriptions/{subscription_id}")


def criar_cobranca_creditos_asaas(db: Session, usuario, quantidade: int, forma_pagamento: str) -> CompraCredito:
    """Create a one-time Asaas payment and store a pending credit purchase."""
    documento = "".join(ch for ch in (usuario.documento or "") if ch.isdigit())
    if not documento:
        raise ValueError("Informe CPF ou CNPJ no cadastro para comprar creditos pelo Asaas.")

    billing_type = "PIX" if forma_pagamento == "PIX" else "CREDIT_CARD"
    valor = Decimal(quantidade).quantize(Decimal("0.01"))
    customer_payload = {
        "name": usuario.nome,
        "email": usuario.email,
        "cpfCnpj": documento,
        "externalReference": f"usuario-{usuario.id}",
    }
    customer = _asaas_post("/customers", customer_payload)
    payment = _asaas_post(
        "/payments",
        {
            "customer": customer["id"],
            "billingType": billing_type,
            "value": float(valor),
            "dueDate": date.today().isoformat(),
            "description": f"Compra de {quantidade} creditos - Conversor SPED",
            "externalReference": f"creditos-{usuario.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        },
    )

    pix_payload = None
    pix_encoded_image = None
    if billing_type == "PIX":
        try:
            pix = _asaas_get(f"/payments/{payment['id']}/pixQrCode")
            pix_payload = pix.get("payload")
            pix_encoded_image = pix.get("encodedImage")
        except requests.RequestException:
            pix_payload = None
            pix_encoded_image = None

    compra = CompraCredito(
        usuario_id=usuario.id,
        quantidade_creditos=valor,
        valor=valor,
        forma_pagamento=billing_type,
        status="PENDENTE",
        asaas_customer_id=customer.get("id"),
        asaas_payment_id=payment.get("id"),
        invoice_url=payment.get("invoiceUrl") or payment.get("bankSlipUrl"),
        pix_payload=pix_payload,
        pix_encoded_image=pix_encoded_image,
        payload_json=json.dumps({"customer": customer, "payment": payment}, ensure_ascii=False),
    )
    db.add(compra)
    db.commit()
    db.refresh(compra)
    return compra


def atualizar_pix_cobranca_asaas(db: Session, compra: CompraCredito) -> CompraCredito:
    if compra.forma_pagamento != "PIX" or not compra.asaas_payment_id:
        return compra
    if compra.pix_payload and compra.pix_encoded_image:
        return compra
    try:
        pix = _asaas_get(f"/payments/{compra.asaas_payment_id}/pixQrCode")
    except requests.RequestException:
        return compra
    compra.pix_payload = pix.get("payload")
    compra.pix_encoded_image = pix.get("encodedImage")
    db.commit()
    db.refresh(compra)
    return compra


def processar_webhook_asaas(db: Session, payload: dict) -> dict:
    evento = payload.get("event", "")
    payment = payload.get("payment") or {}
    payment_id = payment.get("id")
    subscription_id = payment.get("subscription")
    assinatura = None
    if subscription_id:
        assinatura = db.query(Assinatura).filter(Assinatura.asaas_subscription_id == subscription_id).first()

    if assinatura:
        if evento in {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"}:
            assinatura.status = "ATIVA"
        elif evento == "PAYMENT_OVERDUE":
            assinatura.status = "ATRASADA"
        elif evento == "PAYMENT_DELETED":
            assinatura.status = "CANCELADA"
        elif evento in {"PAYMENT_REFUNDED", "PAYMENT_CHARGEBACK_REQUESTED", "PAYMENT_CHARGEBACK_DISPUTE", "PAYMENT_AWAITING_CHARGEBACK_REVERSAL"}:
            assinatura.status = "BLOQUEADA"

        pagamento = Pagamento(
            usuario_id=assinatura.usuario_id,
            empresa_id=assinatura.empresa_id,
            assinatura_id=assinatura.id,
            asaas_payment_id=payment.get("id"),
            asaas_subscription_id=subscription_id,
            status=_status_pagamento(evento),
            valor=payment.get("value"),
            forma_pagamento=payment.get("billingType"),
            evento_webhook=evento,
            payload_json=json.dumps(payload, ensure_ascii=False),
        )
        db.add(pagamento)
        db.commit()

    compra = None
    if payment_id:
        compra = db.query(CompraCredito).filter(CompraCredito.asaas_payment_id == payment_id).first()
    if compra:
        compra.payload_json = json.dumps(payload, ensure_ascii=False)
        if evento in {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"}:
            compra.status = "CONFIRMADO"
            compra.data_confirmacao = datetime.utcnow()
            if not compra.creditos_liberados:
                db.add(
                    CreditoTransacao(
                        usuario_id=compra.usuario_id,
                        tipo="COMPRA",
                        quantidade=compra.quantidade_creditos,
                        descricao=f"Compra de creditos confirmada pelo Asaas ({evento})",
                        referencia=f"ASAAS-{payment_id}",
                        status="CONFIRMADO",
                    )
                )
                compra.creditos_liberados = True
        elif evento == "PAYMENT_OVERDUE":
            compra.status = "VENCIDO"
        elif evento == "PAYMENT_DELETED":
            compra.status = "CANCELADO"
        elif evento in {"PAYMENT_REFUNDED", "PAYMENT_CHARGEBACK_REQUESTED", "PAYMENT_CHARGEBACK_DISPUTE", "PAYMENT_AWAITING_CHARGEBACK_REVERSAL"}:
            compra.status = "ESTORNADO"
            if compra.creditos_liberados:
                db.add(
                    CreditoTransacao(
                        usuario_id=compra.usuario_id,
                        tipo="ESTORNO",
                        quantidade=-compra.quantidade_creditos,
                        descricao=f"Estorno/chargeback de creditos pelo Asaas ({evento})",
                        referencia=f"ASAAS-ESTORNO-{payment_id}",
                        status="CONFIRMADO",
                    )
                )
                compra.creditos_liberados = False
        db.commit()

    return {"ok": True, "event": evento, "assinatura_encontrada": bool(assinatura), "compra_creditos_encontrada": bool(compra)}


def _status_pagamento(evento: str) -> str:
    return {
        "PAYMENT_CREATED": "CRIADO",
        "PAYMENT_CONFIRMED": "CONFIRMADO",
        "PAYMENT_RECEIVED": "RECEBIDO",
        "PAYMENT_OVERDUE": "VENCIDO",
        "PAYMENT_DELETED": "CANCELADO",
        "PAYMENT_REFUNDED": "ESTORNADO",
        "PAYMENT_CHARGEBACK_REQUESTED": "CHARGEBACK",
        "PAYMENT_CHARGEBACK_DISPUTE": "CHARGEBACK",
        "PAYMENT_AWAITING_CHARGEBACK_REVERSAL": "CHARGEBACK",
    }.get(evento, "ERRO")
