# Segurança

## Linha de base
- Segredos só em variáveis de ambiente / GitHub Actions; `.env*` fora do Git. Produção recusa subir
  sem `DJANGO_SECRET_KEY` (`config/settings/prod.py`).
- HTTPS pelo Traefik; em produção, cookies `Secure`, HSTS e `SECURE_PROXY_SSL_HEADER`.
- Sessão por cookie `HttpOnly` com CSRF (ADR-004). Permissão padrão da API: `IsAuthenticated`;
  rota pública precisa declarar `AllowAny` (hoje só o `health`).
- Banco e API sem porta publicada na VPS; o Traefik expõe só o Admin do Django e, no futuro, o front.
- Backup do banco a cada deploy (`~/backups/project-entrelinhas`, modo 700, guarda os 10 mais novos).

## Ameaças de privacidade (o coração do produto)

| Ameaça | Defesa | Teste |
|---|---|---|
| Texto `private` vaza na lista ou no detalhe | filtragem no service de leitura (ADR-002) | T0303: API do parceiro não contém o texto |
| Texto fora do trecho `partial` vaza | truncamento no servidor | T0303: resposta só tem o intervalo |
| Destaque ou comentário revela texto escondido | offsets validados contra o texto visível (AC-11.5) | T0402: 422 fora do trecho; resposta sem texto escondido |
| Terceiro entra no espaço | espaço com no máximo 2 membros; convite | T0202 |
| Membro de outro espaço lê registro | recurso de outro espaço = 404 | T0301: teste de acesso cruzado |
| Texto fica em cache do navegador ou do service worker | service worker não guarda texto; `Cache-Control: no-store` nas respostas de registro | T0502 |
| Foto manuscrita acessível por URL direta | armazenamento privado, entrega só pela API | T0501 |

Cada linha vira teste na spec da tarefa indicada. Linha sem teste, na hora de fechar a spec, é pendência aberta.
