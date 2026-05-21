from pydantic import BaseModel


class PagamentoWebhook(BaseModel):
    event: str
    payment: dict | None = None
