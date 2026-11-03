---
id: entrelinhas
status: rascunho
---

# Mapa de capacidades — Entrelinhas

Fontes: [`specs/origem/especificacao-origem.md`](origem/especificacao-origem.md) e
[`specs/origem/visao-complementar-2026-11-03.md`](origem/visao-complementar-2026-11-03.md).
Reorganização aprovada pelo dono em 2026-11-03; o mapa como um todo ainda aguarda aprovação final (portão do P3).

| Módulo (id estável) | Responsabilidade | Depende de | Spec viva |
|---|---|---|---|
| base | API, banco, health check, CI e deploy na VPS, administrador inicial | — | specs/system/base.md (sai ao arquivar a 001 e a 002) |
| acesso-espaco | contas e sessão; perfil com foto opcional e cor obrigatória; grupo de escrita (máximo 2 membros no MVP) e convites | base | specs/system/acesso-espaco.md |
| fotos | foto do manuscrito: envio, armazenamento privado e entrega só a quem pode ler | acesso-espaco | specs/system/fotos.md |
| registros | registro diário, entrega só com foto e texto, visibilidade `full`/`private`/`partial`, leitura filtrada no servidor, telas de escrita e leitura | acesso-espaco, fotos | specs/system/registros.md |
| destaques | destaques e comentários estilo Kindle sobre o texto visível, na cor de quem comentou | registros | specs/system/destaques.md |
| calendario | agenda com o dia em que cada um escreveu, o dia em que falhou e o aviso "escreveram juntos" | registros | specs/system/calendario.md |
| lembretes | PWA instalável e Web Push diário às 21h30 | acesso-espaco, calendario | specs/system/lembretes.md |
| grupos *(futuro, fora do MVP)* | grupos de estudo e de leitura (clube do livro) | acesso-espaco, registros | sem spec |

Ordem de construção: base → acesso-espaco → fotos → registros → destaques, calendario → lembretes. Depois do MVP: grupos.

Regras:
- ids em kebab-case, escolhidos uma vez, nunca renomeados no meio da iniciativa;
- dependências em uma só direção, sem ciclo;
- o contrato entre dois módulos fica na spec do módulo que fornece (ex.: o texto visível de um registro é
  fornecido por `registros`; `destaques` e `calendario` o consomem).

## Mudanças planejadas (uma P2 por módulo, na ordem do mapa)
| Mudança | Módulo | Tarefas da origem | Estado |
|---|---|---|---|
| 001-base-do-projeto | base | T0101, T0102, T0103 | em andamento (falta T-1.5 e arquivar) |
| 002-administrador-inicial | base | — (pedido do dono em 2026-10-28) | no ar (225324a), 429 e login do dono provados; 2 auditorias independentes feitas, correções das ondas 5 e 6 ainda sem commit; faltam ratificação do usuário, 2º deploy visto e arquivar |
| 003 (a abrir) | acesso-espaco — contas, perfil, cor, grupo de escrita, convites | T0201, T0202 + visão de 2026-11-03 | planejada |
| 004 (a abrir) | fotos — envio e armazenamento privado | T0501 (adiantada) | planejada |
| 005 (a abrir) | registros — backend | T0301, T0302, T0303 | planejada |
| 006 (a abrir) | registros — front (cria `frontend/`) | T0304 | planejada |
| 007 (a abrir) | destaques — backend | T0401, T0402 | planejada |
| 008 (a abrir) | destaques — front | T0403 | planejada |
| 009 (a abrir) | calendario — backend e front | visão de 2026-11-03 | planejada |
| 010 (a abrir) | lembretes — PWA e Web Push | T0502 | planejada |

## Decisões tomadas pelo dono
| Data | Decisão |
|---|---|
| 2026-11-03 | O grupo de escrita (todos escrevem algo todo dia) é o MVP e tem no máximo 2 pessoas. Grupos de estudo e de leitura (clube do livro é o mesmo que leitura) ficam para depois do MVP, como módulo `grupos`. |
| 2026-11-03 | O registro só vale como entregue com foto do manuscrito **e** texto digitado. |
| 2026-11-03 | Perfil: foto personalizada opcional; cor obrigatória, usada nos comentários e no calendário. |
| 2026-11-03 | O calendário mostra o dia escrito e o dia em que falhou, e avisa quando os dois escreveram num intervalo de 2 horas. |
| 2026-11-03 | Mapa reorganizado como acima (fotos antes de registros; calendário e lembretes como módulos). |

## Decisões em aberto por módulo
Cada uma vira esclarecimento (com opções e recomendação) na spec da mudança indicada, antes do design.

| Módulo | Pergunta |
|---|---|
| acesso-espaco | Como o convite é criado e aceito (link, código, e-mail) e quando expira? O que acontece quando uma das duas pessoas sai? Fuso horário por usuário (necessário ao "dia" do calendário e ao lembrete). A cor vem de uma paleta fixa ou é livre, e as duas pessoas do grupo podem ter a mesma cor? Tamanho e tipos da foto de perfil. O modelo de dados deve chamar a unidade de "grupo" com tipo e limite, para o grupo de estudo e de leitura caberem depois sem refazer o banco. |
| fotos | Onde ficam as fotos: SILO da VPS (padrão do Vinculus) ou volume? Tamanho e tipos aceitos. A foto é visível ao parceiro em registro `partial`? Quantas fotos por registro? |
| registros | Unidade dos offsets (caractere Unicode ou unidade UTF-16 do JavaScript) e trecho `partial` por linhas ou por caracteres. Há tamanho mínimo de texto para valer? Registro entregue pode ser editado? A visibilidade pode mudar depois? Quantos registros por dia por pessoa? Registro `private` com foto e texto conta como "escreveu" no calendário do parceiro? |
| destaques | Os offsets referem o texto integral ou o visível? Quem edita ou apaga um comentário? O autor do registro também pode destacar o próprio texto? |
| calendario | O que é "falhou": dia sem entrega até a meia-noite no fuso da pessoa, ou até o horário do lembrete? "Intervalo de 2 horas" é entre os horários de entrega dos dois? O calendário do parceiro mostra o dia escrito mesmo quando o texto é privado? |
| lembretes | Texto do lembrete, e se não é enviado a quem já entregou o dia. Chaves VAPID e o processo que dispara o push (serviço próprio no compose). |

Risco: decidir a unidade dos offsets só depois de haver dados corrompe trechos e destaques; fica como
pré-requisito da mudança 005. Risco: o limite de 2 membros hoje é regra de negócio; guardar o limite como
atributo do grupo (e não fixo no código) evita refazer o banco quando os grupos de estudo e leitura chegarem.
