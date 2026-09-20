from pathlib import Path
B=Path(__file__).resolve().parent;old=B.parent/'jp0208743'
(B/'reader-assets').mkdir(exist_ok=True);(B/'public-review-proposal').mkdir(exist_ok=True)
text=(old/'reader-assets/build_assets.py').read_text(encoding='utf8').replace('Dantas 2002','Yi 2002').replace('dantas2002','yi2002').replace('jp0208743','cm0115416').replace("'visual_reviewed':True,'reviewed':False","'visual_reviewed':False,'reviewed':False")
start=text.index('specs=[');end=text.index('\ndoc=',start)
specs=[
('figure-1','figure',2,(550,79,981,359),'Figure 1 · X-ray diffraction of annealed nanocrystals'),
('figure-2','figure',2,(550,368,981,622),'Figure 2 · TEM before and after 800 °C annealing'),
('figure-3','figure',3,(92,77,522,451),'Figure 3 · Particle-size intensity distribution'),
('figure-4','figure',3,(92,979,978,1321),'Figure 4 · Down-conversion and up-conversion spectra'),
('figure-5','figure',4,(92,77,522,445),'Figure 5 · Near-infrared absorption spectrum'),
('figure-6','figure',4,(92,459,522,799),'Figure 6 · Five annealing-temperature spectra'),
('figure-7','figure',4,(92,815,522,1169),'Figure 7 · Erbium concentration dependence'),
('figure-8','figure',4,(550,78,981,459),'Figure 8 · Up-conversion excitation-power dependence'),
('figure-9','figure',4,(550,467,981,903),'Figure 9 · Proposed Yb/Er energy-level mechanism'),
('figure-10','figure',5,(92,78,522,437),'Figure 10 · Bulk and nanocrystal emission comparison'),
('hydrothermal-preparation','source_note',2,(92,531,522,914),'Hydrothermal preparation · Solutions, precipitation, treatment and workup'),
('bulk-preparation','source_note',2,(92,914,522,999),'Bulk comparison · Solid-state mixing, pressing and firing'),
('characterization-methods','source_note',2,(92,999,522,1252),'Characterization · Microscopy, spectroscopy, diffraction and sizing'),
('excitation-method','source_note',2,(550,635,981,690),'Up-conversion acquisition · Laser and fiber coupling'),
('xrd-analysis','source_note',2,(550,740,981,1008),'XRD analysis · Phase assignment, line widths and Scherrer estimate'),
('power-law-analysis','source_note',3,(550,711,981,957),'Power analysis · Intensity relation and rounded regression slopes'),
]
text=text[:start]+'specs='+repr(specs)+'\n'+text[end:]
(B/'reader-assets/build_assets.py').write_text(text,encoding='utf8')
print('Prepared source-specific crop generator')
