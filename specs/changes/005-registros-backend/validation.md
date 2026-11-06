---
id: 005-registros-backend
status: rascunho
veredito: parcial
---

# Validação — Registros diários (backend)

Evidência do que foi **realmente executado**. A mudança está implementada e testada **localmente**; **nada dela foi visto no ar**, não houve auditoria independente
e o arquivamento não foi feito. Nada commitado ainda (2026-11-05).

## Ambiente
- Backend: máquina local (Windows, Git Bash), PostgreSQL 17 descartável na porta 55433; `uv run pytest`. Sem dependência nova (só Django, DRF e Pillow, que já estavam).
- Números finais (depois da auditoria): **353 passaram, 12 ignorados** (`jq`, rodam no CI); 119 são de `apps/registros`; `ruff` e `makemigrations --check` limpos; o teste de contrato compara as rotas com o OpenAPI (a 005 saiu de "planejado").
- Não houve navegador nesta mudança (a 005 não tem tela; as telas são da 006).

## Critério → evidência
| ID | Como foi provado | Resultado |
|---|---|---|
| REQ-8.1 | `test_req_8_1_*`: 201, registro do grupo, fotos anexadas na ordem, hora e dia do servidor, campos extras do cliente ignorados, as 3 visibilidades, atomicidade (foto ruim não deixa nada), anônimo 401 | ✔ em teste |
| REQ-8.2, CTL-36 | `test_req_8_2_*`: sem foto, 4 fotos, 3 aceitas, foto alheia, inexistente, malformada, de perfil, repetida, já usada em outro registro, marcada como anexada: todas 422 com a mesma mensagem (sem sondar a existência da foto) | ✔ em teste |
| REQ-8.3 | `test_req_8_3_*` (API e domínio): 9 e 10 caracteres úteis, 20 000 e 20 001, controle (`\x00`, `\r`, escape), tipos errados; o texto não aparece na mensagem de erro nem no log | ✔ em teste |
| REQ-8.4, ABU-11 | `test_req_8_4_*`: 22 combinações de trecho (negativo, invertido, vazio, passa do fim, 10¹², string, float, bool, nulo, faltando campo, em `full` e `private`); emoji conta como 1 ponto de código; sempre 422, nunca 500 | ✔ em teste |
| REQ-8.5, ABU-9 | `test_req_8_5_*`: segundo do dia → 409; virada à meia-noite de São Paulo (23h30 e 00h30 de SP, UTC virando o dia); uma pessoa por vez; `test_abu_9_*`: **6 threads reais** entregando juntas → um 201 e cinco 409, um registro e uma foto anexada | ✔ em teste (PostgreSQL real) |
| REQ-8.6 | `test_req_8_6_*`: sem grupo e sem perfil → 409 | ✔ em teste |
| REQ-8.7 | `test_req_8_7_*`: PUT, PATCH e DELETE em `/registros/{id}` e DELETE em `/registros` → 405; a visibilidade continua a mesma | ✔ em teste |
| REQ-9.1 a 9.4 | `test_req_9_*` e `test_visibilidade.py`: as quatro visões (autor, parceiro `full`, `partial`, `private`) pelo detalhe e pela lista | ✔ em teste |
| REQ-9.5, CTL-33 | `test_req_9_5_*`: o parceiro recebe a foto de um `full` e 404 em `partial` e `private`; o autor vê as dele | ✔ em teste |
| REQ-9.6, ABU-10, CTL-35 | `test_req_9_6_*`, `test_abu_10_*` (registro e foto de outro grupo, id inexistente e malformado) | ✔ em teste |
| REQ-9.7, ABU-8, CTL-32 | `test_req_9_7_*`: marcadores únicos num texto `partial`; detalhe, lista (mês atual, 2000-01, inválido, futuro), erros de PUT e DELETE e cabeçalhos do parceiro não trazem nenhum marcador escondido (e o visível aparece, para o teste enxergar a resposta certa); dois registros `private` de 10 e 5 000 caracteres têm resposta idêntica (o tamanho não vaza) | ✔ em teste |
| REQ-10.1 a 10.3 | `test_req_10_*`: ordem decrescente, os dois membros, mês pelo fuso de SP (23h30 de 30/11 é novembro), mês vazio, 11 formatos inválidos, sem o parâmetro, mês atual aceito e seguinte recusado, sem grupo → `[]` | ✔ em teste |
| NFR-REG-1, CTL-31 | `test_nfr_reg_1_*`: só `domain.py` lê `.texto` no app; nenhum outro app lê o texto de registro; deny-by-default (quem não é o autor recebe a visão do parceiro) | ✔ em teste (varredura do código) |
| NFR-REG-2 | cada regra de entrada tem teste de API com 422 | ✔ |
| NFR-REG-3, CTL-37 | `test_nfr_reg_3_*`: o log da entrega e o de erro não levam texto, trecho nem nome de foto; só ids e contagens | ✔ em teste |
| NFR-REG-4, CTL-39 | `test_nfr_reg_4_*`: `Registro` e `Foto` não estão no Admin | ✔ em teste |
| PROP-6 | `test_prop_6_*`: 200 casos sorteados (semente fixa) de tamanho, visibilidade e trecho alinhado aos marcadores; cada marcador aparece na resposta do parceiro se e somente se está no texto visível | ✔ (exemplos, não prova exaustiva) |
| PROP-7 | `test_prop_7_*`: 5 textos (ASCII, emoji e bandeira, acento composto, quebras e tabulação, japonês) × 100 trechos sorteados: `texto_visivel == texto[inicio:fim]` em pontos de código | ✔ (exemplos) |
| Contrato | `test_ctl_18_*` compara as rotas com o OpenAPI da 005; todos os contratos validam | ✔ |

