"""Processing service used by API routes."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.parser_sped import processar_arquivo_sped
from app.database.models import Processamento
from app.services.assinatura_service import incrementar_uso, validar_permissao_processamento
from app.services.storage_service import pasta_saida_usuario


def processar_txt_usuario(db: Session, usuario_id: int, empresa_id: int, caminho_txt: Path, nome_original: str) -> Processamento:
    assinatura = validar_permissao_processamento(db, usuario_id, empresa_id)
    proc = Processamento(
        usuario_id=usuario_id,
        empresa_id=empresa_id,
        arquivo_original_nome=nome_original,
        arquivo_original_path=str(caminho_txt),
        status="PROCESSANDO",
        data_inicio=datetime.utcnow(),
    )
    db.add(proc)
    db.commit()
    db.refresh(proc)

    try:
        resultado = processar_arquivo_sped(caminho_txt, pasta_saida_usuario(usuario_id))
        proc.status = "CONCLUIDO"
        proc.tipo_sped = resultado["tipo_sped_identificado"]
        proc.arquivo_excel_path = resultado["arquivo_excel_gerado"]
        proc.arquivo_excel_nome = Path(resultado["arquivo_excel_gerado"]).name
        proc.cnpj_arquivo = resultado["cnpj"]
        proc.dt_ini = resultado["dt_ini"]
        proc.dt_fin = resultado["dt_fin"]
        proc.quantidade_linhas_lidas = resultado["quantidade_linhas_lidas"]
        proc.quantidade_linhas_geradas = resultado["quantidade_linhas_geradas"]
        incrementar_uso(db, assinatura)
    except Exception as exc:  # noqa: BLE001
        proc.status = "ERRO"
        proc.erro = "Ocorreu um erro ao gerar o relatório. Tente novamente ou fale com o suporte."
    finally:
        proc.data_fim = datetime.utcnow()
        db.commit()
        db.refresh(proc)
    return proc
