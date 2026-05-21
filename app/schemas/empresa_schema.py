from pydantic import BaseModel


class EmpresaCreate(BaseModel):
    razao_social: str
    nome_fantasia: str | None = None
    cnpj: str
    email_financeiro: str | None = None
    telefone: str | None = None


class EmpresaOut(BaseModel):
    id: int
    usuario_id: int
    razao_social: str
    nome_fantasia: str | None
    cnpj: str
    email_financeiro: str | None
    telefone: str | None

    class Config:
        from_attributes = True
