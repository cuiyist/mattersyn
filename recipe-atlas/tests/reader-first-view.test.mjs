import test from 'node:test';
import assert from 'node:assert/strict';
import {structureViewsEmpty} from '../static/reader-structures.mjs';

class Element{
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.className='';this._text='';this.hidden=false;this.id='';}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this.children=[...children];this._text='';}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(child=>child.textContent||'').join(' ');}
 setAttribute(){}
 querySelector(selector){if(selector==='.reader-number')return this.children.find(c=>c.className==='reader-number')||null;return null;}
}
const priorDocument=globalThis.document;
globalThis.document={body:{dataset:{}},createElement:tag=>new Element(tag)};
const {emptySections,hideEmptySections,renderProperties,renderIntuition,displayMethod,GENERIC_METHOD}=await import('../static/reader-app.mjs');
globalThis.document=priorDocument;
const withDOM=callback=>{const prior=globalThis.document;globalThis.document={createElement:tag=>new Element(tag)};try{return callback();}finally{globalThis.document=prior;}};

test('generic extraction phrases are not shown as a method label',()=>{
 assert.equal(displayMethod('Synthesis as described in the source'),'');
 assert.equal(displayMethod('Other'),'');
 assert.ok(GENERIC_METHOD.test(' other '));
 assert.equal(displayMethod('Synthesis as described in the source','Hot injection'),'Hot injection');
 assert.equal(displayMethod('Heat-up'),'Heat-up');
});

test('synonyms are shown under one name',()=>{
 assert.equal(displayMethod('MBE'),'Molecular beam epitaxy');
 assert.equal(displayMethod('Molecular-beam epitaxy'),'Molecular beam epitaxy');
 assert.equal(displayMethod('MOCVD'),'Metal-organic chemical vapor deposition');
 assert.equal(displayMethod('hot injection'),'Hot injection');
 assert.equal(displayMethod('Sol–gel'),'Sol-gel');
 assert.equal(displayMethod('Seed-mediated growth'),'Seed-mediated growth');
});

test('empty sections are hidden and the visible ones renumbered',()=>withDOM(()=>{
 const make=id=>{const s=new Element('section');s.id=id;const n=new Element('span');n.className='reader-number';n.textContent='00';s.append(n);return s;};
 const sections=['precursors','protocol','structures','properties','intuition','sources'].map(make);
 const hidden=hideEmptySections(sections,emptySections({lineage:{source_group:'x'}},{structures:true,properties:false,intuition:true}));
 assert.deepEqual([...hidden].sort(),['intuition','structures']);
 assert.deepEqual(sections.map(s=>s.hidden),[false,false,true,false,true,false]);
 assert.deepEqual(sections.filter(s=>!s.hidden).map(s=>s.children[0].textContent),['01','02','03','04']);
 assert.equal(emptySections({lineage:{source_group:'wu2008'}},{structures:true}).size,0);
}));

test('properties with only the placeholder are marked empty',()=>withDOM(()=>{
 const r={record_id:'r1',lineage:{source_group:'x'},measurements:[],products:[]};
 const host=new Element('section');
 assert.equal(renderProperties(host,[],r,{}),0);
 assert.equal(host.dataset.readerEmpty,'true');
 const measured={...r,measurements:[{property:'absorption_peak',sample_id:'s',value:{value:500,unit:'nm',status:'reported'}}]};
 const other=new Element('section');
 assert.equal(renderProperties(other,[],measured,{}),1);
 assert.equal(other.dataset.readerEmpty,'false');
}));

test('final structures are empty only without a cell, product fact or morphology',async()=>{
 globalThis.fetch=async()=>({ok:true,json:async()=>({record_exceptions:{nonperiodic:{kind:'not_applicable_nonperiodic'}}})});
 const panels=found=>({querySelector:id=>id==='#reader-structure-particle'?{querySelector:()=>found}:null});
 const r=id=>({record_id:id,lineage:{source_group:'x'}});
 assert.equal(await structureViewsEmpty(r('a'),[],[],panels(null)),true);
 assert.equal(await structureViewsEmpty(r('a'),[],[],panels({})),false);
 assert.equal(await structureViewsEmpty(r('a'),[{id:'cell'}],[],panels(null)),false);
 assert.equal(await structureViewsEmpty(r('nonperiodic'),[],[],panels(null)),false);
 assert.equal(await structureViewsEmpty({record_id:'h',lineage:{source_group:'heo2003'}},[],[],panels(null)),false);
});

const backgroundItem=(id='background')=>({id,title:'General chemistry',summary:'A short authored principle.',label:"General background, not the authors' interpretation",reference:{doi:'10.1021/cr400544s',url:'https://doi.org/10.1021/cr400544s',title:'Mechanisms of Nucleation and Growth of Nanoparticles in Solution'}});
const descendants=node=>[node,...(node.children||[]).flatMap(descendants)];
test('background-only intuition stays visible and uses DOI rather than source Evidence links',()=>withDOM(()=>{
 const host=new Element('section'),r={record_id:'r',lineage:{source_group:'s'},sources:[{id:'s'}]};
 assert.equal(renderIntuition(host,r,{general_background:[backgroundItem()]}),true);
 const all=descendants(host);assert.equal(all.filter(n=>n.tagName==='article').length,1);
 assert.ok(host.textContent.includes("General background, not the authors' interpretation"));
 assert.deepEqual(all.filter(n=>n.tagName==='a').map(n=>n.href),['https://doi.org/10.1021/cr400544s']);
 assert.equal(emptySections(r,{intuition:false}).has('intuition'),false);
}));
test('source interpretations remain first and unchanged with their independent source limit and view-all link',()=>withDOM(()=>{
 const r={record_id:'r',lineage:{source_group:'s'},sources:[{id:'s'}]},source=Array.from({length:4},(_,i)=>({title:'Source '+i,summary:'Original '+i,claim_type:'Source interpretation'}));
 const presentation={intuition:source,general_background:Array.from({length:4},(_,i)=>backgroundItem('b'+i))},before=structuredClone(presentation),host=new Element('section');
 assert.equal(renderIntuition(host,r,presentation),true);
 const cards=descendants(host).filter(n=>n.tagName==='article');assert.equal(cards.length,6);
 assert.ok(cards[0].textContent.includes('Original 0'));assert.ok(cards[2].textContent.includes('Original 2'));
 assert.equal(cards[3].dataset.backgroundId,'b0');assert.equal(cards[5].dataset.backgroundId,'b2');
 assert.equal(descendants(host).filter(n=>n.tagName==='a'&&n.textContent==='Evidence →').length,3);
 assert.equal(descendants(host).filter(n=>n.tagName==='a'&&n.textContent==='All interpretations and references →').length,1);
 assert.deepEqual(presentation,before);
}));
test('actual intuition rendering is status-neutral and genuinely empty content keeps prior hidden behavior',()=>withDOM(()=>{
 const r={record_id:'r',lineage:{source_group:'s'},sources:[{id:'s'}],quality:{review_status:'reviewed'}},p={general_background:[backgroundItem()]};
 const first=new Element('section'),second=new Element('section');renderIntuition(first,r,p);renderIntuition(second,{...r,quality:{review_status:'source_extracted'}},p);
 assert.equal(first.textContent,second.textContent);assert.equal(renderIntuition(new Element('section'),r,{}),false);
 assert.equal(emptySections(r,{intuition:true}).has('intuition'),true);
}));
