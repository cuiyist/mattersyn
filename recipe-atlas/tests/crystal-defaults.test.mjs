import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {defaultCrystalReferences,reportedPhases,compositionParts,dopedHost} from '../static/crystal-defaults.mjs';
const entry=(id,formula,name,sg)=>({id,formula,name,spaceGroupNumber:sg,cifPath:id+'.cif',modelPath:'models/'+id+'.json',referenceOnly:true});
const ordered=entry('ordered','CoPt3','CoPt3 ordered L12 bulk reference',221);
const fcc=entry('fcc','CoPt3','CoPt3 disordered fcc bulk reference',225);
const rec=(phase,target)=>({record_id:'synthetic-r',lineage:{source_group:'synthetic'},material:{formula:'CoPt3'},products:[{phase:{value:phase}}],intended_target:{phase:{value:target}}});

const mapiId='ch3nh3pbi3-tetragonal-perovskite-cod-2107954';
const crystalRoot=new URL('../static/assets/crystal-references/',import.meta.url);
const crystalLibrary=JSON.parse(readFileSync(new URL('registry.json',crystalRoot),'utf8'));
const mapi=crystalLibrary.entries.find(ref=>ref.id===mapiId);
const mapiRecord=phase=>({...rec(phase),material:{formula:'CH3NH3PbI3'}});

test('ambient methylammonium lead iodide retains exact COD assets and statistical reference exclusions',()=>{
 assert.ok(mapi);
 assert.equal(mapi.spaceGroupNumber,97);
 for(const [key,value] of Object.entries({referenceOnly:true,trainingEligible:false,measuredSampleStructure:false,
   defaultForSample:false,partialOccupancy:true,displayPolicy:'independent_reference',referenceType:'literature_bulk_reference'}))
  assert.equal(mapi[key],value,key);
 assert.deepEqual(mapi.record_ids,[]);assert.deepEqual(mapi.material_ids,[]);
 assert.match(mapi.scope,/293 K/);assert.match(mapi.scope,/not a structure of any synthesized sample/);
 const cif=readFileSync(new URL(mapi.cifPath,crystalRoot));
 const modelBytes=readFileSync(new URL(mapi.modelPath,crystalRoot));
 assert.equal(createHash('sha256').update(cif).digest('hex'),mapi.cifSha256);
 assert.equal(mapi.cifSha256,'2c71e90403f878f3b8775c84490aee4e7d285b3f8d97d29c05b9725a9b1dc654');
 assert.match(cif.toString('utf8'),/_cell_measurement_temperature\s+293\b/);
 assert.equal(createHash('sha256').update(modelBytes).digest('hex'),mapi.modelSha256);
 const model=JSON.parse(modelBytes),counts={};
 for(const atom of model.atoms)for(const component of atom.components||[{element:atom.element,occupancy:atom.occupancy??1}])
  counts[component.element]=(counts[component.element]||0)+component.occupancy;
 assert.deepEqual(counts,{Pb:4,I:12,C:4,N:4,H:24});
 assert.equal(model.training_eligible,false);assert.equal(model.measured_sample_structure,false);
 assert.ok(model.renderingNotes.some(note=>note.includes('statistical crystallographic populations')));
});

test('the ambient MAPI cell matches its composition and tetragonal or unspecified phase only',()=>{
 const before=JSON.stringify(mapi);
 for(const phase of [null,'tetragonal','tetragonal perovskite'])
  assert.deepEqual(defaultCrystalReferences([mapi],mapiRecord(phase)).map(ref=>ref.id),[mapiId]);
 for(const phase of ['cubic','wurtzite','monoclinic','unknown phase'])
  assert.deepEqual(defaultCrystalReferences([mapi],mapiRecord(phase)),[],phase);
 assert.deepEqual(defaultCrystalReferences([mapi],{...mapiRecord(null),material:{formula:'CH3NH3PbBr3'}}),[]);
 assert.equal(JSON.stringify(mapi),before);
});

