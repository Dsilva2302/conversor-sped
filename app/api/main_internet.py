"""FastAPI entrypoint for the future internet version.

Use app.api.main for the local/test program.
Use app.api.main_internet when publishing with real Asaas credit purchases.
"""

from fastapi import FastAPI

from app.api import (
    routes_assinatura,
    routes_auth,
    routes_creditos_internet,
    routes_download,
    routes_empresas,
    routes_local,
    routes_processamento,
    routes_processar,
    routes_upload,
    routes_webhook_asaas,
)
from app.database.models import Base
from app.database.session import SessionLocal, engine
from app.services.assinatura_service import garantir_planos

app = FastAPI(title="Conversor SPED para Excel - Internet")

app.include_router(routes_local.router)
app.include_router(routes_creditos_internet.router)
app.include_router(routes_auth.router)
app.include_router(routes_empresas.router)
app.include_router(routes_assinatura.router)
app.include_router(routes_upload.router)
app.include_router(routes_processar.router)
app.include_router(routes_processamento.router)
app.include_router(routes_download.router)
app.include_router(routes_webhook_asaas.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        garantir_planos(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "versao": "internet"}
