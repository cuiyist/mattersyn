import {installReaderHashNavigation,applyReaderFragment} from './reader-navigation.mjs';
import {mountWuContext} from './wu2008-reader-context.mjs';
import {el,link,button,badge,section,disclosure,siteURL,recordURL,human,isEquipment,shortMethod,sourceURL} from './reader-utils.mjs';

import {quantityValue} from './quantity-value.mjs';

import {chemicalRegistry,chemicalEntry,chemicalImage,openChemical} from './chemical-viewer.mjs?v=0.34.1';

import {mountProtocol} from './protocol-visuals.mjs?v=0.37.0-r1';

import {mountReaderStructures} from './reader-structures.mjs?v=0.36.0';

const cache=new Map();

function json(path){if(!cache.has(path))cache.set(path,fetch(siteURL(path),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Unavailable '+path);return r.json();}));return cache.get(path);}

export function formatQuantity(q){if(!q)return 'Not reported';const v=quantityValue(q),unit=({degC:'°C',uL:'µL',umol:'µmol',angstrom:'Å',um:'µm',uM:'µM',volume_parts:'volume parts',mass_percent:'wt%',volume_percent:'vol%'})[q.unit]||q.unit||'';if(v===null)return q.raw_text||q.qualifier||'Not reported';return (q.approximate?'≈':'')+v+(unit?' '+unit:'');}

function quantities(rows,compact=true){const dl=el('dl');for(const [key,q] of rows){const div=el('div');div.append(el('dt',human(key)),el('dd',formatQuantity(q)));if(!compact&&q.basis)div.append(el('small',q.basis));dl.append(div);}return dl;}

const normal=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]/g,'');

const safeText=v=>typeof v==='string'?v:v?.text||v?.value||v?.note||'';

function installStyle(){if(document.querySelector('link[data-reader-css]'))return;const style=el('link');style.rel='stylesheet';style.href=siteURL('reader.css?v=0.35.0-conflict-pairs');style.dataset.readerCss='true';document.head.append(style);}
async function precursors(host,r){

 const [data,thumbs,stockBindings]=await Promise.all([chemicalRegistry(),json('data/chemical-thumbnail-map.json'),json('data/reader-stock-bindings.json')]);if(!host.isConnected)return;function cardImage(entry){const img=chemicalImage(entry),item=thumbs.entries[entry.id];if(item?.thumbnail_path)img.src=siteURL(item.thumbnail_path);return img;}const chemicals=r.materials.filter(m=>!isEquipment(m)),grid=el('div',undefined,'reader-chemicals');

 for(const m of chemicals){const card=el('article',undefined,'reader-chemical');card.dataset.materialId=m.id;const entry=chemicalEntry(data,r.record_id,m.id);card.append(el('small',human(m.role)),el('h3',m.name),el('div',entry?.displayFormula||entry?.formula||m.formula||'Source-defined composition','reader-formula'));

  if(entry){const image=cardImage(entry);image.alt=m.name+' chemical structure';card.append(image,button(entry.model3dPath?'Rotate structure ↗':'Inspect structure ↗',()=>openChemical(entry),'molecule-link'));}else card.append(el('p','Chemical identity is retained in the source record.','reader-note'));

  const qs=Object.entries(m.quantities||{}),known=qs.filter(([,q])=>quantityValue(q)!==null);known.sort(([a],[b])=>Number(/purity|grade/.test(a))-Number(/purity|grade/.test(b)));card.append(quantities(known.slice(0,3)));

  if(qs.length>3||qs.some(([,q])=>quantityValue(q)===null))card.append(disclosure('All quantities and specifications',quantities(qs,false)));

  const storage=(m.notes||[]).map(safeText).filter(x=>/stor|drybox|dry box/i.test(x));for(const note of storage)card.append(el('p',note,'reader-note'));

  card.append(link('Source details →',recordURL(r.record_id)+'#precursors','reader-data-link'));grid.append(card);

 }host.append(grid);

 const alternatives=r.condition_options.filter(option=>option.chemical_material_id);
 if(alternatives.length){
  host.append(el('h3','Source-reported precursor alternatives'));
  const choiceGrid=el('div',undefined,'reader-chemicals');
  for(const option of alternatives){
   const material=r.materials.find(item=>item.id===option.chemical_material_id),entry=chemicalEntry(data,r.record_id,option.chemical_material_id);
   const card=el('article',undefined,'reader-chemical');
   card.append(badge('Source-defined alternative','scope'),el('h3',material?.name||entry?.name||option.chemical_material_id),el('div',entry?.displayFormula||entry?.formula||material?.formula||'','reader-formula'),el('p',option.label,'reader-note'));
   if(entry){card.append(cardImage(entry),button(entry.model3dPath?'Rotate structure ↗':'Inspect structure ↗',()=>openChemical(entry),'molecule-link'));}
   const parameters=Object.entries(option.parameters||{});if(parameters.length)card.append(quantities(parameters,false));
   card.append(link('Source details →',recordURL(r.record_id)+'#protocol','reader-data-link'));
   choiceGrid.append(card);
  }
  host.append(el('p','These are mutually exclusive source-reported choices. The article does not identify which Fe(III) alkoxide was used for sample A.','reader-note'),choiceGrid);
 }

 const contextData=await json('assets/chemical-registry/solution-components.json');if(!host.isConnected)return;const contexts=contextData.contexts.filter(c=>c.record_id===r.record_id),used=new Set(),stockList=el('div',undefined,'reader-stock-list');

 function stockCard(stock,context){const name=stock?.name||context.label,d=el('details',undefined,'reader-stock');d.dataset.stockId=stock?.id||context.id||normal(name);d.append(el('summary',name));const body=el('div',undefined,'reader-stock-body'),facts=el('div',undefined,'reader-stock-facts'),images=el('div',undefined,'reader-stock-components');

  if(stock){for(const c of stock.components){const m=r.materials.find(m=>m.id===c.material_id);facts.append(el('p',(m?.name||c.material_id)+': '+Object.entries(c.quantities||{}).map(([k,q])=>human(k)+' '+formatQuantity(q)).join(' · ')));}for(const [k,q] of Object.entries(stock.concentrations||{}))facts.append(el('p',human(k)+': '+formatQuantity(q)));const scope=safeText(stock.scope);if(scope)facts.append(el('p',scope,'reader-note'));}

  const components=context?.components?.map(c=>{const base=data.entries.get(c.registry_id);return {entry:base?{...base,...c.viewOverrides,sourceBindingCaption:c.viewOverrides?.caption}:null,role:c.role};})||stock.components.map(c=>({entry:chemicalEntry(data,r.record_id,c.material_id),role:r.materials.find(m=>m.id===c.material_id)?.role||'Component'}));

  for(const {entry,role} of components.filter(c=>c.entry)){const card=button('',()=>openChemical(entry),'reader-stock-component');card.append(cardImage(entry),el('span',entry.name),el('small',human(role)));images.append(card);}

  if(context?.scope)facts.append(disclosure('Composition and interpretation',el('p',context.scope)));facts.append(link('Complete stock record →',recordURL(r.record_id)+'#precursors','reader-data-link'));body.append(facts,images);d.append(body);stockList.append(d);

 }

 for(const stock of r.stocks){const context=contexts.find(c=>c.id===stockBindings.stockBindings?.[r.record_id]?.[stock.id])||contexts.find(c=>c.id===stock.id||normal(c.label)===normal(stock.name));if(context)used.add(context);stockCard(stock,context);}

 for(const context of contexts)if(!used.has(context))stockCard(null,context);

 if(stockList.children.length)host.append(el('h3','Stocks and solutions'),stockList);

}

let figureDialog;

function enlargeFigure(f){if(f.display_kind==='source_link'){if(!figureDialog){figureDialog=el('dialog',undefined,'reader-figure-dialog');document.body.append(figureDialog);}const header=el('header');header.append(el('h2',f.title||f.id),button('Close ×',()=>figureDialog.close()));figureDialog.replaceChildren(header,el('p',f.display_note||'Original figure withheld. Consult the source.','reader-note'),link('Read the source figure ↗',f.source_url),el('p',f.summary||''));if(!figureDialog.open)figureDialog.showModal();return;}if(!figureDialog){figureDialog=el('dialog',undefined,'reader-figure-dialog');document.body.append(figureDialog);}const header=el('header');header.append(el('h2',f.title||f.id),button('Close ×',()=>figureDialog.close()));const img=el('img');img.src=siteURL(f.public_asset||f.asset);img.alt=f.summary||f.title||f.id;figureDialog.replaceChildren(header,img,el('p',f.summary||'','reader-note'));if(!figureDialog.open)figureDialog.showModal();}

function reviewURL(r,p={},anchor=''){const base=p.data_links?.full_review||recordURL(r.record_id)+'#evidence';return base+(base.startsWith('paper-review.html')?anchor:'');}

export function figureGallery(host,figures,r,category,presentation={}){

 const unique=new Map();for(const f of figures.filter(x=>(x.category===category||x.categories?.includes(category))&&(x.public_asset||x.asset)))unique.set((f.source_id||'')+'|'+f.id,f);const rows=[...unique.values()];const textOnly=figures.filter(f=>(f.category===category||f.categories?.includes(category))&&!(f.public_asset||f.asset));for(const f of textOnly)host.append(disclosure((f.title||f.id)+' · original image unavailable',el('p',f.summary||''),link('Source evidence →',reviewURL(r,presentation),'reader-data-link')));if(!rows.length)return textOnly.length;

 const wrapper=el('div',undefined,'reader-figure-gallery'),tabs=el('div',undefined,'reader-figure-tabs'),display=el('div');tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label',category==='property'?'Property figures':'Characterization figures');wrapper.append(tabs,display);host.append(wrapper);

 function render(i){const f=rows[i];for(const [n,b] of [...tabs.children].entries())b.setAttribute('aria-selected',String(n===i));const figure=el('figure',undefined,'reader-figure'),img=el('img',undefined,'reader-figure-image');img.loading='lazy';img.src=siteURL(f.public_asset||f.asset);img.alt=f.display_kind==='source_link'?'Source-link card; original figure withheld':f.title||f.id;img.tabIndex=0;img.setAttribute('role','button');img.setAttribute('aria-label',(f.display_kind==='source_link'?'Open source reference for ':'Enlarge ')+img.alt);img.onclick=()=>enlargeFigure(f);img.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();enlargeFigure(f);}};

  const caption=el('figcaption',undefined,'reader-figure-caption');caption.append(el('h3',f.title||f.id));if(f.display_kind==='source_link')caption.append(el('p',f.display_note,'reader-note'),link('Read the source figure ↗',f.source_url));if(f.summary&&f.summary!==f.title){const first=f.summary.match(/^.*?[.!?](?=\s+[A-Z]|$)/s)?.[0]?.trim();if(first&&first.length<=300)caption.append(el('p',first));caption.append(disclosure('Full source caption and qualifications',el('p',f.summary)));}caption.append(badge(f.scope_label||f.scope||'Source figure · specimen scope retained','scope'));const source=f.source_id||r.lineage.source_group;const loc=f.source_locator||f.locator||'';if(loc){const locationText=typeof loc==='string'?loc:[loc.document_role,loc.page?'PDF p. '+loc.page:'',loc.figure].filter(Boolean).join(' · ');caption.append(el('small',locationText));}caption.append(link('Full figure evidence →',reviewURL(r,presentation,'#source-'+(category==='property'?'properties':'structures')),'reader-data-link'));figure.append(img,caption);display.replaceChildren(figure);

 }rows.forEach((f,i)=>{const b=button(f.title||f.id,()=>render(i));b.setAttribute('role','tab');tabs.append(b);});render(0);return rows.length;

}

