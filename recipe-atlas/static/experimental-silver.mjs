const SCHEMA='mattersyn-experimental-silver/1';
const HASH=/^[a-f0-9]{64}$/;
const ID=/^[A-Za-z0-9][A-Za-z0-9_.:+/() -]{0,119}$/;
const PATH=/(?:[A-Za-z]:[\\/]|\\\\|file:\/\/|\/Users\/|\/home\/|\/tmp\/)/;
const FIELDS=new Set(['reaction_temperature','duration','precursor_amount','solvent_volume','concentration','particle_diameter','core_diameter','shell_thickness','hydrodynamic_diameter','crystallite_size','phase','morphology','precursor_identity']);
const UNITS=new Set(['°C','K','s','min','h','d','mol','mmol','µmol','g','mg','L','mL','µL','mol/L','M','mM','nm','µm','Å']);
const TOP=['schema','status','calibration_state','measured_accuracy','training_ready','publication_enabled','gold_count_contribution','calibrated_silver_count_contribution','structure_pair_count_contribution','completed_paper_count_contribution','usable_complete_recipes','distinct_sources','entries'];
const ENTRY=['source_id','doi','title','citation','url','document_sha256','tier','scientific_review','calibration_state','precision','recall','training_ready','training_weight','excluded_from','source_scope','extraction','fields','withheld_claim_count','limitations'];
const FIELD=['recipe_id','sample_id','slot_id','field','value','unit','document_id','page','link_page','technique','status','mechanical_checks','training_ready','training_weight'];
const SCOPE=['role','source_pages','input_pages','full_paper_extraction','figures_visually_reviewed','si_reviewed'];
const EXTRACT=['model','model_sha256','prompt_sha256','pipeline_sha256','validator_sha256','passes','model_agreement_claimed','chunks','maximum_claims_per_chunk','configuration_binding','chunk_configurations'];
const keys=(x,allowed)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===allowed.length&&allowed.every(k=>Object.hasOwn(x,k));
const text=(x,n=1000)=>typeof x==='string'&&x.length>0&&x.length<=n&&!PATH.test(x)&&!/[\x00-\x1f]/.test(x);
const id=x=>text(x,120)&&ID.test(x);
const integer=x=>Number.isInteger(x)&&x>=0;
const positive=x=>integer(x)&&x>0;
export function prepareExperimental(data){
  const empty={status:'unavailable',entries:[],distinct_sources:0};
  if(!keys(data,TOP)||data.schema!==SCHEMA||data.status!=='experimental_machine_extraction_not_reviewed'||data.calibration_state!=='unmeasured'||data.measured_accuracy!==null||data.training_ready!==false||data.publication_enabled!==false||!['gold_count_contribution','calibrated_silver_count_contribution','structure_pair_count_contribution','completed_paper_count_contribution','usable_complete_recipes'].every(k=>data[k]===0)||!Array.isArray(data.entries)||!positive(data.distinct_sources)||data.entries.length!==data.distinct_sources)return empty;
  const ids=new Set(),dois=new Set();
  for(const e of data.entries){
    if(!keys(e,ENTRY)||!id(e.source_id)||!text(e.doi,120)||!/^10\.\d{4,9}\/[^\s?#]+$/.test(e.doi)||e.url!=='https://doi.org/'+e.doi||!text(e.title,500)||!text(e.citation)||!HASH.test(e.document_sha256)||e.tier!=='experimental_silver'||e.scientific_review!=='not_performed'||e.calibration_state!=='unmeasured'||e.precision!==null||e.recall!==null||e.training_ready!==false||e.training_weight!==0||!integer(e.withheld_claim_count))return empty;
    if(ids.has(e.source_id)||dois.has(e.doi.toLowerCase()))return empty;ids.add(e.source_id);dois.add(e.doi.toLowerCase());
    if(JSON.stringify(e.excluded_from)!==JSON.stringify(['gold','calibrated_silver','training_exports','gold_evaluation','structure_recipe_pair_counts'])||!Array.isArray(e.limitations)||!e.limitations.length||!e.limitations.every(s=>text(s)))return empty;
    const s=e.source_scope,x=e.extraction;
    if(!keys(s,SCOPE)||s.role!=='main'||!positive(s.source_pages)||!Array.isArray(s.input_pages)||!s.input_pages.length||new Set(s.input_pages).size!==s.input_pages.length||!s.input_pages.every(p=>positive(p)&&p<=s.source_pages)||s.full_paper_extraction!==false||s.figures_visually_reviewed!==false||s.si_reviewed!==false)return empty;
    if(!keys(x,EXTRACT)||!text(x.model,80)||!['model_sha256','prompt_sha256','pipeline_sha256','validator_sha256'].every(k=>HASH.test(x[k]))||x.passes!==1||x.model_agreement_claimed!==false||!positive(x.chunks)||x.maximum_claims_per_chunk!==4||x.configuration_binding!=='aggregate_of_chunk_fingerprints'||!Array.isArray(x.chunk_configurations)||x.chunk_configurations.length!==x.chunks)return empty;
    if(!x.chunk_configurations.every(c=>keys(c,['input_pages','input_sha256','prompt_sha256','pipeline_sha256'])&&['input_sha256','prompt_sha256','pipeline_sha256'].every(k=>HASH.test(c[k]))&&Array.isArray(c.input_pages)&&c.input_pages.length&&c.input_pages.every(p=>s.input_pages.includes(p))))return empty;
    if(!Array.isArray(e.fields)||!e.fields.length||e.fields.length>x.chunks*4)return empty;
    const slots=new Set();
    for(const f of e.fields){
      if(!keys(f,FIELD)||!id(f.recipe_id)||!(f.sample_id===null||id(f.sample_id))||!id(f.slot_id)||!FIELDS.has(f.field)||f.document_id!=='main'||!s.input_pages.includes(f.page)||!s.input_pages.includes(f.link_page)||f.status!=='machine_extracted_not_reviewed'||f.mechanical_checks!=='passed'||f.training_ready!==false||f.training_weight!==0||!(f.technique===null||text(f.technique,80)))return empty;
      if(typeof f.value==='number'){if(!Number.isFinite(f.value)||!UNITS.has(f.unit))return empty;}else if(!text(f.value,120)||f.unit!==null)return empty;
      const key=JSON.stringify([f.recipe_id,f.sample_id,f.slot_id,f.field]);if(slots.has(key))return empty;slots.add(key);
    }
  }
  return {status:'ready',distinct_sources:data.distinct_sources,entries:structuredClone(data.entries)};
}
function el(doc,tag,textValue,className){const node=doc.createElement(tag);if(textValue!==undefined)node.textContent=textValue;if(className)node.className=className;return node;}
export function renderExperimental(host,view){
  host.replaceChildren();const doc=host.ownerDocument;
  if(view.status!=='ready'){host.append(el(doc,'p','Experimental evidence is unavailable.'));return;}
  host.append(el(doc,'p',`${view.distinct_sources} source evidence ${view.distinct_sources===1?'note':'notes'} · 0 complete recipes · 0 synthesis–structure pairs`,'summary'));
  for(const entry of view.entries){
    const card=el(doc,'article');card.append(el(doc,'p','Experimental silver · Machine-extracted · Not reviewed','badge'));card.append(el(doc,'h2',entry.title));
    card.append(el(doc,'p',entry.citation));const link=el(doc,'a','Open source DOI');link.href=entry.url;link.target='_blank';link.rel='noopener noreferrer';card.append(link);
    card.append(el(doc,'p','Accuracy unmeasured. This is partial automatically extracted recipe evidence, not a complete laboratory protocol. It contributes no gold, calibrated-silver, training-ready or synthesis–structure-pair records.','notice'));
    const s=entry.source_scope;card.append(el(doc,'p',`Input pages: ${s.input_pages.join(', ')} of ${s.source_pages}. At most four fields per extraction call; a page may be processed in multiple calls. Completeness is unassessed; figures and SI were not reviewed.`));
    const table=el(doc,'table'),head=el(doc,'tr');for(const label of ['Source method label','Extracted field','Value','Page'])head.append(el(doc,'th',label));table.append(head);
    for(const f of entry.fields){const row=el(doc,'tr');for(const val of [f.recipe_id,`${f.field.replaceAll('_',' ')} (${f.slot_id})`,`${f.value}${f.unit?' '+f.unit:''}`,String(f.page)])row.append(el(doc,'td',val));table.append(row);}card.append(table);
    card.append(el(doc,'p',`${entry.withheld_claim_count} claims withheld from this displayed extraction batch. Displayed values passed automatic quote/value/unit checks; that does not establish scientific correctness or semantic sample linkage.`));
    for(const note of entry.limitations)card.append(el(doc,'p',note));host.append(card);
  }
}
export async function mountExperimental(host,{fetcher=globalThis.fetch}={}){
  try{const response=await fetcher('data/experimental-silver.json',{credentials:'omit'});if(!response.ok)throw Error('Unavailable');renderExperimental(host,prepareExperimental(await response.json()));}catch{renderExperimental(host,{status:'unavailable'});}
}
