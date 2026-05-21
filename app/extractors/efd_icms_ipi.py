"""Extractor for EFD-ICMS/IPI."""

from __future__ import annotations

from app.core.formatadores import (
    converter_decimal_sped,
    data_sped_para_date,
    safe_get,
    traduzir_indicador_emitente,
    traduzir_tipo_item,
    traduzir_tipo_operacao,
    uf_origem_destino,
)
from app.extractors.common import item, participante


def montar_linha_icms_ipi(meta: dict, registro_texto: str, campos: dict) -> dict:
    linha = {coluna: "" for coluna in campos["cabecalho"]}
    vl_operacao = campos.get("vl_opr", "") or campos.get("vl_item", "")
    vl_item = campos.get("vl_item", "") or campos.get("vl_opr", "")
    linha.update(
        {
            "CNPJ": meta.get("cnpj", ""),
            "Período": data_sped_para_date(meta.get("dt_ini", "")),
            "Registros": registro_texto,
            "Tipo Operação": traduzir_tipo_operacao(campos.get("ind_oper", "")),
            "Indicador Emitente": traduzir_indicador_emitente(campos.get("ind_emit", "")),
            "Situação": campos.get("cod_sit", ""),
            "Código Participante": campos.get("cod_part", ""),
            "CNPJ/CPF Participante": campos.get("doc_part", ""),
            "Nome Participante": campos.get("nome_part", ""),
            "UF Origem/Destino": uf_origem_destino(campos.get("uf_part", ""), meta.get("uf", "")),
            "Regime Tributário": campos.get("regime", ""),
            "Número Documento": campos.get("num_doc", ""),
            "Série": campos.get("serie", ""),
            "Modelo": campos.get("cod_mod", ""),
            "Chave NF-e": campos.get("chv_nfe", ""),
            "Data Documento": data_sped_para_date(campos.get("dt_doc", "")),
            "Data Entrada/Saída": data_sped_para_date(campos.get("dt_es", "")),
            "Vlr Documento": converter_decimal_sped(campos.get("vl_doc", "")),
            "Vlr Desconto NF": converter_decimal_sped(campos.get("vl_desc_nf", "")),
            "Vlr Mercadoria": converter_decimal_sped(campos.get("vl_merc", "")),
            "Vlr Frete": converter_decimal_sped(campos.get("vl_frt", "")),
            "Vlr Seguro": converter_decimal_sped(campos.get("vl_seg", "")),
            "Vlr Outras DA": converter_decimal_sped(campos.get("vl_out_da", "")),
            "Número Item": campos.get("num_item", ""),
            "Código Item": campos.get("cod_item", ""),
            "Descrição Item": campos.get("descr_item", ""),
            "Tipo Item": traduzir_tipo_item(campos.get("tipo_item", "")),
            "Código Barra": campos.get("cod_barra", ""),
            "NCM": campos.get("ncm", ""),
            "Vlr Operação": converter_decimal_sped(vl_operacao),
            "Vlr Item": converter_decimal_sped(vl_item),
            "Vlr Desconto Item": converter_decimal_sped(campos.get("vl_desc_item", "")),
            "Qtde": converter_decimal_sped(campos.get("qtd", "")),
            "Unidade Medida": campos.get("unid", ""),
            "Indicador Movimento": campos.get("ind_mov", ""),
            "CFOP": campos.get("cfop", ""),
            "Descrição CFOP": campos.get("descr_cfop", ""),
            "CFOP Faturamento": campos.get("cfop_faturamento", ""),
            "CST ICMS": campos.get("cst_icms", ""),
            "Vlr Base Cálculo ICMS": converter_decimal_sped(campos.get("vl_bc_icms", "")),
            "Vlr Redução Base ICMS": converter_decimal_sped(campos.get("vl_red_bc", "")),
            "Alíquota ICMS": converter_decimal_sped(campos.get("aliq_icms", "")),
            "Vlr ICMS": converter_decimal_sped(campos.get("vl_icms", "")),
            "Vlr Base Cálculo ICMS ST": converter_decimal_sped(campos.get("vl_bc_icms_st", "")),
            "Alíquota ICMS ST": converter_decimal_sped(campos.get("aliq_st", "")),
            "Vlr ICMS ST": converter_decimal_sped(campos.get("vl_icms_st", "")),
            "CST IPI": campos.get("cst_ipi", ""),
            "Vlr Base Cálculo IPI": converter_decimal_sped(campos.get("vl_bc_ipi", "")),
            "Alíquota IPI": converter_decimal_sped(campos.get("aliq_ipi", "")),
            "Vlr IPI": converter_decimal_sped(campos.get("vl_ipi", "")),
            "CST PIS": campos.get("cst_pis", ""),
            "Vlr Base Cálculo PIS": converter_decimal_sped(campos.get("vl_bc_pis", "")),
            "Alíquota PIS": converter_decimal_sped(campos.get("aliq_pis", "")),
            "Vlr PIS": converter_decimal_sped(campos.get("vl_pis", "")),
            "CST Cofins": campos.get("cst_cofins", ""),
            "Vlr Base Cálculo Cofins": converter_decimal_sped(campos.get("vl_bc_cofins", "")),
            "Alíquota Cofins": converter_decimal_sped(campos.get("aliq_cofins", "")),
            "Vlr Cofins": converter_decimal_sped(campos.get("vl_cofins", "")),
            "Conta Contábil": campos.get("cod_cta", ""),
        }
    )
    return linha


