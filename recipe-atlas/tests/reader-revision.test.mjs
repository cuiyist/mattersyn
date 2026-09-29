import test from 'node:test';
import assert from 'node:assert/strict';
import {figureMorphologyContexts} from '../static/reader-figure-morphology.mjs';
import {referenceForRecord,referencesForSample,referenceCellVectors} from '../static/reader-structures.mjs';
import {particleDescriptor,particleGroups} from '../static/reader-particle.mjs';

test('measurement-only Readers retain exact canonical specimen observations without borrowing facts',()=>{
 const field=(value,status='reported')=>({value,status,evidence:[{source_id:'paper-a',locator:'Figure 1'}],note:'Exact specimen scope'});
 const record={record_id:'route-a',material:{formula:'not a measured product'},products:[
  {sample_id:'sample-a',source_sample_label:'Sample A',composition:field('CaCO3'),phase:field('Calcite'),morphology:field('Rhombohedra'),surface:field(null)},
  {sample_id:'sample-b',morphology:field('Rods'),composition:field('unresolved','not_reported')}
 ]};
 const presentation={productContexts:[{record_id:'route-b',sample_id:'sample-a',label:'Other route'}],productFacts:[]};
 const before=JSON.stringify({record,presentation}),groups=particleGroups(record,presentation);
 assert.deepEqual(groups.get('route-a:sample-a').facts.map(f=>f.value),['CaCO3','Calcite','Rhombohedra']);
 assert.equal(groups.get('route-a:sample-b').facts[0].value,'Rods');
 assert.equal(groups.get('route-b:sample-a').facts.length,0);
 assert.deepEqual(groups.get('route-a:sample-a').facts[2].source_locator,record.products[0].morphology.evidence);
 assert.equal(JSON.stringify({record,presentation}),before);
 const existing={kind:'phase',value:'Calcite',status:'reported',record_id:'route-a',sample_id:'sample-a',qualifier:'Reader qualifier'};
 const withFacts=particleGroups(record,{productFacts:[existing]}).get('route-a:sample-a').facts;
 assert.equal(withFacts.filter(f=>f.kind==='phase').length,1);assert.equal(withFacts[0],existing);
 assert.equal(particleGroups({record_id:'empty',material:{formula:'Do not infer'},products:[]}).get('empty:unassigned').facts.length,0);
});

test('figure interpretations require both the exact displayed image and route, never a training label',()=>{
 const entry={id:'figure-context',source_group:'paper-a',binding:'source_figure_context_only',measured_coordinates:false,eligible_training:false,record_ids:['route-a'],asset:'assets/figure.png',shape:'rod'};
 const record={record_id:'route-a',lineage:{source_group:'paper-a'}},presentation={figures:[{asset:'assets/figure.png'}]};
 assert.equal(figureMorphologyContexts([entry],record,presentation).length,1);
 for(const rejected of [{...entry,source_group:'paper-b'},{...entry,record_ids:['route-b']},{...entry,asset:'assets/other.png'},{...entry,eligible_training:true},{...entry,measured_coordinates:true},{...entry,binding:'sample_assignment'}])assert.equal(figureMorphologyContexts([rejected],record,presentation).length,0);
 assert.equal(figureMorphologyContexts([entry],record,{figures:[{asset:entry.asset,display_kind:'source_link'}]}).length,0);
 assert.equal(particleDescriptor({recordId:'route-a',sampleId:'sample',facts:[]},{'figure-context':entry}).shape,'neutral');
});

test('per-record crystal contexts cannot borrow another specimen or the generic context list',()=>{
 const ref={id:'cell',displayPolicy:'sample_context_choice',sample_context_ids:['generic'],sampleContextIdsByRecord:{a:['sample-a'],b:['sample-b']},roleByRecord:{a:'Core'}};
 const before=JSON.stringify(ref);
 const scoped=referenceForRecord(ref,'a',{a:'Core · CdSe'});
 assert.equal(scoped.roleByRecord.a,'Core · CdSe');
 assert.equal(referencesForSample([scoped],'sample-a').length,1);
 for(const id of ['generic','sample-b'])assert.equal(referencesForSample([scoped],id).length,0);
 assert.deepEqual(referenceForRecord(ref,'unassigned').sample_context_ids,[]);
 assert.equal(JSON.stringify(ref),before);
});

test('reference geometry rejects impossible periodic cells',()=>{
 assert.throws(()=>referenceCellVectors({cell:{a:1,b:1,c:1,alpha:0,beta:0,gamma:0}}));
 assert.throws(()=>referenceCellVectors({cellVectors:[[1,0,0],[0,1,0],[0,0,-1]]}));
 assert.equal(referenceCellVectors({cell:{a:2,b:3,c:4,alpha:90,beta:90,gamma:90}}).length,3);
});
