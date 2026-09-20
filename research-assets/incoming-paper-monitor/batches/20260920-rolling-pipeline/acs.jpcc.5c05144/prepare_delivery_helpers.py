"""Root-only endpoint-plan preparation. Default writes private proposed files only."""
from pathlib import Path
import argparse, json
from release_support import read,sha,paper_root,load_config,SID
def make_plan(prior,pm,c):
 assets=[x['public_path'] for x in pm['public_assets']]
 records=[x['record_id'] for x in pm['records']]
 assert len(records)==len(set(records))==19
 assert len(assets)==len(set(assets))==c['expected_public_asset_count']
 assert all(not Path(p).is_absolute() and '..' not in Path(p).parts and ':' not in p and '\\' not in p for p in assets)
 assert all('/pages/' not in p and not p.lower().endswith(('.pdf','.doc','.docx','.zip','.txt')) for p in assets)
 extra=['data/paper-reviews/'+SID+'.json','paper-review.mjs','paper-review.css','paper-review.html','data/inventory-summary.json']+c['new_material_data_paths']+assets+[p for rid in records for p in ['records/'+rid+'.html','data/records/'+rid+'.json']]
 assert len(extra)==len(set(extra)) and not(set(extra)&set(prior['paths']))
 paths=prior['paths']+extra
 withheld=prior['additional_withheld_paths']+['assets/figures/'+SID+'/pages/main-01.png','assets/figures/'+SID+'/pages/si-01.png']
 assert len(paths)==c['expected_endpoint_count'] and len(withheld)==c['expected_additional_withheld_count']
 return {'dataset_version':c['dataset_version'],'source_id':SID,'paths':paths,'count':len(paths),'expected_citation_count':c['expected_citation_count'],'additional_withheld_paths':withheld,'additional_withheld_count':len(withheld),'extra_endpoints':len(extra),'extra_scope':'One reader, every frozen public asset and all 19 HTML/JSON record pairs; prior endpoints retained in order.','source_projection_manifest_sha256':c['promotion_manifest']['sha256'],'source_projection_freeze_sha256':c['promotion_freeze']['sha256']}
def extend_verifier(original,extra):
 marker='assert len(paths)==len(set(paths))';wm='withheld_checks=['
 assert original.count(marker)==original.count(wm)==1
 addition="if (D/'data/paper-reviews/sasongko2025.json').exists():\n paths += "+repr(extra)+'\n'
 after=original.replace(marker,addition+marker)
 withheld="if (D/'data/paper-reviews/sasongko2025.json').exists():withheld += ['assets/figures/sasongko2025/pages/main-01.png','assets/figures/sasongko2025/pages/si-01.png']\n"
 after=after.replace(wm,withheld+wm)
 assert after.replace(addition,'').replace(withheld,'')==original
 return after
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
 J=paper_root();D=J/'release-draft';O=J/'site-integration-proposal';M=J.parents[4];c=load_config(J)
 prior=read(J.parent/'acs.inorgchem.8b02945/site-integration-proposal/release-endpoints.json')
 assert prior['source_id']=='friedfeld2019' and prior['count']==547
 pm=read(J/c['promotion_manifest']['path']);plan=make_plan(prior,pm,c)
 target=M/'research-assets/verify_public_delivery.py';snapshot=D/'input-snapshots/verify_public_delivery.py'
 original=snapshot.read_text('utf8');proposed=extend_verifier(original,plan['paths'][len(prior['paths']):])
 assert target.read_text('utf8') in [original,proposed],'Shared verifier changed; review a new preserved delta.'
 (D/'release-endpoints-proposed.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8')
 (D/'verify_public_delivery-proposed.py').write_text(proposed,'utf8')
 if args.apply:
  p=O/'release-endpoints.json'
  assert not p.exists() or read(p)==plan
  p.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8');target.write_text(proposed,'utf8')
  print('Root adopted the endpoint extension; no network, ledger or publication action executed.')
 else:print('Private endpoint and verifier proposals saved; shared verifier unchanged.')
if __name__=='__main__':main()
