import os
import re
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict, Counter
from openpyxl import load_workbook, Workbook


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ARQUIVO_EXCEL = r"C:\OD Danilo\OneDrive - ALBIERI E ASSOCIADOS CONSULTORIA EMPRESARIAL LTDA\Projetos 2026\Hyundai\input 2021\Input_EFD-C 2021.xlsx"

PASTA_TXT_ORIGEM = r"C:\OD Danilo\OneDrive - ALBIERI E ASSOCIADOS CONSULTORIA EMPRESARIAL LTDA\Projetos 2026\Hyundai\input 2021\TESTE"

PASTA_TXT_SAIDA = r"C:\OD Danilo\OneDrive - ALBIERI E ASSOCIADOS CONSULTORIA EMPRESARIAL LTDA\Projetos 2026\Hyundai\input 2021\TESTE\AJUSTADOS"

PASTA_LOG = r"C:\OD Danilo\OneDrive - ALBIERI E ASSOCIADOS CONSULTORIA EMPRESARIAL LTDA\Projetos 2026\Hyundai\input 2021\TESTE\AJUSTADOS"

# CNPJ usado nos registros A010 e F010
CNPJ_ESTABELECIMENTO = "10394422000142"

# Se True, não insere linha exatamente igual caso ela já exista no TXT
EVITAR_DUPLICIDADE_EXATA = True

EXTENSOES_TXT = [".txt"]


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def criar_pastas():
    Path(PASTA_TXT_SAIDA).mkdir(parents=True, exist_ok=True)
    Path(PASTA_LOG).mkdir(parents=True, exist_ok=True)


def normalizar_linha_txt(linha):
    if linha is None:
        return ""

    linha = str(linha).strip()

    if not linha:
        return ""

    if not linha.startswith("|"):
        linha = "|" + linha

    if not linha.endswith("|"):
        linha += "|"

    # Remove espaços antes/depois dos pipes
    partes = [p.strip() for p in linha.split("|")]
    linha = "|".join(partes)

    if not linha.startswith("|"):
        linha = "|" + linha

    if not linha.endswith("|"):
        linha += "|"

    return linha


def get_registro(linha):
    partes = linha.split("|")
    if len(partes) > 2:
        return partes[1]
    return ""


def linha_inicio_reg(linha, reg):
    return linha.startswith(f"|{reg}|")


def parse_periodo_excel(valor):
    """
    Converte o campo PERIODO da planilha para MM/AAAA.
    Aceita data Excel, datetime, date ou texto.
    """
    if valor is None:
        return None

    if isinstance(valor, datetime):
        return valor.strftime("%m/%Y")

    if isinstance(valor, date):
        return valor.strftime("%m/%Y")

    texto = str(valor).strip()

    if not texto:
        return None

    # 05/2021 ou 05-2021
    m = re.search(r"(\d{1,2})[/-](\d{4})", texto)
    if m:
        mes = int(m.group(1))
        ano = int(m.group(2))
        return f"{mes:02d}/{ano}"

    # 2021-05-01
    m = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", texto)
    if m:
        ano = int(m.group(1))
        mes = int(m.group(2))
        return f"{mes:02d}/{ano}"

    # 01052021
    m = re.search(r"(\d{2})(\d{2})(\d{4})", texto)
    if m:
        mes = int(m.group(2))
        ano = int(m.group(3))
        return f"{mes:02d}/{ano}"

    return None


def extrair_periodo_txt(linhas):
    """
    Registro 0000 do EFD-Contribuições:
    |0000|COD_VER|COD_FIN|DT_INI|DT_FIN|NOME|CNPJ|...
    """
    for linha in linhas:
        if linha.startswith("|0000|"):
            partes = linha.split("|")

            if len(partes) > 3:
                dt_ini = partes[3].strip()

                if re.fullmatch(r"\d{8}", dt_ini):
                    mes = dt_ini[2:4]
                    ano = dt_ini[4:8]
                    return f"{mes}/{ano}"

    return None


