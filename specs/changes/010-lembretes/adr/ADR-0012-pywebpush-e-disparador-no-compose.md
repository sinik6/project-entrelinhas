# ADR-0012 — `pywebpush` e disparador como serviço do compose

- Status: proposto (agente, por delegação do usuário em 2026-11-05); vira "aceito" na ratificação do G1
- Data: 2026-11-05
- Mudança de origem: 010-lembretes

## Contexto
O aviso diário às 21h30 exige (a) cifrar e assinar o envio de Web Push (RFC 8291 e RFC 8292) e (b) um relógio fora das requisições.

## Decisão
1. Usar `pywebpush` (mantido, do ecossistema Mozilla/web-push, no PyPI) para cifrar e enviar; ele traz `py-vapid`, `http-ece`, `cryptography` e `requests`. Versão travada em `uv.lock`, verificada no PyPI antes de instalar (Art. 11); `pip-audit` rodado uma vez e anotado no `validation.md`.
2. O disparador é um serviço do compose, `entrelinhas-lembretes`, **da mesma imagem** da API com o comando `manage.py rodar_lembretes`. Sem porta, sem Traefik, com `restart: unless-stopped` e saúde por arquivo de batimento.
3. Idempotência no banco (`unique(usuario, data)`), não no processo.
4. Chaves VAPID geradas por `manage.py gerar_vapid` (impressas, não gravadas) e guardadas nos segredos do GitHub.

## Consequências
- Um segundo contêiner (mesma imagem, mesmo código): não conta como terceiro projeto implantável (Art. 4), registrado em "Rastreamento de complexidade" da 010.
- Dependência transitiva `requests` entra no backend; o envio roda com tempo limite e só para hosts da lista fixa.
- Trocar de biblioteca depois exige mexer só em `lembretes/envio.py`.

## Alternativas descartadas
- **Implementar RFC 8291/8292 à mão:** cripto própria, risco alto.
- **Cron da VPS:** estado e deploy fora do compose; mais um lugar para esquecer.
- **Serviço de push de terceiros (OneSignal, Firebase SDK):** envia dados do app a terceiros, sem necessidade.
