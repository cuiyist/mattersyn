import fs from 'node:fs';import path from 'node:path';import vm from 'node:vm';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
const B=path.dirname(fileURLToPath(import.meta.url)),O=path.join(B,'visuals/products');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const checks=[];function check(id,ok){checks.push({id,passed:!!ok});}
const html=fs.readFileSync(path.join(O,'preview.html'),'utf8'),data=JSON.parse(html.match(/<script id="data" type="application\/json">([\s\S]*?)<\/script>/)[1]),code=html.match(/<script>([\s\S]*?)<\/script>/)[1];
fs.writeFileSync(path.join(O,'preview-inline-check.js'),code);
const script=new vm.Script(code);check('Inline JavaScript parses',true);
const nodes=new Map();
function node(tag){return {tagName:tag,textContent:'',value:'',children:[],handlers:{},append(...c){this.children.push(...c);if(this.tagName==='select'&&!this.value&&c[0])this.value=c[0].value;},addEventListener(k,fn){this.handlers[k]=fn;}};}
for(const id of ['context','data','title','diagram','caption','phase','measurements','lineage','originals'])nodes.set(id,node(id==='context'?'select':'div'));
nodes.get('data').textContent=JSON.stringify(data);
const document={getElementById:id=>nodes.get(id),createElement:node};script.runInNewContext({document});
check('Exactly 22 source context options',nodes.get('context').children.length===22);
check('Exactly two original image cards',nodes.get('originals').children.length===2);
for(const c of data.contexts){
 const r=read(path.join(B,'canonical-drafts',c.record_id+'.json')),p=r.products.find(x=>x.sample_id===c.sample_id);
 check(c.context_id+' exact canonical product copy',JSON.stringify(p)===JSON.stringify(c.canonical_product));
 check(c.context_id+' exact canonical source hash',sha(path.join(B,'canonical-drafts',c.record_id+'.json'))===c.canonical_record_sha256);
 check(c.context_id+' actual SVG available',fs.existsSync(path.join(O,c.private_svg)));
 nodes.get('context').value=c.context_id;nodes.get('context').handlers.change();
 check(c.context_id+' chosen SVG renders',nodes.get('diagram').src===c.private_svg);
 check(c.context_id+' chosen source caption renders',nodes.get('caption').textContent===c.source_caption);
 check(c.context_id+' scoped phase display',c.sample_id==='si-xrd-cds'?nodes.get('phase').textContent.includes('hexagonal wurtzite'):nodes.get('phase').textContent==='Phase: not assigned to this exact context.');
 check(c.context_id+' no model or download assignment',c.model_phase===null&&c.unit_cell_asset===null&&c.finite_atomic_asset===null&&c.cif_download===null&&c.vesta_download===null);
 for(const m of c.associated_source_measurements){const index=Number(m.canonical_pointer.split('/').at(-1));check(c.context_id+' exact measurement '+m.measurement.id,JSON.stringify(r.measurements[index])===JSON.stringify(m.measurement));}
}
for(const x of data.originals){check(x.reader_figure.id+' original bytes exact',sha(path.join(O,x.private_copy))===x.sha256&&x.sha256===x.reader_figure.public_asset_sha256);}
const failures=checks.filter(x=>!x.passed);const out={schema:'mattersyn.private-product-preview-author-check/1',source_id:'nagasaki2004',created_at:new Date().toISOString(),status:failures.length?'findings':'passed_author_checks',scope:'Actual private inline JavaScript executed with a DOM stub for all 22 selector states, canonical payload comparisons and local resource hashes. No live-browser/layout or independent scientific audit claim.',counts:{checks:checks.length,failures:failures.length,contexts:data.contexts.length},checks,failures,preview_sha256:sha(path.join(O,'preview.html')),helper_sha256:sha(fileURLToPath(import.meta.url))};
fs.writeFileSync(path.join(O,'preview-author-check.json'),JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify({status:out.status,counts:out.counts,failures},null,2));
