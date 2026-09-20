import json,hashlib,re,ast,html,difflib,urllib.parse
from pathlib import Path
O=Path(__file__).resolve().parent;L=O.parent;P=L/'site-integration-proposal';V=P/'v1';S=Path('[local path redacted]')
def rd(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[];bound={}
def bind(p):bound[str(p)]=sha(p)
def check(n,b,detail=None):
    checks.append({'check':n,'passed':bool(b),'detail':detail})
def diff(a,b,p=''):
    if type(a)!=type(b):return[p]
    if isinstance(a,dict):return[q for k in a.keys()|b.keys() for q in ([p+'/'+k] if k not in a or k not in b else diff(a[k],b[k],p+'/'+k))]
    if isinstance(a,list):return[p] if len(a)!=len(b) else[q for i,(x,y) in enumerate(zip(a,b)) for q in diff(x,y,p+'/'+str(i))]
    return[] if a==b else[p]
for folder,audit in [(V,'promotion-delta-audit.json'),(P/'product-context-v1','product-context-audit.json')]:
    a=rd(O/audit);bind(O/audit);bind(folder/'package-freeze.json')
    check(audit+' approved freeze',a['status']=='passed' and a['proposal_freeze_sha256']==sha(folder/'package-freeze.json'))
    for f in rd(folder/'package-freeze.json')['files']:
        p=folder/f['path'];check('frozen proposal '+f['path'],sha(p)==f['sha256']);bind(p)
old=rd(P/'base-record-hashes.json');bind(P/'base-record-hashes.json');check('baseline count530',len(old)==530)
for name,h in old.items():
    p=S/'data/records'/name;check('old canonical '+name,sha(p)==h);bind(p)
    check('old built '+name,sha(S/'dist/data/records'/name)==h);bind(S/'dist/data/records'/name)
promo=rd(V/'promotion-manifest.json');ids=[r['record_id'] for r in promo['records']]
check('actual total546',len(list((S/'data/records').glob('*.json')))==546)
for e in promo['records']:
    rid=e['record_id'];a=V/'records'/f'{rid}.json';b=S/'data/records'/a.name;c=S/'dist/data/records'/a.name
    check(rid+' promotion hash',sha(a)==e['promoted_sha256']==sha(b)==sha(c));bind(b);bind(c)
    r=rd(b);check(rid+' no training/structures',r['quality']['requested_tasks']==[] and r['structure_assets']==[])
    check(rid+' static record page exists',(S/'dist/records'/f'{rid}.html').exists());bind(S/'dist/records'/f'{rid}.html')
    page=S/'dist/records'/f'{rid}.html'
    for url in re.findall(r'(?:href|src)="([^"]+)"',page.read_text(encoding='utf-8')):
        parsed=urllib.parse.urlsplit(html.unescape(url))
        if parsed.scheme or parsed.netloc or not parsed.path:continue
        target=(S/'dist'/parsed.path.lstrip('/')) if parsed.path.startswith('/') else (page.parent/parsed.path)
        check(rid+' static local URL '+url,target.resolve().exists())
dataset=rd(S/'dist/data/dataset-manifest.json');bind(S/'dist/data/dataset-manifest.json');check('dataset0.27.0 count546',dataset['dataset_version']=='0.27.0' and dataset['record_count']==546)
for e in dataset['records']:
    if e['record_id'] in ids:
        check(e['record_id']+' built manifest no eligible task',all(not x['eligible'] for x in e['eligibility'].values()))
        value=rd(S/'data/records'/(e['record_id']+'.json'));normalized=hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        check(e['record_id']+' built manifest normalized record digest',e['record_sha256']==normalized)
for p in (S/'dist/data/exports').glob('*.jsonl'):
    check('no Lian training rows '+p.name,all(rdrow['record_id'] not in ids for rdrow in [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]));bind(p)
base=P/'base-site-inputs';asset='dist/assets/chemical-registry'
before=rd(base/asset/'registry.json');expected=json.loads(json.dumps(before));add=rd(V/'molecules/registry-additions.json')['entries']
for entry in add:e=json.loads(json.dumps(entry));e['published']=True;expected['entries'].append(e)
current=rd(S/asset/'registry.json');check('registry exact15-entry merge',current==expected,diff(expected,current));bind(S/asset/'registry.json')
expected=rd(base/asset/'bindings.json');addition=rd(V/'molecules/bindings-additions.json')
for k in ['recordBindings','bindingNotes','sourceRecordSha256']:expected.setdefault(k,{}).update(addition[k])
current=rd(S/asset/'bindings.json');check('bindings exact merge',current==expected,diff(expected,current));bind(S/asset/'bindings.json')
for filename,extra in [('solution-components.json',V/'molecules/solution-components-additions.json')]:
    expected=rd(base/asset/filename);expected['contexts'].extend(rd(extra)['contexts']);check('solutions exact5-context merge',expected==rd(S/asset/filename));bind(S/asset/filename)
expected=rd(base/asset/'product-contexts.json');addition=rd(P/'product-context-v1/product-contexts-additions.json')
for k in ['recordContexts','sourceNotices']:expected[k].update(addition[k])
check('symbolic product exact22-context merge',expected==rd(S/asset/'product-contexts.json'));bind(S/asset/'product-contexts.json')
expected=rd(base/'data/measurement-display.json')
for sect,key in [('structures','record_structural_measurement_ids'),('properties','record_property_measurement_ids')]:expected[key].update(rd(V/f'record-{sect}-measurements.json'))
check('measurement display source-scoped exact merge',expected==rd(S/'data/measurement-display.json'));bind(S/'data/measurement-display.json')
check('built measurement display exact',rd(S/'dist/data/measurement-display.json')==expected);bind(S/'dist/data/measurement-display.json')
for f in promo['public_assets']:
    p=S/'dist'/f['public_path'];check('public asset '+f['public_path'],sha(p)==f['sha256']);bind(p)
    check('selected public asset not whole-source',not re.search(r'\.pdf$|source-render|complete-source|/main-\d|/si-\d',f['public_path']))
a=rd(V/'reader/lian2021.json');b=rd(S/'data/paper-reviews/lian2021.json');c=rd(S/'dist/data/paper-reviews/lian2021.json')
expected_paths={'/audit_details/symbolic_product_context_audit_sha256','/audit_details/promotion_audit_sha256','/presentation_gates/site_integration','/publication_status'}
check('reader exact four metadata leaves',set(diff(a,b))==expected_paths,diff(a,b))
check('reader proof hashes',b['audit_details']['promotion_audit_sha256']==sha(O/'promotion-delta-audit.json') and b['audit_details']['symbolic_product_context_audit_sha256']==sha(O/'product-context-audit.json'))
check('generated reader only scope label',diff(b,c)==['/review_scope_label'] and c['review_scope_label']=='Complete supplied main + matched SI review')
for p in [S/'data/paper-reviews/lian2021.json',S/'dist/data/paper-reviews/lian2021.json',P/'site-import-manifest.json',P/'reader-presentation-delta.json',P/'code-delta.json']:bind(p)
delta=rd(P/'code-delta.json');changed={x['file'] for x in delta['changes']}|set(delta['cache_revision_files'])
for rel in sorted(changed):
    bp=base/rel
    if not bp.exists():check('code baseline exists '+rel,False);continue
    text=bp.read_text(encoding='utf-8')
    for d in delta['changes']:
        if d['file']==rel:
            check('declared code replacement count '+d['before'][:45],text.count(d['before'])==d['occurrences']);text=text.replace(d['before'],d['after'])
    if rel in delta['cache_revision_files']:text=text.replace('0.26.0-r1','0.27.0-r1')
    target=P/'build-dataset-before-reader-presentation.py' if rel=='scripts/build_dataset.py' else P/'pre-bulk-crystal-viewer.mjs' if rel=='dist/crystal-viewer.mjs' else S/rel
    if rel in ['dist/dataset.html','dist/inventory.html']:
        # These generated pages are rebuilt after the source/code import, rather than cache-token-only edits.
        tokens=lambda t:[html.unescape(x).strip() for x in re.findall('>([^<>]+)<',t) if x.strip()]
        a=tokens(text);b=tokens(target.read_text(encoding='utf-8'))
        changes=[{'op':tag,'before':a[i:j],'after':b[k:l]} for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if tag!='equal']
        allowed={('117','120'),('33','34')} if rel.endswith('dataset.html') else {('33','35'),('103','106'),('203','209'),('110','117'),('530','546'),('4,143','4,142')}
        for change in changes:
            if len(change['before'])==len(change['after'])==1:check(rel+' derived count',tuple([change['before'][0],change['after'][0]]) in allowed,change)
            else:check(rel+' Lian generated content',any(x in '\n'.join(change['after']) for x in ['Zero-dimensional organic antimony halides','(C12H28N)','35 direct synthesis systems','245 pages across 15 sources','10.1021/acsami.1c18038']),change)
    else:check('exact declared code delta '+rel,text==target.read_text(encoding='utf-8'))
    bind(bp);bind(target)
pd=rd(P/'reader-presentation-delta.json');check('presentation before digest',sha(P/'build-dataset-before-reader-presentation.py')==pd['before_sha256']);check('presentation after digest',sha(P/'pre-bulk-build_dataset.py')==pd['after_sha256']);bind(S/'scripts/build_dataset.py');bind(P/'pre-bulk-build_dataset.py')
bulk=rd(P/'bulk-view-integration-delta.json');bind(P/'bulk-view-integration-delta.json')
mobile=rd(P/'mobile-display-delta.json');bind(P/'mobile-display-delta.json');mobile_by_path={str(Path(e['path'])):e for e in mobile['changes']}
for asset in bulk['public_assets']:
    # Hash transport only: the coordinate/model science belongs to the root's distinct audit.
    p=S/'dist'/asset['target'];change=mobile_by_path.get(str(p))
    if change:
        original=Path(asset['source']).read_text(encoding='utf-8');actual=p.read_text(encoding='utf-8')
        before='viewer.zoom(expanded?.95:1.45)';after='viewer.zoom(expanded?.95:(view.clientWidth<400?1.0:1.45))'
        check('root-only ASU camera delta',original.count(before)==1 and actual==original.replace(before,after) and sha(asset['source'])==change['before_sha256']==asset['sha256'] and sha(p)==change['after_sha256'])
    else:check('bulk exact asset copy '+asset['target'],sha(p)==sha(asset['source'])==asset['sha256'])
    bind(p)
for e in bulk['code_changes']:
    p=Path(e['path']);oldp=P/('pre-bulk-'+p.name)
    if p.name=='crystal-viewer.mjs':
        normalized=p.read_bytes().replace(b"./lian2021-bulk-viewer.mjs?v=0.27.0-r2",b"./lian2021-bulk-viewer.mjs")
        # The replaced import line uses LF; the previous file used CRLF throughout.
        normalized=normalized.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
        check('root import cache-buster only',hashlib.sha256(normalized).hexdigest()==e['after_sha256'] and sha(p)==mobile['cache_buster']['sha256'])
        check('bulk code chain '+p.name,sha(oldp)==e['before_sha256'])
    else:check('bulk code chain '+p.name,sha(p)==e['after_sha256'] and sha(oldp)==e['before_sha256'])
    bind(p);bind(oldp)
cv=(S/'dist/crystal-viewer.mjs').read_text(encoding='utf-8');oldcv=(P/'pre-bulk-crystal-viewer.mjs').read_text(encoding='utf-8')
importline="import {mountLianBulk,eligibleBulkContexts} from './lian2021-bulk-viewer.mjs?v=0.27.0-r2';\n"
insertion="if(eligibleBulkContexts(r).length){if(!document.querySelector('link[data-lian-bulk-css]')){const css=document.createElement('link');css.rel='stylesheet';css.href=new URL('./lian2021-bulk-viewer.css',import.meta.url);css.dataset.lianBulkCss='true';document.head.append(css);}await mountLianBulk(host,r);}"
check('root bulk adapter exactly two insertions',cv.replace(importline,'',1).replace(insertion,'',1)==oldcv and cv.count(insertion)==1)
check('identity cards precede bulk adapter',cv.index('await productIdentity(host,r);')<cv.index(insertion))
bd=(S/'scripts/build_dataset.py').read_text(encoding='utf-8');oldbd=(P/'pre-bulk-build_dataset.py').read_text(encoding='utf-8')
newline="    elif r.get('lineage',{}).get('source_group')=='lian2021' and r['record_id'] in {'lian-2021-bulk-a-route','lian-2021-bulk-b-route','lian-2021-bulk-characterization'}:body+='<p class=\"record-note\">Partial non-hydrogen bulk-crystal coordinates from the supporting tables are shown separately below. Hydrogen positions, occupancies and a verified link to the same physical synthesis aliquot are unavailable; no complete sample CIF or exact training pair is assigned.</p>'\n"
check('bulk placeholder only three source-scoped records',bd.count(newline)==1 and bd.replace(newline,'',1)==oldbd)
for name in ['coordinate-math-audit.json','binding-audit.json']:
    path=L/'visuals/bulk-structure-independent-audit'/name;bind(path);a=rd(path);check('distinct root bulk proof exists '+name,a['status']=='passed')
# Execute only the two pure presentation helpers in isolated namespaces; do not import/build Site.
tree=ast.parse((S/'scripts/build_dataset.py').read_text(encoding='utf-8'));names={'human','material_reader_notes','product_reader_note'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
ns={'json':json,'esc':html.escape};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<isolated-presentation-functions>','exec'),ns)
for f in (S/'data/records').glob('*.json'):
    r=rd(f)
    for m in r['materials']:
        expected=list(dict.fromkeys(m['notes']));result=ns['material_reader_notes'](m,r)
        if r['lineage']['source_group']=='lian2021':expected=[n for n in expected if n!='Chemical/atomic visual binding is separately pending.']
        check(f.stem+' material notes '+m['id'],result==expected)
    for p in r['products']:
        for n in p['notes']:
            result=ns['product_reader_note'](n,r)
            if r['lineage']['source_group']!='lian2021' or not n.startswith('Source sample object: '):check(f.stem+' unchanged product note',result=='<p>'+html.escape(n)+'</p>')
            else:
                check(f.stem+' specimen readable details',result.startswith('<details class="source-specimen-context">') and 'Source sample object: {' not in result)
check('specimen HTML escaped','&lt;script&gt;' in ns['product_reader_note']('Source sample object: {"x":"<script>"}',{'lineage':{'source_group':'lian2021'}}))
for rel in ['dist/protocol-visuals.mjs','dist/chemical-viewer.mjs','dist/material-guide.mjs','dist/material-hub.mjs','dist/source-evidence.mjs','dist/illustrated-record.mjs']:
    bind(S/rel)
    for imp in re.findall(r"(?:from\s*|import\s*)['\"](\.[^'\"]+)['\"]",(S/rel).read_text(encoding='utf-8')):
        check(rel+' static import '+imp,((S/rel).parent/imp.split('?')[0]).resolve().exists())
css=S/'dist/illustrated-guide.css';bind(css);rule='.protocol-copy small,.crystal-reference-card small{overflow-wrap:anywhere;word-break:normal;max-width:100%;}'
check('long evidence wrapping rule present once',css.read_text(encoding='utf-8').count(rule)==1)
baseline=O/'illustrated-guide-public-baseline.css';bind(baseline)
suffix='/* Long source digests remain readable without widening mobile record pages. */\n'+rule+'\n@media(max-width:620px){.record-main .lian-bulk-view{height:auto;aspect-ratio:1/1;min-height:260px;}}\n'
check('CSS exactly provenance wrapping plus scoped mobile sizing',css.read_text(encoding='utf-8')==baseline.read_text(encoding='utf-8')+suffix)
css_delta=mobile_by_path[str(css)];check('mobile CSS declared hash boundary',sha(baseline)==css_delta['before_sha256'] and sha(css)==css_delta['after_sha256'] and suffix==css_delta['only_added_rule'])
fail=[x for x in checks if not x['passed']]
report={'status':'passed' if not fail else 'findings','scope':'actual Site root integration transport/code, excluding authored bulk-viewer science and final browser/publication','check_count':len(checks),'failures':fail,'checks':checks,'bound_files':bound,'bulk_adapter_status':'root-only insertion transport checked; science relies on distinct root audits','canonical_or_site_modified':False}
(O/'actual-integration-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':fail},ensure_ascii=False,indent=2))
