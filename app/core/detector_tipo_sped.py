"""SPED type detector."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from app.core.formatadores import safe_get

TIPO_CONTRIBUICOES = "EFD-Contribuições"
TIPO_ICMS_IPI = "EFD-ICMS/IPI"

REGISTROS_CONTRIBUICOES = {"C010", "A100", "A170", "F100", "M100", "M200", "M500", "M600", "1100", "1500"}
REGISTROS_ICMS_IPI = {"C100", "C170", "C190", "C500", "C590", "D700", "D730", "E100", "E110", "E200", "E210", "K200"}


def _parece_data_sped(valor: str) -> bool:
    return len(valor) == 8 and valor.isdigit()


def identificar_tipo_sped(caminho: str | Path, encoding: str = "latin1", limite_linhas: int = 20000) -> str:
    contagem: Counter[str] = Counter()
    tipo_por_0000 = ""
    with open(caminho, "r", encoding=encoding, errors="strict") as arquivo:
        for numero, linha in enumerate(arquivo, start=1):
            partes = linha.rstrip("\n\r").split("|")
            registro = safe_get(partes, 1)
            if registro:
                contagem[registro] += 1
            if registro == "0000":
                if _parece_data_sped(safe_get(partes, 4)) and _parece_data_sped(safe_get(partes, 5)):
                    tipo_por_0000 = TIPO_ICMS_IPI
                elif _parece_data_sped(safe_get(partes, 6)) and _parece_data_sped(safe_get(partes, 7)):
                    tipo_por_0000 = TIPO_CONTRIBUICOES
            if numero >= limite_linhas:
                break

    pontos_contrib = sum(contagem[reg] for reg in REGISTROS_CONTRIBUICOES)
    pontos_icms = sum(contagem[reg] for reg in REGISTROS_ICMS_IPI)

    if tipo_por_0000 and (pontos_contrib == pontos_icms or min(pontos_contrib, pontos_icms) > 0):
        return tipo_por_0000
    if pontos_contrib > pontos_icms:
        return TIPO_CONTRIBUICOES
    if pontos_icms > pontos_contrib:
        return TIPO_ICMS_IPI
    raise ValueError("Não foi possível identificar o tipo do arquivo SPED.")
