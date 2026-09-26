// Figure-level interpretations stay separate from recipe/sample outcome data.
import {el,link,disclosure,siteURL} from './reader-utils.mjs';
import {particleShapeSVG,PARTICLE_SHAPES} from './particle-shapes.mjs?v=0.40.3';

export function figureMorphologyContexts(entries,record,presentation={}){
 const displayed=new Set((presentation.figures||[]).filter(f=>f.display_kind!=='source_link').map(f=>f.public_asset||f.asset).filter(Boolean));
 return entries.filter(e=>e.binding==='source_figure_context_only'&&e.measured_coordinates===false&&e.eligible_training===false&&
  e.source_group===record.lineage?.source_group&&e.record_ids?.includes(record.record_id)&&displayed.has(e.asset)&&
  (e.svg_path||PARTICLE_SHAPES.includes(e.shape)));
}

let pending;
export async function mountFigureMorphology(host,record,presentation={}){
 pending??=fetch(siteURL('data/reader-figure-morphology.json'),{cache:'no-store'}).then(r=>r.ok?r.json():{entries:[]});
 const data=await pending,entries=figureMorphologyContexts(data.entries||[],record,presentation);
 if(!host.isConnected||!entries.length)return;
 const section=el('section',undefined,'reader-figure-morphology'),choice=el('select',undefined,'reader-method-select'),display=el('div');
 section.append(el('h3','Source-figure morphology'),el('p','These drawings interpret the cited figure and its stated specimen context. They are not assigned to the selected recipe or counted as additional recipe–structure pairs.','reader-note'));
 choice.setAttribute('aria-label','Source figure morphology context');
 for(const e of entries){const option=el('option',e.title+(e.sample_label?' · '+e.sample_label:''));option.value=e.id;choice.append(option);}
 section.append(choice,display);host.append(section);
 const show=()=>{
  const e=entries.find(x=>x.id===choice.value)||entries[0],layout=el('div',undefined,'reader-product-layout'),art=el('div',undefined,'reader-product-illustration'),copy=el('div');
  if(e.svg_path){const img=el('img');img.src=siteURL(e.svg_path);img.alt=e.alt||e.title+' qualitative illustration';img.loading='lazy';img.style.width='100%';art.append(img);}else art.innerHTML=particleShapeSVG(e.shape);
  copy.append(el('p','Figure interpretation · not a recipe assignment','reader-reference-role'),el('h4',e.sample_label||e.title),el('p',e.rationale,'reader-note'));
  if(e.panel)copy.append(el('p','Source panel: '+e.panel,'reader-note'));
  copy.append(link('View the source figure ↗',e.asset,'reader-data-link'));
  const details=disclosure('Interpretation and limitations');
  for(const note of e.limitations||[])details.append(el('p',note));
  details.append(el('p','Illustrative outlines, orientations and colors do not establish particle dimensions, population fractions, interfaces or atomic coordinates.'));
  copy.append(details);layout.append(art,copy);display.replaceChildren(layout);
 };
 choice.onchange=show;show();
}
