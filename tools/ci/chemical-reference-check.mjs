// CI-only checks of actual candidate precursor buttons and 3D modal flows.
// No I/O on import. No build, model generation, publication or external lookup.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';

const KIM='kim2013-pbs-ionic-liquid-am3029766-pbs-qd';
const key=s=>String(s).trim().replace(/\s+/g,' ').toLowerCase();
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const widths=[1440,390];

export function selectTargets(registry,bindings,overlay,recordHasMaterial=()=>true){
 const entries=new Map(registry.entries.map(e=>[e.id,e]));
 const targets=[],used=new Set();
 const binding=(eid,forced)=>{
  for(const [rid,row]of Object.entries(bindings.recordBindings).sort(([a],[b])=>a.localeCompare(b))){
   if(forced&&rid!==forced)continue;
   for(const [mid,id]of Object.entries(row))if(id===eid&&recordHasMaterial(rid,mid))return {record_id:rid,material_id:mid};
  }return null;
 };
 const add=(id,eid,forced)=>{
  const e=entries.get(eid),ref=overlay.entries[eid]||{},b=binding(eid,forced);
  assert(e&&b,`No actual Reader precursor binding for ${id}`);
  targets.push({id,registry_id:eid,...b,name:e.name,route:ref.route||'existing_molecule',reference:ref,entry:e});used.add(eid);
 };
 for(const [id,names]of [['oa',['oleic acid','oa']],['ode',['1-octadecene','ode']],['ethanol',['ethanol']],['acetone',['acetone']]]){
  const hits=[...new Set(Object.values(bindings.recordBindings[KIM]||{}))].filter(eid=>names.includes(key(entries.get(eid)?.name)));
  assert.equal(hits.length,1,`Kim2013 ${id} must name exactly one bound identity`);add('kim2013-'+id,hits[0],KIM);
 }
 for(const [id,name,suffix,flat]of [['hmds','hexamethyldisilathiane',null,false],['octane','octane',null,false],['hexane-wash','hexane','--hexane-wash',false],['hexane-tem','hexane','--hexane-tem',false],['pbo','lead oxide',null,true]]){
  const hits=Object.entries(bindings.recordBindings[KIM]||{}).filter(([mid,eid])=>key(entries.get(eid)?.name)===name&&(!suffix||mid.endsWith(suffix)));
  assert.equal(hits.length,1,`Kim2013 ${id} must retain one exact source material binding`);add('kim2013-'+id,hits[0][1],KIM);assert.equal(targets.at(-1).route==='flat',flat,`Kim2013 ${id} reference disposition differs`);
 }
 for(const [id,predicate]of [
  ['reused-molecule',r=>r.route==='molecule_reference'&&['identical_CID','unique_exact_compound_name','owner_fixed_named_identity'].includes(r.reason)],
  ['computed-molecule',r=>r.route==='molecule_reference'&&r.reason==='validated_connectivity_computed_conformer'],
  ['independent-ions',r=>r.route==='independent_component_references'&&!r.namedLigandReference],
  ['ambient-cell',r=>r.route==='ambient_crystal_reference'],
  ['flat-reason',r=>r.route==='flat'&&typeof r.whyNo3d==='string'&&r.whyNo3d.length>0],
 ]){
  const existing=targets.find(t=>predicate(t.reference));
  if(existing){existing.covers=[...(existing.covers||[]),id];continue;}
  const hit=Object.entries(overlay.entries).sort(([a],[b])=>a.localeCompare(b)).find(([eid,r])=>predicate(r)&&binding(eid));
  assert(hit,`No actual bound ${id} target in generated overlay`);add(id,hit[0]);
 }
 const namedId='name-card-indium-palmitate',named=overlay.entries[namedId];
 assert(named?.route==='independent_component_references'&&named.namedLigandReference?.entry_id===namedId,'Exact indium-palmitate named-ligand reference required');
 add('named-ligand-reference',namedId);
 return targets;
}

