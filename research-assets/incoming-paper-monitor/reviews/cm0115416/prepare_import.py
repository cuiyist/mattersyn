from pathlib import Path
B=Path(__file__).resolve().parent;P=B.parent/'jp0208743'
t=(P/'integrate_review.py').read_text(encoding='utf8')
# This operates only on a private helper; its audited import is run separately.
t=t.replace('Dantas contribution','Yi contribution').replace('len(drafts)==16','len(drafts)==18')
t=t.replace('dantas2002','yi2002').replace('Dantas2002','Yi2002')
t=t.replace('Six annealing variants, common glass preparation, optical and AFM specimens, and author calculations retain their own evidence scopes. Glass proportions, sulfur reagent, literal vessel identity and size/radius ambiguity remain unresolved.','Five hydrothermal annealing comparisons, independent solid-state bulk preparation, stock preparation, structural/optical analyses and author mechanisms retain their own evidence scopes. Printed mass/mole and nominal feed/formula conflicts, individual comparison charges and unassigned analysis specimens remain explicit.')
t=t.replace('Six annealing conditions do not establish six independent fusion batches. Optical size estimates and AFM grain-height labels remain distinct, with unresolved radius/size meaning. Original model plots, proposed mechanisms and architecture illustrations are not measured atomic structures.','Five annealing conditions do not establish five independently quantified precursor batches. XRD crystallite size, TEM diameter and intensity-based particle-analyzer distribution retain distinct sample and metric scopes. Proposed energy-transfer mechanisms and specimen diagrams are not measured atomic structures or absolute quantum yields.')
a=t.index("t=t.replace('const sourceArt=");z=t.index("# Explicitly classify",a)
t=t[:a]+'''t=t.replace('const sourceArt=createDantas2002Art','const sourceArt=createYi2002Art(o,r)||createDantas2002Art')
t=t.replace('dantas=buildDantas2002Scene(o,r);','dantas=buildDantas2002Scene(o,r),yi=buildYi2002Scene(o,r);').replace('dantas?.caption||','yi?.caption||dantas?.caption||').replace('||braun||besson||dantas){','||braun||besson||dantas||yi){').replace('=>(gerion||braun||besson||dantas)?','=>(gerion||braun||besson||dantas||yi)?');p.write_text(t,encoding='utf-8')
p=S/'dist/crystal-viewer.mjs';t=p.read_text(encoding='utf-8').replace("'besson2002','dantas2002']","'besson2002','dantas2002','yi2002']")
t=t.replace(" if(r.lineage?.source_group==='dantas2002'&&entryId)"," if(r.lineage?.source_group==='yi2002'&&entryId)host.append(el('p','Specimen diagrams are illustrative. The 800 °C powder is assigned tetragonal La2(MoO4)3 with a small unidentified second phase. No refined atomic coordinates, dopant occupancies or measured unit-cell file are supplied. TEM particle sizes, XRD crystallite size and particle-analyzer distributions retain separate specimen/metric scopes.','guide-notice'));\\n if(r.lineage?.source_group==='dantas2002'&&entryId)")
p.write_text(t,encoding='utf-8')
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf-8');assert "NAMES['La2(MoO4)3:Yb,Er']"not in t;t=t.replace("NAMES['Pt']='Platinum nanocrystals'","NAMES['Pt']='Platinum nanocrystals'\\nNAMES['La2(MoO4)3:Yb,Er']='Ytterbium/erbium-codoped lanthanum molybdate'");p.write_text(t,encoding='utf-8')
'''+t[z:]
t=t.replace("'dataset_version':'0.16.0'","'dataset_version':'0.17.0'").replace("'dataset_version':'0.17.0'\"),","'dataset_version':'0.18.0'\"),")
# Explicit version replacement; avoid matching the wrong replacement operand.
t=t.replace(".replace(\"'dataset_version':'0.17.0'\",\"'dataset_version':'0.17.0'\")",".replace(\"'dataset_version':'0.17.0'\",\"'dataset_version':'0.18.0'\")")
t=t.replace("t.replace('0.16.0-r1','0.17.0-r1')","t.replace('0.17.0-r1','0.18.0-r1')").replace('Imported16audited','Imported18audited')
(B/'integrate_review.py').write_text(t,encoding='utf8')
compile(t,str(B/'integrate_review.py'),'exec')
print('Prepared root-only import, not executed.')
