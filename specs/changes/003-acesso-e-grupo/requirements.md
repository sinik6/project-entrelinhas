---
id: 003-acesso-e-grupo
titulo: Contas, perfil, grupo de escrita, convite e casca do front em Flutter
status: em-revisao
tamanho: P2
risco: alto
capacidades: [acesso-espaco]
autor: jpjamal
criado: 2026-11-03
---

# Requisitos — Contas, perfil, grupo de escrita, convite e casca do front

## Contexto e objetivo
Hoje só existe o Admin do Django. Esta mudança faz as duas pessoas poderem **entrar no app, ter um perfil com cor, formar um
grupo de escrita de até duas pessoas e convidar a segunda pessoa por um link**, tudo por telas no navegador (casca do front
em Flutter). É a primeira mudança que o dono usa de verdade, e a base para registros, destaques e calendário. Toca
autenticação, dado pessoal e convite (risco alto).

## Suposições
| Suposição | Status |
|---|---|
| Front em **Flutter web como PWA**, com o SDK em contêiner e o build servido por nginx atrás do Traefik, como no `analista-b3`; substitui o Next.js do ADR-0001 (o ADR novo nasce no design) | confirmada (usuário, 2026-11-03) |
| O front começa já nesta mudança, só com as telas deste escopo (entrar, criar conta pelo convite, perfil, grupo e convidar) | confirmada (usuário, 2026-11-03) |
| Entrada por **e-mail e senha** | confirmada (usuário, 2026-11-03) |
| A conta do administrador inicial vira a conta do dono no app: ela cria o grupo e convida a outra pessoa | confirmada (usuário, 2026-11-03) |
| Cor do perfil **livre** (`#RRGGBB`) | confirmada (usuário, 2026-11-03) |
| Recuperação de senha **por e-mail** é uma mudança própria depois (precisa de serviço de e-mail); até lá o administrador redefine a senha pelo Admin e a pessoa troca a senha logada | confirmada (usuário, 2026-11-03) |
| Mesmo com cor livre, o sistema recusa cor ilegível (contraste menor que 3 para 1 com o fundo claro ou com o escuro) e cor igual ou indistinguível da outra pessoa do grupo | confirmada (usuário, 2026-11-03) |
| Uma pessoa pertence a no máximo **um** grupo | confirmada (usuário, 2026-11-03) |
| O convite vale **7 dias**, é de uso único, e cada grupo tem no máximo um convite pendente (gerar outro invalida o anterior) | confirmada (usuário, 2026-11-03) |
| Sair do grupo e remover membro **não existem** no MVP; o administrador resolve pelo Admin | confirmada (usuário, 2026-11-03) |
| A **foto de perfil** entra com a mudança de fotos (004), porque o armazenamento privado ainda não existe | confirmada (usuário, 2026-11-03) (a visão pedia foto opcional no perfil) |
| O fuso é `America/Sao_Paulo` para todos; fuso por pessoa vai com calendário e lembretes | confirmada (usuário, 2026-11-03) |
| A outra pessoa do grupo vê meu **nome e minha cor**, nunca meu e-mail | confirmada (usuário, 2026-11-03) |
| O modelo de dados chama a unidade de **grupo**, com tipo (`escrita`) e limite de membros (2), para grupos de estudo e leitura caberem depois | confirmada (usuário, 2026-11-03) |

## Métricas de sucesso
- O dono e a segunda pessoa entram no mesmo grupo em menos de 5 minutos, só com o navegador.
- Nenhuma resposta da API revela se um e-mail tem conta ou se um convite existe.

## Glossário
| Termo | Significado |
|---|---|
| Participante | pessoa com conta no app (não confundir com a conta de administrador do Admin; a do dono é a mesma) |
| Grupo de escrita | espaço de até 2 participantes que escrevem todos os dias |
| Convite | link com código de uso único que dá entrada em um grupo e cria a conta de quem o abre |
| Perfil | nome e cor do participante |
| Cor | marca `#RRGGBB` que identifica o participante em comentários e no calendário |

## Papéis e autorização
| Papel | Ação | Recurso | Permitido? | Condição |
|---|---|---|---|---|
| Anônimo | obter o token de proteção, entrar e aceitar convite | autenticação, convite | sim | só essas três rotas são públicas; o link do convite é aberto pelo próprio app, sem rota no servidor |
| Anônimo | qualquer outra rota | API | não | exige autenticação |
| Participante | ver e alterar o próprio perfil e a própria senha | perfil | sim | só o próprio |
| Participante | ver nome e cor da outra pessoa do grupo | grupo | sim | só do próprio grupo |
| Participante sem grupo | criar um grupo | grupo | sim | se ainda não pertencer a nenhum |
| Participante de um grupo | gerar convite | convite | sim | se o grupo tiver menos de 2 membros |
| Participante | ver grupo ou convite de outro grupo | grupo, convite | não | recurso de outro grupo responde 404 |
| Administrador | criar e redefinir contas, resolver saída de membro | Admin | sim | só pelo Admin |

