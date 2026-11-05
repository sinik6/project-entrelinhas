# ADR-0013 — Recuperação de senha por token do Django, link no fragmento e SMTP

- Status: proposto (agente, por delegação do usuário em 2026-11-05); vira "aceito" na ratificação do G1
- Data: 2026-11-05
- Mudança de origem: 011-recuperacao-de-senha

## Contexto
A 003 deixou a recuperação por e-mail como mudança própria. O front é um app Flutter na mesma origem da API (ADR-0006); o link do e-mail precisa chegar ao app sem expor o token.

## Decisão
1. Token do gerador do Django (`default_token_generator`), com `PASSWORD_RESET_TIMEOUT = 3600`. Sem tabela de tokens: o token é derivado do estado da conta e deixa de valer quando a senha ou o último login mudam.
2. O link usa o **fragmento** (`#/redefinir/<uid>/<token>`): o fragmento não vai ao servidor nem ao `Referer`. O endereço-base vem de `APP_URL_BASE`, nunca do cabeçalho `Host`.
3. Resposta ao pedido sempre igual; envio em thread de segundo plano; 3 pedidos por conta por hora; balde de 5 por minuto no Traefik.
4. E-mail por SMTP com o `EmailMessage` do Django, credenciais em segredos. Sem pacote novo.

## Consequências
- Sem estado novo além do contador de pedidos (24 h).
- Uma thread de segundo plano pode perder o e-mail se o processo cair; a pessoa pede de novo.
- O provedor SMTP é escolha do usuário (dependência externa registrada na 011).

## Alternativas descartadas
- **Tabela própria de tokens com hash:** mais estado e código para o mesmo efeito.
- **Link com o token em caminho ou query:** vai ao servidor e ao `Referer`, e entra em log de proxy.
- **Fila externa (Celery, Redis):** serviço novo e dependência para 2 pessoas.
- **Login automático depois de redefinir:** amplia o risco de "login CSRF" e de roubo de link; a pessoa entra com a senha nova.
