---
id: entrelinhas
status: rascunho
---

# Mapa de capacidades — Entrelinhas

Fonte: [`specs/origem/especificacao-origem.md`](origem/especificacao-origem.md). Aguarda aprovação do dono
do produto (portão do P3) antes de qualquer spec de feature.

| Módulo (id estável) | Responsabilidade | Depende de | Spec viva |
|---|---|---|---|
| base | API, banco, health check, CI e deploy na VPS | — | specs/system/base.md (sai ao arquivar a 001) |
| acesso-espaco | contas, sessão, espaço de 2 pessoas, convites | base | specs/system/acesso-espaco.md |
| registros | registro diário, entrega, visibilidade `full`/`private`/`partial`, leitura filtrada no servidor, tela de escrita e leitura | acesso-espaco | specs/system/registros.md |
| destaques | destaques e comentários estilo Kindle sobre o texto visível | registros | specs/system/destaques.md |
| fotos-lembretes | fotos de textos manuscritos, PWA e Web Push às 21h30 | registros | specs/system/fotos-lembretes.md |

Ordem de construção: base → acesso-espaco → registros → destaques, fotos-lembretes

Regras:
- ids em kebab-case, escolhidos uma vez, nunca renomeados no meio da iniciativa;
- dependências em uma só direção, sem ciclo;
- o contrato entre dois módulos fica na spec do módulo que fornece (ex.: o texto visível de um registro é
  fornecido por `registros`; `destaques` o consome).

## Mudanças planejadas (uma P2 por módulo, na ordem do mapa)
| Mudança | Módulo | Tarefas da origem | Estado |
|---|---|---|---|
| 001-base-do-projeto | base | T0101, T0102, T0103 | em andamento |
| 002 (a abrir) | acesso-espaco | T0201, T0202 | planejada |
| 003 (a abrir) | registros — backend | T0301, T0302, T0303 | planejada |
| 004 (a abrir) | registros — front (cria `frontend/`) | T0304 | planejada |
| 005 (a abrir) | destaques — backend | T0401, T0402 | planejada |
| 006 (a abrir) | destaques — front | T0403 | planejada |
| 007 (a abrir) | fotos-lembretes — fotos | T0501 | planejada |
| 008 (a abrir) | fotos-lembretes — PWA e push | T0502 | planejada |

## Decisões em aberto por módulo
Cada uma vira esclarecimento (com opções e recomendação) na spec da mudança indicada, antes do design.

| Módulo | Pergunta |
|---|---|
| acesso-espaco | Como o convite é criado e aceito (link, código, e-mail) e quando expira? O que acontece quando uma das duas pessoas sai? Fuso horário por usuário, necessário ao lembrete. |
| registros | Unidade dos offsets (caractere Unicode ou unidade UTF-16 do JavaScript) e trecho `partial` por linhas ou por caracteres. Registro entregue pode ser editado? A visibilidade pode mudar depois? Quantos registros por dia por pessoa? |
| destaques | Os offsets referem o texto integral ou o visível? Quem edita ou apaga um comentário? O autor do registro também pode destacar o próprio texto? |
| fotos-lembretes | Fotos no SILO da VPS (padrão do Vinculus) ou em volume? Tamanho e tipos aceitos. Foto visível em registro `partial`? Texto do lembrete e regra de não enviar se o dia já foi entregue. |

Risco: decidir a unidade dos offsets só depois de haver dados corrompe trechos e destaques; fica como
pré-requisito da mudança 003.
