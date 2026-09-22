// Source-bound morphology illustrations; never measured coordinates or training labels.
import {el,link,badge,recordURL,disclosure,siteURL} from './reader-utils.mjs';
import {particleShapeSVG,particleShapeInfo} from './particle-shapes.mjs?v=0.34.1';

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

export function classifyMorphology(value){
 const m=text(value).toLowerCase();
 if(!m||/\b(unknown|unresolved|unassigned|not determined)\b/.test(m))return 'neutral';
 if(/\b(proposed|damage|not demonstrated|non[ -]spherical)\b/.test(m))return 'neutral';
 if(/\b(spher\w*|round)\b/.test(m)&&/\b(cubic|cube\w*)\b/.test(m))return 'neutral';
 if(/\b(?:no|not|without)\b(?:[\s-]+\w+){0,3}[\s-]+(?:spher\w*|round|cub\w*|rods?|nanorods?|islands?|plates?|shell\w*|stars?)\b/.test(m))return 'neutral';
 if(/\b(?:spher\w*|cub\w*|rods?|islands?)\s+(?:(?:were|are)\s+)?(?:not|never)\s+(?:observed|confirmed)/.test(m))return 'neutral';
 const primitiveShapes=[/\b(spher\w*|round)\b/,/\b(cubic shaped|cubes?|cuboidal)\b/,/\b(nanorods?|rods?|nanowires?)\b/,/\b(platelets?|nanoplates?)\b/,/\b(star\w*|octapods?)\b/].filter(re=>re.test(m));
 if(primitiveShapes.length>1&&!/assembl|embedded|nanotube|core[\s/–-]+shell/.test(m))return 'neutral';
 if(/nanotubes?/.test(m))return 'nanotube-supported';
 if(/embedded|confined within|polymer microparticles/.test(m))return 'matrix';
 if(/core[\s/–-]+shell/.test(m))return 'core-shell';
 if(/assembl/.test(m))return /wire/.test(m)?'wire-assembly':/spher/.test(m)?'sphere-assembly':'assembly';
 if(/islands?/.test(m))return 'islands';
 if(/thin film|base\/composite/.test(m))return 'layered-film';
 if(/truncated octahedr/.test(m))return 'truncated-octahedron';
 if(/truncated.*star|smoothed.*star/.test(m))return 'truncated-star';
 if(/octapod|star/.test(m))return 'star';
 if(/belts?/.test(m))return 'belt';
 if(/platelets?|nanoplates?|sheets?/.test(m))return 'platelet';
 if(/ellipsoid|oval|oblate|prolate/.test(m))return 'ellipsoid';
 if(/\b(nanorods?|rods?|nanowires?)\b/.test(m))return 'rod';
 if(/\b(cubes?|cuboidal|cubic shaped)\b/.test(m))return 'cube';
 if(/\b(spherical|spheres?|round)\b/.test(m))return 'sphere';
 if(/irregular|anisotropic/.test(m))return 'irregular';
 return 'neutral';
}

export function particleDescriptor(group,interpretations={}){
 const observed=kind=>{
  const fact=group.facts.find(f=>f.kind===kind&&knownStatus.has(f.status)&&text(f.value));
  if(fact)return text(fact.value);
  const field=group.product?.[kind];return field&&knownStatus.has(field.status)?text(field.value):'';
 };
 const composition=observed('composition'),morphology=observed('morphology');
 // Curated interpretations join only the selected source record and sample.
 // A material formula or another specimen's TEM cannot supply this shape.
 const inferred=interpretations[group.recordId+':'+group.sampleId];
 const shape=inferred?.shape||classifyMorphology(morphology);
 const sourceFact=group.facts.find(f=>f.kind==='morphology'&&knownStatus.has(f.status));
 return {composition:composition||'Composition not assigned',scope:group.label||group.sampleId,
         morphology,shape,inferred,sourceFact,
         caption:shape==='neutral'?'The source evidence does not yet support a specific morphology illustration for this specimen.':inferred?.rationale||'Schematic interpretation of the source description. Geometry and colors are illustrative; not to scale or an atomic reconstruction.'};
}

