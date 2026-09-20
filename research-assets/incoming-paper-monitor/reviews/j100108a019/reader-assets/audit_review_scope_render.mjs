/** Read-only bounded DOM/text harness; no browser, network, Site writes or builds. */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const site=process.argv[2]||'[local path redacted]';
const read=relative=>JSON.parse(fs.readFileSync(path.join(site,relative),'utf8'));
const library=read('dist/data/library-index.json');
const scope={scope:'supplied_main_only_si_unverified',label:'Complete supplied main review; SI unverified',si_status:'not_located_or_verified'};
const fixture={id:'paper-c93e8dc8393a5d19cda8',doi:'10.1021/j100108a019',doiUrl:'https://doi.org/10.1021/j100108a019',title:'A Luminescent Silicon Nanocrystal Colloid via a High-Temperature Aerosol Reaction',year:1993,materials:[],candidateMaterialMentions:[],reviewedRecordIds:[],benchmarkRecordIds:[],coverage:{localDocumentCount:1,mainDocumentAvailable:true,supportingDocumentAvailable:false,extractionStatusCounts:{extracted:1}},reviewStatus:'main_only_reviewed',fullDocumentReview:{...scope,id:'littau1993',url:'paper-review.html?id=littau1993',pages:7,figures:12}};
const review={paper_id:'littau1993',title:fixture.title,doi:fixture.doi,review_scope:scope.scope,review_scope_label:scope.label,supporting_information:{status:'not_located_or_verified',note:'Main-only fixture; SI availability remains unverified.'},documents:[{role:'main',page_count:7,source_file:'main.pdf',sha256:'d'.repeat(64),pages:Array.from({length:7},(_,i)=>({page:i+1,sections:['Supplied main page']}))}],figures:[],tables:[],recipe_inventory:[],characterization_inventory:[],remaining_gaps:['SI not located or verified.'],independent_audit:'Complete only for supplied-main reading'};
class Node {
  constructor(tag='div'){this.tag=tag;this.children=[];this.dataset={};this.style={};this.events={};this.value='';this.textContent='';this.classList={add(){},toggle(){}};}
  append(...nodes){this.children.push(...nodes);} replaceChildren(...nodes){this.children=[...nodes];}
  insertBefore(node){this.children.push(node);} addEventListener(name,callback){this.events[name]=callback;}
  setAttribute(name,value){this[name]=value;} showModal(){} close(){}
  get innerText(){return [this.textContent??'',...this.children.map(n=>typeof n==='string'?n:n.innerText)].join(' ');}
}
async function execute(name,fixtures,search='?id=paper-c93e8dc8393a5d19cda8'){
  const nodes=new Map(),errors=[];
  const doc={body:new Node('body'),title:'',createElement:tag=>new Node(tag),getElementById:id=>{if(!nodes.has(id))nodes.set(id,new Node());return nodes.get(id);},querySelector:id=>doc.getElementById(id),addEventListener(){}};
  const context=vm.createContext({document:doc,location:{search},URL,URLSearchParams,console:{error:err=>errors.push(String(err))},fetch:async input=>{
    const key=typeof input==='string'?input:new URL(input).pathname.replace(/^\//,'');
    const data=fixtures[key];if(data===undefined)throw new Error('Unexpected mocked fetch: '+key);
    return {ok:true,json:async()=>structuredClone(data)};
  }});
  const module=new vm.SourceTextModule(fs.readFileSync(path.join(site,'dist',name),'utf8'),{context,initializeImportMeta:meta=>{meta.url='https://local.invalid/'+name;}});
  await module.link(async spec=>{
    let names=spec.includes('crystal-viewer')?['mountCrystalReferences']:spec.includes('protocol-visuals')?['mountProtocol']:spec.includes('chemical-viewer')?['chemicalRegistry','chemicalEntry','chemicalImage','openChemical']:['mountMaterialGuide'];
    return new vm.SyntheticModule(names,function(){for(const key of names)this.setExport(key,async()=>{});},{context});
  });
  await module.evaluate();assert.deepEqual(errors,[],name+' rendering errors');
  return {nodes,doc,module};
}
const matched=library.papers.filter(p=>p.fullDocumentReview?.scope==='supplied_main_and_matched_si');
assert.equal(matched.length,5);assert.equal(matched.reduce((n,p)=>n+p.fullDocumentReview.pages,0),74);
const lib=await execute('library-app.mjs',{'data/library-index.json':{...library,papers:[...matched,fixture],local_paper_groups:6}});
assert.match(lib.nodes.get('full-review-state').innerText,/5 papers.*74 pages.*1 have.*SI unverified \(7 pages\)/);
lib.nodes.get('paper-status').value='main_only_reviewed';lib.nodes.get('paper-status').events.change();
assert.equal(lib.nodes.get('paper-results').children.length,1);assert.match(lib.nodes.get('paper-results').innerText,/SI unverified/);assert.doesNotMatch(lib.nodes.get('paper-results').innerText,/matched SI review/);
const paper=await execute('paper-app.mjs',{['data/papers/'+fixture.id+'.json']:fixture,'data/materials-index.json':{materials:[]}});
assert.match(paper.nodes.get('paper-review').innerText,/SI unverified/);assert.doesNotMatch(paper.nodes.get('paper-review').innerText,/matched SI/);
const reviewed=await execute('paper-review.mjs',{'data/paper-reviews/littau1993.json':review},'?id=littau1993');
assert.match(reviewed.nodes.get('review-summary').innerText,/SI unverified.*7 pages/);
assert.match(reviewed.nodes.get('documents').innerText,/Supplied documents and review scope.*Supporting-information availability.*not_located_or_verified.*SI availability remains unverified/);
const material={id:'si-test',formula:'Si',name:'Silicon',elements:['Si'],scope_note:'Fixture label test only.',reviewed_records:0,component_only:false,records:[],papers:[fixture]};
const hub=await execute('material-hub.mjs',{'data/materials-index.json':{materials:[material]},'data/materials/si-test.json':material},'?id=si-test');
assert.match(hub.nodes.get('material-papers').innerText,/SI unverified/);assert.doesNotMatch(hub.nodes.get('material-papers').innerText,/matched SI review/);
const guide=await execute('material-guide.mjs',{'data/paper-review-index.json':{papers:[{id:'littau1993'}]},'data/paper-reviews/littau1993.json':review});
const host=new Node();await guide.module.namespace.mountEvidence(host,{lineage:{source_group:'littau1993'},context_links:[]});
assert.match(host.innerText,/SI unverified/);assert.doesNotMatch(host.innerText,/Complete main\/SI|matched SI review|Primary paper and supplements/);
console.log(JSON.stringify({status:'passed',kind:'bounded_mock_DOM_text_regression',modules:['library-app','paper-app','paper-review','material-hub','material-guide'],fixture:'Explicit supplied-main-only seven-page Littau pathway; not a published-data assertion',existing_matched_reviews:5,existing_matched_pages:74,library_main_only_filter:'one matching fixture; no matched-SI label',network_used:false,site_written:false}));
