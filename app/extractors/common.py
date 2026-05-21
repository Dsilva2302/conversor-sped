"""Common SPED extraction helpers."""

from __future__ import annotations

from app.core.formatadores import safe_get, texto_excel


def participante(participantes: dict, codigo: str) -> dict:
    return participantes.get(texto_excel(codigo), {})


def item(itens: dict, codigo: str) -> dict:
    return itens.get(texto_excel(codigo), {})


def extrair_dicionarios_auxiliares(partes: list[str], estado: dict) -> None:
    registro = safe_get(partes, 1)
    if registro == "0150":
        estado["participantes_0150"][safe_get(partes, 2)] = {
            "nome": safe_get(partes, 3),
            "cnpj": safe_get(partes, 5),
            "cpf": safe_get(partes, 6),
            "ie": safe_get(partes, 7),
            "municipio": safe_get(partes, 8),
            "uf": "",
            "endereco": safe_get(partes, 10),
        }
    elif registro == "0190":
        estado["unidades_0190"][safe_get(partes, 2)] = safe_get(partes, 3)
    elif registro == "0200":
        estado["itens_0200"][safe_get(partes, 2)] = {
            "descricao": safe_get(partes, 3),
            "codigo_barra": safe_get(partes, 4),
            "unidade": safe_get(partes, 6),
            "tipo_item": safe_get(partes, 7),
            "ncm": safe_get(partes, 8),
            "codigo_servico": safe_get(partes, 11),
        }
    elif registro == "0400":
        estado["natureza_0400"][safe_get(partes, 2)] = safe_get(partes, 3)
    elif registro == "0450":
        estado["informacoes_0450"][safe_get(partes, 2)] = safe_get(partes, 3)
