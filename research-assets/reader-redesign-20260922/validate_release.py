from pathlib import Path
import hashlib,json,subprocess,urllib.parse,math
W=Path(__file__).resolve().parent;S=W.parents[1]/'recipe-atlas';D=S/'dist'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def ck(label,value):checks.append({'check':label,'passed':bool(value)})
for rel,h in read(W/'scientific-baseline.json').items():ck('Scientific bytes preserved: '+rel,sha(S/rel)==h)
presentation=read(D/'data/reader-presentation.json');index=read(D/'data/materials-index.json')
ck('All 50 hubs retained',len(index['materials'])==len(presentation['materials'])==50)
ck('All 123 synthesis routes',len(presentation['records'])==123)
for rid,r in presentation['records'].items():
    ck('Route HTML and JSON: '+rid,(D/'records'/f'{rid}.html').is_file() and (D/r['data_links']['record']).is_file())
    for kind in ['full_review','record_page']:
        url=r['data_links'].get(kind)
        if url:
            u=urllib.parse.urlsplit(url);ck('Reader destination '+rid+'/'+kind,(D/u.path).is_file())
            if u.path=='paper-review.html':ck('Review data '+rid,(D/'data/paper-reviews'/f"{urllib.parse.parse_qs(u.query)['id'][0]}.json").is_file())
    for f in r['figures']:
        if f.get('public_asset'):ck('Figure '+rid+'/'+f['id'],(D/f['public_asset']).is_file())
reg=read(D/'assets/crystal-references/registry.json')
for r in reg['entries']:
    for k in ['modelPath','cifPath','finiteModelPath']:
        if r.get(k):ck('Structure asset '+r['id']+'/'+k,(D/'assets/crystal-references'/r[k]).is_file())
    m=read(D/'assets/crystal-references'/r['modelPath'])
    ck('Complete cell '+r['id'],all(isinstance(m.get('cell',{}).get(k),(float,int)) for k in ['a','b','c','alpha','beta','gamma']))
    ck('Finite reference coordinates '+r['id'],all(all(isinstance(a.get(k),(float,int)) and math.isfinite(a[k]) for k in ['x','y','z']) for a in m['atoms']))
for rid,bindings in read(D/'data/reader-stock-bindings.json')['stockBindings'].items():
    contexts=[x for x in read(D/'assets/chemical-registry/solution-components.json')['contexts'] if x['record_id']==rid]
    source=read(S/'data/records'/f'{rid}.json')
    for stock,context in bindings.items():ck('Stock binding '+rid+'/'+stock,any(s['id']==stock for s in source['stocks']) and any(c.get('id')==context for c in contexts))
for eid,row in read(D/'data/chemical-thumbnail-map.json')['entries'].items():
    ck('Unchanged chemical depiction '+eid,sha(D/row['original_svg'])==row['original_sha256'])
    ck('Thumbnail exists '+eid,(D/row['thumbnail_path']).is_file())
node=Path(r'[local path redacted]')
for p in [*D.glob('reader-*.mjs'),D/'chemical-viewer.mjs',D/'protocol-references.mjs',D/'protocol-visuals.mjs',D/'crystal-viewer.mjs']:
    proc=subprocess.run([str(node),'--check',str(p)],capture_output=True);ck('JavaScript syntax '+p.name,proc.returncode==0)
summary={'status':'passed' if all(c['passed'] for c in checks) else 'failed','checks':len(checks),'failures':[c for c in checks if not c['passed']],'scope':'Canonical/export byte preservation; all50hubs/123routes; figure, stock and chemical transport; reference assets/cell fields; changed JavaScript syntax. Browser verification is recorded separately.'}
(W/'release-validation.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,indent=2));raise SystemExit(bool(summary['failures']))
