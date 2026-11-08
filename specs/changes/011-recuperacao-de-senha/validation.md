---
id: 011-recuperacao-de-senha
status: rascunho
veredito: parcial
---

# Validação — Recuperação de senha por e-mail

Evidência do que foi **realmente executado** (2026-11-08). Implementado e testado localmente, e o caminho principal foi percorrido **no navegador local com o e-mail impresso no console da API**. **Nenhum e-mail real foi enviado**,
nada no ar, sem auditoria independente, sem arquivamento, nada commitado. **Falta uma ação do dono antes do deploy: escolher o provedor de e-mail e criar as variáveis e o segredo (T-3.1).**

## Ambiente
- Backend: PostgreSQL 17 descartável (porta 55433), `uv run pytest`; 42 testes em `test_recuperacao.py` mais `test_infra_recuperacao.py`; migração `acesso 0005_pedido_recuperacao`; sem dependência nova (SMTP e gerador de token são do Django); `ruff` e `makemigrations --check` limpos.
- Front: contêiner do SDK; `flutter analyze` limpo; 328 testes Flutter no total (os da 011 em `recuperacao_test.dart`, mais 3 telas na acessibilidade e 3 testes do cliente HTTP).
- Navegador: pilha local (`docker compose up`), backend de e-mail do console (sem `EMAIL_HOST`): pedir, ler o link nos logs da API, abrir, trocar, entrar.

## Critério → evidência
| ID | Como foi provado | Resultado |
|---|---|---|
| REQ-20.1 | `test_req_20_1_*`: 202 e um e-mail em português para o endereço da conta, com o link `…/#/redefinir/<uid>/<token>` (o token confere no gerador do Django); maiúsculas e espaços acham a conta; navegador local: o e-mail apareceu no console | ✔ teste e navegador local |
| REQ-20.2, ABU-24, PROP-14 | `test_req_20_2_*` (10 entradas ruins: sem conta, vazio, só espaços, sem `@`, 300 caracteres, número, nulo, lista, corpo que não é objeto, conta inativa) e `test_abu_24_prop_14_*` (status, corpo e cabeçalhos relevantes idênticos para 7 entradas); nada é gravado nem enviado | ✔ em teste |
| REQ-20.3, ABU-27 | `test_req_20_3_*`, `test_abu_27_*`: `X-Forwarded-Host` e campos `base`/`url` do atacante não entram no link (que começa na `APP_URL_BASE`); `Host` falso é recusado antes de qualquer envio; o token vai no fragmento | ✔ em teste |
| REQ-20.4 | `test_req_20_4_*`: SMTP de 2 s; a resposta volta em menos de 1 s e o e-mail chega depois | ✔ em teste |
| REQ-20.5, CTL-93 | `test_req_20_5_*`: SMTP quebrado; mesma resposta; o log tem só o tipo do erro (nem e-mail, nem token, nem corpo, nem a senha do SMTP) | ✔ em teste |
| REQ-20.6, ABU-25 | `test_req_20_6_*`: no 4º pedido em 1 hora nada é enviado e a resposta é igual; 61 minutos depois volta a enviar; o limite é por conta; pedidos com mais de 24 h são apagados (também pelo comando `limpar_pedidos`, chamado no deploy) | ✔ em teste |
| REQ-21.1 | `test_req_21_1_*`: 204; a senha nova vale e a antiga não; a sessão aberta antes morre (e sai do banco); **sem login automático** (nem cookie de sessão); navegador local: entrar com a senha nova → 200 | ✔ teste e navegador local |
| REQ-21.2, ABU-26 | `test_req_21_2_*`: 9 tipos de link ruim (vazio, token adulterado, `uid` de outra pessoa, `uid` malformado, inexistente, nulo…) → 400 com **o mesmo corpo**; vencido depois de 1 h (59 min ainda vale, 61 min não: relógio injetado no gerador de tokens); conta desativada; corpo mal formado nunca dá 500 | ✔ em teste |
| REQ-21.3 | `test_req_21_3_*`: 4 senhas fracas → 422 sem alterar, e **o mesmo token continua valendo** (depois uma senha boa funciona) | ✔ em teste |
| REQ-21.4 | `test_req_21_4_*`: e-mail "sua senha foi alterada" para a conta, sem a senha nova no texto; navegador local: o aviso saiu no console | ✔ teste e navegador local |
| REQ-21.5 | `test_req_21_2_21_5_*`, `test_req_21_5_*`: o token não vale duas vezes; trocar a senha por outro caminho e entrar de novo também o matam; navegador local: reuso → 400 "Link inválido ou vencido." | ✔ teste e navegador local |
| REQ-22.1, REQ-22.2 | `recuperacao_test.dart`: "Esqueci minha senha" leva ao pedido; **a mesma confirmação** para qualquer e-mail (o app nunca diz se existe); e-mail vazio não vai ao servidor; sem conexão e 429 têm mensagem própria; toque duplo manda um pedido só | ✔ em teste |
| REQ-22.3, REQ-22.4, REQ-22.5 | `recuperacao_test.dart`: tela de senha nova com confirmação e mostrar/ocultar; sucesso leva a Entrar com "Senha trocada. Entre com a nova senha." e **não entra sozinho**; senhas diferentes não vão ao servidor; 400 mostra "Link inválido ou vencido." com "Pedir outro link"; sem token (página recarregada) mostra o mesmo; 422 aparece em português e a tela continua para tentar de novo; toque duplo manda um pedido só | ✔ em teste |
| REQ-22.6 | `recuperacao_test.dart` (a rota vira `/redefinir`, sem token; o token não aparece em nenhum texto) e `sem_persistencia_test.dart` (nada de armazenamento do navegador em `lib/`); **navegador local: a barra de endereço passou de `#/redefinir/MQ/<token>` para `#/redefinir`** | ✔ teste e navegador local |
| NFR-REC-1 | `test_nfr_rec_1_*`, `test_ctl_94_*`, `test_nfr_rec_1_a_senha_do_smtp_*`: a senha do SMTP não está em resposta nem em log nem em arquivo versionado; é segredo do GitHub (sem variable com esse nome) | ✔ em teste |
| NFR-REC-2 | todas as regras de entrada têm teste de API (422 ou 400) | ✔ |
| NFR-REC-3 | `acessibilidade_test.dart`: pedido, senha nova e link inválido nos dois temas e em 360 e 1280 px | ✔ em teste |
| NFR-REC-4 | `test_nfr_rec_4_*`: o compose exige as seis variáveis na API; o `deploy.sh` confere as seis **antes de parar a API** e nunca imprime o valor; os testes do deploy existentes foram atualizados | ✔ em teste |
| CTL-91 | `test_ctl_91_*`: as duas rotas exigem o token de CSRF; `test_prop_1_*`: entram na lista de rotas públicas e só elas | ✔ em teste |
| CTL-92 | `test_ctl_92_*`: as duas rotas entram nos roteadores do balde de 5 por minuto (domínio e IP) | ✔ em teste. **Medido no ar: não** |

