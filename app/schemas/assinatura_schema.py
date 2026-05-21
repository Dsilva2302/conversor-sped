from pydantic import BaseModel


class AssinaturaCreate(BaseModel):
    empresa_id: int
    plano_id: int


class AssinaturaStatus(BaseModel):
    status: str
    limite_arquivos_mes: int
    arquivos_processados_mes: int
