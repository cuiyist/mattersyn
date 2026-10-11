import test from 'node:test';
import assert from 'node:assert/strict';
import {defaultCrystalReferences,reportedPhases} from '../static/crystal-defaults.mjs';
const entry=(id,formula,name,sg)=>({id,formula,name,spaceGroupNumber:sg,cifPath:id+'.cif',modelPath:'models/'+id+'.json',referenceOnly:true});
const ordered=entry('ordered','CoPt3','CoPt3 ordered L12 bulk reference',221);
const fcc=entry('fcc','CoPt3','CoPt3 disordered fcc bulk reference',225);
const rec=(phase,target)=>({record_id:'synthetic-r',lineage:{source_group:'synthetic'},material:{formula:'CoPt3'},products:[{phase:{value:phase}}],intended_target:{phase:{value:target}}});
test('unreported phase permits all bulk composition forms with explicit scope',()=>{
 const refs=defaultCrystalReferences([ordered,fcc],rec(null));assert.equal(refs.length,2);assert.ok(refs.every(e=>e.scope.includes('paper does not state the phase')&&e.scope.includes('not a structure')));
});
test('unrecognized reported phase cannot silently become no reported phase',()=>{assert.deepEqual(defaultCrystalReferences([ordered,fcc],rec('unrecognized phase')),[])});
test('qualifiers are conjunctive: cubic plus fcc does not admit ordered primitive cubic',()=>{assert.deepEqual(defaultCrystalReferences([ordered,fcc],rec('chemically disordered cubic fcc')).map(e=>e.id),['fcc'])});
test('reported fcc with no matching library cell remains blank',()=>{assert.deepEqual(defaultCrystalReferences([ordered],rec('chemically disordered cubic fcc')),[])});
test('reported product phase takes precedence over a different intended target',()=>{const r=rec('fcc','ordered cubic');assert.deepEqual(reportedPhases(r),['fcc']);assert.deepEqual(defaultCrystalReferences([ordered,fcc],r).map(e=>e.id),['fcc'])});
test('unreported product uses stated intended target conservatively',()=>{assert.deepEqual(defaultCrystalReferences([ordered,fcc],rec(null,'fcc')).map(e=>e.id),['fcc'])});
test('composites without a phase retain parallel component bulk references',()=>{const r=rec(null);r.material={formula:'CdSe/CdS',components:['CdSe','CdS']};const refs=defaultCrystalReferences([entry('core','CdSe','CdSe wurtzite',186),entry('shell','CdS','CdS wurtzite',186)],r);assert.equal(refs.length,2);assert.ok(refs.every(e=>e.roleByRecord['synthetic-r']==='Component reference'))});
test('explicitly excluded compositions and custom viewers remain unchanged',()=>{assert.deepEqual(defaultCrystalReferences([ordered],rec(null),[{formula:'CoPt3'}]),[]);const r=rec(null);r.lineage.source_group='heo2003';assert.deepEqual(defaultCrystalReferences([ordered],r),[])});

const zirconia=(phase,target)=>({...rec(phase,target),material:{formula:'ZrO2'}});
const tetragonal=entry('zro2-tetragonal','ZrO2','ZrO2 tetragonal bulk reference',137);
const monoclinic=entry('zro2-monoclinic','ZrO2','ZrO2 monoclinic bulk reference',14);
test('separately stated mixed product phases show their bulk cells in parallel',()=>{
 const refs=defaultCrystalReferences([tetragonal,monoclinic],zirconia('97% tetragonal; 3% monoclinic (XRD peak-area fractions)'));
 assert.deepEqual(refs.map(e=>e.id),['zro2-tetragonal','zro2-monoclinic']);
 assert.ok(refs.every(e=>e.scope.includes('not a structure of the synthesized sample')));
});
test('a missing cell for one stated mixture component does not hide the available component',()=>{
 assert.deepEqual(defaultCrystalReferences([tetragonal],zirconia('97% tetragonal; 3% monoclinic')).map(e=>e.id),['zro2-tetragonal']);
});
test('mixed-phase components preserve their own conjunctive qualifiers',()=>{
 const tet=entry('copt-tetragonal','CoPt3','CoPt3 tetragonal bulk reference',123);
 assert.deepEqual(defaultCrystalReferences([ordered,fcc,tet],rec('90% chemically disordered cubic fcc; 10% tetragonal')).map(e=>e.id),['fcc','copt-tetragonal']);
});
test('a semicolon between compatible qualifiers does not admit ordered primitive cubic',()=>{
 assert.deepEqual(defaultCrystalReferences([ordered],rec('fcc; cubic')),[]);
 assert.deepEqual(defaultCrystalReferences([ordered,fcc],rec('fcc; cubic')).map(e=>e.id),['fcc']);
});
test('unknown nonempty mixture components never expand to all bulk cells',()=>{
 assert.deepEqual(defaultCrystalReferences([tetragonal,monoclinic],zirconia('unknown alpha phase; unknown beta phase')),[]);
});
test('reported mixture still takes precedence over an intended different phase',()=>{
 assert.deepEqual(defaultCrystalReferences([tetragonal,monoclinic],zirconia('97% tetragonal; 3% monoclinic','cubic')).map(e=>e.id),['zro2-tetragonal','zro2-monoclinic']);
});
