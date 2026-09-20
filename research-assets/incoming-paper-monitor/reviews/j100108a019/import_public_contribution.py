"""Root-only controlled import of audited source proposals; does not publish."""
import json,hashlib,shutil
from pathlib import Path
BASE=Path(__file__).resolve().parent
SITE=BASE.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

proposal=BASE/'public-record-proposal'
validation=read(proposal/'validation.json');assert validation['status']=='passed' and not validation['errors']
changes=read(proposal/'changes.json');imported=[]
for entry in changes['records']:
    rid=entry['record_id'];draft=BASE/entry['draft_path'];candidate=proposal/'records'/f'{rid}.json'
    assert sha(draft)==entry['audited_draft_sha256'] and sha(candidate)==entry['proposal_sha256'],rid
    old=read(draft);new=read(candidate)
    assert old['measurements']==new['measurements'] and old['products']==new['products'] and old['lineage']==new['lineage']
    assert [(m['id'],m['name'],m['formula'],m['role']) for m in old['materials']]==[(m['id'],m['name'],m['formula'],m['role']) for m in new['materials']]
    destination=SITE/'data/records'/candidate.name
    if destination.exists():assert read(destination)==new,'Refuse to overwrite a diverged canonical record'
    else:shutil.copyfile(candidate,destination)
    imported.append(rid)
assert len(imported)==13

# Recheck the existing registry snapshot before merging, then preserve unchanged assets.
chem=BASE/'molecular-assets';merged=chem/'merged-proposal';report=read(merged/'merge-report.json')
target=SITE/'dist/assets/chemical-registry'
if sha(target/'registry.json')==report['existingRegistrySha256']:
    assert sha(target/'bindings.json')==report['existingBindingsSha256']
    registry=read(merged/'registry.json');bindings=read(merged/'bindings.json')
else:
    registry=read(target/'registry.json');bindings=read(target/'bindings.json')
    assert {e['id'] for e in read(chem/'registry-additions.json')['entries']}<={e['id'] for e in registry['entries']}
for e in read(chem/'registry-additions.json')['entries']:
    for key in ['svgPath','model2dPath','model3dPath']:
        if not e.get(key):continue
        source=chem/e[key];assert sha(source)==e['assetHashes'][key]
        dest=target/e[key];dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():assert sha(dest)==sha(source)
        else:shutil.copyfile(source,dest)
for rid in imported:
    # Only approved review metadata/context relocation changed; identities checked above.
    bindings['sourceRecordSha256'][rid]=sha(SITE/'data/records'/f'{rid}.json')
write(target/'registry.json',registry);write(target/'bindings.json',bindings)

review=read(BASE/'public-review-proposal/littau1993.json')
assert review['review_scope']=='supplied_main_only_si_unverified'
assert set(rid for x in review['recipe_inventory'] for rid in x['record_ids'])==set(imported)
for figure in review['figures']+review['tables']:
    source=BASE/'crop-assets'/Path(figure['public_asset']).name
    assert sha(source)==figure['public_asset_sha256']
    dest=SITE/'dist'/figure['public_asset'];dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():assert sha(dest)==sha(source)
    else:shutil.copyfile(source,dest)
write(SITE/'data/paper-reviews/littau1993.json',review)
write(BASE/'site-import-report.json',{'status':'imported_locally_not_published','record_ids':sorted(imported),'measurements':48,'original_assets':13,'chemical_registry_entries':len(registry['entries']),'chemical_bindings':sum(map(len,bindings['recordBindings'].values())),'source_main_sha256':review['documents'][0]['sha256'],'si_verified':False,'reader_audit_complete':False})
print('Imported 13 records / 48 measurements, 13 original assets and reviewed molecular additions; publication pending.')
