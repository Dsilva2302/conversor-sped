"""Extractor for EFD-Contribuicoes."""

from __future__ import annotations

from app.core.formatadores import (
    converter_decimal_sped,
    data_sped_para_date,
    safe_get,
    traduzir_tipo_item,
    traduzir_tipo_operacao,
    uf_origem_destino,
)
from app.extractors.common import item, participante


def montar_linha_contribuicoes(meta: dict, registro_texto: str, campos: dict) -> dict:
    linha = {coluna: "" for coluna in campos["cabecalho"]}
    vl_mercadoria_operacao = campos.get("vl_merc", "") or campos.get("vl_item", "")
    vl_item = campos.get("vl_item", "") or campos.get("vl_merc", "")
    linha.update(
        {
            "CNPJ": meta.get("cnpj", ""),
            "Período": data_sped_para_date(meta.get("dt_ini", "")),
            "Registros": registro_texto,
            "Tipo Operação": traduzir_tipo_operacao(campos.get("ind_oper", "")),
            "Situação": campos.get("cod_sit", ""),
            "Código Participante": campos.get("cod_part", ""),
            "CNPJ Participante": campos.get("cnpj_part", ""),
            "CPF Participante": campos.get("cpf_part", ""),
            "Nome Participante": campos.get("nome_part", ""),
            "Regime Tributário": campos.get("regime", ""),
            "UF Origem/Destino": uf_origem_destino(campos.get("uf_part", ""), meta.get("uf", "")),
            "Número Documento": campos.get("num_doc", ""),
            "Série": campos.get("serie", ""),
            "Chave NF-e": campos.get("chv_nfe", ""),
            "Data Documento": data_sped_para_date(campos.get("dt_doc", "")),
            "Data Entrada/Saída": data_sped_para_date(campos.get("dt_es", "")),
            "Vlr Documento": converter_decimal_sped(campos.get("vl_doc", "")),
            "Vlr Desconto NF": converter_decimal_sped(campos.get("vl_desc_nf", "")),
            "Vlr Mercadoria/Operação": converter_decimal_sped(vl_mercadoria_operacao),
            "Vlr Frete": converter_decimal_sped(campos.get("vl_frt", "")),
            "Vlr Seguro": converter_decimal_sped(campos.get("vl_seg", "")),
            "Vlr Outras DA": converter_decimal_sped(campos.get("vl_out_da", "")),
            "Número Item": campos.get("num_item", ""),
            "Código Item": campos.get("cod_item", ""),
            "Descrição Complementar": campos.get("descr_compl", ""),
            "Descrição Item": campos.get("descr_item", ""),
            "NCM": campos.get("ncm", ""),
            "Código Serviço": campos.get("cod_serv", ""),
            "Código Barra": campos.get("cod_barra", ""),
            "Tipo Item": traduzir_tipo_item(campos.get("tipo_item", "")),
            "Vlr Item": converter_decimal_sped(vl_item),
            "Qtde": converter_decimal_sped(campos.get("qtd", "")),
            "Unidade Medida": campos.get("unid", ""),
            "Vlr Desconto Item": converter_decimal_sped(campos.get("vl_desc_item", "")),
            "Natureza Crédito": campos.get("nat_bc_cred", ""),
            "CFOP": campos.get("cfop", ""),
            "Descrição CFOP": campos.get("descr_cfop", ""),
            "CFOP Faturamento": campos.get("cfop_faturamento", ""),
            "CST ICMS": campos.get("cst_icms", ""),
            "CST IPI": campos.get("cst_ipi", ""),
            "CST PIS": campos.get("cst_pis", ""),
            "Vlr Base Cálculo PIS": converter_decimal_sped(campos.get("vl_bc_pis", "")),
            "Qtde Base Cálculo PIS": converter_decimal_sped(campos.get("qtd_bc_pis", "")),
            "Alíquota PIS": converter_decimal_sped(campos.get("aliq_pis", "")),
            "Qtde Alíquota PIS": converter_decimal_sped(campos.get("qtd_aliq_pis", "")),
            "Vlr PIS": converter_decimal_sped(campos.get("vl_pis", "")),
            "CST Cofins": campos.get("cst_cofins", ""),
            "Vlr Base Cálculo Cofins": converter_decimal_sped(campos.get("vl_bc_cofins", "")),
            "Qtde Base Cálculo Cofins": converter_decimal_sped(campos.get("qtd_bc_cofins", "")),
            "Alíquota Cofins": converter_decimal_sped(campos.get("aliq_cofins", "")),
            "Qtde Alíquota Cofins": converter_decimal_sped(campos.get("qtd_aliq_cofins", "")),
            "Vlr Cofins": converter_decimal_sped(campos.get("vl_cofins", "")),
            "Conta Contábil": campos.get("cod_cta", ""),
            "Débito/Crédito": campos.get("deb_cred", ""),
        }
    )
    return linha