def extrair_efd_icms_ipi(partes: list[str], estado: dict) -> list[dict]:
    registro = safe_get(partes, 1)
    meta = estado["meta"]
    cabecalho = estado["cabecalho"]
    participantes = estado["participantes_0150"]
    itens = estado["itens_0200"]
    natureza = estado["natureza_0400"]
    linhas: list[dict] = []

    if registro == "C100":
        part = participante(participantes, safe_get(partes, 4))
        doc_part = part.get("cnpj") or part.get("cpf", "")
        estado["pai_C100_tem_C170"] = False
        estado["pai_C100"] = {
            "ind_oper": safe_get(partes, 2),
            "ind_emit": safe_get(partes, 3),
            "cod_part": safe_get(partes, 4),
            "doc_part": doc_part,
            "nome_part": part.get("nome", ""),
            "uf_part": part.get("uf", ""),
            "cod_mod": safe_get(partes, 5),
            "cod_sit": safe_get(partes, 6),
            "serie": safe_get(partes, 7),
            "num_doc": safe_get(partes, 8),
            "chv_nfe": safe_get(partes, 9),
            "dt_doc": safe_get(partes, 10),
            "dt_es": safe_get(partes, 11),
            "vl_doc": safe_get(partes, 12),
            "vl_desc_nf": safe_get(partes, 14),
            "vl_merc": safe_get(partes, 16),
            "vl_frt": safe_get(partes, 18),
            "vl_seg": safe_get(partes, 19),
            "vl_out_da": safe_get(partes, 20),
        }
    elif registro == "C170":
        estado["pai_C100_tem_C170"] = True
        cod_item = safe_get(partes, 3)
        it = item(itens, cod_item)
        campos = {
            **estado.get("pai_C100", {}),
            "num_item": safe_get(partes, 2),
            "cod_item": cod_item,
            "descr_item": it.get("descricao", safe_get(partes, 4)),
            "tipo_item": it.get("tipo_item", ""),
            "cod_barra": it.get("codigo_barra", ""),
            "ncm": it.get("ncm", ""),
            "qtd": safe_get(partes, 5),
            "unid": safe_get(partes, 6),
            "vl_item": safe_get(partes, 7),
            "vl_desc_item": safe_get(partes, 8),
            "ind_mov": safe_get(partes, 9),
            "cst_icms": safe_get(partes, 10),
            "cfop": safe_get(partes, 11),
            "descr_cfop": natureza.get(safe_get(partes, 11), ""),
            "vl_bc_icms": safe_get(partes, 13),
            "aliq_icms": safe_get(partes, 14),
            "vl_icms": safe_get(partes, 15),
            "vl_bc_icms_st": safe_get(partes, 16),
            "aliq_st": safe_get(partes, 17),
            "vl_icms_st": safe_get(partes, 18),
            "cst_ipi": safe_get(partes, 20),
            "vl_bc_ipi": safe_get(partes, 22),
            "aliq_ipi": safe_get(partes, 23),
            "vl_ipi": safe_get(partes, 24),
            "cst_pis": safe_get(partes, 25),
            "vl_bc_pis": safe_get(partes, 26),
            "aliq_pis": safe_get(partes, 27),
            "vl_pis": safe_get(partes, 30),
            "cst_cofins": safe_get(partes, 31),
            "vl_bc_cofins": safe_get(partes, 32),
            "aliq_cofins": safe_get(partes, 33),
            "vl_cofins": safe_get(partes, 36),
            "cod_cta": safe_get(partes, 37),
            "cabecalho": cabecalho,
        }
        linhas.append(montar_linha_icms_ipi(meta, "C100/C170 - Nota Fiscal", campos))
    elif registro == "C190":
        if estado.get("pai_C100_tem_C170"):
            return linhas
        campos = {
            **estado.get("pai_C100", {}),
            "cst_icms": safe_get(partes, 2),
            "cfop": safe_get(partes, 3),
            "aliq_icms": safe_get(partes, 4),
            "vl_opr": safe_get(partes, 5),
            "vl_bc_icms": safe_get(partes, 6),
            "vl_icms": safe_get(partes, 7),
            "vl_bc_icms_st": safe_get(partes, 8),
            "vl_icms_st": safe_get(partes, 9),
            "vl_red_bc": safe_get(partes, 10),
            "vl_ipi": safe_get(partes, 11),
            "cabecalho": cabecalho,
        }
        linhas.append(montar_linha_icms_ipi(meta, "C100/C190 - Analítico Nota Fiscal", campos))
    elif registro == "C500":
        part = participante(participantes, safe_get(partes, 4))
        estado["pai_C500"] = {
            "ind_oper": safe_get(partes, 2),
            "ind_emit": safe_get(partes, 3),
            "cod_part": safe_get(partes, 4),
            "doc_part": part.get("cnpj") or part.get("cpf", ""),
            "nome_part": part.get("nome", ""),
            "uf_part": part.get("uf", ""),
            "cod_mod": safe_get(partes, 5),
            "cod_sit": safe_get(partes, 6),
            "serie": safe_get(partes, 7),
            "num_doc": safe_get(partes, 10),
            "dt_doc": safe_get(partes, 11),
            "dt_es": safe_get(partes, 12),
            "vl_doc": safe_get(partes, 13),
            "vl_desc_nf": safe_get(partes, 14),
            "vl_merc": safe_get(partes, 15),
            "chv_nfe": safe_get(partes, 28),
            "cabecalho": cabecalho,
        }
    elif registro == "D700":
        part = participante(participantes, safe_get(partes, 4))
        estado["pai_D700"] = {
            "ind_oper": safe_get(partes, 2),
            "ind_emit": safe_get(partes, 3),
            "cod_part": safe_get(partes, 4),
            "doc_part": part.get("cnpj") or part.get("cpf", ""),
            "nome_part": part.get("nome", ""),
            "uf_part": part.get("uf", ""),
            "cod_mod": safe_get(partes, 5),
            "cod_sit": safe_get(partes, 6),
            "serie": safe_get(partes, 7),
            "num_doc": safe_get(partes, 8),
            "dt_doc": safe_get(partes, 9),
            "dt_es": safe_get(partes, 10),
            "vl_doc": safe_get(partes, 11),
            "vl_desc_nf": safe_get(partes, 12),
            "vl_merc": safe_get(partes, 13),
            "chv_nfe": safe_get(partes, 22),
            "cabecalho": cabecalho,
        }
    elif registro in {"C590", "D730"}:
        pai = "pai_C500" if registro == "C590" else "pai_D700"
        campos = {
            **estado.get(pai, {}),
            "cst_icms": safe_get(partes, 2),
            "cfop": safe_get(partes, 3),
            "aliq_icms": safe_get(partes, 4),
            "vl_opr": safe_get(partes, 5),
            "vl_bc_icms": safe_get(partes, 6),
            "vl_icms": safe_get(partes, 7),
            "vl_bc_icms_st": safe_get(partes, 8),
            "vl_icms_st": safe_get(partes, 9),
            "vl_red_bc": safe_get(partes, 10),
            "cabecalho": cabecalho,
        }
        texto = "C500/C590 - Energia Elétrica" if registro == "C590" else "D700/D730 - Comunicação/Telecom"
        linhas.append(montar_linha_icms_ipi(meta, texto, campos))
    elif registro == "K200":
        return linhas
    return linhas
