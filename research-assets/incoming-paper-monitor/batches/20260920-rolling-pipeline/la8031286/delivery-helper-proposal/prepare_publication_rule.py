from pathlib import Path
import json,hashlib
N=Path(__file__).resolve().parent
if N.name=='delivery-helper-proposal':N=N.parent
O=N/'site-integration-proposal';S=N.parents[4]/'recipe-atlas'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=S/'data/paper-reviews/pati2009.json';r=json.loads(p.read_text('utf8'));assert r['presentation_gates']['browser_render'] is True and r['presentation_gates']['publication'] is False
proposal={'author':'/root/norberg2004_extract','executed_by':'root after review','baseline_reader_sha256':sha(p),'finalizer_script_sha256':sha(N/'finalize_reader_publication.py'),'endpoint_plan_sha256':sha(O/'release-endpoints.json'),'exact_allowed_changes':[{'pointer':'/presentation_gates/publication','before':False,'after':True},{'pointer':'/publication_status','before':r['publication_status'],'after':'Published after independent source, data, illustration and integrated browser reviews; exact deployed GitHub Pages commit and anonymous public bytes verified. Complete supplied main and matched SI reviewed; source conflicts remain explicit.'}],'only_after':'Passed exact science release proof for dataset0.31.0,39 citations, 324 allowlisted endpoints and matching site/build commit. No scientific field changes.'}
(O/'conditional-publication-rule-proposal.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n','utf8')
print('Conditional publication rule prepared for separate audit; not applied.')
