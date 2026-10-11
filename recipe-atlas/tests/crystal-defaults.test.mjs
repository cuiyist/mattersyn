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


const titleEntries=[entry('title-core','CdSe','Bulk wurtzite CdSe reference · core comparison',186),
 entry('title-shell','CdS','Bulk wurtzite CdS reference · shell comparison',186)];
const titleRecord=(status,architecture)=>({...rec(null),quality:{review_status:status},
 material:{formula:'CdSe/CdS',components:['CdSe','CdS'],...(architecture?{architecture}:{})}});

test('machine-extracted composite defaults never inherit unspecified core/shell title roles',()=>{
 for(const architecture of [undefined,'unresolved','single_material','core_shell','core_multishell','composite']){
  const refs=defaultCrystalReferences(titleEntries,titleRecord('source_extracted',architecture));
  assert.deepEqual(refs.map(ref=>ref.name),['Bulk wurtzite CdSe reference','Bulk wurtzite CdS reference']);
  assert.ok(refs.every(ref=>ref.roleByRecord['synthetic-r']==='Component reference'));
 }
});

test('audited, pending and unspecified-status defaults retain original library titles',()=>{
 for(const status of ['reviewed','independently_audited','pending',undefined])
  assert.deepEqual(defaultCrystalReferences(titleEntries,titleRecord(status,'unresolved')).map(ref=>ref.name),titleEntries.map(ref=>ref.name));
});

test('single-composition defaults keep their title scope unchanged',()=>{
 const r={...titleRecord('source_extracted','single_material'),material:{formula:'CdSe'}};
 assert.equal(defaultCrystalReferences(titleEntries,r)[0].name,titleEntries[0].name);
});

test('neutral-title cleanup removes only a trailing role comparison suffix',()=>{
 const record=titleRecord('source_extracted');
 for(const separator of [' · ',': ',' — ',' – ',' - ',' ']){
  const refs=defaultCrystalReferences([entry('suffix','CdSe','CdSe independent bulk reference'+separator+'core comparison',186)],record);
  assert.equal(refs[0].name,'CdSe independent bulk reference');
 }
 const unchanged='CdSe core comparison bulk reference';
 assert.equal(defaultCrystalReferences([entry('middle','CdSe',unchanged,186)],record)[0].name,unchanged);
});

test('neutral titles retain phase filtering, cell/provenance pins and immutable inputs',()=>{
 const refs=titleEntries.map(ref=>Object.freeze({...ref,cifSha256:'synthetic-cif-pin',sourceUrl:'https://example.invalid/bulk',
  modelSha256:'synthetic-model-pin',description:'Independent bulk reference provenance.'}));
 const record=Object.freeze({...titleRecord('source_extracted','core_shell'),products:[{phase:{value:'wurtzite'}}]});
 const before=JSON.stringify({refs,record});
 const result=defaultCrystalReferences(refs,record);
 assert.equal(result.length,2);
 for(let i=0;i<result.length;i++)for(const field of ['id','formula','spaceGroupNumber','cifPath','cifSha256','modelPath','modelSha256','sourceUrl'])
  assert.equal(result[i][field],refs[i][field],field);
 assert.ok(result.every(ref=>ref.phaseScope.includes('paper reports this phase')&&ref.phaseScope.includes('not a structure')));
 assert.equal(JSON.stringify({refs,record}),before);
 assert.deepEqual(defaultCrystalReferences(refs,{...record,products:[{phase:{value:'unknown phase'}}]}),[]);
});

test('ordinary core/shell library assets remain unchanged for their audited contexts',()=>{
 const entries=titleEntries.map(ref=>({...ref,record_ids:['audited-core-shell'],componentRole:ref.formula==='CdSe'?'Core reference':'Shell reference'}));
 const before=JSON.stringify(entries);
 const result=defaultCrystalReferences(entries,titleRecord('reviewed','core_shell'));
 assert.deepEqual(result.map(ref=>ref.name),entries.map(ref=>ref.name));
 assert.equal(JSON.stringify(entries),before);
});
