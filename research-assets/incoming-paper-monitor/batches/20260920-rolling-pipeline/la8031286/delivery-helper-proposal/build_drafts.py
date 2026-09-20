"""Author private helper drafts only. Never applies them to Site/shared files."""
from pathlib import Path
import json,hashlib,ast,datetime
D=Path(__file__).resolve().parent;N=D.parent;M=N.parents[4];MON=N.parents[2];T=N.parent/'acsanm.2c04342'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,text):(D/name).write_text(text,'utf8')
def save(name,obj):write(name,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
base=read(T/'site-integration-proposal/release-endpoints.json');assert base['count']==len(base['paths'])==219
pm=read(N/'site-integration-proposal/v1/promotion-manifest.json');rm=read(N/'canonical-proposal/v2/record-manifest.json')
extra=['data/paper-reviews/pati2009.json']+[a['public_path']for a in pm['public_assets']]+[prefix+r['record_id']+suffix for r in rm['records']for prefix,suffix in [('records/','.html'),('data/records/','.json')]]
assert len(pm['public_assets'])==66 and len(rm['records'])==19 and len(extra)==105 and len(set(base['paths']+extra))==324
sources=['heo2003','evans2010','morrison2017','lian2021','ghosh2012','sommer2020','matuhina2023','pati2009'];withheld=[f'assets/figures/{s}/pages/{d}-01.png'for s in sources for d in ['main','si']]
save('release-endpoints.json',{'dataset_version':'0.31.0','source_id':'pati2009','paths':base['paths']+extra,'count':324,'expected_citation_count':39,'additional_withheld_paths':withheld,'additional_withheld_count':16,'extra_endpoints':105,'extra_scope':'One reader, 66 passed public assets and both HTML/JSON endpoints for 19 records. Previous219 endpoints retained.'})
verifier=M/'research-assets/verify_public_delivery.py';s=verifier.read_text('utf8');assert 'data/paper-reviews/pati2009.json'not in s
s=s.replace('assert len(paths)==len(set(paths))',"if (D/'data/paper-reviews/pati2009.json').exists():\n paths += "+repr(extra)+"\nassert len(paths)==len(set(paths))")
s=s.replace('withheld_checks=[',"if (D/'data/paper-reviews/pati2009.json').exists():withheld += ['assets/figures/pati2009/pages/main-01.png','assets/figures/pati2009/pages/si-01.png']\nwithheld_checks=[")
write('verify_public_delivery-proposed.py',s)
snap=D/'input-snapshots';snap.mkdir(exist_ok=True);(snap/'verify_public_delivery.py').write_bytes(verifier.read_bytes())
s=(T/'finalize_reader_publication.py').read_text('utf8').replace("N=Path(__file__).resolve().parent;O=", "N=Path(__file__).resolve().parent\nif N.name=='delivery-helper-proposal':N=N.parent\nO=")
s=s.replace('matuhina2023','pati2009').replace('0.30.0','0.31.0').replace('==38','==39').replace('==219','==324').replace('==14','==16')
s=s.replace("'ghosh2012','sommer2020','pati2009']", "'ghosh2012','sommer2020','matuhina2023','pati2009']")
write('finalize_reader_publication.py',s)
s=(T/'prepare_publication_rule.py').read_text('utf8').replace("N=Path(__file__).resolve().parent;O=", "N=Path(__file__).resolve().parent\nif N.name=='delivery-helper-proposal':N=N.parent\nO=")
s=s.replace('matuhina2023','pati2009').replace('0.30.0','0.31.0').replace('38citations,219allowlisted','39 citations, 324 allowlisted').replace("'author':'/root'","'author':'/root/norberg2004_extract','executed_by':'root after review'")
write('prepare_publication_rule.py',s)
s=(T/'sync_release_delta.py').read_text('utf8')
s=s.replace("L=Path(__file__).resolve().parent;MON=", "L=Path(__file__).resolve().parent\nif L.name=='delivery-helper-proposal':L=L.parent\nMON=")
s=s.replace('matuhina-review-scope-20260920.json','pati-review-scope-20260920.json').replace('matuhina-published-scope-20260920.json','pati-published-scope-20260920.json')
start=s.index('folders=[L,');end=s.index('for folder in folders:',start)
s=s[:start]+"folders=[L,L.parent/'acsanm.2c04342',L.parent/'intake-20260920T114139Z',MON/'deadline-20260920/admission-20260920T114139Z',M/'skills',M/'recipe-atlas/data',M/'recipe-atlas/dist',M/'recipe-atlas/scripts']\nfolders += [L.parent/'acs.inorgchem.8b02945',L.parent/'intake-20260920T133256Z',MON/'deadline-20260920/admission-20260920T133256Z']\n"+s[end:]
s=s.replace("files += [MON/'deadline-20260920/pati-published-scope-20260920.json']", "files += [p for p in [MON/'deadline-20260920/pati-published-scope-20260920.json'] if p.is_file()]")
write('sync_release_delta.py',s)
prepare='''"""Root applies reviewed helper drafts; --check is read-only and the default."""
from pathlib import Path
import argparse,json,hashlib,shutil
D=Path(__file__).resolve().parent;N=D.parent;M=N.parents[4]
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
manifest=read(D/'package-manifest.json')
for row in manifest['files']:assert sha(D/row['path'])==row['sha256'],row['path']
target=M/'research-assets/verify_public_delivery.py';original=D/'input-snapshots/verify_public_delivery.py';proposed=D/'verify_public_delivery-proposed.py'
assert sha(target) in {sha(original),sha(proposed)},'Shared verifier changed; prepare a new reviewed delta.'
assert read(D/'release-endpoints.json')['count']==324
if args.apply:
 for name in ['finalize_reader_publication.py','prepare_publication_rule.py','sync_release_delta.py','release_pati.py']:
  p=N/name
  if p.exists():assert p.read_bytes()==(D/name).read_bytes(),str(p)
  else:shutil.copyfile(D/name,p)
 destination=N/'site-integration-proposal/release-endpoints.json'
 if destination.exists():assert destination.read_bytes()==(D/'release-endpoints.json').read_bytes()
 else:shutil.copyfile(D/'release-endpoints.json',destination)
 target.write_bytes(proposed.read_bytes())
 print('Applied reviewed verifier extension and local helpers; no publication or network verification run.')
else:print('Draft checks passed; no mutation. Root may apply after independent review.')
'''
write('prepare_delivery_helpers.py',prepare)
print('Private drafts generated. Final author validation/manifest follows after release helper authorship.')