## Mutação da regra de visibilidade (T-2.6)
O roteiro agora está no repositório (`backend/apps/registros/tests/mutacao.py`) e tem **26 mutantes**; os 26 foram mortos na última rodada. A descrição abaixo é da primeira rodada, com 22 mutantes em `domain.py`, `services.py` e `fotos/servicos.py`; os 22 foram mortos (os 4 acrescentados depois cobrem a saída do grupo e a limpeza de fotos): parcial devolve o texto inteiro; parcial devolve fotos; `private` devolve o texto; `private` devolve fotos;
parceiro recebe o trecho; todos veem como autor; trecho vazio aceito; trecho passa do fim; trecho negativo aceito; mínimo de texto 5; controle aceito; dia pelo UTC; mês futuro aceito; lista e detalhe sem filtro de grupo;
foto de outro dono; foto já anexada aceita; sem teto de 3 fotos; lista em ordem errada; parceiro vê foto de `partial`; parceiro vê foto de `private`; foto de registro de outro grupo.
Um mutante sobreviveu na primeira rodada ("aceita foto já anexada": era equivalente porque `registro__isnull` já bloqueava) e o teste `test_req_8_2_foto_marcada_como_anexada_*` foi acrescentado para matá-lo.

## Não provado
- **Nada no ar:** o deploy da 005 (migração de `registros` e das fotos, rotas novas) não foi feito.
- Sem teste de carga nem de volume: a lista do mês não é paginada (no máximo 2 pessoas × 31 dias).
- A `entregue_em` guarda o instante do servidor; não há teste com relógio do servidor adulterado (fora do alcance).
- O texto fica legível no banco para quem opera a VPS (ADR-0010, risco aceito, THR-38).
- Auditoria independente feita (ver acima), mas só uma rodada, sobre o código antes das correções; as correções foram verificadas pelos testes e pela mutação, não por um segundo auditor. Sem prova de que a 006 converterá offsets UTF-16 corretamente (é da 006).

## Veredito
**Parcial.** O backend de registros está implementado, auditado por um revisor independente e corrigido nos achados, com a regra de visibilidade protegida por 26 mutantes; faltam o deploy das correções e a conferência no ar, e o arquivamento em `registros.md`.

## Auditoria independente (T-3.2, parte 1)
Feita por um subagente separado (somente leitura, instruído a tentar quebrar a regra), que também rodou `pytest apps/registros apps/fotos` (155 passaram na hora). **Veredito dele: aprovado com ressalvas;
nenhum caminho pela API entrega ao parceiro texto `private`, texto fora do trecho, offsets, tamanho do texto ou foto fora do `full`.** Achados e o que foi feito:

| # | Severidade | Achado | Tratamento |
|---|---|---|---|
| 1 | média | registros ficam no grupo de origem: quem entra depois no grupo (ou o parceiro que ficou) lê os de quem saiu; o autor que saiu perdia os próprios | **corrigido**: `_pode_ler` (autor sempre; parceiro só se os dois ainda estão no grupo do registro), a lista com `autor = eu OU (grupo e autor ainda nele)`, a mesma conferência na foto; REQ-9.8 e CTL-40 novos; `test_troca_de_grupo.py` (6 testes) |
| 2 | baixa | a limpeza de fotos avulsas podia apagar a foto que uma entrega acabara de anexar | **corrigido**: cada foto é reconferida com `select_for_update(skip_locked=True)` na hora de apagar; 2 testes (foto travada por outra transação e anexação no meio tempo) |
| 3 | baixa | o banco garantia menos que a aplicação | **corrigido**: CHECKs de `visibilidade`, de `trecho_fim <= char_length(texto)` (em pontos de código, provado com emoji) e de "foto com registro está anexada"; migrações `registros 0002` e `fotos 0004`; `test_integridade.py` |
| 4 | baixa | testes que provavam menos do que diziam | **corrigido**: a lista confere que o registro está nela; o log confere o nome real do arquivo; o ramo `IntegrityError → 409` ganhou teste próprio; a varredura de NFR-REG-1 pega `values`, `values_list`, `only` e `defer` em várias linhas |
| 5 | baixa | divergências spec × código; roteiro de mutação fora do repositório; `
` | **corrigido**: requirements, design e threat-model alinhados ao código; roteiro em `tests/mutacao.py`; a 006 (REQ-11.4) passa a trocar `
` por `
` antes de calcular posições |

O auditor também listou o que **não** verificou: tempo de resposta (o ORM carrega o texto inteiro mesmo na visão do parceiro), nginx e BFF (cache ou log de corpo), o deploy e o OpenAPI linha a linha. Continuam sem verificação.
A auditoria foi feita sobre o commit `e998f08`; as correções acima ainda **não estão commitadas nem no ar**.
