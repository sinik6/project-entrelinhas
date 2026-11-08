---
id: 010-lembretes
status: rascunho
veredito: parcial
---

# Validação — Lembretes (PWA e Web Push)

Evidência do que foi **realmente executado** (2026-11-08). Implementado e testado localmente. **Nenhum push real foi enviado ou recebido**, o service worker **não foi registrado em nenhum navegador**,
nada no ar, sem auditoria independente, sem arquivamento, nada commitado. **Falta uma ação do dono antes do deploy: criar os segredos das chaves VAPID (T-5.1).**

## Ambiente
- Backend: PostgreSQL 17 descartável, `uv run pytest`; 86 testes de `apps/lembretes` mais os de infra; dependência nova `pywebpush 2.5.0` (com `py-vapid`, `http-ece`, `requests`, travada no `uv.lock`); `ruff` e `makemigrations --check` limpos.
- Front: contêiner do SDK; `flutter analyze` limpo; testes de widget da seção do lembrete com um Web Push falso.
- JS: `node --test frontend/test_js/sw.test.mjs` (Node 24), chamado também pelo pytest (pulado se não houver Node).
- Navegador (pilha local com a chave pública no `.env` ignorado pelo git): a seção apareceu em Perfil, leu a permissão real do navegador (`denied`, no navegador do aplicativo) e mostrou "Bloqueado pelo navegador…"; `sw.js`, `manifest.json` e os ícones saíram do nginx com os cabeçalhos certos.

## Critério → evidência
| ID | Como foi provado | Resultado |
|---|---|---|
| REQ-18.1 | `test_req_18_1_*`: manifesto com nome, ícones de 192 e 512 (comuns e mascaráveis, arquivos PNG nos tamanhos declarados), cores, `start_url` e escopo relativos (`./`), idioma; **ícones próprios** gerados (fundo teal do tema, página com linhas); o `index.html` liga o manifesto | ✔ em teste |
| REQ-18.2 | `lembrete_test.dart`: ligar pede a permissão, assina com a chave do servidor e envia `{endpoint, p256dh, auth}`; `test_req_18_2_*`: só a chave pública sai pela API | ✔ em teste. **A assinatura real no navegador não foi feita** |
| REQ-18.3 | `test_req_18_3_*`: 201, repetir não duplica, assinatura de outra conta passa para a atual | ✔ em teste |
| REQ-18.4, ABU-21, CTL-81 | `test_req_18_4_*`: **25 endereços recusados** (`http`, `localhost`, IPs v4 e v6, `169.254.169.254`, host interno, `fcm.googleapis.com.evil.com`, `evilpush.apple.com`, usuário e senha na URL, porta 8443, ponto final, esquemas estranhos, 3000 caracteres…) e 5 serviços aceitos; com **toda chamada de rede proibida no teste** (nenhum endereço é chamado); chaves inválidas (base64, tamanhos, `0x04`); a lista vale também na hora de enviar (banco adulterado) | ✔ em teste |
| REQ-18.5 | `test_req_18_5_*`: a 6ª → 409; reenviar uma existente continua valendo | ✔ em teste |
| REQ-18.6, ABU-22 | `test_req_18_6_*`, `test_abu_22_*`: remover a do aparelho; de outra pessoa ou inexistente → 404 sem mudar nada; `lembrete_test.dart`: desligar cancela no navegador e remove do servidor | ✔ em teste |
| REQ-18.7, REQ-18.8 | `lembrete_test.dart`: bloqueado (pedido negado e já negado ao abrir), iPhone fora da tela inicial (instruções "Compartilhar → Adicionar à Tela de Início"), sem suporte, sem chaves (503 esconde a seção), ligado ao abrir se já há assinatura; falhas em português sem detalhe técnico; assinatura órfã é desfeita se o servidor recusar; toque duplo assina uma vez | ✔ em teste |
| REQ-19.1, 19.5 | `test_req_19_1_*`, `test_req_19_5_*`: 21h29min59s não envia; 21h30 envia; 22h59min59s envia atrasado; 23h00 pula; cada aparelho recebe; sem grupo não recebe | ✔ em teste |
| REQ-19.2 | `test_req_19_2_*`: quem já entregou não recebe (nem é marcado); registro de outro dia não conta; 21h30 de SP no instante UTC do dia seguinte | ✔ em teste |
| REQ-19.3, ABU-23 | `test_req_19_3_*` e `test_abu_23_*`: uma vez por pessoa por dia; **6 execuções simultâneas em threads reais**, cada pessoa recebe 1; o processo "morre" no meio do envio e, ao voltar, ninguém repete (a marca é gravada antes) | ✔ em teste (PostgreSQL real) |
| REQ-19.4, REQ-19.8 | `test_req_19_4_*`, `test_req_19_8_*`, `test_req_19_4_19_8_*`: 404 e 410 removem; 429, 400 e 500 viram falha sem apagar; falha de rede e exceção inesperada não param os outros; falha não repete no dia; **log sem endereço** | ✔ em teste |
| REQ-19.6, CTL-85 | `test_req_19_6_*`: a carga é exatamente `{titulo, corpo genérico, url "#/hoje"}`, sem nome, e-mail nem texto de registro | ✔ em teste |
| REQ-19.7 | `sw.test.mjs`: tocar na notificação abre `…/#/hoje`, ou foca a janela do app e leva a Hoje; um endereço de fora na carga nunca vira destino | ✔ em teste Node. **Não visto num navegador de verdade** |
| NFR-LEMB-1, CTL-82 | `test_nfr_lemb_1_*` e `test_ctl_82_84_*`: a chave privada não está em resposta nem em log (nem na mensagem de erro da biblioteca); só o serviço do disparador a recebe (a API só a pública); o app não a conhece | ✔ em teste |
| NFR-LEMB-2 | `test_nfr_lemb_2_*` + `sw.test.mjs`: o `sw.js` não tem `fetch`, `caches`, `indexedDB` etc., e só escuta `install`, `activate`, `push` e `notificationclick`; o nginx serve com `no-cache` e `Service-Worker-Allowed: ./` | ✔ em teste; cabeçalhos conferidos no nginx local |
| NFR-LEMB-3, CTL-83 | `test_ctl_83_*`: serviço `entrelinhas-lembretes` da mesma imagem, `command`, `restart`, `healthcheck` por batimento, sem porta e sem rótulos do Traefik; `test_comando_rodar_lembretes_*`: o batimento é atualizado | ✔ em teste. **O serviço subiu no compose local** (e o primeiro ciclo falhou antes da migração, como previsto; o laço continua) |
| CTL-84 | `test_ctl_84_*`: `deploy.sh` confere as três chaves **antes de parar a API** e nunca as imprime; o workflow as trata como segredos obrigatórios sem aspa nem quebra de linha; os testes do deploy existentes ganharam as variáveis | ✔ em teste |
| PROP-13 | `test_prop_13_*`: 60 cenários sorteados (pessoas, aparelhos, entregas, instantes dentro e fora da janela, virada do dia) comparados a um oráculo; a segunda execução envia vazio | ✔ (exemplos) |
| NFR-LEMB-4 | `acessibilidade_test.dart`: 3 estados da seção (desligado, bloqueado, iPhone) nos dois temas e em 360 e 1280 px | ✔ em teste |
| `gerar_vapid` | `test_gerar_vapid_*`: o par impresso assina de verdade (`py-vapid`) e a pública bate com a privada (87 caracteres); nada é gravado | ✔ em teste |

