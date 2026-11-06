# ADR-0010 — Confiança no operador; sem criptografia por usuário no MVP

- Status: aceito (usuário, 2026-11-05: "Ir para a 005" ao pedir a implementação; proposto pelo agente por delegação)
- Data: 2026-11-05
- Mudança de origem: 005-registros-backend

## Contexto
O mapa perguntou se `private` vale também contra quem administra a plataforma (uma das duas pessoas), o que exigiria criptografia por usuário.

## Decisão
No MVP, `private` vale **na API e na interface**. Quem opera a VPS e o banco é de confiança do grupo (são as duas pessoas, ou uma delas). Medidas que reduzem a exposição sem criptografia:
1. o Django Admin não registra `Registro` nem `Foto` (não há tela que mostre texto ou imagem);
2. logs nunca levam texto, trecho nem nome de foto;
3. backups ficam em `~/backups` com modo 600.

## Consequências
- Uma pessoa que administra o banco consegue ler texto `private` com SQL. O README e a tela de perfil devem dizer isso com franqueza (texto simples).
- Esquecer a senha não destrói o diário (com criptografia por usuário, destruiria; a recuperação de senha chega só na 011).

## Alternativas descartadas
- **Criptografia por usuário (chave derivada da senha):** protege contra o operador, mas a recuperação de senha apagaria o diário e os destaques entre as duas pessoas exigiriam troca de chaves.
- **Criptografia com chave do servidor:** quem lê o banco costuma ter também a chave; custo sem proteção real contra o operador.

## Revisão
Revisitar se o produto sair do círculo de duas pessoas de confiança (ex.: grupos maiores, usuários desconhecidos).
