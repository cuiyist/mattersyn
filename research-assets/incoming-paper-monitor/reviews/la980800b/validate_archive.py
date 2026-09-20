from pathlib import Path
import tarfile,hashlib,json
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';p=S/'.sites-runtime/site-v18.tar.gz'
with tarfile.open(p,'r:gz')as tar:
 names={m.name for m in tar.getmembers()if m.isfile()}
 assert 'dist/index.html'in names
 assert not any(n.lower().endswith('.pdf')or 'downloaded_papers/'in n or 'research-assets/'in n for n in names)
 hosting=json.load(tar.extractfile('dist/.openai/hosting.json'));assert hosting['project_id']=='appgprj_6aaad65d939881918d6b5d5254e0f0d9'
 manifest=json.load(tar.extractfile('dist/data/dataset-manifest.json'));assert manifest['dataset_version']=='0.11.0'
 inv=json.load(tar.extractfile('dist/data/inventory-summary.json'));assert inv['summary']['canonical_records']==241 and inv['summary']['public_material_hubs']==22
 for f in (S/'data/records').glob('stiger-1999-*.json'):
  assert json.load(tar.extractfile('dist/data/records/'+f.name))==json.loads(f.read_text(encoding='utf-8'))
 assert 'dist/assets/figures/stiger1999/figure-06b-saed.png'in names
 result={'status':'passed','archive':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'file_count':len(names),'dataset_version':manifest['dataset_version'],'canonical_records':241,'material_hubs':22,'project_id':hosting['project_id'],'checks':['Existing project identity','Static index present','All8Stiger records exact','ActualSAED asset included','Expected dataset and inventory','No raw source PDFs or private research folders']}
(B/'archive-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
