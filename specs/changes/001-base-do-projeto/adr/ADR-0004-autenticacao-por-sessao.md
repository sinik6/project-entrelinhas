# ADR-0004 — Autenticação por sessão do Django

- Status: aceito
- Data: 2026-10-19
- Mudança de origem: 001-base-do-projeto (aplicada na mudança de acesso)

## Contexto
A especificação de origem pede autenticação nativa do Django com sessão segura e cookie `HttpOnly`.

## Decisão
`SessionAuthentication` do DRF com cookie `HttpOnly`, `Secure` em produção e proteção de CSRF ligada. O front,
quando existir, fala com a API pelo BFF do Next, no mesmo domínio.

## Alternativas consideradas
| Opção | Prós | Contras |
|---|---|---|
| JWT em cookie (padrão do Vinculus) | stateless | o Vinculus precisa por ter várias clínicas e papéis; aqui são duas pessoas |
| Token em `localStorage` | simples | exposto a XSS |

## Consequências
Requisições que mudam dados exigem o token CSRF. Encerrar a sessão no servidor é possível de verdade.
