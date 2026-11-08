---
id: 008-destaques-front
status: em-revisao
---

# Tarefas — Destaques e comentários (telas)

Legenda: `[P]` paralelizável · teste antes da implementação · cada tarefa com `Req:` e `Verifica:` · tamanho XS/S/M/L.
Estratégia de fatiamento: pintura e posições primeiro (onde o erro machuca), depois a folha.
Os testes levam `[008]` no nome. Depende da 006 e da 007 no ar. Comandos Flutter: no contêiner do SDK.

## Onda 1 — Testes primeiro (devem falhar)
- [x] T-1.1 Testes da pintura: spans por destaque, cor e sublinhado, sobreposição, contraste, PROP-10 (M)
  - Req: REQ-15.3, REQ-15.7, PROP-10, CTL-62
  - Arquivos: `frontend/test/destaque_pintura_test.dart`
  - Verifica: `flutter test test/destaque_pintura_test.dart` → vermelho
- [x] T-1.2 [P] Testes da seleção: menu de ações, posições em pontos de código, ajuste a grafemas, seleção fora do visível, registro `private` sem ação (M)
  - Req: REQ-15.1, REQ-15.2, REQ-15.9, CTL-62
  - Arquivos: `frontend/test/destaque_selecao_test.dart`
  - Verifica: vermelho
- [x] T-1.3 [P] Testes da folha: abrir, comentar, editar, apagar comentário, apagar destaque com confirmação, erros, marcação literal, duplo toque (L)
  - Req: REQ-15.4, REQ-15.5, REQ-15.6, REQ-15.8, ABU-17, ABU-18, NFR-DESTF-2, CTL-61, CTL-63
  - Arquivos: `frontend/test/destaque_folha_test.dart`, `frontend/test/suporte/api_falsa.dart`
  - Verifica: vermelho
- [x] T-1.4 [P] Testes de acessibilidade e teclado das telas novas (S)
  - Req: NFR-DESTF-1, NFR-DESTF-3
  - Arquivos: `frontend/test/acessibilidade_test.dart`
  - Verifica: vermelho

## Onda 2 — Implementação
- [x] T-2.1 Cliente da API e modelos da 007 (S)
  - Req: REQ-15.2, REQ-15.5
  - Arquivos: `frontend/lib/shared/api/`, `frontend/lib/features/destaques/modelos.dart`
  - Verifica: testes do cliente HTTP verdes (estende `api_http_test.dart`)
  - Depende: T-1.3
- [x] T-2.2 Leitor com `SelectableText.rich`: spans por destaque, cor, sublinhado, sobreposição, toque (M)
  - Req: REQ-15.3, REQ-15.7, PROP-10
  - Arquivos: `frontend/lib/features/destaques/leitor.dart`
  - Verifica: `destaque_pintura_test.dart` verde
  - Depende: T-1.1, T-2.1
- [x] T-2.3 Menu de seleção e criação do destaque (M)
  - Req: REQ-15.1, REQ-15.2, REQ-15.9, ABU-18
  - Arquivos: `frontend/lib/features/destaques/selecao.dart`
  - Verifica: `destaque_selecao_test.dart` verde
  - Depende: T-1.2, T-2.2
- [x] T-2.4 Folha de comentários: conversa, comentar, editar, apagar, seletor de sobrepostos, confirmação (L)
  - Req: REQ-15.4 a 15.8, ABU-17, ABU-18
  - Arquivos: `frontend/lib/features/destaques/folha.dart`
  - Verifica: `destaque_folha_test.dart` verde
  - Depende: T-1.3, T-2.2
- [x] T-2.5 Integrar o leitor à tela de registro (006) e acessibilidade (rótulos, teclado) (M)
  - Req: NFR-DESTF-1, NFR-DESTF-3
  - Arquivos: `frontend/lib/features/diario/`
  - Verifica: `acessibilidade_test.dart` e testes da 006 verdes; `flutter analyze` limpo
  - Depende: T-1.4, T-2.3, T-2.4

## Onda 3 — Navegador e fechamento
- [ ] T-3.1 Teste no navegador, em contêiner, com dois participantes: destacar com emoji, comentar, apagar; Chrome desktop e celular emulado; 360 e 1280 px, claro e escuro (M)
  - Req: REQ-15.2, REQ-15.4, NFR-DESTF-1
  - Verifica: roteiro verde; evidência no `validation.md`
  - Depende: T-2.5
- [ ] T-3.2 Deploy (o dono manda "Commit e push") e conferência no ar (S)
  - Req: REQ-15.2, REQ-15.4
  - Verifica: evidência no `validation.md`
- [ ] T-3.3 Rastreabilidade, `sdd_lint`, auditoria independente por subagente, `validation.md`, arquivamento em `destaques.md` (M)
  - Req: PROP-10, NFR-DESTF-1
  - Verifica: lint sem erro; auditoria sem achado grave aberto
