"""Synthetic metadata fixtures; direct Ge never changes historical reviewed routes."""
import ast,copy,json,unittest
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


class DialysisIsolation(unittest.TestCase):
    def setUp(self):
        self.byid, self.hub = fixtures()
        r = self.byid[DIRECT]
        r['method'] = 'Synthesis as described in the source'
        state = DIRECT + '--after-s01-dialyze'
        evidence = lambda page: [{'source_id': DIRECT, 'locator': 'Main PDF p.' + str(page)}]
        r['material_states'] = [{'id': state, 'kind': 'product'}]
        r['operations'] = [{'action': 'dialyze', 'stage': 'synthesis', 'outputs': [state],
                            'evidence': evidence(2), 'parameters': {'duration': {
                                'value': 3, 'unit': 'day', 'status': 'reported', 'evidence': evidence(2)}}}]
        r['products'] = [{'source_sample_label': 'PVP-GeQDs', 'material_state_id': state,
                          'recipe_link': 'explicit', 'link_evidence': evidence(2),
                          'composition': {'value': 'Ge', 'status': 'reported', 'evidence': evidence(1)}}]
    def passes(self):
        return all(ok for ok, _ in Q['germanium_reviewed_regression_checks'](self.hub, self.byid))
    def test_four_labels_accept_source_bound_isolation_without_mutation(self):
        for label in ['PVP-GeQDs', 'PPA-GeQDs', 'ANI-GeQDs', 'BNA-GeQDs']:
            self.byid[DIRECT]['products'][0]['source_sample_label'] = label
            before = copy.deepcopy((self.byid, self.hub))
            with self.subTest(label=label):
                self.assertTrue(self.passes()); self.assertEqual((self.byid, self.hub), before)
    def test_known_method_GeQDs_needs_no_fallback(self):
        r = self.byid[DIRECT]; r['method'] = 'Microwave'
        r.pop('material_states'); r['operations'] = [{'stage': 'synthesis'}]
        r['products'][0].pop('link_evidence'); self.assertTrue(self.passes())
    def test_only_exact_generic_placeholder_uses_isolation(self):
        for method in ['Chemical reduction', 'Ion implantation', 'Milling', 'Microwave deposition', '', 'Synthesis as described elsewhere']:
            self.byid[DIRECT]['method'] = method
            with self.subTest(method=method): self.assertFalse(self.passes())
    def test_exact_GeQDs_token_and_every_context_guard(self):
        for label in ['Ge', 'Ge CQDs', 'Ge QDs', 'GeQDsfilm', 'xGeQDs', 'GeQD'] + ['GeQDs ' + w for w in ['embedded','matrix','substrate','supported','film','device','implant','well']]:
            self.byid[DIRECT]['products'][0]['source_sample_label'] = label
            with self.subTest(label=label): self.assertFalse(self.passes())
    def test_reported_single_Ge_material_and_product_still_required(self):
        r = self.byid[DIRECT]
        for key, value in [('formula','GeO2'), ('components',['Ge','SiO2']), ('elements',['Ge','O']), ('architecture','composite')]:
            old = copy.deepcopy(r['material']); r['material'][key] = value
            with self.subTest(key=key): self.assertFalse(self.passes())
            r['material'] = old
        for key, value in [('value','GeO2'), ('status','inferred')]:
            old = copy.deepcopy(r['products'][0]['composition']); r['products'][0]['composition'][key] = value
            with self.subTest(key=key): self.assertFalse(self.passes())
            r['products'][0]['composition'] = old
    def test_all_four_evidence_sites_are_required_and_same_source(self):
        r = self.byid[DIRECT]
        sites = [(r['operations'][0], 'evidence'), (r['operations'][0]['parameters']['duration'], 'evidence'),
                 (r['products'][0], 'link_evidence'), (r['products'][0]['composition'], 'evidence')]
        for owner, key in sites:
            old = copy.deepcopy(owner[key])
            for bad in [None, [], {}, [{'source_id':'other', 'locator':'Main PDF p.2'}],
                        [{'source_id':DIRECT, 'locator':'Main PDF'}], [{'source_id':DIRECT, 'locator':'Main PDF p.0'}],
                        [{'source_id':DIRECT, 'locator':''}], old + [{'source_id':'other', 'locator':'Main PDF p.2'}]]:
                owner[key] = bad
                with self.subTest(key=key, bad=bad): self.assertFalse(self.passes())
            owner[key] = old
    def test_primary_source_must_exist_uniquely(self):
        r = self.byid[DIRECT]; old = copy.deepcopy(r['sources'])
        for sources in [[], [{'id':'other'}], old + old]:
            r['sources'] = sources
            with self.subTest(sources=sources): self.assertFalse(self.passes())
        r['sources'] = old; r['lineage']['source_group'] = 'other'; self.assertFalse(self.passes())
    def test_duration_must_be_positive_finite_reported_time(self):
        d = self.byid[DIRECT]['operations'][0]['parameters']['duration']; original = copy.deepcopy(d)
        for key, value in [('value',0), ('value',-1), ('value',True), ('value',float('nan')), ('value',float('inf')),
                           ('value','3'), ('status','inferred'), ('status','not_reported'), ('unit','mg'), ('unit','')]:
            d.clear(); d.update(copy.deepcopy(original)); d[key] = value
            with self.subTest(key=key, value=value): self.assertFalse(self.passes())
    def test_dialysis_action_and_producer_stage_are_explicit(self):
        op = self.byid[DIRECT]['operations'][0]
        for stage in ['synthesis', 'workup']:
            op['stage'] = stage
            with self.subTest(stage=stage): self.assertTrue(self.passes())
        for stage in ['characterization', '', None]:
            op['stage'] = stage
            with self.subTest(stage=stage): self.assertFalse(self.passes())
        op['stage'] = 'synthesis'
        for action in ['wash', 'dialysis', 'dialyze sample', '', None]:
            op['action'] = action
            with self.subTest(action=action): self.assertFalse(self.passes())
    def test_output_must_identify_unique_declared_product_state(self):
        r = self.byid[DIRECT]; op = r['operations'][0]; state = r['products'][0]['material_state_id']
        for outputs in [[], ['other'], state, [state,state]]:
            op['outputs'] = outputs
            with self.subTest(outputs=outputs): self.assertFalse(self.passes())
        op['outputs'] = [state]
        for states in [[], [{'id':'other','kind':'product'}], [{'id':state,'kind':'reaction_batch'}],
                       [{'id':state,'kind':'product'}, {'id':state,'kind':'product'}]]:
            r['material_states'] = states
            with self.subTest(states=states): self.assertFalse(self.passes())
    def test_explicit_product_recipe_link_required(self):
        p = self.byid[DIRECT]['products'][0]
        for link in ['inferred','unmatched','',None]:
            p['recipe_link'] = link
            with self.subTest(link=link): self.assertFalse(self.passes())
    def test_every_product_needs_own_positive_isolation_proof(self):
        r = self.byid[DIRECT]; other = copy.deepcopy(r['products'][0]); other['material_state_id'] = 'unlinked'
        r['products'].append(other); self.assertFalse(self.passes())
    def test_no_DOI_or_record_ID_exception(self):
        r = self.byid.pop(DIRECT); new = 'different-synthetic-isolated-Ge'
        r['record_id'] = new; r['sources'][0]['doi'] = '10.synthetic/not-a-real-paper'
        self.byid[new] = r; self.hub['record_ids'].remove(DIRECT); self.hub['record_ids'].append(new); self.hub['direct_record_ids'] = [new]
        self.assertTrue(self.passes())
    def test_reviewed_Heath_scope_cannot_be_changed_by_isolation(self):
        rid = next(iter(HEATH)); self.byid[rid] = copy.deepcopy(self.byid[DIRECT]); self.byid[rid]['record_id'] = rid
        self.hub['direct_record_ids'].append(rid)
        checks = [ok for ok, _ in Q['germanium_reviewed_regression_checks'](self.hub, self.byid)]
        self.assertFalse(checks[0]); self.assertFalse(checks[1])

