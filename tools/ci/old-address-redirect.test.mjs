import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const index = fs.readFileSync(new URL('../old-address-redirect/index.html', import.meta.url), 'utf8');
const notFound = fs.readFileSync(new URL('../old-address-redirect/404.html', import.meta.url), 'utf8');
function run(html, address) {
  const url = new URL(address), replacements = [], link = {href: null};
  const location = {origin: url.origin, pathname: url.pathname, search: url.search, hash: url.hash,
    replace(value) { replacements.push(value); }};
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  assert.equal(scripts.length, 1);
  vm.runInNewContext(scripts[0][1], {URL, window: {location}, document: {getElementById(id) {
    assert.equal(id, 'destination'); return link;
  }}});
  return {replacements, link};
}

test('both prepared pages use identical redirect logic and the new brand', () => {
  assert.equal(index, notFound);
  assert.match(index, /<title>NanoXtalSyn/);
  assert.match(index, /Nanocrystal synthesis atlas/);
  assert.doesNotMatch(index, /http-equiv=["']refresh/i);
});
test('old root and slashless project root redirect once to the exact new base', () => {
  for (const html of [index, notFound]) for (const old of ['https://cuiyist.github.io/mattersyn-site/', 'https://cuiyist.github.io/mattersyn-site']) {
    const result = run(html, old);
    assert.deepEqual(result.replacements, ['https://cuiyist.github.io/nanoxtalsyn-site/']);
    assert.equal(result.link.href, result.replacements[0]);
  }
});
test('material method query and anchor remain unchanged', () => {
  for (const html of [index, notFound]) {
    const result = run(html, 'https://cuiyist.github.io/mattersyn-site/material.html?id=gaas-889234&method=record%2Fone#intuition');
    assert.deepEqual(result.replacements, ['https://cuiyist.github.io/nanoxtalsyn-site/material.html?id=gaas-889234&method=record%2Fone#intuition']);
  }
});
test('unknown deep paths encoded bytes repeated queries and anchors are preserved', () => {
  const suffix = 'records/a%2Fb-%E2%82%AC.html?view=data&x=1&x=2+3#part%20one';
  for (const html of [index, notFound]) assert.deepEqual(run(html, 'https://cuiyist.github.io/mattersyn-site/' + suffix).replacements,
    ['https://cuiyist.github.io/nanoxtalsyn-site/' + suffix]);
});
test('query parameters cannot choose a different redirect origin', () => {
  const result = run(notFound, 'https://cuiyist.github.io/mattersyn-site/missing.html?url=https%3A%2F%2Fevil.test%2F#https://evil.test/');
  const target = new URL(result.replacements[0]);
  assert.equal(target.origin, 'https://cuiyist.github.io');
  assert.equal(target.pathname, '/nanoxtalsyn-site/missing.html');
  assert.equal(target.search, '?url=https%3A%2F%2Fevil.test%2F');
  assert.equal(target.hash, '#https://evil.test/');
});
test('other origins similar prefixes and the new address never redirect or loop', () => {
  for (const address of ['https://other.test/mattersyn-site/a.html', 'https://cuiyist.github.io/mattersyn-site-other/a.html',
    'https://cuiyist.github.io/nanoxtalsyn-site/a.html']) {
    assert.deepEqual(run(notFound, address).replacements, []);
  }
});
