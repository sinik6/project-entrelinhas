# Registros diários e visibilidade

**Origem:** RF-05 da especificação de origem. Tarefas T0301 a T0304.

## Regras
- Um registro (`entries`) tem autor, data (`entry_date`), texto integral (`body`), modo de
  visibilidade, `status` (`draft` ou `submitted`) e `submitted_at`.
- **Entregar** registra data e hora **no servidor** (AC-05.2) e escolhe o modo de visibilidade:

| Modo | O parceiro vê |
|---|---|
| `full` | texto completo e anexos |
| `private` | só a indicação de entrega: *"Enviado, mas mantido privado pelo autor"*. O texto não vai na API |
| `partial` | só o trecho delimitado pelo autor (linhas ou intervalo). O backend trunca e envia estritamente o intervalo |

- O trecho `partial` é guardado em `visible_start_offset` e `visible_end_offset`.
- O texto integral (`body`) é sempre do autor; o autor vê o próprio registro inteiro.
- **A filtragem é do backend** (constituição, regra 2). Nenhum endpoint devolve texto fora da regra.

## Pendências (a decidir na spec da T0301/T0302)
- Unidade dos offsets (caractere Unicode ou unidade UTF-16 do JavaScript) e se o trecho é
  escolhido por linhas ou por caracteres. Afeta backend e front; decidir antes de gravar dados.
- Se um registro `submitted` pode ser editado e, em caso afirmativo, o que acontece com a
  visibilidade e com os destaques já feitos.
- Se o autor pode mudar a visibilidade depois de entregar.
- Quantos registros por dia cada pessoa pode ter.
