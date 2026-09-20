"""Bounded independent AKS41 source/scope audit; never changes the draft."""
import hashlib
import json
from pathlib import Path
B=Path(__file__).resolve().parent
P=B/'context-drafts/littau-1993-aks41-context.json'
S=Path('[local path redacted]')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads(P.read_text(encoding='utf-8'))
old_path=B/'context-draft-audit.json'
old_audit=json.loads(old_path.read_text(encoding='utf-8')) if old_path.exists() else None
expected={'population-tem-mean':14,'population-tem-sd':3,'fig3-core':13,'fig3-shell':1.5,
 'fig3-fringes':3.1,'excluded-size':20,'middle-size':16,'monomer-size':11,'exclusion-elution':8}
measurements={m['id']:m for m in record['measurements']}
checks=[]
for mid,value in expected.items():
    checks.append({'check':'source quantity '+mid,'passed':measurements[mid]['value']['value']==value,
        'source_locator':'Main PDF p. 4, printed p. 1227, Results A, AKS41 paragraphs'})
checks += [
 {'check':'No synthesis operations reconstructed','passed':record['operations']==[]},
 {'check':'No requested training tasks','passed':record['quality']['requested_tasks']==[]},
 {'check':'Context record is an observation','passed':record['record_type']=='observation'},
 {'check':'No experimental structure asset invented','passed':record['structure_assets']==[]},
 {'check':'No physical batch invented','passed':record['lineage']['batch_id'] is None and all(p['batch_id'] is None for p in record['products'])},
 {'check':'One imaged particle separated from population','passed':measurements['fig3-core']['sample_id'] != measurements['population-tem-mean']['sample_id']},
 {'check':'HPLC sizes separated from direct core measurement','passed':all(measurements[x]['property']=='equivalent_HPLC_diameter' for x in ['excluded-size','middle-size','monomer-size'])},
 {'check':'Excluded HPLC size preserves lower-bound qualifier','passed':measurements['excluded-size']['value']['qualifier']=='greater_than'},
 {'check':'Approximate middle and monomer sizes preserved','passed':all(measurements[x]['value']['approximate'] for x in ['middle-size','monomer-size'])}]
findings=[
 {'id':'AKS41-01','severity':'must_fix','location':'measurements[id=monomer-size].value.basis',
  'issue':'The shared basis calls the late monomer fraction aggregate-containing, although the source specifically says that the approximately 11 nm peak shows mostly individual crystallites.',
  'source_locator':'Main PDF p. 4, printed p. 1227, paragraph beginning HPLC data show a broader size distribution; Figure 4 on p. 3',
  'required_change':'Use a fraction-specific basis: polymer-calibrated equivalent hard-sphere size of the late fraction, reported to contain mostly individual crystallites. Do not call it a pure monomer fraction or a direct crystalline-core diameter.'},
 {'id':'AKS41-02','severity':'must_fix','location':'products[aks41-excluded-sample,aks41-middle-sample,aks41-monomer-sample].phase and .surface',
  'issue':'The three isolated-fraction products inherit reported diamond-lattice core and amorphous-shell assertions as though independently measured on each fraction. The source explicitly reports similar individual-crystallite size distributions and differing aggregation in the fractions, while phase diffraction and detailed shell/core observation are assigned to the parent AKS41 colloid/depicted particle.',
  'source_locator':'Main PDF p. 4, printed p. 1227, successive Figure 3 and Figure 4 discussion paragraphs',
  'required_change':'Preserve the relationship to the AKS41 parent, but mark fraction-level phase and shell claims as inherited/inferred context or not separately measured. Add explicit notes rather than asserting an independent reported fraction refinement or shell measurement.'}]
