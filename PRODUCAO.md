# Publicacao em producao

## Render

Crie um Web Service apontando para este repositorio.

Configuracao:

```text
Build Command:
pip install -r requirements.txt

Start Command:
uvicorn app.api.main_internet:app --host 0.0.0.0 --port $PORT
```

## Variaveis de ambiente

Configure no Render, em Environment:

```env
DATABASE_URL=postgresql+psycopg2://usuario:senha@host:5432/banco
SECRET_KEY=troque-por-uma-chave-grande-e-segura
STORAGE_ROOT=storage
MAX_UPLOAD_MB=80

ASAAS_BASE_URL=https://api.asaas.com/v3
ASAAS_API_KEY=sua-chave-producao-asaas
ASAAS_WEBHOOK_TOKEN=um-token-seguro
ASAAS_WALLET_ID=
```

Para homologacao com sandbox:

```env
ASAAS_BASE_URL=https://api-sandbox.asaas.com/v3
ASAAS_API_KEY=sua-chave-sandbox
```

## Webhook Asaas

No painel do Asaas, configure o webhook de cobrancas:

```text
https://SEU-DOMINIO/webhooks/asaas
```

O token configurado no Asaas deve ser igual ao `ASAAS_WEBHOOK_TOKEN`.

## Cuidados

- Nunca envie `.env` para o GitHub.
- Nunca envie banco local `sped_saas.db`.
- Nunca envie arquivos TXT, Excel gerados ou dados fiscais de clientes.
- Em producao, prefira PostgreSQL e storage persistente.
