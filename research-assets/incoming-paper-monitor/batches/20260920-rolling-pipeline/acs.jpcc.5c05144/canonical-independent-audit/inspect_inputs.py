from pathlib import Path
import json
O=Path(__file__).resolve().parent;J=O.parent;C=J/'canonical-proposal/v1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
src=read(J/'source-extraction-revision-2/source-facts.json');reader=read(C/'reader/sasongko2025.json')
for i,s in enumerate(reader['reader_sections']):
 (O/f'reader-prose-{i}.txt').write_text(s['title']+'\n\n'+'\n\n'.join(x['id']+' | '+x['title']+'\n'+x['text']+'\n'+'\n'.join(x.get('notes',[])) for x in s['items']),encoding='utf8')
(O/'source-facts-compact.txt').write_text('\n\n'.join(x['id']+' | '+x['claim']+'\n'+json.dumps(x['quantities'],ensure_ascii=False) for x in src['facts']),encoding='utf8')
for x in read(C/'record-manifest.json')['records']:
 r=read(x['path']);out={k:r[k] for k in ['record_id','record_type','title','intended_target','materials','stocks','material_states','operations','condition_options','products','context_links','quality']}
 (O/(r['record_id']+'-compact.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print([(s['title'],len(s['items'])) for s in reader['reader_sections']])
