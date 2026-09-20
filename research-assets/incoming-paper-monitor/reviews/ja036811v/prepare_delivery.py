from pathlib import Path
import json
B=Path(__file__).resolve().parent;P=B.parent/'ja035980c';V=B/'visuals'
scope='All14 main pages and4 matched SI pages text-read and visually inspected, with independent source, canonical, molecular, apparatus and reader audits. Pure and doped ZnO routes, TOPO processing, surface-bound controls, aggregated magnetic specimens, measured spectra and theoretical models retain separate scopes. Source conflicts and missing quantities remain explicit; cited external works are not independently inspected.'
notes=['Three pure/Co-doped/Ni-doped ZnO synthesis routes with separately represented postprocessing, specimen preparation, measurements and theoretical interpretations.','All11 main figures, six SI figures, two tables, Scheme1, ten equation groups and source excerpts are retained. TEM and original electron-diffraction patterns are available; source-reported XRD conclusions have no supplied original trace.','Nominal dopant feeds, incorporated concentrations, deliberate surface-bound control, optical specimens and aggregate powder are distinct. Source concentration, equivalent, size and spectral-wording inconsistencies remain visible.']
for name in ['run_build.py','build_inventory_actual.py','verify_archive.py']:
 t=(P/name).read_text(encoding='utf8').replace('banerjee2003','schwartz2003').replace('banerjee-2003-','schwartz-2003-').replace('ja035980c','ja036811v').replace('0.19.0','0.20.0').replace('all_banerjee_records','all_schwartz_records').replace('-banerjee-actual','-schwartz-actual')
 if name=='build_inventory_actual.py':
  a=t.index("'review_scope':",t.index("row={'source_group'"));b=t.index(",'evidence_locator'",a)
  t=t[:a]+"'review_scope':"+repr(scope)+",'documents':[{'role':'main','page_count':14,'all_text_read':True,'all_visually_reviewed':True},{'role':'si','page_count':4,'all_text_read':True,'all_visually_reviewed':True}]"+t[b:]
  a=t.index(",'notes':",t.index("row={'source_group'"));b=t.index("\ninv['per_paper']",a);t=t[:a]+",'notes':"+repr(notes)+'}'+t[b:]
 (B/name).write_text(t,encoding='utf8')
t=(P/'visuals/render_banerjee_scenes.mjs').read_text(encoding='utf8').replace('Banerjee2003','Schwartz2003').replace('banerjee2003','schwartz2003').replace('record_count:14','record_count:30')
(V/'render_schwartz_scenes.mjs').write_text(t,encoding='utf8')
for name in ['render_scene_contacts.py','diagnose_scene_geometry.py']:(V/name).write_bytes((P/'visuals'/name).read_bytes())
print('Prepared build/inventory/archive and scene-render helpers. No Site mutation.')