def ler_txt(caminho):
    encodings = ["latin1", "utf-8-sig", "utf-8"]

    for enc in encodings:
        try:
            with open(caminho, "r", encoding=enc) as f:
                linhas = [normalizar_linha_txt(l) for l in f.readlines()]
                linhas = [l for l in linhas if l.strip()]
                return linhas, enc
        except UnicodeDecodeError:
            continue

    raise Exception("Não foi possível ler o TXT com latin1, utf-8-sig ou utf-8.")


def salvar_txt(caminho, linhas, encoding="latin1"):
    with open(caminho, "w", encoding=encoding, newline="\n") as f:
        for linha in linhas:
            linha = linha.rstrip("\r\n")
            if linha.strip():
                f.write(linha + "\n")


def nome_saida_sem_sobrescrever(pasta_saida, nome_original):
    base = Path(nome_original).stem
    ext = Path(nome_original).suffix

    saida = Path(pasta_saida) / f"{base}_AJUSTADO{ext}"

    contador = 1
    while saida.exists():
        saida = Path(pasta_saida) / f"{base}_AJUSTADO_{contador}{ext}"
        contador += 1

    return saida


# ============================================================
# LEITURA DA PLANILHA
# ============================================================

def carregar_dados_excel(caminho_excel):
    """
    Estrutura esperada em cada aba:
    Coluna A: PERIODO
    Coluna B: TXT

    Abas:
    0150
    0200
    0500
    A100
    F100
    """
    wb = load_workbook(caminho_excel, data_only=True, read_only=True)

    abas_esperadas = ["0150", "0200", "0500", "A100", "F100"]

    dados = defaultdict(lambda: defaultdict(list))

    print("=" * 100)
    print("LENDO PLANILHA DE INPUT")
    print("=" * 100)

    for aba in abas_esperadas:
        if aba not in wb.sheetnames:
            print(f"⚠️ Aba não encontrada: {aba}")
            continue

        ws = wb[aba]
        total_linhas = 0

        for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if idx == 1:
                continue

            periodo_raw = row[0] if len(row) > 0 else None
            txt_raw = row[1] if len(row) > 1 else None

            periodo = parse_periodo_excel(periodo_raw)
            linha_txt = normalizar_linha_txt(txt_raw)

            if not periodo or not linha_txt:
                continue

            dados[periodo][aba].append(linha_txt)
            total_linhas += 1

        print(f"✅ Aba {aba}: {total_linhas:,} linhas carregadas".replace(",", "."))

    print("=" * 100)
    print("PERÍODOS LOCALIZADOS NA PLANILHA")
    print("=" * 100)

    for periodo in sorted(dados.keys(), key=lambda x: (x.split("/")[1], x.split("/")[0])):
        qtd = sum(len(v) for v in dados[periodo].values())
        print(f"📅 {periodo}: {qtd:,} linhas".replace(",", "."))

    return dados


# ============================================================
# LOCALIZAÇÃO DE POSIÇÕES
# ============================================================

def encontrar_indice_primeiro_reg(linhas, reg):
    for i, linha in enumerate(linhas):
        if linha_inicio_reg(linha, reg):
            return i
    return None


def encontrar_indice_linha_exata(linhas, linha_exata):
    linha_exata = normalizar_linha_txt(linha_exata)

    for i, linha in enumerate(linhas):
        if normalizar_linha_txt(linha) == linha_exata:
            return i

    return None


def remover_duplicidades_exatas(novas_linhas, linhas_existentes):
    if not EVITAR_DUPLICIDADE_EXATA:
        return novas_linhas

    existentes = set(linhas_existentes)

    filtradas = []

    for linha in novas_linhas:
        if linha in existentes:
            continue

        filtradas.append(linha)

    return filtradas


# ============================================================
# INSERÇÕES
# ============================================================