## Histórias e critérios de aceite

### US-1 — Entrar e sair
**Como** participante, **quero** entrar com e-mail e senha e sair, **para** usar o app com segurança.

- **REQ-1.1** QUANDO uma pessoa enviar e-mail e senha corretos, O sistema DEVE iniciar uma sessão e devolver o perfil dela.
- **REQ-1.2** SE o e-mail ou a senha estiverem errados, ENTÃO O sistema DEVE recusar com a mesma resposta nos dois casos.
- **REQ-1.3** QUANDO o participante pedir para sair, O sistema DEVE encerrar a sessão no servidor.
- **REQ-1.4** ENQUANTO a pessoa não estiver autenticada, O sistema DEVE recusar toda rota que não seja obter o token de proteção, entrar ou aceitar convite.

### US-2 — Criar o grupo
**Como** dono, **quero** criar o grupo de escrita, **para** convidar a outra pessoa.

- **REQ-2.1** QUANDO um participante sem grupo pedir um grupo novo, O sistema DEVE criar um grupo de escrita com ele como único membro.
- **REQ-2.2** SE o participante já pertencer a um grupo, ENTÃO O sistema DEVE recusar a criação de outro.
- **REQ-2.3** SE o grupo já tiver 2 membros, ENTÃO O sistema DEVE recusar a entrada de qualquer outra pessoa, por qualquer caminho.
- **REQ-2.4** SE o participante ainda não tiver nome e cor, ENTÃO O sistema DEVE recusar a criação do grupo.

### US-3 — Convidar a segunda pessoa
**Como** dono, **quero** gerar um link de convite, **para** a outra pessoa entrar no meu grupo.

- **REQ-3.1** QUANDO um membro de um grupo com vaga gerar um convite, O sistema DEVE devolver um link com código de uso único e a data de expiração.
- **REQ-3.2** QUANDO um membro gerar um novo convite, O sistema DEVE invalidar o convite pendente anterior do mesmo grupo.
- **REQ-3.3** QUANDO passarem 7 dias da criação de um convite, O sistema DEVE recusá-lo como expirado.
- **REQ-3.4** QUANDO uma pessoa sem conta abrir um convite válido e enviar nome, e-mail, senha e cor, O sistema DEVE criar a conta, o perfil e a entrada no grupo e invalidar o convite.
- **REQ-3.5** SE o convite estiver usado, expirado ou não existir, ENTÃO O sistema DEVE recusar com a mesma resposta nos três casos.
- **REQ-3.6** SE o e-mail enviado ao aceitar o convite já tiver conta, ENTÃO O sistema DEVE recusar com a mesma resposta de qualquer outra falha de convite.
- **REQ-3.7** SE o grupo já tiver 2 membros, ENTÃO O sistema DEVE recusar gerar convite.

### US-4 — Perfil e senha
**Como** participante, **quero** ajustar meu nome, minha cor e minha senha, **para** me identificar e manter a conta segura.

- **REQ-4.1** QUANDO o participante consultar o próprio perfil, O sistema DEVE devolver nome, e-mail, cor e o grupo a que pertence.
- **REQ-4.2** QUANDO o participante alterar nome ou cor, O sistema DEVE gravar e devolver o perfil atualizado.
- **REQ-4.3** SE a cor não estiver no formato `#RRGGBB`, ENTÃO O sistema DEVE recusar com erro de validação.
- **REQ-4.4** SE a cor tiver contraste menor que 3 para 1 com o fundo claro ou com o escuro, ENTÃO O sistema DEVE recusá-la.
- **REQ-4.5** SE a cor for igual à da outra pessoa do grupo ou indistinguível dela, ENTÃO O sistema DEVE recusá-la.
- **REQ-4.6** QUANDO o participante trocar a senha informando a senha atual e uma nova, O sistema DEVE gravar a nova e encerrar as outras sessões dele.
- **REQ-4.7** SE a senha atual estiver errada ou a nova não atender à política de senhas, ENTÃO O sistema DEVE recusar sem alterar a senha.
- **REQ-4.8** QUANDO o participante consultar o grupo, O sistema DEVE devolver nome e cor da outra pessoa, e nunca o e-mail dela.
- **REQ-4.9** QUANDO um participante que ainda não tem nome e cor (a conta do administrador, no primeiro acesso) consultar o perfil, O sistema DEVE indicar que o perfil está incompleto.

### US-5 — Telas (casca do front)
**Como** participante, **quero** telas simples no navegador, **para** usar tudo isso sem o Admin.

- **REQ-5.1** QUANDO uma pessoa sem sessão abrir o app, O app DEVE mostrar a tela de entrar.
- **REQ-5.2** QUANDO uma pessoa abrir um link de convite, O app DEVE mostrar a tela de criar conta com aquele convite.
- **REQ-5.3** QUANDO o participante entrar, O app DEVE mostrar o perfil, o grupo com nome e cor dos membros e, havendo vaga, o botão de convidar.
- **REQ-5.5** SE o perfil estiver incompleto, ENTÃO O app DEVE levar o participante à tela de perfil antes de qualquer outra.
- **REQ-5.4** SE o servidor recusar um pedido, ENTÃO O app DEVE mostrar a mensagem em português, sem detalhe técnico.

