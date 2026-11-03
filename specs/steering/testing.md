# Testes — Entrelinhas

## Pirâmide e onde fica cada nível
| Nível | Ferramenta | Pasta | Comando |
|---|---|---|---|
| Unidade | pytest | `backend/apps/<app>/tests/` | `uv run pytest apps` |
| Integração (banco real) | pytest-django + PostgreSQL 17 em container | `backend/apps/<app>/tests/`, `backend/tests/` | `uv run pytest --create-db` |
| Contrato | comparação com `contracts/openapi.yaml` | a definir na primeira API de domínio | — |
| Property-based | Hypothesis, quando uma PROP pedir | `backend/apps/<app>/tests/` | `uv run pytest -k prop` |
| E2E | Playwright, junto da mudança do front | `frontend/e2e/` | a definir |
| Mutação (regras críticas) | a avaliar para a regra de visibilidade | — | — |

## Convenções
- ID da spec no nome do teste (`test_req_1_3_…`) ou na docstring (`REQ-1.3`); o `sdd_lint --code backend` confere.
- Todo endpoint que devolve texto de registro: teste que cria registro `private` e `partial`, lê como
  parceiro e confere que o texto escondido não aparece em nenhum ponto da resposta (Art. 12).
- Todo recurso novo: teste de acesso cruzado (outro grupo recebe 404).
- Mocks só na fronteira externa.
- Suíte rápida (hoje 72 casos mais 12 que dependem de `jq`, ~15 s); flaky é bug.

## Definição de pronto
Testes da tarefa vistos falhando e depois passando; suíte afetada verde; lint limpo; `sdd_lint.py` sem erro;
`validation.md` com a evidência do que foi executado e do que não foi.
