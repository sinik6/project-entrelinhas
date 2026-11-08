---
id: 009-calendario
status: rascunho
veredito: parcial
---

# Validação — Calendário (backend e telas)

Evidência do que foi **realmente executado** (2026-11-08). Implementado e testado localmente; a grade foi vista **uma vez no navegador local**. Nada no ar, sem auditoria independente, sem arquivamento, nada commitado.

## Ambiente
- Backend: PostgreSQL 17 descartável (porta 55433), `uv run pytest`; 48 testes de `apps/calendario`; migração `acesso 0004_perfil_entrou_em` (com preenchimento das contas existentes); `ruff` e `makemigrations --check` limpos; o teste de contrato compara a rota com o OpenAPI (a 009 saiu de "planejado").
- Front: contêiner do SDK; `flutter analyze` limpo; testes de widget do calendário (grade, marcadores, legenda, navegação, lista do dia, erros) e 2 telas novas na acessibilidade.
- Navegador: pilha local (`docker compose up`), as duas contas de teste; conferido o 5º destino do menu e a grade de novembro.

## Critério → evidência
| ID | Como foi provado | Resultado |
|---|---|---|
| REQ-16.1 | `test_req_16_1_*` (dias do mês até hoje, mês passado inteiro, forma da resposta com `membros` e `estados` alinhados) | ✔ em teste |
| REQ-16.2 | `test_req_16_2_*` (`escreveu` com registro; `private` conta como escreveu para o parceiro, e a resposta não traz o texto) | ✔ em teste |
| REQ-16.3 | `test_req_16_3_*`: `falhou`, `pendente` hoje, `fora` antes da entrada (a data vem do perfil), registro antes da entrada vence a data, `entrou_em` desconhecido nunca vira `fora` | ✔ em teste |
| REQ-16.4, REQ-16.5, PROP-12 | `test_req_16_4_16_5_*`: 0, 3600, 7199 e 7200 s juntos; 7201 e 20 000 s não; só um escreveu; 23h50 e 00h10 são dias diferentes; simetria | ✔ em teste |
| REQ-16.6, CTL-61 | `test_req_16_6_*`: a resposta só tem `mes`, `hoje`, `membros` (nome, cor, foto) e `dias` (data, estados, juntos); nenhuma hora, texto, visibilidade, e-mail | ✔ em teste |
| REQ-16.7 | `test_req_16_7_*`: 10 formatos de mês inválidos, mês futuro e mês anterior à entrada do grupo → 422 | ✔ em teste |
| REQ-16.8 | `test_req_16_8_*`: sem grupo e sem perfil → vazio | ✔ em teste |
| REQ-16.9, ABU-20 | `test_abu_20_*` e `test_req_16_9_*`: 23:59:59 e 00:00:00 de São Paulo (02:59:59 e 03:00:00 UTC), "hoje" no 02h30 UTC é o dia anterior, `juntos` perto da meia-noite | ✔ em teste |
| ABU-19 | `test_abu_19_*`: quem é de outro grupo vê só os dele; registro de um membro num grupo antigo não conta | ✔ em teste |
| NFR-CAL-3 | `test_nfr_cal_3_*`: 31 dias cheios, no máximo 3 consultas da rota (fora a autenticação) | ✔ em teste |
| PROP-11 | `test_prop_11_12_*`: **1000 cenários sorteados** (semente fixa, entregas em 0, 8 e 23 h, diferenças de 0, 1, 7199, 7200, 7201 s) comparados a um oráculo escrito de outro jeito | ✔ (exemplos) |
| `entrou_em` | `test_entrou_em.py`: gravada ao criar o grupo (23h30 de SP = dia de SP) e ao aceitar o convite; o preenchimento das contas existentes usa a data de criação em SP | ✔ em teste |
| REQ-17.1 | `calendario_test.dart`: mês atual, 1º de novembro/2026 na coluna do domingo, mês anterior e volta, **não passa do mês atual**, mês anterior à entrada (422) fica de fora e desabilita a seta; navegador local: grade de novembro | ✔ teste e navegador local |
| REQ-17.2, REQ-17.3 | `calendario_test.dart`: um marcador por membro na cor dele, quem estava fora sem marcador, selo "juntos", **forma própria por estado** (cheio, vazado com ×, tracejado), texto alternativo exato de cada dia ("Dia 1: Ana escreveu; Bia escreveu; escreveram juntos") | ✔ em teste |
| REQ-17.4, REQ-17.5 | lista do dia (só os registros daquele dia, na visão de quem pede; "Nenhum registro neste dia."), legenda com os 5 itens | ✔ em teste |
| REQ-17.6 | erro 500 com "Tentar de novo", 401 → entrar, sem grupo → Grupo | ✔ em teste |
| NFR-CAL-1 | `acessibilidade_test.dart`: calendário e folha do dia, nos dois temas e em 360 e 1280 px (alvos de toque de 48 px: a tela do calendário usa 8 px de margem) | ✔ em teste |

## Mutação
- Backend (`backend/apps/calendario/tests/mutacao.py`): 15 mutantes (janela de 7199 e 7201 s, sem módulo, juntos com um só, registro que não vence a entrada, sem `fora`, hoje vira falha, dia de amanhã, mês futuro e anterior à entrada, registros e perfis de outro grupo, dia pelo UTC, entrada não gravada ao criar grupo e ao aceitar convite). Na primeira rodada **2 sobreviveram** ("registros de outro grupo" e "dia pelo UTC"); acrescentados o teste do registro de grupo antigo e o do "hoje" às 02h30 UTC; **15 de 15 mortos**.
- Front (`frontend/tool/mutacao_calendario.py`): 10 mutantes (formas trocadas, rótulos sem "não" e sem "juntos", primeira coluna errada, selo sempre, passa do mês atual, mês anterior sem trava, lista do dia com o mês todo, "fora" desenhado). **10 de 10 mortos.**

## Não provado
- **Nada no ar** (a migração `0004` e a rota nova nunca rodaram na VPS; o preenchimento de `entrou_em` das contas reais não foi conferido).
- Só a grade de novembro foi vista no navegador (a Bia escreveu em 06/11 e não em 07/11; o dia de hoje aparece tracejado); o selo "juntos" e a lista do dia **não** foram vistos no navegador, só em teste de widget. 360 px no navegador não foi conferido.
- Sem teclado puro nem leitor de tela reais; sem auditoria independente.
- Escolhas do agente que o dono ainda ratifica: `private` conta como escreveu; "juntos" = mesmo dia e até 2 h entre as entregas; `entrou_em` desconhecido nunca é "fora".

## Veredito
**Parcial.** Backend e telas implementados, 48 testes de backend, 15/15 e 10/10 mutantes mortos; faltam deploy, conferência no ar, auditoria independente e arquivamento em `calendario.md`.
