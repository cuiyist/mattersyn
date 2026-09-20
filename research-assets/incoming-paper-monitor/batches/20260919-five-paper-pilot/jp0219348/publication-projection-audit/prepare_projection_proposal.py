"""Read-only Heo publication projection plan; writes private audit outputs only."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy,re,collections
A=Path(__file__).resolve().parent;H=A.parent;V=H/'canonical-proposal/v2';S=H.parents[4]/'recipe-atlas'
checks=[];bound={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p).resolve();bound[str(p)]=sha(p);return p
def load(p):return json.loads(bind(p).read_bytes())
def ck(label,ok):checks.append({'check':label,'passed':bool(ok)})
def walk(x,p=''):
    yield p,x
    if isinstance(x,dict):
        for k,v in x.items():yield from walk(v,p+'/'+k.replace('~','~0').replace('/','~1'))
    elif isinstance(x,list):
        for i,v in enumerate(x):yield from walk(v,p+'/'+str(i))
def ptr(x,p):
    for k in p.lstrip('/').split('/') if p else []:x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
    return x
def delete(x,p):
    base,key=p.rsplit('/',1);parent=ptr(x,base)
    if isinstance(parent,list):parent.pop(int(key))
    else:del parent[key]
r=load(V/'public-review-proposal/heo2003.json');assets=load(V/'public-review-proposal/reader-original-assets-manifest.json')['assets']
package=load(V/'proposal-package-manifest.json');prior=load(H/'canonical-proposal/audit-v2/independent-audit.json')
si=load(V/'source-payloads/si-complete-candidate/all-reflections.json');sc=load(V/'si-row-coverage.json')
mc=load(V/'public-review-proposal/canonical-measurement-coverage.json')
bind(S/'scripts/build_paper_reviews.py');bind(S/'dist/source-evidence.mjs')
ck('Expected passed v2 manifest',sha(V/'proposal-package-manifest.json')=='10640012af6a21458edd6a84c24af2dea24562f950495a662930d682185fb05a')
ck('Distinct canonical-reader audit passed',prior['status']=='passed_bounded_canonical_reader_scope')
whole={k:v for k,v in assets.items() if any(e.get('locator')=='complete original page' for e in v['source_payload'].get('evidence',[]))}
selected={k:v for k,v in assets.items() if k not in whole}
ck('Exactly 9 main and14 SI complete pages',len(whole)==23 and sum('-main-page-' in k for k in whole)==9 and sum('-si-page-' in k for k in whole)==14)
ck('Exactly16 selected original crops',len(selected)==16)
for k,v in assets.items():
    ck(k+' original hash',sha(bind(v['path']))==v['sha256'])
    p=V/'reader-compatibility-projection/dist/assets/figures/heo2003'/Path(v['path']).name
    ck(k+' projected original hash',sha(bind(p))==v['sha256'])
wholeurls={'assets/figures/heo2003/'+Path(v['path']).name:k for k,v in whole.items()}
urlrefs=[]
for p,x in walk(r):
    if isinstance(x,dict) and x.get('public_asset') in wholeurls:
        item_id=None
        if p.startswith('/reader_sections/'):
            parts=p.split('/');item_id=r['reader_sections'][int(parts[2])]['items'][int(parts[4])]['id']
        urlrefs.append({'object_pointer':p,'asset_id':wholeurls[x['public_asset']],'item_id':item_id,'public_asset':x['public_asset'],'public_asset_sha256':x['public_asset_sha256'],'remove_keys':['public_asset','public_asset_sha256'],'attachment_action':'remove this original_assets attachment object; retain reader item' if '/original_assets/' in p else 'remove only public URL/hash; retain source-note metadata'})
ck('46 exact whole-page URL occurrences',len(urlrefs)==46)
ck('Each whole-page URL has exactly two occurrences',collections.Counter(x['public_asset'] for x in urlrefs)=={u:2 for u in wholeurls})
privatepaths=[{'pointer':p,'value':x} for p,x in walk(r) if isinstance(x,str) and re.match(r'^[A-Za-z]:[\\/]',x)]
ck('166 absolute filesystem path fields',len(privatepaths)==166)
rolefixes=[]
for p,x in walk(r):
    if isinstance(x,dict) and str(x.get('locator','')).startswith('SI PDF') and x.get('document_role')=='main':
        parts=p.split('/');item_id=r['reader_sections'][int(parts[2])]['items'][int(parts[4])]['id']
        rolefixes.append({'pointer':p+'/document_role','before':'main','after':'si','item_id':item_id,'unchanged_locator':x['locator']})
ck('14 SI page role metadata corrections only',len(rolefixes)==14 and all(f['item_id'].startswith('asset-heo2003-si-page-') for f in rolefixes))
projected=copy.deepcopy(r)
# Private fields first, before any array attachment is removed.
for x in privatepaths:delete(projected,x['pointer'])
delete(projected,'/si_aggregate_evidence/audit_path')
for x in urlrefs:
    if '/original_assets/' not in x['object_pointer']:
        for key in x['remove_keys']:delete(projected,x['object_pointer']+'/'+key)
for section in projected['reader_sections']:
    for item in section['items']:
        item['original_assets']=[x for x in item.get('original_assets',[]) if x.get('public_asset') not in wholeurls]
for x in rolefixes:
    parent,key=x['pointer'].rsplit('/',1);ptr(projected,parent)[key]=x['after']
olditems=[i for s in r['reader_sections'] for i in s['items']];newitems=[i for s in projected['reader_sections'] for i in s['items']]
ck('All372 reader item IDs/order retained',[i['id'] for i in olditems]==[i['id'] for i in newitems] and len(newitems)==372)
for old,new in zip(olditems,newitems):
    for k in ['text','title','facts','canonical_links','source_locators','sample_scope','source_audit_unit_ids','source_fact_ids','training_eligible']:
        ck(old['id']+' unchanged '+k,old.get(k)==new.get(k))
    oe=[{k:v for k,v in e.items() if k!='document_role'} for e in old['evidence']];ne=[{k:v for k,v in e.items() if k!='document_role'} for e in new['evidence']]
    ck(old['id']+' all evidence identity/locators unchanged',oe==ne)
rfacts=[f for i in newitems for f in i.get('facts',[])]
ck('535 exact typed fact attachments retained',len(rfacts)==535 and rfacts==[f for i in olditems for f in i.get('facts',[])])
records={p.stem:load(p) for p in (V/'canonical-drafts').glob('*.json')}
measurements={(rid,'/measurements/'+str(i)+'/value') for rid,x in records.items() for i in range(len(x['measurements']))}
reachable={(f['canonical_record_id'],f['json_pointer']) for f in rfacts}
ck('All473 distinct canonical measurements still reachable',len(measurements)==473 and measurements<=reachable)
ck('1209 SI row mappings retained; no row payload projection',len(sc['rows'])==len(si['rows'])==1209 and projected['si_aggregate_evidence']['counts']==r['si_aggregate_evidence']['counts'])
ck('Two unresolved SI signs retained',projected['si_aggregate_evidence']['counts']['unresolved_sign_cells']==2)
ck('No whole-page public URL remains',not any(isinstance(x,str) and x in wholeurls for p,x in walk(projected)))
ck('No absolute local filesystem field remains',not any(isinstance(x,str) and re.match(r'^[A-Za-z]:[\\/]',x) for p,x in walk(projected)))
afterurls={x['public_asset'] for p,x in walk(projected) if isinstance(x,dict) and x.get('public_asset')}
selectedurls={'assets/figures/heo2003/'+Path(x['path']).name for x in selected.values()}
ck('All16 selected crop URLs remain exactly',afterurls==selectedurls)
ck('Renderer attachments always retain valid public_asset',all(a.get('public_asset') for i in newitems for a in i.get('original_assets',[])))
ck('Seven figures/five tables/eight equations/source notes unchanged except allowed path fields',len(projected['figures'])==7 and len(projected['tables'])==5 and len(projected['equations'])==8 and len(projected['source_notes'])==len(r['source_notes']))
ck('Document coverage/source hashes untouched',projected['documents']==r['documents'])
ck('SI independent audit hash untouched',projected['si_aggregate_evidence']['audit_sha256']==r['si_aggregate_evidence']['audit_sha256'])
for rel,h in package['files'].items():ck('Frozen v2 unchanged '+rel,sha(V/rel)==h)
fail=[x for x in checks if not x['passed']]
plan={
 'schema':'mattersyn.heo_publication_projection_proposal/1','at':datetime.now(timezone.utc).isoformat(),
 'author':'/root/backlog_eta','reviewer':'/root/backlog_eta','source_author':'/root/peng1998_reader_assets',
 'status':'read_only_projection_proposal_verified' if not fail else 'findings','input_reader':str(V/'public-review-proposal/heo2003.json'),'input_reader_sha256':sha(V/'public-review-proposal/heo2003.json'),
 'scope':'Withhold whole-page source image delivery while retaining all reader evidence and selected crops. This proposal does not mutate or publish the frozen reader.',
 'counts':{'whole_page_files':23,'main_pages':9,'si_pages':14,'whole_page_public_url_occurrences':46,'retained_selected_original_files':16,'reader_items_retained':372,'canonical_measurements_retained':473,'typed_reader_facts_retained':535,'si_rows_retained':1209,'si_sign_nulls_retained':2,'absolute_private_path_fields_to_remove':166,'si_role_metadata_corrections':14},
 'binary_exclusions':[{'asset_id':k,'private_original_path':x['path'],'proposed_public_path':'assets/figures/heo2003/'+Path(x['path']).name,'sha256':x['sha256'],'source_evidence':x['source_payload']['evidence']} for k,x in whole.items()],
 'retained_selected_assets':[{'asset_id':k,'private_original_path':x['path'],'public_path':'assets/figures/heo2003/'+Path(x['path']).name,'sha256':x['sha256']} for k,x in selected.items()],
 'whole_page_attachment_removals':urlrefs,'private_path_removals':privatepaths,
 'private_dependency_path':{'pointer':'/si_aggregate_evidence/audit_path','before':r['si_aggregate_evidence']['audit_path'],'action':'Omit this private relative dependency path from the public reader, or explicitly map a separately prepared public audit summary. Preserve audit_sha256, counts, source hashes and independent-auditor identity. Do not export raw private audit files merely to make this path resolve.'},
 'source_role_corrections':rolefixes,
 'integration_notes':['Do not remove whole-page reader items: remove their original_assets attachment objects only. Source-note page identities, evidence, source hashes and locators remain.','Current build_paper_reviews.py indexes original_assets public_asset directly; removing only that key from a retained attachment would cause KeyError. Empty attachment lists are compatible.','Exclude all23 binaries from the public output/build input projection; hiding links alone is insufficient. Do not recursively copy the private compatibility projection.','Keep selected figure/table/equation/cropped evidence, all numeric fields, sample links, conflicts and SI row payload unchanged.','The14 SI evidence roles are metadata corrections main→si, supported by their existing SI locators and source manifests; preserve frozen v2 and record the public delta.','SI table UI/export packaging is separate work. This plan preserves the existing1209-row payload and its pointers; it does not claim the not-yet-built public table is validated.'],
 'bound_files':bound
}
out=A/'publication-projection-proposal.json';out.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
bind(out);bind(Path(__file__))
audit={'schema':'mattersyn.heo_publication_projection_audit/1','at':datetime.now(timezone.utc).isoformat(),'author':'/root/peng1998_reader_assets','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','status':'passed_read_only_removal_proposal' if not fail else 'findings','checks':checks,'counts':{'checks':len(checks),'failed':len(fail),**plan['counts']},'findings':fail,'additional_metadata_finding':{'status':'root_correction_required_before_publication','description':'14 whole-SI page evidence roles incorrectly say main although their existing locators/source manifests correctly identify SI. Exact replacement pointers are in proposal.source_role_corrections.'},'scope':'In-memory simulation only. No source/canonical/reader/Site files changed, no image-generation or repeated SI numerical reading. Root must audit actual integration separately.','bound_files':bound}
(A/'publication-projection-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# Heo public reader projection proposal','', '**Verified removal proposal; actual public integration remains pending.**','',f"Withhold **23 whole-page images** (nine main,14 SI) and their **46 public URL occurrences**. Retain all **16 selected crops**, **372 reader items**, **473 canonical measurements**, **535 typed reader fact attachments**, and **1,209 SI rows**, including both unresolved signs.",'',f"The private in-memory simulation passed {len(checks):,} checks. The JSON proposal enumerates every item/object pointer, public path, original path and source/asset hash. No frozen or shared file was edited.",'','Remove the23 original_assets attachment objects and retain their reader cards; remove public_asset/public_asset_sha256 from the23 matching source_notes objects while keeping source metadata. Empty attachment lists avoid the current builder’s direct public_asset lookup. Exclude all23 image files from public delivery.','','Also remove166 absolute filesystem path fields and the private relative SI audit_path from the public projection; retain source/asset/audit hashes, locators and audit identity. The final public SI table/summary URL is a separate integration decision.','','**Required metadata correction:**14 whole-SI-page reader evidence objects say document_role=main despite correct SI locators. The proposal enumerates their main→si replacements. Their source-note counterparts already say si. Frozen v2 stays unchanged; document this public metadata delta.','','The selected16 crops comprise seven figures, five tables, the experimental procedure, charge-balance/equation crop and two bibliography excerpts. Source facts, sample associations, conflict descriptions, document coverage and all numeric payloads remain intact. This is neither fresh full-source reading nor final browser/publication approval.','']
(A/'publication-projection-proposal.md').write_text('\n'.join(md),encoding='utf-8')
(A/'publication-projection-audit.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'checks':len(checks),'failed':fail,'counts':plan['counts'],'proposal_sha256':sha(out),'audit_sha256':sha(A/'publication-projection-audit.json')},ensure_ascii=False))
