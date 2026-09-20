"""Private bounded source-to-draft audit; reads canonical drafts without editing them."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

B=Path(__file__).resolve().parent
paths=sorted((B/'canonical-drafts').glob('*.json'))
snapshots={p.name:p.read_bytes() for p in paths}
records={r['record_id']:r for r in [json.loads(b) for b in snapshots.values()]}
r100=records['heath-1996-ge-100nm-wells']
r150=records['heath-1996-ge-150nm-wells']
char=records['heath-1996-ge-characterization']
pilot=records['heath-1996-ge-unpatterned-growth-context']
def op(r,id):return next(x for x in r['operations'] if x['id']==id)
def m(r,id):return next(x for x in r['measurements'] if x['id']==id)
def p(r,id):return next(x for x in r['products'] if x['sample_id']==id)
def cites(e,page):return any(f'Main PDF p. {page},' in x['locator'] for x in e)
def val(q):return (q['value'],q['minimum'],q['maximum'],q['unit'],q['qualifier'],q['approximate'])
checks=[]
def check(id,passed,description):checks.append({'id':id,'pass':bool(passed),'description':description})

check('pilot_scope', 'template' not in pilot['method'].lower() and 'mask' not in str(pilot['intended_target']['composition'].get('value')).lower() and 'Spatially positioned' not in str(pilot['intended_target']['morphology'].get('value')),
      'The unpatterned pilot no longer inherits template-confined method, patterned-mask target or spatially positioned array morphology.')
check('pilot_missingness',not any(x in ' '.join(pilot['quality']['missing_fields']) for x in ['PMMA molecular weight','Developer ratio basis','CF4/CHF3 flow ratio','Both well sizes occur']),
      'Pilot missingness is scoped to the incomplete unpatterned series rather than the patterned lithographic process.')
check('depth_sources',cites(m(r150,'template-depth')['evidence'],1) and cites(m(r150,'template-depth')['value']['evidence'],1) and cites(m(r100,'template-depth')['evidence'],2),
      '30 nm depth is traced to p1; 17 nm depth to p2; both remain approximate and template dimensions.')
check('characterization_context_sources',all(cites(op(char,'tem')['evidence'],i) for i in [2,3,5]) and all(cites(op(char,'afm')['evidence'],i) for i in [2,5]),
      'Shared TEM and AFM instrument/context claims carry p2 instrument, p3 TEM and p5 specimen/convolution evidence as applicable.')
check('etch_interpretation_source',cites(op(r100,'etch')['evidence'],5),
      'The 100 nm HF-exposes-base interpretation carries its p5 discussion locator, rather than only method pages.')
check('calibration_source',cites(m(r150,'close-distances')['evidence'],2) and cites(m(r150,'close-distances')['evidence'],4),
      'Three separations below 100 nm remain p4 values with the p2 well-center calibration context retained.')
check('100nm_phase_semantics',p(r100,'ge-islands')['phase'].get('value') is None,
      'The 100 nm phase remains unassigned; composition assignment from the shared cohort is not promoted into a phase value.')
expected={'stock_gas_flow':(90,None,None,'sccm','',False),'deposition_pressure':(None,1,2,'mTorr','',False),'growth_temperature':(600,None,None,'degC','',False),'exposure_duration':(5,None,None,'min','',False)}
check('shared_CVD_quantities',all(val(op(r,'grow')['parameters'][k])==v for r in [r100,r150] for k,v in expected.items()) and all('mixture' in op(r,'grow')['parameters']['stock_gas_flow']['basis'] for r in [r100,r150]),
      'Both template variants retain the same reported 10% GeH4/He mixture exposure: 90 sccm, 1–2 mTorr, 600 °C, 5.0 min, without pure-germane flow substitution.')
check('base_pressure_scope',all(val(op(r,'load')['parameters']['base_pressure'])==(5e-6,None,None,'Torr','less_than',False) for r in [r100,r150]),
      'Below 5×10^-6 Torr remains the base-pressure threshold, separate from deposition pressure.')
check('AFM_dimensions_and_bounds',val(m(r100,'fig6-height')['value'])[:4]==(1.4,None,None,'nm') and val(m(r100,'fig6-width')['value'])[:4]==(33,None,None,'nm') and m(r100,'first-bounds')['value']['status']=='author_derived' and m(r100,'second-bounds')['value']['status']=='author_derived' and m(r100,'first-bounds')['value']['maximum']==34 and m(r100,'second-bounds')['value']['maximum']==35,
      'Apparent AFM height/width remain separate from author-derived bounds and from exact crystal diameters.')
check('property_cohort',len(char['measurements'])==2 and all(x['sample_id']=='patterned-cohort' for x in char['measurements']) and m(char,'raman-ge-lo')['value']['value']==301 and m(char,'nir-ge-surface')['value']['value']==5890 and 'not a bandgap' in m(char,'nir-ge-surface')['value']['basis'],
      'Raman and near-IR observations remain shared-cohort measurements; the near-IR surface-state peak is not relabeled as a bandgap.')
check('pilot_nonrecipe_context',pilot['record_type']=='observation' and not pilot['operations'] and p(pilot,'pilot-cohort')['recipe_link']=='unresolved' and m(pilot,'incubation')['value']['qualifier']=='just_under' and m(pilot,'late-size')['value']['approximate'],
      'The incomplete pilot series stays an observation with unresolved recipe linkage, non-exact incubation and approximate size.')
check('no_training_or_atomic_structure_promotion',all(r['quality']['requested_tasks']==[] and not r['structure_assets'] for r in records.values()),
      'Requested training tasks remain empty and no measured atomic-structure asset is asserted.')
stable=all(p.read_bytes()==snapshots[p.name] for p in paths)
findings=[{'id':x['id'],'severity':'must_fix','description':x['description']} for x in checks if not x['pass']]
report={'status':'passed_bounded_scientific_draft_audit' if not findings and stable else 'findings_or_drafts_changed','audited_at_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':'016e78158e4f83837f13b1412f3e08d5f7134724a3758d14468a41ff926e156a','scope':'Independent six-page source review followed by read-only audit of all four current private draft operation/stock/quantity/product/measurement fields and sample joins. This is not a source-to-view, SI, image-crop, frontend or publication audit.','reviewed_hashes':{p:hashlib.sha256(b).hexdigest() for p,b in snapshots.items()},'record_count':len(records),'measurement_count':sum(len(r['measurements']) for r in records.values()),'drafts_stable_during_check':stable,'checks':checks,'outstanding_findings':findings,'manual_disposition':['All four records were compared with the source text and six visually inspected main pages; targeted checks here capture high-impact fields and finding closure, not every manually inspected leaf.','Two template variants share wafer/exposure; neither is an independent run count. Spectroscopy is cohort-level; 100 nm AFM and 150 nm TEM/statistical identities stay distinct.','Narrative details including 10 nm over-etch, PMMA opening-size conflict, model equations, pseudo-time reconstruction, 40 nm size ambiguity and citation-only context require reader-ledger mapping; their omission from measured targets is appropriate.','Figure 2 has unresolved 100/150 nm identity. Figure 5 is author-model-derived. No missing Raman/IR spectrum, XRD, SAED or measured atom coordinates may be synthesized.'],'remaining':['Matching SI remains unverified.','Final source-to-reader coverage, original figure assets and actual browser presentation are separate pending integration checks.','Review/publishing state changes and training eligibility are controlled by root, not by this audit.']}
(B/'canonical-records-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(B/'canonical-records-audit.md').write_text('# Heath 1996 bounded canonical-record audit\n\n'+report['scope']+'\n\nStatus: '+report['status']+'\n\n'+'\n'.join('- '+('PASS' if x['pass'] else 'MUST FIX')+': '+x['description'] for x in checks)+'\n\n'+'\n'.join('- '+x for x in report['remaining'])+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'findings':findings,'measurement_count':report['measurement_count'],'stable':stable},indent=2))
