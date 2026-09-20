from pathlib import Path
import json
B=Path(__file__).resolve().parent;O=B/'reader-assets';O.mkdir(exist_ok=True)
old=(B.parent/'ja036811v/reader-assets/build_assets.py').read_text(encoding='utf8')
specs=[
('figure-1','figure','main',3,(92,68,517,748),'Figure 1 · Individual PbSe nanocrystal and polycrystalline spherical assemblies'),
('figure-2','figure','main',3,(550,68,974,468),'Figure 2 · Wire-like assemblies, junction and selected-area electron diffraction'),
('figure-3','figure','main',4,(92,67,517,1020),'Figure 3 · Bent assembly and high-resolution lattice fringes'),
('figure-4','figure','main',4,(550,67,974,486),'Figure 4 · Absorption of spherical assemblies at three growth times'),
('figure-5','figure','main',5,(92,65,974,715),'Figure 5 · Device architecture, actual contacted wire and current–voltage measurements'),
('synthesis-method','source_note','main',2,(92,888,517,1287),'Source method · Stocks, rapid injection and temperature branches'),
('workup-method','source_note','main',2,(550,65,974,194),'Source method · Aliquot quenching and purification'),
('characterization-method','source_note','main',2,(550,195,974,443),'Source methods · Microscopy, electron diffraction and absorption'),
('device-method','source_note','main',2,(550,447,974,905),'Source method · Single-wire circuit fabrication and measurement'),
('dipole-model','equation','main',5,(92,953,517,1288),'Source inline models · Dipole moment and dipole–dipole energy'),
('transport-model','equation','main',6,(92,65,517,770),'Source inline models · Internal field, capacitance, transfer energy and barriers'),
('assembly-model','source_note','main',5,(550,722,974,1099),'Source interpretation · Entropy, assembly kinetics and TOPO impurity effects'),
('summary-conflict','source_note','main',6,(92,776,517,1285),'Source summary · Printed stock-ratio and electric-field terminology conflicts'),
]
start=old.index('specs=[');end=old.index("manifest={'schema_version'",start)
new=old[:start]+'specs='+repr(specs)+'\n'+old[end:]
new=new.replace('schwartz2003','sashchiuk2004').replace('10.1021/ja036811v','10.1021/nl0345116')
new=new.replace("'main':list(range(1,15)),'si':list(range(1,5))","'main':list(range(1,8)),'si':[]")
new=new.replace("{'status':'matched_and_reviewed','evidence':'Main p.14 explicitly lists S1–S6, all six supplied SI figures match in subject and order; SI author metadata identifies Daniel Gamelin.'}","{'status':'not_located','evidence':'No SI declaration observed in the supplied seven-page main article; no matched local SI available in the current source bundle.'}")
new=new.replace("f'main-{n:02}.png'","f'main-{n}.png'")
(O/'build_assets.py').write_text(new,encoding='utf8')
print('Asset builder prepared:',len(specs))
