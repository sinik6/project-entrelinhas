---
id: 004-fotos
titulo: Fotos privadas — envio, armazenamento e entrega (manuscrito e perfil)
status: em-revisao
tamanho: P2
risco: alto
capacidades: [fotos, acesso-espaco]
autor: jpjamal
criado: 2026-11-05
---

# Requisitos — Fotos privadas (manuscrito e perfil)

## Contexto e objetivo
O registro só vale como entregue com a **foto do manuscrito** e o texto digitado (decisão do dono, 2026-11-03). Antes de
`registros` existir, o app precisa saber **receber, guardar e entregar uma foto com privacidade**. Esta mudança entrega isso para
dois usos: a foto do manuscrito (que a 005 vai anexar a um registro) e a foto de perfil opcional (prometida na 003). A foto é dado
sensível (mostra a letra e o texto íntimo da pessoa); por isso risco alto.

> **Decisões tomadas pelo agente por delegação do usuário** ("faça todas as specs faltantes, sem me perguntar nada", 2026-11-05).
> Elas entram em revisão no portão G1 e só valem depois da ratificação do dono. Cada linha marcada "decidida pelo agente" é uma
> dessas decisões, com a alternativa descartada.

## Suposições
| Suposição | Status |
|---|---|
| As fotos ficam num **volume Docker privado** da própria API, servidas só por endpoint autenticado; o SILO (bucket) não entra agora | decidida pelo agente (alternativa descartada: SILO da VPS; exige rede `infra_storage` e bucket por projeto, complexidade sem ganho para 2 pessoas) |
| Tipos aceitos: **JPEG, PNG e WebP**; tamanho máximo **8 MB** por envio; lado maior até **4096 px** | decidida pelo agente (HEIC fica de fora: o navegador do celular converte para JPEG ao escolher a foto) |
| A foto é **recodificada no servidor** (Pillow): o arquivo guardado é uma imagem nova, sem metadados (EXIF, GPS) | decidida pelo agente |
| Foto de perfil é opcional, **uma por pessoa**, reduzida a no máximo 1024 px no lado maior | decidida pelo agente |
| Foto de manuscrito: de **1 a 3** por registro (o mínimo de 1 é regra da 005; o teto de 3 é guardado aqui) | decidida pelo agente |
| Foto de manuscrito é visível **só ao autor** nesta mudança; a regra "o parceiro vê a foto quando o registro é `full`" é contrato da 005 | decidida pelo agente (a foto mostra o texto inteiro: em `partial` e `private` ela nunca pode ir ao parceiro; Art. 12) |
| Foto de perfil é visível ao autor e à outra pessoa do mesmo grupo | decidida pelo agente |
| Foto enviada e ainda não anexada a registro (avulsa) é apagada depois de 24 h pelo comando `limpar_fotos`, chamado no deploy | decidida pelo agente |
| Pacote novo: **Pillow** no backend e **image_picker** no front, cada um com ADR | decidida pelo agente (ADR-0007, ADR-0008) |

## Métricas de sucesso
- Uma foto de celular de 6 MB é enviada e aparece no perfil em menos de 5 segundos numa conexão comum.
- Nenhum arquivo de foto é alcançável por URL sem sessão válida e sem a regra de quem pode ver.

## Glossário
| Termo | Significado |
|---|---|
| Foto avulsa | foto enviada e ainda não anexada a registro nem ao perfil |
| Finalidade | `manuscrito` ou `perfil`; define limites e quem pode ver |
| Recodificar | abrir a imagem e gravar uma nova, descartando metadados e qualquer conteúdo extra do arquivo original |

## Papéis e autorização
| Papel | Ação | Recurso | Permitido? | Condição |
|---|---|---|---|---|
| Participante | enviar foto | foto | sim | autenticado, dentro dos limites |
| Participante | ver foto de manuscrito | foto | sim | só as próprias (parceiro: 404 até a 005) |
| Participante | ver foto de perfil | foto | sim | a própria ou a da outra pessoa do grupo |
| Participante | apagar foto avulsa | foto | sim | só as próprias e só enquanto avulsa |
| Participante | definir ou remover a própria foto de perfil | perfil | sim | só a própria |
| Anônimo | qualquer rota de foto | foto | não | 401 |
| Participante | foto de outro grupo | foto | não | 404 |

## Histórias e critérios de aceite

### US-6 — Enviar foto do manuscrito
**Como** participante, **quero** enviar a foto da minha letra, **para** anexá-la ao meu registro.