function intuition(host,r,presentation){const items=presentation.intuition||presentation.chemical_intuition||[];if(!items.length){host.append(el('p','Interpretation is available with the original source and complete review.','reader-note'),link('Source discussion →',reviewURL(r,presentation,'#source-intuition'),'reader-data-link'));return;}
 const grid=el('div',undefined,'reader-intuition');for(const item of items.slice(0,3)){const card=el('article');if(item.title)card.append(el('h3',item.title));card.append(el('p',item.summary||item.text||''),el('small',human(item.claim_type||'Source interpretation')),link('Evidence →',reviewURL(r,presentation,'#source-intuition'),'reader-data-link'));grid.append(card);}host.append(grid);if(items.length>3)host.append(link('All interpretations and references →',reviewURL(r,presentation,'#source-intuition'),'reader-data-link'));}
function sourceDisagreements(host,pairs,r){if(!Array.isArray(pairs)||!pairs.length)return;const heading=el('h3','Source comparisons','reader-conflict-heading');heading.id='source-disagreements';host.append(heading,el('p','Each account retains its context and source locator. Unresolved discrepancies remain marked; distinct measurement bases are shown separately.','reader-conflict-intro'));for(const pair of pairs){if(!Array.isArray(pair.claims)||pair.claims.length<2)continue;const card=el('article',undefined,'reader-conflict');const top=el('div',undefined,'reader-conflict-top');top.append(el('h4',pair.topic||'Source disagreement'),badge(pair.status==='preserved_distinct'?'Distinct bases':'Unresolved','reader-conflict-status'));card.append(top);if(pair.context)card.append(el('p',pair.context,'reader-conflict-context'));const claims=el('div',undefined,'reader-conflict-claims');pair.claims.forEach((claim,index)=>{const item=el('section',undefined,'reader-conflict-claim');item.append(el('span',claim.label||`Report ${index+1}`,'reader-conflict-label'),el('p',claim.statement||'Claim text not supplied.'));if(claim.sourceLocator)item.append(el('small',claim.sourceLocator,'reader-conflict-locator'));const source=r.sources.find(s=>s.id===claim.sourceId);if(source)item.append(link(source.title+' ↗',sourceURL(source),'reader-data-link'));claims.append(item);});card.append(claims);host.append(card);}}
function dataSwitch(r,active='reader'){const nav=el('nav',undefined,'reader-switch');nav.setAttribute('aria-label','Reader or data view');nav.append(link('Reader',recordURL(r.record_id,'reader'),active==='reader'?'active':''),link('Data and evidence',recordURL(r.record_id,'data'),active==='data'?'active':''),link('Download JSON ↓','data/records/'+r.record_id+'.json'));return nav;}
async function buildMethod(host,r,presentation){

 const sections=[section('precursors','01','Precursors'),section('protocol','02','Synthesis protocol'),section('structures','03','Final structures'),section('properties','04','Properties'),section('intuition','05','Chemical intuition')];host.append(...sections);

 const protocol=el('div',undefined,'reader-protocol');sections[1].append(protocol);mountProtocol(protocol,r);sections[1].append(link('Full operations, branches and source notes →',recordURL(r.record_id)+'#protocol','reader-data-link'));

 const structureHost=el('div');sections[2].append(structureHost);const figs=presentation.figures||[];figureGallery(sections[2],figs,r,'structure',presentation);

 const count=figureGallery(sections[3],figs,r,'property',presentation);if(!count){const measurements=r.measurements.filter(m=>/absorp|emiss|lumines|raman|magnet|quantum_yield|conduct|band.?gap|lifetime/i.test(m.property));if(measurements.length){const dl=el('dl',undefined,'reader-product-facts');for(const m of measurements.slice(0,4)){const row=el('div');row.append(el('dt',human(m.property)),el('dd',formatQuantity(m.value)),el('small',m.technique+' · '+m.sample_id));dl.append(row);}sections[3].append(dl);}else sections[3].append(el('p','No property result is assigned to this method in the reviewed record. Related source evidence remains available below.','reader-note'));}

 sections[3].append(link('Complete measurements and source evidence →',recordURL(r.record_id)+'#properties','reader-data-link'));intuition(sections[4],r,presentation);

 const sources=section('sources','06','Sources');for(const source of r.sources){const card=el('div',undefined,'reader-citation');card.append(el('strong',source.title),el('p',source.authors+' · '+source.year),link((source.doi||'Source')+' ↗',sourceURL(source)),document.createTextNode(' · '),link('Source review →',source.id===r.lineage.source_group?reviewURL(r,presentation):sourceURL(source)));sources.append(card);}sourceDisagreements(sources,presentation.conflictPairs,r);host.append(sources);
 mountWuContext(host,sections,sources,r,presentation);
 await Promise.all([precursors(sections[0],r),mountReaderStructures(structureHost,r,presentation)]);

}

