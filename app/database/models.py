"""SQLAlchemy models for the SaaS layer."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Integer().with_variant(Integer, "sqlite")
    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    nome = __import__("sqlalchemy").Column(String(255), nullable=False)
    email = __import__("sqlalchemy").Column(String(255), unique=True, index=True, nullable=False)
    senha_hash = __import__("sqlalchemy").Column(String(255), nullable=False)
    telefone = __import__("sqlalchemy").Column(String(50))
    documento = __import__("sqlalchemy").Column(String(30))
    tipo_documento = __import__("sqlalchemy").Column(String(20))
    ativo = __import__("sqlalchemy").Column(Boolean, default=True)
    data_criacao = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow)
    data_atualizacao = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    empresas = relationship("Empresa", back_populates="usuario")


class Empresa(Base):
    __tablename__ = "empresas"
    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    usuario_id = __import__("sqlalchemy").Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    razao_social = __import__("sqlalchemy").Column(String(255), nullable=False)
    nome_fantasia = __import__("sqlalchemy").Column(String(255))
    cnpj = __import__("sqlalchemy").Column(String(20), index=True, nullable=False)
    email_financeiro = __import__("sqlalchemy").Column(String(255))
    telefone = __import__("sqlalchemy").Column(String(50))
    data_criacao = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow)
    data_atualizacao = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario = relationship("Usuario", back_populates="empresas")


class Plano(Base):
    __tablename__ = "planos"
    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    nome = __import__("sqlalchemy").Column(String(100), unique=True, nullable=False)
    descricao = __import__("sqlalchemy").Column(Text)
    valor_mensal = __import__("sqlalchemy").Column(Numeric(10, 2), nullable=False)
    limite_arquivos_mes = __import__("sqlalchemy").Column(Integer, nullable=False)
    dias_teste = __import__("sqlalchemy").Column(Integer, default=0)
    ativo = __import__("sqlalchemy").Column(Boolean, default=True)


class Assinatura(Base):
    __tablename__ = "assinaturas"
    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    usuario_id = __import__("sqlalchemy").Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    empresa_id = __import__("sqlalchemy").Column(Integer, ForeignKey("empresas.id"), nullable=False)
    plano_id = __import__("sqlalchemy").Column(Integer, ForeignKey("planos.id"), nullable=False)
    status = __import__("sqlalchemy").Column(String(40), nullable=False, default="TESTE_ATIVO")
    data_inicio = __import__("sqlalchemy").Column(Date)
    data_fim = __import__("sqlalchemy").Column(Date)
    data_vencimento = __import__("sqlalchemy").Column(Date)
    arquivos_processados_mes = __import__("sqlalchemy").Column(Integer, default=0)
    mes_referencia_uso = __import__("sqlalchemy").Column(String(7))
    asaas_customer_id = __import__("sqlalchemy").Column(String(100))
    asaas_subscription_id = __import__("sqlalchemy").Column(String(100))
    data_criacao = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow)
    data_atualizacao = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    plano = relationship("Plano")
    empresa = relationship("Empresa")


class UsoMensal(Base):
    __tablename__ = "uso_mensal"
    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    usuario_id = __import__("sqlalchemy").Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    empresa_id = __import__("sqlalchemy").Column(Integer, ForeignKey("empresas.id"), nullable=False)
    plano_id = __import__("sqlalchemy").Column(Integer, ForeignKey("planos.id"), nullable=False)
    mes_referencia = __import__("sqlalchemy").Column(String(7), nullable=False)
    limite_arquivos = __import__("sqlalchemy").Column(Integer, nullable=False)
    arquivos_processados = __import__("sqlalchemy").Column(Integer, default=0)
    data_criacao = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow)
    data_atualizacao = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Processamento(Base):
    __tablename__ = "processamentos"
    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    usuario_id = __import__("sqlalchemy").Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    empresa_id = __import__("sqlalchemy").Column(Integer, ForeignKey("empresas.id"), nullable=False)
    tipo_sped = __import__("sqlalchemy").Column(String(60))
    arquivo_original_nome = __import__("sqlalchemy").Column(String(255), nullable=False)
    arquivo_original_path = __import__("sqlalchemy").Column(String(500), nullable=False)
    arquivo_excel_nome = __import__("sqlalchemy").Column(String(255))
    arquivo_excel_path = __import__("sqlalchemy").Column(String(500))
    cnpj_arquivo = __import__("sqlalchemy").Column(String(20))
    dt_ini = __import__("sqlalchemy").Column(String(20))
    dt_fin = __import__("sqlalchemy").Column(String(20))
    status = __import__("sqlalchemy").Column(String(40), default="PENDENTE")
    erro = __import__("sqlalchemy").Column(Text)
    quantidade_linhas_lidas = __import__("sqlalchemy").Column(Integer, default=0)
    quantidade_linhas_geradas = __import__("sqlalchemy").Column(Integer, default=0)
    data_inicio = __import__("sqlalchemy").Column(DateTime)
    data_fim = __import__("sqlalchemy").Column(DateTime)
    data_criacao = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow)


class Pagamento(Base):
    __tablename__ = "pagamentos"
    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    usuario_id = __import__("sqlalchemy").Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    empresa_id = __import__("sqlalchemy").Column(Integer, ForeignKey("empresas.id"), nullable=False)
    assinatura_id = __import__("sqlalchemy").Column(Integer, ForeignKey("assinaturas.id"), nullable=False)
    asaas_payment_id = __import__("sqlalchemy").Column(String(100), index=True)
    asaas_subscription_id = __import__("sqlalchemy").Column(String(100), index=True)
    status = __import__("sqlalchemy").Column(String(40), nullable=False)
    valor = __import__("sqlalchemy").Column(Numeric(10, 2))
    data_vencimento = __import__("sqlalchemy").Column(Date)
    data_pagamento = __import__("sqlalchemy").Column(Date)
    forma_pagamento = __import__("sqlalchemy").Column(String(50))
    evento_webhook = __import__("sqlalchemy").Column(String(100))
    payload_json = __import__("sqlalchemy").Column(Text)
    data_criacao = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow)


class CreditoTransacao(Base):
    __tablename__ = "creditos_transacoes"
    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    usuario_id = __import__("sqlalchemy").Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    tipo = __import__("sqlalchemy").Column(String(30), nullable=False)
    quantidade = __import__("sqlalchemy").Column(Numeric(10, 2), nullable=False)
    descricao = __import__("sqlalchemy").Column(String(255))
    referencia = __import__("sqlalchemy").Column(String(120), index=True)
    status = __import__("sqlalchemy").Column(String(30), default="CONFIRMADO")
    data_criacao = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow)


class CompraCredito(Base):
    __tablename__ = "compras_creditos"
    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    usuario_id = __import__("sqlalchemy").Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    quantidade_creditos = __import__("sqlalchemy").Column(Numeric(10, 2), nullable=False)
    valor = __import__("sqlalchemy").Column(Numeric(10, 2), nullable=False)
    forma_pagamento = __import__("sqlalchemy").Column(String(50), nullable=False)
    status = __import__("sqlalchemy").Column(String(40), nullable=False, default="PENDENTE")
    asaas_customer_id = __import__("sqlalchemy").Column(String(100), index=True)
    asaas_payment_id = __import__("sqlalchemy").Column(String(100), unique=True, index=True)
    invoice_url = __import__("sqlalchemy").Column(String(500))
    pix_payload = __import__("sqlalchemy").Column(Text)
    pix_encoded_image = __import__("sqlalchemy").Column(Text)
    creditos_liberados = __import__("sqlalchemy").Column(Boolean, default=False)
    payload_json = __import__("sqlalchemy").Column(Text)
    data_confirmacao = __import__("sqlalchemy").Column(DateTime)
    data_criacao = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow)
    data_atualizacao = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
