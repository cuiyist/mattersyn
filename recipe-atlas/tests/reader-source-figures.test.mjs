import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {figureMatchesCategory,sourceFigureRows} from '../static/reader-utils.mjs';

// UI fixtures use the category combinations which caused reviewed crops to be
// unreachable. They are not new scientific records or release approvals.
class Node {
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.attributes={};this._text='';this.open=false;}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this.children=children;this._text='';}
 setAttribute(key,value){this.attributes[key]=String(value);}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(c=>c.textContent??String(c)).join(' ');}
 set innerHTML(_){throw Error('Unexpected HTML rendering');}
 showModal(){this.open=true;}
 close(){this.open=false;}
}
globalThis.document={createElement:tag=>new Node(tag),body:new Node('body'),getElementById:()=>null};
const {figureGallery}=await import('../static/reader-app.mjs');
// A guide import query alone does not isolate its fixed loader dependency. Evaluate
// the actual guide with absolute imports and a fresh actual loader module per fixture.
const guideURL=new URL('../static/material-guide.mjs',import.meta.url);
const guideCode=await readFile(guideURL,'utf8');
async function isolatedGuide(name){
 const code=guideCode.replace(/\bfrom (['"])(\.\/[^'"]+)\1/g,(_match,quote,path)=>{
  const url=new URL(path,guideURL);
  if(url.pathname.endsWith('/reader-presentation-loader.mjs'))url.searchParams.set('fixture',name);
  return 'from '+quote+url.href+quote;
 }).replaceAll('import.meta.url',JSON.stringify(guideURL.href));
 return import('data:text/javascript;base64,'+Buffer.from(code).toString('base64')+'#'+name);
}
const jsonResponse=value=>new Response(JSON.stringify(value));
const presentationResponse=data=>jsonResponse({records:{},materials:{},figures_by_source:{},...data});
const {fallbackSources}=await isolatedGuide('fallback-source-fixture');
const walk=n=>[n,...n.children.flatMap(c=>c instanceof Node?walk(c):[])];
const nodes=(n,tag)=>walk(n).filter(x=>x.tagName===tag);
const freeze=o=>{if(o&&typeof o==='object'){for(const v of Object.values(o))freeze(v);Object.freeze(o);}return o;};
const figure=(id,category,source_id='reviewed-main',extra={})=>({id,source_id,category,title:id,
 public_asset:'assets/paper-reviews/ui-fixture/'+id+'.png',summary:'Source context only. No exact batch is assigned.',
 scope:'Contextual specimen; no recipe-pair assignment',scope_note:'Keep comparator panels separate.',
 source_locator:{document_role:source_id==='reviewed-si'?'si':'main',page:2,figure:id},
 record_links:['route-a'],sample_links:[],same_batch_asserted:false,...extra});
const record={record_id:'route-a',lineage:{source_group:'reviewed-main'},sources:[]};
const host=()=>new Node('section');
const fixture=freeze([
 figure('Scheme 1','protocol'),figure('Figure 1','characterization'),
 figure('Figure 2','structure'),figure('Figure 4','structure'),figure('Figure 5','structure'),
 figure('Figure S3','characterization','reviewed-si'),figure('Figure S5','structure','reviewed-si')
]);

test('previously unplaced protocol and characterization figures remain accessible without recategorizing',()=>{
 const before=JSON.stringify(fixture),extra=sourceFigureRows(fixture,true);
 assert.deepEqual(extra.map(f=>f.id),['Scheme 1','Figure 1','Figure S3']);
 assert.equal(extra[0],fixture[0]);assert.equal(extra[1],fixture[1]);assert.equal(extra[2],fixture[5]);
 assert.equal(figureMatchesCategory(fixture[0],'structure'),false);
 const existing=new Set(fixture.filter(f=>['structure','property','precursor'].some(c=>figureMatchesCategory(f,c))).map(f=>f.id));
 assert.equal(new Set([...existing,...extra.map(f=>f.id)]).size,7);
 assert.equal(JSON.stringify(fixture),before);
});

test('morphology and atomic_structure categories are shown as source context rather than assigned another category',()=>{
 const f=freeze(figure('Yang Figure 1','morphology','reviewed-main',{categories:['morphology','atomic_structure']}));
 assert.deepEqual(sourceFigureRows([f],true),[f]);assert.equal(figureMatchesCategory(f,'structure'),false);
 const h=host();assert.equal(figureGallery(h,[f],record,'source'),1);
 assert.match(h.textContent,/Contextual specimen; no recipe-pair assignment/);
 assert.match(h.textContent,/Keep comparator panels separate/);
 assert.match(h.textContent,/main · PDF p. 2 · Yang Figure 1/);
 assert.equal(f.category,'morphology');assert.deepEqual(f.categories,['morphology','atomic_structure']);
});

test('all existing category aliases and multi-category placements avoid duplicate fallback entries',()=>{
 const rows=['structure','structures','composition','property','properties','optical','precursor'].map((c,i)=>figure('placed-'+i,c));
 rows.push(figure('multi','protocol','reviewed-main',{categories:['properties']}));
 assert.deepEqual(sourceFigureRows(rows,true),[]);
 assert.deepEqual(sourceFigureRows([figure('same','unknown'),figure('same','structure')],true),[]);
});

test('source figures deduplicate by source identity and figure identity, keeping distinct sources',()=>{
 const a=figure('Figure 1','protocol'),last=figure('Figure 1','characterization'),b=figure('Figure 1','protocol','reviewed-si');
 const selected=sourceFigureRows([a,last,b],true);
 assert.deepEqual(selected,[last,b]);assert.equal(selected[0],last);
 const h=host();assert.equal(figureGallery(h,[a,last,b],record,'source'),2);
 assert.equal(nodes(h,'button').filter(n=>n.attributes.role==='tab').length,2);
 const collision=host();assert.equal(figureGallery(collision,[figure('c','protocol','a|b'),figure('b|c','protocol','a')],record,'source'),2);
});

test('all additional original figures open exact images while retaining caption qualifiers and locators',()=>{
 const rows=sourceFigureRows(fixture,true),h=host();figureGallery(h,rows,record,'source');
 const tabs=nodes(h,'button').filter(n=>n.attributes.role==='tab');
 assert.deepEqual(tabs.map(n=>n.textContent),['Scheme 1','Figure 1','Figure S3']);
 for(let i=0;i<tabs.length;i++){
  tabs[i].onclick();const image=nodes(h,'img')[0];assert.ok(image.src.endsWith(encodeURI(rows[i].public_asset)));
  image.onclick();const dialog=nodes(document.body,'dialog').at(-1);
  assert.equal(dialog.open,true);assert.equal(nodes(dialog,'img')[0].src,image.src);
  assert.ok(dialog.textContent.includes(rows[i].summary));
  assert.ok(h.textContent.includes(rows[i].scope));assert.ok(h.textContent.includes(rows[i].scope_note));
 }
});

test('source_link placeholders keep the source-link dialog and never become original images',()=>{
 const f=freeze(figure('withheld','protocol','reviewed-main',{display_kind:'source_link',
  public_asset:'assets/source-link-placeholder.svg',source_url:'https://doi.org/10.0000/fixture',
  display_note:'Original figure withheld; rights status remains unverified.'}));
 const h=host();figureGallery(h,[f],record,'source');
 assert.match(h.textContent,/Original figure withheld; rights status remains unverified/);
 const image=nodes(h,'img')[0];assert.equal(image.alt,'Source-link card; original figure withheld');image.onclick();
 const dialog=nodes(document.body,'dialog').at(-1);assert.equal(nodes(dialog,'img').length,0);
 assert.equal(nodes(dialog,'a')[0].href,f.source_url);assert.ok(dialog.textContent.includes(f.summary));
});

test('text-only figures remain disclosures and do not acquire fabricated image assets',()=>{
 const f=freeze(figure('text-only','characterization','reviewed-main',{public_asset:null})),h=host();
 assert.equal(figureGallery(h,[f,f],record,'source'),1);
 assert.equal(nodes(h,'img').length,0);assert.equal(nodes(h,'details').length,1);
 assert.match(h.textContent,/original image unavailable/);assert.match(h.textContent,/No exact batch is assigned/);
});


test('source-extracted figure introduction stays neutral without changing source figures or status',async()=>{
 const {fallbackSources:neutralFallback}=await isolatedGuide('neutral-source-intro-fixture');
 const data=freeze({records:{'route-a':{figures:fixture}}});
 globalThis.fetch=async()=>presentationResponse(data);
 const r=freeze({...record,quality:{review_status:'source_extracted'},review_status:'source_reviewed'});
 const before=JSON.stringify({r,data}),h=host();
 assert.equal(await neutralFallback(h,r),true);
 assert.equal(h.children[0].textContent,'Source figures assigned to this record retain their own specimen and context qualifications; their display does not establish the same physical batch.');
 assert.doesNotMatch(h.children[0].textContent,/reviewed|audited|extracted/i);
 assert.equal(nodes(h,'button').filter(n=>n.attributes.role==='tab').length,7);
 assert.equal(JSON.stringify({r,data}),before);
});
test('audited and other existing figure introductions retain their exact wording and gallery',async()=>{
 const {fallbackSources:legacyFallback}=await isolatedGuide('legacy-source-intro-fixture');
 const data=freeze({records:{'route-a':{figures:fixture}}});
 globalThis.fetch=async()=>presentationResponse(data);
 const before=JSON.stringify(data);
 for(const status of ['source_reviewed','audited','pending',undefined]){
  const r=freeze({...record,quality:{review_status:status},review_status:'source_extracted'}),rBefore=JSON.stringify(r),h=host();
  assert.equal(await legacyFallback(h,r),true);
  assert.equal(h.children[0].textContent,'Source figures assigned to this reviewed record retain their own specimen and context qualifications; their display does not establish the same physical batch.');
  assert.equal(nodes(h,'button').filter(n=>n.attributes.role==='tab').length,7);
  assert.equal(JSON.stringify(r),rBefore);
 }
 assert.equal(JSON.stringify(data),before);
});

test('Data fallback reads only the exact record presentation without adding other paper or sample figures',async()=>{
 const data=freeze({records:{'route-a':{figures:fixture},'other-route':{figures:[figure('unrelated','protocol')]}}});
 const requests=[];globalThis.fetch=async url=>{requests.push(String(url));return presentationResponse(data);};
 const h=host(),before=JSON.stringify(data);assert.equal(await fallbackSources(h,record),true);
 assert.equal(nodes(h,'button').filter(n=>n.attributes.role==='tab').length,7);
 assert.doesNotMatch(h.textContent,/unrelated/);assert.match(h.textContent,/does not establish the same physical batch/);
 const absent=host();assert.equal(await fallbackSources(absent,{...record,record_id:'unreviewed-record'}),false);
 assert.equal(absent.children.length,0);assert.equal(requests.length,1);
 assert.ok(requests[0].endsWith('/data/reader-presentation.json'));assert.equal(JSON.stringify(data),before);
});

test('the core-scoped Data entrypoint renders the fallback and retains existing context links',async()=>{
 const {mountEvidence}=await isolatedGuide('data-entrypoint-fixture');
 const requests=[];globalThis.fetch=async url=>{const path=String(url);requests.push(path);
  if(path.endsWith('/data/paper-review-index.json'))return jsonResponse({papers:[]});
  assert.ok(path.endsWith('/data/reader-presentation.json'));
  return presentationResponse({records:{'route-a':{figures:fixture}}});
 };
 const h=host();await mountEvidence(h,{...record,context_links:[{label:'Reviewed source context',url:'data/fixture-context.json'}]});
 assert.equal(nodes(h,'button').filter(n=>n.attributes.role==='tab').length,7);
 assert.ok(nodes(h,'a').some(n=>n.textContent==='Reviewed source context →'));
 assert.doesNotMatch(h.textContent,/Original characterization is available/);
 assert.equal(requests.length,2);
 const absent=host();await mountEvidence(absent,{...record,record_id:'unreviewed-record'});
 assert.equal(nodes(absent,'img').length,0);
 assert.match(absent.textContent,/Original characterization is available/);
});