def inserir_antes_primeiro_reg(linhas, novas_linhas, reg_alvo, reg_fallback_fechamento):
    """
    Insere antes do primeiro registro do mesmo tipo.
    Exemplo:
    0150 antes do primeiro 0150
    0200 antes do primeiro 0200
    0500 antes do primeiro 0500

    Se o registro não existir, insere antes do fechamento informado.
    """
    if not novas_linhas:
        return linhas, 0, ""

    idx = encontrar_indice_primeiro_reg(linhas, reg_alvo)

    observacao = ""

    if idx is None:
        idx = encontrar_indice_primeiro_reg(linhas, reg_fallback_fechamento)
        observacao = f"Registro {reg_alvo} não encontrado. Inserido antes de {reg_fallback_fechamento}."

    if idx is None:
        idx = len(linhas)
        observacao = f"Registro {reg_alvo} e fechamento {reg_fallback_fechamento} não encontrados. Inserido no final."

    linhas = linhas[:idx] + novas_linhas + linhas[idx:]

    return linhas, len(novas_linhas), observacao


def inserir_apos_linha_exata(linhas, novas_linhas, linha_ancora, reg_fallback_fechamento):
    """
    Insere após uma linha exata.
    Exemplo:
    após |A010|10394422000142|
    após |F010|10394422000142|

    Se a âncora não existir, insere antes do fechamento do bloco.
    """
    if not novas_linhas:
        return linhas, 0, ""

    idx = encontrar_indice_linha_exata(linhas, linha_ancora)

    observacao = ""

    if idx is not None:
        posicao_insercao = idx + 1
    else:
        idx_fallback = encontrar_indice_primeiro_reg(linhas, reg_fallback_fechamento)

        if idx_fallback is not None:
            posicao_insercao = idx_fallback
            observacao = f"Âncora {linha_ancora} não encontrada. Inserido antes de {reg_fallback_fechamento}."
        else:
            posicao_insercao = len(linhas)
            observacao = f"Âncora {linha_ancora} e fechamento {reg_fallback_fechamento} não encontrados. Inserido no final."

    linhas = linhas[:posicao_insercao] + novas_linhas + linhas[posicao_insercao:]

    return linhas, len(novas_linhas), observacao


def inserir_dados_periodo(linhas, dados_periodo):
    resumo = {
        "0150_inseridos": 0,
        "0200_inseridos": 0,
        "0500_inseridos": 0,
        "A100_A170_inseridos": 0,
        "F100_inseridos": 0,
        "observacoes": [],
    }

    # ========================================================
    # 0150 antes do primeiro 0150
    # ========================================================
    linhas_0150 = dados_periodo.get("0150", [])
    linhas_0150 = remover_duplicidades_exatas(linhas_0150, linhas)

    linhas, qtd, obs = inserir_antes_primeiro_reg(
        linhas=linhas,
        novas_linhas=linhas_0150,
        reg_alvo="0150",
        reg_fallback_fechamento="0990"
    )

    resumo["0150_inseridos"] = qtd
    if obs:
        resumo["observacoes"].append(obs)

    # ========================================================
    # 0200 antes do primeiro 0200
    # ========================================================
    linhas_0200 = dados_periodo.get("0200", [])
    linhas_0200 = remover_duplicidades_exatas(linhas_0200, linhas)

    linhas, qtd, obs = inserir_antes_primeiro_reg(
        linhas=linhas,
        novas_linhas=linhas_0200,
        reg_alvo="0200",
        reg_fallback_fechamento="0990"
    )

    resumo["0200_inseridos"] = qtd
    if obs:
        resumo["observacoes"].append(obs)

    # ========================================================
    # 0500 antes do primeiro 0500
    # ========================================================
    linhas_0500 = dados_periodo.get("0500", [])
    linhas_0500 = remover_duplicidades_exatas(linhas_0500, linhas)

    linhas, qtd, obs = inserir_antes_primeiro_reg(
        linhas=linhas,
        novas_linhas=linhas_0500,
        reg_alvo="0500",
        reg_fallback_fechamento="0990"
    )

    resumo["0500_inseridos"] = qtd
    if obs:
        resumo["observacoes"].append(obs)

    # ========================================================
    # A100/A170 após |A010|10394422000142|
    # ========================================================
    linhas_a100 = dados_periodo.get("A100", [])
    linhas_a100 = remover_duplicidades_exatas(linhas_a100, linhas)

    linha_ancora_a010 = f"|A010|{CNPJ_ESTABELECIMENTO}|"

    linhas, qtd, obs = inserir_apos_linha_exata(
        linhas=linhas,
        novas_linhas=linhas_a100,
        linha_ancora=linha_ancora_a010,
        reg_fallback_fechamento="A990"
    )

    resumo["A100_A170_inseridos"] = qtd
    if obs:
        resumo["observacoes"].append(obs)

    # ========================================================
    # F100 após |F010|10394422000142|
    # ========================================================
    linhas_f100 = dados_periodo.get("F100", [])
    linhas_f100 = remover_duplicidades_exatas(linhas_f100, linhas)

    linha_ancora_f010 = f"|F010|{CNPJ_ESTABELECIMENTO}|"

    linhas, qtd, obs = inserir_apos_linha_exata(
        linhas=linhas,
        novas_linhas=linhas_f100,
        linha_ancora=linha_ancora_f010,
        reg_fallback_fechamento="F990"
    )

    resumo["F100_inseridos"] = qtd
    if obs:
        resumo["observacoes"].append(obs)

    return linhas, resumo


