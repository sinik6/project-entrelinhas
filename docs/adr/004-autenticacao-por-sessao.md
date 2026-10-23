# ADR-004 — Autenticação por sessão do Django

**Status:** aceita (arquitetura da especificação de origem).

## Decisão
Autenticação nativa do Django com sessão e cookie `HttpOnly` (`SessionAuthentication` do DRF).
O front, quando existir, fala com a API pelo BFF do Next, no mesmo domínio, e a proteção de CSRF
do Django continua ligada.

## Por quê
A spec pede sessão segura com cookie `HttpOnly`. Para um app de duas pessoas, sessão no servidor é
mais simples que JWT e permite encerrar a sessão de verdade. (O Vinculus usa JWT em cookie por ter
várias clínicas e papéis; não é o caso aqui.)

## Consequências
Requisições que mudam dados exigem o token CSRF. O cookie de sessão é `Secure` em produção.
