"""Local SPED TXT to Excel converter.

Edit only the constants below for local execution. The processing engine lives
in app/core and is reused by the SaaS API.
"""

from app.core.formatadores import (
    converter_decimal_sped,
    formatar_data_sped,
    safe_get,
    texto_excel,
    traduzir_indicador_emitente,
    traduzir_tipo_item,
    traduzir_tipo_operacao,
)
from app.core.nomes_arquivos import gerar_nome_saida, nao_sobrescrever
from app.core.parser_sped import (
    abrir_arquivo_com_encoding,
    encontrar_arquivos_txt,
    gerar_log,
    main as executar_processamento,
    parse_0000_contribuicoes,
    parse_0000_icms_ipi,
)
from app.core.detector_tipo_sped import identificar_tipo_sped
from app.core.excel_writer import aplicar_formatacao_excel, salvar_excel
from app.extractors.common import extrair_dicionarios_auxiliares
from app.extractors.efd_contribuicoes import extrair_efd_contribuicoes, montar_linha_contribuicoes
from app.extractors.efd_icms_ipi import extrair_efd_icms_ipi, montar_linha_icms_ipi

PASTA_TXT = r"C:\OD Danilo\OneDrive - ALBIERI E ASSOCIADOS CONSULTORIA EMPRESARIAL LTDA\Projetos IA\Relatorios SPED\TXT"
PASTA_SAIDA = r"C:\OD Danilo\OneDrive - ALBIERI E ASSOCIADOS CONSULTORIA EMPRESARIAL LTDA\Projetos IA\Relatorios SPED\Relatorios_Gerados"

PROCESSAR_SUBPASTAS = True
NAO_SOBRESCREVER = True
GERAR_LOG = True


def main():
    return executar_processamento(
        PASTA_TXT,
        PASTA_SAIDA,
        processar_subpastas=PROCESSAR_SUBPASTAS,
        nao_sobrescrever_arquivos=NAO_SOBRESCREVER,
        gerar_log_processamento=GERAR_LOG,
    )


if __name__ == "__main__":
    main()
