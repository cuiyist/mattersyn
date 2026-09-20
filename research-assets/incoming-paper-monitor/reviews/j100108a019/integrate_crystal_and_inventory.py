"""Root-owned import of independently validated reference assets and counts."""
from pathlib import Path
import json, hashlib, shutil
B=Path(__file__).resolve().parent
S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=B/'crystal-assets';target=S/'dist/assets/crystal-references'
delta=read(source/'registry-additions.json');registry=read(target/'registry.json')
for entry in delta['entries']:
    assert entry['trainingEligible'] is False and entry['measuredSampleStructure'] is False
    files=[(entry['cifPath'],entry['cifSha256']),(entry['modelPath'],entry['modelSha256']),(entry['finiteModelPath'],entry['finiteModelSha256'])]+[(x['path'],x['sha256']) for x in entry['additionalDownloads']]
    for rel,digest in files:
        assert sha(source/rel)==digest
        dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/rel,dest)
    registry['entries']=[x for x in registry['entries'] if x['id']!=entry['id']]+[entry]
write(target/'registry.json',registry)
adapter=(source/'viewer-adapter.mjs').read_text(encoding='utf-8').split('export function',1)[1]
(S/'dist/finite-crystal-reference.mjs').write_text('export function'+adapter,encoding='utf-8')
assets=read(source/'proposed-record-structure-assets.json')['record_structure_assets']
for rid,items in assets.items():
    path=S/'data/records'/f'{rid}.json';record=read(path)
    before=record['quality']['requested_tasks'][:]
    for item in items:
        item['url']='/'+item['url'].lstrip('/')
        assert item['eligible_as_measured_label'] is False and item['sample_id'] is None
        record['structure_assets']=[x for x in record['structure_assets'] if x['id']!=item['id']]+[item]
    assert record['quality']['requested_tasks']==before
    write(path,record)
bindings_path=S/'dist/assets/chemical-registry/bindings.json';bindings=read(bindings_path)
for path in (S/'data/records').glob('littau-*.json'):
    bindings['sourceRecordSha256'][path.stem]=sha(path)
write(bindings_path,bindings)
inventory=B/'inventory-proposal/inventory-summary.json'
assert read(inventory)['summary']['canonical_records']==168
shutil.copy2(inventory,S/'data/inventory-summary.json')
p=S/'scripts/build_inventory.py';text=p.read_text(encoding='utf-8')
text=text.replace("('Published PbS benchmark rows',", "('Contextual observations',summary.get('contextual_observation_records',0),'Characterization of an earlier or incompletely specified preparation; not a reconstructed synthesis.'),('Published PbS benchmark rows',",1)
text=text.replace('The four categories above;','The five record categories above;')
text=text.replace('<th>Procedures</th><th>Benchmark rows</th>','<th>Procedures</th><th>Observations</th><th>Benchmark rows</th>')
text=text.replace("str(p[k])", "str(p.get(k,0))")
text=text.replace("'procedure_count','benchmark_row_count'", "'procedure_count','contextual_observation_count','benchmark_row_count'")
p.write_text(text,encoding='utf-8')
p=S/'scripts/build_dataset.py';text=p.read_text(encoding='utf-8').replace("'dataset_version':'0.4.0'", "'dataset_version':'0.5.0'")
p.write_text(text,encoding='utf-8')
print('Imported validated reference assets; no measured labels or training tasks added. Inventory renderer includes observations.')
