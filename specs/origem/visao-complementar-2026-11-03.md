# Visão complementar do dono do produto — 2026-11-03

> Transcrição de uma explicação falada, guardada como veio (fonte, não se edita). Complementa
> `especificacao-origem.md` e, onde discordar dela, ainda **não** vale: depende das decisões registradas
> em `specs/capability-map.md`.

Texto recebido:

> comentário, escreva esse texto, você pode fazer um comentário dentro daquele texto, você seleciona com o
> mouse e faz, saca? E o que mais? Basicamente isso, ele tem uma agenda, uma data, tudo bonitinho para você
> poder fazer exatamente isso. Eu incentivo as outras a escrever, então todo dia tá o horário, ele mandou um
> alerta para as duas pessoas que estão na mesma sala, e elas têm que escrever juntas, e no calendário vai
> aparecer o dia que cada um escreveu, o dia que cada um falhou, e quando os dois escreveram num intervalo de
> 2 horas, ele vai aparecer informando que os dois escreveram juntos, meio que para incentivar um ao outro.
> Então a ideia é que sejam isso, é um lugar para você escrever e as outras pessoas poderem ver, que estão
> linkadas na sua sala, é mais privado por enquanto. Ah, entendi. Então também vai ter a questão quando for
> escrever, tem que colocar a foto que escreveu e digitar também. Isso, para ser validado. Será validado se
> tiver a foto, né? O anexo também. Vai ter o usuários também? Os usuários vão poder montar grupos de estudo?
> Vão poder montar grupos de estudo, grupo de leitura, grupo de livro, perfil pode colocar foto personalizada,
> se você quiser, e toda vez que você criar o perfil, é obrigado a você selecionar uma cor para você. Porque
> toda vez que você fizer um comentário ou aparecer na agenda, vai aparecer a sua cor para te determinar que
> foi você que fez. As pessoas que estão no seu grupo saber, a cor tal é aquela pessoa. Entendi. Beleza.

## Leitura do agente (não é decisão; serve de pauta)
| Ideia dita | Já está na spec de origem? | Efeito |
|---|---|---|
| comentar selecionando o texto com o mouse | sim (RF-11, destaques) | nenhum |
| alerta diário às duas pessoas da sala | sim (Web Push às 21h30) | nenhum |
| calendário com o dia em que cada um escreveu e o dia em que falhou | não | módulo novo (calendário) |
| aviso "escreveram juntos" quando os dois entregam num intervalo de 2 horas | não | regra nova no calendário |
| registro só é validado com foto do manuscrito **e** texto digitado | em parte (foto é anexo opcional na fase 5) | a foto sobe para o núcleo de `registros` |
| perfil com foto opcional | não | `acesso-espaco` |
| cor obrigatória no perfil, usada nos comentários e na agenda | não | `acesso-espaco`; usada por `destaques` e calendário |
| grupos de estudo, leitura e livro | **contradiz** "exatamente dois participantes" (Art. 13) | decisão do dono |