## Mutação (roteiro em `backend/apps/acesso/tests/mutacao_recuperacao.py`)
16 mutantes: limite de 3 e janela de 1 h, minúsculas, espaços e formato do e-mail, conta inativa, link com query em vez de fragmento, envio síncrono, log com a mensagem do erro, token não conferido, `uid` de conta inativa, senha sem política, sem e-mail de aviso, sessões não encerradas, pedidos antigos não apagados, resposta diferente.
Na primeira rodada **5 não morreram**: "sessões não encerradas" (as sessões já caíam pelo hash da senha; acrescentei a conferência de que saem do banco) e "pedidos antigos" (o roteiro estava desatualizado; corrigido) **morreram**;
"minúsculas" e "validar formato do e-mail" são **equivalentes** (a busca é `iexact` e um e-mail ruim nunca acha conta), e o mutante "responde diferente" **não era real** (retirados). **13 mortos + 2 equivalentes (+1 retirado).**

## Não provado (e o que depende do dono)
- **Nenhum e-mail real:** SMTP de verdade, entrega, spam e SPF/DKIM do provedor só no ar, com o provedor escolhido (T-5.2).
- **T-3.1 é do dono:** escolher o provedor, criar a conta de envio e, no GitHub (ambiente `production`), as variables `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `DEFAULT_FROM_EMAIL`, `APP_URL_BASE` (ex.: `https://jpsys.duckdns.org/entrelinhas/`) e o segredo `EMAIL_HOST_PASSWORD`. **Sem elas o próximo deploy aborta** (de propósito, antes de parar a API); a senha nunca vai ao chat.
- O limite do Traefik (429 no 6º pedido em 1 minuto) **não foi medido**. Desvio do `design.md`: em vez de roteadores novos `entrelinhas-recuperar-*`, as duas rotas entraram nos roteadores `entrelinhas-entrar-*` (um balde por origem, compartilhado com o login: mais rígido, e um limitador por roteador não divide contador).
- O tempo de resposta com e sem conta **não foi medido**: o envio sai do pedido (testado) e a conta inexistente faz o mesmo número de consultas, mas diferenças de microssegundos não foram medidas.
- O botão Voltar do navegador depois de abrir o link não foi inspecionado (o token saiu da barra de endereço, mas o histórico do navegador pode ainda guardar o endereço original).
- Quem controla o e-mail controla a conta (risco aceito no design; sessões encerradas e o aviso por e-mail mitigam). Sem auditoria independente (foco pedido: enumeração, Host, token, tempo).

## Veredito
**Parcial.** Implementado e testado; o caminho principal funcionou no navegador local; faltam as credenciais de e-mail do dono, o deploy e a prova com e-mail real, a auditoria independente e o arquivamento em `acesso-espaco.md`.
