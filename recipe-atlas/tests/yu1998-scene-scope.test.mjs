import test from 'node:test';
import assert from 'node:assert/strict';
import {buildYu1998Scene} from '../static/yu1998-protocol.mjs';

const scene=(id,stage)=>buildYu1998Scene({id:`${id}-${stage}`},{record_id:id,lineage:{source_group:'yu1998cde'}});
test('general procedure alone states the source vessel capacity',()=>{
 assert.match(scene('yu1998-cde-general-140c-12h','load').caption,/100 mL/);
 for(const id of ['yu1998-cds-py-160c-12h','yu1998-cdse-dien-180c-12h']){
  assert.doesNotMatch(scene(id,'load').caption,/100 mL|80%/);
  assert.match(scene(id,'hold').caption,/capacity, filling fraction, pressure and closure remain unreported/);
 }
});
test('vessel liquid levels are explicitly conceptual for all vessel stages',()=>{
 for(const id of ['yu1998-cde-general-140c-12h','yu1998-cds-py-160c-12h'])
  for(const stage of ['load','hold','cool'])assert.match(scene(id,stage).caption,/conceptual and not to scale/);
});
