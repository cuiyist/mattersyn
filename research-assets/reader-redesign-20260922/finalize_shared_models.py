from pathlib import Path
import re
D=Path(__file__).resolve().parents[2]/'recipe-atlas/dist'
p=D/'chemical-viewer.mjs';s=p.read_text(encoding='utf-8')
s=s.replace("const atomColors=", "export const atomColors=")
s=s.replace("Zn:'#6d96ba'}", "Zn:'#6d96ba',Ge:'#9484a8',Te:'#b79b57',La:'#809aad',Ce:'#aaa16d',Mo:'#738c9c',In:'#7e88b5',Co:'#4c83b5',Ni:'#5caa87',Ir:'#9d8fb5',Mn:'#be7eaf',Pt:'#a2afb9',Sn:'#718695',Al:'#b7bfc9',As:'#a48cc4',X:'#9975b3'}")
p.write_text(s,encoding='utf-8')
p=D/'reader-structures.mjs';s=p.read_text(encoding='utf-8')
s=s.replace("import {elementLegend}","import {elementLegend,atomColors}")
s=re.sub(r'const colors=\{[^\n]+\};', 'const colors=atomColors;', s, count=1)
s=s.replace(".includes(r.record_id));}",".includes(r.record_id)).map(ref=>ref.bindingScopes?.[r.record_id]?{...ref,scope:ref.bindingScopes[r.record_id],phaseScope:ref.bindingScopes[r.record_id],sample_context_note:null}:ref);}",1)
s=s.replace('viewer.zoom(.85);viewer.render();','viewer.zoom(1.2);viewer.render();')
p.write_text(s,encoding='utf-8')
p=D/'crystal-viewer.mjs';s=p.read_text(encoding='utf-8')
s=s.replace('A verified local Ag crystal reference is unavailable; no sample CIF or atomistic interface is invented.','An independent bulk Ag unit cell is available for comparison; no sample CIF or atomistic interface is inferred.')
s=s.replace('A verified cubic CdS reference structure is not available in this local collection.','Independent cubic and hexagonal CdS unit cells are available for comparison; neither is a measured specimen refinement.')
s=s.replace('No verified local CdS/FePt CIF is available for this contribution.','Independent CdS reference cells do not establish FePt order or a measured interface.')
needle=" host.append(el('h3','Reference crystal structures'),"
pos=s.index(needle)
s=s[:pos]+" const referenceHost=el('div');host.append(referenceHost);const {mountReaderStructures}=await import('./reader-structures.mjs?v=0.34.0');await mountReaderStructures(referenceHost,r);return;\n"+s[pos:]
p.write_text(s,encoding='utf-8')
print('Unified element colors, binding scopes, and qualified Data-view reference display.')
