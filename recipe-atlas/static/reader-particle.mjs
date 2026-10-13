// Source-bound morphology illustrations; never measured coordinates or training labels.
import {el,link,badge,recordURL,disclosure,siteURL} from './reader-utils.mjs?v=0.41.7';
import {particleShapeSVG,particleShapeInfo} from './particle-shapes.mjs?v=0.40.5';
import {scopedProductArt} from './reader-scoped-product-art.mjs';

const knownStatus=new Set(['reported','author_derived','calculated','inherited']);
const text=v=>v===null||v===undefined?'':typeof v==='object'?JSON.stringify(v):String(v);
const sourceRecord=(context,fallback)=>context.record_id||context.source?.data_path?.match(/(?:^|\/)records\/([^/]+)\.json$/)?.[1]||fallback;
// Zhong's branched specimens cannot be represented by the straight-rod primitive.
const pendingZhongBranches=(value,recordId)=>recordId==='zhong2007-cdte-cdse-jp0709407-sequential-growth-series'&&/\bmultiple[- ](?:armed|branched)\s+rods?\b/.test(text(value).toLowerCase());

function sameCanonicalProductFact(fact,group,kind){
 const field=group.product?.[kind],source=fact.source;
 if(!field||fact.kind!=='product_fact'||fact.record_id!==group.recordId||fact.sample_id!==group.sampleId||
  source?.data_path!=='data/records/'+group.recordId+'.json'||fact.status!==field.status||text(fact.value)!==text(field.value))return false;
 const pointer='/products/'+group.productIndex+'/'+kind;
 if(source?.json_pointer!==pointer&&source?.json_pointer!==pointer+'/value')return false;
 const inputHash=group.context?.source?.input_sha256;
 if(inputHash&&source.input_sha256!==inputHash)return false;
 if(JSON.stringify(fact.source_locator||[])!==JSON.stringify(field.evidence||[]))return false;
 return !field.note||text(fact.qualifier).includes(text(field.note));
}

export function particleGroups(r,presentation={}){
 const groups=new Map();
 const ensure=(recordId,sampleId,label)=>{const key=recordId+':'+sampleId;if(!groups.has(key))groups.set(key,{key,recordId,sampleId,label:label||sampleId,facts:[],context:null});return groups.get(key);};
 // Seed from complete contexts, not only non-null fact rows. Unknown is visible.
 for(const context of presentation.productContexts||[])ensure(sourceRecord(context,r.record_id),context.sample_id,context.label).context=context;
 for(const [productIndex,product] of (r.products||[]).entries()){const g=ensure(r.record_id,product.sample_id,product.source_sample_label||product.sample_id);g.product=product;g.productIndex=productIndex;}
 for(const fact of presentation.allProductFacts||presentation.productFacts||[]){const g=ensure(fact.record_id||r.record_id,fact.sample_id||'unassigned',fact.scope);g.facts.push(fact);}
 // Some scoped Readers list measurements only. Retain the canonical product's
 // qualitative observations without borrowing another record or specimen.
 for(const group of groups.values())for(const kind of ['composition','phase','morphology','surface']){
  const field=group.product?.[kind];
  if(!field||!knownStatus.has(field.status)||!text(field.value))continue;
  if(group.facts.some(f=>f.kind===kind&&knownStatus.has(f.status)&&text(f.value)||sameCanonicalProductFact(f,group,kind)))continue;
  group.facts.push({kind,label:kind[0].toUpperCase()+kind.slice(1),value:field.value,status:field.status,
   record_id:group.recordId,sample_id:group.sampleId,scope:group.label,
   qualifier:[field.status==='reported'?'':field.status.replaceAll('_',' '),field.note].filter(Boolean).join(' · '),
   source_locator:field.evidence||[]});
 }
 if(!groups.size)ensure(r.record_id,'unassigned','Specimen not assigned');
 return groups;
}

