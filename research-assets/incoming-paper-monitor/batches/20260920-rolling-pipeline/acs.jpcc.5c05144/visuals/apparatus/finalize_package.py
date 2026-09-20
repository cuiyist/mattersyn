"""Freeze only this private apparatus proposal after actual author inspection."""
from pathlib import Path
import json, hashlib, re
from datetime import datetime, timezone
A=Path(__file__).resolve().parent;J=A.parents[1];C=J/'canonical-proposal/v1'
assert not (A/'package-freeze.json').exists(), 'Never overwrite a freeze.'
read=lambda p:json.loads(Path(p).read_bytes())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(A/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
checks=[];inputs={}
def ck(label,yes):
 checks.append({'check':label,'passed':bool(yes)})
 assert yes,label
def bind(p,h=None):
 p=Path(p);actual=sha(p)
 if h:ck('SHA256 '+str(p),actual==h)
 inputs[str(p)]=actual
 return actual
def boundary(p,expected):
 bind(p,expected);v=read(p)
 for path,h in v['bound_files'].items():
  q=Path(path);bind(q if q.is_absolute() else p.parent/q,h)
 return v
source=boundary(J/'source-extraction-revision-2/package-freeze.json','d34778349e9942a73a1d275536af354e93d52739692e689fe2f12d394db7fddc')
canonical=boundary(C/'package-freeze.json','3cab2fe6181dbf2149b2a0ac59f4a80d99c05cab4870342e141815c904549fb5')
sourceaudit=J/'source-independent-audit/independent-audit-v2.json'
caudit=J/'canonical-independent-audit/independent-audit-v1.json'
bind(sourceaudit,'c709225b9555ba89d3d952a6153561b011351c00fb2c62733c920447479edb58')
bind(caudit,'86691d16cedb8115d02e46c9d658e6a25f96593cc9f8d2363733ec81bffd71aa')
ck('Distinct upstream source and canonical audits passed',read(sourceaudit)['status']=='passed' and read(caudit)['status']=='passed')
for x in read(J/'intake-identity.json')['file_copies']:bind(x['source_path'],x['sha256'])
records={r['record_id']:r for r in read(A/'records.json')};bindings=read(A/'canonical-bindings.json')['bindings']
scenes=read(A/'rendered-scenes.json');configs=read(A/'scene-config.json')['configs'];typed=read(A/'typed-field-map.json')
rm=read(C/'record-manifest.json')['records']
for r in rm:
 bind(r['path'],r['sha256'])
 if r['record_id'] in records:ck('Exact operational record '+r['record_id'],read(r['path'])==records[r['record_id']])
ck('All and only operational records',set(records)=={r['record_id'] for r in rm if read(r['path'])['operations']})
ck('21 scene configurations and mappings',len(scenes)==len(bindings)==len(configs)==21)
ck('Every operation once',set((s['record_id'],s['operation_id']) for s in scenes)==set((r['record_id'],o['id']) for r in records.values() for o in r['operations']))
def at(x,p):
 for k in p.split('/')[1:]:x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
 return x
facts=read(J/'source-extraction-revision-2/source-facts.json');factids={f['id'] for f in facts['facts']}
for b in bindings:
 r=records[b['record_id']];o=at(r,b['operation_pointer']);s=next(s for s in scenes if s['kind']==b['scene_id'])
 for k in ['inputs','outputs','retained_fraction']:ck(b['scene_id']+' exact '+k,b[k]==o[k])
 ck(b['scene_id']+' exact evidence',b['source_evidence']==o['evidence'])
 ck(b['scene_id']+' source facts exist',set(b['source_context_fact_ids'])<=factids)
 ck(b['scene_id']+' description from passed reader',s['description']==b['human_prose'])
 ck(b['scene_id']+' explanatory scope', 'explanatory' in s['caption'] and 'measured images and structure data remain separate' in s['caption'])
 for t in [t for t in typed if t['scene_id']==b['scene_id']]:ck(b['scene_id']+t['pointer'],at(r,t['pointer'])==t['quantity'])
ck('35 operation parameters and 135 paired-context quantities',sum(x['kind']=='operation_parameter' for x in typed)==35 and sum(x['kind']=='paired_comparison_context' for x in typed)==135)
route=records['sasongko-2025-hot-injection'];ops={o['id']:o for o in route['operations']}
ck('One coherent 12-stage route',len(route['operations'])==12)
ck('Retain first precipitate then final supernatant',ops['first-spin']['retained_fraction']=='first-precipitate' and ops['second-spin']['retained_fraction']=='final-supernatant')
ck('Hexane receives first precipitate', 'first-precipitate' in ops['redisperse-hexane']['inputs'])
ck('0.51 mL injection is only an aliquot',ops['inject-fa']['parameters']['fa_precursor_aliquot']['value']==.51 and len(ops['inject-fa']['parameters'])==1)
ck('Nine source-paired comparison options',len(route['condition_options'])==9)
expected=[(100,.4,.2,1,20),(100,.6,.2,1,20),(100,.8,.2,1,20),(100,.6,.2,1,1),(100,.6,.2,1,10),(100,.6,.2,1,20),(25,.6,.2,1,20),(50,.6,.2,1,20),(100,.6,.2,1,20)]
keys=['growth_temperature','oa_volume','oam_volume','wash_acetonitrile_parts','wash_toluene_parts']
ck('Companion conditions retained, no Cartesian combinations',[tuple(o['parameters'][k]['value'] for k in keys) for o in route['condition_options']]==expected)
for s in scenes:
 rows=[r for r in s['rows'] if r['kind']=='paired_comparison_context']
 ck(s['kind']+' paired context placement',len(rows)==(9 if s['operation_id'] in ['add-oa','cool-equilibrate','add-wash'] else 0))
 if rows:ck(s['kind']+' not simultaneous actions','Current action' in [r['label'] for r in s['rows']])
module=A/'sasongko2025-protocol.mjs';code=module.read_text('utf8')
ck('Public module no private paths',not re.search(r'C:[\\/]|Desktop|source-render|downloaded_papers',code))
ck('Only source-neutral formatter import',re.findall(r"from ['\"]([^'\"]+)['\"]",code)==['./quantity-value.mjs'])
formatter=J.parents[3]/'recipe-atlas/dist/quantity-value.mjs'
# The Site is read-only. Locate it explicitly rather than inferring a sibling.
formatter=Path('[local path redacted]')
ck('Existing Site quantity formatter byte-compatible',sha(formatter)==sha(A/'quantity-value.mjs'));bind(formatter)
for h in read(A/'helper-provenance.json')['templates']:bind(h['path'],h['sha256'])
mc=read(A/'module-author-checks.json');ck('Actual module checks passed',mc['check_count']==426 and all(c['passed'] for c in mc['checks']))
pm=read(A/'preview-manifest.json');inspected=[]
for item in pm['scenes']:
 for prefix in ['svg','png','art_svg','art_png']:
  p=A/item[prefix+'_path'];ck('Rendered asset '+str(p.relative_to(A)),sha(p)==item[prefix+'_sha256'])
 inspected.append({'scene_id':item['scene_id'],'full_png':item['png_path'],'full_png_sha256':item['png_sha256'],'art_png':item['art_png_path'],'art_png_sha256':item['art_png_sha256'],'author_actually_viewed':True,'scope':'Art contacts and full-condition contacts; long paired-context panels also read at standalone size.'})
for item in pm['contacts']+pm['art_contacts']:ck('Contact '+item['path'],sha(A/item['path'])==item['sha256'])
sourceviews=[]
for n in ['si-03.png','si-04.png','main-06.png']:
 p=J/'source-render'/n;sourceviews.append({'path':str(p),'sha256':bind(p),'read_viewed_in_this_apparatus_author_turn':True})
priorreceipt=C/'author-reading-receipt.json';bind(priorreceipt)
manual=[
 '15 preparation/synthesis stages compared with the original SI S3; no numerical pressure or apparatus geometry invented.',
 'FA 0.1042 g / OA 0.8 mL / ODE 3.2 mL whole-stock charges remain separate from the 0.51 mL injection.',
 'Lead degassing is 60 °C / 30 min; explicit vacuum belongs to FA preparation. Nitrogen belongs to the synthesis statement and FA hot hold, not automatically to optical acquisition.',
 '135 °C precursor treatment, OA then OAm order, and selected 25/50/100 °C hold remain distinct.',
 'Nine comparison contexts retain all fixed companion values; no 27-condition experimental matrix or physical sample identity is inferred.',
 'First 12,000 rpm / 5 min retains precipitate; hexane redispersion precedes 6,000 rpm / 5 min and final supernatant retention.',
 'XRD, TEM, TRPL and thermal optics represent separate specimens and unreported mounting/atmosphere remains explicit.',
 '404 nm, 4 ns and triple-exponential fitting are acquisition/analysis details; no fitted trace or individual coefficients are fabricated.',
 'Raman attempted 80–200 K and displayed 80–190 K remain distinct; 633 nm and 50–300 cm−1 match source.',
 'PL 80–430 K acquisition differs from 140/250 K phase interpretations; no structural coordinates inferred.',
 '350 K aging shows 0–210 min every 30 min and a separate 300 K reference; normalized slope remains a result.',
 'All 21 illustrations, all adjacent rows and three long condition layouts inspected. Pre-freeze label/arrow overlaps corrected and affected renders reopened.'
]
save('author-visual-review.json',{'author':'/root/norberg2004_extract','status':'completed_author_visual_inspection_pending_distinct_audit','scenes':inspected,'source_views_this_turn':sourceviews,'earlier_source_review_receipt':{'path':str(priorreceipt),'sha256':sha(priorreceipt),'scope':'Earlier bounded canonical-author reading of main/SI and selected crops; not a new full independent source audit.'},'manual_scope_checks':manual,'browser_executed':False,'independent_approval':False})
pm['visual_review_status']='completed_author_static_inspection_pending_distinct_audit';pm['visual_review_receipt']='author-visual-review.json';save('preview-manifest.json',pm)
save('public-module-proposal.json',{'status':'private_pending_distinct_apparatus_audit','source_group':'sasongko2025','assets':[{'source_path':str(module),'public_path':'sasongko2025-protocol.mjs','sha256':sha(module),'role':'stage_specific_explanatory_svg_module'}],'existing_dependency':{'public_path':'quantity-value.mjs','sha256':sha(A/'quantity-value.mjs')},'public_original_documents':0,'public_full_pages':0,'public_raw_text':0,'browser_approval':False,'training_approval':False})
save('author-validation.json',{'status':'passed_author_checks_pending_distinct_audit','checks':checks,'check_count':len(checks),'module_check_count':mc['check_count'],'combined_executed_checks':len(checks)+mc['check_count'],'counts':{'records':8,'scenes':21,'operation_parameter_displays':35,'comparison_contexts':9,'comparison_rows':27,'comparison_quantity_displays':135,'typed_quantity_displays':170,'scope_notes':58,'all_rows':120,'full_svg':21,'art_svg':21,'full_png':21,'art_png':21,'contacts':10},'manual_scope_checks':len(manual),'independent_approval':False})
(A/'author-progress.md').write_text('# Sasongko apparatus frozen handoff\n\nThe 21-scene author package is complete and frozen in package-freeze.json, pending distinct independent apparatus review. All 21 art scenes and condition layouts were actually inspected; all three long paired-context layouts were read separately. All source and canonical bytes remain unchanged.\n\nNext action: a separate reviewer should verify the frozen manifest, scene/source/field bindings, all rendered panels and actual module behavior. Root owns subsequent Site integration and mounted browser checks. No apparatus-independent, training or publication approval is asserted. Only this active paper was advanced; no new paper admitted.\n','utf8')
bound={str(p.relative_to(A)).replace('\\','/'):sha(p) for p in sorted(A.rglob('*')) if p.is_file() and p.name!='package-freeze.json' and '__pycache__' not in p.parts}
freeze={'schema':'mattersyn-private-apparatus-freeze/1','author':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'status':'frozen_author_proposal_pending_distinct_audit','source_group':'sasongko2025','source_generation':1,'source_freeze_sha256':sha(J/'source-extraction-revision-2/package-freeze.json'),'source_audit_sha256':sha(sourceaudit),'canonical_freeze_sha256':sha(C/'package-freeze.json'),'canonical_audit_sha256':sha(caudit),'module_sha256':sha(module),'counts':read(A/'author-validation.json')['counts'],'bound_files':bound,'external_inputs':inputs,'independent_apparatus_approval':False,'mounted_browser_approval':False,'publication_approval':False,'training_approval':False}
save('package-freeze.json',freeze)
print(json.dumps({'freeze_sha256':sha(A/'package-freeze.json'),'module_sha256':sha(module),'bound_files':len(bound),'external_inputs':len(inputs),'checks':len(checks)+426,'scenes':21,'typed_fields':170}))
