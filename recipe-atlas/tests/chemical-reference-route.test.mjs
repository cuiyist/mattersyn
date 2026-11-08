import assert from 'node:assert/strict';
import {test} from 'node:test';
import {referenceRoute,viewerEntry,hasReference3d,chemicalButtonLabel,flatReferenceReason,chemicalDisplayCaption,chemicalModelCaption} from '../static/chemical-reference-route.mjs';
const sha='a'.repeat(64),entry=()=>({id:'source-name-card',name:'Printed compound',formula:'C2H6O',depictionKind:'formula',caption:'Original identity scope',svgPath:'svg/original.svg',assetHashes:{svgPath:'b'.repeat(64)}});
test('new molecular reference preserves original entry/classification and original scope',()=>{
 const e=entry();e.readerReference3d={route:'molecule_reference',model3dPath:'models/h-reader-abc-3d.json',model3dSha256:sha,referenceOnly:true,trainingEligible:false,caption:'Computed reference only'};
 const before=JSON.stringify(e),view=viewerEntry(e);assert.equal(JSON.stringify(e),before);assert.equal(e.depictionKind,'formula');assert.equal(view.name,e.name);assert.equal(view.svgPath,e.svgPath);assert.equal(view.sourceBindingCaption,e.caption);assert.equal(view.assetHashes.svgPath,e.assetHashes.svgPath);assert.equal(view.model3dPath,e.readerReference3d.model3dPath);assert.equal(chemicalButtonLabel(e),'Rotate 3D ↗');
});
test('flat reason remains one line and button is exact owner wording',()=>{const e={...entry(),readerReference3d:{route:'flat',whyNo3d:'The form is unspecified.'}};assert.equal(chemicalButtonLabel(e),'View formula ↗');assert.equal(flatReferenceReason(e),'The form is unspecified.');assert.equal(viewerEntry(e).model3dPath,null);});
test('ionic components do not become a whole ion assembly',()=>{const e={...entry(),readerReference3d:{route:'independent_component_references',referenceOnly:true,trainingEligible:false,component3dModels:[{model3dPath:'models/acetate.json',model3dSha256:sha}],component3dScope:'Independent components; no relative ion geometry.'}};const v=viewerEntry(e);assert.equal(v.model3dPath,null);assert.equal(v.component3dModels.length,1);assert.match(v.component3dScope,/no relative ion geometry/);});
test('opening a component cannot recursively inherit its parent reference route',()=>{const e={...entry(),readerReference3d:{route:'independent_component_references',referenceOnly:true,trainingEligible:false,component3dModels:[{model3dPath:'models/acetate.json',model3dSha256:sha}]}};const parent=viewerEntry(e),child={...parent,id:'acetate',model3dPath:'models/acetate.json',component3dModels:[]};assert.equal(viewerEntry(child).model3dPath,'models/acetate.json');assert.equal(viewerEntry(child).component3dModels.length,0);});
test('existing valid stock-solvent and component references are preserved',()=>{for(const e of [{...entry(),model3dPath:'models/water.json',assetHashes:{model3dPath:sha}},{...entry(),component3dModels:[{model3dPath:'models/water.json',model3dSha256:sha}]}]){assert.equal(viewerEntry(e),e);assert.equal(hasReference3d(e),true);}});
test('invalid route, flags or path fail closed',()=>{for(const bad of [{route:'molecule_reference',model3dPath:'models/../../private.json',model3dSha256:sha,referenceOnly:true,trainingEligible:false},{route:'molecule_reference',model3dPath:'models/x.json',model3dSha256:sha,referenceOnly:false,trainingEligible:false},{route:'invented'}])assert.equal(referenceRoute({...entry(),readerReference3d:bad}).route,'flat');});
test('ambient reference uses the existing unit-cell route, never molecule atoms',()=>{const ref={name:'InAs bulk reference',modelPath:'models/inas.json',modelSha256:sha,referenceOnly:true,trainingEligible:false};const e={...entry(),readerReference3d:{route:'ambient_crystal_reference',referenceOnly:true,trainingEligible:false,crystalReference:ref}};const v=viewerEntry(e);assert.equal(v.model3dPath,null);assert.equal(v.readerAmbientReference,ref);assert.equal(chemicalButtonLabel(e),'Rotate 3D ↗');assert.equal(chemicalButtonLabel(v),'Rotate 3D ↗');assert.equal(flatReferenceReason(v),'');});
const legacyFlat='Source-qualified identity/formula only. No atoms, bonds, bound surface geometry, molecular conformer or measured coordinates are assigned.';
const newMolecule=()=>({...entry(),caption:legacyFlat,sourceBindingCaption:legacyFlat,limitations:[legacyFlat,'The source does not specify a bound-surface conformation.'],readerReference3d:{route:'molecule_reference',model3dPath:'models/h-reader-abc-3d.json',model3dSha256:sha,referenceOnly:true,trainingEligible:false,caption:'Computed illustrative conformer, not measured sample coordinates.'}});
test('exact observed legacy flat boilerplate is qualified in a temporary 3D viewer only',()=>{
 const e=newMolecule(),before=JSON.stringify(e),v=viewerEntry(e);
 assert.equal(JSON.stringify(e),before);assert.equal(v.caption,e.readerReference3d.caption);
 for(const text of [v.caption,v.sourceBindingCaption,...v.limitations])assert.doesNotMatch(text,/identity\/formula only|No atoms, bonds|molecular conformer or measured coordinates are assigned/);
 assert.match(v.sourceBindingCaption,/Source-qualified chemical identity/);assert.match(v.sourceBindingCaption,/Bound surface geometry and measured sample coordinates are not assigned/);
 assert.equal(v.limitations[1],e.limitations[1]);assert.match(chemicalDisplayCaption(e),/Computed illustrative conformer/);
});
test('button-adjacent and explicit precursor captions share the validated reference presentation',()=>{
 const e=newMolecule();assert.equal(chemicalButtonLabel(e),'Rotate 3D ↗');
 for(const text of [chemicalDisplayCaption(e),chemicalDisplayCaption(e,legacyFlat)]){assert.match(text,/Computed illustrative conformer/);assert.doesNotMatch(text,/No atoms, bonds|identity\/formula only/);}
 const applicable='Only the source-reported chemical identity is assigned; no bound surface arrangement is known.';
 assert.equal(chemicalDisplayCaption(e,applicable),applicable);
 const ions={...e,readerReference3d:{route:'independent_component_references',referenceOnly:true,trainingEligible:false,component3dModels:[{model3dPath:'models/acetate.json',model3dSha256:sha}],component3dScope:'Independent molecular components; no relative ion geometry.'}};
 assert.match(chemicalDisplayCaption(ions),/no relative ion geometry/);
});
test('flat, invalid overlay and existing models keep their original depiction statements',()=>{
 for(const e of [{...entry(),caption:legacyFlat},{...newMolecule(),readerReference3d:{route:'molecule_reference',referenceOnly:false}}, {...entry(),caption:legacyFlat,model3dPath:'models/existing.json'}]){
  assert.equal(chemicalDisplayCaption(e),legacyFlat);assert.equal(viewerEntry(e).caption,legacyFlat);
 }
});
test('temporary reference retains source and reference attribution/qualifications together',()=>{
 const e=newMolecule();e.sourceUrls=['https://doi.org/10.1000/original'];e.readerReference3d.sourceUrls=['https://pubchem.ncbi.nlm.nih.gov/compound/1'];e.readerReference3d.limitations=['The reference is not a measured sample structure.'];const v=viewerEntry(e);
 assert.deepEqual(v.sourceUrls,[...e.sourceUrls,...e.readerReference3d.sourceUrls]);assert.ok(v.limitations.includes(e.readerReference3d.limitations[0]));assert.deepEqual(e.sourceUrls,['https://doi.org/10.1000/original']);
});
test('fixed systematic octane presentation removes only its obsolete isomer uncertainty',()=>{
 const oldModel='Illustrative straight-chain octane reference and one locally computed free-molecule conformer. A source that names octane without specifying an isomer does not establish this exact connectivity; the model does not specify solvent purity, amount, solution arrangement, surface adsorption or an observed geometry.';
 const e={...entry(),id:'kim-octane',name:'octane',formula:null,caption:'octane; source-named solvent only. No unique isomer or molecular connectivity is assigned.',limitations:['No unique isomer or molecular connectivity is assigned.','This card does not establish solution speciation or measured geometry.'],readerReference3d:{route:'molecule_reference',reason:'owner_fixed_named_identity',referenceRegistryId:'octane',model3dPath:'models/octane-3d.json',model3dSha256:sha,referenceOnly:true,trainingEligible:false,caption:oldModel}};
 const before=JSON.stringify(e),v=viewerEntry(e);assert.equal(JSON.stringify(e),before);assert.match(chemicalDisplayCaption(e),/straight-chain reference/);
 for(const text of [v.caption,v.sourceBindingCaption,...v.limitations,chemicalModelCaption(v,oldModel)])assert.doesNotMatch(text,/No unique isomer|does not establish this exact connectivity/);
 assert.match(chemicalModelCaption(v,oldModel),/solvent purity, amount, solution arrangement, surface adsorption or an observed geometry/);assert.ok(v.limitations.includes(e.limitations[1]));
 const ambiguous={...e,name:'octanes',readerReference3d:{route:'flat',whyNo3d:'Reported isomers are unresolved.'}};assert.match(chemicalDisplayCaption(ambiguous),/No unique isomer/);assert.equal(chemicalModelCaption(ambiguous,oldModel),oldModel);
});
test('existing named octane model remains byte-identical while its presentation follows systematic-name rule',()=>{
 const caption='A source that names octane without specifying an isomer does not establish this exact connectivity; the model does not specify solvent purity.';const e={...entry(),id:'octane',name:'Octane',caption,model3dPath:'models/octane-3d.json'};const before=JSON.stringify(e),v=viewerEntry(e);assert.equal(JSON.stringify(e),before);assert.equal(v.model3dPath,e.model3dPath);assert.equal(chemicalDisplayCaption(e),'the model does not specify solvent purity.');assert.doesNotMatch(chemicalModelCaption(v,caption),/does not establish/);
});