async function run({base,dist,out}){
 const output=path.resolve(out);assert(!fs.existsSync(output),'Fresh browser receipt directory required');fs.mkdirSync(output,{recursive:true});
 const root=new URL(base);assert(['http:','https:'].includes(root.protocol)&&!root.username&&!root.password&&!root.search&&!root.hash);if(!root.pathname.endsWith('/'))root.pathname+='/';
 const load=rel=>JSON.parse(fs.readFileSync(path.join(dist,rel),'utf8'));
 const files=['assets/chemical-registry/registry.json','assets/chemical-registry/bindings.json','assets/chemical-registry/reader-3d-reference-overrides.json'];
 const [registry,bindings,overlay]=files.map(load),recordCache=new Map();
 const eligible=(rid,mid)=>{
  assert(/^[A-Za-z0-9._-]+$/.test(rid)&&/^[A-Za-z0-9._-]+$/.test(mid));
  if(!fs.existsSync(path.join(dist,'data/reader/chemicals',rid+'.json')))return false;
  if(!recordCache.has(rid))recordCache.set(rid,load('data/records/'+rid+'.json'));
  return recordCache.get(rid).materials.some(m=>m.id===mid);
 };
 const targets=selectTargets(registry,bindings,overlay,eligible);
 const receipt={schema:'MatterSyn-H-actual-precursor-modal-browser-check/1',started_utc:new Date().toISOString(),inputs:files.map(file=>({path:file,sha256:sha(fs.readFileSync(path.join(dist,file)))})),targets:targets.map(({entry,reference,...t})=>t),views:[],errors:[]};
 const require=createRequire(path.join(process.env.PLAYWRIGHT_DIR||process.cwd(),'package.json')),{chromium}=require('playwright');
 let browser;
 try{
  browser=await chromium.launch();
  for(const width of widths)for(const target of targets){
   const page=await browser.newPage({viewport:{width,height:900},deviceScaleFactor:1}),errors=[];page.on('pageerror',e=>errors.push(String(e.message)));
   try{
    const url=new URL('records/'+target.record_id+'.html?view=reader',root);await page.goto(url.href,{waitUntil:'domcontentloaded'});
    const card=page.locator('.reader-chemical[data-material-id="'+target.material_id+'"]');await card.waitFor({state:'visible',timeout:30000});
    const button=card.locator('button.molecule-link').first();const isFlat=target.route==='flat';assert.equal((await button.textContent()).trim(),isFlat?'View formula ↗':'Rotate 3D ↗');
    const ref=target.reference,component=ref.component3dModels?.[0];
    const modelPath=isFlat?null:target.route==='ambient_crystal_reference'?'assets/crystal-references/'+ref.crystalReference.modelPath:'assets/chemical-registry/'+(component?.model3dPath||ref.model3dPath||target.entry.model3dPath);
    const expectedSha=isFlat?null:target.route==='ambient_crystal_reference'?ref.crystalReference.modelSha256:component?.model3dSha256||ref.model3dSha256||target.entry.assetHashes?.model3dPath;
    const modelURL=modelPath?new URL(modelPath,root):null;
    const responseWait=modelURL?page.waitForResponse(r=>new URL(r.url()).pathname===modelURL.pathname&&r.status()===200,{timeout:30000}):null;
    await button.click();const dialog=page.locator('dialog.reader-molecule-dialog');await dialog.waitFor({state:'visible'});
    if(component){const scope=dialog.locator('.independent-molecular-components');await scope.waitFor({state:'visible'});assert.match(await scope.textContent(),/no geometry between ions|no relative ion geometry|no inter-ion geometry/i);const rows=scope.locator('.independent-molecular-component');assert.equal(await rows.count(),ref.component3dModels.length);for(let i=0;i<ref.component3dModels.length;i++){const c=ref.component3dModels[i],identity=rows.nth(i).locator('.chemical-component-identity');await identity.waitFor({state:'visible'});assert.equal((await identity.textContent()).trim(),[...new Set([c.name,c.formula].filter(Boolean))].join(' · '));assert.equal((await rows.nth(i).locator('button').textContent()).trim(),'Rotate 3D ↗');}await rows.first().locator('button').click();}
    let modelPin=null,rotation=null;
    if(isFlat){await dialog.getByText(ref.whyNo3d,{exact:true}).waitFor();assert.equal(await dialog.locator('canvas').count(),0);}
    else{
     const response=await responseWait,body=await response.body();assert.equal(sha(body),expectedSha,'Browser loaded the wrong model bytes');modelPin={path:modelPath,bytes:body.length,sha256:sha(body)};
     const canvas=dialog.locator('canvas').first();await canvas.waitFor({state:'visible'});await canvas.scrollIntoViewIfNeeded();await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
     const before=sha(await canvas.screenshot()),box=await canvas.boundingBox();assert(box&&box.width>40&&box.height>40,'3D canvas is not usable');
     await page.mouse.move(box.x+box.width*.4,box.y+box.height*.5);await page.mouse.down();await page.mouse.move(box.x+box.width*.65,box.y+box.height*.6,{steps:8});await page.mouse.up();await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
     const after=sha(await canvas.screenshot());assert.notEqual(before,after,'Dragging did not change the rendered model');rotation={before_png_sha256:before,after_png_sha256:after,changed:true};
     assert.doesNotMatch(await dialog.textContent(),/Source-qualified identity\/formula only|No atoms, bonds, bound surface geometry, molecular conformer or measured coordinates are assigned/);
    }
    const overflow=await dialog.evaluate(d=>({scroll:d.scrollWidth,client:d.clientWidth,left:d.getBoundingClientRect().left,right:d.getBoundingClientRect().right}));assert(overflow.scroll<=overflow.client+1&&overflow.left>=-1&&overflow.right<=width+1,'Modal overflows phone/desktop viewport');
    assert.deepEqual(errors,[],'Uncaught script error');const filename=target.id+'-'+width+'-modal.png';await dialog.screenshot({path:path.join(output,filename),animations:'disabled'});
    receipt.views.push({id:target.id,width,record_id:target.record_id,registry_id:target.registry_id,route:target.route,model:modelPin,rotation,overflow,screenshot:{path:filename,sha256:sha(fs.readFileSync(path.join(output,filename)))},passed:true});
   }catch(e){receipt.errors.push({id:target.id,width,message:String(e.message)});throw e;}finally{await page.close();}
  }
 }catch(e){if(!receipt.errors.length)receipt.errors.push({message:String(e.message)});throw e;}
 finally{await browser?.close();receipt.finished_utc=new Date().toISOString();receipt.passed=receipt.errors.length===0&&receipt.views.length===targets.length*widths.length;fs.writeFileSync(path.join(output,'receipt.actual.json'),JSON.stringify(receipt,null,2)+'\n');}
}

if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
 const args=process.argv.slice(2);if(!args.length){console.log('DEFAULT INERT: supply --base, --dist and --out for the CI candidate.');}
 else{const options={};for(let i=0;i<args.length;i+=2){assert(['--base','--dist','--out'].includes(args[i])&&args[i+1]);options[args[i].slice(2)]=args[i+1];}assert(options.base&&options.dist&&options.out);await run(options);}
}