export function classifyMorphology(value,recordId=''){
 const m=text(value).toLowerCase();
 if(pendingZhongBranches(value,recordId))return 'neutral';
 if(!m||/\b(unknown|unresolved|unassigned|not determined)\b/.test(m))return 'neutral';
 if(/\b(proposed|damage|not demonstrated|non[ -]spherical)\b/.test(m))return 'neutral';
 if(/\b(spher\w*|round)\b/.test(m)&&/\b(cubic|cube\w*)\b/.test(m))return 'neutral';
 if(/\b(?:no|not|without)\b(?:[\s-]+\w+){0,3}[\s-]+(?:spher\w*|round|cub\w*|rods?|nanorods?|islands?|plates?|disklike|nanodisks?|shell\w*|stars?)\b/.test(m))return 'neutral';
 if(/\b(?:spher\w*|cub\w*|rods?|islands?|nanodisks?)\s+(?:(?:were|are)\s+)?(?:not|never)\s+(?:observed|confirmed)/.test(m))return 'neutral';
 // This article reports nanocrystal assembly outcomes whose descriptions also
 // name their constituent rods, plates or islands. Bind the presentation rule
 // to that audited source instead of changing other papers' morphology labels.
 if(recordId.startsWith('xu2008-hierarchical-nc-assemblies-adma200800215-')){
  if(/\bternary porous architecture with tio2\b/.test(m))return 'mixed-rod-dot-assembly';
  if(/\b(?:2d porous architecture of (?:long|short) tio2 nanorods|two shifted hexagonal layers of short rods|2d short-rod architecture on wafer|orthogonally ordered pores)\b/.test(m))return 'rod-assembly';
  if(/\bag nanocrystals arranged like petals around hexagonal coo nanoplates\b/.test(m))return 'platelet-dot-assembly';
  if(/\bporous ag–coo architecture\b/.test(m))return 'porous-hybrid-film';
  if(/\bporous architecture containing square eu:lavo4 particles\b/.test(m))return 'square-dot-assembly';
  if(/\bsquare nanocrystals\b/.test(m))return 'square-projection';
  if(/\b(?:architecture|superlattice|monolayer|bilayer(?:ed)?)\b|\btwo shifted hexagonal layers\b|\bnanocrystals? arranged like petals\b|\borthogonally ordered pores\b/.test(m))return 'assembly';
 }
 const primitiveShapes=[/\b(spher\w*|round)\b/,/\b(cubic[ -]shaped|cubes?|cuboidal)\b/,/\b(nanorods?|rods?|nanowires?)\b/,/\b(platelets?|nanoplates?|disklike|nanodisks?)\b/,/\b(star\w*|octapods?)\b/].filter(re=>re.test(m));
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
 if(/platelets?|nanoplates?|sheets?|\bdisklike\b|\bnanodisks?\b/.test(m))return 'platelet';
 if(/ellipsoid|oval|oblate|prolate/.test(m))return 'ellipsoid';
 if(/\b(nanorods?|rods?|nanowires?)\b/.test(m))return 'rod';
 if(/\b(cubes?|cuboidal|cubic[ -]shaped)\b/.test(m))return 'cube';
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
 const shape=inferred?.shape||classifyMorphology(morphology,group.recordId);
 const sourceFact=group.facts.find(f=>f.kind==='morphology'&&knownStatus.has(f.status)||sameCanonicalProductFact(f,group,'morphology'));
 return {composition:composition||'Composition not assigned',scope:group.label||group.sampleId,
         morphology,shape,inferred,sourceFact,
         caption:shape==='neutral'?(pendingZhongBranches(morphology,group.recordId)?'The source reports a branched morphology for this specimen. A matching illustration has not yet been assigned; the source description and figures remain available.':'The source evidence does not yet support a specific morphology illustration for this specimen.'):inferred?.rationale||(
          shape==='rod-assembly'?'Schematic rods only; source-reported pore geometry, layer alignment and spacing are not reconstructed. Constituent count and orientation are illustrative.':
          shape==='porous-hybrid-film'?'Schematic repeated hybrid motifs in a porous film; number, positions and pore geometry are illustrative.':
          'Schematic interpretation of the source description. Geometry and colors are illustrative; not to scale or an atomic reconstruction.')};
}

