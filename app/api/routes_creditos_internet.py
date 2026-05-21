"""Credit purchase routes for the future internet version.

This router is intentionally separate from routes_local.py so the local/test
program keeps working without real payments.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.database.models import CompraCredito, Usuario
from app.database.session import SessionLocal
from app.services.credito_service import CUSTO_POR_RELATORIO, saldo_creditos
from app.services.pagamento_service import asaas_configurado, atualizar_pix_cobranca_asaas, criar_cobranca_creditos_asaas
from app.utils.seguranca import decodificar_token

router = APIRouter(prefix="/internet/creditos", tags=["creditos-internet"])
COMPRA_MINIMA_CREDITOS = 50


def _db():
    return SessionLocal()


def _usuario_logado(request: Request, db) -> Usuario | None:
    token = request.cookies.get("conversor_token")
    if not token:
        return None
    try:
        usuario_id = int(decodificar_token(token))
    except ValueError:
        return None
    return db.get(Usuario, usuario_id)


def _pagina(conteudo: str) -> str:
    return f"""
    <!doctype html>
    <html lang="pt-br">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Comprar creditos - Versao internet</title>
        <style>
            body {{ font-family: Arial, Helvetica, sans-serif; margin: 0; background: #eef2f6; color: #1f2937; }}
            main {{ max-width: 900px; margin: 28px auto; background: white; padding: 28px; border-radius: 8px; border: 1px solid #d8dee8; }}
            label {{ display: block; font-weight: 700; margin-top: 12px; }}
            input, select, textarea {{ width: 100%; box-sizing: border-box; padding: 12px; margin-top: 6px; border: 1px solid #cbd5e1; border-radius: 6px; }}
            button, .button {{ display: inline-block; padding: 12px 18px; margin-top: 16px; border: 0; border-radius: 6px; background: #0f5db8; color: white; font-weight: 700; text-decoration: none; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 18px; table-layout: fixed; }}
            th, td {{ border-bottom: 1px solid #e5e7eb; padding: 8px; overflow-wrap: anywhere; }}
            .alert {{ border: 1px solid #fecdca; background: #fffbfa; color: #b42318; border-radius: 8px; padding: 12px; }}
            .muted {{ color: #667085; }}
        </style>
    </head>
    <body><main>{conteudo}</main></body>
    </html>
    """


@router.get("", response_class=HTMLResponse)
def tela_comprar_creditos(request: Request):
    with _db() as db:
        usuario = _usuario_logado(request, db)
        if not usuario:
            return RedirectResponse("/login", status_code=303)
        compras = (
            db.query(CompraCredito)
            .filter(CompraCredito.usuario_id == usuario.id)
            .order_by(CompraCredito.id.desc())
            .limit(10)
            .all()
        )
        saldo = saldo_creditos(db, usuario.id)

    if not asaas_configurado():
        aviso = '<div class="alert">ASAAS_API_KEY ainda nao configurada. Esta tela e somente para a versao publicada na internet.</div>'
    else:
        aviso = '<p class="muted">Pagamento real via Asaas ativo.</p>'

    linhas = "".join(
        f"""
        <tr>
            <td>{compra.id}</td>
            <td>R$ {Decimal(str(compra.valor)):.2f}</td>
            <td>{compra.forma_pagamento}</td>
            <td>{compra.status}</td>
            <td>{'<a href="' + compra.invoice_url + '" target="_blank" rel="noopener">Pagar</a>' if compra.invoice_url and compra.status == 'PENDENTE' else ''}</td>
        </tr>
        """
        for compra in compras
    )
    return _pagina(
        f"""
        <h1>Comprar creditos - versao internet</h1>
        <p>Saldo atual: <strong>R$ {saldo:.2f}</strong></p>
        <p>Cada relatório baixado consome <strong>R$ {CUSTO_POR_RELATORIO:.2f}</strong> em créditos.</p>
        <p>A compra mínima é de <strong>R$ {COMPRA_MINIMA_CREDITOS:.2f}</strong> em créditos.</p>
        {aviso}
        <form method="post" action="/internet/creditos/comprar">
            <label>CPF ou CNPJ</label>
            <input type="text" name="documento" value="{usuario.documento or ''}" required>
            <label>Telefone</label>
            <input type="text" name="telefone" value="{usuario.telefone or ''}">
            <label>Quantidade de creditos</label>
            <input type="number" name="quantidade" min="{COMPRA_MINIMA_CREDITOS}" step="1" value="{COMPRA_MINIMA_CREDITOS}" required>
            <label>Forma de pagamento</label>
            <select name="forma_pagamento">
                <option value="PIX">Pix</option>
                <option value="CREDIT_CARD">Cartao de credito</option>
            </select>
            <button type="submit">Gerar cobranca no Asaas</button>
        </form>
        <h2>Compras</h2>
        <table>
            <thead><tr><th>Pedido</th><th>Valor</th><th>Forma</th><th>Status</th><th>Pagamento</th></tr></thead>
            <tbody>{linhas or '<tr><td colspan="5">Nenhuma compra registrada.</td></tr>'}</tbody>
        </table>
        <p><a href="/">Voltar ao conversor local</a></p>
        """
    )


@router.post("/comprar")
def comprar_creditos(
    request: Request,
    quantidade: int = Form(...),
    forma_pagamento: str = Form(...),
    documento: str = Form(...),
    telefone: str = Form(""),
):
    if not asaas_configurado():
        raise HTTPException(status_code=400, detail="ASAAS_API_KEY nao configurada.")
    quantidade = max(COMPRA_MINIMA_CREDITOS, int(quantidade))
    with _db() as db:
        usuario = _usuario_logado(request, db)
        if not usuario:
            return RedirectResponse("/login", status_code=303)
        usuario.documento = "".join(ch for ch in documento if ch.isdigit())
        usuario.tipo_documento = "CNPJ" if len(usuario.documento) == 14 else "CPF"
        usuario.telefone = telefone
        db.commit()
        try:
            compra = criar_cobranca_creditos_asaas(db, usuario, quantidade, forma_pagamento)
        except Exception as exc:  # noqa: BLE001
            return _pagina(
                f"""
                <h1>Nao foi possivel gerar a cobranca</h1>
                <p>{str(exc)}</p>
                <p class="muted">Confira CPF/CNPJ, tente no minimo R$ {COMPRA_MINIMA_CREDITOS:.2f} em creditos e use a chave do Asaas correta.</p>
                <p><a class="button" href="/internet/creditos">Voltar</a></p>
                """
            )
    return RedirectResponse(f"/internet/creditos/pagamento/{compra.id}", status_code=303)


@router.get("/pagamento/{compra_id}", response_class=HTMLResponse)
def pagamento_creditos(request: Request, compra_id: int):
    with _db() as db:
        usuario = _usuario_logado(request, db)
        if not usuario:
            return RedirectResponse("/login", status_code=303)
        compra = db.get(CompraCredito, compra_id)
        if not compra or compra.usuario_id != usuario.id:
            return _pagina(
                """
                <h1>Compra nao encontrada</h1>
                <p>Esta cobranca nao pertence ao usuario logado ou ja nao existe neste ambiente.</p>
                <p>Para testar, volte para a tela de creditos e gere uma nova cobranca com o seu usuario.</p>
                <p><a class="button" href="/internet/creditos">Comprar creditos</a></p>
                """
            )
        compra = atualizar_pix_cobranca_asaas(db, compra)

    pix_img = ""
    if compra.pix_encoded_image:
        pix_img = f'<img alt="QR Code Pix" style="max-width:260px;width:100%;height:auto" src="data:image/png;base64,{compra.pix_encoded_image}">'
    pix_payload = ""
    if compra.pix_payload:
        pix_payload = f'<label>Pix copia e cola</label><textarea readonly>{compra.pix_payload}</textarea>'
    link = ""
    if compra.invoice_url:
        link = f'<a class="button" href="{compra.invoice_url}" target="_blank" rel="noopener">Abrir pagamento no Asaas</a>'

    return _pagina(
        f"""
        <h1>Pagamento de creditos</h1>
        <p>Pedido #{compra.id} - R$ {Decimal(str(compra.valor)):.2f} - Status: <strong>{compra.status}</strong></p>
        <p class="muted">Depois da confirmacao do Asaas, o webhook libera os creditos automaticamente.</p>
        {link}
        <div>{pix_img}</div>
        {pix_payload}
        <p><a href="/internet/creditos">Voltar</a></p>
        """
    )
