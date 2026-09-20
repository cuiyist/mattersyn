const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);if(cls)n.className=cls;return n;};
const human=x=>String(x??'').replaceAll('_',' ');
function describe(value){
 if(value===null||value===undefined)return 'Not reported';
 if(typeof value!=='object')return String(value);
 if(Array.isArray(value))return value.map(describe).join(' · ');
 return Object.entries(value).map(([key,val])=>human(key)+': '+describe(val)).join('; ');
}
function sourceLabel(e){return [e.source_id,e.document_role||e.document,e.pdf_page?'PDF page '+e.pdf_page:null,e.printed_page?'printed page '+e.printed_page:null,e.locator].filter(Boolean).join(' · ');}
function presentationFacts(facts){
 const rows=[],shared=new Map();
 for(const fact of facts){
  if(fact.canonical_material_id&&fact.basis==='reagent_specification'){
   const {id,canonical_record_id,json_pointer,...specification}=fact,key=JSON.stringify(specification);
   const existing=shared.get(key);if(existing){existing.records.add(canonical_record_id);continue;}
   const row={fact,records:new Set([canonical_record_id])};shared.set(key,row);rows.push(row);
  }else rows.push({fact,records:new Set()});
 }
 return rows;
}

export function sourceItemCard(item,{compact=false,sourceDoi=null,sourceId=null}={}){
 const card=el(compact?'details':'article',undefined,'source-evidence-item');card.dataset.evidenceItem=item.id;card.id='evidence-'+item.id;
 const heading=el(compact?'summary':'h4',item.title||human(item.id));card.append(heading);
 if(item.claim_type)card.append(el('span',human(item.claim_type),'source-claim-kind'));
 for(const paragraph of item.paragraphs||[item.text])if(paragraph)card.append(el('p',describe(paragraph)));
 const scope=item.sample_scope;
 if(scope){const parts=[scope.formulations?.length?'Formulations: '+scope.formulations.join(', '):null,scope.state&&scope.state!=='Not assigned'?'State: '+human(scope.state):null,scope.scope_kind?'Scope: '+human(scope.scope_kind):null,scope.link_limit];card.append(el('p',parts.filter(Boolean).join(' · '),'source-sample-scope'));}
 if(item.facts?.length){const list=el('dl',undefined,'source-facts');for(const {fact,records} of presentationFacts(item.facts)){const row=el('div');row.append(el('dt',fact.label||fact.name||'Source fact'));const value=(fact.approximate?'≈ ':'')+describe(fact.value)+(fact.unit?' '+fact.unit:'');row.append(el('dd',value));for(const key of ['status','qualifier','basis'])if(fact[key])row.append(el('small',human(fact[key])));if(fact.evidence?.length)row.append(el('small',fact.evidence.map(sourceLabel).join('; ')));if(records.size>1)row.append(el('small','Source specification shared by '+records.size+' linked records.'));list.append(row);}card.append(list);}
 if(item.notes?.length){const list=el('ul');for(const note of item.notes)list.append(el('li',describe(note)));card.append(list);}
 for(const asset of item.original_assets||[]){if(!asset.public_asset)continue;const a=el('a',asset.label||'Open original source excerpt');a.href=new URL(asset.public_asset,import.meta.url);a.target='_blank';a.rel='noopener';card.append(a);}
 const evidence=item.evidence||[];if(evidence.length){const sources=el('p',undefined,'source-evidence-locator');for(const [i,e] of evidence.entries()){if(i)sources.append(document.createTextNode('; '));const label=sourceLabel(e);if(sourceDoi&&(!e.source_id||e.source_id===sourceId)){const a=el('a',label);a.href='https://doi.org/'+sourceDoi;sources.append(a);}else sources.append(document.createTextNode(label));}card.append(sources);}else if(item.source_locators?.length)card.append(el('small',describe(item.source_locators),'source-evidence-locator'));
 if(item.canonical_links?.length){const links=el('details',undefined,'source-record-provenance'),seen=new Set();links.append(el('summary','Linked records and evidence locations'));for(const l of item.canonical_links){const id=typeof l==='string'?l:l.record_id,key=id+'|'+(l.json_pointer||'');if(!id||seen.has(key))continue;seen.add(key);const row=el('p'),a=el('a',l.label||human(id)+' →');a.href=new URL('records/'+id+'.html',import.meta.url);row.append(a);if(l.relation)row.append(el('small',l.relation));if(l.json_pointer){const data=el('a','Record JSON · '+l.json_pointer);data.href=new URL('data/records/'+id+'.json',import.meta.url);row.append(data);}links.append(row);}card.append(links);}
 return card;
}

export function mountSourceSections(host,review){
 if(!host||!review.reader_sections?.length)return;host.replaceChildren();
 host.append(el('h2','Source evidence and interpretation'),el('p','Reported observations, supporting procedures and author models retain their own specimen and treatment scope. Contextual evidence is not an additional synthesis experiment.','guide-notice'));
 const label=el('label','Find evidence in this paper','source-evidence-search'),input=el('input');input.type='search';input.placeholder='Chemical, condition, sample, technique or interpretation';label.append(input);host.append(label);const count=el('p',undefined,'source-evidence-count');count.setAttribute('aria-live','polite');host.append(count);
 const blocks=[];
 for(const section of review.reader_sections){const group=el('section',undefined,'source-evidence-group');group.id='source-'+section.id;group.append(el('h3',section.title));const cards=[];for(const item of section.items||[]){const card=sourceItemCard(item,{compact:true,sourceDoi:review.doi,sourceId:review.paper_id||review.source_id});group.append(card);cards.push({card,text:card.textContent.toLowerCase()});}if(cards.length){host.append(group);blocks.push({group,cards});}}
 const filter=()=>{const query=input.value.trim().toLowerCase();let visible=0,total=0;for(const {group,cards} of blocks){let matched=0;for(const c of cards){const show=!query||c.text.includes(query);c.card.hidden=!show;total++;if(show){visible++;matched++;}}group.hidden=!matched;}count.textContent=visible+' of '+total+' source evidence items';};input.addEventListener('input',filter);filter();
}
