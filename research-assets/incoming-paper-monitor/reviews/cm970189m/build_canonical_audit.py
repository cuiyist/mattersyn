"""Independent private source-to-record audit, using the separately transcribed source inventory."""
from pathlib import Path
import json,hashlib,re
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records={r['record_id']:r for r in [read(p) for p in sorted((B/'canonical-drafts').glob('*.json'))]}
prefix='veinot-1997-'
def R(k):return records[prefix+k]
src=read(B/'source-audit.json');U={u['id']:u for u in src['units']}
char=R('characterization');MEAS={m['id']:m for m in char['measurements']}
checks=[]
def ck(name,passed,detail=''):checks.append(dict(name=name,passed=bool(passed),detail=detail))
def pos(q):return (q.get('minimum'),q.get('maximum')) if q.get('value') is None else q['value']
def expected_positions(signals):
    result=[]
    for seg in signals.split(';'):
        s=seg.split('(')[0].strip().replace('–','-')
        for chunk in re.split(r',|and',s):
            vals=re.findall(r'\d+(?:\.\d+)?',chunk)
            if len(vals)==1:result.append(float(vals[0]))
            elif len(vals)==2:result.append(tuple(sorted(map(float,vals))))
    return result
for c in ['1','2a','2b','2c','2d','2e','3a','3b','3c','3d','3e']:
    expected=expected_positions(U['table1-'+c]['nmr']['signals'])
    actual=[pos(m['value']) for m in char['measurements'] if re.fullmatch(re.escape(c)+r'-nmr-\d+',m['id'])]
    ck('Table1 '+c+' all NMR positions/ranges',expected==actual,f'{len(expected)} independently transcribed source positions')
for c in ['1','2a','2b','2c','2d','2e']:
    expected=expected_positions(U['table2-'+c]['signals'])
    actual=[pos(m['value']) for m in char['measurements'] if m['id'].startswith(c+'-ir-')]
    ck('Table2 '+c+' all IR positions/ranges',expected==actual,f'{len(expected)} independently transcribed source positions')
    u=U['table3-'+c]
    ck('Table3 '+c+' TEM diameter',MEAS[c+'-tem-diameter']['value']['value']==u['TEM_diameter_angstrom'])
    ck('Table3 '+c+' author-derived diameter',MEAS[c+'-model-diameter']['value']['value']==u['author_calculated_diameter_angstrom'])
    if c!='2c':ck('Table3 '+c+' CdS optical wavelength',MEAS[c+'-absorption']['value']['value']==u['wavelength_nm'])
    else:ck('Table3 2c pyrene-only range',(MEAS[c+'-pyrene-absorption']['value']['minimum'],MEAS[c+'-pyrene-absorption']['value']['maximum'])==tuple(u['wavelength_nm']) and MEAS[c+'-model-diameter']['value']['status']=='not_reported')
for c in ['2a','2b','2c','2d','2e']:
    ck('Table1 '+c+' site conversion',MEAS[c+'-conversion']['value']['value']==U['table1-'+c]['yield_or_conversion_percent'] and MEAS[c+'-conversion']['value']['status']=='author_derived')
for c in ['3a','3b','3c','3d','3e']:
    ck('Table1 '+c+' molecular yield/time',MEAS[c+'-yield']['value']['value']==U['table1-'+c]['yield_or_conversion_percent'] and MEAS[c+'-reaction-time']['value']['value']==U['table1-'+c]['reaction_time']['value'])

