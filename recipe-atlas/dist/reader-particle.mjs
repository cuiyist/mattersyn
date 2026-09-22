// Proposed new dist module; author proposal only. No coordinate/phase inference.
import {el,link,badge,recordURL,disclosure} from './reader-utils.mjs';

const knownStatus=new Set(['reported','author_derived','calculated','inherited']);
const text=v=>v===null||v===undefined?'':typeof v==='object'?JSON.stringify(v):String(v);
const sourceRecord=(context,fallback)=>context.record_id||context.source?.data_path?.match(/(?:^|\/)records\/([^/]+)\.json$/)?.[1]||fallback;

export function particleGroups(r,presentation={}){
 const groups=new Map();
 const ensure=(recordId,sampleId,label)=>{const key=recordId+':'+sampleId;if(!groups.has(key))groups.set(key,{key,recordId,sampleId,label:label||sampleId,facts:[],context:null});return groups.get(key);};
 // Seed from complete contexts, not only non-null fact rows. Unknown is visible.
 for(const context of presentation.productContexts||[])ensure(sourceRecord(context,r.record_id),context.sample_id,context.label).context=context;
 for(const product of r.products||[]){const g=ensure(r.record_id,product.sample_id,product.source_sample_label||product.sample_id);g.product=product;}
 for(const fact of presentation.allProductFacts||presentation.productFacts||[]){const g=ensure(fact.record_id||r.record_id,fact.sample_id||'unassigned',fact.scope);g.facts.push(fact);}
 if(!groups.size)ensure(r.record_id,'unassigned','Specimen not assigned');
 return groups;
}

export function particleDescriptor(group){
 const observed=kind=>{
  const fact=group.facts.find(f=>f.kind===kind&&knownStatus.has(f.status)&&text(f.value));
  if(fact)return text(fact.value);
  const field=group.product?.[kind];return field&&knownStatus.has(field.status)?text(field.value):'';
 };
 const composition=observed('composition'),morphology=observed('morphology');
 // Never infer morphology, layers, dopants or phase from the route formula.
 // Only unambiguous positive morphology words in this specimen's field qualify.
 const qualified=/\b(no|not|unknown|unresolved|unassigned|varied|mixture|mixed|versus|rather than|or)\b/i.test(morphology);
 const shape=!qualified&&/\b(spherical|spheres?|round)\b/i.test(morphology)?'sphere':!qualified&&/\b(cubes?|cuboidal)\b/i.test(morphology)?'cube':!qualified&&/\b(rods?|nanorods?|nanowires?)\b/i.test(morphology)?'rod':'neutral';
 return {composition:composition||'Composition not assigned',scope:group.label||group.sampleId,
         morphology,shape,caption:shape==='neutral'?'Specimen identity schematic; shape, layers and dopant positions are not assigned.':'Reported specimen morphology illustrated schematically; not to scale or an atomic reconstruction.'};
}

function particleArt(descriptor){
 const host=el('div',undefined,'reader-product-illustration');let path;
 if(descriptor.shape==='sphere')path='<circle cx="200" cy="150" r="95" fill="#91bac9"/><ellipse cx="174" cy="115" rx="52" ry="35" fill="white" opacity=".15"/>';
 else if(descriptor.shape==='cube')path='<path d="M100 99L210 49L302 102L192 155Z" fill="#b7dce2"/><path d="M100 99L192 155V269L100 209Z" fill="#80aebd"/><path d="M192 155L302 102V212L192 269Z" fill="#6092a9"/>';
 else if(descriptor.shape==='rod')path='<path d="M73 149L283 52L327 81L117 180Z" fill="#badbe1"/><path d="M73 149L117 180V230L73 196Z" fill="#779fb1"/><path d="M117 180L327 81V129L117 230Z" fill="#5890a7"/>';
 else path='<rect x="95" y="65" width="210" height="175" rx="24" fill="#edf3f6" stroke="#8badbd" stroke-width="2" stroke-dasharray="6 6"/><text x="200" y="156" text-anchor="middle" fill="#54778c" font-size="19">Selected specimen</text>';
 host.innerHTML='<svg viewBox="0 0 400 310" role="img" aria-label="'+(descriptor.shape==='neutral'?'Specimen placeholder; shape unassigned':'Illustrative reported specimen morphology')+'">'+path+'</svg>';
 return host;
}

export function mountParticleContext(panel,r,presentation={}){
 const groups=particleGroups(r,presentation),choose=el('select',undefined,'reader-method-select'),display=el('div');choose.setAttribute('aria-label','Particle specimen or reported context');
 for(const [id,g] of groups){const option=el('option',g.label||g.sampleId);option.value=id;choose.append(option);}
 const wanted=r.record_id+':'+presentation.primary_product?.default_sample_id;if(groups.has(wanted))choose.value=wanted;
 panel.append(choose,display);
 function show(){const group=groups.get(choose.value)||groups.values().next().value,d=particleDescriptor(group),layout=el('div',undefined,'reader-product-layout'),copy=el('div');
  copy.append(badge('Illustration','reference'),el('h3',d.composition),el('p',d.scope,'reader-note'),el('p',d.caption,'reader-note'));
  const dl=el('dl',undefined,'reader-product-facts');for(const f of group.facts.slice(0,5)){const row=el('div');row.append(el('dt',f.label),el('dd',text(f.value)));if(f.scope)row.append(el('small',f.scope));if(f.qualifier)row.append(el('small',f.qualifier));dl.append(row);}
  if(!dl.children.length)dl.append(el('p','No non-null composition, phase, morphology or size facts are assigned to this context. Its source scope is retained.','reader-note'));
  if(group.facts.length>5){const extra=el('dl',undefined,'reader-product-facts');for(const f of group.facts.slice(5)){const row=el('div');row.append(el('dt',f.label),el('dd',text(f.value)));if(f.qualifier)row.append(el('small',f.qualifier));extra.append(row);}copy.append(disclosure('Additional specimen observations',extra));}copy.append(dl,link('Complete specimen evidence →',recordURL(group.recordId)+'#structures','reader-data-link'));
  const readableNotes=(group.context?.notes||group.product?.notes||[]).filter(n=>typeof n==='string'&&!/^Source context object:/.test(n));if(readableNotes.length)copy.append(disclosure('Specimen scope',...readableNotes.map(n=>el('p',n))));
  layout.append(particleArt(d),copy);display.replaceChildren(layout);
 }
 choose.onchange=show;show();return {groups,choose,display};
}