test('the MAPI addition preserves other formulas and the six existing matching contexts',()=>{
 const old=crystalLibrary.entries.filter(ref=>ref.id!==mapiId);
 const selected=(library,record)=>{
  const explicit=library.filter(ref=>(ref.record_ids||[]).includes(record.record_id));
  return explicit.length?explicit:defaultCrystalReferences(library,record,crystalLibrary.excluded_materials);
 };
 const required=new Set(['heo2017-pbs-perovskite-acsami7b12046-r19-perovskite-model-1',
  'heo2017-pbs-perovskite-acsami7b12046-r20-perovskite-model-2p5',
  'heo2017-pbs-perovskite-acsami7b12046-r21-perovskite-model-5',
  'naphade2016-acsami-5b10208-mapbi3-based-2-d-perovskite-nanosheets-1',
  'zhang2017-acs-chemmater-7b01100-ch3nh3pbi3-quantum-dots-qds-with-tunable-1',
  'zhao2017-acsnano-7b00404-mapbi3-nanocrystal-thin-film-with-fpmai-1']);
 const records=new URL('../data/records/',import.meta.url),found=new Set();
 for(const name of readdirSync(records).filter(name=>name.endsWith('.json'))){
  const record=JSON.parse(readFileSync(new URL(name,records),'utf8')),before=JSON.stringify(record);
  const prior=selected(old,record).map(ref=>ref.id),after=selected(crystalLibrary.entries,record).map(ref=>ref.id);
  if(record.material?.formula!=='CH3NH3PbI3')assert.deepEqual(after,prior,name);
  if(after.includes(mapiId)){assert.equal(record.material.formula,'CH3NH3PbI3');found.add(record.record_id);}
  assert.equal(JSON.stringify(record),before);
 }
 assert.deepEqual([...found].sort(),[...required].sort());
});
test('unreported phase permits all bulk composition forms with explicit scope',()=>{
 const refs=defaultCrystalReferences([ordered,fcc],rec(null));assert.equal(refs.length,2);assert.ok(refs.every(e=>e.scope.includes('The record does not assign a crystal phase; available bulk references are shown for comparison.')&&e.scope.includes('not a structure')));
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

test('audited, pending and unspecified-status defaults use the same neutral component titles',()=>{
 for(const status of ['reviewed','independently_audited','pending',undefined])
  assert.deepEqual(defaultCrystalReferences(titleEntries,titleRecord(status,'unresolved')).map(ref=>ref.name),['Bulk wurtzite CdSe reference','Bulk wurtzite CdS reference']);
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

test('ordinary core/shell references use neutral titles while their audited library data stays unchanged',()=>{
 const entries=titleEntries.map(ref=>({...ref,record_ids:['audited-core-shell'],componentRole:ref.formula==='CdSe'?'Core reference':'Shell reference'}));
 const before=JSON.stringify(entries);
 const result=defaultCrystalReferences(entries,titleRecord('reviewed','core_shell'));
 assert.deepEqual(result.map(ref=>ref.name),['Bulk wurtzite CdSe reference','Bulk wurtzite CdS reference']);
 assert.equal(JSON.stringify(entries),before);
});


test('generic crystallinity is unspecified phase for bulk composition references',()=>{
 for(const phase of ['crystal','crystalline','Crystal','  CRYSTALLINE  ']){
  const r=rec(phase,phase),before=JSON.stringify(r),refs=defaultCrystalReferences([ordered,fcc],r);
  assert.deepEqual(reportedPhases(r),[]);
  assert.deepEqual(refs.map(ref=>ref.id),['ordered','fcc']);
  assert.ok(refs.every(ref=>ref.defaultByComposition&&ref.scope.includes('not a structure of the synthesized sample')));
  assert.equal(JSON.stringify(r),before);
 }
});
test('generic product crystallinity retains the existing intended-phase fallback',()=>{
 const r=rec('crystal','fcc');
 assert.deepEqual(reportedPhases(r),['fcc']);
 assert.deepEqual(defaultCrystalReferences([ordered,fcc],r).map(ref=>ref.id),['fcc']);
});
test('a specific product phase still overrides generic or differing target phases',()=>{
 const r=rec('fcc','crystal');r.products.push({phase:{value:'crystalline'}});
 assert.deepEqual(reportedPhases(r),['fcc']);
 assert.deepEqual(defaultCrystalReferences([ordered,fcc],r).map(ref=>ref.id),['fcc']);
});
test('unknown named phases containing crystal words remain suppressed',()=>{
 for(const phase of ['unknown crystal phase','icosahedral crystal','quasicrystal','amorphous','crystal-like phase'])
  assert.deepEqual(defaultCrystalReferences([ordered,fcc],rec(phase)),[],phase);
});
test('crystal words do not remove recognized phase qualifiers',()=>{
 for(const phase of ['fcc crystal','crystalline cubic fcc'])
  assert.deepEqual(defaultCrystalReferences([ordered,fcc],rec(phase)).map(ref=>ref.id),['fcc']);
});
test('InAs generic crystal receives only an independent matching composition reference',()=>{
 const inas=entry('inas-bulk','InAs','InAs zinc blende reference',216);
 const r={...rec('crystal','crystal'),quality:{review_status:'source_extracted'},material:{formula:'InAs',components:['InAs'],architecture:'heterostructure'}};
 const refs=defaultCrystalReferences([inas,entry('other','AlAs','AlAs reference',216)],r);
 assert.deepEqual(refs.map(ref=>ref.id),['inas-bulk']);
 assert.equal(refs[0].displayPolicy,'independent_reference');
 assert.equal(refs[0].roleByRecord[r.record_id],'Reference by composition');
 assert.ok(refs[0].scope.includes('not a structure of the synthesized sample'));
});
test('alloy and core/shell names show their end-member cells as component references',()=>{
 const library=[entry('cdse-zb','CdSe','CdSe zinc blende bulk reference',216),entry('cds-zb','CdS','CdS zinc blende bulk reference',216),entry('zns-zb','ZnS','ZnS zinc blende bulk reference',216)];
 const r=rec('zinc blende');r.material={formula:'CdSeS',components:['CdSeS']};
 assert.deepEqual(compositionParts(r,library),['CdSe','CdS']);
 const refs=defaultCrystalReferences(library,r);
 assert.deepEqual(refs.map(e=>e.id),['cdse-zb','cds-zb']);
 assert.ok(refs.every(e=>e.roleByRecord[r.record_id]==='Component reference'&&/not a structure of the synthesized sample/.test(e.scope)));
 const shell=rec(null);shell.material={formula:'CdSe-ZnS',components:['CdSe-ZnS']};
 assert.deepEqual(defaultCrystalReferences(library,shell).map(e=>e.id),['cdse-zb','zns-zb']);
});
test('an alloy whose end members are not all in the library shows no cell',()=>{
 const library=[entry('inas-zb','InAs','InAs zinc blende bulk reference',216)];
 const r=rec(null);r.material={formula:'InGaAs',components:['InGaAs']};
 assert.deepEqual(compositionParts(r,library),[]);
 assert.deepEqual(defaultCrystalReferences(library,r),[]);
 assert.deepEqual(compositionParts(r),['InAs','GaAs'],'without a library the end members are listed');
});
test('mineral and polytype phase names select the matching new bulk references',()=>{
 const lib=[entry('hgte','HgTe','HgTe zinc blende (coloradoite) bulk reference',216),entry('mgo','MgO','MgO rock salt (periclase) bulk reference',225),
  entry('sic3c','SiC','SiC 3C (zinc blende-type, β-SiC) bulk reference',216),entry('sic6h','SiC','SiC 6H hexagonal (α-SiC) bulk reference',186),
  entry('ws2','WS2','WS2 2H hexagonal bulk reference',194),entry('hap','Ca10(PO4)6(OH)2','Ca10(PO4)6(OH)2 hexagonal hydroxyapatite bulk reference',176)];
 const pick=(formula,phase)=>{const r=rec(phase);r.material={formula};return defaultCrystalReferences(lib,r).map(e=>e.id);};
 assert.deepEqual(pick('HgTe','coloradoite'),['hgte']);
 assert.deepEqual(pick('HgTe','zinc blend'),['hgte']);
 assert.deepEqual(pick('MgO','periclase'),['mgo']);
 assert.deepEqual(pick('SiC','3C-SiC'),['sic3c']);
 assert.deepEqual(pick('SiC','cubic (3C-SiC)'),['sic3c']);
 assert.deepEqual(pick('SiC',null),['sic3c','sic6h']);
 assert.deepEqual(pick('WS2','2H-phase'),['ws2']);
 assert.deepEqual(pick('Ca10(PO4)6(OH)2','hydroxyapatite'),['hap']);
 assert.deepEqual(pick('Ca10(PO4)6(OH)2','anatase and rutile'),[]);
});
test('second-batch phase names and end members select their references',()=>{
 const lib=[entry('czts','Cu2ZnSnS4','Cu2ZnSnS4 tetragonal kesterite bulk reference',121),entry('pbmo','PbMoO4','PbMoO4 tetragonal scheelite-type (wulfenite) bulk reference',88),
  entry('cos2','CoS2','CoS2 cubic pyrite-type (cattierite) bulk reference',205),entry('bto','Bi4Ti3O12','Bi4Ti3O12 orthorhombic Aurivillius-type layered perovskite (average cell) bulk reference',69),
  entry('bwo','Bi2WO6','Bi2WO6 orthorhombic (russellite) bulk reference',29),entry('yag','Y3Al5O12','Y3Al5O12 cubic garnet (YAG) bulk reference',230),
  entry('inp','InP','InP zinc blende bulk reference',216),entry('gap','GaP','GaP zinc blende bulk reference',216)];
 const pick=(formula,phase,components)=>{const r=rec(phase);r.material={formula,...(components?{components}:{})};return defaultCrystalReferences(lib,r).map(e=>e.id);};
 assert.deepEqual(pick('Cu2ZnSnS4','kesterite CZTS'),['czts']);
 assert.deepEqual(pick('PbMoO4','tetragonal scheelite-type'),['pbmo']);
 assert.deepEqual(pick('CoS2','cubic pyrite'),['cos2']);
 assert.deepEqual(pick('Bi4Ti3O12','Aurivillius-type layered perovskite'),['bto']);
 assert.deepEqual(pick('Bi2WO6','P21ab'),['bwo']);
 assert.deepEqual(pick('Y3Al5O12:Ce','Crystalline NC YAG:Ce by HRTEM'),['yag']);
 assert.deepEqual(pick('InGaP','cubic',['InGaP']),['inp','gap']);
});
test('doped formulas compare with the host in either order, never with the dopant',()=>{
 assert.equal(dopedHost('InP:Zn'),'InP');
 assert.equal(dopedHost('Mn:ZnO'),'ZnO');
 assert.equal(dopedHost('Cu:Al2O3'),'Al2O3');
 assert.equal(dopedHost('Co2+:CdS'),'CdS');
 assert.equal(dopedHost('La2(MoO4)3:Yb,Er'),'La2(MoO4)3');
 assert.equal(dopedHost('Si:Er'),'Si');
 assert.equal(dopedHost('Ge:H'),'Ge');
 const lib=[entry('cu','Cu','Cu face-centered cubic bulk reference',225),entry('al2o3','Al2O3','Al2O3 corundum bulk reference',167)];
 const r=rec(null);r.material={formula:'Cu:Al2O3',components:['Cu:Al2O3']};
 assert.deepEqual(defaultCrystalReferences(lib,r).map(e=>e.id),['al2o3']);
});
test('third-batch alloy names and phase words select their references',()=>{
 const lib=[entry('inas','InAs','InAs zinc blende bulk reference',216),entry('gaas','GaAs','GaAs zinc blende bulk reference',216),
  entry('si','Si','Si diamond bulk reference',227),entry('ge','Ge','Ge diamond bulk reference',227),
  entry('mn3o4','Mn3O4','Mn3O4 tetragonal spinel (hausmannite) bulk reference',141),entry('se','Se','Se trigonal (helical chains) bulk reference',152),
  entry('kcl','KCl','KCl rock salt (sylvite) bulk reference',225)];
 const pick=(formula,phase)=>{const r=rec(phase);r.material={formula,components:[formula]};return defaultCrystalReferences(lib,r).map(e=>e.id);};
 assert.deepEqual(pick('In0.41Ga0.59As',null),['inas','gaas']);
 assert.deepEqual(pick('SiGe',null),['si','ge']);
 assert.deepEqual(pick('Mn3O4','hausmannite'),['mn3o4']);
 assert.deepEqual(pick('KCl','sylvite'),['kcl']);
 assert.deepEqual(pick('Se','trigonal'),['se']);
 assert.deepEqual(pick('Se','Rhombohedral (R-Se)'),[]);
});
test('fourth-batch names select their references',()=>{
 const lib=[entry('nayf4','NaYF4','NaYF4 cubic α (disordered fluorite-type) bulk reference',225),entry('ag3aus2','Ag3AuS2','Ag3AuS2 cubic (uytenbogaardtite) bulk reference',213),
  entry('inp','InP','InP zinc blende bulk reference',216),entry('gap','GaP','GaP zinc blende bulk reference',216)];
 const pick=(formula,phase)=>{const r=rec(phase);r.material={formula,components:[formula]};return defaultCrystalReferences(lib,r).map(e=>e.id);};
 assert.deepEqual(pick('NaYF4:Yb3+','cubic'),['nayf4']);
 assert.deepEqual(pick('NaYF4:20','hexagonal'),[]);
 assert.deepEqual(pick('Ag3AuS2','uytenbogaardtite'),['ag3aus2']);
 assert.deepEqual(pick('In1−xGaxP','zinc blende'),['inp','gap']);
});