function particleArt(descriptor){
 const host=el('div',undefined,'reader-product-illustration');
 host.innerHTML=particleShapeSVG(descriptor.shape);
 const info=particleShapeInfo(descriptor.shape);
 if(info.legend?.length){const legend=el('div',undefined,'element-legend');for(const item of info.legend){const span=el('span'),dot=el('i');dot.style.background=item.color;span.append(dot,document.createTextNode(item.label));legend.append(span);}host.append(legend);}
 return host;
}

let interpretationsPromise;
export async function mountParticleContext(panel,r,presentation={}){
 interpretationsPromise??=fetch(siteURL('data/reader-morphology-interpretations.json'),{cache:'no-store'}).then(response=>{if(!response.ok)throw Error('Morphology interpretation file unavailable');return response.json();}).then(data=>data.entries);
 let interpretations={};try{interpretations=await interpretationsPromise;}catch(error){console.warn(error.message);}
 if(!panel.isConnected)return;
 const groups=particleGroups(r,presentation),choose=el('select',undefined,'reader-method-select'),display=el('div');choose.setAttribute('aria-label','Particle specimen or reported context');
 for(const [id,g] of groups){const option=el('option',g.label||g.sampleId);option.value=id;choose.append(option);}
 const wanted=r.record_id+':'+presentation.primary_product?.default_sample_id;
 const illustrated=[...groups.values()].filter(g=>particleDescriptor(g,interpretations).shape!=='neutral');
 const preferred=illustrated.find(g=>g.key===wanted)||illustrated.find(g=>g.recordId===r.record_id&&(g.context?.recipe_link||g.product?.recipe_link)==='explicit')||illustrated[0];
 if(preferred)choose.value=preferred.key;else if(groups.has(wanted))choose.value=wanted;
 panel.append(choose,display);
 function show(){const group=groups.get(choose.value)||groups.values().next().value,d=particleDescriptor(group,interpretations),layout=el('div',undefined,'reader-product-layout'),copy=el('div');
  copy.append(badge(d.inferred?'Inferred morphology':'Morphology illustration','reference'),el('h3',d.inferred?.label||d.composition),el('p',d.scope,'reader-note'),el('p',d.caption,'reader-note'));
  if(d.inferred)copy.append(el('p','Interpretive schematic · dimensions, interfaces and atomic positions are not reconstructed.','reader-note'));
  const basis=disclosure('Illustration basis and limitations');
  if(d.morphology)basis.append(el('p','Source description: '+d.morphology));
  for(const item of d.inferred?.evidence||d.sourceFact?.source_locator||[]){const target=item.record_id||group.recordId;basis.append(link([item.source_id,item.locator].filter(Boolean).join(' · ')||'Source evidence →',recordURL(target)+'#structures','reader-data-link'));}
  for(const note of d.inferred?.limitations||[])basis.append(el('p',note));
  if(d.shape!=='neutral')basis.append(el('p','The drawing summarizes source evidence. It is not a micrograph, a measured coordinate model, or an exact structure–recipe training label.'));
  if(basis.children.length>1)copy.append(basis);
  const dl=el('dl',undefined,'reader-product-facts');for(const f of group.facts.slice(0,5)){const row=el('div');row.append(el('dt',f.label),el('dd',text(f.value)));if(f.scope)row.append(el('small',f.scope));if(f.qualifier)row.append(el('small',f.qualifier));dl.append(row);}
  if(!dl.children.length)dl.append(el('p','No non-null composition, phase, morphology or size facts are assigned to this context. Its source scope is retained.','reader-note'));
  if(group.facts.length>5){const extra=el('dl',undefined,'reader-product-facts');for(const f of group.facts.slice(5)){const row=el('div');row.append(el('dt',f.label),el('dd',text(f.value)));if(f.qualifier)row.append(el('small',f.qualifier));extra.append(row);}copy.append(disclosure('Additional specimen observations',extra));}copy.append(dl,link('Complete specimen evidence →',recordURL(group.recordId)+'#structures','reader-data-link'));
  const readableNotes=(group.context?.notes||group.product?.notes||[]).filter(n=>typeof n==='string'&&!/^Source context object:/.test(n));if(readableNotes.length)copy.append(disclosure('Specimen scope',...readableNotes.map(n=>el('p',n))));
  layout.append(particleArt(d),copy);display.replaceChildren(layout);
 }
 choose.onchange=show;show();return {groups,choose,display};
}
