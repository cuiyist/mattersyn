"""Synthetic metadata fixtures; direct Ge never changes historical reviewed routes."""
import ast,copy,unittest
from pathlib import Path

def quality():
    path=Path(__file__).resolve().parents[1]/'scripts/check_quality.py';tree=ast.parse(path.read_bytes())
    names={'germanium_reviewed_regression_checks','material_membership_errors','primary_doi','hub_publication_status_matches'}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names]
    nodes += [n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='HEATH_GE_SI_ROUTES'for t in n.targets)]
    env={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env);return env
Q=quality();HEATH=Q['HEATH_GE_SI_ROUTES'];DIRECT='synthetic-direct-Ge';COMPONENT='synthetic-embedded-Ge'

def record(rid,formula,components,architecture,status):
    return {'record_id':rid,'collection':'reviewed_literature','record_type':'literature_protocol','reader_role':'synthesis_route',
            'quality':{'review_status':status,'requested_tasks':[]},'operations':[{'stage':'synthesis'}],
            'material':{'formula':formula,'components':components,'architecture':architecture,'elements':['Ge']if formula=='Ge'else['Ge','Si']},
            'lineage':{'source_group':rid},'sources':[{'id':rid,'doi':'10.synthetic/'+rid}]}

def fixtures():
    rows=[record(r,'Ge/Si',['Ge','Si'],'heterostructure','source_reviewed')for r in sorted(HEATH)]
    rows.append(record(COMPONENT,'Ge/SiO2',['Ge','SiO2'],'composite','source_extracted'))
    direct=record(DIRECT,'Ge',['Ge'],'single_material','source_extracted');direct['method']='Heat-up';direct['products']=[{'source_sample_label':'Ge CQD #1','composition':{'value':'Ge','status':'reported'}}];rows.append(direct)
    hub={'formula':'Ge','record_ids':[r['record_id']for r in rows],'direct_record_ids':[DIRECT],'component_only':False,'paper_dois':[Q['primary_doi'](r)for r in rows],'publication_status':'verified_synthesis_contribution'}
    return {r['record_id']:r for r in rows},hub

