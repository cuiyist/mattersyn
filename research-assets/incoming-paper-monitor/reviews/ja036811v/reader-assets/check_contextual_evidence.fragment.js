// Exercise actual mountEvidence route-scoped galleries, including the all-source override.
globalThis.fetch=async rel=>{const url=String(rel),p=url.startsWith('file:')?fileURLToPath(url):path.resolve(dist,url);if(!path.resolve(p).startsWith(path.resolve(dist)+path.sep))throw Error('Unexpected evidence path');return{ok:fs.existsSync(p),json:async()=>JSON.parse(fs.readFileSync(p,'utf8'))};};
const {mountEvidence}=await import(pathToFileURL(path.join(dist,'material-guide.mjs')).href+'?audit='+Date.now());
const gallerySources=[...ledger.figures,...ledger.tables.filter(t=>t.public_asset)];
for(const [suffix,formula,expectedCount,required,forbidden]of [
 ['zno-route','ZnO',5,['figure-1','figure-2','si-figure-6'],['figure-5','figure-10','si-figure-3']],
 ['co-route','ZnO:Co',15,['figure-5','figure-10','si-figure-2'],['figure-2','si-figure-3','si-figure-6']],
 ['ni-route','ZnO:Ni',8,['figure-6','figure-8','si-figure-3'],['figure-2','figure-5','figure-9','figure-10','si-figure-2','si-figure-4']]
]){
 const rid='schwartz-2003-'+suffix,record=JSON.parse(fs.readFileSync(path.join(dist,'data/records',rid+'.json'),'utf8')),host=new Element('div');
 await mountEvidence(host,record,{materialFormula:formula});
 const tree=descend(host),gallery=tree.find(x=>x.className==='guide-evidence-gallery'),filter=tree.find(x=>x.attributes['aria-label']==='Figure scope');
 check(rid+' figure selector mounted',!!filter&&gallery?.children.length===19);
 filter.value='record';filter.onchange();
 const shown=()=>gallerySources.filter((x,i)=>!gallery.children[i].hidden).map(x=>x.id);
 check(rid+' intended material gallery count',shown().length===expectedCount);
 check(rid+' required applicable figures visible',required.every(id=>shown().includes(id)));
 check(rid+' other-material specific figures excluded',forbidden.every(id=>!shown().includes(id)));
 const allowed=new Set(ledger.material_original_asset_ids[formula]);
 check(rid+' every visible asset explicitly allowed',shown().every(id=>allowed.has(id)));
 check(rid+' contextual sample identity disclosure',host.textContent.includes(ledger.material_asset_scope_note));
 const links=tree.filter(x=>x.tagName==='a').map(x=>String(x.href));
 check(rid+' all declared evidence contexts linked',ledger.route_evidence_contexts[rid].every(id=>links.some(url=>url.endsWith('/records/'+id+'.html'))));
 filter.value='all';filter.onchange();check(rid+' all-source override retains all 19 originals',shown().length===19);
 filter.value='record';filter.onchange();check(rid+' selector restores material context',shown().length===expectedCount);
}
// Existing source without new optional fields retains its original direct/formulation behavior.
const priorLedger=JSON.parse(fs.readFileSync(path.join(dist,'data/paper-reviews/braun2001.json'),'utf8'));
const priorRecord=JSON.parse(fs.readFileSync(path.join(dist,'data/records/braun-2001-system-i.json'),'utf8'));
const priorHost=new Element('div');await mountEvidence(priorHost,priorRecord);
const priorTree=descend(priorHost),priorFilter=priorTree.find(x=>x.attributes['aria-label']==='Figure scope'),priorGallery=priorTree.find(x=>x.className==='guide-evidence-gallery');
priorFilter.value='record';priorFilter.onchange();
const priorFigures=[...priorLedger.figures,...(priorLedger.tables||[]).filter(t=>t.public_asset)],priorLabels=priorLedger.record_formulation_labels[priorRecord.record_id]||[];
check('Prior source retains original relevance logic',priorFigures.every((f,i)=>priorGallery.children[i].hidden===!((f.sample_links||[]).some(x=>(typeof x==='string'?x:x.record_id)===priorRecord.record_id)||(f.formulation_labels||[]).some(x=>priorLabels.includes(x)))));
priorFilter.value='all';priorFilter.onchange();check('Prior source retains all-originals override',priorGallery.children.every(x=>!x.hidden));
