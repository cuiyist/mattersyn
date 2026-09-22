from pathlib import Path
import sys,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1];DEST=ROOT.parent/'mattersyn-github-project'
receipt=json.loads((W/'live-delivery.json').read_text(encoding='utf8'));assert receipt['status']=='passed'
with (ROOT/'MEMORY.md').open('a',encoding='utf8') as f:f.write('\nPublication verified: website version0.34.0 is live at https://cuiyist.github.io/mattersyn-site/. Pages deployment35777260522 succeeded for commit8b1d50201a0ba3d801fa3bdd1b6b9f4403415d93. Sixteen representative anonymous public files match the isolated published checkout byte-for-byte. The live FAPbI3 reader shows all seven property figures and its qualified computed CIF; Reader→Data→Reader navigation was exercised with no console errors. Detailed receipt: `research-assets/reader-redesign-20260922/live-delivery.json`. Corpus review remains paused.\n')
p=W/'browser-verification.json';b=json.loads(p.read_text(encoding='utf8'));b['live_checks']={'FAPbI3_reader_properties':7,'live_data_operations':12,'reader_data_round_trip':'passed','console_errors':0,'public_project_prefix_links':'passed'};p.write_text(json.dumps(b,indent=2)+'\n',encoding='utf8')
# Make future bibliography regeneration retain the separately qualified crystal sources.
p=ROOT/'research-assets/build_reference_readmes.py';s=p.read_text(encoding='utf8')
if '## Crystal reference models' not in s:
    extension='''
# Independent structure sources do not increase the reviewed synthesis-paper count.
registry=read(DIST/'assets/crystal-references/registry.json')
modelrefs=['\\n## Crystal reference models\\n','Reference models support the Reader and are excluded from measured synthesis labels. Full unit-cell provenance, limitations and licenses are in the [reference registry](https://cuiyist.github.io/mattersyn-site/assets/crystal-references/registry.json).\\n']
seen=set()
for item in registry['entries']:
 if not item.get('record_ids') or item['sourceUrl'] in seen:continue
 seen.add(item['sourceUrl']);modelrefs.append('- ['+item['name']+']('+item['sourceUrl']+'). '+item.get('sourceType','Qualified existing reference').replace('_',' ')+'.\\n')
for name in ['README.md','REFERENCES.md']:
 for folder in [ROOT,DIST]:
  target=folder/name
  target.write_text(target.read_text(encoding='utf8').split('\\n## Crystal reference models\\n')[0]+'\\n'.join(modelrefs),encoding='utf8')
'''
    p.write_text(s+extension,encoding='utf8')
sys.path.insert(0,str(ROOT/'research-assets'));import public_projection_policy as policy
rels=['MEMORY.md','research-assets/build_reference_readmes.py','research-assets/github-public-project-sync.json']+['research-assets/reader-redesign-20260922/'+name for name in ['live-delivery.json','browser-verification.json','verify_live_release.py','finalize_delivery_memory.py']]
for rel in rels:
    assert not policy.exclude_path(rel),rel
    clean,_=policy.project_bytes(rel,(ROOT/rel).read_bytes());out=DEST/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(clean)
print('Saved verified live delivery and synchronized seven final project artifacts through the public projection.')