## Mutação (roteiro em `backend/apps/lembretes/tests/mutacao.py`)
23 mutantes (http aceito, IP, porta, credenciais na URL, sufixos, host que só termina igual, ponto final, limite de 5, tamanhos das chaves, remover sem dono, janela em 21h00 e 23h30 e inclusiva, quem entregou recebe, trava do dia, marca depois de enviar, assinatura morta não removida, sem grupo recebe, dia pelo UTC, 410, sem tempo limite, destino sem conferir). Na primeira rodada **5 sobreviveram**:
"sufixo sem ponto" e "quem já entregou recebe" ganharam teste (endereços `evilpush.apple.com` e a conferência de que quem entregou nem é marcado) e **morreram**; os outros 3 são **equivalentes** (as defesas se repetem: o IP e o ponto final já não passariam na lista de hosts; a exclusão dos já marcados é repetida pela marca única). **20 mortos + 3 equivalentes.**

## Não provado (e o que depende do dono)
- **Nenhum push real:** sem celular nem serviço de push, o ciclo cifra-envia-recebe só foi provado com o `webpush` falso. A chave VAPID real, o aviso às 21h30, o toque abrindo Hoje no Android e no iPhone instalado: **só no ar**, em aparelhos reais (T-5.2).
- **O service worker nunca foi registrado:** o navegador do aplicativo recusa até um arquivo vazio ("erro ao buscar o script"); o `sw.js` foi provado só em Node.
- `PushApi` web (`dart:js_interop`) compilou, leu a permissão real e o suporte, mas **assinar e cancelar não foram executados**.
- **T-5.1 é do dono:** gerar as chaves (`manage.py gerar_vapid`) e criar no GitHub, ambiente `production`, `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY` e `VAPID_ASSUNTO` (um `mailto:`). **Sem elas o próximo deploy aborta** (de propósito, antes de parar a API); a chave privada nunca vai ao chat.
- `pip-audit` não foi rodado; sem auditoria independente (foco pedido: SSRF, segredo, duplicidade).
- Um dia pulado (servidor fora das 21h30 às 23h) não é recuperado por design; o horário é fixo em São Paulo.

## Veredito
**Parcial.** Implementado e testado em tudo o que dá para testar sem aparelho real; faltam as chaves do dono, o deploy e a prova em celulares reais, a auditoria independente e o arquivamento em `lembretes.md`.
