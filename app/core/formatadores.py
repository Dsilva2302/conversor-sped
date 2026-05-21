"""Formatting helpers shared by local script and API."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def safe_get(partes: list[str], indice: int, padrao: str = "") -> str:
    if indice < 0 or indice >= len(partes):
        return padrao
    return partes[indice].strip()


def somente_digitos(valor: str) -> str:
    return "".join(ch for ch in texto_excel(valor) if ch.isdigit())


def texto_excel(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def formatar_data_sped(valor: str) -> str:
    valor = somente_digitos(valor)
    if len(valor) != 8:
        return ""
    try:
        return datetime.strptime(valor, "%d%m%Y").strftime("%d/%m/%Y")
    except ValueError:
        return ""


def data_sped_para_date(valor: str) -> date | None:
    valor = somente_digitos(valor)
    if len(valor) != 8:
        return None
    try:
        return datetime.strptime(valor, "%d%m%Y").date()
    except ValueError:
        return None


def data_sped_para_nome(valor: str) -> str:
    valor = somente_digitos(valor)
    if len(valor) != 8:
        return ""
    return f"{valor[4:8]}{valor[2:4]}{valor[0:2]}"


def converter_decimal_sped(valor: str) -> Decimal | None:
    valor = texto_excel(valor)
    if not valor:
        return None
    valor = valor.replace(".", "").replace(",", ".")
    try:
        return Decimal(valor)
    except InvalidOperation:
        return None


def traduzir_tipo_operacao(codigo: str) -> str:
    return {"0": "0 - Entrada", "1": "1 - Saída"}.get(texto_excel(codigo), texto_excel(codigo))


def traduzir_indicador_emitente(codigo: str) -> str:
    return {"0": "0 - Emissão Própria", "1": "1 - Terceiros"}.get(texto_excel(codigo), texto_excel(codigo))


def traduzir_tipo_item(codigo: str) -> str:
    mapa = {
        "00": "00 - Mercadoria para Revenda",
        "01": "01 - Matéria-Prima",
        "02": "02 - Embalagem",
        "03": "03 - Produto em Processo",
        "04": "04 - Produto Acabado",
        "05": "05 - Subproduto",
        "06": "06 - Produto Intermediário",
        "07": "07 - Material de Uso e Consumo",
        "08": "08 - Ativo Imobilizado",
        "09": "09 - Serviços",
        "10": "10 - Outros Insumos",
        "99": "99 - Outras",
    }
    return mapa.get(texto_excel(codigo), texto_excel(codigo))


def uf_origem_destino(uf_participante: str, uf_empresa: str) -> str:
    uf_participante = texto_excel(uf_participante)
    uf_empresa = texto_excel(uf_empresa)
    if uf_participante and uf_empresa:
        return f"{uf_participante}/{uf_empresa}"
    return uf_participante or uf_empresa
