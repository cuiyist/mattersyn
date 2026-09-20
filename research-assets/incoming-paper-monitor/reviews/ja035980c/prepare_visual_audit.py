from pathlib import Path
B=Path(__file__).resolve().parent
old=B.parent/'cm0115416'/'visuals'; V=B/'visuals'
text=(old/'render_yi_scenes.mjs').read_text(encoding='utf8').replace('Yi2002','Banerjee2003').replace('yi2002','banerjee2003').replace('record_count:18','record_count:14')
(V/'render_banerjee_scenes.mjs').write_text(text,encoding='utf8')
for n in ['render_scene_contacts.py','diagnose_scene_geometry.py']:
 (V/n).write_bytes((old/n).read_bytes())
