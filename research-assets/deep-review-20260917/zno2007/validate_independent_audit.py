"""Schema/graph and source-specific boundary checks after independent full-page review."""
import sys,json,hashlib,math,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'nak2017/runtime'))
import jsonschema
sys.path.insert(0,str(R.parents[2]/'recipe-atlas/scripts'))
from dataset_lib import validate_record,walk
from PIL import Image
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
C=json.loads((R/'coverage.json').read_text(encoding='utf-8'))
rs={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in (R/'canonical').glob('*.json')}
errors=[]
checks=[]
def check(ok,msg):
    checks.append({'check':msg,'passed':bool(ok)})
    if not ok:errors.append(msg)
for r in rs.values():errors+=validate_record(r)
check(len(rs)==6,'Six canonical protocols/controls, not six independent measured batches')
expected={'main':'a2740a2d7e6874219644a88ae0a1c447bda6c621fa49e9571f1012724d8e5824','si':'ef4fe0a6911e91eb211027e9ec4a5c4bf78de80cf0c1adf7837e03fb05f98e6b'}
for d in C['documents']:
    check(sha(Path(d['source_path']))==d['sha256']==expected[d['role']],'Original source hash '+d['role'])
    check(len(d['pages'])==d['page_count'] and all(p['text_read'] and p['visual_review'] for p in d['pages']),'All pages reviewed '+d['role'])
    for p in d['pages']:
        check((R/'audit-text'/f"{d['role']}-{p['page']}.txt").exists() and (R/d['role']/f"page-{p['page']}.png").exists(),'Full text and original page render '+d['role']+str(p['page']))
check(len(C['figures'])==11 and not C['tables'],'Seven main figures, three SI figures, one unnumbered chemical scheme, zero tables')
for f in C['figures']:
    path=R/f['crop']['path'];check(path.exists() and sha(path)==f['crop']['sha256'],'Original crop hash '+f['id'])
    im=Image.open(path);check(im.width>100 and im.height>100,'Crop pixel dimensions '+f['id'])
check(set(next(f for f in C['figures'] if f['id']=='fig4')['sample_links'])=={'S1','S2'},'Figure4 includes S1 and aqueous S2')
check('Confinement model' not in C['documents'][0]['pages'][2]['sections'] and 'Quantum-confinement model' in C['documents'][0]['pages'][3]['sections'],'Confinement model on physical main page4')
P='fu-2007-zno-'
s1,s2,s3,s4=[rs[P+x] for x in ['s1','s2','s3','s4']]
check(len(s1['measurements'])==17,'S1 has ten original and seven added measurements, without regenerated duplicates')
def op(r,i):return next(o for o in r['operations'] if o['id']==i)
for r in [s2,s3,s4]:
    for key in ['materials','stocks','operations']:
        for path,f in walk(r[key]):
            if f.get('status')=='reported' and 'value' in f:
                check(r is s4 and f.get('unit')=='mmol/L' and f.get('value')==4,'Only changed S4 concentration independently reported in variant preparation '+r['record_id']+path)
    check('3.8' not in json.dumps(r['intended_target']),'No copied S1 size target prose '+r['record_id'])
check('oleic_acid' not in {m['id'] for m in s2['materials']} and 'oleic_acid' not in op(s2,'combine-stocks-oa')['inputs'],'S2 no OA material or input')
check('0.35' not in json.dumps(s2['operations']) and '0.35' not in json.dumps(s2['stocks']),'S2 no copied OA charge prose')
check(all(m['sample_id']=='fu2007-s2-dry' for m in s2['measurements'] if m['property']=='photoluminescence_peak'),'S2 numeric PL peaks belong only to dry powder')
check(next(p for p in s2['products'] if p['sample_id']=='fu2007-s2-early')['recipe_link']=='general_context','Early60C/20min remains contextually linked, not exact timed-hold synthesis')
check('diethanolamine' not in {m['id'] for m in s3['materials']} and s3['stocks'][0]['id']=='ammonia-stock','S3 ammonia replaces DEA identity')
check(not s3['measurements'] and all(p['phase']['value'] is None for p in s3['products']),'S3 no inherited S1 numerical outcomes or phase')
check('100 mL' not in json.dumps(s3) and '26.3' not in json.dumps(s3),'S3 no copied total-water or DEA charge')
check(all(q['value'] is None for q in s3['operations'][0]['parameters'].values()),'S3 ammonia amount, volume and concentration unknown')
check(s4['stocks'][1]['components'][0]['quantities']['mass']['value'] is None and op(s4,'prepare-zinc-stock')['parameters']['precursor_mass']['value'] is None,'S4 precursor mass unknown in both stock and operation')
check('37.2' not in op(s4,'prepare-zinc-stock')['description'] and '2.5' not in op(s4,'prepare-zinc-stock')['description'],'S4 no stale S1 salt charge in preparation prose')
check(s4['stocks'][1]['concentrations']['zinc_nitrate']['value']==4 and s4['stocks'][1]['components'][0]['quantities']['nominal_zinc_amount']['value']==.2,'S4 reported4mM versus conditional calculated0.2mmol')
check({m['property'] for m in s4['measurements']}=={'particle_size','relative_surface_area_reduction','relative_photoluminescence_intensity_reduction'},'S4 no inherited S1 QY/phase/diameter outcomes')
for suffix,times in [('s2-oa-post-treatment',[.5,1.5,2.5,3.5]),('s1-hcl-perturbation',[1,3,8])]:
    r=rs[P+suffix];check([m['value']['value'] for m in r['measurements']]==times,'Correct treatment sampling times '+suffix)
    check(all(m['property']=='treatment_sampling_time' for m in r['measurements']),'No digitized or fabricated post-treatment intensities '+suffix)
check(not any('Fig.3a' in json.dumps(r) or 'Fig.3b' in json.dumps(r) for r in rs.values()),'No nonexistent Figure3 panel labels')
check(abs(.55*113.8/82.6-.76)<.003,'Relative QY calibration reproduces approximately76%')
check(abs((1-3.8/4.2)*100-9.5)<.03,'Author fixed-amount surface-area comparison approximately9.5%, not measured area')
check(len(C['model_and_context_inventory'])==3,'Model quantities and prior-work comparisons inventoried separately')
report={'status':'passed' if not errors else 'failed','auditor':'Independent atomistic_frontier review','date':'2026-09-17','source_pages_fully_read_and_visually_inspected':9,'canonical_records':len(rs),'numbered_figures':10,'unnumbered_schemes':1,'errors':errors,'checks':checks,'generator_sha256':sha(R/'build_review.py'),'frozen_base_sha256':sha(R/'s1-base-snapshot.json'),'canonical_sha256':{p.name:sha(p) for p in sorted((R/'canonical').glob('*.json'))},'source_sha256':expected,'limitations':['Checks do not establish a fully specified reproducible SOP.','Unreported formulation, timing and specimen-identity details remain unknown.','Continuous plot traces are not digitized; cited background papers are not fully reviewed.']}
(R/'independent-audit-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if not errors:
    C['independent_audit']={'status':'completed_with_corrections','auditor':'atomistic_frontier','date':'2026-09-17','scope':'Independent full-text and visual review of all 5 main and 4 SI pages; source-specific numerical, variant, specimen and figure checks.','report':'audit.md','validation_report':'independent-audit-validation.json','remaining_source_gaps':True}
    (R/'coverage.json').write_text(json.dumps(C,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'records':len(rs),'checks':len(checks),'errors':errors},indent=2))
raise SystemExit(bool(errors))
