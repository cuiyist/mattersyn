import assert from 'node:assert/strict';
import {test} from 'node:test';
import {createGenericThermalScene, genericThermalSceneKind} from '../static/generic-thermal-scenes.mjs';

function fakeElement() {
  return {
    className: '',
    dataset: {},
    attributes: {},
    children: [],
    setAttribute(name, value) { this.attributes[name] = value; },
    getAttribute(name) { return this.attributes[name] ?? null; },
    append(child) { this.children.push(child); }
  };
}

function withFakeDocument(run) {
  const previous = globalThis.document;
  globalThis.document = {
    createElement: () => fakeElement(),
    createElementNS: () => ({attributes: {}, setAttribute(name, value) { this.attributes[name] = value; }})
  };
  try { run(); } finally { globalThis.document = previous; }
}

test('generic reflux rendering is a condenser scene and labels cooling-water ports only when reported', () => {
  const operation = {action: 'reflux', label: 'Reflux with water-cooled condenser', description: 'Return solvent to the vessel.'};
  assert.equal(genericThermalSceneKind(operation, 'heat'), 'reflux');
  withFakeDocument(() => {
    const scene = createGenericThermalScene(operation, 'heat');
    assert.equal(scene.dataset.scene, 'reflux');
    assert.match(scene.attributes['aria-label'], /condenser/);
    assert.match(scene.children[0].innerHTML, /water in/);
    assert.match(scene.children[0].innerHTML, /water out/);
  });
});

test('generic calcination rendering uses a distinct qualified thermal-treatment scene', () => {
  const operation = {action: 'calcination', label: 'Calcine at 400 °C'};
  assert.equal(genericThermalSceneKind(operation, 'heat'), 'thermal-treatment');
  withFakeDocument(() => {
    const scene = createGenericThermalScene(operation, 'heat');
    assert.equal(scene.dataset.scene, 'thermal-treatment');
    assert.match(scene.attributes['aria-label'], /[Ii]llustrative/);
    assert.match(scene.children[0].innerHTML, /HEATING ZONE/);
    assert.doesNotMatch(scene.children[0].innerHTML, /CONDENSER/);
  });
});

test('nonthermal and preparatory actions keep existing scene selection', () => {
  assert.equal(genericThermalSceneKind({action: 'dissolve', label: 'Prepare a feed for later reflux'}, 'prepare'), null);
  assert.equal(genericThermalSceneKind({action: 'wash'}, 'separate'), null);
});

