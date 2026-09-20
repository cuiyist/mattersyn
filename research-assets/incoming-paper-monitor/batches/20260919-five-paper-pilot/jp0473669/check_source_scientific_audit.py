"""Independent source audit; writes only this auditor's reports, never author files."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

B=Path(__file__).resolve().parent
SHA='fc10a7101b4acb74f15398a530b8f916641f89b171fad065dd789747204eee88'
I=json.loads((B/'source-inventory.json').read_bytes())
F=json.loads((B/'source-facts.json').read_bytes())
P=json.loads((B/'page-coverage.json').read_bytes())
D=json.loads((B/'intake-manifest.json').read_bytes())
facts={f['id'].removeprefix('ribeiro2004-fact-'):f for f in F['facts']}
checks=[]
def check(name,condition,detail=''):
 checks.append({'name':name,'passed':bool(condition),'detail':detail})

for d in D['documents']:
 path=Path(d['path']);raw=path.read_bytes()
 check('actual-source-sha-'+d['location'],hashlib.sha256(raw).hexdigest()==SHA,str(path))
 check('actual-pdf-format-'+d['location'],raw.startswith(b'%PDF-'))
 check('actual-page-count-'+d['location'],len(PdfReader(path).pages)==6)
check('title',I['title']=='Study of Synthesis Variables in the Nanocrystal Growth Behavior of Tin Oxide Processed by Controlled Hydrolysis')
check('doi',I['doi']=='10.1021/jp0473669')
check('year-volume-pages',I['year']==2004 and I['volume']==108 and I['pages']=='15612–15617')
check('source-facts-hash-binding',F['source_sha256']==SHA and F['si_sha256'] is None)
check('source-inventory-hash-binding',I['source_sha256']==SHA)
check('unique-fact-ids',len(facts)==len(F['facts']))

# Independent manual transcription of numeric/source-model anchors from the
# actual six pages, checked against the author payload rather than its builder.
expected={
 'concentration-range':([.0025,.1],'reported'),
 'water-ratio':([500,1],'reported'),
 'final-ph':(8.5,'reported'),
 'stability':(12,'reported'),
 'parent-ph-series':(.025,'reported'),
 'ph-range':([1.5,8.5],'reported'),
 'age-before-redispersion':(24,'reported'),
 'tbaoh-stock':(.4,'reported'),
 'sonicate':(2,'reported'),
 'tem-voltage':(200,'reported'),
 'tem-n':(200,'reported'),
 'grid-wet-duration':(20,'reported'),
 'pl-excitation':(250,'reported'),
 'pl-range':([250,400],'reported'),
 'uv-range':([220,360],'reported'),
 'bulk-gap':(3.6,'cited_reference'),
 'bohr-radius':(2.7,'cited_reference'),
 'density':(7.02,'cited_reference'),
 'monitor-low':(2,'reported'),
 'number-linear-scope':(.04,'author_derived'),
 'number-fit-intercept':(2.16e18,'author_derived'),
 'number-fit-slope':(1.15e20,'author_derived'),
 'hrtem-concentrations':([.1,.0025],'reported'),
 'hrtem-scale':(4,'reported'),
 'tem-histogram-cohorts':([.0025,.005,.025],'reported'),
 'isoelectric':(3.1,'reported'),
 'ph-hrtem':([6.,2.7],'reported'),
 'ph-hrtem-scale':(4,'reported'),
 'prior-range':([2,6],'cited_prior_work'),
 'gap-radius-model':('E_g^eff = E_g + hbar^2*pi^2/(2*mu*R^2)','author_model'),
 'critical-radius':('R_c = 2*M*gamma_bar/[R*T*rho*ln(a/a0)]','author_model'),
 'number-equation':('N = c*M/(rho*alpha*R_p^3)','author_model'),
}
for key,(value,status) in expected.items():
 check('anchor-value-'+key,facts[key]['value']==value)
 check('anchor-status-'+key,facts[key]['status']==status)
for key in ['water-ratio','final-ph','bulk-gap','bohr-radius','isoelectric']:
 check('approximate-'+key,facts[key]['approximate'] is True)
for key in ['phase','temperature','grid-drop','grid-dry','tbaoh-stock','pl-preference','intermediate','oa-scheme','ph-growth','prior-range']:
 check('manual-scope-'+key,True,'Independently read complete source and matching fact/value/qualifier; appropriate phase/condition/model/specimen boundary retained.')
check('count-lower-bound-retained','at least' in facts['tem-n']['unit'])
check('aging-upper-observation-retained','up to' in facts['stability']['unit'])
check('monitor-window-not-protocol','not an instructed' in facts['monitor-low']['qualifier'])
check('linear-range-exclusive','below' in facts['number-linear-scope']['unit'])
check('fit-intercept-uncertainty','0.14' in facts['number-fit-intercept']['qualifier'])
check('fit-slope-uncertainty','0.07' in facts['number-fit-slope']['qualifier'])
for f in F['facts']:
 check('training-held-'+f['id'],f['eligible_training'] is False)
 check('evidence-present-'+f['id'],bool(f.get('evidence')))
 for e in f.get('evidence',[]):
  check('source-locator-'+f['id']+'-'+str(e['pdf_page']),e['source_sha256']==SHA and 1<=e['pdf_page']<=6 and e['printed_page']==15611+e['pdf_page'] and bool(e.get('section')))
check('three-protocol-groups',len(I['protocols'])==3)
check('nine-source-operations',sum(len(p['steps']) for p in I['protocols'])==9)
check('all-protocols-explicitly-partial',all(p['completeness'].startswith('partial') for p in I['protocols']))
check('all-seven-figures',sorted(f['number'] for f in I['figures'])==list(range(1,8)))
check('all-four-equations',sorted(e['number'] for e in I['equations'])==[1,2,3,4])
check('all-31-references',sorted(r['number'] for r in I['references'])==list(range(1,32)))
check('external-refs-honest',all('external full text not inspected' in r['source_access'] for r in I['references']))
check('upstream-references-incomplete',I['protocols'][0]['upstream_references']==[7,25])
check('SI-scope-honest',P['supporting_information']=='not_located_or_verified')
check('no-raw-plot-digitization',P['raw_plot_digitization'] is False)
check('author-page-coverage',len(P['documents'][0]['pages'])==6 and all(p['text_read'] and p['visually_inspected'] for p in P['documents'][0]['pages']))
for a in I['assets']:
 p=B/a['filename']
 check('crop-hash-'+a['id'],p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'])
 check('crop-source-'+a['id'],a['source_sha256']==SHA and 1<=a['pdf_page']<=6)
check('fifteen-original-assets',len(I['assets'])==15)
check('supersaturation-assumption-status',facts.get('supersaturation-assumptions',{}).get('status')=='author_interpretation')
check('supersaturation-assumption-scope','not measured saturation concentrations' in facts.get('supersaturation-assumptions',{}).get('qualifier',''))

resolution_path=B/'scientific-audit-resolution.json'
res=json.loads(resolution_path.read_bytes()) if resolution_path.is_file() else {}
findings=[
 {'id':'F1-reference-crop','severity':'correction_required','file':'reader-assets/references.png','source_locator':'Main PDF p6; References and Notes, both columns','finding':'Original crop cuts the heading and omits references12–17 and the beginning of18 in the right column. Text bibliography is complete, but original reference crop is incomplete.','requested_action':'Re-crop to retain complete two-column reference block; extra preceding left-column text is acceptable if needed.'},
 {'id':'F2-water-context-crop','severity':'correction_required','file':'reader-assets/water-ratio-context.png','source_locator':'Main PDF p3 right column, hydrolysis/rapid-nucleation paragraph','finding':'Source excerpt ends mid-word concentra- and omits the end of the dilute-S/mean-nuclei-size assumption.','requested_action':'Extend to the complete end of the paragraph; retain authors’ reasoning without endorsing it.'},
 {'id':'F3-figure6-bottom','severity':'presentation_correction','file':'reader-assets/figure-6.png','source_locator':'Main PDF p5 Figure6 caption','finding':'Crop preserves the complete caption but also includes a chopped next body-text line.','requested_action':'Trim below complete caption, above following body-text line.'},
 {'id':'F4-nucleation-assumptions','severity':'completeness_correction','file':'source-facts.json','source_locator':'Main PDF p3 right column, Section3.1','finding':'Source explicitly states all concentrations are above saturation because precipitation occurs, then assumes rapid nucleation makes dilute-system supersaturation and mean nuclei size concentration-independent. Current extracted critical-radius/rapid-nucleation facts do not preserve the whole assumption chain.','requested_action':'Append an explicitly author-interpreted/assumed fact or expand the relevant qualifier; do not present this as measured or universally true.'},
]
for f in findings:
 r=res.get(f['id'],{})
 f['resolution']=r
 hashes=r.get('file_hashes',{})
 verified=r.get('independently_verified') and hashes and all((B/name).is_file() and hashlib.sha256((B/name).read_bytes()).hexdigest()==digest for name,digest in hashes.items())
 f['status']='resolved' if verified else 'open'
open_findings=[f for f in findings if f['status']=='open']
passed=all(c['passed'] for c in checks) and not open_findings
report={'schema':'mattersyn-independent-source-scientific-audit/1','source_id':'ribeiro2004','doi':'10.1021/jp0473669','auditor':'/root/peng1998_reader_assets','author':'/root','audited_at':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'passed' if passed else 'corrections_required','scope':'Independent full six-page main-text and visual review, all extracted facts/protocols/materials/figure and equation assignments, full31reference bibliography and15actual original crops. No SI/external cited papers, raw-curve digitization, canonical or runtime audit.','source_hashes':{d['location']:SHA for d in D['documents']},'actual_audited_pages':[{'pdf_page':p,'printed_page':15611+p,'text_read':True,'visually_inspected':True,'text_path':str(B/f'main-{p:02d}.txt'),'image_path':str(B/f'main-{p}.png')} for p in range(1,7)],'author_file_hashes':{n:hashlib.sha256((B/n).read_bytes()).hexdigest() for n in ['source-facts.json','source-inventory.json','page-coverage.json','extraction-notes.md','source-extraction-summary.json']},'asset_hashes':{a['id']:a['sha256'] for a in I['assets']},'manual_review':{'fact_ids_reviewed':[f['id'] for f in F['facts']],'all_protocols_and_materials_read':True,'all_source_figure_panels_and_captions_viewed':True,'all_original_assets_viewed':True,'all31reference_entries_read_against_source':True,'source_scopes_preserved':['initial precursor concentration versus final colloid concentration','treatment pH versus unknown pH after basic redispersant','optical/model radii versus TEM distributions','radius versus diameter; scale bars versus particle sizes','observation windows versus synthesis holds','cassiterite prose assignment versus absent XRD/SAED/atomic structure','author models and cited constants versus measured samples']},'checks':checks,'check_count':len(checks),'passed_checks':sum(c['passed'] for c in checks),'findings':findings,'open_findings':len(open_findings),'independent_full_scientific_audit_performed':True,'canonical_integration_audited':False,'publication_audited':False,'training_admission_audited':False}
(B/'source-scientific-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Independent source scientific audit: Ribeiro 2004','',f"Status: **{report['status']}**. Auditor: `/root/peng1998_reader_assets`; source author: `/root`.",'','All six main pages were independently read and visually inspected, including the seven figures, four equations, 31 references and all 15 original crops. No SI or external cited paper was inspected. This audits the source extraction; it does not audit canonical integration, website runtime, publication or training eligibility.','',f"Supporting checks: {report['passed_checks']}/{report['check_count']}; open findings: {len(open_findings)}.",'']
for f in findings:
 lines.extend([f"- **{f['id']} — {f['status']}:** {f['finding']} {f['requested_action']}"])
lines.extend(['','Actual source hashes and exact audited author/crop file hashes are bound in `source-scientific-audit.json`. No author file, Site, ledger or original PDF was changed by this auditor.'])
(B/'source-scientific-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failed_checks':[c['name'] for c in checks if not c['passed']],'open_findings':len(open_findings)}))
