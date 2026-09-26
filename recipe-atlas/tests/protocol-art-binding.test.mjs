import test from 'node:test';
import assert from 'node:assert/strict';
import {selectProtocolArt} from '../static/protocol-art-binding.mjs';
const record={record_id:'example-route'},operation={id:'sealed-hold'};
const item={operation_id:'sealed-hold',asset_path:'assets/protocol/example.svg',asset_sha256:'a'.repeat(64),caption:'Illustrative equipment only.',source_locator:'Main p. 1'};
const binding={record_id:'example-route',bindings:[item]};
test('matches the exact record and operation without adding conditions',()=>{
 assert.equal(selectProtocolArt(binding,record,operation),item);
 assert.equal(selectProtocolArt(binding,{record_id:'other'},operation),null);
 assert.equal(selectProtocolArt(binding,record,{id:'other'}),null);
 assert.equal(selectProtocolArt(null,record,operation),null);
});
test('rejects ambiguous, unsupported or unattributed artwork',()=>{
 assert.equal(selectProtocolArt({...binding,bindings:[item,item]},record,operation),null);
 for(const invalid of [{asset_path:'https://example.com/image.svg'},{asset_path:'assets/protocol/../image.svg'},{asset_sha256:'x'},{source_locator:''},{caption:''}])
  assert.equal(selectProtocolArt({...binding,bindings:[{...item,...invalid}]},record,operation),null);
});
