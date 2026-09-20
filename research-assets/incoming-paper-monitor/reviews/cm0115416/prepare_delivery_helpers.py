"""Prepare this source's root-only delivery scripts; does not edit the Site."""
from pathlib import Path
import json
B=Path(__file__).resolve().parent;P=B.parent/'jp0208743'
for name in ['run_build.py','verify_archive.py','finalize_publication.py','build_inventory_actual.py']:
 t=(P/name).read_text(encoding='utf8')
 for a,b in [('dantas2002','yi2002'),('dantas-2002','yi-2002'),('dantas','yi'),('jp0208743','cm0115416'),('0.17.0','0.18.0'),('PbS/glass','La2(MoO4)3:Yb,Er'),('a44f927e3c2b3e9f75925e1e47cd105acc652c443b4ace1ab471cf3cac603a41','5025768ecf6ddd21d556ffb63dac2e912982fc4adf6835cdd0b9bebc647e56e7'),('c8fd35a429bf636fcccc5dfeb3211cea44299e911fbfc80e1a308c75b7b04917','6438ee53b3fffb86f5e36508f265041d9235b8ee9f3e20dd99d46aae91c68a57')]:t=t.replace(a,b)
 t=t.replace('original_figures=7','original_figures=10').replace('len(records)==16','len(records)==18').replace("p['operations']==48","p['operations']==105")
 if name=='build_inventory_actual.py':
  start=t.index("'notes':['Shared glass preparation")
  end=t.index('}\ninv[',start)
  t=t[:start]+"'notes':['Five hydrothermal/annealing comparison conditions and one independently specified solid-state bulk method retain their preparation lineage and missing individual comparison charges.','All ten original figures and six source excerpts preserve XRD, TEM, intensity-based sizing, down-conversion, up-conversion, near-IR absorption, annealing/doping/power comparisons and proposed mechanisms.','Printed ammonium molybdate mass/mole and nominal feed/formula conflicts remain unresolved. No measured atomic coordinates, SAED, absolute quantum yield or unreported raw data are invented.']"+t[end:]
 (B/name).write_text(t,encoding='utf8')
# Derive bindings from the final registry and current canonical hashes.
t=(P/'build_bindings.py').read_text(encoding='utf8')
a=t.index('mapping=');z=t.index('registry=',a)
t=t[:a]+"mapping={e['id'].removeprefix('identity-yi-'):e['id'] for e in read(V/'registry-additions.json')['entries']};mapping['water']='water'\n"+t[z:]
t=t.replace('len(drafts)==16','len(drafts)==18').replace('dantas-2002-','yi-2002-')
t=t.replace("if suffix in ['sg1','sg2','sg3','sg4','afm1','afm2']:products[rid]='identity-dantas-'+suffix+'-specimen'","if suffix in ['anneal-600','anneal-700','anneal-800','anneal-900','anneal-1000','bulk']:products[rid]='identity-yi-'+suffix+'-specimen'")
t=t.replace('Source powder identities and specimen architecture only. Oxide atom-count diagrams do not represent molecular or crystalline geometry; sulfur identity, glass proportions and literal vessel ambiguity remain unresolved.','Source formula/composition identities and illustrative specimen states; generic analysis specimens do not inherit a specific annealing batch. Reference stock quantities do not assign comparison-batch charges. Printed mass/mole and feed/formula conflicts remain explicit.')
t=t.replace('Six source-defined PbS/glass specimens, with illustrative embedded-particle architecture. No measured atomic structure supplied; unassigned analysis/model contexts have no generic product binding.','Five annealed phosphor conditions and the distinct bulk comparator, with illustrative specimen identity. No source atomic structure or dopant occupancy is supplied; unassigned analysis contexts have no route product binding.')
(B/'build_bindings.py').write_text(t,encoding='utf8')
struct=['scherrer_crystallite_size','diffraction_reference','phase_purity_limit','figure1_display_scope','author_particle_crystallinity_inference','tem_scale_bar','tem_majority_particle_diameter_range','tem_morphology','annealing_size_comparison','instrumental_majority_particle_diameter_range','instrumental_average_particle_diameter','abstract_summary_particle_diameter','figure3_distribution_scope','author_size_method_agreement','annealing_morphology_observation']
(B/'structural-property-additions.json').write_text(json.dumps(struct,indent=2)+'\n',encoding='utf8')
print('Prepared delivery/inventory/finalization scripts and bindings generator; Site unchanged.')
