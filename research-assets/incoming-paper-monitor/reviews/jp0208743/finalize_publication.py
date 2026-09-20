from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;MON=B.parent.parent;M=MON.parent.parent;S=M/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
n=read(B/'native-publication.json');saved=n['saved_version'];d=n['deployment']
assert d['status']=='succeeded' and d['url'] and saved['id']==d['version_id']
assert saved['source']['commit_sha']==read(B/'publication-source.json')['commit_sha']
ledger=read(MON/'ledger.json');assert ledger['current_paper']['group_id']=='10.1021_jp0208743'
g=ledger['groups']['10.1021_jp0208743'];fp=g['fingerprint']
assert fp['generation']==g['generation']==2
assert fp['bundle_sha256']=='a44f927e3c2b3e9f75925e1e47cd105acc652c443b4ace1ab471cf3cac603a41'
assert set(fp['files'].values())=={'c8fd35a429bf636fcccc5dfeb3211cea44299e911fbfc80e1a308c75b7b04917'}
write(B/'final-source-fingerprint.json',{'group_id':'10.1021_jp0208743',**fp})
inv=read(S/'data/inventory-summary.json');row=next(x for x in inv['per_paper']if x['source_group']=='dantas2002')
index=read(S/'dist/data/materials-index.json');hub=next(x for x in index['materials']if x['formula']=='PbS/glass')
reader=read(S/'data/paper-reviews/dantas2002.json');audit=read(B/'source-audit.json');records=[read(S/'data/records'/(k+'.json'))for k in row['record_ids']]
archive=S/'.sites-runtime/site-dantas2002.tar.gz';assert sha(archive)==read(B/'archive-validation.json')['sha256']
p=dict(status='published',source_commit=saved['source']['commit_sha'],site_project_id=saved['project_id'],public_live_version=saved['version_number'],dataset_version='0.17.0',source_pushed=True,archive=str(archive.relative_to(M)),archive_sha256=sha(archive),archive_storage=saved['archive_storage'],version_id=saved['id'],deployment_id=d['id'],deployment_status=d['status'],public_url=d['url'],published_at=d['updated_at'],review_scope='supplied_main_only_si_unverified',source_id='dantas2002',doi='10.1021/jp0208743',records=len(records),synthesis_routes=row['synthesis_route_variant_count'],controls=row['contextual_control_count'],supporting_procedures=row['procedure_count'],contextual_observations=row['contextual_observation_count'],measurement_entries=sum(len(r['measurements'])for r in records),operations=sum(len(r['operations'])for r in records),reader_evidence_items=sum(len(s['items'])for s in reader['reader_sections']),source_audit_units=audit['unit_count'],typed_facts=sum(reader['counts'][k]for k in ['typed_characterization_rows','operation_parameter_facts','reagent_quantity_facts','stock_quantity_facts']),source_typed_anchors=audit['typed_anchor_count'],original_assets=len(read(B/'reader-assets/crop-manifest.json')['assets']),original_figures=7,original_tables=0,canonical_records_total=inv['summary']['canonical_records'],material_hubs_total=len(index['materials']),source_groups_total=inv['summary']['total_canonical_source_groups'],source_documents_unchanged=True,source_generation=2,source_fingerprint_at=fp['created_at'],bundle_sha256=fp['bundle_sha256'],native_publication_evidence='native-publication.json',browser_checks='browser-qa.json',build_checks='build-validation.json',independent_audit=['source-audit.json','canonical-records-audit.json','reader-source-audit.json','molecular-source-audit.json','bindings-source-audit.json','visual-source-audit.json','public-review-proposal/proposal-validation.json','reader-assets/integrated-presentation-audit.json'],material_url=d['url'].rstrip('/')+'/'+hub['url'],paper_url=d['url'].rstrip('/')+'/paper-review.html?id=dantas2002',si_status='No SI declaration observed in supplied main; matching SI not located or verified.')
assert len(records)==16 and p['synthesis_routes']==6 and p['operations']==48
write(B/'publication-checkpoint.json',p)
ms=read(B/'milestones.json');ms['publish']={'status':'complete','evidence':[str(B/'publication-checkpoint.json'),str(B/'native-publication.json'),str(B/'final-source-fingerprint.json')],'note':'Native publication succeeded on the same existing public MatterSyn Site. Source generation unchanged. Closure covers supplied main only; later SI reopens review.'}
assert all(x['status']=='complete' and x['evidence']for x in ms.values());write(B/'milestones.json',ms)
c=read(B/'checkpoint.json');c.update(website_published=True,checkpoint_at=datetime.now(timezone.utc).isoformat(),public_live_version=saved['version_number'],dataset_version='0.17.0',publication_evidence=str(B/'publication-checkpoint.json'),current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']}for k,v in ms.items()],next_action='Supplied-main contribution published and closed. Continue oldest eligible local arrival through existing heartbeat; later SI reopens this source.');write(B/'checkpoint.json',c)
print(json.dumps({'publication':'succeeded','version':p['public_live_version'],'material_url':p['material_url'],'records':p['records'],'milestones':'complete'}))

