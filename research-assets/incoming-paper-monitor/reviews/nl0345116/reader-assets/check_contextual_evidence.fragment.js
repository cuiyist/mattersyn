const gradeFacts=items.flatMap(x=>x.facts).filter(f=>f.canonical_condition_option_id);
check('All eight alternative-grade quantities executed',gradeFacts.length===8&&gradeFacts.every(f=>[90,99].includes(f.value)&&f.qualifier.includes('Alternative source reagent grade')&&cardMap.get('topo').textContent.includes(f.qualifier)));
globalThis.fetch=async rel=>{const url=String(rel),p=url.startsWith('file:')?fileURLToPath(url):path.resolve(dist,url);if(!path.resolve(p).startsWith(path.resolve(dist)+path.sep))throw Error('Unexpected evidence path');return{ok:fs.existsSync(p),json:async()=>JSON.parse(fs.readFileSync(p,'utf8'))};};
const {mountEvidence}=await import(pathToFileURL(path.join(dist,'material-guide.mjs')).href+'?audit='+Date.now());
for(const [suffix,required]of [['individual-low',['figure-1']],['sphere-intermediate',['figure-1','figure-4']],['wire-intermediate',['figure-2','figure-3','figure-5']],['wire-high',['figure-2','figure-3','figure-5']]]){
 const rid='sashchiuk-2004-'+suffix,record=JSON.parse(fs.readFileSync(path.join(dist,'data/records',rid+'.json'),'utf8')),host=new Element('div');await mountEvidence(host,record,{materialFormula:'PbSe'});
 const tree=descend(host),gallery=tree.find(x=>x.className==='guide-evidence-gallery'),filter=tree.find(x=>x.attributes['aria-label']==='Figure scope');
 check(rid+' gallery and selector mounted',!!filter&&gallery?.children.length===5);filter.value='record';filter.onchange();
 const shown=()=>ledger.figures.filter((f,i)=>!gallery.children[i].hidden).map(f=>f.id);
 check(rid+' precise source-context figures',JSON.stringify(shown().sort())===JSON.stringify([...required].sort()));
 check(rid+' specimen and ratio caveat visible',host.textContent.includes(ledger.material_asset_scope_note));
 const links=tree.filter(x=>x.tagName==='a').map(x=>String(x.href));check(rid+' explicit context links',ledger.route_evidence_contexts[rid].every(id=>links.some(url=>url.endsWith('/records/'+id+'.html'))));
 filter.value='all';filter.onchange();check(rid+' all five original figures accessible',shown().length===5);filter.value='record';filter.onchange();check(rid+' context restored',shown().length===required.length);
}
const crystalRegistry=JSON.parse(fs.readFileSync(path.join(dist,'assets/crystal-references/registry.json'),'utf8'));
const ideal=crystalRegistry.entries.find(x=>x.id==='sashchiuk-2004-pbse-ideal-reference');
check('Constructed ideal reference retains provenance',ideal?.referenceOnly===true&&ideal?.measuredSampleStructure===false&&ideal?.trainingEligible===false&&ideal?.referenceType==='locally_constructed_ideal_reference');
check('Ideal reference is bound to exactly four synthesis routes',ideal?.record_ids.length===4&&ideal.record_ids.every(x=>ledger.route_evidence_contexts[x]));
for(const [key,hkey]of [['cifPath','cifSha256'],['modelPath','modelSha256'],['finiteModelPath','finiteModelSha256']])check('Reference '+key+' exact downloadable bytes',!!ideal?.[key]&&digest(path.join(dist,'assets/crystal-references',ideal[key]))===ideal[hkey]);
for(const x of ideal?.additionalDownloads||[])check('Additional reference download '+x.label,digest(path.join(dist,'assets/crystal-references',x.path))===x.sha256);
globalThis.window={};const {mountCrystalReferences}=await import(pathToFileURL(path.join(dist,'crystal-viewer.mjs')).href+'?audit='+Date.now());
for(const rid of ideal?.record_ids||[]){const r=JSON.parse(fs.readFileSync(path.join(dist,'data/records',rid+'.json'),'utf8')),host=new Element('div');await mountCrystalReferences(host,r);const tree=descend(host);check(rid+' ideal-reference disclosure mounted',host.textContent.includes(ideal.scope));check(rid+' CIF download mounted',tree.some(x=>x.tagName==='a'&&String(x.href).includes(ideal.cifPath)));}
