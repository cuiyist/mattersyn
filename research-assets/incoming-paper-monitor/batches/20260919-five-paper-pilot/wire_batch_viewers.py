"""Root-only renderer integration; source assets and scientific records remain frozen."""
from pathlib import Path
S=Path('[local path redacted]')
def patch(rel,replacements):
    p=S/rel;t=p.read_text(encoding='utf8')
    for old,new in replacements:
        assert old in t,(rel,old)
        t=t.replace(old,new)
    p.write_text(t,encoding='utf8')
patch('dist/protocol-visuals.mjs',[
 ("import {buildGu2004Scene", "import {buildNagasaki2004Scene,createNagasaki2004Art} from './nagasaki2004-protocol.mjs';\nimport {buildRibeiro2004Scene,createRibeiro2004Art} from './ribeiro2004-protocol.mjs';\nimport {buildNorberg2004Scene,createNorberg2004Art} from './norberg2004-protocol.mjs';\nimport {buildGu2004Scene"),
 ('const sourceArt=createGu2004Art','const sourceArt=createNagasaki2004Art(o,r)||createRibeiro2004Art(o,r)||createNorberg2004Art(o,r)||createGu2004Art'),
 ('gu=buildGu2004Scene(o,r);','gu=buildGu2004Scene(o,r),nagasaki=buildNagasaki2004Scene(o,r),ribeiro=buildRibeiro2004Scene(o,r),norberg=buildNorberg2004Scene(o,r);'),
 ('gu?.caption||','nagasaki?.caption||ribeiro?.caption||norberg?.caption||gu?.caption||'),
 ('||sashchiuk||gu)', '||sashchiuk||gu||nagasaki||ribeiro||norberg)')])
patch('scripts/build_dataset.py',[
 ("'<article class=\"stock-record\"><h4>'+esc(stock['name'])", "'<article class=\"stock-record\" data-stock-id=\"'+esc(stock['id'])+'\"><h4>'+esc(stock['name'])"),
 ("s+=section('precursors','01'", "body+='<div id=\"record-reagent-components\"></div>'\n    s+=section('precursors','01'")])
patch('dist/material-guide.mjs',[
 ('chemicalRegistry,chemicalEntry,chemicalImage,openChemical}', 'chemicalRegistry,chemicalEntry,chemicalImage,openChemical,mountStockComponents,mountReagentComponents}'),
 ("content.append(d);}}\n  content.append(el('h3','Synthesis protocol'))", "mountStockComponents(d,r,s,chemicals);content.append(d);}}\n  await mountReagentComponents(content,r,chemicals);if(current!==generation)return;\n  content.append(el('h3','Synthesis protocol'))")])
patch('dist/crystal-viewer.mjs',[
 ("let productReferencePromise;", "let productReferencePromise,productContextsPromise;"),
 ("async function productIdentity(host,r){", """async function productIdentity(host,r){
 productContextsPromise??=fetch(new URL('assets/chemical-registry/product-contexts.json',import.meta.url),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Product contexts unavailable');return r.json();});
 const contextual=await productContextsPromise,contexts=contextual.recordContexts[r.record_id]||[],notice=contextual.sourceNotices[r.lineage?.source_group];
 if(contexts.length){const data=await chemicalRegistry(),card=el('article',undefined,'crystal-reference-card'),select=el('select',undefined,'guide-route-select'),view=el('div');select.setAttribute('aria-label','Product specimen or source context');for(const [i,c] of contexts.entries()){const option=el('option',c.label+' · '+c.sample_id);option.value=String(i);select.append(option);}const render=()=>{const c=contexts[Number(select.value)],entry=data.entries.get(c.registry_id);view.replaceChildren();if(entry){view.append(chemicalImage(entry));const b=el('button','Enlarge product representation ↗','molecule-link');b.type='button';b.onclick=()=>openChemical({...entry,caption:c.caption,sourceBindingCaption:c.caption});view.append(b);}view.append(el('p',c.caption),el('p','Phase in this context: '+(c.phase?.value||'Not reported')+(c.phase?.note?' · '+c.phase.note:''),'guide-notice'));for(const e of c.phase?.evidence||[])view.append(el('small',e.source_id+' · '+e.locator));};card.append(el('h3','Product specimens and structural evidence'),select,view);host.append(card);select.onchange=render;render();}
 if(notice)host.append(el('p',notice,'guide-notice'));
"""),
 ("'sashchiuk2004','gu2004']", "'sashchiuk2004','gu2004','nagasaki2004','ribeiro2004','norberg2004']")])
print('Wired three source-specific protocols, stock/reagent component selectors and sample-scoped product contexts.')
