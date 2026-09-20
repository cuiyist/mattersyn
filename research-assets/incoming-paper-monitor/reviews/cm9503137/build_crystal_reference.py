"""Reuse the existing locally verified bulk CdSe reference; no Danek structure inferred."""
from pathlib import Path
import json,hashlib,math,shutil
from collections import Counter
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';old=S/'dist/assets/cdse-structures';out=B/'crystal-reference';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
src=json.loads((old/'cdse-unit-cell-viewer.json').read_text(encoding='utf-8'));cif=old/'cdse-wurtzite-cod-9016056-original.cif'
assert src['spaceGroupNumber']==186 and src['uniqueComposition']=={'Cd':2,'Se':2}
assert src['source']['doi']=='10.1107/S0567739477000977'
atoms=[{'element':a['elem'],'x':a['x'],'y':a['y'],'z':a['z'],'fractional':a['fractional'],'occupancy':1} for a in src['atoms']]
vectors=src['latticeVectors']
for a in atoms:
 for k,axis in enumerate('xyz'):assert abs(a[axis]-sum(a['fractional'][j]*vectors[j][k] for j in range(3)))<1e-10
assert Counter(a['element'] for a in atoms)=={'Cd':2,'Se':2}
model={'id':'cdse-wurtzite-cod-9016056','cell':{k:src[k] for k in ['a','b','c','alpha','beta','gamma']},'cellVectors':vectors,'atoms':atoms,'source':{'doi':src['source']['doi'],'url':src['source']['url'],'sha256':sha(cif),'citation':src['source']['citation'],'reused_viewer_sha256':sha(old/'cdse-unit-cell-viewer.json')},'training_eligible':False,'measured_sample_structure':False,'reference_only':True,'notes':src['notes']+['Danek Figure3 uses wurtzite comparison lines; this bulk reference is not an assignment of the experimental overlayer or interface. No ZnSe shell coordinates are added.']}
model['notes']=[n for n in model['notes'] if n.startswith('The original CIF') or n.startswith('Danek Figure3')]
write('model.json',model);shutil.copy2(cif,out/'9016056.cif')
ref={'id':'cdse-wurtzite-cod-9016056','name':'Bulk wurtzite CdSe reference · core comparison','formula':'CdSe','record_ids':['danek-1996-znse-overgrowth','danek-1996-solution-characterization','danek-1996-bare-dot-film','danek-1996-overcoated-dot-film'],'description':'Existing COD9016056 bulk CdSe structure reused for comparison. Not a measured Danek nanocrystal, shell or film structure.','scope':'Danek Figure3 compares wurtzite reference lines with broad particle patterns. The experimentally unresolved ZnSe overlayer/interface is omitted; this pure bulk CdSe reference neither assigns the shell phase nor reconstructs core/shell atoms.','sourceUrl':src['source']['url'],'cifPath':'9016056.cif','modelPath':'models/cdse-wurtzite-cod-9016056.json','spaceGroup':'P 63 m c','spaceGroupNumber':186,'mixedOccupancy':False,'cifSha256':sha(out/'9016056.cif'),'modelSha256':sha(out/'model.json'),'referenceOnly':True,'trainingEligible':False}
write('registry-entry.json',ref);write('validation.json',{'status':'passed','scope':'Existing source CIF/viewer identity and four-atom coordinate mapping checked; bulk reference only','cif_sha256':ref['cifSha256'],'model_sha256':ref['modelSha256'],'atoms':4,'composition':dict(Counter(a['element'] for a in atoms)),'no_shell_or_sample_coordinates':True})
print(json.dumps({'cif_sha256':ref['cifSha256'],'atoms':len(atoms),'bulk_reference_only':True}))
