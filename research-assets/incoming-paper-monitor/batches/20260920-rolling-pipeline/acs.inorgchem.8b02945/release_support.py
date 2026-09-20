"""Import-safe, read-only Friedfeld release gates. No network or credentials."""
from pathlib import Path
import hashlib,json
read=lambda p:json.loads(Path(p).read_text('utf8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
SID='friedfeld2019';VERSION='0.32.0';GID='legacy::10.1021_acs.inorgchem.8b02945'
def assert_source_current(F):
 M=F.parents[4];MON=F.parents[2];identity=read(F/'intake-identity.json');ledger=read(MON/'ledger.json');g=ledger['groups'][GID]
 assert g['generation']==identity['source_generation']==1 and not g.get('needs_recheck')
 assert g['fingerprint']['bundle_sha256']==identity['bundle_sha256']
 for x in identity['file_copies']:
  assert sha(x['source_path'])==x['sha256']==g['fingerprint']['files'][x['file_key']]
 return identity
def assert_local_candidate(F):
 M=F.parents[4];S=M/'recipe-atlas';O=F/'site-integration-proposal'
 assert read(S/'dist/data/dataset-manifest.json')['dataset_version']==VERSION
 summary=read(S/'data/inventory-summary.json')['summary']
 expected={'canonical_records':656,'synthesis_route_variant_records':122,'public_material_hubs':49,'direct_synthesis_target_systems':38,'component_only_hubs':11,'total_canonical_source_groups':40,'verified_exact_structure_recipe_pairs':0}
 assert all(summary[k]==v for k,v in expected.items())
 assert len(read(S/'dist/data/paper-review-index.json')['papers'])==35
 base=read(O/'base-record-hashes.json');assert len(base)==626
 for rid,h in base.items():assert sha(S/'data/records'/(rid if rid.endswith('.json')else rid+'.json'))==h
 exports=read(O/'base-training-export-hashes.json');assert len(exports)==6
 for n,h in exports.items():assert sha(S/'dist/data/exports'/n)==h
 assert read(O/'old-science-preservation.json')['status']=='passed'
 assert_source_current(F)
 return summary
def validate_delivery(F,v,plan):
 """Check actual proof bytes; a completed record is impossible before this returns."""
 M=F.parents[4];S=M/'recipe-atlas';D=M.parent/'mattersyn-github-public-clean/mattersyn-site'
 assert plan['source_id']==SID and plan['dataset_version']==VERSION and plan['count']==len(plan['paths'])==547
 assert len(set(plan['paths']))==547 and plan['expected_citation_count']==40
 assert len(plan['additional_withheld_paths'])==18 and len(set(plan['additional_withheld_paths']))==18
 assert v['status']=='passed'and v['build']['status']=='built'and v['site_commit']==v['build']['commit']
 assert v['expected_citation_count']==40
 a=v['anonymous'];assert a['authenticated']is False and a['cookies_used']is False
 checks=a['checks'];assert len(checks)==547 and {x['path']for x in checks}==set(plan['paths'])
 assert all(x['http_status']==200 and x['matches_checked_local_bytes']and x['redirect_stays_on_site']for x in checks)
 for x in checks:assert x['sha256']==sha(D/x['path']),'Verified projected bytes have changed: '+x['path']
 withheld=a['additional_withheld_paths'];assert len(withheld)==18 and {x['path']for x in withheld}==set(plan['additional_withheld_paths'])
 assert all(x['http_status']==404 for x in withheld)and a['excluded_complete_page_http_status']==404
 assert len(v['repositories'])==2 and {x['name']for x in v['repositories']}=={'mattersyn','mattersyn-site'}
 assert all(x['public']and x['commit_matches']and x['anonymous_status']==200 for x in v['repositories'])
 assert len(a['readmes'])==2 and {x['repository']for x in a['readmes']}=={'mattersyn','mattersyn-site'}
 assert all(x['http_status']==200 and x['bytes_match']and x['doi_links']==40 for x in a['readmes'])
 bypath={x['path']:x for x in checks}
 for rel in ['data/dataset-manifest.json','data/paper-reviews/friedfeld2019.json']:
  assert bypath[rel]['sha256']==sha(S/'dist'/rel)
 assert sha(S/'data/paper-reviews/friedfeld2019.json')==sha(S/'dist/data/paper-reviews/friedfeld2019.json')
 assert_local_candidate(F)
 return v
