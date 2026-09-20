"""Explicit semantic map, keyed through a frozen independent source inventory."""
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent
p=B/'source-audit.json'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='c0b0f00e205a5e1fe7fef09e41bcf8d33f46a9e043b7cbd17f60b65271eb67d9'
a=json.loads(p.read_text(encoding='utf8'));m={}
def bind(target,numbers):
 for n in numbers:
  assert a['units'][n]['id'].startswith('gerion2001-')
  m.setdefault(a['units'][n]['id'],[]).append(target)
data={
'identity':[0,1,2,3,4],'structure-scope':[5,6],'optical-width':[7,115,118],'study-summary':[8,17,203,204],'motivation':[9,13],'background-quantitative':[10,11,12,14],'prior-coatings':[15,16],
'chemical-topo':[18],'chemical-mps':[19],'chemical-aps':[20],'chemical-base':[21,22],'chemical-phosphonate':[23],'chemical-quench':[24],'chemical-mpa':[25],'chemical-dmap':[26],'analytical-reagents':[27,34,35],
'chemical-solvents':[28,29,30,31,32,33],'buffers':[36],'purification-materials':[37,38,39,40],'silica-optional':[41,63],'core-shell-stock':[42,43,44],
'silica-prime':[45,46,47],'silica-primary':[48,49,50],'silica-secondary':[51,52,53],'silica-quench':[54,55,56],'silica-dialysis':[57,58],'silica-concentrate':[59,60],'silica-exchange':[61,62],'silica-finish':[64,65,180],'unreported':[66,250],
'mpa-exchange':[67,68,69,70,71],'mpa-recovery':[72,73,74,75],'mpa-optional':[76],'buffer-exchange':[77],
'primary-network':[78,79,80],'secondary-network':[81],'quench-rationale':[82],
'optical-acquisition':[83,84,85],'storage-acquisition':[86],'cw-acquisition':[87,88,89],'tem-acquisition':[90,91,92],'eels-acquisition':[93],'afm-acquisition':[94,95],'afm-exclusions':[96,142,243,244],
'hplc-acquisition':[97,98,99],'ellman-acquisition':[100,101,102],'gel-acquisition':[103,104,105,106],'gel-salt':[107,159,160],'gel-narrowing':[108,162,163],
'table1-blue':[109],'table1-green':[110],'table1-yellow':[111],'table1-orange':[112],'table1-red':[113],'cohort-boundaries':[114,129],'optical-overview':[116,121,122,123],'optical-conflicts':[117],'storage-result':[119,124,125],'ph-optical':[120],'cw-result':[126,127,128],
'tem-results':[130,131,132,133],'si-microscopy':[134,206],'eels-result':[135],'afm-results':[136,137,138],'size-ambiguity':[139,189,190,191,192],'figure5-yellow':[140,141],
'table2-green':[143],'table2-yellow':[144],'table2-red':[145],'table2-dark-red':[146],'shell-thickness':[147,193],
'hplc-three':[148,149,150,151],'hplc-purified':[152,153],'thiol-result':[154,155],'gel-charge':[156,158],'gel-ph':[157],'salt-result':[161],'narrowing-result':[164],
'silica-literature':[165,166,185],'methanol-choice':[167,169],'mps-binding':[168],'primary-network':[78,79,80,170],'thermal-control':[171,172],'secondary-network':[81,173],'quench-rationale':[82,174,175],
'equilibration':[176,181],'column-chemistry':[177,178,179],'surface-chemistry':[182,200,201],'aps-control':[183],'aps-variant':[184],'brightening-mechanism':[186],'future-qy':[187],'afm-cross-reference-conflict':[188],
'hplc-size-limit':[194,195,197],'hplc-outlook':[196,198],'gel-interpretation':[199],'future-bioconjugation':[202],'affiliations':[205],
'upstream-zns':[245,246,247],'note34-scattering':[248,249],
}
for key,nums in data.items():bind(key,nums)
for key,nums in {'silica-dialysis':[41],'equilibration':[41],'optical-overview':[115],'mps-binding':[79],'cw-acquisition':[127],'hplc-outlook':[195]}.items():bind(key,nums)
for n in range(1,37):bind(f'reference-{n:02}',[206+n])
assert set(m)=={u['id'] for u in a['units']},[u['id'] for u in a['units'] if u['id'] not in m]
out=json.loads((O/'gerion2001.json').read_text(encoding='utf8'));items={i['id'] for s in out['reader_sections'] for i in s['items']}
assert all(t in items for targets in m.values() for t in targets)
(O/'source-item-mapping.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Explicitly mapped',len(m),'source units')
