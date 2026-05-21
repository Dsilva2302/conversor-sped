from pydantic import BaseModel


class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str
    telefone: str | None = None
    documento: str | None = None
    tipo_documento: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str
    ativo: bool

    class Config:
        from_attributes = True