def O(k,op):return next(o for o in R(k)['operations'] if o['id']==op)
def M(k,mid):return next(m for m in R(k)['materials'] if m['id']==mid)
ck('21 scoped records',len(records)==21)
ck('QDOH formation temperature remains unreported',O('qdoh','stir')['parameters']['temperature']['value'] is None)
ck('QDOH printed precursor masses/amounts retained',[(M('qdoh',m)['quantities']['mass']['value'],M('qdoh',m)['quantities']['amount']['value']) for m in ['na2s','hpt','cd-acetate']]==[(2.53,11),(4.93,39),(5.05,29)])
ck('QDOH 12h and isolated ligand-bearing mass2.23g',O('qdoh','stir')['parameters']['duration']['value']==12 and R('qdoh')['measurements'][0]['value']['value']==2.23)
ck('Only 2a has reported300mg/170mg charges',M('ester-2a','qdoh')['quantities']['mass']['value']==300 and M('ester-2a','3a')['quantities']['mass']['value']==170 and all(M('ester-2'+x,'qdoh')['quantities']['mass']['value'] is None and M('ester-2'+x,'3'+x)['quantities']['mass']['value'] is None for x in 'bcde'))
ck('Ice bath does not become0C sampletemperature',all(O('ester-2'+x,'cool')['parameters']['temperature']['value'] is None for x in 'abcde'))
ck('Pyrene upstream1g/4.1mmol/20mL and80C3h',M('pyrenecarbonyl-chloride','pyrene-acid')['quantities']['mass']['value']==1 and M('pyrenecarbonyl-chloride','pyrene-acid')['quantities']['amount']['value']==4.1 and M('pyrenecarbonyl-chloride','socl2')['quantities']['volume']['value']==20 and O('pyrenecarbonyl-chloride','heat')['parameters']['temperature']['value']==80 and O('pyrenecarbonyl-chloride','heat')['parameters']['duration']['value']==3)
ck('Acid chloride retains filtrate',O('pyrenecarbonyl-chloride','filter')['retained_fraction']=='filtrate')
ck('Acyl chloride3c–e2.05equiv/50%basis unresolved/100C',all(M('acylimidazole-3'+x,'imidazole')['quantities']['equivalents']['value']==2.05 and O('acylimidazole-3'+x,'heat')['parameters']['temperature']['value']==100 and R('acylimidazole-3'+x)['stocks'][0]['concentrations']['reported_percentage']['value']==50 for x in 'cde'))
ck('3b15/30 conflict retained as source labelled quantities',O('acylimidazole-3b','react')['parameters']['duration']['value']==30 and O('acylimidazole-3b','react')['parameters']['table1_reaction_duration']['value']==15)
ck('TEM source quantities and calibration',M('tem','cluster')['quantities']['mass']['value']==2.5 and M('tem','chloroform')['quantities']['specimen_solvent_volume']['value']==3 and O('tem','deposit')['parameters']['drops']['value']==3 and O('tem','calibrate')['parameters']['line_density']['value']==21600 and O('tem','image')['parameters']['figure6_magnification']['value']==290000)
ck('TEM centrifugation retained fraction unspecified',O('tem','centrifuge')['retained_fraction'] is None)
ck('QDOH±7 uncertainty not silently madeSD',MEAS['1-tem-uncertainty']['value']['value']==7 and 'not defined' in MEAS['1-tem-uncertainty']['value']['basis'])
ck('20/34thiol-derived sulfur conflict retained',MEAS['1-thiol-sulfur-20']['value']['value']==20 and MEAS['1-thiol-sulfur-34']['value']['value']==34)
ck('295/305 versus390 spectral conflict retained',MEAS['1-methods-edge']['value']['value']==295 and MEAS['1-methods-shoulder']['value']['value']==305 and MEAS['1-absorption']['value']['value']==390)
ck('Prolonged exposure is strict>12h context',O('prolonged-degradation','exposure')['parameters']['duration_threshold']['value']==12 and 'greater than' in O('prolonged-degradation','exposure')['parameters']['duration_threshold']['qualifier'])
for rid,r in records.items():
    ck(rid+' disabled training and unreviewed',r['quality']['requested_tasks']==[] and r['quality']['review_status']=='imported_unreviewed')
    ck(rid+' no exact atomic labels',not any(a.get('eligible_as_measured_label') for a in r['structure_assets']))
    ck(rid+' no invented batch identity',r['lineage']['batch_id'] is None and all(p['batch_id'] is None for p in r['products']))

findings=[]
def finding(id,title,detail,resolved,refs,records_affected):
    findings.append(dict(id=id,title=title,detail=detail,status='resolved' if resolved else 'open',source_units=refs,record_ids=[prefix+k for k in records_affected]))