export async function mountReader(main,{materialId,recordId}={}){

 installStyle();installReaderHashNavigation();main.className='reader-main';main.replaceChildren(el('div','Loading reviewed material…','reader-loading'));

 const [index,presentations]=await Promise.all([json('data/materials-index.json'),json('data/reader-presentation.json')]);

 let material=materialId?index.materials.find(m=>m.id===materialId):null;

 if(recordId&&!material){
  const candidates=index.materials.filter(m=>(presentations.materials?.[m.id]?.record_ids||[]).includes(recordId));
  if(candidates.length){
   const routeRecord=candidates.length>1?await json('data/records/'+recordId+'.json'):null;
   const targetFormula=normal(routeRecord?.material?.formula);
   material=(targetFormula&&candidates.find(m=>normal(m.formula)===targetFormula))||candidates.find(m=>!m.component_only)||candidates[0];
  }
 }
 if(!material&&materialId)throw Error('This material does not have a reviewed synthesis page.');

 let data=material?await json('data/materials/'+material.id+'.json'):null;

 const records=(data?.records||[]).filter(r=>r.is_synthesis_route&&r.collection==='reviewed_literature');

 if(recordId&&!records.some(r=>r.record_id===recordId)){const r=await json('data/records/'+recordId+'.json');records.unshift({record_id:recordId,title:r.title,method:r.method,formula:r.material.formula,year:r.sources[0].year});}

 if(!records.length)throw Error('No reviewed synthesis method is available.');

 let active=recordId&&records.some(r=>r.record_id===recordId)?recordId:records[0].record_id;const baseTitle=data?.formula||records[0].formula;

 main.replaceChildren();const toolbar=el('div',undefined,'reader-view-toolbar');toolbar.append(link('Periodic table / '+baseTitle,'index.html','reader-breadcrumb'),el('span','Reviewed synthesis and evidence','reader-version'));main.append(toolbar);

 const heading=el('header',undefined,'reader-heading');heading.append(el('h1',baseTitle),el('p',data?.name||'Reviewed synthesis and material evidence'));if(data?.component_only)heading.append(badge('Component within a heterostructure','scope'));main.append(heading);

 const selector=el('section');selector.append(el('h2','Synthesis methods'));const cards=el('div',undefined,'reader-methods');

 for(const meta of records){const card=button('',()=>select(meta.record_id),'reader-method-card');card.dataset.recordId=meta.record_id;card.append(el('small',shortMethod(meta.method).toUpperCase()),el('strong',meta.title),el('small',String(meta.year||'')));cards.append(card);}selector.append(cards);if(records.length>6){[...cards.children].slice(6).forEach(x=>x.hidden=true);selector.append(button('Show all '+records.length+' methods',e=>{for(const c of cards.children)c.hidden=false;e.currentTarget.hidden=true;},'reader-chip'));}main.append(selector);

 const methodInfo=el('div',undefined,'reader-method-info'),nav=el('nav',undefined,'reader-nav');nav.setAttribute('aria-label','Reader sections');for(const [id,title] of [['precursors','Precursors'],['protocol','Synthesis protocol'],['structures','Final structures'],['properties','Properties'],['intuition','Chemical intuition'],['sources','Sources']])nav.append(link(title,'#'+id));const body=el('div');main.append(methodInfo,nav,body);let generation=0;

 async function select(rid){delete main.dataset.readerReady;const turn=++generation;active=rid;for(const c of cards.children)c.setAttribute('aria-pressed',String(c.dataset.recordId===rid));const r=await json('data/records/'+rid+'.json');if(turn!==generation)return;const presentation=presentations.records?.[rid]||{};methodInfo.replaceChildren();const badges=el('div',undefined,'reader-badges');badges.append(badge(shortMethod(r.method)),badge(r.sources[0].year+' · '+(r.sources[0].authors.split(/[,;]/)[0]+' et al.'||'Source'),'scope'));methodInfo.append(badges,el('p',r.sources[0].title,'reader-citation'),dataSwitch(r));if(data?.component_only||data&&data.formula!==r.material.formula)methodInfo.append(el('p','This method produces '+r.material.formula+'. Evidence describes the named product and its components.','reader-note'));body.replaceChildren();const content=el('div');body.append(content);await buildMethod(content,r,presentation);if(turn!==generation)return;document.title=baseTitle+' · '+shortMethod(r.method)+' | MatterSyn';const url=new URL(location.href);url.searchParams.set('method',rid);history.replaceState(null,'',url);main.dataset.readerReady=rid;await applyReaderFragment(main);}

 await select(active);return {material:data,recordId:active};

}

export async function bootstrapRecord(r){installStyle();const presentations=await json('data/reader-presentation.json');const eligible=!!presentations.records?.[r.record_id];const original=document.querySelector('main');if(!eligible||new URLSearchParams(location.search).get('view')==='data'){if(eligible){const nav=dataSwitch(r,'data');nav.classList.add('reader-data-nav');original.prepend(nav);}return false;}

 const main=el('main');original.replaceWith(main);try{await mountReader(main,{recordId:new URLSearchParams(location.search).get('method')||r.record_id});}catch(error){main.replaceWith(original);original.prepend(el('p','Reader view unavailable. Complete data is shown below.','reader-note'));console.error(error);return false;}return true;

}

if(document.body.dataset.readerPage==='material'){

 const params=new URLSearchParams(location.search);try{await mountReader(document.querySelector('main'),{materialId:params.get('id')||document.body.dataset.materialId,recordId:params.get('method')||document.body.dataset.recordId||undefined});}catch(error){document.querySelector('main').replaceChildren(el('h1','Material reader'),el('p',error.message),link('Explore reviewed materials →','index.html'));console.error(error);}

}

