# ADR-0006 — Uma origem só, sessão por cookie e CSRF por token no corpo

- Status: aceito (usuário, 2026-11-03)
- Data: 2026-11-03
- Mudança de origem: 003-acesso-e-grupo
- Complementa: ADR-0003 (deploy sob `/entrelinhas`) e ADR-0004 (sessão do Django)

## Contexto
O app Flutter roda no navegador e precisa de uma sessão segura. A API hoje não é alcançável pela internet (só o Admin é).

## Decisão
- Um contêiner **nginx** (`entrelinhas-web`) serve o app e repassa `/api/` à API pela rede interna; o Traefik só entrega o prefixo
  `/entrelinhas` ao nginx. As rotas diretas do Admin (002) não mudam.
- Sessão do Django em cookie `entrelinhas_sessionid` (`HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/entrelinhas`). O cookie de
  proteção contra CSRF também é `HttpOnly` e tem nome e caminho próprios.
- O token de CSRF é entregue em `GET /api/v1/auth/csrf` (no corpo) e enviado pelo app no cabeçalho `X-CSRFToken`.
- Toda rota que muda estado, inclusive as anônimas (entrar, aceitar convite), exige o token: uma classe de autenticação própria
  força a checagem que o DRF faria só para quem já está autenticado.
- O convite vai no **fragmento** da URL (`#/convite/<código>`) e o código só é enviado no corpo do `POST`.

## Alternativas consideradas
| Opção | Prós | Contras |
|---|---|---|
| API pública direta no Traefik, origem separada | nenhum contêiner a mais | exige CORS e cookies de terceiros; superfície maior |
| JWT em `localStorage` | simples no Flutter | exposto a script injetado; contraria o ADR-0004 |
| Cookie de CSRF legível pelo script | padrão do Django | o script passa a ler um cookie; o token no corpo evita isso |
| Código do convite no caminho da URL | link mais simples | cai em log do nginx, do Traefik e no cabeçalho `Referer` |

## Consequências
Um contêiner a mais. O app guarda o token de CSRF em memória e o busca de novo ao recarregar. O Django precisa confiar no
cabeçalho `X-Forwarded-Proto` (já configurado na 001). O limite de login fica no Traefik (sem cache compartilhado).
