from pathlib import Path
import json,hashlib,shutil
P=Path(__file__).resolve().parent;E=P.parent.parent
S=Path(r'[local path redacted]')
M=E/'visuals/molecules';V=P/'preview'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
entry=next(x for x in load(M/'registry-additions.json')['entries'] if x['id']=='evans2010-species9-reference')
public=[]
for k in ['svgPath','model3dPath']:
 src=M/entry[k];assert sha(src)==entry['assetHashes'][k]
 dst=V/'assets/chemical-registry'/entry[k];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 public.append({'existing_source_path':str(src),'public_path':'assets/chemical-registry/'+entry[k],'sha256':sha(src),'new_model_created':False})
V.mkdir(parents=True,exist_ok=True)
for src,dst in [(P/'evans2010-products.mjs',V/'evans2010-products.mjs'),(S/'chemical-viewer.mjs',V/'chemical-viewer.mjs'),(S/'vendor/3Dmol-min.js',V/'vendor/3Dmol-min.js')]:
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
write(V/'assets/chemical-registry/registry.json',{'entries':[entry]})
write(V/'assets/chemical-registry/bindings.json',{'recordBindings':{}})
records=[];bindings=[]
for rid,sid,loc in [('evans-2010-species9-crystallization','species9-crystallization','SI S15–S16; isolated species9 crystallization'),('evans-2010-molecular9-structure','species9-cif','SI S15 and supplied molecular species9 CIF')]:
 src=E/'canonical-proposal/v3'/(rid+'.json');r=load(src);sample=next(x for x in r['products'] if x['sample_id']==sid)
 records.append({k:r[k] for k in ['record_id','lineage','material','products']})
 bindings.append({'record_id':rid,'sample_id':sid,'source_sample_label':sample['source_sample_label'],'canonical_record_path':str(src),'canonical_sha256':sha(src),'registry_id':entry['id'],'source_locator':loc,'existing_model_public_path':'assets/chemical-registry/'+entry['model3dPath'],'model_sha256':entry['assetHashes']['model3dPath'],'source_cif_sha256':entry['provenance']['sourceCifSha256'],'sample_mapping_qualification':'Molecular species9 only; no physical batch identity beyond the source context is inferred.','intended_canonical_promotion':{'structure_asset_role':'measured_sample','coordinate_basis':'Source single-crystal refinement including calculated riding hydrogen sites; documented CIF-to-Cartesian transform.','eligible_as_measured_label':False,'requested_tasks':[]},'independent_adapter_review':'pending'})
write(V/'preview-records.json',records)
write(P/'product-bindings-proposal.json',{'schema':'mattersyn.evans-species9-product-adapter.v1','source_id':'evans2010','status':'private_author_proposal','bindings':bindings,'excluded_scope':'Every other record and sample, including all PbSe/CdSe QDs and magic-size clusters, DPPSe crystals, solution intermediates and intermolecular-packing-only context.','unchanged_assets':public,'new_model_or_cif_qualification':False,'root_promotion_note':'Root may add source-qualified structure_assets links to the two exact products to suppress the generic no-coordinates message. No scientific quantity, coordinate, sample identity or task eligibility is changed by this adapter.'})
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Evans species 9 · product adapter preview</title><style>
body{font:16px/1.55 system-ui,sans-serif;color:#17354a;background:#edf3f6;margin:0}main{max-width:860px;margin:28px auto;padding:0 20px}h1{font-size:28px}h4{font-size:22px;margin:0 0 8px}button,a{font:inherit}button{border:1px solid #51768d;background:#fff;color:#153c56;border-radius:7px;padding:9px 12px;cursor:pointer}a{color:#165d8d}.protocol-controls{display:flex;align-items:center;gap:16px;flex-wrap:wrap}.chemical-caption{color:#435d6d}.guide-notice{font-size:14px;color:#435d6d}.guide-molecule-dialog{border:1px solid #7494a5;border-radius:15px;width:min(900px,90vw);max-height:90vh;box-sizing:border-box;padding:24px}.guide-molecule-dialog::backdrop{background:#17354a80}.guide-molecule-dialog header{display:flex;align-items:center;justify-content:space-between;gap:10px}.guide-molecule-dialog h2{font-size:22px}.molecule-model{width:100%;height:420px;position:relative}.functional-group-controls{display:flex;gap:12px;flex-wrap:wrap;font-size:14px}select{padding:8px;font:inherit;width:100%}</style>
<main><h1>Final structures · molecular species 9</h1><p>Private integration preview using the existing qualified molecular model.</p><label for="record">Source context</label><select id="record"></select><div id="product"></div></main><script src="./vendor/3Dmol-min.js"></script><script type="module">
import {mountEvansSpecies9} from './evans2010-products.mjs';
const records=await(await fetch('./preview-records.json')).json(),select=document.getElementById('record');for(const [i,r] of records.entries()){const o=document.createElement('option');o.value=i;o.textContent=i?'Single-crystal structure context':'Species 9 crystallization';select.append(o)}
async function render(){const host=document.getElementById('product');host.replaceChildren();window.adapterResult=await mountEvansSpecies9(host,records[Number(select.value)]);}
select.onchange=render;await render();</script></html>'''
(V/'index.html').write_text(html,encoding='utf-8')
print('Prepared only private adapter, bindings, and preview snapshots. No new coordinates or shared writes.')
