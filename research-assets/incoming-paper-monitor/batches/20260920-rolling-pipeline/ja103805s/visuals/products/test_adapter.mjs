import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {EVANS_SPECIES9,evansSpecies9Context,evansSpecies9Entry,mountEvansSpecies9} from './evans2010-products.mjs';
const P=path.dirname(fileURLToPath(import.meta.url)),E=path.resolve(P,'../..');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,'')),sha=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const checks=[],check=(name,passed)=>checks.push({name,passed:!!passed});
const expected=new Map([['evans-2010-species9-crystallization','species9-crystallization'],['evans-2010-molecular9-structure','species9-cif']]);
const records=fs.readdirSync(path.join(E,'canonical-proposal/v3')).filter(n=>n.startsWith('evans-2010-')&&n.endsWith('.json')).map(n=>read(path.join(E,'canonical-proposal/v3',n)));
for(const r of records){const c=evansSpecies9Context(r);check('record scope '+r.record_id,!!c===expected.has(r.record_id));for(const s of r.products)check('product scope '+r.record_id+'/'+s.sample_id,!!evansSpecies9Context(r,s.sample_id)===(expected.get(r.record_id)===s.sample_id));}
const original=read(path.join(E,'visuals/molecules/registry-additions.json')).entries.find(e=>e.id===EVANS_SPECIES9.registryId);
const data={entries:new Map([[original.id,original]])};
for(const k of ['svgPath','model3dPath'])check('existing exact asset '+k,sha(path.join(E,'visuals/molecules',original[k]))===original.assetHashes[k]);
const r=records.find(r=>r.record_id==='evans-2010-molecular9-structure'),c=evansSpecies9Context(r);
check('original qualified registry accepted',!!evansSpecies9Entry(data,c));
for(const key of ['formula','depictionKind','svgPath','model3dPath']){const e={...original,[key]:'wrong'};check('reject changed '+key,!evansSpecies9Entry({entries:new Map([[e.id,e]])},c));}
for(const key of ['svgPath','model3dPath']){const e={...original,assetHashes:{...original.assetHashes,[key]:'0'.repeat(64)}};check('reject changed asset digest '+key,!evansSpecies9Entry({entries:new Map([[e.id,e]])},c));}
check('reject changed CIF digest',!evansSpecies9Entry({entries:new Map([[original.id,{...original,provenance:{...original.provenance,sourceCifSha256:'wrong'}}]])},c));
check('reject false source group',!evansSpecies9Context({...r,lineage:{source_group:'other'}}));
check('reject false product formula',!evansSpecies9Context({...r,material:{formula:'PbSe'}}));
check('reject missing exact sample',!evansSpecies9Context({...r,products:[]}));
class Element{constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.style={};this.isConnected=true;this.attributes={};this.textContent='';}append(...xs){this.children.push(...xs)}setAttribute(k,v){this.attributes[k]=v}querySelector(s){return this.find(n=>s==='[data-evans-species9]'&&n.dataset?.evansSpecies9)}find(fn){for(const n of this.children){if(fn(n))return n;const q=n.find?.(fn);if(q)return q}return null}}
globalThis.document={createElement:tag=>new Element(tag)};
let opened;const api={chemicalRegistry:async()=>data,chemicalImage:()=>new Element('img'),openChemical:async e=>{opened=e}};
const host=new Element('div'),res=await mountEvansSpecies9(host,r,{chemicalApi:api});
check('mounted exact context',res.mounted&&res.sampleId==='species9-cif');
const btn=host.find(n=>n.tag==='button');await btn.onclick();check('rotate delegates scoped entry',opened.id===original.id&&opened.sourceBindingCaption.includes('20 H'));
const link=host.find(n=>n.tag==='a');check('download uses exact existing model path',link.href.endsWith(EVANS_SPECIES9.model3dPath+'?sha='+EVANS_SPECIES9.modelSha256));
check('one model JSON download',link.download.endsWith('.json'));
check('preview exists',!!host.find(n=>n.tag==='img'));
check('duplicate mount prevented',!(await mountEvansSpecies9(host,r,{chemicalApi:api})).mounted&&host.children.length===1);
check('outside QD mount prevented',!(await mountEvansSpecies9(new Element('div'),records.find(x=>x.record_id==='evans-2010-pbse-qd'),{chemicalApi:api})).mounted);
const detached=new Element('div');detached.isConnected=false;check('detached host not populated',!(await mountEvansSpecies9(detached,r,{chemicalApi:api})).mounted&&detached.children.length===0);
check('missing qualified entry not populated',!(await mountEvansSpecies9(new Element('div'),r,{chemicalApi:api,data:{entries:new Map()}})).mounted);
check('registry not mutated',JSON.stringify(original)===JSON.stringify(read(path.join(E,'visuals/molecules/registry-additions.json')).entries.find(e=>e.id===original.id)));
const report={schema:'mattersyn.product-adapter-author-checks.v1',status:checks.every(c=>c.passed)?'passed':'failed',checks,count:checks.length,record_count:records.length,positive_record_scopes:expected.size,actual_browser_check_separate:true,source_asset_hashes:original.assetHashes,module_sha256:sha(path.join(P,'evans2010-products.mjs'))};
fs.writeFileSync(path.join(P,'author-tests.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,checks:report.count,failures:checks.filter(x=>!x.passed)},null,2));if(report.status!=='passed')process.exitCode=1;
