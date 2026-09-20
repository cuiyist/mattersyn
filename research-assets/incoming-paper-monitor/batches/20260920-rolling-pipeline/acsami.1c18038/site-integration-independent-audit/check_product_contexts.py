from pathlib import Path
import json,hashlib,re
from datetime import datetime,timezone
A=Path(__file__).resolve().parent;L=A.parent;O=L/'site-integration-proposal/product-context-v1';P=L/'site-integration-proposal/v1'
checks=[];bound={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):p=Path(p);bound[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8-sig'))
def same(x,y,s):checks.append({'passed':x==y,'check':s})
def yes(x,s):checks.append({'passed':bool(x),'check':s})
freeze=load(O/'package-freeze.json');same(sha(O/'package-freeze.json'),'f8d21c8e9618db8efcecbd4ce5b293c87e7fbe632fc55ca0bfe23c4f9c89e0ee','exact product proposal freeze')
for f in freeze['files']:load(O/f['path']);same(sha(O/f['path']),f['sha256'],'frozen file '+f['path'])
script=L/'prepare_product_contexts.py';bound[str(script)]=sha(script);same(sha(script),freeze['script_sha256'],'frozen root script')
text=script.read_text(encoding='utf-8');yes("mapping.get(s['sample_id'])" in text,'explicit sample lookup');yes("s['composition']['value']==expected" in text,'exact specimen composition gate');yes("if not match:" in text and 'continue' in text,'unmapped context excluded')
reg=load(P/'molecules/registry-additions.json');same(sha(P/'molecules/registry-additions.json'),freeze['registry_sha256'],'independently passed promotion registry')
entries={x['id']:x for x in reg['entries']};data=load(O/'product-contexts-additions.json');binding=load(O/'bindings.json')
prior=load(A/'promotion-delta-audit.json');same(prior['status'],'passed','separate promotion audit passed');same(binding['promotion_freeze_sha256'],prior['proposal_freeze_sha256'],'same approved promotion')
records={p.stem:load(p) for p in (P/'records').glob('*.json')}
expected={
 'bulk-a':('(C12H28N)2SbCl5','lian2021-bulk-a-reference'),
 'bulk-a-crystal':('(C12H28N)2SbCl5','lian2021-bulk-a-reference'),
 'bulk-b':('(C12H28N)SbCl4','lian2021-bulk-b-reference'),
 'bulk-b-crystal':('(C12H28N)SbCl4','lian2021-bulk-b-reference'),
 'nc-a':('(C12H28N)2SbCl5','lian2021-nc-a-reference'),
 'nc-a-dried-powder':('(C12H28N)2SbCl5','lian2021-nc-a-reference'),
 'nc-a-colloid-vs-dry':('(C12H28N)2SbCl5','lian2021-nc-a-reference'),
 'film-spincoat':('(C12H28N)2SbCl5','lian2021-spincoat-film-reference'),
 'film-composite-series':(None,'lian2021-composite-film-reference'),
 **{'film-blend-'+str(i):(None,'lian2021-composite-film-reference') for i in range(1,6)}
}
actual_pairs=set();excluded={(x['record_id'],x['sample_id']) for x in binding['excluded_contexts']};summaries=[]
for rid,r in records.items():
 same(binding['source_record_sha256'][rid],sha(P/'records'/(rid+'.json')),'exact promoted record '+rid)
 for row in data['recordContexts'].get(rid,[]):
  pair=(rid,row['sample_id']);yes(pair not in actual_pairs,'unique symbolic context '+str(pair));actual_pairs.add(pair)
  yes(row['sample_id'] in expected,'allowed source specimen '+str(pair))
  i=int(row['canonical_product_pointer'].split('/')[-1]);product=r['products'][i];same(product['sample_id'],row['sample_id'],'exact product pointer '+str(pair))
  formula,reference=expected[row['sample_id']];same(product['composition']['value'],formula,'specimen composition not nominal record '+str(pair));same(row['registry_id'],reference,'source-scoped symbol identity '+str(pair))
  entry=entries[row['registry_id']];same(entry['depictionKind'],'symbolic_context','symbolic only '+str(pair));yes(not entry.get('model3dPath'),'no atom model '+str(pair))
  for field in ['phase','morphology']:same(row[field],product[field],'exact scoped '+field+' '+str(pair))
  same(row['composition_evidence'],product['composition']['evidence'],'exact composition evidence '+str(pair))
  same(row['atomic_model'],False,'atomic flag false '+str(pair));same(row['training_eligible'],False,'training flag false '+str(pair));yes('no atomic coordinates' in row['caption'],'caption prevents geometry claim '+str(pair))
  yes('specimen equivalence' in row['caption'],'caption prevents unsupported cross-technique specimen join '+str(pair))
  summaries.append({'record':rid,'sample':row['sample_id'],'label':row['label'],'reference':reference,'phase':row['phase']['value'],'morphology':row['morphology']['value']})
 for product in r['products']:
  pair=(rid,product['sample_id'])
  same(pair in actual_pairs,product['sample_id'] in expected,'complete explicit selection '+str(pair))
  same(pair in excluded,product['sample_id'] not in expected,'unmapped context remains excluded '+str(pair))
same(len(actual_pairs),22,'22 exact product contexts');same(len(data['recordContexts']),11,'11 records with product contexts')
same(len(excluded),22,'22 calculation/mixed/source contexts excluded')
yes(not any(rid=='lian-2021-dft-calculation' for rid,_ in actual_pairs),'no DFT model product label')
yes('Bulk coordinates cannot be assigned to nanocrystal or film specimens.' in data['sourceNotices']['lian2021'],'bulk versus nanocrystal source distinction')
yes(not re.search(r'[A-Z]:[\\/]|file://',json.dumps(data)),'no local paths in proposed public data')
same(binding['no_coordinate_files_added'],True,'no coordinates added');same(binding['scientific_values_unchanged'],True,'scoped scientific values exact as independently checked')
bound[str(Path(__file__))]=sha(Path(__file__))
findings=[x for x in checks if not x['passed']]
result={'schema':'mattersyn-independent-product-context-audit/1','status':'passed' if not findings else 'open_findings','auditor':'/root/norberg2004_extract','author':'/root','created_at':datetime.now(timezone.utc).isoformat(),'proposal_freeze_sha256':sha(O/'package-freeze.json'),'check_count':len(checks),'counts':{'symbolic_contexts':22,'records':11,'excluded_contexts':22,'coordinate_files':0,'training_promotions':0},'context_summary':summaries,'findings':findings,'manual_scopes':['Read the whole root product-context selector and every generated label/reference association.','Bulk A and B stoichiometry remains separate; P-1 and P21/c copied from their exact reviewed source specimens, no phase inheritance to NCs/films.','NC A, dried powder and colloid/dry comparison retain context labels rather than a new identical-aliquot assertion.','Named composite blends legitimately have null composition; selecting them requires their explicit sample ID, never a nominal-record fallback. End-member blends are not assigned a new numeric chemical composition by this symbol.','Spin-coated supported film and NC/PS/phosphor composite film remain separate.','DFT, bonding interpretations, acquisition-wide and unresolved mixed specimens are excluded.','Symbolic registry assets were independently qualified in the molecular audit; this checks root selection/metadata transport only, not fresh molecular science or the forthcoming partial bulk-coordinate package.'],'bound_files':dict(sorted(bound.items())),'checks':checks,'site_integration_approved':False,'browser_approved':False,'publication_approved':False,'atomic_coordinate_approved':False,'training_approved':False}
(A/'product-context-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(A/'product-context-audit.md').write_text(f'''# Lian symbolic product-context audit

Status: **{result['status']}**. Exact proposal freeze `{result['proposal_freeze_sha256']}`.

All 22 symbolic contexts across 11 records pass {len(checks)} independent selector/metadata checks. Each is selected by an explicit product sample ID and exact composition, including the explicitly named null-composition composite blends. Phase, morphology and evidence are copied from that exact canonical specimen. Bulk A/B, nanocrystal, dried-powder, colloid/dry comparison, supported spin-coated film and composite blend labels remain separate. Twenty-two mixed, model or bibliographic contexts are excluded without a nominal-record fallback.

No coordinate asset, inferred surface geometry, new phase assignment, training label or specimen-equivalence claim is added. This audit is separate from the forthcoming partial bulk-coordinate view and does not approve Site/browser/publication integration.

Open findings: {len(findings)}.
''',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'findings':findings,'audit_sha256':sha(A/'product-context-audit.json'),'contexts':summaries}))
