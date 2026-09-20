"""Record completed SI and average-model audits without closing Heo or publishing it."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
B=Path(__file__).resolve().parent;H=B/'jp0219348'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def bind(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
now=datetime.now(timezone.utc).isoformat()
agg=H/'si-complete-candidate';structure=H/'structure-candidate'
assert bind(agg/'independent-audit.json')['sha256']=='e5f0cb753560f9a1561b0b55b06bb647b16a315cdd8b4a51fb9b7563591ad741'
assert bind(structure/'independent-audit-addendum.json')['sha256']=='b570d03f43e1a1f1ef779d257ae1d9a550aff4a3dd0da32786039b6c8bc8eb5e'
data=read(agg/'all-reflections.json');c=data['counts'];progress=read(H/'si-numerical-progress-index.json')
progress.update({'at':now,'transcribed_and_independently_audited_pages':list(range(1,15)),
 'chunks':data['chunk_audits'],'remaining_untranscribed_and_unaudited_pages':[],
 'remaining_row_count':0,'complete_SI_numerical_review':True,'complete_SI_numeric_resolution':False,
 'rows':c['rows'],'numeric_cells':c['numeric_positions'],'resolved_numeric_values':c['resolved_numeric_values'],
 'markers':c['markers'],'negative_Fobs2':c['definite_negative_Fobs2'],'zero_Fobs2':c['zero_Fobs2'],
 'uncertain_signs':c['unresolved_sign_cells'],'aggregate':bind(agg/'all-reflections.json'),
 'aggregate_freeze':bind(agg/'package-freeze.json'),'aggregate_audit':bind(agg/'independent-audit.json'),
 'progress_note':'All 14 pages and 1,209 rows transcribed and independently audited. Two source-unreadable signs remain null with both candidates. Combined transport audited separately. No ordered crystal or exact recipe pair is created.'})
write(H/'si-numerical-progress-index.json',progress)
checkpoint={'schema':'mattersyn-heo-source-stage-checkpoint/1','at':now,'source_id':'heo2003',
 'status':'source_evidence_audits_passed_with_explicit_gaps_canonical_visual_integration_pending',
 'source_generation':2,'main_pages_read':9,'si_pages_read':14,'typed_source_facts':114,
 'si_numerical_progress':progress,'main_audit':bind(H/'source-scientific-audit.json'),
 'average_model_freeze':bind(structure/'package-freeze.json'),
 'average_model_initial_audit':bind(structure/'independent-audit.json'),
 'average_model_corrected_label_audit':bind(structure/'independent-audit-addendum.json'),
 'canonical_mapping_plan':bind(H/'canonical-mapping-plan.json'),
 'unresolved':['Two signs in the SI reflection table.','Three synthesis-condition conflicts between prose and Table 1.',
 'Nominal framework composition differs from the statistical Si/Al average refinement.',
 'One Table 3 angle differs from printed-coordinate geometry by 2.27 reported ESDs.',
 'Literal O2/O3/O4 ADPs have exact site-symmetry inconsistencies; geometric CIF omits all ADPs.',
 'No unique ordered charge-balanced microscopic model or exact structure-recipe pair.'],
 'published':False,'canonical_records_promoted':False,'reader_or_browser_audit_completed':False,
 'next_steps':['Complete and independently audit canonical record proposal.','Complete source-qualified molecule, apparatus and crystal/characterization reader views.',
 'Independent visual and reader checks, integration, browser QA and verified GitHub Pages publication.']}
write(H/'comprehensive-source-checkpoint.json',checkpoint)
milestones={
 'read':{'status':'complete','evidence':[str(H/'page-coverage.json'),str(H/'source-scientific-audit.json'),str(agg/'independent-audit.json')],
 'note':'All supplied main/SI pages read within recorded scopes. Seven numerical SI chunks and combined table independently audited; two signs remain explicitly unresolved.'},
 'extract':{'status':'partial','evidence':[str(H/'source-facts.json'),str(H/'main-tables.json'),str(agg/'all-reflections.json'),str(H/'canonical-mapping-plan.json')],
 'note':'Source facts, all main tables and complete SI table extracted. Canonical record proposal and reader mapping still in preparation.'},
 'audit':{'status':'partial','evidence':[str(H/'source-scientific-audit.json'),str(agg/'independent-audit.json'),str(structure/'independent-audit-addendum.json')],
 'note':'Main source, complete SI and average geometry/occupancy audits passed their exact scopes. Canonical, visual, final reader and publication checks remain.'},
 'integrate':{'status':'pending','evidence':[],'note':'Private preparation only; no Heo records in the live website.'},
 'publish':{'status':'pending','evidence':[],'note':'Heo publication remains pending; live dataset stays 0.23.0.'}}
write(H/'source-stage-milestones.json',milestones)
wf=read(B/'workflow-state.json');wf['updated_at']=now
wf['status']='Gu_Nagasaki_Ribeiro_Norberg_published;Heo_full_SI_and_average_model_audited_canonical_visual_pending'
for p in wf['papers']:
 if p['group_id']=='10.1021_jp0219348':
  p.update({'full_extraction':'source_evidence_complete_with_gaps_canonical_pending','full_scientific_audit':'source_and_SI_audits_passed_canonical_visual_pending',
    'si_numerical_progress':progress,'checkpoint':str(H/'comprehensive-source-checkpoint.json'),'publication':'pending'})
write(B/'workflow-state.json',wf)
print(json.dumps({'checkpoint':str(H/'comprehensive-source-checkpoint.json'),'SI_rows':c['rows'],'Heo_published':False}))
