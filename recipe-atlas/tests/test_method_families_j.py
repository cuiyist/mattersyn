"""J grouping behavior only; synthetic records, no papers/network/models."""
import copy,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import method_families as m
from test_method_families import record,mat

class JGroupingTest(unittest.TestCase):
 def test_fixed_combined_route_classes_and_no_free_text_family_class(self):
  cases={'Non-injection one-pot':'Heat-up','one-pot hot-injection':'Hot injection','microwave-assisted hydrothermal':'Microwave','SILAR shell growth':'SILAR','Hydrothermal at source conditions':'Solvothermal or hydrothermal','Solvothermal':'Solvothermal or hydrothermal','Aqueous precipitation':'Aqueous or colloidal precipitation','Colloidal route':'Aqueous or colloidal precipitation','MOCVD':'Chemical vapour deposition','Metalorganic vapor-phase epitaxy':'Chemical vapour deposition','Electrodeposition':'Electrochemical','Microwave synthesis':'Microwave','Solid-state synthesis':'Solid state','PLD':'Other vapour or physical deposition','Brust method':'Brust','Citrate reduction':'Turkevich/citrate reduction'}
  for text,want in cases.items():self.assertEqual(m.route_class(text),want,text)
  self.assertEqual(m.route_class('A source-specific descriptive procedure'),'')
  self.assertEqual(m.classify_record(record(route='An unknown route label'),'CdSe')['label'],'Other methods')
 def test_negated_competing_routes_are_not_promoted(self):
  for text in ('Not hot injection','Hot injection or heat-up','Unlike MBE, another process','Avoid sol-gel'):
   self.assertEqual(m.route_class(text),'',text)
 def test_j2_compound_synonyms_and_hydrates_merge(self):
  for spellings in [('Me2Cd','CdMe2','dimethylcadmium'),('Cd acetate','Cd acetate dihydrate','Cd(Ac)2'),('HAuCl4','HAuCl4\u00b73H2O','chloroauric acid trihydrate'),('cadmium myristate','Cadmium myristate')]:
   keys={m.source_identity(mat('m',name,'metal_precursor'))['key']for name in spellings}
   self.assertEqual(len(keys),1,spellings)
 def test_j3_feed_folding_changes_only_family_identity(self):
  rows=[]
  for i,name in enumerate(('Se','TOP-Se','TBP-Se','Se in ODE','Se/TOP feed','selenium shots')):
   row=record(str(i),doi='10.1/'+str(i),nonmetal=name);rows.append(row)
  before=copy.deepcopy(rows);families=m.build_method_families(rows,'CdSe',identity_context={})
  self.assertEqual(len(families['families']),1);self.assertEqual(families['families'][0]['paper_count'],6)
  self.assertEqual(families['families'][0]['label'],'Hot injection - CdO + Se');self.assertEqual(rows,before)
  self.assertNotEqual(m.classify_record(record(nonmetal='(TMS)2Se'),'CdSe')['key'],m.classify_record(record(nonmetal='Se'),'CdSe')['key'])
  for name in ('(TMS)2S','thiourea','Na2S'):
   row=record(nonmetal=name);row['material']['formula']='CdS'
   self.assertNotEqual(m.classify_record(row,'CdS')['nonmetal_source'],'S')
 def test_route_only_survives_missing_source_while_unknown_route_is_other(self):
  row=record(metal='Unspecified precursor',route='MBE');row['material']['formula']='InAs'
  self.assertEqual(m.classify_record(row,'InAs')['label'],'Molecular beam epitaxy, sources not listed')
  row['method']='Unknown route';self.assertEqual(m.classify_record(row,'InAs')['kind'],'other')
 def test_reported_own_system_recovers_route_without_paper_or_collection_text(self):
  row=record(route='Supporting procedure');row['operations'][0]['vessel']='Molecular-beam epitaxy system'
  self.assertEqual(m.route(row),'Molecular beam epitaxy')
  row['operations'][0].pop('vessel');row['title']='MBE title';row['material']['family']='MBE collection'
  self.assertEqual(m.route(row),'')
 def test_single_paper_source_families_fold_by_distinct_paper_not_variant_count(self):
  rows=[record('a'+str(i),metal='Cd metal')for i in range(6)]+[record('b',doi='10.1/b',metal='Cd acetate')]
  out=m.build_method_families(rows,'CdSe',identity_context={})
  self.assertEqual(len(out['families']),1);self.assertEqual(out['families'][0]['label'],'Hot injection, other sources');self.assertEqual(out['families'][0]['paper_count'],2)
 def test_folded_ties_keep_original_input_order(self):
  rows=[record('a1',metal='Cd metal'),record('b',metal='Cd acetate'),record('a2',metal='Cd metal')]
  out=m.build_method_families(rows,'CdSe',identity_context={})
  self.assertEqual(out['families'][0]['papers'][0]['record_ids'],['a1','b','a2'])
 def test_own_product_before_larger_component_then_processing(self):
  own=record('own',doi='10.1/own');own['material'].update(formula='ZnS',components=['ZnS'],architecture='single_material');own['materials'][0]['name']='ZnO';own['materials'][1]['name']='S'
  components=[]
  for i in range(3):
   row=record('component'+str(i),doi='10.1/c'+str(i));row['material'].update(formula='CdSe/ZnS',components=['CdSe','ZnS'],architecture='unresolved');components.append(row)
  processing=copy.deepcopy(own);processing['record_id']='processed';processing['method']='Ligand exchange';processing['materials'].append(mat('given','preformed ZnS nanocrystals','seed'));processing['operations'][0]['inputs'].append('given')
  out=m.build_method_families(components+[processing,own],'ZnS',identity_context={})
  self.assertEqual([f['kind']for f in out['families']],['synthesis','component','processing']);self.assertEqual(out['default_record_id'],'own')
  self.assertEqual(m.build_method_families(components,'ZnS',identity_context={})['families'][0]['kind'],'component')
 def test_final_product_not_collection_family_controls_component(self):
  row=record();row['material'].update(formula='CdSe',components=['CdSe'],architecture='single_material',family='CdSe/CdS dots and complexes')
  self.assertFalse(m.component_product(row,'CdSe'))
  row['products']=[{'composition':{'status':'reported','value':'CdSe/ZnS'}}]
  self.assertTrue(m.component_product(row,'CdSe'))
 def test_rejected_explicit_route_never_recovers_from_system_fallback(self):
  row=record(route='Not MBE');row['operations'][0]['vessel']='Molecular beam epitaxy system'
  self.assertEqual(m.route(row),'')
  row['method']='Hot injection or heat-up';self.assertEqual(m.route(row),'')
 def test_named_route_cannot_override_other_explicit_class(self):
  self.assertEqual(m.route_class('Chemical reduction or MBE'),'')
  self.assertEqual(m.route_class('Brust aqueous reduction'),'Brust')
  self.assertEqual(m.route_class('Chemical bath deposition (CBD)'),'Chemical bath deposition')
  self.assertEqual(m.route_class('Microfluidic'),'Microfluidic')
 def test_generic_reagent_role_hydrate_resolves_same_fixed_compound(self):
  row=record(metal='zinc acetate dihydrate',nonmetal='S');row['material']['formula']='ZnS';row['materials'][0]['role']='reagent'
  self.assertEqual(m.classify_record(row,'ZnS')['metal_source'],'Zn acetate')
  self.assertEqual(m.fixed_source_identity(mat('m','Reagent A','reagent','Zn(C2H3O2)2.2H2O'))['label'],'Zn acetate')
 def test_equivalent_formula_order_is_not_component_evidence(self):
  row=record();row['material'].update(formula='AsIn',components=['InAs'],architecture='single_material')
  row['products']=[{'composition':{'status':'reported','value':'AsIn'}}]
  self.assertFalse(m.component_product(row,'InAs'))
  row['material'].update(formula='InAs/GaAs',components=['InAs','GaAs'],architecture='heterostructure');self.assertTrue(m.component_product(row,'InAs'))
 def test_fallback_aggregates_reported_systems_and_rejects_cross_field_conflict(self):
  row=record(route='Supporting procedure');row['operations'][0]['vessel']='Molecular beam epitaxy system'
  row['operations'][0]['environment']={'status':'reported','value':'MOCVD system'}
  self.assertEqual(m.route(row),'')
  row['method']='Other';self.assertEqual(m.route(row),'')
  row['operations'][0]['environment']={'status':'not_reported'};self.assertEqual(m.route(row),'Molecular beam epitaxy')
 def test_h_pinned_synonym_index_uses_whole_compound_not_ligand_reference(self):
  registry={'entries':[{'id':'old','name':'Own exact compound','formula':'CdCl2','pubchemCid':123},{'id':'ligand','name':'Unrelated ligand','pubchemCid':456}]}
  bindings={'recordBindings':{'r':{'m':'old'}}};overlay={'entries':{'old':{'route':'independent_component_references','referenceRegistryId':'ligand'}}}
  context=m.identity_context_from_chemistry(registry,bindings,overlay)
  self.assertEqual(context['r']['m']['key'],'cid:123')
  overlay['entries']['old']={'route':'flat','reason':'identity_conflict'}
  self.assertNotIn('r',m.identity_context_from_chemistry(registry,bindings,overlay))

if __name__=='__main__':unittest.main(verbosity=2)
