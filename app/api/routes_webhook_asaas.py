"""Asaas webhook route."""

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import get_db
from app.services.pagamento_service import processar_webhook_asaas

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/asaas")
async def webhook_asaas(request: Request, asaas_access_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    if settings.ASAAS_WEBHOOK_TOKEN and asaas_access_token != settings.ASAAS_WEBHOOK_TOKEN:
        raise HTTPException(status_code=401, detail="Webhook token inválido.")
    payload = await request.json()
    return processar_webhook_asaas(db, payload)