organic=['pyrenecarbonyl-chloride']+['acylimidazole-3'+x for x in 'abcde']
finding('F01','Molecular precursor intended composition','The shared CdS hub context must not turn a molecular precursor synthesis into a CdS synthesis target.',all(R(k)['intended_target']['composition']['value']==R(k)['products'][0]['composition']['value'] and R(k)['intended_target']['composition']['value']!='CdS' for k in organic),['procedure-06','procedure-08','procedure-10'],organic)
direct=R('direct-acylchloride-degradation')
finding('F02','Direct acyl-chloride failure locator','The actually performed initial failures occur onp3; p2alone only reaches the earlier general-stability discussion.',all(any('p. 3,'in e['locator'] for e in obj['evidence']) for obj in direct['materials']+direct['operations']),['procedure-19'],['direct-acylchloride-degradation'])
finding('F03','Optical compound-label typo','The19Angstrom optical size is2d,not3d.',not any('Table33d optical' in s for s in char['quality']['conflicts']),['table3-2d'],['characterization'])
finding('F04','Unspecified filter-paper chemistry','The source gives filter paper but not its composition; do not assert cellulose.',M('tem','filter-paper')['formula'] in [None,'','Unspecified'],['chemical-19','procedure-18'],['tem'])
finding('F05','Inherited ester framework statuses','Finite common-procedure24h drying and environment of2b–e must retain inherited status; Table1per-variant30min remains reported.',all(O('ester-2'+x,'dry')['parameters']['duration']['status']=='inherited' and O('ester-2'+x,'react')['parameters']['duration']['status']=='reported' for x in 'bcde'),['procedure-13','procedure-14'],['ester-2'+x for x in 'bcde'])
finding('F06','Molecular3e NMR specimen lineage','Figure2 describes3e; its analytical input needs a separate preparation/acquisition branch rather than only prose attached to CdSspecimens.',any('3e' in o['inputs'] for o in R('nmr')['operations']),['figure-2','method-02'],['nmr'])
finding('F07','Molecular product structure provenance','AddScheme1/compound-structure evidence for molecular product identities.',all(any('p. 3,'in e['locator'] for e in R('acylimidazole-3'+x)['products'][0]['composition']['evidence']) for x in 'abcde'),['scheme-1'],['acylimidazole-3'+x for x in 'abcde'])
finding('F08','Unidentified direct-degradation product','Source says the cluster was destroyed but doesnot identify a resulting CdSphase/composition. Keep the product unresolved.',direct['products'][0]['composition']['value'] is None and direct['products'][0]['composition']['status']=='not_reported',['procedure-19'],['direct-acylchloride-degradation'])
finding('F09','Nonreactive-control outcome semantics','A deliberate nonreactive control is not an unsuccessful QDOHsynthesis training example. Preserve explicit qualitative no-reaction observation.',R('unfunctionalized-control')['quality']['experimental_outcome']=='not_established' and len(R('unfunctionalized-control')['measurements'])>0,['procedure-16'],['unfunctionalized-control'])

procedure_map={1:['qdoh'],2:['qdoh'],3:['qdoh'],4:['qdoh'],5:['characterization'],6:['pyrenecarbonyl-chloride'],7:['pyrenecarbonyl-chloride'],8:['acylimidazole-3a','acylimidazole-3b'],9:['acylimidazole-3a','acylimidazole-3b'],10:['acylimidazole-3c','acylimidazole-3d','acylimidazole-3e'],11:['acylimidazole-3c','acylimidazole-3d','acylimidazole-3e'],12:['ester-2a'],13:['ester-2'+x for x in 'abcde'],14:['ester-2'+x for x in 'bcde'],15:['nmr','characterization'],16:['unfunctionalized-control'],17:['prolonged-degradation'],18:['tem'],19:['direct-acylchloride-degradation']}
method_map={1:['ftir','characterization'],2:['nmr','characterization'],3:['uv-visible','characterization'],4:['tem','characterization'],5:['characterization'],6:['characterization']}
coverage=[]
for u in src['units']:
    cat=u['category'];ids=[];disposition='reader_context_required'
    if cat=='procedures_and_controls':ids=procedure_map[int(u['id'].split('-')[1])];disposition='canonical_and_reader_context'
    elif cat=='characterization_methods':ids=method_map[int(u['id'].split('-')[1])];disposition='canonical_and_reader_context'
    elif cat=='table_rows':ids=['characterization'];disposition='canonical_transcription'
    elif cat=='chemical_inventory':ids=['reagent-conditioning','qdoh','tem','nmr'];disposition='canonical_inventory_and_reader_context'
    elif cat=='observations_and_author_interpretations':ids=['characterization'];disposition='canonical_or_reader_context_by_claim'
    elif cat=='conflicts_and_semantic_hazards':ids=['characterization'];disposition='canonical_conflicts_and_reader_context'
    coverage.append(dict(source_unit_id=u['id'],category=cat,disposition=disposition,canonical_record_ids=[prefix+k for k in ids],note='References, author intuition, source figures, absence notes and unlinked comparative observations remain reader-context requirements; not new machine outcome labels.'))
