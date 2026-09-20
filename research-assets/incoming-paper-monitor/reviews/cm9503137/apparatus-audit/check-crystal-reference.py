"""Bounded independent provenance, CIF/coordinate and reference-only audit."""
import sys,json,hashlib,math,collections
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
import gemmi
OUT=Path(__file__).resolve().parent
B=OUT.parent
SOURCE=Path('[local path redacted]')
R=B/'crystal-reference'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(ok,label):checks.append({'check':label,'passed':bool(ok)})
entry=read(R/'registry-entry.json');model=read(R/'model.json');old=read(SOURCE/'cdse-unit-cell-viewer.json')
check(sha(R/'9016056.cif')==sha(SOURCE/'cdse-wurtzite-cod-9016056-original.cif')=='92e759602b5c7fd26e8bb0fe63bc7a3b52c86d09cfbe72d79f71a297f8b8ac4a','Byte-identical existing COD9016056 CIF')
check(entry['cifSha256']==sha(R/'9016056.cif') and entry['modelSha256']==sha(R/'model.json'),'Registry hashes resolve to private files')
check(model['source']['reused_viewer_sha256']==sha(SOURCE/'cdse-unit-cell-viewer.json'),'Original viewer hash preserved')
check(model['source']['doi']=='10.1107/S0567739477000977','Structure provenance points to Freeman1977, not Danek1996 measured structure')
check(entry['referenceOnly'] and not entry['trainingEligible'] and model['reference_only'] and not model['measured_sample_structure'] and not model['training_eligible'],'Reference-only and no measured/training flags')
check(len(model['atoms'])==4 and collections.Counter(a['element'] for a in model['atoms'])=={'Cd':2,'Se':2},'Four-site stoichiometric bulk CdSe unit cell only')
check(not any(a['element']=='Zn' for a in model['atoms']),'No invented ZnSe shell coordinates')
check(model['cell']=={k:old[k] for k in ['a','b','c','alpha','beta','gamma']} and model['cellVectors']==old['latticeVectors'],'Cell and lattice-vector mapping exact')
check(all(a['occupancy']==1 for a in model['atoms']) and not entry['mixedOccupancy'],'Full occupancy only; no mixed sites hidden')
ss=gemmi.make_small_structure_from_block(gemmi.cif.read_file(str(R/'9016056.cif')).sole_block())
check(ss.spacegroup_hm.replace(' ','')=='P63mc' and entry['spaceGroupNumber']==186,'CIF space group agrees with reference entry')
sites=ss.get_all_unit_cell_sites()
check(len(sites)==4,'CIF symmetry expansion has four sites')
def periodic_delta(x,y):return abs((x-y+.5)%1-.5)
for i,a in enumerate(model['atoms']):
    f=a['fractional']
    check(any(s.element.name==a['element'] and max(periodic_delta(f[j],[s.fract.x,s.fract.y,s.fract.z][j]) for j in range(3))<1e-5 for s in sites),f'Model atom {i} matches source-CIF symmetry expansion within accumulated source rounding')
    check(max(abs(a[ax]-sum(f[j]*model['cellVectors'][j][k] for j in range(3))) for k,ax in enumerate('xyz'))<1e-9,f'Atom {i} fractional-to-Cartesian mapping')
check(all(abs(getattr(ss.cell,k)-model['cell'][k])<1e-8 for k in ['a','b','c','alpha','beta','gamma']),'Cell constants exactly match source CIF')
check('Not a measured Danek' in entry['description'] and 'neither assigns the shell phase' in entry['scope'],'Visible description clearly limits sample assignment')
errors=[x['check'] for x in checks if not x['passed']]
out={'status':'passed' if not errors else 'corrections_required','scope':'Source-byte/hash, four-site CIF expansion and coordinate conversion, occupancy, cell, source DOI and reference-only flags. No new geometry, DFT, shell fitting or full geometric revalidation performed.',
 'source_doi':'10.1021/cm9503137','external_structure_doi':'10.1107/S0567739477000977','checks':checks,'errors':errors,
 'private_hashes':{p.name:sha(p) for p in R.iterdir() if p.is_file()},
 'integration_notes':['registry-entry modelPath is the intended public models/cdse-wurtzite-cod-9016056.json path; root must copy private model.json there.','References linked from film records must remain visibly labeled bulk CdSe comparison; they are not models of film, ZnSe matrix or core/shell interface.','The inherited viewer restores source five-decimal thirds to exact 1/3 and 2/3; source u = 0.37679 is retained. Gemmi symmetry expansion includes x-y = -0.33334; periodic deviation from the exact 2/3 site is 0.000006667, requiring a 0.00001 fractional-coordinate tolerance. This is disclosed source rounding, not a conversion error.']}
(B/'crystal-reference-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':out['status'],'checkCount':len(checks),'errors':errors}))
