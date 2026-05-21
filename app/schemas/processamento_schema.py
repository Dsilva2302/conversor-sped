from pydantic import BaseModel


class ProcessamentoOut(BaseModel):
    id: int
    tipo_sped: str | None
    arquivo_original_nome: str
    arquivo_excel_nome: str | None
    status: str
    erro: str | None
    quantidade_linhas_lidas: int
    quantidade_linhas_geradas: int

    class Config:
        from_attributes = True