# ============================================================
# TOTALIZADORES
# ============================================================

def contar_linhas_bloco(linhas, reg_inicio, reg_fim):
    idx_ini = encontrar_indice_primeiro_reg(linhas, reg_inicio)
    idx_fim = encontrar_indice_primeiro_reg(linhas, reg_fim)

    if idx_ini is None or idx_fim is None:
        return None

    return idx_fim - idx_ini + 1


def atualizar_linha_totalizador(linhas, reg_totalizador, quantidade):
    for i, linha in enumerate(linhas):
        if linha_inicio_reg(linha, reg_totalizador):
            linhas[i] = f"|{reg_totalizador}|{quantidade}|"
            return True

    return False


def atualizar_totalizadores_blocos(linhas):
    qtd_0990 = contar_linhas_bloco(linhas, "0001", "0990")
    if qtd_0990 is not None:
        atualizar_linha_totalizador(linhas, "0990", qtd_0990)

    qtd_a990 = contar_linhas_bloco(linhas, "A001", "A990")
    if qtd_a990 is not None:
        atualizar_linha_totalizador(linhas, "A990", qtd_a990)

    qtd_f990 = contar_linhas_bloco(linhas, "F001", "F990")
    if qtd_f990 is not None:
        atualizar_linha_totalizador(linhas, "F990", qtd_f990)

    return linhas


def remover_9900_existentes(linhas):
    return [linha for linha in linhas if not linha_inicio_reg(linha, "9900")]


def registros_em_ordem_estrutural(linhas):
    ordem = []

    for linha in linhas:
        reg = get_registro(linha)

        if not reg:
            continue

        if reg not in ordem:
            ordem.append(reg)

    return ordem


def montar_9900(linhas_sem_9900):
    contagem = Counter()

    for linha in linhas_sem_9900:
        reg = get_registro(linha)

        if reg:
            contagem[reg] += 1

    ordem = registros_em_ordem_estrutural(linhas_sem_9900)

    if "9900" not in ordem:
        if "9990" in ordem:
            ordem.insert(ordem.index("9990"), "9900")
        elif "9999" in ordem:
            ordem.insert(ordem.index("9999"), "9900")
        else:
            ordem.append("9900")

    qtd_linhas_9900 = len(ordem)
    contagem["9900"] = qtd_linhas_9900

    linhas_9900 = []

    for reg in ordem:
        qtd = contagem.get(reg, 0)

        if reg == "9900":
            qtd = qtd_linhas_9900

        linhas_9900.append(f"|9900|{reg}|{qtd}|")

    return linhas_9900


