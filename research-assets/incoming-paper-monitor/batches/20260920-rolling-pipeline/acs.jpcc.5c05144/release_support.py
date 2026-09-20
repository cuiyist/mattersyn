"""Import-safe draft gates, adapted from the corrected Friedfeld release helper."""
from pathlib import Path
import copy, hashlib, json, re
read=lambda p:json.loads(Path(p).read_text('utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
SID='sasongko2025';GID='legacy::10.1021_acs.jpcc.5c05144'
def paper_root():
 p=Path(__file__).resolve().parent
 return p.parent if p.name=='release-draft' else p
def load_config(J=None):
 J=J or paper_root();p=J/'release-config.json'
 if not p.exists():p=J/'release-draft/release-config.json'
 c=read(p)
 assert c['ready_for_root_execution'] is True,'Fill/review the explicit draft placeholders before execution.'
 assert c['source_id']==SID and c['group_id']==GID and c['source_generation']==1
 assert c['no_new_admissions'] is True and c['later_arrivals_separate'] is True
 assert c['version_is_proposed_until_root_verifies'] is False
 assert isinstance(c['new_material_data_paths'],list) and len(c['new_material_data_paths'])==1
 assert all(isinstance(p,str) and re.fullmatch(r'data/materials/fapbi3-[a-f0-9]{6}\.json',p) for p in c['new_material_data_paths'])
 assert all(isinstance(v,int) for v in c['expected_summary'].values())
 for k in ['expected_reader_count','expected_citation_count','expected_public_asset_count','expected_endpoint_count','expected_additional_withheld_count']:assert isinstance(c[k],int) and c[k]>0,k
 for k in ['promotion_manifest','promotion_freeze','integration_audit','browser_validation','browser_delta_audit','build_checks']:
  x=c[k];assert isinstance(x['sha256'],str) and len(x['sha256'])==64,k
  assert sha(J/x['path'])==x['sha256'],k
 return c
def assert_source_current(J,c):
 identity=read(J/'intake-identity.json');g=read(J.parents[2]/'ledger.json')['groups'][GID]
 assert g['generation']==identity['source_generation']==c['source_generation'] and not g.get('needs_recheck')
 assert g['fingerprint']['bundle_sha256']==identity['bundle_sha256']
 for x in identity['file_copies']:assert sha(x['source_path'])==x['sha256']==g['fingerprint']['files'][x['file_key']]
 return identity
def assert_local_candidate(J,c):
 S=J.parents[4]/'recipe-atlas';O=J/'site-integration-proposal'
 assert read(S/'dist/data/dataset-manifest.json')['dataset_version']==c['dataset_version']
 summary=read(S/'data/inventory-summary.json')['summary']
 assert all(summary[k]==v for k,v in c['expected_summary'].items())
 assert len(read(S/'dist/data/paper-review-index.json')['papers'])==c['expected_reader_count']
 base=read(O/'base-record-hashes.json');assert len(base)==c['prior_record_count']==656
 for rid,h in base.items():assert sha(S/'data/records'/(rid if rid.endswith('.json') else rid+'.json'))==h
 exports=read(O/'base-training-export-hashes.json');assert len(exports)==c['prior_training_export_count']==6
 for n,h in exports.items():assert sha(S/'dist/data/exports'/n)==h
 assert read(O/'old-science-preservation.json')['status']=='passed'
 assert_source_current(J,c)
 for k in ['integration_audit','browser_validation','browser_delta_audit']:assert read(J/c[k]['path'])['status']=='passed',k
 assert all(x['exit_code']==0 for x in read(J/c['build_checks']['path'])['runs'])
 pm=read(J/c['promotion_manifest']['path'])
 assert len(pm['records'])==19 and len(pm['public_assets'])==c['expected_public_asset_count']
 for rel,h in pm['source_audits'].items():assert sha(J/rel)==h and read(J/rel)['status']=='passed'
 return summary
def projected_reader_equal(source,derived,label):
 """Exactly the builder-added display leaf; all other fields are equal."""
 expected=copy.deepcopy(source);expected['review_scope_label']=label
 return expected==derived
def validate_proof_fields(v,plan,c):
 assert plan['source_id']==SID and plan['dataset_version']==c['dataset_version']
 assert plan['count']==len(plan['paths'])==len(set(plan['paths']))==c['expected_endpoint_count']
 assert plan['expected_citation_count']==c['expected_citation_count']
 assert len(plan['additional_withheld_paths'])==len(set(plan['additional_withheld_paths']))==c['expected_additional_withheld_count']
 assert v['status']=='passed' and v['build']['status']=='built' and v['site_commit']==v['build']['commit']
 assert v['expected_citation_count']==c['expected_citation_count']
 a=v['anonymous'];assert a['authenticated'] is False and a['cookies_used'] is False
 checks=a['checks'];assert len(checks)==len(plan['paths']) and {x['path'] for x in checks}==set(plan['paths'])
 assert all(x['http_status']==200 and x['matches_checked_local_bytes'] and x['redirect_stays_on_site'] for x in checks)
 withheld=a['additional_withheld_paths'];assert len(withheld)==len(plan['additional_withheld_paths']) and {x['path'] for x in withheld}==set(plan['additional_withheld_paths'])
 assert all(x['http_status']==404 for x in withheld) and a['excluded_complete_page_http_status']==404
 assert len(v['repositories'])==2 and {x['name'] for x in v['repositories']}=={'mattersyn','mattersyn-site'}
 assert all(x['public'] and x['commit_matches'] and x['anonymous_status']==200 for x in v['repositories'])
 assert len(a['readmes'])==2 and {x['repository'] for x in a['readmes']}=={'mattersyn','mattersyn-site'}
 assert all(x['http_status']==200 and x['bytes_match'] and x['doi_links']==c['expected_citation_count'] for x in a['readmes'])
 return v
def validate_delivery(J,v,plan,c):
 validate_proof_fields(v,plan,c);M=J.parents[4];S=M/'recipe-atlas';D=M.parent/'mattersyn-github-public-clean/mattersyn-site'
 checks=v['anonymous']['checks']
 for x in checks:assert x['sha256']==sha(D/x['path']),'Verified projected bytes changed: '+x['path']
 bypath={x['path']:x for x in checks}
 for rel in ['data/dataset-manifest.json','data/paper-reviews/'+SID+'.json']:assert bypath[rel]['sha256']==sha(S/'dist'/rel)
 assert projected_reader_equal(read(S/('data/paper-reviews/'+SID+'.json')),read(S/('dist/data/paper-reviews/'+SID+'.json')),c['reader_scope_label'])
 assert_local_candidate(J,c)
 return v
