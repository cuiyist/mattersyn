"""Finite OA/ODE stock cases; synthetic only, no queries or generated assets."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'scripts'))
import chemical_L_identity as rules


def stock(name,**kw):
    return {'id':'stock','name':name,'formula':None,'pubchemCid':None,
            'depictionKind':'formula',**kw}


class NamedStockSolventTests(unittest.TestCase):
    def test_two_reported_concentrations_keep_three_explicit_names_and_original_input(self):
        for concentration in ['0.04','0.5']:
            e=stock(concentration+' M cadmium oleate stock in OA/ODE')
            before=copy.deepcopy(e);p=rules.plan_identity(e)
            self.assertEqual(p['ownerpart'],'L5')
            self.assertEqual([q['name']for q in p['lookups']],['Oleate ion','Oleic acid','1-Octadecene'])
            self.assertEqual([q['formula']for q in p['lookups']],['C18H33O2-','C18H34O2','C18H36'])
            self.assertIn('fixed_named_OA_ODE_stock_solvents',p['transformations'])
            self.assertEqual(p['lookups'][2]['preferred_reference_ids'],['1-octadecene'])
            self.assertEqual(e,before)

    def test_exact_reverse_preserves_reported_component_order(self):
        p=rules.plan_identity(stock('Cadmium oleate stock in ODE/OA'))
        self.assertEqual([q['name']for q in p['lookups']],['Oleate ion','1-Octadecene','Oleic acid'])

    def test_unknown_slash_strings_are_not_split(self):
        for solvent in ['OA/TOP','OA/ODE/hexane','OA / ODE']:
            p=rules.plan_identity(stock('Cadmium oleate stock in '+solvent))
            self.assertNotIn('fixed_named_OA_ODE_stock_solvents',p.get('transformations',[]))
            self.assertEqual(len(p['lookups']),2)
            self.assertEqual(p['lookups'][1]['name'],solvent)

    def test_core_shell_and_specimens_remain_held(self):
        for name in ['CdSe/CdS core/shell stock in OA/ODE',
                     'Cadmium oleate substrate in OA/ODE']:
            self.assertEqual(rules.plan_identity(stock(name))['kind'],'hold')
        direct=rules.plan_identity(stock('OA/ODE'))
        self.assertNotIn('fixed_named_OA_ODE_stock_solvents',direct.get('transformations',[]))

    def test_existing_ode_only_stock_keeps_its_two_component_plan(self):
        p=rules.plan_identity(stock('Cadmium oleate in ODE; solution speciation unresolved'))
        self.assertEqual([q['name']for q in p['lookups']],['Oleate ion','1-Octadecene'])
        self.assertNotIn('fixed_named_OA_ODE_stock_solvents',p['transformations'])
        self.assertEqual(p['default_disclaimer'],rules.DEFAULT_LINE)

    def test_three_existing_references_compose_and_validate_without_ratios_or_whole_stock(self):
        e=stock('0.04 M cadmium oleate stock in OA/ODE');p=rules.plan_identity(e)
        entries={rules.EXISTING_OLEATE_SOURCE['id']:copy.deepcopy(rules.EXISTING_OLEATE_SOURCE)}
        for eid,name,formula,cid in [('oleic-acid','Oleic acid','C18H34O2',None),
                                     ('1-octadecene','1-Octadecene','C18H36',8217)]:
            entries[eid]={'id':eid,'name':name,'formula':formula,'pubchemCid':cid,
                          'model3dPath':'models/'+eid+'.json',
                          'assetHashes':{'model3dPath':'a'*64},
                          'caption':'Existing illustrative independent molecular reference.',
                          'sourceUrls':[]}
        groups=[rules.existing_named_component_group(p['lookups'][0],entries)]
        for lookup,eid in zip(p['lookups'][1:],['oleic-acid','1-octadecene']):
            groups.append({'lookup':lookup,'basis':'existing_registry','registry_id':eid,
                           'reference':rules.registry_group_reference(lookup,eid,entries)})
        ref=rules.compose_L_reference(e,p,groups)
        proof={'schema':rules.SCHEMA,'entry_id':e['id'],'source_entry_sha256':rules.digest(e),
               'plan':p,'groups':groups,'reference_sha256':rules.digest(ref)}
        self.assertEqual(rules.validate_L_reference(e,ref,proof,entries),[])
        self.assertEqual(ref['route'],'independent_component_references')
        self.assertEqual([c['formula']for c in ref['component3dModels']],['C18H33O2-','C18H34O2','C18H36'])
        self.assertTrue(all('multiplicityInReferenceFormula'not in c for c in ref['component3dModels']))
        self.assertIn('No geometry between ions or components',ref['component3dScope'])


if __name__=='__main__':unittest.main()