def inserir_9900_apos_9001(linhas_sem_9900, linhas_9900):
    idx_9001 = encontrar_indice_primeiro_reg(linhas_sem_9900, "9001")

    if idx_9001 is not None:
        posicao = idx_9001 + 1
        return linhas_sem_9900[:posicao] + linhas_9900 + linhas_sem_9900[posicao:]

    idx_9990 = encontrar_indice_primeiro_reg(linhas_sem_9900, "9990")

    if idx_9990 is not None:
        return linhas_sem_9900[:idx_9990] + linhas_9900 + linhas_sem_9900[idx_9990:]

    return linhas_sem_9900 + linhas_9900


def atualizar_9990(linhas):
    idx_9001 = encontrar_indice_primeiro_reg(linhas, "9001")
    idx_9990 = encontrar_indice_primeiro_reg(linhas, "9990")

    if idx_9001 is None or idx_9990 is None:
        return linhas

    qtd_9990 = idx_9990 - idx_9001 + 1
    atualizar_linha_totalizador(linhas, "9990", qtd_9990)

    return linhas


def atualizar_9999(linhas):
    qtd_total = len(linhas)
    atualizar_linha_totalizador(linhas, "9999", qtd_total)

    return linhas


def recalcular_totalizadores(linhas):
    linhas = atualizar_totalizadores_blocos(linhas)

    linhas_sem_9900 = remover_9900_existentes(linhas)

    linhas_9900 = montar_9900(linhas_sem_9900)

    linhas = inserir_9900_apos_9001(linhas_sem_9900, linhas_9900)

    linhas = atualizar_9990(linhas)

    linhas = atualizar_9999(linhas)

    return linhas


# ============================================================
# LOG
# ============================================================

def salvar_log_excel(logs):
    agora = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_log = Path(PASTA_LOG) / f"LOG_INCLUSAO_EFD_CONTRIBUICOES_{agora}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "LOG"

    cabecalho = [
        "arquivo_origem",
        "arquivo_saida",
        "periodo_txt",
        "status",
        "erro",
        "0150_inseridos",
        "0200_inseridos",
        "0500_inseridos",
        "A100_A170_inseridos",
        "F100_inseridos",
        "total_inserido",
        "observacoes",
    ]

    ws.append(cabecalho)

    for log in logs:
        ws.append([
            log.get("arquivo_origem", ""),
            log.get("arquivo_saida", ""),
            log.get("periodo_txt", ""),
            log.get("status", ""),
            log.get("erro", ""),
            log.get("0150_inseridos", 0),
            log.get("0200_inseridos", 0),
            log.get("0500_inseridos", 0),
            log.get("A100_A170_inseridos", 0),
            log.get("F100_inseridos", 0),
            log.get("total_inserido", 0),
            log.get("observacoes", ""),
        ])

    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter

        for cell in col:
            valor = str(cell.value) if cell.value is not None else ""
            max_len = max(max_len, len(valor))

        ws.column_dimensions[col_letter].width = min(max_len + 2, 80)

    wb.save(caminho_log)

    print(f"📘 Log salvo em: {caminho_log}")


# ============================================================
# PROCESSAMENTO
# ============================================================

def listar_txts(pasta):
    arquivos = []

    for raiz, _, nomes in os.walk(pasta):
        for nome in nomes:
            if Path(nome).suffix.lower() in EXTENSOES_TXT:
                arquivos.append(Path(raiz) / nome)

    return arquivos


