# ADR-0011 — Pacote `characters` para fronteiras de grafema

- Status: proposto (agente, por delegação do usuário em 2026-11-05); vira "aceito" na ratificação do G1
- Data: 2026-11-05
- Mudança de origem: 006-registros-front (usado também pela 008)

## Contexto
Ao escolher o trecho `partial` ou um destaque, a seleção do `TextField` vem em unidades UTF-16 e pode cair no meio de um grafema (um emoji com tom de pele, uma letra com acento
composto, uma bandeira). Cortar ali mostra ao parceiro metade de um símbolo ou, no pior caso, um caractere a mais que o autor não queria mostrar.

## Decisão
Usar o pacote `characters` (publicado pela equipe do Dart/Flutter, já presente no `pubspec.lock` como dependência transitiva do SDK) declarado em `pubspec.yaml` na mesma versão que o SDK
fixa, para empurrar as extremidades da seleção para fronteiras de grafema antes de converter para pontos de código (ADR-0009).

## Consequências
- Nenhum pacote novo no build (já vinha no SDK); passa a ser dependência direta e entra na lista do teste `test_ctl_20_*`.
- A regra de grafemas depende da versão do Unicode do pacote. O ajuste é sempre **para dentro** da seleção (a seleção encolhe até a fronteira de grafema mais próxima, nunca cresce): na dúvida, o parceiro lê menos, não mais. A prévia mostra o resultado.

## Alternativas descartadas
- **Cortar em ponto de código:** pode partir um emoji composto.
- **Biblioteca de ICU/segmentação própria:** peso e risco sem ganho.
