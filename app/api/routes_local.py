"""Simple local browser interface for converting SPED TXT files."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys
import time
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.core.parser_sped import processar_arquivo_sped
from app.database.models import Usuario
from app.database.session import SessionLocal
from app.services.credito_service import CUSTO_POR_RELATORIO, adicionar_creditos, consumir_creditos, saldo_creditos
from app.utils.arquivos import nome_interno_seguro, validar_txt_upload
from app.utils.seguranca import criar_token_acesso, decodificar_token, gerar_hash_senha, verificar_senha

router = APIRouter(tags=["programa-local"])

LOCAL_ROOT = settings.STORAGE_ROOT / "local"
JOBS: dict[str, dict] = {}


def _asset_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets"
    return Path("assets")


def _db() -> Session:
    return SessionLocal()


def _usuario_logado(request: Request, db: Session) -> Usuario | None:
    token = request.cookies.get("conversor_token")
    if not token:
        return None
    try:
        usuario_id = int(decodificar_token(token))
    except ValueError:
        return None
    return db.get(Usuario, usuario_id)


def _html_base(conteudo: str, usuario: Usuario | None = None, saldo: Decimal | None = None) -> str:
    nav = ""
    if usuario:
        nav = f"""
            <nav>
                <span>{usuario.nome}</span>
                <strong id="saldo-creditos">Creditos: R$ {saldo or Decimal("0.00")}</strong>
                <a href="/creditos">Comprar creditos</a>
                <a href="/sair">Sair</a>
            </nav>
        """
    return f"""
    <!doctype html>
    <html lang="pt-br">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Conversor SPED para Excel</title>
        <link rel="icon" href="/assets/sped_excel_icon.png">
        <style>
            :root {{
                color-scheme: light;
                font-family: Arial, Helvetica, sans-serif;
                color: #1f2937;
                background: #eef2f6;
            }}
            body {{ margin: 0; }}
            header {{
                background: #123c69;
                color: white;
                padding: 22px 34px;
            }}
            header h1 {{ margin: 0 0 4px; font-size: 26px; }}
            header p {{ margin: 0; opacity: .9; }}
            nav {{
                margin-top: 14px;
                display: flex;
                gap: 14px;
                align-items: center;
                flex-wrap: wrap;
            }}
            nav a {{
                color: white;
                font-weight: 700;
            }}
            main {{
                max-width: 980px;
                margin: 28px auto;
                background: white;
                border: 1px solid #d8dee8;
                border-radius: 8px;
                padding: 28px;
                box-shadow: 0 10px 28px rgba(31, 41, 55, .08);
            }}
            .upload {{
                border: 2px dashed #8aa4c2;
                background: #f8fbff;
                border-radius: 8px;
                padding: 24px;
            }}
            input[type=file] {{
                width: 100%;
                padding: 12px;
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                box-sizing: border-box;
            }}
            input[type=text], input[type=email], input[type=password], input[type=number], select {{
                width: 100%;
                padding: 12px;
                margin-top: 6px;
                margin-bottom: 12px;
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                box-sizing: border-box;
            }}
            label {{ display: block; font-weight: 700; margin-top: 10px; }}
            button, .button {{
                display: inline-block;
                margin-top: 16px;
                padding: 12px 18px;
                border: 0;
                border-radius: 6px;
                background: #0f5db8;
                color: white;
                font-weight: 700;
                text-decoration: none;
                cursor: pointer;
            }}
            button:hover, .button:hover {{ background: #0b4d99; }}
            button:disabled {{ opacity: .65; cursor: wait; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 18px;
                font-size: 13px;
                table-layout: fixed;
            }}
            th, td {{
                border-bottom: 1px solid #e5e7eb;
                padding: 8px 7px;
                text-align: left;
                vertical-align: top;
                overflow-wrap: anywhere;
                word-break: break-word;
                white-space: normal;
                max-width: 0;
            }}
            th {{ background: #f3f6fa; }}
            th:nth-child(1), td:nth-child(1) {{ width: 28%; }}
            th:nth-child(2), td:nth-child(2) {{ width: 12%; }}
            th:nth-child(3), td:nth-child(3) {{ width: 13%; }}
            th:nth-child(4), td:nth-child(4) {{ width: 7%; }}
            th:nth-child(5), td:nth-child(5) {{ width: 9%; }}
            th:nth-child(6), td:nth-child(6) {{ width: 19%; }}
            th:nth-child(7), td:nth-child(7) {{ width: 12%; }}
            #resultado {{
                margin-top: 20px;
                max-width: 100%;
                overflow-x: auto;
            }}
            #resultado table {{ min-width: 760px; }}
            .ok {{ color: #067647; font-weight: 700; }}
            .erro {{ color: #b42318; font-weight: 700; }}
            .muted {{ color: #667085; }}
            .alert {{
                border: 1px solid #fecdca;
                background: #fffbfa;
                color: #b42318;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 14px;
            }}
            .actions {{ margin-top: 18px; }}
            .progress-wrap {{
                display: none;
                margin-top: 22px;
                border: 1px solid #d8dee8;
                border-radius: 8px;
                padding: 18px;
                background: #fbfcfe;
            }}
            .progress-bar {{
                height: 22px;
                background: #e6edf5;
                border-radius: 999px;
                overflow: hidden;
            }}
            .progress-fill {{
                height: 100%;
                width: 0%;
                background: #0f5db8;
                transition: width .25s ease;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 12px;
                margin-top: 14px;
            }}
            .stat {{
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 10px;
            }}
            .stat strong {{ display: block; font-size: 20px; margin-top: 4px; }}
            #mensagem {{
                margin-top: 12px;
                font-weight: 700;
                overflow-wrap: anywhere;
                word-break: break-word;
                line-height: 1.35;
                max-width: 100%;
            }}
            @media (max-width: 720px) {{
                .stats {{ grid-template-columns: 1fr; }}
                main {{ padding: 18px; margin: 16px; }}
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>Conversor SPED para Excel</h1>
            <p>Cada TXT convertido custa R$ 1,00 em creditos para baixar o Excel.</p>
            {nav}
        </header>
        <main>
            {conteudo}
        </main>
    </body>
    </html>
    """


@router.get("/", response_class=HTMLResponse)
def tela_inicial(request: Request):
    with _db() as db:
        usuario = _usuario_logado(request, db)
        if not usuario:
            return RedirectResponse("/login", status_code=303)
        saldo = saldo_creditos(db, usuario.id)
    return _html_base(
        """
        <form class="upload" id="form-conversao">
            <h2>Selecione os arquivos TXT do SPED</h2>
            <p class="muted">Pode selecionar um ou varios arquivos ao mesmo tempo.</p>
            <input id="arquivos" type="file" name="arquivos" accept=".txt" multiple required>
            <button id="botao" type="submit">Converter para Excel</button>
        </form>
        <p class="muted">Os arquivos TXT originais nao sao alterados.</p>

        <section class="progress-wrap" id="progresso">
            <div class="progress-bar">
                <div class="progress-fill" id="barra"></div>
            </div>
            <div class="stats">
                <div class="stat">Progresso<strong id="percentual">0%</strong></div>
                <div class="stat">Tempo decorrido<strong id="tempo">00:00</strong></div>
                <div class="stat">Arquivos<strong id="contador">0/0</strong></div>
            </div>
            <div id="mensagem">Aguardando...</div>
        </section>

        <section id="resultado"></section>

        <script>
            const form = document.getElementById("form-conversao");
            const botao = document.getElementById("botao");
            const progresso = document.getElementById("progresso");
            const barra = document.getElementById("barra");
            const percentual = document.getElementById("percentual");
            const tempo = document.getElementById("tempo");
            const contador = document.getElementById("contador");
            const mensagem = document.getElementById("mensagem");
            const resultado = document.getElementById("resultado");

            function formatarTempo(segundos) {
                segundos = Math.max(0, Math.floor(segundos || 0));
                const min = String(Math.floor(segundos / 60)).padStart(2, "0");
                const sec = String(segundos % 60).padStart(2, "0");
                return `${min}:${sec}`;
            }

            function texto(valor) {
                return String(valor ?? "");
            }

            function renderizarResultado(status) {
                resultado.innerHTML = "";
                const h2 = document.createElement("h2");
                h2.textContent = "Resultado da conversao";
                resultado.appendChild(h2);

                const actions = document.createElement("div");
                actions.className = "actions";
                if (status.zip_nome) {
                    const zip = document.createElement("button");
                    zip.className = "button";
                    zip.type = "button";
                    zip.textContent = "Baixar todos em ZIP";
                    zip.dataset.downloadUrl = `/baixar/${status.job_id}/${encodeURIComponent(status.zip_nome)}`;
                    zip.addEventListener("click", baixarComCredito);
                    actions.appendChild(zip);
                }
                resultado.appendChild(actions);

                const table = document.createElement("table");
                table.innerHTML = `
                    <thead>
                        <tr>
                            <th>Arquivo</th>
                            <th>Tipo</th>
                            <th>CNPJ</th>
                            <th>Linhas</th>
                            <th>Status</th>
                            <th>Erro</th>
                            <th>Download</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                `;
                const tbody = table.querySelector("tbody");
                for (const item of status.resultados || []) {
                    const tr = document.createElement("tr");
                    const classe = item.status_processamento === "CONCLUIDO" ? "ok" : "erro";
                    const tdArquivo = document.createElement("td");
                    const tdTipo = document.createElement("td");
                    const tdCnpj = document.createElement("td");
                    const tdLinhas = document.createElement("td");
                    const tdStatus = document.createElement("td");
                    const tdErro = document.createElement("td");
                    const tdDownload = document.createElement("td");
                    tdArquivo.textContent = texto(item.nome_original || item.arquivo_origem);
                    tdArquivo.title = texto(item.nome_original || item.arquivo_origem);
                    tdTipo.textContent = texto(item.tipo_sped_identificado);
                    tdCnpj.textContent = texto(item.cnpj);
                    tdLinhas.textContent = texto(item.quantidade_linhas_geradas || 0);
                    tdStatus.textContent = texto(item.status_processamento);
                    tdStatus.className = classe;
                    tdErro.textContent = texto(item.erro);
                    if (item.arquivo_excel_nome) {
                        const link = document.createElement("button");
                        link.type = "button";
                        link.className = "button";
                        link.dataset.downloadUrl = `/baixar/${status.job_id}/${encodeURIComponent(item.arquivo_excel_nome)}`;
                        link.textContent = "Baixar Excel (R$ 1)";
                        link.addEventListener("click", baixarComCredito);
                        tdDownload.appendChild(link);
                    }
                    tr.append(tdArquivo, tdTipo, tdCnpj, tdLinhas, tdStatus, tdErro, tdDownload);
                    tbody.appendChild(tr);
                }
                resultado.appendChild(table);
            }

            async function atualizarSaldo() {
                const resposta = await fetch("/saldo");
                if (!resposta.ok) return;
                const dados = await resposta.json();
                const alvo = document.getElementById("saldo-creditos");
                if (alvo) {
                    alvo.textContent = `Creditos: R$ ${dados.saldo}`;
                }
            }

            async function baixarComCredito(event) {
                const botaoDownload = event.currentTarget;
                const url = botaoDownload.dataset.downloadUrl;
                botaoDownload.disabled = true;
                const textoOriginal = botaoDownload.textContent;
                botaoDownload.textContent = "Verificando creditos...";
                try {
                    const resposta = await fetch(url + "?modo=json");
                    const dados = await resposta.json();
                    if (!resposta.ok || !dados.ok) {
                        alert(dados.mensagem || "Nao foi possivel baixar o arquivo.");
                        if (dados.saldo !== undefined) {
                            const alvo = document.getElementById("saldo-creditos");
                            if (alvo) alvo.textContent = `Creditos: R$ ${dados.saldo}`;
                        }
                        return;
                    }
                    await atualizarSaldo();
                    window.location.href = dados.download_url;
                } catch (erro) {
                    alert("Nao foi possivel baixar o arquivo.");
                } finally {
                    botaoDownload.disabled = false;
                    botaoDownload.textContent = textoOriginal;
                }
            }

            async function acompanhar(jobId) {
                const timer = setInterval(async () => {
                    const resposta = await fetch(`/status/${jobId}`);
                    const status = await resposta.json();
                    const pct = Math.max(0, Math.min(100, status.percentual || 0));
                    barra.style.width = `${pct}%`;
                    percentual.textContent = `${pct}%`;
                    tempo.textContent = formatarTempo(status.tempo_decorrido);
                    contador.textContent = `${status.arquivos_processados || 0}/${status.total_arquivos || 0}`;
                    mensagem.textContent = status.mensagem || "";
                    mensagem.title = status.mensagem || "";

                    if (status.status === "CONCLUIDO" || status.status === "ERRO") {
                        clearInterval(timer);
                        botao.disabled = false;
                        botao.textContent = "Converter para Excel";
                        renderizarResultado(status);
                    }
                }, 1000);
            }

            form.addEventListener("submit", async (event) => {
                event.preventDefault();
                resultado.innerHTML = "";
                progresso.style.display = "block";
                botao.disabled = true;
                botao.textContent = "Convertendo...";
                barra.style.width = "0%";
                percentual.textContent = "0%";
                tempo.textContent = "00:00";
                contador.textContent = "0/0";
                mensagem.textContent = "Enviando arquivos...";

                const dados = new FormData(form);
                const resposta = await fetch("/converter", { method: "POST", body: dados });
                if (resposta.redirected) {
                    window.location.href = resposta.url;
                    return;
                }
                if (resposta.status === 401) {
                    window.location.href = "/login";
                    return;
                }
                if (!resposta.ok) {
                    mensagem.textContent = "Erro ao iniciar conversao.";
                    botao.disabled = false;
                    botao.textContent = "Converter para Excel";
                    return;
                }
                const inicio = await resposta.json();
                acompanhar(inicio.job_id);
            });
        </script>
        """,
        usuario,
        saldo,
    )


@router.get("/login", response_class=HTMLResponse)
def login_tela(request: Request, erro: str = ""):
    with _db() as db:
        if _usuario_logado(request, db):
            return RedirectResponse("/", status_code=303)
    alerta = f'<div class="alert">{erro}</div>' if erro else ""
    return _html_base(
        f"""
        <h2>Entrar</h2>
        {alerta}
        <form method="post" action="/login">
            <label>E-mail</label>
            <input type="email" name="email" required>
            <label>Senha</label>
            <input type="password" name="senha" required>
            <button type="submit">Entrar</button>
        </form>
        <p class="muted">Ainda nao tem conta? <a href="/cadastro">Criar cadastro</a></p>
        """
    )


@router.post("/login")
def login_post(email: str = Form(...), senha: str = Form(...)):
    with _db() as db:
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        if not usuario or not verificar_senha(senha, usuario.senha_hash):
            return RedirectResponse("/login?erro=E-mail ou senha invalidos", status_code=303)
        resposta = RedirectResponse("/", status_code=303)
        resposta.set_cookie("conversor_token", criar_token_acesso(str(usuario.id)), httponly=True, samesite="lax")
        return resposta


@router.get("/cadastro", response_class=HTMLResponse)
def cadastro_tela():
    return _html_base(
        """
        <h2>Criar cadastro</h2>
        <form method="post" action="/cadastro">
            <label>Nome</label>
            <input type="text" name="nome" required>
            <label>E-mail</label>
            <input type="email" name="email" required>
            <label>Senha</label>
            <input type="password" name="senha" required>
            <button type="submit">Criar conta</button>
        </form>
        <p class="muted">Ja tem conta? <a href="/login">Entrar</a></p>
        """
    )


@router.post("/cadastro")
def cadastro_post(nome: str = Form(...), email: str = Form(...), senha: str = Form(...)):
    with _db() as db:
        existente = db.query(Usuario).filter(Usuario.email == email).first()
        if existente:
            return RedirectResponse("/login?erro=E-mail ja cadastrado", status_code=303)
        usuario = Usuario(nome=nome, email=email, senha_hash=gerar_hash_senha(senha), ativo=True)
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        resposta = RedirectResponse("/", status_code=303)
        resposta.set_cookie("conversor_token", criar_token_acesso(str(usuario.id)), httponly=True, samesite="lax")
        return resposta


@router.get("/sair")
def sair():
    resposta = RedirectResponse("/login", status_code=303)
    resposta.delete_cookie("conversor_token")
    return resposta


@router.get("/creditos", response_class=HTMLResponse)
def creditos_tela(request: Request):
    with _db() as db:
        usuario = _usuario_logado(request, db)
        if not usuario:
            return RedirectResponse("/login", status_code=303)
        saldo = saldo_creditos(db, usuario.id)
    return _html_base(
        """
        <h2>Comprar creditos</h2>
        <p>Cada TXT convertido custa <strong>R$ 1,00</strong> para baixar o Excel.</p>
        <form method="post" action="/creditos/comprar">
            <label>Quantidade de creditos</label>
            <input type="number" name="quantidade" min="1" step="1" value="10" required>
            <label>Forma de pagamento</label>
            <select name="forma_pagamento">
                <option value="PIX">Pix</option>
                <option value="CREDIT_CARD">Cartao de credito</option>
            </select>
            <button type="submit">Comprar creditos</button>
        </form>
        <p class="muted">Versao local em modo teste: os creditos entram automaticamente para validar o fluxo de download.</p>
        """,
        usuario,
        saldo,
    )


@router.post("/creditos/comprar")
def creditos_comprar(
    request: Request,
    quantidade: int = Form(...),
    forma_pagamento: str = Form(...),
):
    quantidade = max(1, int(quantidade))
    with _db() as db:
        usuario = _usuario_logado(request, db)
        if not usuario:
            return RedirectResponse("/login", status_code=303)
        adicionar_creditos(
            db,
            usuario.id,
            Decimal(quantidade),
            f"Compra de creditos via {forma_pagamento} em modo teste",
            referencia=f"TESTE-{uuid4().hex}",
        )
    return RedirectResponse("/", status_code=303)


@router.post("/converter")
async def converter(request: Request, background_tasks: BackgroundTasks, arquivos: list[UploadFile] = File(...)):
    if not arquivos:
        raise HTTPException(status_code=400, detail="Selecione pelo menos um arquivo TXT.")
    with _db() as db:
        usuario = _usuario_logado(request, db)
        if not usuario:
            raise HTTPException(status_code=401, detail="Login obrigatorio.")

    job_id = uuid4().hex
    pasta_job = LOCAL_ROOT / job_id
    pasta_uploads = pasta_job / "uploads"
    pasta_outputs = pasta_job / "outputs"
    pasta_uploads.mkdir(parents=True, exist_ok=True)
    pasta_outputs.mkdir(parents=True, exist_ok=True)

    uploads: list[dict] = []
    for arquivo in arquivos:
        try:
            validar_txt_upload(arquivo)
            caminho_upload = pasta_uploads / nome_interno_seguro(arquivo.filename or "sped.txt")
            with open(caminho_upload, "wb") as destino:
                while chunk := await arquivo.read(1024 * 1024):
                    destino.write(chunk)
            uploads.append(
                {
                    "nome_original": arquivo.filename or caminho_upload.name,
                    "caminho": str(caminho_upload),
                    "erro_upload": "",
                }
            )
        except Exception as exc:  # noqa: BLE001
            uploads.append(
                {
                    "nome_original": arquivo.filename or "",
                    "caminho": "",
                    "erro_upload": str(exc),
                }
            )

    JOBS[job_id] = {
        "job_id": job_id,
        "status": "PROCESSANDO",
        "inicio": time.time(),
        "fim": None,
        "total_arquivos": len(uploads),
        "arquivos_processados": 0,
        "percentual": 0,
        "mensagem": "Iniciando processamento...",
        "resultados": [],
        "zip_nome": "",
        "usuario_id": usuario.id,
        "pagos": [],
    }
    background_tasks.add_task(_processar_job, job_id, uploads, pasta_outputs)
    return {"job_id": job_id}


def _processar_job(job_id: str, uploads: list[dict], pasta_outputs: Path) -> None:
    job = JOBS[job_id]
    resultados: list[dict] = []
    total = max(len(uploads), 1)

    for indice, upload in enumerate(uploads, start=1):
        nome_original = upload.get("nome_original", "")
        job["mensagem"] = f"Processando {indice} de {total}: {nome_original}"
        if upload.get("erro_upload"):
            resultados.append(
                {
                    "nome_original": nome_original,
                    "status_processamento": "ERRO",
                    "erro": upload["erro_upload"],
                    "quantidade_linhas_geradas": 0,
                    "arquivo_excel_gerado": "",
                    "arquivo_excel_nome": "",
                }
            )
        else:
            try:
                resultado = processar_arquivo_sped(upload["caminho"], pasta_outputs, impedir_sobrescrita=True)
                resultado["nome_original"] = nome_original
                resultado["arquivo_excel_nome"] = Path(resultado["arquivo_excel_gerado"]).name if resultado.get("arquivo_excel_gerado") else ""
                resultados.append(resultado)
            except Exception as exc:  # noqa: BLE001
                resultados.append(
                    {
                        "nome_original": nome_original,
                        "status_processamento": "ERRO",
                        "erro": str(exc),
                        "quantidade_linhas_geradas": 0,
                        "arquivo_excel_gerado": "",
                        "arquivo_excel_nome": "",
                    }
                )

        job["arquivos_processados"] = indice
        job["percentual"] = int(indice / total * 100)
        job["resultados"] = resultados.copy()

    arquivos_excel = [Path(r["arquivo_excel_gerado"]) for r in resultados if r.get("arquivo_excel_gerado")]
    if arquivos_excel:
        zip_file = pasta_outputs / "relatorios_sped_excel.zip"
        with ZipFile(zip_file, "w", ZIP_DEFLATED) as zip_out:
            for arquivo_excel in arquivos_excel:
                zip_out.write(arquivo_excel, arquivo_excel.name)
        job["zip_nome"] = zip_file.name

    job["fim"] = time.time()
    job["percentual"] = 100
    job["status"] = "CONCLUIDO" if arquivos_excel else "ERRO"
    job["mensagem"] = "Processamento concluido." if arquivos_excel else "Nenhum arquivo foi convertido."


@router.get("/status/{job_id}")
def status_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Processamento nao encontrado.")
    agora = job["fim"] or time.time()
    return {**job, "tempo_decorrido": int(agora - job["inicio"])}


@router.get("/saldo")
def saldo_usuario(request: Request):
    with _db() as db:
        usuario = _usuario_logado(request, db)
        if not usuario:
            raise HTTPException(status_code=401, detail="Login obrigatorio.")
        saldo = saldo_creditos(db, usuario.id)
    return {"saldo": f"{saldo:.2f}"}


@router.get("/baixar/{job_id}/{nome_arquivo}")
def baixar(request: Request, job_id: str, nome_arquivo: str, modo: str = ""):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Processamento nao encontrado.")
    with _db() as db:
        usuario = _usuario_logado(request, db)
        if not usuario:
            if modo == "json":
                return JSONResponse({"ok": False, "mensagem": "Faca login para baixar o arquivo."}, status_code=401)
            return RedirectResponse("/login", status_code=303)
        if usuario.id != job.get("usuario_id"):
            raise HTTPException(status_code=403, detail="Arquivo de outro usuario.")

    pasta_outputs = LOCAL_ROOT / job_id / "outputs"
    caminho = (pasta_outputs / Path(nome_arquivo).name).resolve()
    raiz = pasta_outputs.resolve()
    if raiz not in caminho.parents and caminho != raiz:
        raise HTTPException(status_code=400, detail="Arquivo invalido.")
    if not caminho.exists():
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado.")

    excel_names = [r.get("arquivo_excel_nome") for r in job.get("resultados", []) if r.get("arquivo_excel_nome")]
    pagos = set(job.get("pagos", []))
    if modo == "arquivo":
        if caminho.suffix.lower() == ".zip" or caminho.name in pagos:
            return FileResponse(caminho, filename=caminho.name)
        raise HTTPException(status_code=402, detail="Credito ainda nao confirmado para este arquivo.")

    if caminho.suffix.lower() == ".zip":
        pendentes = [name for name in excel_names if name not in pagos]
        custo = CUSTO_POR_RELATORIO * Decimal(len(pendentes))
        if custo > 0:
            with _db() as db:
                usuario = _usuario_logado(request, db)
                if not consumir_creditos(db, usuario.id, custo, f"Download ZIP com {len(pendentes)} relatorios", referencia=job_id):
                    saldo_atual = saldo_creditos(db, usuario.id)
                    if modo == "json":
                        return JSONResponse(
                            {
                                "ok": False,
                                "mensagem": f"Voce esta sem creditos suficientes. Para baixar este ZIP precisa de R$ {custo:.2f}. Seu saldo atual e R$ {saldo_atual:.2f}.",
                                "saldo": f"{saldo_atual:.2f}",
                            },
                            status_code=402,
                        )
                    return _html_base(
                        f"""
                        <h2>Creditos insuficientes</h2>
                        <p>Para baixar todos os relatorios deste ZIP voce precisa de R$ {custo} em creditos.</p>
                        <p>Seu saldo atual e R$ {saldo_creditos(db, usuario.id)}.</p>
                        <a class="button" href="/creditos">Comprar creditos</a>
                        <a class="button" href="/">Voltar</a>
                        """,
                        usuario,
                        saldo_creditos(db, usuario.id),
                    )
            job["pagos"] = sorted(pagos | set(pendentes))
    elif caminho.name in excel_names and caminho.name not in pagos:
        with _db() as db:
            usuario = _usuario_logado(request, db)
            if not consumir_creditos(db, usuario.id, CUSTO_POR_RELATORIO, f"Download do relatorio {caminho.name}", referencia=f"{job_id}:{caminho.name}"):
                saldo_atual = saldo_creditos(db, usuario.id)
                if modo == "json":
                    return JSONResponse(
                        {
                            "ok": False,
                            "mensagem": f"Voce esta sem creditos. Para baixar este relatorio precisa de R$ {CUSTO_POR_RELATORIO:.2f}. Seu saldo atual e R$ {saldo_atual:.2f}.",
                            "saldo": f"{saldo_atual:.2f}",
                        },
                        status_code=402,
                    )
                return _html_base(
                    f"""
                    <h2>Creditos insuficientes</h2>
                    <p>Para baixar este relatorio voce precisa de R$ {CUSTO_POR_RELATORIO} em creditos.</p>
                    <p>Seu saldo atual e R$ {saldo_creditos(db, usuario.id)}.</p>
                    <a class="button" href="/creditos">Comprar creditos</a>
                    <a class="button" href="/">Voltar</a>
                    """,
                    usuario,
                    saldo_creditos(db, usuario.id),
                )
        pagos.add(caminho.name)
        job["pagos"] = sorted(pagos)

    if modo == "json":
        with _db() as db:
            usuario = _usuario_logado(request, db)
            saldo_atual = saldo_creditos(db, usuario.id)
        return {
            "ok": True,
            "mensagem": "Download liberado.",
            "saldo": f"{saldo_atual:.2f}",
            "download_url": f"/baixar/{job_id}/{Path(nome_arquivo).name}?modo=arquivo",
        }

    return FileResponse(caminho, filename=caminho.name)


@router.get("/assets/{nome_arquivo}")
def asset(nome_arquivo: str):
    caminho = (_asset_root() / Path(nome_arquivo).name).resolve()
    raiz = _asset_root().resolve()
    if raiz not in caminho.parents and caminho != raiz:
        raise HTTPException(status_code=400, detail="Arquivo invalido.")
    if not caminho.exists():
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado.")
    return FileResponse(caminho)