def processar_arquivo_txt(caminho_txt, dados_excel):
    log = {
        "arquivo_origem": str(caminho_txt),
        "arquivo_saida": "",
        "periodo_txt": "",
        "status": "",
        "erro": "",
        "0150_inseridos": 0,
        "0200_inseridos": 0,
        "0500_inseridos": 0,
        "A100_A170_inseridos": 0,
        "F100_inseridos": 0,
        "total_inserido": 0,
        "observacoes": "",
    }

    try:
        linhas, encoding = ler_txt(caminho_txt)

        periodo_txt = extrair_periodo_txt(linhas)
        log["periodo_txt"] = periodo_txt or ""

        if not periodo_txt:
            log["status"] = "ERRO"
            log["erro"] = "Não foi possível identificar o período no registro 0000"
            return log

        if periodo_txt not in dados_excel:
            log["status"] = "SEM_DADOS_PARA_PERIODO"
            log["erro"] = f"Não existem dados na planilha para o período {periodo_txt}"
            return log

        dados_periodo = dados_excel[periodo_txt]

        linhas, resumo = inserir_dados_periodo(linhas, dados_periodo)

        linhas = recalcular_totalizadores(linhas)

        caminho_saida = nome_saida_sem_sobrescrever(
            PASTA_TXT_SAIDA,
            Path(caminho_txt).name
        )

        salvar_txt(caminho_saida, linhas, encoding=encoding)

        total_inserido = (
            resumo["0150_inseridos"]
            + resumo["0200_inseridos"]
            + resumo["0500_inseridos"]
            + resumo["A100_A170_inseridos"]
            + resumo["F100_inseridos"]
        )

        log["arquivo_saida"] = str(caminho_saida)
        log["0150_inseridos"] = resumo["0150_inseridos"]
        log["0200_inseridos"] = resumo["0200_inseridos"]
        log["0500_inseridos"] = resumo["0500_inseridos"]
        log["A100_A170_inseridos"] = resumo["A100_A170_inseridos"]
        log["F100_inseridos"] = resumo["F100_inseridos"]
        log["total_inserido"] = total_inserido
        log["observacoes"] = " | ".join(resumo["observacoes"])
        log["status"] = "PROCESSADO"

        return log

    except Exception as e:
        log["status"] = "ERRO"
        log["erro"] = str(e)
        return log


def main():
    criar_pastas()

    print("=" * 100)
    print("INCLUSÃO DE REGISTROS NO EFD-CONTRIBUIÇÕES")
    print("=" * 100)
    print(f"📘 Excel de entrada : {ARQUIVO_EXCEL}")
    print(f"📁 Pasta TXT origem : {PASTA_TXT_ORIGEM}")
    print(f"📁 Pasta TXT saída  : {PASTA_TXT_SAIDA}")
    print(f"📁 Pasta LOG        : {PASTA_LOG}")
    print(f"🏢 CNPJ A010/F010   : {CNPJ_ESTABELECIMENTO}")
    print("=" * 100)

    dados_excel = carregar_dados_excel(ARQUIVO_EXCEL)

    arquivos_txt = listar_txts(PASTA_TXT_ORIGEM)

    print()
    print("=" * 100)
    print("INICIANDO PROCESSAMENTO DOS TXT")
    print("=" * 100)
    print(f"📄 TXT encontrados: {len(arquivos_txt):,}".replace(",", "."))
    print("=" * 100)

    logs = []

    for idx, caminho_txt in enumerate(arquivos_txt, start=1):
        print()
        print("-" * 100)
        print(f"📄 [{idx}/{len(arquivos_txt)}] Processando: {caminho_txt}")

        log = processar_arquivo_txt(caminho_txt, dados_excel)
        logs.append(log)

        print(f"📅 Período TXT : {log.get('periodo_txt')}")
        print(f"📌 Status      : {log.get('status')}")

        if log.get("status") == "PROCESSADO":
            print(f"✅ 0150 inseridos      : {log.get('0150_inseridos')}")
            print(f"✅ 0200 inseridos      : {log.get('0200_inseridos')}")
            print(f"✅ 0500 inseridos      : {log.get('0500_inseridos')}")
            print(f"✅ A100/A170 inseridos : {log.get('A100_A170_inseridos')}")
            print(f"✅ F100 inseridos      : {log.get('F100_inseridos')}")
            print(f"✅ Total inserido      : {log.get('total_inserido')}")
            print(f"💾 Arquivo saída       : {log.get('arquivo_saida')}")

            if log.get("observacoes"):
                print(f"⚠️ Observações         : {log.get('observacoes')}")
        else:
            print(f"⚠️ Erro/Observação: {log.get('erro')}")

    print()
    print("=" * 100)
    print("PROCESSAMENTO FINALIZADO")
    print("=" * 100)

    salvar_log_excel(logs)


if __name__ == "__main__":
    main()