import assert from 'node:assert/strict';
import {test} from 'node:test';
import {selectTargets} from './chemical-reference-check.mjs';
const KIM='kim2013-pbs-ionic-liquid-am3029766-pbs-qd';
function fixture(){
 const entries=[['oa','Oleic acid'],['ode','1-Octadecene'],['ethanol','Ethanol'],['acetone','Acetone'],['computed','Computed name'],['ion','Salt'],['ambient','InAs'],['flat','TiO2'],['hmds','Hexamethyldisilathiane'],['octane','Octane'],['hx-wash','Hexane'],['hx-tem','Hexane'],['pbo','Lead oxide']].map(([id,name])=>({id,name}));
 const references={oa:{route:'molecule_reference',reason:'identical_CID'},ode:{route:'molecule_reference',reason:'unique_exact_compound_name'},ethanol:{route:'molecule_reference',reason:'identical_CID'},acetone:{route:'molecule_reference',reason:'identical_CID'},computed:{route:'molecule_reference',reason:'validated_connectivity_computed_conformer'},ion:{route:'independent_component_references'},ambient:{route:'ambient_crystal_reference'},flat:{route:'flat',whyNo3d:'The form is unreported.'},hmds:{route:'molecule_reference',reason:'unique_exact_compound_name'},octane:{route:'molecule_reference',reason:'owner_fixed_named_identity'},'hx-wash':{route:'molecule_reference',reason:'owner_fixed_named_identity'},'hx-tem':{route:'molecule_reference',reason:'owner_fixed_named_identity'},pbo:{route:'flat',whyNo3d:'The form is unreported.'}};
 const bindings={recordBindings:{[KIM]:{m1:'oa',m2:'ode',m3:'ethanol',m4:'acetone',m9:'hmds',m10:'octane','chemical--hexane-wash':'hx-wash','chemical--hexane-tem':'hx-tem',m11:'pbo'},other:{m5:'computed',m6:'ion',m7:'ambient',m8:'flat'}}};
 return [{entries},bindings,{entries:references}];
}
test('all four actual Kim2013 identities plus five route classes must be covered',()=>{
 const targets=selectTargets(...fixture());assert.equal(targets.length,12);assert.deepEqual(targets.filter(t=>['kim2013-oa','kim2013-ode','kim2013-ethanol','kim2013-acetone'].includes(t.id)).map(t=>t.name),['Oleic acid','1-Octadecene','Ethanol','Acetone']);
 const covered=new Set(targets.flatMap(t=>[t.id,...t.covers||[]]));for(const id of ['reused-molecule','computed-molecule','independent-ions','ambient-cell','flat-reason'])assert(covered.has(id));
});
test('missing route or actual precursor binding fails instead of silently skipping',()=>{
 let args=fixture();delete args[2].entries.computed;assert.throws(()=>selectTargets(...args),/computed-molecule/);
 args=fixture();assert.throws(()=>selectTargets(...args,(rid,mid)=>mid!=='m5'),/computed-molecule/);
});
test('Kim ambiguity or missing exact named identity fails',()=>{
 const [registry,bindings,overlay]=fixture();registry.entries.push({id:'oa-ambiguous',name:'Oleic acid'});bindings.recordBindings[KIM].m9='oa-ambiguous';assert.throws(()=>selectTargets(registry,bindings,overlay),/exactly one/);
});
