// [010] REQ-19.6, REQ-19.7, NFR-LEMB-2: o service worker em Node, com os eventos `push` e `notificationclick` simulados.
// Roda com `node --test frontend/test_js` (sem dependências).
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const codigo = readFileSync(new URL('../web/sw.js', import.meta.url), 'utf8');

/** Carrega o sw.js num contexto isolado e devolve o que ele registrou e o que foi chamado. */
function carregar({ janelas = [], escopo = 'https://exemplo.org/entrelinhas/' } = {}) {
  const ouvintes = {};
  const mostradas = [];
  const abertas = [];
  const focadas = [];
  const navegadas = [];
  const proibidos = [];
  const proibido = (nome) => () => proibidos.push(nome);
  const self = {
    addEventListener: (tipo, fn) => (ouvintes[tipo] = fn),
    skipWaiting: async () => {},
    registration: {
      scope: escopo,
      showNotification: async (titulo, opcoes) => mostradas.push({ titulo, ...opcoes }),
    },
    clients: {
      claim: async () => {},
      matchAll: async () =>
        janelas.map((url) => ({
          url,
          focus: async () => {
            focadas.push(url);
            return { navigate: async (destino) => navegadas.push(destino) };
          },
        })),
      openWindow: async (url) => abertas.push(url),
    },
    // Qualquer uso destes no service worker é um defeito (NFR-LEMB-2).
    fetch: proibido('fetch'),
    caches: { open: proibido('caches'), match: proibido('caches') },
    indexedDB: { open: proibido('indexedDB') },
  };
  vm.runInNewContext(codigo, { self, console });
  return { ouvintes, mostradas, abertas, focadas, navegadas, proibidos };
}

/** Evento com `waitUntil` que guarda a promessa para o teste esperar. */
function evento(extra = {}) {
  const pendentes = [];
  return { ...extra, waitUntil: (p) => pendentes.push(p), pronto: () => Promise.all(pendentes) };
}

test('REQ-19.6: o push mostra a notificação genérica com a rota Hoje', async () => {
  const sw = carregar();
  const e = evento({ data: { json: () => ({ titulo: 'Entrelinhas', corpo: 'Hora de escrever o seu dia.', url: '#/hoje' }) } });

  sw.ouvintes.push(e);
  await e.pronto();

  assert.equal(sw.mostradas.length, 1);
  assert.equal(sw.mostradas[0].titulo, 'Entrelinhas');
  assert.equal(sw.mostradas[0].body, 'Hora de escrever o seu dia.');
  assert.equal(sw.mostradas[0].data.url, '#/hoje');
});

test('REQ-19.6: carga ausente, inválida ou estranha cai no texto genérico', async () => {
  for (const data of [null, { json: () => { throw new Error('json ruim'); } }, { json: () => ({ titulo: 5, corpo: {}, url: 'https://evil.example.com' }) }]) {
    const sw = carregar();
    const e = evento({ data });

    sw.ouvintes.push(e);
    await e.pronto();

    assert.equal(sw.mostradas[0].titulo, 'Entrelinhas');
    assert.equal(sw.mostradas[0].body, 'Hora de escrever o seu dia.');
    assert.equal(sw.mostradas[0].data.url, '#/hoje', 'um endereço de fora nunca vira destino do toque');
  }
});

test('REQ-19.7: tocar na notificação abre o app na tela Hoje quando não há janela', async () => {
  const sw = carregar();
  let fechou = false;
  const e = evento({ notification: { close: () => (fechou = true), data: { url: '#/hoje' } } });

  sw.ouvintes.notificationclick(e);
  await e.pronto();

  assert.equal(fechou, true);
  assert.deepEqual(sw.abertas, ['https://exemplo.org/entrelinhas/#/hoje']);
});

test('REQ-19.7: com o app já aberto, foca a janela e leva a Hoje (sem abrir outra)', async () => {
  const sw = carregar({ janelas: ['https://outro.org/', 'https://exemplo.org/entrelinhas/#/diario'] });
  const e = evento({ notification: { close() {}, data: { url: '#/hoje' } } });

  sw.ouvintes.notificationclick(e);
  await e.pronto();

  assert.deepEqual(sw.focadas, ['https://exemplo.org/entrelinhas/#/diario']);
  assert.deepEqual(sw.navegadas, ['https://exemplo.org/entrelinhas/#/hoje']);
  assert.deepEqual(sw.abertas, []);
});

test('NFR-LEMB-2: o service worker nunca toca em rede, cache nem banco', async () => {
  const sw = carregar({ janelas: ['https://exemplo.org/entrelinhas/'] });
  for (const tipo of ['install', 'activate']) {
    const e = evento();
    sw.ouvintes[tipo](e);
    await e.pronto();
  }
  const p = evento({ data: { json: () => ({}) } });
  sw.ouvintes.push(p);
  await p.pronto();
  const c = evento({ notification: { close() {}, data: {} } });
  sw.ouvintes.notificationclick(c);
  await c.pronto();

  assert.deepEqual(sw.proibidos, []);
});

test('NFR-LEMB-2: só escuta install, activate, push e notificationclick', () => {
  const sw = carregar();

  assert.deepEqual(Object.keys(sw.ouvintes).sort(), ['activate', 'install', 'notificationclick', 'push']);
});
