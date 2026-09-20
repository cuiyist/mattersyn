from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib
B=Path(__file__).resolve().parent;MON=B.parent.parent;M=MON.parent.parent;S=M/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
n=read(B/'native-publication.json');saved=n['saved_version'];d=n['deployment']
assert d['status']=='succeeded' and d['url'] and saved['id']==d['version_id']
assert saved['source']['commit_sha']==read(B/'publication-source.json')['commit_sha']
ledger=read(MON/'ledger.json');assert ledger['current_paper']['group_id']=='10.1021_jp010002l'
g=ledger['groups']['10.1021_jp010002l'];fp=g['fingerprint']
assert fp['generation']==g['generation']==2
assert fp['bundle_sha256']=='f09cafb6571e19e9dade734c99c74202528a6648701947a446c46d64434e7f90'
assert set(fp['files'].values())=={'00ac817e60651f0e7f9faabe85ba18372ac37fea1f0f5d174779c982064b4184'}
write(B/'final-source-fingerprint.json',{'group_id':'10.1021_jp010002l',**fp})
inv=read(S/'data/inventory-summary.json');row=next(x for x in inv['per_paper']if x['source_group']=='braun2001')
index=read(S/'dist/data/materials-index.json');hub=next(x for x in index['materials']if x['formula']=='CdS/HgS/CdS')
archive=S/'.sites-runtime/site-braun2001.tar.gz'
p=dict(status='published',source_commit=saved['source']['commit_sha'],site_project_id=saved['project_id'],public_live_version=saved['version_number'],dataset_version='0.15.0',source_pushed=True,archive=str(archive.relative_to(M)),archive_sha256=sha(archive),archive_storage=saved['archive_storage'],version_id=saved['id'],deployment_id=d['id'],deployment_status=d['status'],public_url=d['url'],published_at=d['updated_at'],review_scope='supplied_main_only_si_unverified',source_id='braun2001',doi='10.1021/jp010002l',records=9,synthesis_routes=3,controls=0,supporting_procedures=3,contextual_observations=3,measurement_entries=75,operations=45,reader_evidence_items=85,source_audit_units=132,typed_facts=179,original_assets=8,original_figures=4,original_tables=0,canonical_records_total=inv['summary']['canonical_records'],material_hubs_total=len(index['materials']),source_groups_total=inv['summary']['total_canonical_source_groups'],source_documents_unchanged=True,source_generation=2,source_fingerprint_at=fp['created_at'],bundle_sha256=fp['bundle_sha256'],native_publication_evidence='native-publication.json',browser_checks='browser-qa.json',build_checks='build-validation.json',independent_audit=['source-audit.json','canonical-records-audit.json','reader-source-audit.json','molecular-source-audit.json','bindings-source-audit.json','visual-source-audit.json','role-normalization-source-audit.json','public-review-proposal/proposal-validation.json','reader-assets/integrated-presentation-audit.json'],material_url=d['url'].rstrip('/')+'/'+hub['url'],paper_url=d['url'].rstrip('/')+'/paper-review.html?id=braun2001',si_status='No SI declaration observed in supplied main; matching SI not located or verified.')
assert row['canonical_record_count']==9 and row['synthesis_route_variant_count']==3 and row['procedure_count']==3 and row['contextual_observation_count']==3
write(B/'publication-checkpoint.json',p)
ms=read(B/'milestones.json');ms['publish']={'status':'complete','evidence':[str(B/'publication-checkpoint.json'),str(B/'native-publication.json'),str(B/'final-source-fingerprint.json')],'note':'Native deployment succeeded on the same existing public MatterSyn Site. Source generation unchanged after publication. Closure covers the supplied main only; matching SI remains unverified and later SI reopens review.'}
assert all(x['status']=='complete' and x['evidence']for x in ms.values());write(B/'milestones.json',ms)
c=read(B/'checkpoint.json');c.update(website_published=True,checkpoint_at=datetime.now(timezone.utc).isoformat(),public_live_version=saved['version_number'],dataset_version='0.15.0',publication_evidence=str(B/'publication-checkpoint.json'),current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']}for k,v in ms.items()],next_action='Supplied main review closed after native publication. Continue oldest eligible local arrival through the existing heartbeat; late SI reopens this source.');write(B/'checkpoint.json',c)
print(json.dumps({'publication':'succeeded','version':saved['version_number'],'material_url':p['material_url'],'source_generation':2,'milestones':'complete'}))
