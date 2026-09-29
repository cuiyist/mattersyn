// Public display checks are defensive shape checks, not scientific or private-evidence validation.
export const SCHEMA='mattersyn-preliminary-synthesis/1';
const HASH=/^[a-f0-9]{64}$/,ID=/^prelim-[a-f0-9]{16}$/,HUB=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const DOI=/^10\.\d{4,9}\/\S+$/;
const PRIVATE=/(?:[A-Za-z]:[\\/]|\\\\|file:\/\/|\/(?:Users|home|tmp)\/)/;
const SYMBOLS=new Set('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'.split(' '));
const ENTRY=['source_id','doi','title','citation','document_sha256','document_role','source_pages','inspected_pages','material','method_label','scope','deferred','precursors','operations','outcome','missing_fields','review','extraction','evidence_fingerprint'];
const exact=(x,keys)=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
const text=(x,max=600)=>typeof x==='string'&&x.trim().length>0&&x.length<=max&&!/[\x00-\x1f\x7f]/.test(x)&&!PRIVATE.test(x);
const list=(x,min,max,test)=>Array.isArray(x)&&x.length>=min&&x.length<=max&&x.every(test);
const positive=x=>Number.isSafeInteger(x)&&x>0;
const texts=x=>list(x,0,64,v=>text(v,240));
function locators(value,e){return list(value,1,32,x=>exact(x,['page','section'])&&positive(x.page)&&x.page<=e.source_pages&&e.inspected_pages.includes(x.page)&&text(x.section,160));}
export function doiURL(doi){if(!text(doi,200)||!DOI.test(doi))throw new TypeError('Invalid DOI');return 'https://doi.org/'+doi.split('/').map(encodeURIComponent).join('/');}
export function preparePreliminary(data){
 const unavailable={status:'unavailable',entries:[]};
 if(!exact(data,['schema','entries'])||data.schema!==SCHEMA||!list(data.entries,0,20000,x=>exact(x,ENTRY)))return unavailable;
 const ids=new Set(),dois=new Set();
 for(const e of data.entries){
  if(typeof e.source_id!=='string'||!ID.test(e.source_id)||!text(e.doi,200)||!DOI.test(e.doi)||e.doi!==e.doi.toLowerCase()||ids.has(e.source_id)||dois.has(e.doi)||!text(e.title)||!text(e.citation)||typeof e.document_sha256!=='string'||!HASH.test(e.document_sha256)||typeof e.evidence_fingerprint!=='string'||!HASH.test(e.evidence_fingerprint)||!['main','si'].includes(e.document_role)||!positive(e.source_pages)||e.source_pages>5000)return unavailable;
  ids.add(e.source_id);dois.add(e.doi);
  if(!list(e.inspected_pages,1,e.source_pages,p=>positive(p)&&p<=e.source_pages)||new Set(e.inspected_pages).size!==e.inspected_pages.length)return unavailable;
  const m=e.material,r=e.review,x=e.extraction;
  if(!exact(m,['label','elements','existing_hub_id'])||!text(m.label,240)||!list(m.elements,1,118,s=>SYMBOLS.has(s))||new Set(m.elements).size!==m.elements.length||!(m.existing_hub_id===null||typeof m.existing_hub_id==='string'&&m.existing_hub_id.length<=100&&HUB.test(m.existing_hub_id)))return unavailable;
  if(!exact(r,['tier','author_source_checked','independent_audit','accuracy','training_ready'])||r.tier!=='preliminary'||r.author_source_checked!==true||r.independent_audit!=='pending'||r.accuracy!=='unmeasured'||r.training_ready!==false)return unavailable;
  if(!exact(x,['origin','recipe_scope_complete','omitted_variants','source_identity_checked'])||!['assistant_source_checked','local_model_source_checked'].includes(x.origin)||x.recipe_scope_complete!==true||x.source_identity_checked!==true||!text(x.omitted_variants))return unavailable;
  if(!text(e.method_label,240)||!text(e.scope)||!texts(e.deferred)||!texts(e.missing_fields))return unavailable;
  if(!list(e.precursors,1,64,p=>exact(p,['name','amount','role','locators'])&&text(p.name,240)&&(p.amount===null||text(p.amount,240))&&text(p.role,240)&&locators(p.locators,e)))return unavailable;
  if(!list(e.operations,2,100,(o)=>exact(o,['order','action','conditions','locators'])&&positive(o.order)&&text(o.action,240)&&list(o.conditions,0,32,c=>exact(c,['parameter','reported'])&&text(c.parameter,120)&&text(c.reported,240))&&locators(o.locators,e))||!e.operations.every((o,i)=>o.order===i+1))return unavailable;
  const o=e.outcome;
  if(!exact(o,['sample_label','link_basis','descriptors','locators'])||!text(o.sample_label,240)||!text(o.link_basis)||!locators(o.locators,e)||!list(o.descriptors,1,32,d=>exact(d,['kind','reported','technique','locators'])&&['phase','composition','morphology','size','architecture'].includes(d.kind)&&text(d.reported,320)&&text(d.technique,160)&&locators(d.locators,e)))return unavailable;
 }
 return {status:'ready',entries:structuredClone(data.entries)};
}
export function filterEntries(entries,{query='',element='',hub=''}={}){
 const q=String(query).trim().toLocaleLowerCase();
 return entries.filter(e=>(!element||e.material.elements.includes(element))&&(!hub||e.material.existing_hub_id===hub)&&(!q||[e.material.label,e.title,e.doi,e.method_label].join(' ').toLocaleLowerCase().includes(q)));
}
function node(doc,tag,value,cls){const n=doc.createElement(tag);if(value!==undefined)n.textContent=value;if(cls)n.className=cls;return n;}
function link(doc,label,url){const n=node(doc,'a',label);n.href=url;return n;}
function locs(doc,rows){const ul=node(doc,'ul',undefined,'locators');for(const r of rows)ul.append(node(doc,'li',`p. ${r.page} · ${r.section}`));return ul;}
function listSection(doc,title,rows,empty){const s=node(doc,'section');s.append(node(doc,'h3',title));if(!rows.length)s.append(node(doc,'p',empty));else{const ul=node(doc,'ul');for(const row of rows)ul.append(node(doc,'li',row));s.append(ul);}return s;}
export function renderPreliminary(host,view,filters={}){
 host.replaceChildren();const doc=host.ownerDocument;
 if(view.status!=='ready'){host.append(node(doc,'p','Preliminary contributions are unavailable. No unvalidated contribution is shown.','unavailable'));return;}
 const shown=filterEntries(view.entries,filters);
 host.append(node(doc,'p',`${shown.length} of ${view.entries.length} preliminary sources shown · Separate from reviewed dataset and verified pair counts`,'summary'));
 if(!shown.length){host.append(node(doc,'p',view.entries.length?'No preliminary contributions match these filters.':'No preliminary contributions have been published yet.','empty'));return;}
 for(const e of shown){
  const card=node(doc,'article',undefined,'contribution');card.id=e.source_id;
  card.append(node(doc,'p','PRELIMINARY · INDEPENDENT AUDIT PENDING','badge'),node(doc,'h2',e.title),node(doc,'p',e.citation,'citation'));
  const links=node(doc,'div',undefined,'card-links'),doi=link(doc,'Source DOI ↗',doiURL(e.doi));doi.target='_blank';doi.rel='noopener noreferrer';links.append(doi,link(doc,'Link to this contribution','#'+e.source_id));
  if(e.material.existing_hub_id!==null)links.append(link(doc,'Reviewed material page →','material.html?id='+encodeURIComponent(e.material.existing_hub_id)));
  card.append(links,node(doc,'p',e.material.label+' · Elements: '+e.material.elements.join(', '),'elements'),node(doc,'h3',e.method_label),node(doc,'p',e.scope,'scope'));
  card.append(node(doc,'p',`${e.document_role==='main'?'Main article':'Supporting information'} · Inspected pages ${e.inspected_pages.join(', ')} of ${e.source_pages}. Extractor checked the source; independent scientific audit pending. Accuracy unmeasured; training excluded.`,'provenance'));
  card.append(node(doc,'h3','Precursors'));const scroll=node(doc,'div',undefined,'table-scroll'),table=node(doc,'table'),thead=node(doc,'thead'),tr=node(doc,'tr');
  for(const title of ['Precursor / input','Reported amount','Role and source']){const th=node(doc,'th',title);th.scope='col';tr.append(th);}thead.append(tr);table.append(thead);const tbody=node(doc,'tbody');
  for(const p of e.precursors){const row=node(doc,'tr'),source=node(doc,'td',p.role);source.append(locs(doc,p.locators));row.append(node(doc,'td',p.name),node(doc,'td',p.amount===null?'Not reported':p.amount),source);tbody.append(row);}table.append(tbody);scroll.append(table);card.append(scroll);
  card.append(node(doc,'h3','Ordered synthesis protocol'));const protocol=node(doc,'ol',undefined,'protocol');
  for(const o of e.operations){const item=node(doc,'li');item.append(node(doc,'h4',o.action));if(o.conditions.length){const ul=node(doc,'ul',undefined,'conditions');for(const c of o.conditions)ul.append(node(doc,'li',c.parameter+': '+c.reported));item.append(ul);}item.append(locs(doc,o.locators));protocol.append(item);}card.append(protocol);
  card.append(node(doc,'h3','Linked structural outcome'));const outcome=node(doc,'div',undefined,'outcome');outcome.append(node(doc,'strong',e.outcome.sample_label),node(doc,'p',e.outcome.link_basis),locs(doc,e.outcome.locators));
  for(const d of e.outcome.descriptors){const item=node(doc,'div',undefined,'descriptor');item.append(node(doc,'strong',d.kind[0].toUpperCase()+d.kind.slice(1)),node(doc,'p',d.reported),node(doc,'p','Technique: '+d.technique,'provenance'),locs(doc,d.locators));outcome.append(item);}card.append(outcome);
  const limits=node(doc,'div',undefined,'limits');limits.append(listSection(doc,'Missing information',e.missing_fields,'No additional missing fields listed for this limited scope.'),listSection(doc,'Deferred coverage',e.deferred,'No additional deferred items listed.'));card.append(limits,node(doc,'p','Variant coverage: '+e.extraction.omitted_variants,'scope'));
  const provenance=node(doc,'details',undefined,'provenance');provenance.append(node(doc,'summary','Document and evidence identifiers'),node(doc,'p','Document SHA-256: '+e.document_sha256),node(doc,'p','Evidence fingerprint: '+e.evidence_fingerprint));card.append(provenance);host.append(card);
 }
}
export async function mountPreliminary(doc,{fetcher=globalThis.fetch,search=globalThis.location?.search||'',hash=globalThis.location?.hash||''}={}){
 const host=doc.getElementById('preliminary-results'),form=doc.getElementById('preliminary-filters'),query=doc.getElementById('preliminary-search'),element=doc.getElementById('preliminary-element'),clear=doc.getElementById('preliminary-clear'),context=doc.getElementById('preliminary-filter-context');
 const params=new URLSearchParams(search);let hub=params.get('hub')||'';query.value=(params.get('material')||'').slice(0,200);
 try{
  const response=await fetcher('data/preliminary-synthesis.json',{credentials:'omit'});if(!response.ok)throw Error('Unavailable');const view=preparePreliminary(await response.json());if(view.status!=='ready')throw Error('Invalid public shape');
  for(const symbol of [...new Set(view.entries.flatMap(e=>e.material.elements))].sort()){const option=node(doc,'option',symbol);option.value=symbol;element.append(option);}
  const selected=params.get('element')||'';if(SYMBOLS.has(selected)){if(!view.entries.some(e=>e.material.elements.includes(selected))){const option=node(doc,'option',selected);option.value=selected;element.append(option);}element.value=selected;}
  const refresh=()=>{context.textContent=hub?'Filtered to this material hub; clear filters to see all preliminary sources.':'';renderPreliminary(host,view,{query:query.value,element:element.value,hub});};
  form.addEventListener('submit',event=>event.preventDefault());query.addEventListener('input',refresh);element.addEventListener('change',refresh);clear.addEventListener('click',()=>{hub='';query.value='';element.value='';refresh();});refresh();
  if(ID.test(hash.slice(1))){const target=doc.getElementById(hash.slice(1));target?.scrollIntoView?.({block:'start'});}
 }catch{renderPreliminary(host,{status:'unavailable',entries:[]});}finally{host.setAttribute('aria-busy','false');}
}
if(typeof document!=='undefined'&&document.getElementById('preliminary-results'))mountPreliminary(document);