## Requisitos não funcionais
- **NFR-SEC-1** O sistema DEVE manter a sessão em cookie que o script do navegador não lê, enviado só por HTTPS em produção, com proteção contra pedidos forjados de outro site.
- **NFR-SEC-2** O sistema DEVE guardar o código do convite apenas como hash e gerá-lo com pelo menos 128 bits de aleatoriedade.
- **NFR-SEC-3** O sistema DEVE aplicar toda validação no backend, com teste de API, e não apenas na tela.
- **NFR-A11Y-1** O app DEVE atender WCAG 2.2 AA nas telas desta mudança, nos temas claro e escuro.
- **NFR-RESP-1** O app DEVE funcionar sem rolagem horizontal de 360 px a 1280 px de largura.

## Dados pessoais (LGPD)
| Dado | Finalidade | Base legal | Retenção | Quem acessa |
|---|---|---|---|---|
| Nome | identificar quem escreve e comenta | execução do serviço | enquanto a conta existir | o próprio e a outra pessoa do grupo |
| E-mail | entrar no app | execução do serviço | enquanto a conta existir | só o próprio (e o administrador, pelo Admin) |
| Cor | distinguir quem escreveu | execução do serviço | enquanto a conta existir | o próprio e a outra pessoa do grupo |
| Hash da senha | autenticar | execução do serviço | enquanto a conta existir | ninguém lê; só o sistema compara |
| Hash do convite | validar o convite | execução do serviço | até usar ou expirar | só o sistema |

## Casos de abuso
- **ABU-1** SE o mesmo endereço de origem errar a senha mais de 5 vezes seguidas, ENTÃO O sistema DEVE recusar as tentativas seguintes por um tempo.
- **ABU-2** SE alguém tentar descobrir se um e-mail tem conta, ENTÃO O sistema DEVE responder do mesmo jeito, com e sem conta, em entrar e em aceitar convite.
- **ABU-3** SE alguém tentar adivinhar ou reutilizar um código de convite, ENTÃO O sistema DEVE recusar sem revelar se o código existiu.
- **ABU-4** SE um site de terceiros induzir o navegador de um participante a enviar um pedido, ENTÃO O sistema DEVE recusá-lo.

## Fora de escopo
- Recuperação de senha por e-mail (mudança própria, depende de serviço de e-mail); até lá o administrador redefine pelo Admin.
- Foto de perfil (vai com a mudança de fotos), registros, destaques, calendário, lembretes e instalação como PWA.
- Sair do grupo, remover membro, mais de um grupo por pessoa, grupos de estudo e de leitura.
- Passkey, biometria e verificação em duas etapas.
- Cadastro aberto: contas só nascem por convite ou pelo Admin.

## Esclarecimentos
| Data | Pergunta | Resposta |
|---|---|---|
| 2026-11-03 | Como entra no app? | e-mail e senha (usuário) |
| 2026-11-03 | Como nasce a primeira conta? | a conta do administrador vira a do dono no app (usuário) |
| 2026-11-03 | Recuperação de senha | por e-mail, como mudança própria depois (usuário); até lá, redefinição pelo Admin (agente) |
| 2026-11-03 | Cor do perfil | livre, `#RRGGBB` (usuário); recusa de cor ilegível e repetida é suposição do agente |
| 2026-11-03 | Como a segunda pessoa entra? | link com código de uso único (usuário) |
| 2026-11-03 | Linguagem do front | Flutter web como PWA (usuário) |
| 2026-11-03 | As 6 suposições pendentes (cor com contraste e sem repetir, foto de perfil na 004, convite de 7 dias, sem sair do grupo, só nome e cor ao parceiro, uma pessoa um grupo e grupo com tipo e limite) | confirmadas (usuário, "Confirmo as 6") |
| 2026-11-03 | O design revelou que o convite abre no próprio app (fragmento da URL) e que a conta do dono nasce sem nome e cor | REQ-1.4 reescrito; REQ-2.4, REQ-4.9 e REQ-5.5 acrescentados (agente); confirmados pelo usuário no G2 ("Aprovo e aceito", 2026-11-03) |

## Checklist (G1)
- [x] Nenhum marcador de esclarecimento pendente
- [x] Todo critério em EARS, com ID e resultado observável
- [x] Erro, vazio, limite e permissões cobertos
- [x] Casos de abuso para fluxos sensíveis
- [x] Sem tecnologia citada nos critérios; sem termos vagos
- [x] Sem conflito com a constituição (Art. 13 respeitado: grupo de até 2, limite como atributo)
- [x] Suposições pendentes confirmadas pelo usuário (2026-11-03)