class NonSolutionParticleProof(unittest.TestCase):
    def setUp(self):
        self.byid, self.hub = fixtures()

    def route(self, mode):
        r = self.byid[DIRECT]
        evidence = lambda page: [{'source_id': DIRECT, 'locator': 'Main PDF p.' + str(page)}]
        final = DIRECT + '--product'
        r['products'] = [{'source_sample_label': 'Ge nanocrystals', 'material_state_id': final,
                          'recipe_link': 'explicit', 'link_evidence': evidence(2),
                          'composition': {'value': 'Ge', 'status': 'reported', 'evidence': evidence(1)},
                          'notes': []}]
        r['material_states'] = [{'id': final, 'kind': 'product'}]
        if mode in ('gas', 'laser'):
            r['method'] = 'Gas-phase condensation' if mode == 'gas' else 'Pulsed laser ablation'
            r['operations'] = [{'action': 'condense' if mode == 'gas' else 'ablate',
                                'stage': 'synthesis', 'inputs': [DIRECT + '--Ge-feed'],
                                'outputs': [final], 'evidence': evidence(2)}]
        elif mode == 'plasma-dissociate':
            mid = DIRECT + '--plasma-batch'
            r['method'] = 'Plasma synthesis'
            r['products'][0]['notes'] = ['Reactor: plasma reactor (Main PDF p.1).']
            r['material_states'].insert(0, {'id': mid, 'kind': 'reaction_batch'})
            r['operations'] = [
                {'action': 'dissociate', 'stage': 'synthesis', 'inputs': [DIRECT + '--Ge-feed'],
                 'outputs': [mid], 'evidence': evidence(1)},
                {'action': 'collect', 'stage': 'workup', 'inputs': [mid],
                 'outputs': [final], 'evidence': evidence(2)}]
        elif mode == 'plasma-colloid':
            mids = [DIRECT + '--collected', DIRECT + '--refluxed', DIRECT + '--dried']
            r['method'] = 'Nonthermal plasma'
            r['products'][0]['notes'] = ['Reactor: flow-through plasma reactor (Main PDF p.2).']
            r['material_states'] = [{'id': s, 'kind': 'reaction_batch'} for s in mids] + r['material_states']
            r['operations'] = [
                {'action': 'collect', 'stage': 'workup', 'inputs': [], 'outputs': [mids[0]],
                 'evidence': evidence(2), 'parameters': {'duration': {
                     'value': 5, 'unit': 'min', 'status': 'reported', 'evidence': evidence(2)}}},
                {'action': 'reflux', 'stage': 'synthesis', 'inputs': [mids[0], DIRECT + '--ligand'],
                 'outputs': [mids[1]], 'evidence': evidence(2)},
                {'action': 'dry', 'stage': 'workup', 'inputs': [mids[1]],
                 'outputs': [mids[2]], 'evidence': evidence(2)},
                {'action': 'filter', 'stage': 'workup', 'inputs': [mids[2]],
                 'outputs': [final], 'evidence': evidence(2)}]
        return r

    def passes(self):
        return all(ok for ok, _ in Q['germanium_reviewed_regression_checks'](self.hub, self.byid))

    def test_source_bound_non_solution_modes_do_not_mutate_records_or_reviewed_scope(self):
        for mode in ('gas', 'plasma-dissociate', 'plasma-colloid', 'laser'):
            self.route(mode)
            before = copy.deepcopy((self.byid, self.hub))
            with self.subTest(mode=mode):
                self.assertTrue(self.passes())
                self.assertEqual((self.byid, self.hub), before)

    def test_unlinked_ambiguous_cyclic_or_unlocated_producer_is_not_proof(self):
        def duplicate_producer(r): r['operations'].append(copy.deepcopy(r['operations'][0]))
        def cycle(r): r['operations'][0]['inputs'] = [r['products'][0]['material_state_id']]
        mutations = [
            lambda r: r['products'][0].update(recipe_link='inferred'),
            lambda r: r['products'][0].update(link_evidence=[]),
            lambda r: r['products'][0]['composition'].update(evidence=[{'source_id':'other','locator':'Main PDF p.1'}]),
            lambda r: r['material_states'][0].update(kind='reaction_batch'),
            lambda r: r['operations'][0].update(outputs=['unlinked']),
            lambda r: r['operations'][0].update(stage='characterization'),
            lambda r: r['operations'][0].update(evidence=[{'source_id':DIRECT,'locator':'Main PDF'}]),
            duplicate_producer, cycle,
        ]
        for mutate in mutations:
            r = self.route('gas'); mutate(r)
            with self.subTest(mutation=mutate): self.assertFalse(self.passes())

    def test_plasma_needs_its_source_bound_reactor_and_connected_collection(self):
        for mode in ('plasma-dissociate', 'plasma-colloid'):
            for notes in [[], ['Reactor: plasma reactor'], ['Reactor: plasma reactor (Main PDF p.99).'],
                          ['Reactor: non-plasma reactor (Main PDF p.2).']]:
                r = self.route(mode); r['products'][0]['notes'] = notes
                with self.subTest(mode=mode, notes=notes): self.assertFalse(self.passes())
        for value in [0, -1, True, float('inf'), float('nan')]:
            r = self.route('plasma-colloid'); r['operations'][0]['parameters']['duration']['value'] = value
            with self.subTest(duration=value): self.assertFalse(self.passes())
        r = self.route('plasma-dissociate'); r['operations'][-1]['inputs'] = []
        self.assertFalse(self.passes())

    def test_method_name_or_precursor_preparation_alone_stays_held(self):
        for method in ['Gas-phase condensation', 'Pulsed laser ablation', 'Nonthermal plasma',
                       'Plasma synthesis', 'Naphthalide-mediated reduction']:
            r = self.route('gas'); r['method'] = method
            r['operations'][0].update(action='dissolve', inputs=[DIRECT+'--sodium', DIRECT+'--naphthalene'])
            r['products'][0]['source_sample_label'] = 'ST12-Ge (nanocrystalline)'
            with self.subTest(method=method): self.assertFalse(self.passes())

    def test_new_proof_keeps_existing_particle_and_component_protections(self):
        for label in ['Ge', 'Ge nanocrystals embedded in SiO2', 'Ge quantum dot substrate film']:
            r = self.route('gas'); r['products'][0]['source_sample_label'] = label
            with self.subTest(label=label): self.assertFalse(self.passes())
        r = self.route('gas'); r['material']['architecture'] = 'composite'
        self.assertFalse(self.passes())
        r = self.route('gas'); r['material']['architecture'] = 'single_material'
        r['products'][0]['composition']['status'] = 'inferred'
        self.assertFalse(self.passes())


