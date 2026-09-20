"""Distinct root review of the frozen, source-scoped product presentation."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re,subprocess,sys
J=Path(__file__).resolve().parent;Q=J/'visuals/products';O=J/'product-independent-audit';S=J.parents[4]/'recipe-atlas'
sys.path.insert(0,str(J.parents[4]/'research-assets'))
from sync_github_public import io_path
read=lambda p:json.loads(io_path(p).read_text('utf8'))
sha=lambda p:hashlib.sha256(io_path(p).read_bytes()).hexdigest()
def save(p,x):
 p=io_path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
assert not (O/'independent-audit.json').exists();O.mkdir(exist_ok=True)
checks=[]
def ck(s,yes):
 checks.append({'check':s,'passed':bool(yes)});assert yes,s
f=read(Q/'package-freeze.json')
for name,h in f['bound_files'].items():ck('Frozen '+name,sha(Path(name) if Path(name).is_absolute() else Q/name)==h)
b=read(Q/'bindings.json');ck('Distinct author',b['author']!='/root')
records={p.stem:read(p) for p in (J/'canonical-proposal/v1/records').glob('*.json')}
def ptr(v,p):
 for k in p.strip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');v=v[int(k)] if isinstance(v,list) else v[k]
 return v
payload=read(Q/'public-product-contexts-proposal.json');reg=read(Q/'registry-additions.json');entries={e['id']:e for e in reg['entries']}
covered=set()
for row in b['bindings']:
 r=records[row['record_id']];p=ptr(r,row['canonical_product_pointer']);ck('Exact product snapshot '+row['record_id']+'/'+row['sample_id'],p==row['canonical_product_snapshot'] and p['sample_id']==row['sample_id'])
 ck('Exact record digest '+row['record_id'],sha(Path(row['canonical_record_path']))==row['canonical_record_sha256'])
 ctx=next(c for c in payload['recordContexts'][row['record_id']] if c['sample_id']==row['sample_id']);e=entries[ctx['registry_id']]
 ck('Named registry binding '+row['sample_id'],ctx['registry_id']==row['registry_id'] and not e['model2dPath'] and not e['model3dPath'])
 covered.add((row['record_id'],row['sample_id']))
for row in b['excluded_contexts']:
 ck('Excluded slot exists '+row['record_id']+'/'+row['sample_id'],row['sample_id'] in {p['sample_id'] for p in records[row['record_id']]['products']})
 ck('Excluded not promoted '+row['record_id']+'/'+row['sample_id'],(row['record_id'],row['sample_id']) not in covered)
 covered.add((row['record_id'],row['sample_id']))
ck('All117 slots accounted',covered=={(r['record_id'],p['sample_id']) for r in records.values() for p in r['products']} and len(covered)==117)
ck('33 named symbolic contexts',len(entries)==33 and len({c['sample_id'] for rows in payload['recordContexts'].values() for c in rows})==33)
ck('42 mapped instances',sum(map(len,payload['recordContexts'].values()))==42)
ck('Public payload no local paths',not re.search(r'[A-Z]:[\\/]|file://',json.dumps(payload)))
for a in read(Q/'public-assets-proposal.json')['assets']:
 ck('Exact symbolic asset '+a['entry_id'],sha(Path(a['path']))==a['sha256']==entries[a['entry_id']]['assetHashes']['svgPath'])
 ck('SVG only '+a['entry_id'],a['public_path'].startswith('assets/chemical-registry/sasongko2025-products/') and a['public_path'].endswith('.svg'))
originals={a['sha256']:a for a in read(J/'original-assets-manifest.json')['assets']}
for rid,rows in payload['recordContexts'].items():
 for c in rows:
  for link in c['original_evidence_links']:
   a=originals[link['sha256']];ck('Original figure exact '+rid+'/'+c['sample_id'],link['public_asset']=='assets/figures/sasongko2025/'+Path(a['path']).name and sha(Path(a['path']))==link['sha256'] and not a['contains_complete_source_page'])
patch=read(Q/'original-evidence-consumer-insertion.json');ck('Exact consumer baseline',sha(S/patch['target'])==patch['baseline_sha256']);ck('Single insertion',io_path(S/patch['target']).read_text('utf8').count(patch['anchor'])==1)
# Independently re-execute the frozen consumer fixture against the same exact consumer bytes;
# redirect reports outside the immutable package. Scope is transport/dispatch, not a browser.
test=(Q/'test_consumer.mjs').read_text('utf8');test=test.replace("const O=path.dirname(fileURLToPath(import.meta.url));","const O=process.argv[2];")
test=test.replace("fs.writeFileSync(path.join(O,proposalMode?'proposed-links-consumer-checks.json':'consumer-execution-checks.json')","fs.writeFileSync(path.join(process.argv[3],proposalMode?'proposed-links-consumer-checks.json':'consumer-execution-checks.json')")
(O/'check-consumer.mjs').write_text(test,'utf8')
node=r'[local path redacted]'
for extra in [[],['--proposal-links']]:subprocess.run([node,str(O/'check-consumer.mjs'),str(Q),str(O),*extra],check=True)
for name in ['consumer-execution-checks.json','proposed-links-consumer-checks.json']:ck('Actual consumer fixture '+name,all(c['passed'] for c in read(O/name)['checks']))
viewed=['source-render/'+n+'.png' for n in ['main-02','main-03','main-04','main-05','main-06','si-03','si-04','si-05','si-06','si-08','si-09']]+['visuals/products/contacts/contact-'+str(i).zfill(2)+'.png' for i in range(1,10)]
manual=[
 'Actually read the listed eleven original pages and inspected all33 rendered context cards in nine contact sheets. Separate all20-page independent source audit remains the authority for full-paper completeness.',
 'Nine factor-series contexts retain Figure1 ligand/100C/1:20, Figure2 washing/100C/1:3 and Figure3 growth/1:3/1:20 pairings. Same optimum labels are not promoted to common aliquots or replicate identities.',
 'Figure3 25C mixture alpha+delta+PbI2 versus source alpha assignments at50/100C retained; TEM7.6+/-2.4,9.5+/-1.6,10.4+/-1.1nm and separate histogramFWHM5.7/3.7/2.7nm match.20nm scale bars are not sizes.',
 'Unresolved d(002)=6.38A versus quoted6.36A cubic reference remains explicit. Literal Pm3m has no inserted overbar. Reference cells and Scheme1 drawings are not current-QD coordinates.',
 'Main4/5 PL regimes and slopes retained as measurements/interpretation; SI S2 Raman actual80-190K versus attempted80-200K and source misplacedS1 callout remain explicit.',
 'SI TableS1 ten literature rows and one current-study summary remain distinct; blank beta-to-alpha cells stay unknown; mixed film composition is not a current synthesized sample.',
 'First precipitate, hexane redispersion, final supernatant and washing waste retain distinct process states. No measured whole composition, atomic lattice or concentration is invented.',
 'Source original-image insertion is a narrow exact-source/path-prefix/hash-checked navigation change. It changes neither product data nor existing source dispatch. Malformed paths and foreign-source links were rejected by the executed fixture.'
]
save(O/'independent-audit.json',{'schema':'mattersyn.independent_product_context_audit/1','at':datetime.now(timezone.utc).isoformat(),'reviewer':'/root','author':b['author'],'status':'passed','open_findings':[],'inputs':{'product_freeze':{'path':str(Q/'package-freeze.json'),'sha256':sha(Q/'package-freeze.json')}},'source_audit_sha256':sha(J/'source-independent-audit/independent-audit-v2.json'),'canonical_audit_sha256':sha(J/'canonical-independent-audit/independent-audit-v1.json'),'checks':checks,'check_count':len(checks),'manual_review':manual,'actually_viewed':[{'path':p,'sha256':sha(J/p)} for p in viewed],'consumer_fixture_reexecution_counts':[read(O/n)['check_count'] for n in ['consumer-execution-checks.json','proposed-links-consumer-checks.json']],'browser_approval':False,'training_approval':False,'publication_approval':False})
print(json.dumps({'status':'passed','checks':len(checks),'audit_sha256':sha(O/'independent-audit.json')}))
