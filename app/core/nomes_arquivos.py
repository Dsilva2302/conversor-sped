"""Output file naming helpers."""

from __future__ import annotations

from pathlib import Path

from app.core.detector_tipo_sped import TIPO_CONTRIBUICOES, TIPO_ICMS_IPI
from app.core.formatadores import data_sped_para_nome, somente_digitos


def gerar_nome_saida(tipo_sped: str, cnpj: str, dt_ini: str, dt_fin: str) -> str:
    cnpj_limpo = somente_digitos(cnpj) or "SEM_CNPJ"
    ini = data_sped_para_nome(dt_ini) or "SEM_DTINI"
    fim = data_sped_para_nome(dt_fin) or "SEM_DTFIN"
    if tipo_sped == TIPO_CONTRIBUICOES:
        prefixo = "EFD - Contribuições - Todos os Registros"
    elif tipo_sped == TIPO_ICMS_IPI:
        prefixo = "EFD - ICMS-IPI - Todos os Registros"
    else:
        prefixo = "SPED - Todos os Registros"
    return f"{prefixo} - {cnpj_limpo}_{ini}_{fim}.xlsx"


def nao_sobrescrever(caminho: str | Path) -> Path:
    caminho = Path(caminho)
    if not caminho.exists():
        return caminho
    for indice in range(1, 1000):
        candidato = caminho.with_name(f"{caminho.stem}_{indice:03d}{caminho.suffix}")
        if not candidato.exists():
            return candidato
    raise FileExistsError(f"Não foi possível gerar nome disponível para {caminho}.")
