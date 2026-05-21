"""Date helpers."""

from datetime import date


def mes_referencia_atual() -> str:
    hoje = date.today()
    return f"{hoje.year:04d}-{hoje.month:02d}"
