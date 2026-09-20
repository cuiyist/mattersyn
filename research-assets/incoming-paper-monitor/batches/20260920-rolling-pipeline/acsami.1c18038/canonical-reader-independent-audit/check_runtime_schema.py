"""Execute current Site validators against a private projection; never invoke its build."""
from pathlib import Path
import json,sys,hashlib,shutil
sys.stdout.reconfigure(encoding='utf-8')
A=Path(__file__).resolve().parent;B=A.parent
S=Path(r'[local path redacted]')
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,eligibility
import build_paper_reviews
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
C=B/'canonical-proposal/v1';P=B/'public-review-proposal/v1';projection=A/'isolated-validator-input'
reader=load(P/'lian2021.json');results=[]
for p in C.glob('lian-*.json'):
    r=load(p);errors=validate_record(r);admission=eligibility(r)
    results.append({'record_id':r['record_id'],'errors':errors,'eligibility':admission,'passed':not errors and not any(x['eligible'] for x in admission.values())})
    dest=projection/'data/records'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
sourceassets={a['id']:a for a in load(B/'original-assets-manifest.json')['assets']}
for key in ['figures','tables','schemes','equations','source_notes']:
    for asset in reader[key]:
        if not asset.get('public_asset'):continue
        src=Path(sourceassets[asset['id'].removeprefix('lian2021-')]['path'])
        dest=projection/'dist'/asset['public_asset'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
build_paper_reviews.ROOT=projection
reader_errors=build_paper_reviews.validate(reader)
out={'auditor':'/root/peng1998_reader_assets','scope':'Current Site schema/semantic eligibility and paper-review validator, executed read-only against canonical author records and isolated private projection. No Site build or browser approval.','status':'passed' if all(r['passed'] for r in results) and not reader_errors else 'findings','records':results,'reader_errors':reader_errors,'reader_sha256':sha(P/'lian2021.json'),'validator_hashes':{str(p):sha(p) for p in [S/'scripts/dataset_lib.py',S/'scripts/schema_definition.py',S/'scripts/build_paper_reviews.py',S/'scripts/review_scope.py']}}
(A/'runtime-schema-checks-v1.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':out['status'],'records':len(results),'schema_errors':[x for r in results for x in r['errors']],'reader_errors':reader_errors},ensure_ascii=False))