export function particleDisplayDescriptor(r,group,presentation={},interpretations={}){
 const d=particleDescriptor(group,interpretations),product=group.product;
 const shapeOnly=new Set(['sphere','cube','rod','platelet','belt','ellipsoid','irregular','truncated-octahedron']);
 const sourceIds=new Set((r.sources||[]).map(source=>source.id));
 const reportedMorphology=text(product?.morphology?.value),wire=reportedMorphology.trim().toLowerCase()==='wire';
 const reportedPrimitive=wire?'rod':classifyMorphology(reportedMorphology,group.recordId);
 const reportedShape=r.quality?.review_status==='source_extracted'&&group.recordId===r.record_id&&
  (r.products||[]).includes(product)&&product?.sample_id===group.sampleId&&
  product.morphology?.status==='reported'&&shapeOnly.has(reportedPrimitive)&&d.morphology===reportedMorphology&&
  (d.shape===reportedPrimitive||wire&&d.shape==='neutral')&&
  (product.morphology.evidence||[]).some(item=>sourceIds.has(item.source_id)&&text(item.locator));
 if(reportedShape&&!d.inferred&&wire){
  d.shape=reportedPrimitive;d.caption='Illustrative elongated outline for the source-reported wire. Geometry and colors are illustrative; not to scale or an atomic reconstruction.';
 }
 // A reported primitive supports an illustrative outline even when chemistry
 // is unassigned. Pending reviewed contexts keep their interpretation rule.
 if(presentation.presentation_status==='pending'&&!d.inferred&&!reportedShape)d.shape='neutral';
 return d;
}

function particleArt(descriptor){
 const host=el('div',undefined,'reader-product-illustration');
 if(descriptor.inferred?.inline_art_id){
  const markup=scopedProductArt(descriptor.inferred.inline_art_id);if(!markup)throw Error('Scoped product illustration ID is not registered');
  host.innerHTML=markup;return host;
 }
 if(descriptor.inferred?.svg_path){
  const image=el('img');image.src=siteURL(descriptor.inferred.svg_path);image.alt=descriptor.inferred.alt||descriptor.inferred.label||'Source-based interpretation of particle morphology';image.loading='lazy';image.style.width='100%';image.style.height='auto';host.append(image);return host;
 }
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
 const illustrated=[...groups.values()].filter(g=>particleDisplayDescriptor(r,g,presentation,interpretations).shape!=='neutral');
 const preferred=illustrated.find(g=>g.key===wanted)||illustrated.find(g=>g.recordId===r.record_id&&(g.context?.recipe_link||g.product?.recipe_link)==='explicit')||illustrated[0];
 if(preferred)choose.value=preferred.key;else if(groups.has(wanted))choose.value=wanted;
 panel.append(choose,display);
 function show(){const group=groups.get(choose.value)||groups.values().next().value,d=particleDisplayDescriptor(r,group,presentation,interpretations),layout=el('div',undefined,'reader-product-layout'),copy=el('div');
  const caption=d.shape==='neutral'&&presentation.presentation_status==='pending'?'A morphology illustration has not yet been assigned to this specimen. Its available source-reported observations are retained below.':d.caption;
  copy.append(badge(d.shape==='neutral'?'Reported product information':d.inferred?.display_kind==='composition_schematic'?'Conceptual product':d.inferred?'Inferred morphology':'Morphology illustration','reference'),el('h3',d.inferred?.label||d.composition),el('p',d.scope,'reader-note'),el('p',caption,'reader-note'));
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
  if(d.shape==='neutral'){layout.style.gridTemplateColumns='1fr';layout.append(copy);}else layout.append(particleArt(d),copy);
  display.replaceChildren(layout);
 }
 choose.onchange=show;show();return {groups,choose,display};
}