def extrair_efd_contribuicoes(partes: list[str], estado: dict) -> list[dict]:
    registro = safe_get(partes, 1)
    meta = estado["meta"]
    linhas: list[dict] = []
    cabecalho = estado["cabecalho"]
    participantes = estado["participantes_0150"]
    itens = estado["itens_0200"]
    natureza = estado["natureza_0400"]

    if registro == "A100":
        part = participante(participantes, safe_get(partes, 4))
        estado["pai_A100"] = {
            "ind_oper": safe_get(partes, 2),
            "cod_sit": safe_get(partes, 5),
            "cod_part": safe_get(partes, 4),
            "cnpj_part": part.get("cnpj", ""),
            "cpf_part": part.get("cpf", ""),
            "nome_part": part.get("nome", ""),
            "uf_part": part.get("uf", ""),
            "serie": safe_get(partes, 6),
            "num_doc": safe_get(partes, 8),
            "chv_nfe": safe_get(partes, 9),
            "dt_doc": safe_get(partes, 10),
            "dt_es": safe_get(partes, 11),
            "vl_doc": safe_get(partes, 12),
            "vl_desc_nf": safe_get(partes, 14),
            "vl_merc": safe_get(partes, 12),
        }
    elif registro == "A170":
        cod_item = safe_get(partes, 3)
        it = item(itens, cod_item)
        campos = {
            **estado.get("pai_A100", {}),
            "num_item": safe_get(partes, 2),
            "cod_item": cod_item,
            "descr_compl": safe_get(partes, 4),
            "descr_item": it.get("descricao", ""),
            "ncm": it.get("ncm", ""),
            "cod_serv": it.get("codigo_servico", ""),
            "cod_barra": it.get("codigo_barra", ""),
            "tipo_item": it.get("tipo_item", ""),
            "vl_item": safe_get(partes, 5),
            "vl_desc_item": safe_get(partes, 6),
            "nat_bc_cred": safe_get(partes, 7),
            "cst_pis": safe_get(partes, 9),
            "vl_bc_pis": safe_get(partes, 10),
            "aliq_pis": safe_get(partes, 11),
            "vl_pis": safe_get(partes, 12),
            "cst_cofins": safe_get(partes, 13),
            "vl_bc_cofins": safe_get(partes, 14),
            "aliq_cofins": safe_get(partes, 15),
            "vl_cofins": safe_get(partes, 16),
            "cod_cta": safe_get(partes, 17),
            "cabecalho": cabecalho,
        }
        linhas.append(montar_linha_contribuicoes(meta, "A100/A170 - Nota Fiscal de Serviço", campos))
    elif registro == "C100":
        part = participante(participantes, safe_get(partes, 4))
        estado["pai_C100"] = {
            "ind_oper": safe_get(partes, 2),
            "cod_sit": safe_get(partes, 6),
            "cod_part": safe_get(partes, 4),
            "cnpj_part": part.get("cnpj", ""),
            "cpf_part": part.get("cpf", ""),
            "nome_part": part.get("nome", ""),
            "uf_part": part.get("uf", ""),
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
        cod_item = safe_get(partes, 3)
        it = item(itens, cod_item)
        campos = {
            **estado.get("pai_C100", {}),
            "num_item": safe_get(partes, 2),
            "cod_item": cod_item,
            "descr_compl": safe_get(partes, 4),
            "descr_item": it.get("descricao", ""),
            "ncm": it.get("ncm", ""),
            "cod_barra": it.get("codigo_barra", ""),
            "tipo_item": it.get("tipo_item", ""),
            "qtd": safe_get(partes, 5),
            "unid": safe_get(partes, 6),
            "vl_item": safe_get(partes, 7),
            "vl_desc_item": safe_get(partes, 8),
            "cfop": safe_get(partes, 11),
            "cst_icms": safe_get(partes, 10),
            "cst_ipi": safe_get(partes, 20),
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
        linhas.append(montar_linha_contribuicoes(meta, "C100/C170 - Nota Fiscal", campos))
    elif registro == "F100":
        campos = {
            "ind_oper": safe_get(partes, 2),
            "cod_part": safe_get(partes, 3),
            "cod_item": safe_get(partes, 4),
            "dt_doc": safe_get(partes, 10),
            "vl_item": safe_get(partes, 11),
            "cst_pis": safe_get(partes, 7),
            "vl_bc_pis": safe_get(partes, 12),
            "aliq_pis": safe_get(partes, 13),
            "vl_pis": safe_get(partes, 14),
            "cst_cofins": safe_get(partes, 15),
            "vl_bc_cofins": safe_get(partes, 16),
            "aliq_cofins": safe_get(partes, 17),
            "vl_cofins": safe_get(partes, 18),
            "nat_bc_cred": safe_get(partes, 19),
            "cod_cta": safe_get(partes, 20),
            "cabecalho": cabecalho,
        }
        linhas.append(montar_linha_contribuicoes(meta, "F100 - Demais Documentos e Operações", campos))
    return linhas
