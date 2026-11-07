"""Focused synthetic tests; public code only, no paper/record/model reads."""
import copy,importlib.util,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import method_families as m

def mat(mid,name,role,formula=None):return {'id':mid,'name':name,'role':role,'formula':formula,'quantities':{}}
def record(rid='r1',doi='10.1234/one',metal='CdO',nonmetal='TOPSe',route='Hot injection',year=2020,status='source_extracted'):
 return {'record_id':rid,'method':route,'material':{'formula':'CdSe'},'materials':[mat('metal',metal,'metal_precursor'),mat('nonmetal',nonmetal,'chalcogen_precursor')],
 'stocks':[],'material_states':[],'operations':[{'id':'step','action':'inject','label':'Inject precursor','stage':'synthesis','inputs':['metal','nonmetal'],'optional_inputs':[],'parameters':{},'environment':{'status':'not_reported'}}],
 'products':[],'measurements':[],'lineage':{'source_group':'primary'},'sources':[{'id':'primary','doi':doi,'year':year,'authors':'First Author; Second Author; Third Author'}], 'quality':{'review_status':status}}
class FamiliesTest(unittest.TestCase):
 def test_named_metal_sources_stay_distinct_with_same_TOPSe(self):
  a=m.classify_record(record(metal='CdO'),'CdSe');b=m.classify_record(record(metal='cadmium metal'),'CdSe')
  self.assertEqual(a['metal_source'],'CdO');self.assertEqual(a['nonmetal_source'],'Se/TOP feed');self.assertNotEqual(a['key'],b['key'])
 def test_fixed_synonyms_merge_without_changing_record(self):
  r=record(metal='cadmium oxide',route='hot-injection');before=copy.deepcopy(r)
  self.assertEqual(m.classify_record(r,'CdSe')['key'],m.classify_record(record(),'CdSe')['key']);self.assertEqual(r,before)
 def test_exact_used_named_stock_can_identify_TOPSe_feed(self):
  r=record(nonmetal='selenium');r['materials'].append(mat('top','trioctylphosphine','solvent'));r['stocks']=[{'id':'feed','name':'TOP-Se solution','components':[{'material_id':'nonmetal'},{'material_id':'top'}]}];r['operations'][0]['inputs']=['metal','feed']
  self.assertEqual(m.classify_record(r,'CdSe')['nonmetal_source'],'Se/TOP feed')
  r['operations'][0]['inputs']=['metal','nonmetal']
  self.assertEqual(m.classify_record(r,'CdSe')['nonmetal_source'],'Se/TOP feed','Declared exact stock remains own evidence when the old graph omits its ID')
  r['operations'][0]['inputs']=['metal','feed'];r['stocks'][0]['name']='Chalcogen feed'
  self.assertEqual(m.classify_record(r,'CdSe')['nonmetal_source'],'Se/TOP feed','An exact used Se-plus-TOP stock describes the solution without asserting a bond')
  r['stocks']=[];r['operations'][0]['inputs']=['metal','nonmetal'];self.assertEqual(m.classify_record(r,'CdSe')['nonmetal_source'],'Se','Unrelated TOP and Se do not establish a stock')
 def test_exact_state_parent_links_reach_stock_components(self):
  r=record();r['material_states']=[{'id':'state','parent_ids':['metal','nonmetal']}];r['operations'][0]['inputs']=['state']
  self.assertEqual(m.classify_record(r,'CdSe')['kind'],'synthesis')
 def test_ambiguous_or_unresolved_sources_go_to_Other(self):
  r=record();r['materials'].append(mat('cd2','cadmium metal','metal_precursor'));r['operations'][0]['inputs'].append('cd2')
  self.assertEqual(m.classify_record(r,'CdSe')['reason'],'metal_multiple_sources')
  r['materials'][-1]['name']='Cadmium precursor'
  self.assertEqual(m.classify_record(r,'CdSe')['reason'],'metal_unresolved_source_identity')
 def test_fixed_known_generic_reagent_names_qualify_but_unknown_generic_does_not(self):
  r=record();r['materials'][0]['role']='reagent'
  self.assertEqual(m.classify_record(r,'CdSe')['metal_source'],'CdO')
  r['materials'][0]['name']='Unspecified metal reagent'
  self.assertEqual(m.classify_record(r,'CdSe')['kind'],'other')
 def test_no_route_and_generic_source_names_remain_Other(self):
  r=record(route='Other');r['operations'][0].update(action='add',label='Add materials')
  self.assertEqual(m.classify_record(r,'CdSe')['reason'],'missing_route')
  r=record(nonmetal='Selenium stock')
  self.assertEqual(m.classify_record(r,'CdSe')['kind'],'other')
 def test_elemental_Au_does_not_require_nonmetal_source(self):
  r=record(metal='HAuCl4');r['materials']=r['materials'][:1];r['operations'][0]['inputs']=['metal']
  c=m.classify_record(r,'Au');self.assertEqual(c['kind'],'synthesis');self.assertIsNone(c['nonmetal_source'])
 def test_given_core_shell_processing_is_last_but_seed_growth_is_not_assumed_processing(self):
  processing=record('processed',route='Shell growth');processing['materials'].append(mat('given','preformed CdSe cores','seed'));processing['operations'][0]['inputs'].append('given')
  self.assertEqual(m.classify_record(processing,'CdSe')['kind'],'processing')
  regular=record('fresh');g=m.build_method_families([processing,regular],'CdSe');self.assertEqual(g['families'][-1]['label'],'Processing of material')
  growth=record(metal='HAuCl4',route='Seed-mediated growth');growth['materials']=[growth['materials'][0],mat('seed','preformed Au nanocrystals','seed')];growth['operations'][0]['inputs']=['metal','seed']
  self.assertEqual(m.classify_record(growth,'Au')['kind'],'synthesis')
 def test_unique_paper_adoption_not_variant_count_orders_largest_family(self):
  records=[record('variant'+str(i),doi='10.1234/one') for i in range(6)]+[record('b1',doi='10.1234/two',metal='Cd metal'),record('b2',doi='10.1234/three',metal='Cd metal')]
  g=m.build_method_families(records,'CdSe');self.assertEqual(g['families'][0]['metal_source'],'Cd metal');self.assertEqual(g['families'][0]['paper_count'],2)
  folded=g['families'][1];self.assertEqual(folded['paper_count'],1);self.assertEqual(len(folded['papers']),1);self.assertEqual(len(folded['papers'][0]['record_ids']),6)
 def test_primary_source_DOI_normalization_and_explicit_source_fallback(self):
  a=record(doi='https://doi.org/10.1234/ABC');b=record('r2',doi='10.1234/abc');self.assertEqual(m.paper_key(a),m.paper_key(b))
  a['sources'][0]['doi']=None;b['sources'][0]['doi']=None;self.assertEqual(m.paper_key(a),m.paper_key(b))
 def test_review_status_then_completeness_then_earliest_year(self):
  a=record('reviewed',status='source_reviewed',year=2025);b=record('complete',year=2020);b['operations'][0]['parameters']={'duration':{'status':'reported','value':10}}
  c=record('old',year=1995);d=record('new',year=2000)
  g=m.build_method_families([d,b,c,a],'CdSe');self.assertEqual(g['families'][0]['record_ids'],['reviewed','complete','old','new'])
 def test_citation_uses_etal_only_for_more_than_two_or_explicit_existing_etal(self):
  self.assertEqual(m.author_label('Alpha; Beta; Gamma',2020),'Alpha et al. (2020)')
  self.assertEqual(m.author_label('Alpha; Beta',2020),'Alpha and Beta (2020)')
  self.assertEqual(m.author_label('Alpha',2020),'Alpha (2020)')
  self.assertEqual(m.author_label('Alpha et al.',2020),'Alpha et al. (2020)')
  self.assertIn('Murray, C. B., Norris, D. J.',m.author_label('Murray, C. B., Norris, D. J.',2000))
 def test_hydration_is_not_silently_discarded(self):
  a=mat('a','cadmium chloride','metal_precursor','CdCl2');b=mat('b','cadmium chloride','metal_precursor','CdCl2.2H2O')
  self.assertNotEqual(m.source_identity(a)['key'],m.source_identity(b)['key'])
 def test_metadata_preserves_every_variant_link_and_original_record(self):
  rows=[record('b'),record('a')];old=copy.deepcopy(rows);g=m.build_method_families(rows,'CdSe')
  self.assertEqual(set(g['families'][0]['papers'][0]['record_ids']),{'a','b'});self.assertEqual(rows,old)
 def test_given_nanocrystals_with_explicit_self_assembly_are_processing(self):
  r=record(route='Evaporation-based self-assembly');r['materials'].append(mat('given','preformed CdSe quantum dots','seed'));r['operations'][0]['inputs'].append('given')
  self.assertEqual(m.classify_record(r,'CdSe')['kind'],'processing')
 def test_used_given_cores_with_explicit_shell_overgrowth_are_processing(self):
  r=record(route='Seeded shell overgrowth in TOPO/TOP');r['materials'].append(mat('given','CdSe cores','seed'));r['operations'][0]['inputs'].append('given')
  self.assertEqual(m.classify_record(r,'ZnS')['kind'],'processing')
  r['operations'][0]['inputs'].remove('given')
  self.assertNotEqual(m.classify_record(r,'CdSe')['kind'],'processing','An unused reference core cannot convert a full synthesis to processing')
 def test_explicit_route_prefix_groups_method_qualifiers_without_inventing_new_route(self):
  a=record(route='Hot injection followed by size focusing');b=record(route='hot-injection')
  self.assertEqual(m.classify_record(a,'CdSe')['route'],'Hot injection');self.assertEqual(m.classify_record(a,'CdSe')['key'],m.classify_record(b,'CdSe')['key'])
 def test_explicit_core_shell_architecture_and_used_given_cores_identify_shell_processing(self):
  r=record(route='Seeded ZnS overgrowth in TOPO/TOP');r['material']['architecture']='core_shell';r['materials'].append(mat('given','CdSe cores','core seed'));r['operations'][0]['inputs'].append('given')
  self.assertEqual(m.classify_record(r,'ZnS')['kind'],'processing')
 def test_fixed_formula_under_generic_reagent_and_declared_source_without_input_graph(self):
  r=record();r['materials'][0].update(name='Reagent A',formula='CdCl2',role='reagent');r['operations'][0]['inputs']=['nonmetal']
  self.assertEqual(m.classify_record(r,'CdSe')['metal_source'],'CdCl2')
 def test_fixed_sources_do_not_override_explicit_solvent_or_ligand_role(self):
  for role in ['solvent','ligand','reaction medium','Core-shell ligand']:
   r=record();r['materials'][0]['role']=role
   self.assertEqual(m.classify_record(r,'CdSe')['kind'],'other')
 def test_product_compound_generic_reagent_is_not_element_sources(self):
  r=record(metal='InAs',nonmetal='arsine');r['materials'][0]['role']='reagent';r['materials'][1]['role']='reagent'
  self.assertEqual(m.classify_record(r,'InAs')['kind'],'other')
  r['materials'][0]['name']='trimethylindium'
  self.assertEqual(m.classify_record(r,'InAs')['metal_source'],'TMIn')
 def test_known_generic_competitor_is_not_silently_ignored(self):
  r=record();r['materials'].append(mat('second','cadmium metal','reagent'))
  self.assertEqual(m.classify_record(r,'CdSe')['reason'],'metal_multiple_sources')
 def test_other_is_fallback_after_identified_routes_but_can_default_when_only_fallback(self):
  a=record('known');b=record('other1',doi='10.1234/two',metal='Unspecified precursor');c=record('other2',doi='10.1234/three',metal='Unspecified precursor')
  g=m.build_method_families([a,b,c],'CdSe')
  self.assertEqual(g['families'][0]['kind'],'synthesis');self.assertEqual(g['default_record_id'],'known')
  g=m.build_method_families([b,c],'CdSe');self.assertEqual(g['families'][0]['kind'],'other');self.assertEqual(g['default_record_id'],'other1')
 def test_counterion_atoms_are_not_promoted_to_main_generic_nonmetal_source(self):
  r=record(metal='zinc sulfate',nonmetal='Unknown reagent');r['materials'][0]['role']='reagent';r['materials'][1]['role']='reagent'
  self.assertEqual(m.classify_record(r,'ZnS')['reason'],'nonmetal_missing_source')
 def test_display_strings_are_utf8_without_introduced_mojibake(self):
  r=record(route='Sol\u2013gel');c=m.classify_record(r,'CdSe')
  self.assertEqual(c['route'],'Sol-gel');self.assertEqual(c['label'],'Sol-gel - CdO + Se/TOP feed')
 def test_exact_used_TOP_stock_composition_merges_with_named_feed_without_bond_claim(self):
  r=record(nonmetal='Selenium pellets');r['materials'][1]['formula']='Se';r['materials'].append(mat('top','Tri-n-octylphosphine','precursor solvent','C24H51P'));r['stocks']=[{'id':'feed','name':'Chalcogen in TOP','components':[{'material_id':'nonmetal'},{'material_id':'top'}]}];r['operations'][0]['inputs']=['metal','feed']
  c=m.classify_record(r,'CdSe');self.assertEqual(c['nonmetal_source'],'Se/TOP feed');self.assertEqual(c['key'],m.classify_record(record(),'CdSe')['key'])
 def test_reported_ODE_diluent_keeps_main_feed_and_explicit_other_used_stock_wins(self):
  r=record(nonmetal='selenium');r['materials'] += [mat('top','trioctylphosphine','solvent'),mat('ode','1-octadecene','solvent')];r['stocks']=[{'id':'feed','name':'Se/TOP/ODE','components':[{'material_id':'nonmetal'},{'material_id':'top'},{'material_id':'ode'}]}];r['operations'][0]['inputs']=['metal','feed']
  self.assertEqual(m.classify_record(r,'CdSe')['nonmetal_source'],'Se/TOP feed')
  r['stocks'][0]['components'].pop();r['stocks'].append({'id':'used-other','name':'Se in ODE','components':[{'material_id':'nonmetal'},{'material_id':'ode'}]});r['operations'][0]['inputs']=['metal','used-other'];self.assertEqual(m.classify_record(r,'CdSe')['nonmetal_source'],'Se')
 def test_competing_declared_named_feeds_are_ambiguous_without_stock_use_link(self):
  r=record(nonmetal='selenium');r['materials'].append(mat('top','TOP','solvent'));r['stocks']=[{'id':'feedA','name':'TOP-Se solution','components':[{'material_id':'nonmetal'},{'material_id':'top'}]},{'id':'feedB','name':'TBPSe','components':[{'material_id':'nonmetal'}]}]
  self.assertEqual(m.classify_record(r,'CdSe')['reason'],'nonmetal_ambiguous_named_stock_feeds')
 def test_given_core_core_shell_seeded_growth_is_processing(self):
  r=record(route='Hot injection / seeded growth');r['material']['architecture']='core_shell';r['materials'].append(mat('given','wz-CdSe core nanocrystals','seed'));r['operations'][0]['inputs'].append('given')
  self.assertEqual(m.classify_record(r,'CdS')['kind'],'processing')
  r['material']['architecture']='single_material';r['materials'][-1]['name']='preformed Au nanocrystals';r['method']='Seed-mediated growth';self.assertNotEqual(m.classify_record(r,'CdSe')['kind'],'processing')
 def test_explicit_symbol_elemental_precursor_synonyms_are_fixed_not_substring_guesses(self):
  r=record(metal='Cd oxide',nonmetal='S elemental precursor');self.assertEqual(m.classify_record(r,'CdS')['metal_source'],'CdO');self.assertEqual(m.classify_record(r,'CdS')['nonmetal_source'],'S')
 def test_known_full_name_and_matching_abbreviation_plus_typed_solute_feed(self):
  r=record(nonmetal='Trioctylphosphine selenide (TOPSe)');r['materials'][1].update(role='selenium precursor solute',formula='C24H51PSe');r['materials'].append(mat('inventory','Selenium shot','source-listed selenium starting reagent; inventory only','Se'))
  c=m.classify_record(r,'CdSe');self.assertEqual(c['nonmetal_source'],'Se/TOP feed')
  for role in ['selenium precursor feed','chalcogen precursor component','selenium stock component']:
   r['materials'][1]['role']=role;self.assertEqual(m.classify_record(r,'CdSe')['nonmetal_source'],'Se/TOP feed')
 def test_mismatched_abbreviation_and_empirical_formula_do_not_create_identity(self):
  r=record(nonmetal='Cadmium oxide (CdCl2)');self.assertEqual(m.classify_record(r,'CdSe')['kind'],'other')
  r=record(nonmetal='Unspecified compound');r['materials'][1].update(role='reagent',formula='C24H51PSe');self.assertEqual(m.classify_record(r,'CdSe')['kind'],'other')
 def test_explicit_inventory_only_source_is_excluded_even_if_known(self):
  r=record(nonmetal='Unknown reagent');r['materials'][1]['role']='reagent';r['materials'].append(mat('unused','Selenium shot','inventory-only selenium precursor','Se'))
  self.assertEqual(m.classify_record(r,'CdSe')['kind'],'other')
 def test_source_prefixed_single_unambiguous_route_phrase_is_grouped(self):
  r=record(route='Cd-stearate/TOPSe hot injection; para-aniline exposure; source-defined observation')
  self.assertEqual(m.classify_record(r,'CdSe')['route'],'Hot injection')
  self.assertEqual(r['method'],'Cd-stearate/TOPSe hot injection; para-aniline exposure; source-defined observation')
 def test_conflicting_negated_or_comparative_routes_are_not_canonicalized(self):
  for label in ['Hot injection or heat-up','Not hot injection','Heat-up compared with hot injection','Unlike hot injection, a different method','Avoid hot injection; use another approach']:
   self.assertEqual(m.classify_record(record(route=label),'CdSe')['kind'],'other',label)
  self.assertEqual(m.classify_record(record(route='Molecular beam epitaxy (MBE)'),'CdSe')['route'],'Molecular beam epitaxy')
 def test_remaining_ties_preserve_the_supplied_current_order_not_record_id(self):
  g=m.build_method_families([record('z-last-lexically'),record('a-first-lexically')],'CdSe')
  self.assertEqual(g['families'][0]['papers'][0]['record_ids'],['z-last-lexically','a-first-lexically']);self.assertEqual(g['default_record_id'],'z-last-lexically')
 def test_explicit_named_feed_wins_over_elemental_formula(self):
  for name in ['Se-TOP','selenium in TOP','Selenium/TOP solution']:
   r=record(nonmetal=name);r['materials'][1]['formula']='Se';self.assertEqual(m.classify_record(r,'CdSe')['nonmetal_source'],'Se/TOP feed')
  r=record(nonmetal='Selenium in unspecified carrier');r['materials'][1]['formula']='Se';self.assertEqual(m.classify_record(r,'CdSe')['kind'],'other')
 def test_own_prepare_to_inject_link_proves_feed_without_stock_or_carried_state_expansion(self):
  r=record(nonmetal='selenium');r['materials'].append(mat('top','trioctylphosphine','ligand'));r['material_states']=[{'id':'prior','parent_ids':['metal']}]
  r['operations']=[{'id':'prep','stage':'synthesis','action':'prepare','label':'Preparing Se precursor','inputs':['prior','nonmetal','top'],'outputs':['feed']},{'id':'inj','stage':'synthesis','action':'inject','label':'Injecting Se precursor into Cd mixture','inputs':['feed'],'outputs':['product']}]
  self.assertEqual(m.classify_record(r,'CdSe')['nonmetal_source'],'Se/TOP feed')
  r['operations'][1]['inputs']=['nonmetal'];self.assertEqual(m.classify_record(r,'CdSe')['nonmetal_source'],'Se')
 def test_copresence_or_general_reaction_mix_does_not_prove_a_feed(self):
  r=record(nonmetal='selenium');r['materials'].append(mat('top','TOP','solvent'));r['operations'][0].update(action='mix',label='Mix reaction mixture',inputs=['metal','nonmetal','top'],outputs=['feed'])
  r['operations'].append({'id':'inject','stage':'synthesis','action':'inject','label':'Inject Se precursor','inputs':['feed']})
  self.assertEqual(m.classify_record(r,'CdSe')['nonmetal_source'],'Se')
 def test_competing_phosphine_cannot_be_hidden_as_a_diluent(self):
  r=record(nonmetal='selenium');r['materials'] += [mat('top','TOP','solvent'),mat('tbp','Tributylphosphine','solvent')];r['stocks']=[{'id':'stock','name':'Mixed phosphine stock','components':[{'material_id':'nonmetal'},{'material_id':'top'},{'material_id':'tbp'}]}];r['operations'][0]['inputs']=['metal','stock']
  self.assertEqual(m.classify_record(r,'CdSe')['reason'],'nonmetal_ambiguous_named_stock_feeds')
 def test_core_shell_explicit_overgrowth_with_consumed_typed_seed_stock_is_processing(self):
  r=record(route='Seeded ZnS overgrowth in TOPO/TOP');r['material']['architecture']='core_shell';r['materials'].append(mat('given','TOPO/TOP-capped CdSe seeds dispersed in hexane','seed'));r['stocks']=[{'id':'seed-stock','name':'Reported seed stock','components':[{'material_id':'given'}]}];r['operations'][0]['inputs'].append('seed-stock')
  self.assertEqual(m.classify_record(r,'ZnS')['kind'],'processing')
  r['operations'][0]['inputs'].remove('seed-stock');self.assertNotEqual(m.classify_record(r,'ZnS')['kind'],'processing')
  r['material']['architecture']='single_material';r['method']='Seed-mediated Au growth';r['operations'][0]['inputs'].append('seed-stock');self.assertNotEqual(m.classify_record(r,'Au')['kind'],'processing')
if __name__=='__main__':unittest.main(verbosity=2)