class DirectGe(unittest.TestCase):
    def setUp(self):self.byid,self.hub=fixtures()
    def checks(self):return [ok for ok,_ in Q['germanium_reviewed_regression_checks'](self.hub,self.byid)]
    def test_direct_Ge_and_components_coexist(self):
        before=copy.deepcopy((self.byid,self.hub));self.assertTrue(all(self.checks()));self.assertEqual((self.byid,self.hub),before)
        self.assertEqual(Q['material_membership_errors'](self.hub,list(self.byid.values())),[])
    def test_solution_method_and_particle_label_variants(self):
        for method,label in [('Heat-up','Ge CQD #1'),('Hot-injection','Ge nanocrystals'),('Colloidal synthesis','Colloidal Ge quantum dots')]:
            self.byid[DIRECT]['method']=method;self.byid[DIRECT]['products'][0]['source_sample_label']=label
            with self.subTest(method=method,label=label):self.assertTrue(all(self.checks()))
    def microwave(self,label='dodecanethiol-capped Ge NCs'):
        self.byid[DIRECT]['method']='Microwave';self.byid[DIRECT]['products'][0]['source_sample_label']=label
    def test_microwave_exact_NC_and_NCs_tokens(self):
        for label in ['dodecanethiol-capped Ge NCs','Ge NC','Ge nanocrystals']:
            self.microwave(label);before=copy.deepcopy((self.byid,self.hub))
            with self.subTest(label=label):
                self.assertTrue(all(self.checks()));self.assertEqual((self.byid,self.hub),before)
    def test_microwave_NCs_keeps_composition_and_reported_status_guards(self):
        self.microwave()
        for value,status in [('GeO2','reported'),('Ge/Si','reported'),('Ge','inferred'),(None,'not_reported')]:
            self.byid[DIRECT]['products'][0]['composition']={'value':value,'status':status}
            with self.subTest(value=value,status=status):self.assertFalse(all(self.checks()))
    def test_metathesis_hyphenated_nanocrystal_label(self):
        self.byid[DIRECT]['method']='Metathesis'
        self.byid[DIRECT]['products'][0]['source_sample_label']='Rˆ -nc-Ge (methyl-terminated)'
        before=copy.deepcopy((self.byid,self.hub))
        self.assertTrue(all(self.checks()));self.assertEqual((self.byid,self.hub),before)
    def test_metathesis_keeps_product_and_context_guards(self):
        self.byid[DIRECT]['method']='Metathesis'
        for label in ['ncsource-Ge','Ge','R-nc-Ge embedded in matrix','R-nc-Ge substrate film','supported R-nc-Ge device','implanted R-nc-Ge wells']:
            self.byid[DIRECT]['products'][0]['source_sample_label']=label
            with self.subTest(label=label):self.assertFalse(all(self.checks()))
        self.byid[DIRECT]['products'][0]['source_sample_label']='R-nc-Ge'
        for value,status in [('GeO2','reported'),('Ge/Si','reported'),('Ge','inferred'),(None,'not_reported')]:
            self.byid[DIRECT]['products'][0]['composition']={'value':value,'status':status}
            with self.subTest(value=value,status=status):self.assertFalse(all(self.checks()))
    def test_metathesis_keeps_method_and_architecture_guards(self):
        self.byid[DIRECT]['products'][0]['source_sample_label']='R-nc-Ge'
        for method in ['Metathesis deposition','Ion implantation','Milling','']:
            self.byid[DIRECT]['method']=method
            with self.subTest(method=method):self.assertFalse(all(self.checks()))
        self.byid[DIRECT]['method']='Metathesis'
        for key,value in [('formula','GeO2'),('components',['Ge','SiO2']),('elements',['Ge','O']),('architecture','composite')]:
            before=copy.deepcopy(self.byid[DIRECT]['material']);self.byid[DIRECT]['material'][key]=value
            with self.subTest(key=key):self.assertFalse(all(self.checks()))
            self.byid[DIRECT]['material']=before
    def test_microwave_NCs_keeps_material_architecture_guards(self):
        self.microwave()
        for key,value in [('formula','GeO2'),('components',['Ge','SiO2']),('elements',['Ge','O']),('architecture','composite')]:
            before=copy.deepcopy(self.byid[DIRECT]['material']);self.byid[DIRECT]['material'][key]=value
            with self.subTest(key=key):self.assertFalse(all(self.checks()))
            self.byid[DIRECT]['material']=before
    def test_microwave_NCs_keeps_all_context_exclusions(self):
        for word in ['embedded','matrix','substrate','supported','film','device','implant','well']:
            self.microwave('Ge NCs '+word)
            with self.subTest(word=word):self.assertFalse(all(self.checks()))
    def test_microwave_does_not_allow_substrings_or_other_methods(self):
        for label in ['Ge','Ge CDs','Ge ncsource','Ge NCsfilm']:
            self.microwave(label)
            with self.subTest(label=label):self.assertFalse(all(self.checks()))
        self.microwave()
        for method in ['Microwave deposition','Ion implantation','Milling','Synthesis as described in the source']:
            self.byid[DIRECT]['method']=method
            with self.subTest(method=method):self.assertFalse(all(self.checks()))
    def test_no_DOI_or_recordID_allowlist(self):
        other=self.byid.pop(DIRECT);other['record_id']='another-Ge-QD';self.byid[other['record_id']]=other
        self.hub['record_ids'].remove(DIRECT);self.hub['record_ids'].append(other['record_id']);self.hub['direct_record_ids']=[other['record_id']]
        other['sources'][0]['doi']='10.synthetic/a-different-paper';self.assertTrue(all(self.checks()))
    def test_component_only_original_hub_still_passes(self):
        self.byid.pop(DIRECT);self.hub['record_ids'].remove(DIRECT);self.hub.update(direct_record_ids=[],component_only=True);self.assertTrue(all(self.checks()))
    def test_all_material_fields_must_be_consistent(self):
        for key,value in [('formula','GeO2'),('components',['Ge','SiO2']),('elements',['Ge','O']),('architecture','composite')]:
            before=copy.deepcopy(self.byid[DIRECT]['material']);self.byid[DIRECT]['material'][key]=value
            with self.subTest(key=key):self.assertFalse(all(self.checks()))
            self.byid[DIRECT]['material']=before
    def test_wrong_compound_cannot_be_relabelled_direct_Ge(self):
        self.byid[DIRECT]['products'][0]['composition']['value']='GeO2';self.assertFalse(all(self.checks()))
    def test_missing_or_not_reported_product_cannot_establish_direct_Ge(self):
        for mutation in ['no_products','missing_composition','not_reported']:
            original=copy.deepcopy(self.byid[DIRECT]['products'])
            if mutation=='no_products':self.byid[DIRECT]['products']=[]
            elif mutation=='missing_composition':self.byid[DIRECT]['products'][0].pop('composition')
            else:self.byid[DIRECT]['products'][0]['composition']['status']='not_reported'
            with self.subTest(mutation=mutation):self.assertFalse(all(self.checks()))
            self.byid[DIRECT]['products']=original
    def test_embedded_or_device_labels_are_not_free_products(self):
        for label in ['Ge nanocrystals embedded in SiO2','Ge QD matrix','substrate-supported Ge quantum dots','Ge QD film device','Ge implanted QD wells','Ge']:
            self.byid[DIRECT]['products'][0]['source_sample_label']=label
            with self.subTest(label=label):self.assertFalse(all(self.checks()))
    def test_non_solution_method_rejected(self):
        for method in ['Template-confined UHV chemical vapor deposition','Ion implantation','Milling','']:
            self.byid[DIRECT]['method']=method
            with self.subTest(method=method):self.assertFalse(all(self.checks()))
    def test_each_reviewed_Heath_route_can_never_be_direct(self):
        for rid in HEATH:
            self.hub['direct_record_ids']=[rid,DIRECT]
            with self.subTest(rid=rid):self.assertFalse(self.checks()[0])
    def test_Heath_demoted_then_relabelled_direct_still_fails(self):
        rid=next(iter(HEATH));self.byid[rid]=copy.deepcopy(self.byid[DIRECT]);self.byid[rid]['record_id']=rid;self.hub['direct_record_ids'].append(rid)
        self.assertFalse(self.checks()[0]);self.assertFalse(self.checks()[1])
    def test_reviewed_fake_direct_or_extra_reviewed_fails(self):
        self.byid[DIRECT]['quality']['review_status']='source_reviewed';self.assertFalse(self.checks()[0]);self.assertFalse(self.checks()[1])
    def test_hiding_a_direct_product_or_wrong_component_only_fails(self):
        self.hub['direct_record_ids']=[];self.hub['component_only']=True;self.assertFalse(self.checks()[3])
        self.byid,self.hub=fixtures();self.hub['component_only']=True;self.assertFalse(self.checks()[0])
    def test_component_host_architecture_checks_remain(self):
        for key,value in [('components',['Ge']),('architecture','single_material'),('formula','Ge')]:
            old=copy.deepcopy(self.byid[COMPONENT]['material']);self.byid[COMPONENT]['material'][key]=value
            with self.subTest(key=key):self.assertFalse(self.checks()[3])
            self.byid[COMPONENT]['material']=old
    def test_unknown_or_inadmissible_status_fails(self):
        self.hub['record_ids'].append('unknown');self.assertFalse(self.checks()[2]);self.hub['record_ids'].pop()
        self.byid[DIRECT]['quality']['review_status']='draft';self.assertFalse(self.checks()[2])

if __name__=='__main__':unittest.main()
