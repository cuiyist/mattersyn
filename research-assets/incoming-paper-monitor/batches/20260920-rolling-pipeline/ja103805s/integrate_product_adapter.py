from pathlib import Path
import hashlib,json,shutil
E=Path(__file__).resolve().parent;S=E.parents[4]/'recipe-atlas';P=E/'visuals/products';O=E/'site-integration-proposal'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'package-freeze.json')=='47fa08d95c2a553768bd190966ab9cf5a15201d5bdf1bc1faf4e2f037c3d5e33'
assert sha(P/'evans2010-products.mjs')=='ae87a6f413ab86fe8667519aba83077a485700250ebcc55a4238a33fbbc30ccd'
shutil.copy2(P/'evans2010-products.mjs',S/'dist/evans2010-products.mjs')
p=S/'dist/crystal-viewer.mjs';t=p.read_text(encoding='utf8');assert 'mountEvansSpecies9' not in t
old='if(await mountHeoAverage(host,r))return;await productIdentity(host,r);'
new='if(await mountHeoAverage(host,r))return;if((await mountEvansSpecies9(host,r)).mounted)return;await productIdentity(host,r);'
assert t.count(old)==1
p.write_text("import {mountEvansSpecies9} from './evans2010-products.mjs';\n"+t.replace(old,new),encoding='utf8')
(O/'product-adapter-integration.json').write_text(json.dumps({'status':'local_integration_pending_independent_audit','freeze_sha256':sha(P/'package-freeze.json'),'module_sha256':sha(S/'dist/evans2010-products.mjs'),'crystal_viewer_sha256':sha(p),'before':old,'after':new,'source_model_unchanged':True,'allowed_record_ids':['evans-2010-species9-crystallization','evans-2010-molecular9-structure']},indent=2)+'\n',encoding='utf8')
print('Integrated existing species 9 molecular adapter with exact context gates.')
