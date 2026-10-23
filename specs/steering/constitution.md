---
versao: 1.0.0
ratificada: 2026-10-23
ultima_emenda: 2026-10-23
---

# Constituição — Entrelinhas

Princípios inegociáveis. Cada artigo é um portão no design (G2). Exceção só com
justificativa em "Rastreamento de complexidade" e aprovação humana.
Emenda: commit com motivo, impacto em specs existentes e incremento de versão.

## Art. 1 — Spec antes do código
Nenhuma mudança ≥ P1 sem spec aprovada. Mudou o rumo, muda a spec primeiro. Sem expansão automática
de escopo: só o que está na spec e no mapa de capacidades é implementado, uma tarefa pequena por vez.

## Art. 2 — Teste primeiro
Todo critério gera teste escrito antes e visto falhando. Teste deriva da spec, não do código.

## Art. 3 — Integração real
Testes de integração usam PostgreSQL real em container; mocks apenas para serviços externos.

## Art. 4 — Simplicidade
Sem camadas, projetos ou abstrações especulativas. No máximo 2 projetos implantáveis: API (`backend/`) e web (`frontend/`).

## Art. 5 — Anti-abstração
Usar o framework diretamente (ORM do Django, DRF, Server Components); uma representação por modelo.

## Art. 6 — Validação no backend
Toda regra validada no front existe no backend com teste de API (422).

## Art. 7 — Segurança por padrão
Deny-by-default; autorização por objeto e por espaço no servidor; ASVS L2; threat model para risco médio/alto.

## Art. 8 — Contratos explícitos
APIs descritas em OpenAPI versionado em `specs/changes/<id>/contracts/` e, depois de arquivada a
mudança, gerado do código; breaking change exige nova versão.

## Art. 9 — Observabilidade e privacidade
Logs sem texto de registro, sem foto e sem segredo; auditoria de ações sensíveis; LGPD por dado pessoal.

## Art. 10 — Acessibilidade
WCAG 2.2 AA na web; semântica e rótulos nos controles.

## Art. 11 — Dependências
Pacote novo só com justificativa (ADR), verificação no registro oficial e lockfile.

## Art. 12 — Privacidade filtrada no servidor
Texto de registro `private`, ou a parte de um registro `partial` fora do trecho escolhido, nunca vai na
resposta HTTP do Django. Esconder no front não conta. Todo endpoint que devolve texto de registro tem
teste de API provando que o texto escondido não aparece.

## Art. 13 — Espaço de exatamente duas pessoas
Um espaço nunca passa de 2 membros, garantido no backend. Recurso de outro espaço responde 404, nunca 403.

## Fronteiras do agente
| Sempre | Perguntar antes | Nunca |
|---|---|---|
| rodar testes antes de commit | mudar schema do banco / migração que altera ou apaga dados | commitar segredos ou `.env` |
| seguir os padrões de `structure.md` | adicionar dependência (exige ADR) | editar migrations já aplicadas |
| validar entrada no backend | mudar CI, deploy, Traefik ou settings de produção | remover ou pular teste que falha sem aprovação |
| citar IDs da spec no commit | commit ou push na `main` (o push dispara o deploy) | aprovar portão em nome do humano |
| teste provando que texto escondido não vaza | mudar regra de visibilidade ou o limite de 2 membros | enviar texto `private` ou fora do `partial` na API |
| Conventional Commits, autor `jpjamal`, sem coautor nem atribuição de IA | mexer em segredos do GitHub ou chaves da VPS | coautor ou atribuição de IA no commit |
