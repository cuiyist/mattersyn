"""Root-only two-leaf publication labels, after actual anonymous science proof."""
from datetime import datetime,timezone
from pathlib import Path
import argparse,copy,json
from release_support import read,sha,paper_root,load_config,validate_delivery,SID
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
 J=paper_root();O=J/'site-integration-proposal';S=J.parents[4]/'recipe-atlas';c=load_config(J)
 prep=read(O/'release-preparation.json');plan=read(O/'release-endpoints.json')
 assert prep['status']=='prepared_unpublished' and prep['dataset_version']==c['dataset_version'] and prep['source_id']==SID
 assert prep['finalizer_script_sha256']==sha(Path(__file__)) and prep['release_support_sha256']==sha(J/'release_support.py')
 assert prep['config_sha256']==sha(J/'release-config.json') and prep['endpoint_plan_sha256']==sha(O/'release-endpoints.json')
 proof=O/'science-release-anonymous-verification.json';v=validate_delivery(J,read(proof),plan,c)
 p=S/('data/paper-reviews/'+SID+'.json');assert sha(p)==prep['reader_sha256'];before=read(p)
 assert before['paper_id']==SID and before['presentation_gates']['browser_render'] is True and before['presentation_gates']['publication'] is False
 assert before['presentation_gates']['exact_product_atomic_structure_binding'] is False
 after=copy.deepcopy(before);after['presentation_gates']['publication']=True
 after['publication_status']='Published after independent source, canonical, illustration and integrated browser reviews; exact deployed GitHub Pages commit and anonymous public bytes verified. Complete supplied main and matched SI reviewed; source conflicts and reference-versus-measured structure limits remain explicit.'
 check=copy.deepcopy(after);check['presentation_gates']['publication']=False;check['publication_status']=before['publication_status'];assert check==before
 if not args.apply:print('Actual science proof and exact two-leaf delta verified; no mutation.');return
 assert not(O/'publication-label-delta.json').exists()
 save(O/'reader-pre-publication-label.json',before);save(p,after)
 save(O/'publication-label-delta.json',{'at':datetime.now(timezone.utc).isoformat(),'status':'applied_after_verified_release','preparation_sha256':sha(O/'release-preparation.json'),'anonymous_proof_sha256':sha(proof),'science_commit':v['site_commit'],'before_sha256':prep['reader_sha256'],'after_sha256':sha(p),'exact_two_leaf_changes':True,'all_other_data_deep_equal':True,'changes':[{'pointer':'/presentation_gates/publication','before':False,'after':True},{'pointer':'/publication_status','before':before['publication_status'],'after':after['publication_status']}]})
 print('Two labels applied after verified science; regenerate and separately verify final paused progress delivery.')
if __name__=='__main__':main()