- **REQ-6.1** QUANDO o participante enviar um arquivo JPEG, PNG ou WebP válido de até 8 MB com a finalidade `manuscrito`, O sistema DEVE guardá-lo como foto avulsa e devolver o identificador dela.
- **REQ-6.2** SE o conteúdo do arquivo não for uma imagem JPEG, PNG ou WebP (mesmo que o nome ou o tipo declarado digam que é), ENTÃO O sistema DEVE recusá-lo com erro de validação.
- **REQ-6.3** SE o arquivo passar de 8 MB ou o lado maior da imagem passar de 4096 px, ENTÃO O sistema DEVE recusá-lo com erro de validação.
- **REQ-6.4** O sistema DEVE guardar a foto recodificada, sem metadados, com nome gerado (UUID) e nunca com o nome enviado.
- **REQ-6.5** QUANDO o autor consultar uma foto de manuscrito dele, O sistema DEVE devolver a imagem com tipo fixo, `Cache-Control: private, no-store` e `X-Content-Type-Options: nosniff`.
- **REQ-6.6** SE outra pessoa (do mesmo grupo ou de outro) consultar uma foto de manuscrito que não é dela, ENTÃO O sistema DEVE responder 404.
- **REQ-6.7** QUANDO o autor apagar uma foto avulsa dele, O sistema DEVE remover o registro e o arquivo.
- **REQ-6.8** SE o autor tentar apagar uma foto já anexada a registro, ENTÃO O sistema DEVE recusar com 409.
- **REQ-6.9** QUANDO o comando `limpar_fotos` rodar, O sistema DEVE apagar as fotos avulsas criadas há mais de 24 horas, e nenhuma outra.

### US-7 — Foto de perfil
**Como** participante, **quero** ter uma foto no meu perfil, **para** a outra pessoa me reconhecer.

- **REQ-7.1** QUANDO o participante enviar uma imagem válida com a finalidade `perfil` e defini-la como foto do perfil, O sistema DEVE reduzi-la a no máximo 1024 px e passar a devolvê-la no perfil dele.
- **REQ-7.2** QUANDO o participante trocar ou remover a foto de perfil, O sistema DEVE apagar a foto anterior (registro e arquivo).
- **REQ-7.3** QUANDO o participante consultar o grupo, O sistema DEVE incluir, para cada membro, o endereço da foto de perfil quando houver, e nunca o e-mail.
- **REQ-7.4** QUANDO um membro do grupo consultar a foto de perfil da outra pessoa do grupo, O sistema DEVE devolvê-la; foto de perfil de pessoa de outro grupo DEVE responder 404.
- **REQ-7.5** SE o participante tentar usar como foto de perfil uma foto de finalidade `manuscrito` ou de outra pessoa, ENTÃO O sistema DEVE recusar.

### Telas da foto de perfil (continuação da US-7)
- **REQ-7.6** QUANDO o participante abrir o perfil, O app DEVE permitir escolher uma foto, mostrá-la em prévia circular e enviá-la, e permitir removê-la.
- **REQ-7.7** SE o servidor recusar a foto, ENTÃO O app DEVE mostrar a mensagem em português, sem detalhe técnico.
- **REQ-7.8** ENQUANTO a foto de perfil não existir ou não carregar, O app DEVE mostrar a inicial do nome sobre a cor da pessoa.

## Requisitos não funcionais
- **NFR-FOTO-1** O sistema DEVE gravar as fotos fora da pasta pública (nenhum `static` nem `media` servido pelo nginx ou pelo WhiteNoise) e dentro de um volume Docker que entra no backup.
- **NFR-FOTO-2** O sistema DEVE limitar o corpo do envio de foto a 9 MB no nginx e a 8 MB na API, e não limitar outras rotas além de 1 MB.
- **NFR-FOTO-3** O app DEVE funcionar sem rolagem horizontal de 360 px a 1280 px e atender WCAG 2.2 AA nas telas desta mudança (texto alternativo da foto, controles com rótulo).
- **NFR-FOTO-4** O sistema DEVE aplicar toda validação no backend, com teste de API (Art. 6).

## Dados pessoais (LGPD)
| Dado | Finalidade | Base legal | Retenção | Quem acessa |
|---|---|---|---|---|
| Foto do manuscrito | prova de que a pessoa escreveu à mão | execução do serviço | enquanto a conta existir | o autor (e o parceiro só nas condições da 005) |
| Foto de perfil | a outra pessoa reconhecer quem é | execução do serviço | até trocar, remover ou a conta acabar | a própria e a outra pessoa do grupo |
| Metadados da imagem (EXIF, GPS) | nenhuma | — | não são guardados: descartados na recodificação | ninguém |

## Casos de abuso
- **ABU-5** SE alguém enviar um arquivo que parece imagem mas carrega outro conteúdo (HTML, script, arquivo compactado, imagem enorme que estoura a memória), ENTÃO O sistema DEVE recusá-lo ou neutralizá-lo na recodificação sem executar nada.
- **ABU-6** SE alguém trocar o identificador da foto na URL, ENTÃO O sistema DEVE responder 404 para qualquer foto que a pessoa não possa ver.
- **ABU-7** SE alguém enviar fotos em volume para encher o disco, ENTÃO O sistema DEVE recusar acima de 20 envios por hora por pessoa e de 30 fotos avulsas por pessoa.

## Propriedades de corretude
- **PROP-5** Para qualquer arquivo enviado, o que é guardado é sempre uma imagem decodificável do tipo declarado pelo servidor, sem metadados, ou nada é guardado.

## Fora de escopo
- Ver foto do manuscrito do parceiro (contrato da 005); anexar foto a registro (005); recorte, rotação e edição de imagem; miniaturas; HEIC; vídeo; armazenamento em SILO.
- Antivírus: a recodificação é a defesa; não há varredura por antivírus.

## Esclarecimentos
Todas as perguntas em aberto do mapa para `fotos` foram decididas pelo agente (ver Suposições): onde guardar, tipos e tamanho, visibilidade em
`partial` (foto nunca vai) e quantidade por registro (1 a 3).