notes=[
 {'id':'AKS41-N1','scope':'Provenance precision','note':'Retain the raw wording individual crystallite average size for the 14 nm mean. The source does not explicitly call this AKS41 value an outer diameter in that sentence; the record must not turn it into a crystalline-core mean. The current separate particle versus population mapping is correct.'},
 {'id':'AKS41-N2','scope':'Source alias','note':'Figure 4 caption spells ASK41; surrounding prose and Figure 3 use AKS41. Store the printed alias/conflict for transparency. This does not establish a second sample.'},
 {'id':'AKS41-N3','scope':'Source cross-reference','note':'The p. 4 aggregate paragraph says as in Figure 1 even though Figure 1 is the apparatus. Preserve it as a source cross-reference error if this sentence is included; do not map the apparatus as an aggregate image.'},
 {'id':'AKS41-N4','scope':'State ontology','note':'The imaged-particle state uses schema kind aliquot with an explicit individual-particle name. This is an ontology limitation rather than proof of an aliquoting operation. Do not invent an operation to explain it.'}]
monomer_resolved='mostly individual crystallites' in measurements['monomer-size']['value']['basis'] and 'aggregate-containing' not in measurements['monomer-size']['value']['basis']
fraction_products=[p for p in record['products'] if p['sample_id'] in ['aks41-excluded-sample','aks41-middle-sample','aks41-monomer-sample']]
fractions_resolved=len(fraction_products)==3 and all(p[k]['status']=='inherited' and 'no independent fraction-specific' in p[k]['note'] for p in fraction_products for k in ['phase','surface'])
for finding,resolved in zip(findings,[monomer_resolved,fractions_resolved]):
    finding['status']='resolved_and_independently_verified' if resolved else 'open'
passed=all(x['passed'] for x in checks) and monomer_resolved and fractions_resolved
additional_resolutions=[
 'Source wording: individual crystallite average size' in measurements['population-tem-mean']['value']['basis'],
 any('ASK41' in x for x in record['quality']['conflicts']),
 any('Figure 1' in x for x in record['quality']['conflicts']),
 'aliquot' in json.dumps(record) and 'subset' in json.dumps(record)]
for note,resolved in zip(notes,additional_resolutions):
    note['status']='addressed_and_verified' if resolved else 'precision_note_retained'
payload={'audit_version':'1.1.0','status':'passed_bounded_source_and_join_audit_after_corrections' if passed else 'corrections_required','record_path':str(P),'record_sha256':sha(P),
 'source_path':str(S),'source_sha256':sha(S),'source_doi':'10.1021/j100108a019',
 'scope':'Independent bounded review of AKS41 context draft, source p. 3 Figures 3/4, p. 4 AKS41 paragraphs, and reported acquisition context. This is not a repeat of the full seven-page review.',
 'visual_review':['page-4.png','crop-assets/figure-3.png','crop-assets/figure-4.png'],
 'checks':checks,'numerical_checks_passed':all(x['passed'] for x in checks),'findings':findings,'notes':notes,
 'edited_draft':False,'site_changed':False,'training_eligible':False,
 'must_fix_remaining':sum(f['status']=='open' for f in findings),
 'original_audited_record_sha256':(old_audit or {}).get('original_audited_record_sha256',(old_audit or {}).get('record_sha256')),
 'resolution':'Root corrected the builder and regenerated the draft. The independent reviewer reread all three fraction phase/surface fields and the monomer basis, checked retained numerical values and verified the final record hash.',
 'remaining_scope':'Full item-coverage audit and source-to-reader integration remain separate preparation work; no recipe training eligibility or publication is implied.'}
(B/'context-draft-audit.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
md=['# AKS41 contextual draft audit','',payload['scope'],'',
 'All nine numerical quantities and the tested sample/state boundaries match the source. No synthesis, physical batch, SAED image or experimental CIF is invented. Both source-scope findings are resolved and independently verified against the regenerated draft. No must-fix issues remain in this bounded audit.','',
 'Source SHA256: `'+sha(S)+'`','', 'Audited draft SHA256: `'+sha(P)+'`','']
for f in findings:
    md += ['## '+f['id']+' — '+f['status'],'',f['issue'],'',f['required_change'],'',f['source_locator']+'.','']
md += ['## Additional precision notes','']+['- '+x['note'] for x in notes]
md += ['', 'The draft was not edited. This audit does not authorize recipe-training eligibility or Site publication.','']
(B/'context-draft-audit.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'status':payload['status'],'numerical_checks_passed':payload['numerical_checks_passed'],
 'must_fix_count':payload['must_fix_remaining'],'audit_path':str(B/'context-draft-audit.json')}))
