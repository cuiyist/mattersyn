from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;O=R/'molecular-assets';O.mkdir(exist_ok=True)
P=Path('[local path redacted]');reg=json.loads(P.read_text(encoding='utf8'));byid={e['id']:e for e in reg['entries']}
text={'sulfuric-acid':'Neutral H2SO4 chemical-identity reference. Any conformer is illustrative, not measured solution geometry. Acid concentration, temperature, protonation and treatment conditions belong to each source record; this molecule does not specify acid-solution composition.','hydrogen-fluoride':'Neutral HF chemical-connectivity reference. Any conformer is illustrative, not measured solution geometry or an aqueous-speciation model. Supplied concentration, mixture ratio, solvent and etching conditions belong to each source record.'}
rows=[]
for id,t in text.items():
 e=byid[id];rows.append({'id':id,'expectedAssetHashes':e.get('assetHashes',{}),'caption':t,'limitations':[t],'reason':'Remove unrelated previous-paper conditions from shared identity metadata; retain existing coordinates and asset hashes.'})
(O/'registry-neutralizations.json').write_text(json.dumps({'scope':'Metadata-only neutralization; existing molecular assets unchanged','sourceRegistrySha256':hashlib.sha256(P.read_bytes()).hexdigest(),'updates':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Prepared two metadata-only neutralizations.')