errors=[c for c in checks if not c['passed']]
openfindings=[f for f in findings if f['status']=='open']
out=dict(schema_version='1.0',source_id='veinot1997',scope='All21private records compared with independently read six-page main and141-unit inventory. Source-to-canonical science/coverage audit; no reader rendering, SI verification or publication claim.',source_sha256=src['source_sha256'],status='passed' if not(errors or openfindings) else 'must_fix',record_count=len(records),measurement_count=sum(len(r['measurements']) for r in records.values()),operation_count=sum(len(r['operations']) for r in records.values()),record_hashes=[dict(record_id=rid,sha256=sha(B/'canonical-drafts'/(rid+'.json'))) for rid in records],source_audit_sha256=sha(B/'source-audit.json'),check_count=len(checks),checks=checks,findings=findings,open_findings=openfindings,failed_checks=errors,source_unit_coverage=coverage,manual_review=['Read full authoring builder and all generated record structures/typed values. Compared all independently transcribed NMR/IR/TEM/optical table values, quantities, source semantic qualifiers, molecular names/formulas, synthesis branches, preparation states and measurement scopes.','Reference-only surface-coverage comparators, chemical rationale and sparse qualitative observations may remain reader context. The presence of a canonical record does not establish measured atomistic structure, per-batch replicate linkage or full paper-to-reader integration.','Source-reported conflicts retained:5.05g/29mmol,20/34mol%,295/305/390nm,3b15/30min,3d anomalousmethyl,ImC4/C5,1010cm−1assignments,19–27Å narrative equality,1100Åvs6nmbar,and absentEq1.','Physical aliquots are not unified across NMR/IR/optical/TEM. Compound-class products remain general_context; temperatures/pressure/centrifuge settings absent from the source remain missing.'])
out['records']=[dict(record_id=x['record_id'],basename=x['record_id']+'.json',sha256=x['sha256']) for x in out['record_hashes']]
(B/'canonical-records-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
md=['# Veinot1997 independent canonical-record audit','',f"Status: **{out['status']}**. {out['record_count']} records, {out['measurement_count']} measurement entries, {out['operation_count']} operations. {len(checks)} checks; {len(errors)} failed checks; {len(openfindings)} open findings.",'','All 141 independent source units have a canonical/reader-context disposition. This does not claim that the final reader has rendered every source item or that SI was located.','','## Findings','']+[f"- **{f['id']} [{f['status']}]: {f['title']}.** {f['detail']}" for f in findings]+['','## Scientific review scope','']+['- '+s for s in out['manual_review']]+['','Exact current record hashes, independent source-table checks and source-unit dispositions are retained in canonical-records-audit.json. Reproducible private checker: build_canonical_audit.py. No Site files were changed.']
(B/'canonical-records-audit.md').write_text('\n'.join(md)+'\n',encoding='utf8')
print(json.dumps(dict(status=out['status'],records=out['record_count'],measurements=out['measurement_count'],operations=out['operation_count'],checks=len(checks),failed_checks=errors,open_findings=[f['id'] for f in openfindings]),indent=2))
