---
id: 007-destaques-backend
status: rascunho
veredito: parcial
---

# Validação — Destaques e comentários (backend)

Evidência do que foi **realmente executado** (2026-11-08). Implementado e testado **localmente**; nada visto no ar, sem auditoria independente, sem arquivamento, nada commitado.

## Ambiente
- Backend local (Windows, Git Bash), PostgreSQL 17 descartável na porta 55433; `uv run pytest`. Sem dependência nova.
- Suíte inteira: **396 passaram, 12 ignorados** (`jq`, rodam no CI); 43 são de `apps/destaques`; `ruff` e `makemigrations --check` limpos; o teste de contrato compara as rotas com o OpenAPI (a 007 saiu de "planejado").

## Critério → evidência
| ID | Como foi provado | Resultado |
|---|---|---|
| REQ-13.1 | `test_req_13_1_*`: 201 com o trecho calculado; o autor também destaca; em `partial` a posição é relativa ao trecho visível, para o parceiro e para o autor | ✔ em teste |
| REQ-13.2, CTL-51 | `test_req_13_2_*`: 12 combinações inválidas (negativo, igual, invertido, enorme, string, float, bool, nulo, lista, objeto) e campos faltando → 422, nunca 500 | ✔ em teste |
| REQ-13.3, CTL-52 | `test_req_13_3_*`: `private` → 409 ao criar e ao listar, para o parceiro e para o autor | ✔ em teste |
| REQ-13.4 | `test_req_13_4_*`: comentário junto; comentário inválido não deixa destaque órfão | ✔ em teste |
| REQ-13.5, ABU-15, CTL-54 | `test_req_13_5_*` (51º → 409; o limite é por pessoa) e `test_abu_15_destaques_simultaneos_*`: **60 pedidos em threads reais**, 50 entram | ✔ em teste (PostgreSQL real) |
| REQ-13.6 | `test_req_13_6_*`: apagar o destaque apaga os comentários dos dois | ✔ em teste |
| REQ-13.7, ABU-16, CTL-53 | `test_req_13_7_*`, `test_abu_16_*`: 403 com a mensagem fixa e nada muda | ✔ em teste |
| REQ-14.1 | `test_req_14_1_*`: comentário com autor e hora; vazio, só espaços, 1001, controle, tipo errado → 422 sem repetir o texto; 1000 e quebra/tabulação passam | ✔ em teste |
| REQ-14.2, ABU-15 | `test_req_14_2_*` (21º → 409) e `test_abu_15_vinte_comentarios_simultaneos_*`: 25 threads, exatamente 20 entram | ✔ em teste |
| REQ-14.3, REQ-14.4 | `test_req_14_3_*` (edita, `editado_em`; edição inválida não muda), `test_req_14_4_*` | ✔ em teste |
| REQ-14.5 | `test_req_14_5_*`: posição, trecho, autor (nome e cor lida na hora), comentários e `meu` conforme quem pede; ordem de criação | ✔ em teste |
| REQ-14.6 | `test_req_14_6_*`: outro grupo, ids malformados e inexistentes, quem saiu do grupo → 404 em todas as 6 rotas; sem sessão → 401 | ✔ em teste |
| REQ-14.7, NFR-DEST-2, CTL-55 | `test_nfr_dest_*`: log só com ids (nenhum comentário, trecho ou edição); Admin sem os modelos | ✔ em teste |
| ABU-14, Art. 12 | `test_abu_14_*`: em `partial`, 6 posições além do trecho; a mensagem é a mesma para todas, cita só o tamanho do **visível** (`entre 0 e 7,`), nunca o do texto inteiro nem o escondido | ✔ em teste |
| PROP-9 | `test_prop_9_*`: 6 registros (`full` e `partial`), 25 posições sorteadas cada, semente fixa: `trecho == visível[inicio:fim]` e nenhum marcador escondido no JSON | ✔ (exemplos) |
| CTL-56 | `test_nfr_dest_so_o_dominio_*`: o app só chama `texto_visivel_para`; varredura proíbe `.texto` de registro; o teste da 005 continua verde | ✔ em teste |

## Mutação (roteiro em `backend/apps/destaques/tests/mutacao.py`)
18 mutantes: posição que passa do visível, negativa, vazia, `bool` como inteiro, tamanho errado na mensagem, `partial` e `private` devolvendo mais texto, limites 50 e 20 desfeitos, sem trava no registro e no destaque,
apagar e editar do outro, 404 de grupo removido (destaque e comentário), comentário de 1001 e só de espaços. Na primeira rodada **1 sobreviveu** ("mensagem cita o tamanho a mais": o teste só procurava "7");
os testes passaram a conferir a frase exata e o mutante morreu. **18 de 18 mortos.**

## Não provado
- **Nada no ar** (migração `destaques 0001` e as rotas novas nunca rodaram na VPS).
- Sem auditoria independente (a 005 teve uma e achou um vazamento que os testes do próprio autor não viam: fica o risco análogo aqui, em especial na regra "quem saiu do grupo").
- Sem teste de volume além dos limites (≤ 100 destaques × 20 comentários por resposta, sem paginação).
- O operador da VPS lê comentários no banco (ADR-0010).

## Veredito
**Parcial.** Backend implementado, 43 testes e 18/18 mutantes mortos; faltam deploy, conferência no ar, auditoria independente e arquivamento em `destaques.md`.
