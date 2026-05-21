# Conversor SPED para Excel

Programa local em Python para converter arquivos TXT do SPED em relatórios Excel com layouts fixos, sem depender de modelos Excel em cada execução.

## Uso recomendado

Para usar sem comandos técnicos, clique duas vezes em:

```text
ABRIR_PROGRAMA.bat
```

O navegador abrirá em:

```text
http://127.0.0.1:8765
```

Na tela, selecione um ou vários arquivos `.txt` do SPED, clique em **Converter para Excel** e baixe os relatórios gerados.

## O que a versão local faz

- Lê arquivos `.txt` de EFD-Contribuições e EFD-ICMS/IPI.
- Identifica automaticamente o tipo de SPED.
- Gera Excel do zero com `openpyxl`.
- Usa layouts fixos em código:
  - `app/layouts/layout_contribuicoes.py`
  - `app/layouts/layout_icms_ipi.py`
- Preserva CNPJ, CPF, NF-e, documento, item, NCM, CFOP e CST como texto.
- Converte valores com vírgula decimal para números no Excel.
- Formata datas no padrão brasileiro.
- Não altera os TXT originais.
- Não sobrescreve arquivos existentes.
- Gera log em `LOG_PROCESSAMENTO_SPED.xlsx`.

## Como rodar a versão local

1. Instale as dependências:

```powershell
pip install -r requirements.txt
```

2. Edite as constantes em `local_converter.py`:

```python
PASTA_TXT = r"C:\caminho\para\pasta\com\txt"
PASTA_SAIDA = r"C:\caminho\para\saida"
PROCESSAR_SUBPASTAS = True
NAO_SOBRESCREVER = True
GERAR_LOG = True
```

3. Execute:

```powershell
python local_converter.py
```

## Estrutura do projeto

```text
app/
  core/
    parser_sped.py
    detector_tipo_sped.py
    formatadores.py
    excel_writer.py
    logger.py
    nomes_arquivos.py
  extractors/
    efd_contribuicoes.py
    efd_icms_ipi.py
  layouts/
    layout_contribuicoes.py
    layout_icms_ipi.py
  services/
    processamento_service.py
    assinatura_service.py
    pagamento_service.py
    storage_service.py
    usuario_service.py
  api/
    main.py
    routes_auth.py
    routes_upload.py
    routes_processamento.py
    routes_download.py
    routes_assinatura.py
    routes_webhook_asaas.py
  database/
    models.py
    session.py
    migrations/
  schemas/
  utils/
  config.py
```

## Como rodar a API FastAPI

Configure o `.env` conforme necessário:

```env
DATABASE_URL=postgresql+psycopg2://usuario:senha@localhost:5432/sped_saas
SECRET_KEY=troque-em-producao
ASAAS_API_KEY=
ASAAS_BASE_URL=https://sandbox.asaas.com/api/v3
ASAAS_WEBHOOK_TOKEN=
ASAAS_WALLET_ID=
STORAGE_ROOT=storage
```

Para desenvolvimento rápido, sem PostgreSQL, a API usa SQLite por padrão.

Execute:

```powershell
uvicorn app.api.main:app --reload
```

Para a versão futura de internet com compra real de créditos pelo Asaas, use outro entrypoint:

```powershell
uvicorn app.api.main_internet:app --reload
```

A versão local/teste continua em `app.api.main:app` e não depende do Asaas para comprar créditos.

Endpoints iniciais:

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /empresas`
- `GET /empresas`
- `GET /empresas/{id}`
- `GET /planos`
- `GET /assinatura/status`
- `POST /assinatura/criar`
- `POST /assinatura/cancelar`
- `POST /upload`
- `POST /processar`
- `GET /processamentos`
- `GET /processamentos/{id}`
- `GET /download/{processamento_id}`
- `POST /webhooks/asaas`

## Planos e limite mensal

Planos iniciais:

- Teste grátis: R$ 0, 3 arquivos, 7 dias.
- Básico: R$ 197/mês, 30 arquivos/mês.
- Profissional: R$ 497/mês, 150 arquivos/mês.
- Consultoria: R$ 1.497/mês, 700 arquivos/mês.

Antes de processar um TXT, o SaaS chama `validar_permissao_processamento(usuario_id)`. O processamento só é liberado para assinaturas `TESTE_ATIVO` ou `ATIVA` e quando o uso mensal ainda está abaixo do limite do plano.

Fluxo atual validado na API:

1. Criar usuário em `POST /auth/register`.
2. Fazer login em `POST /auth/login`.
3. Cadastrar empresa em `POST /empresas`.
4. Listar planos em `GET /planos`.
5. Criar assinatura em `POST /assinatura/criar`.
6. Enviar TXT em `POST /upload`.
7. Consultar histórico em `GET /processamentos`.
8. Baixar Excel em `GET /download/{processamento_id}`.

## Asaas

O serviço `app/services/pagamento_service.py` contém:

- `criar_cliente_asaas`
- `criar_assinatura_asaas`
- `cancelar_assinatura_asaas`
- `buscar_assinatura_asaas`
- `criar_cobranca_creditos_asaas`
- `processar_webhook_asaas`

### Compra de créditos

A tela `/creditos` funciona de duas formas:

- Sem `ASAAS_API_KEY`: modo teste local, credita automaticamente.
- Com `ASAAS_API_KEY`: cria uma cobrança real no Asaas e deixa a compra como `PENDENTE`.

Cada crédito vale R$ 1,00 e cada TXT baixado consome R$ 1,00.

O pagamento é feito pela página segura do Asaas (`invoiceUrl`). Para Pix, o sistema também tenta exibir QR Code e Pix copia-e-cola.

Quando o Asaas chamar `POST /webhooks/asaas`, o sistema:

- libera créditos em `PAYMENT_CONFIRMED` ou `PAYMENT_RECEIVED`;
- marca compra como vencida em `PAYMENT_OVERDUE`;
- marca compra como cancelada em `PAYMENT_DELETED`;
- estorna/bloqueia créditos em `PAYMENT_REFUNDED` e eventos de chargeback;
- evita duplicar créditos se o mesmo webhook chegar mais de uma vez.

Para usar em produção, configure no Asaas o endpoint público:

```text
https://SEU-DOMINIO.com/webhooks/asaas
```

E use o mesmo token configurado em `ASAAS_WEBHOOK_TOKEN`.

Eventos tratados:

- `PAYMENT_CONFIRMED` e `PAYMENT_RECEIVED`: assinatura `ATIVA`.
- `PAYMENT_OVERDUE`: assinatura `ATRASADA`.
- `PAYMENT_DELETED`: assinatura `CANCELADA`.
- `PAYMENT_REFUNDED` e chargeback: assinatura `BLOQUEADA`.

## Segurança e privacidade

- Uploads e outputs são separados por usuário em `storage/usuarios/{usuario_id}`.
- O nome físico do arquivo enviado é gerado internamente.
- A API valida extensão `.txt`.
- O download confere o dono do processamento.
- O projeto já tem configurações para retenção de uploads e outputs.

## Próximos passos

- Criar migrations Alembic reais.
- Adicionar cadastro de empresa via endpoint dedicado.
- Trocar processamento síncrono por Celery/Redis.
- Implementar frontend em React ou Next.js.
- Adicionar rotina de retenção e exclusão automática.
- Criar testes automatizados com TXT sintéticos por registro.
