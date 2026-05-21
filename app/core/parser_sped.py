"""Local SPED TXT to Excel processing engine."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
import sys
from typing import TextIO

from openpyxl import Workbook

from app.core.detector_tipo_sped import TIPO_CONTRIBUICOES, TIPO_ICMS_IPI, identificar_tipo_sped
from app.core.excel_writer import salvar_excel
from app.core.formatadores import safe_get
from app.core.nomes_arquivos import gerar_nome_saida, nao_sobrescrever
from app.extractors.common import extrair_dicionarios_auxiliares
from app.extractors.efd_contribuicoes import extrair_efd_contribuicoes
from app.extractors.efd_icms_ipi import extrair_efd_icms_ipi
from app.layouts.layout_contribuicoes import CABECALHO_CONTRIBUICOES
from app.layouts.layout_icms_ipi import CABECALHO_ICMS_IPI

ENCODINGS = ("latin1", "cp1252", "utf-8")


def encontrar_arquivos_txt(pasta_txt: str | Path, processar_subpastas: bool = True) -> list[Path]:
    pasta = Path(pasta_txt)
    padrao = "**/*.txt" if processar_subpastas else "*.txt"
    return sorted(p for p in pasta.glob(padrao) if p.is_file())


def abrir_arquivo_com_encoding(caminho: str | Path) -> tuple[TextIO, str]:
    ultimo_erro: Exception | None = None
    for encoding in ENCODINGS:
        try:
            arquivo = open(caminho, "r", encoding=encoding, errors="strict")
            arquivo.readline()
            arquivo.seek(0)
            return arquivo, encoding
        except Exception as exc:  # noqa: BLE001 - logged by caller.
            ultimo_erro = exc
    raise UnicodeError(f"Não foi possível abrir o arquivo com os encodings {ENCODINGS}: {ultimo_erro}")


def parse_0000_contribuicoes(partes: list[str]) -> dict:
    return {
        "cod_ver": safe_get(partes, 2),
        "cod_fin": safe_get(partes, 3),
        "dt_ini": safe_get(partes, 6),
        "dt_fin": safe_get(partes, 7),
        "nome_empresa": safe_get(partes, 8),
        "cnpj": safe_get(partes, 9),
        "uf": safe_get(partes, 10),
        "ie": "",
    }


def parse_0000_icms_ipi(partes: list[str]) -> dict:
    return {
        "cod_ver": safe_get(partes, 2),
        "cod_fin": safe_get(partes, 3),
        "dt_ini": safe_get(partes, 4),
        "dt_fin": safe_get(partes, 5),
        "nome_empresa": safe_get(partes, 6),
        "cnpj": safe_get(partes, 7),
        "uf": safe_get(partes, 9),
        "ie": safe_get(partes, 10),
    }


def _estado_inicial(cabecalho: list[str]) -> dict:
    return {
        "meta": {},
        "cabecalho": cabecalho,
        "participantes_0150": {},
        "itens_0200": {},
        "unidades_0190": {},
        "natureza_0400": {},
        "informacoes_0450": {},
    }


def processar_arquivo_sped(caminho_txt: str | Path, pasta_saida: str | Path, impedir_sobrescrita: bool = True) -> dict:
    caminho_txt = Path(caminho_txt)
    pasta_saida = Path(pasta_saida)
    inicio = datetime.now()
    contadores: Counter[str] = Counter()
    linhas_saida: list[dict] = []
    quantidade_linhas_lidas = 0
    meta: dict = {}
    tipo_sped = ""
    arquivo_excel = ""

    arquivo, encoding = abrir_arquivo_com_encoding(caminho_txt)
    with arquivo:
        tipo_sped = identificar_tipo_sped(caminho_txt, encoding=encoding)
        cabecalho = CABECALHO_CONTRIBUICOES if tipo_sped == TIPO_CONTRIBUICOES else CABECALHO_ICMS_IPI
        estado = _estado_inicial(cabecalho)
        for linha in arquivo:
            quantidade_linhas_lidas += 1
            partes = linha.strip().split("|")
            registro = safe_get(partes, 1)
            if not registro:
                continue
            contadores[registro] += 1
            if registro == "0000":
                meta = parse_0000_contribuicoes(partes) if tipo_sped == TIPO_CONTRIBUICOES else parse_0000_icms_ipi(partes)
                estado["meta"] = meta
            extrair_dicionarios_auxiliares(partes, estado)
            if tipo_sped == TIPO_CONTRIBUICOES:
                linhas_saida.extend(extrair_efd_contribuicoes(partes, estado))
            else:
                linhas_saida.extend(extrair_efd_icms_ipi(partes, estado))

    nome_saida = gerar_nome_saida(tipo_sped, meta.get("cnpj", ""), meta.get("dt_ini", ""), meta.get("dt_fin", ""))
    caminho_saida = pasta_saida / nome_saida
    if impedir_sobrescrita:
        caminho_saida = nao_sobrescrever(caminho_saida)
    salvar_excel(caminho_saida, cabecalho, linhas_saida)
    arquivo_excel = str(caminho_saida)

    return {
        "arquivo_origem": caminho_txt.name,
        "caminho_completo": str(caminho_txt),
        "tipo_sped_identificado": tipo_sped,
        "cnpj": meta.get("cnpj", ""),
        "nome_empresa": meta.get("nome_empresa", ""),
        "uf": meta.get("uf", ""),
        "ie": meta.get("ie", ""),
        "dt_ini": meta.get("dt_ini", ""),
        "dt_fin": meta.get("dt_fin", ""),
        "status_processamento": "CONCLUIDO",
        "erro": "",
        "quantidade_linhas_lidas": quantidade_linhas_lidas,
        "quantidade_linhas_geradas": len(linhas_saida),
        "quantidade_registros_0000": contadores["0000"],
        "quantidade_registros_0150": contadores["0150"],
        "quantidade_registros_0200": contadores["0200"],
        "quantidade_registros_C100": contadores["C100"],
        "quantidade_registros_C170": contadores["C170"],
        "quantidade_registros_C190": contadores["C190"],
        "quantidade_registros_A100": contadores["A100"],
        "quantidade_registros_A170": contadores["A170"],
        "quantidade_registros_F100": contadores["F100"],
        "quantidade_registros_M100": contadores["M100"],
        "quantidade_registros_M200": contadores["M200"],
        "quantidade_registros_M500": contadores["M500"],
        "quantidade_registros_M600": contadores["M600"],
        "data_hora_processamento": inicio.strftime("%d/%m/%Y %H:%M:%S"),
        "arquivo_excel_gerado": arquivo_excel,
    }


LOG_COLUNAS = [
    "arquivo_origem",
    "caminho_completo",
    "tipo_sped_identificado",
    "cnpj",
    "nome_empresa",
    "uf",
    "ie",
    "dt_ini",
    "dt_fin",
    "status_processamento",
    "erro",
    "quantidade_linhas_lidas",
    "quantidade_linhas_geradas",
    "quantidade_registros_0000",
    "quantidade_registros_0150",
    "quantidade_registros_0200",
    "quantidade_registros_C100",
    "quantidade_registros_C170",
    "quantidade_registros_C190",
    "quantidade_registros_A100",
    "quantidade_registros_A170",
    "quantidade_registros_F100",
    "quantidade_registros_M100",
    "quantidade_registros_M200",
    "quantidade_registros_M500",
    "quantidade_registros_M600",
    "data_hora_processamento",
    "arquivo_excel_gerado",
]


def gerar_log(pasta_saida: str | Path, registros: list[dict]) -> Path:
    caminho = Path(pasta_saida) / "LOG_PROCESSAMENTO_SPED.xlsx"
    caminho = nao_sobrescrever(caminho)
    wb = Workbook()
    ws = wb.active
    ws.title = "Log"
    ws.append(LOG_COLUNAS)
    for registro in registros:
        ws.append([registro.get(coluna, "") for coluna in LOG_COLUNAS])
    ws.auto_filter.ref = ws.dimensions
    ws.freeze_panes = "A2"
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = min(max(len(str(col[0].value)) + 4, 14), 48)
    wb.save(caminho)
    wb.close()
    return caminho


def main(
    pasta_txt: str | Path,
    pasta_saida: str | Path,
    processar_subpastas: bool = True,
    nao_sobrescrever_arquivos: bool = True,
    gerar_log_processamento: bool = True,
) -> list[dict]:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    print("🚀 Iniciando processamento")
    print(f"📁 Pasta origem: {pasta_txt}")
    print(f"📁 Pasta saída: {pasta_saida}")
    Path(pasta_saida).mkdir(parents=True, exist_ok=True)
    arquivos = encontrar_arquivos_txt(pasta_txt, processar_subpastas)
    print(f"📄 Quantidade de TXT localizados: {len(arquivos)}")
    resultados: list[dict] = []

    for caminho in arquivos:
        print(f"📄 Arquivo atual: {caminho.name}")
        try:
            resultado = processar_arquivo_sped(caminho, pasta_saida, impedir_sobrescrita=nao_sobrescrever_arquivos)
            print(f"🏢 CNPJ: {resultado['cnpj']}")
            print(f"📅 Período: {resultado['dt_ini']} a {resultado['dt_fin']}")
            print(f"📘 Tipo de SPED identificado: {resultado['tipo_sped_identificado']}")
            print(f"📊 Quantidade de linhas geradas: {resultado['quantidade_linhas_geradas']}")
            print(f"💾 Arquivo salvo: {resultado['arquivo_excel_gerado']}")
        except Exception as exc:  # noqa: BLE001 - processing must continue.
            print(f"⚠️ Erro: {exc}")
            resultado = {
                "arquivo_origem": caminho.name,
                "caminho_completo": str(caminho),
                "status_processamento": "ERRO",
                "erro": str(exc),
                "data_hora_processamento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            }
        resultados.append(resultado)

    if gerar_log_processamento:
        log = gerar_log(pasta_saida, resultados)
        print(f"💾 Log salvo: {log}")
    print("✅ Processamento concluído")
    return resultados
