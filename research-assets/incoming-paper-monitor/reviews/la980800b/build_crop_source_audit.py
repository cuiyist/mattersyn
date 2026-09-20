"""Private source-crop audit after independent visual examination of all four sheets."""
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent;M=B/'crop-assets/manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(M.read_text(encoding='utf8'));checks=[]
def check(n,b):checks.append({'name':n,'passed':bool(b)})
check('Verified9page source',d['source_sha256']=='e581449713ddca5e0cb68d05593df476d0e5150b88bc7c6dcbdb269ac70881fb'and d['source_page_count']==9)
expected={**{f'figure-{n:02d}':p for n,p in enumerate([2,3,4,5,6,7,8,8,8],1)},'figure-06b-saed':7,'scheme-01':4,'table-01':7,'equation-01':4,'equation-02':5,'equation-03':9}
check('All15expectedoriginalassets',len(d['assets'])==15 and {a['id']for a in d['assets']}==set(expected))
for a in d['assets']:
 check(a['id']+' exact image and page',sha(B/'crop-assets'/a['relative_asset'])==a['sha256']and a['pdf_page']==expected[a['id']])
 check(a['id']+' original source with locators and scope',a['original_source_asset']and not a['synthetic']and not a['digitized']and not a['eligible_training']and bool(a['sample_scope'])and len(a['bbox_pdf_points_top_left'])==4)
 check(a['id']+' correctsourcehash',a['source_sha256']==d['source_sha256'])
assets={a['id']:a for a in d['assets']}
check('ActualSAEDisolatedfromindexingschematic','SAED'in assets['figure-06b-saed']['title']or'selected-area'in assets['figure-06b-saed']['title'].lower())
notes=['All15assets independently viewed on four contact sheets and compared with already-read full source pages. Axes, legends, Figure4inset, Figure5heightprofiles, Table1footnotes, Figure7panelnumbers and originalcaptionconflicts remain legible.','Figure6fullasset contains TEM, actualSAED and authorindexingdrawing; the dedicated6b crop retains only the original measured SAED with its panelmarker. It does not include a duplicated fullcaption, available with fullFigure6.','Figure1 is pristineSi; Figure2d doping/axisunits and1vs10mMAgremain sourceconflicts; Figure3is1.5mMthreepotentialcomparison; Figure4isone trace replotted.','Figure5mC printedcharges remain distinct fromFigure7/9µC; Figure7fourvisiblehistogramsremainfour despitefive-caption; Figure8densityaxis versusheightcaption remains visible.','Equation2is preserved without inserting missingF or definingA. Table1expected111=2.32Åunchanged. Referenceintensities remain separatefrommeasuredSAED.','No curve or histogrambin digitization, inferredexperiments, XRDpattern or atomicpositions. No publicpathsanitization/renderer/publishing claim; root owns integration. SIunverified.']
out={'source_id':'stiger1999','status':'passed'if all(x['passed']for x in checks)else'must_fix','manifest_sha256':sha(M),'asset_count':15,'check_count':len(checks),'checks':checks,'open_findings':[],'independent_visual_review':[{'basename':p.name,'sha256':sha(p),'status':'independently_viewed'}for p in sorted((B/'crop-assets').glob('contact-*.png'))],'assets':[{'id':a['id'],'basename':a['relative_asset'],'sha256':a['sha256'],'pdf_page':a['pdf_page']}for a in d['assets']],'scope_notes':notes}
(B/'crop-source-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'crop-source-audit.md').write_text('# Independent Stiger original-crop audit\n\nStatus: **'+out['status']+'**. All15sourcecrops independently inspected;'+str(len(checks))+'boundedchecks.\n\n'+'\n'.join('- '+n for n in notes)+'\n',encoding='utf8')
print(json.dumps({'status':out['status'],'checks':len(checks),'failed':[x for x in checks if not x['passed']]}))
