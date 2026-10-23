# Destaques e comentários (estilo Kindle)

**Origem:** RF-11 da especificação de origem. Tarefas T0401 a T0403.

## Regras
- O parceiro seleciona uma área do texto **que lhe é visível** e a destaca (AC-11.1).
- O destaque (`entry_highlights`) guarda `start_offset`, `end_offset` e `highlighted_text`; fica
  marcado visualmente no leitor (AC-11.2).
- O usuário anexa um comentário (`entry_comments`) ao destaque (AC-11.3); hover, clique ou toque
  mostra o comentário (AC-11.4).
- Os offsets são **validados contra o texto visível** devolvido ao parceiro (AC-11.5). Em registro
  `partial`, destaque fora do trecho visível é rejeitado com 422; em `private`, não existe destaque.
- O texto do destaque na resposta não pode revelar o que está fora do trecho visível (constituição, regra 2).
- **Proposta, a confirmar na spec da T0402:** `highlighted_text` é gravado pelo servidor a partir do
  texto que ele tem, sem aceitar o valor do cliente.

## Pendências (a decidir na spec da T0401/T0402)
- Referência dos offsets: texto integral ou texto visível. Em `partial`, a escolha muda o que acontece
  se o autor alterar o trecho depois de haver destaques.
- Quem pode editar ou apagar um comentário, além do próprio autor dele.
- Se o autor do registro também pode destacar o próprio texto (a spec fala do parceiro).