class EtchIsolation(unittest.TestCase):
    """Use the complete committed Lai record; mutations never change its file."""
    def setUp(self):
        self.byid, self.hub = fixtures()
        path = Path(__file__).resolve().parents[1] / 'data/records/lai2025-jacs-5c00423-dc-geqds-1.json'
        self.actual = json.loads(path.read_bytes())
        self.byid.pop(DIRECT)
        self.rid = self.actual['record_id']
        self.byid[self.rid] = copy.deepcopy(self.actual)
        self.hub['record_ids'].remove(DIRECT)
        self.hub['record_ids'].append(self.rid)
        self.hub['direct_record_ids'] = [self.rid]

    def fresh(self):
        self.byid[self.rid] = copy.deepcopy(self.actual)
        return self.byid[self.rid]

    def passes(self):
        return all(ok for ok, _ in Q['germanium_reviewed_regression_checks'](self.hub, self.byid))

    def test_actual_full_record_passes_without_mutation_or_filling_unknowns(self):
        before = copy.deepcopy((self.byid, self.hub))
        self.assertEqual(self.actual['method'], 'Synthesis as described in the source')
        self.assertIsNone(self.actual['products'][0]['morphology']['value'])
        self.assertTrue(self.passes())
        self.assertEqual((self.byid, self.hub), before)

    def test_isolation_wording_is_positive_and_explicit_in_both_fields(self):
        for key in ('label', 'description'):
            for text in ['', 'HF-etching', 'HF-etching to isolate GeQDs',
                         'Etching to isolate freestanding GeQDs',
                         'HF-etching did not isolate freestanding GeQDs',
                         'HF-etching failed to isolate freestanding GeQDs',
                         'HF-etching to isolate freestanding GeQDs was proposed',
                         'HF-etching to isolate freestanding GeQDs from precursors only']:
                r = self.fresh(); r['operations'][1][key] = text
                with self.subTest(key=key, text=text): self.assertFalse(self.passes())

    def test_all_evidence_is_same_source_and_physically_located(self):
        selectors = [lambda r: (r['products'][0], 'link_evidence'),
                     lambda r: (r['products'][0]['composition'], 'evidence'),
                     lambda r: (r['products'][0]['phase'], 'evidence'),
                     lambda r: (r['products'][0]['surface'], 'evidence'),
                     lambda r: (r['operations'][0], 'evidence'),
                     lambda r: (r['operations'][0]['parameters']['temperature'], 'evidence'),
                     lambda r: (r['operations'][1], 'evidence'),
                     lambda r: (r['operations'][2], 'evidence')]
        for select in selectors:
            for bad in [None, [], [{'source_id':'wrong', 'locator':'Main PDF p.2'}],
                        [{'source_id':self.actual['lineage']['source_group'], 'locator':'Main PDF'}],
                        [{'source_id':self.actual['lineage']['source_group'], 'locator':'Main PDF p.0'}]]:
                r = self.fresh(); owner, key = select(r); owner[key] = bad
                with self.subTest(select=select, bad=bad): self.assertFalse(self.passes())

    def test_wrong_page_cannot_supply_formation_etch_or_surface_corroboration(self):
        for select in [lambda r: r['operations'][0],
                       lambda r: r['operations'][0]['parameters']['temperature'],
                       lambda r: r['operations'][1], lambda r: r['operations'][2],
                       lambda r: r['products'][0]['phase'], lambda r: r['products'][0]['surface']]:
            r = self.fresh(); select(r)['evidence'][0]['locator'] = 'Main PDF p.99'
            with self.subTest(select=select): self.assertFalse(self.passes())

    def test_chain_rejects_disconnect_cycle_duplicate_producer_or_state(self):
        def disconnect(r):
            r['operations'][2]['inputs'] = [r['material_states'][0]['id']]
            r['material_states'][2]['parent_ids'] = r['operations'][2]['inputs'][:]
        def cycle(r):
            r['operations'][0]['inputs'] = [r['material_states'][2]['id']]
            r['material_states'][0]['parent_ids'] = r['operations'][0]['inputs'][:]
        for mutate in [disconnect, cycle,
                       lambda r: r['operations'].append(copy.deepcopy(r['operations'][1])),
                       lambda r: r['material_states'].append(copy.deepcopy(r['material_states'][1])),
                       lambda r: r['operations'][1]['outputs'].append(r['material_states'][1]['id']),
                       lambda r: r['operations'][1].update(outputs=['disconnected']),
                       lambda r: r['material_states'][1].update(parent_ids=[]),
                       lambda r: r['operations'][2].update(id=r['operations'][1]['id'])]:
            r = self.fresh(); mutate(r)
            with self.subTest(mutate=mutate): self.assertFalse(self.passes())

    def test_formation_and_only_surface_finishing_are_required(self):
        for mutate in [lambda r: r['operations'][0].update(action='dissolve'),
                       lambda r: r['operations'][0].update(stage='characterization'),
                       lambda r: r['operations'][1].update(action='wash'),
                       lambda r: r['operations'][1].update(optional=True),
                       lambda r: r['operations'][2].update(action='deposit'),
                       lambda r: r['operations'][2].update(description='Surface functionalization into an embedded film')]:
            r = self.fresh(); mutate(r)
            with self.subTest(mutate=mutate): self.assertFalse(self.passes())
        for key, value in [('value', 0), ('value', True), ('value', float('nan')), ('value', float('inf')),
                           ('status', 'inferred'), ('unit', 'mg')]:
            r = self.fresh(); r['operations'][0]['parameters']['temperature'][key] = value
            with self.subTest(key=key, value=value): self.assertFalse(self.passes())

    def test_generic_method_only_and_unchanged_identity_product_guards(self):
        for method in ['Milling', 'Chemical reduction', 'Ion implantation', '']:
            r = self.fresh(); r['method'] = method
            with self.subTest(method=method): self.assertFalse(self.passes())
        for label in ['Ge', 'GeQDsfilm', 'GeQDs precursor only', 'GeQDs film', 'GeQDs embedded in SiO2']:
            r = self.fresh(); r['products'][0]['source_sample_label'] = label
            if label == 'GeQDs precursor only':
                r['operations'][1]['description'] = 'HF-etching to isolate freestanding GeQDs precursor only'
            with self.subTest(label=label): self.assertFalse(self.passes())
        for key, value in [('formula', 'GeO2'), ('components', ['Ge','SiO2']),
                           ('elements', ['Ge','O']), ('architecture', 'composite')]:
            r = self.fresh(); r['material'][key] = value
            with self.subTest(key=key): self.assertFalse(self.passes())
        for mutate in [lambda r: r['products'][0].update(recipe_link='inferred'),
                       lambda r: r['products'][0]['composition'].update(status='inferred'),
                       lambda r: r['material_states'][2].update(kind='reaction_batch'),
                       lambda r: r['sources'].append(copy.deepcopy(r['sources'][0]))]:
            r = self.fresh(); mutate(r)
            with self.subTest(mutate=mutate): self.assertFalse(self.passes())

    def test_each_product_needs_own_proof_and_no_DOI_or_record_ID_allowlist(self):
        r = self.fresh(); other = copy.deepcopy(r['products'][0]); other['material_state_id'] = 'unlinked'
        r['products'].append(other); self.assertFalse(self.passes())
        r = self.fresh(); r['sources'][0]['doi'] = '10.synthetic/different-paper'
        new_id = 'unlisted-source-bound-isolation'
        self.byid.pop(self.rid); r['record_id'] = new_id; self.byid[new_id] = r
        self.hub['record_ids'].remove(self.rid); self.hub['record_ids'].append(new_id)
        self.hub['direct_record_ids'] = [new_id]
        self.assertTrue(self.passes())


if __name__=='__main__':unittest.main()
