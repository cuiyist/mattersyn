import test from 'node:test';
import assert from 'node:assert/strict';
import {resolveMaterialEntry} from '../static/material-aliases.mjs';

test('historical shell-count material URLs resolve to phase-level hubs', () => {
  const materials = [
    {id: 'cdse-cds-34750d', alias_ids: ['cdse-cds4-cb849e']},
    {id: 'cdse-cds-zns-759020', alias_ids: [
      'cdse-cds-zns-cds-zns-d8a75e', 'cdse-cds2-zns-cds-9787c9',
      'cdse-cds2-zns2-eeb2d8', 'cdse-cds3-zns-30e81b',
    ]},
    {id: 'cdse-zns-cds-1d40df', alias_ids: ['cdse-zns-cds3-07193f']},
    {id: 'cdse-zns-2ec1c2', alias_ids: ['cdse-zns4-d24dd9']},
  ];
  for (const material of materials) {
    assert.equal(resolveMaterialEntry(materials, material.id), material);
    for (const oldId of material.alias_ids) {
      assert.equal(resolveMaterialEntry(materials, oldId), material, oldId);
    }
  }
  assert.equal(resolveMaterialEntry(materials, 'missing-material'), undefined);
});
