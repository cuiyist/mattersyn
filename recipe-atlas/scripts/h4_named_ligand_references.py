"""Exact H4 named-ligand reference preparation. Import inert; no I/O/generation.

These references do not assert free ions, solution speciation, coordination,
metal-ligand geometry, or an assembly of the original source chemical.
"""
from collections import Counter

IN_ID='name-card-indium-palmitate'
SN_ID='name-card-tin-iv-bis-acetylacetonate-dichloride'
IN_NAME='indium palmitate'
SN_NAME='tin(IV) bis(acetylacetonate) dichloride'
IN_SMILES='CCCCCCCCCCCCCCCC(=O)O[In](OC(=O)CCCCCCCCCCCCCCC)OC(=O)CCCCCCCCCCCCCCC'
SN_SMILES='CC(=CC(=O)C)O[Sn](OC(=CC(=O)C)C)(Cl)Cl'
ACAC_REFERENCE={'id':'wu2008-copper-ii-acetylacetonate-reference-component-1','formula':'C5H7O2-','model3dPath':'models/wu2008-copper-ii-acetylacetonate-reference-component-1-illustrative-3d.json','model3dSha256':'f2405ec245b9650cdfefda894e240ae339583ef52c97ad7400924b0c3b41b043','multiplicityInReferenceFormula':2}
REFERENCE_SCOPE='Independent named-ligand reference only. This does not claim free ions, solution speciation, metal-ligand geometry or any relative arrangement of the source chemical.'

def _need(value,message):
    if not value:raise ValueError(message)

def validate_named_ligand_reference(proof):
    """Standard-library-only validation for the explicit presentation scope."""
    _need(isinstance(proof,dict),'named-ligand proof object required')
    _need(proof.get('schema')=='MatterSyn-H4-named-ligand-reference/1','named-ligand schema')
    _need(proof.get('entry_id')in{IN_ID,SN_ID},'only exact two H4 ligand identities')
    _need(proof.get('reference_scope')==REFERENCE_SCOPE,'explicit named-ligand scope required')
    _need(proof.get('referenceOnly')is True and proof.get('trainingEligible')is False,'reference/training flags')
    for key in ['free_ion_claim','solution_speciation_claim','metal_ligand_geometry_assigned','relative_component_geometry_assigned']:
        _need(proof.get(key)is False,'forbidden '+key)
    for field in ['source_CID','ligand_multiplicity']+(['removed_In_O_bonds','omitted_In_atoms','formerly_bound_O_charge']if proof['entry_id']==IN_ID else[]):
        _need(type(proof.get(field))is int,'integer named-ligand count required: '+field)
    if proof['entry_id']==IN_ID:
        _need((proof.get('source_CID'),proof.get('source_formula'),proof.get('ligand_formula'),proof.get('ligand_multiplicity'),proof.get('removed_In_O_bonds'),proof.get('omitted_In_atoms'))==(140056355,'C48H93InO6','C16H31O2-',3,3,1),'exact In palmitate counts')
        for key in ['ligand_atoms_preserved','ligand_bonds_preserved','hydrogens_preserved','composition_preserved']:_need(proof.get(key)is True,'required graph preservation '+key)
        _need(proof.get('formerly_bound_O_charge')==-1 and proof.get('metal_charge_not_assigned')is True,'only explicit named-ligand charge transform')
    else:
        _need((proof.get('source_CID'),proof.get('source_formula'),proof.get('ligand_formula'),proof.get('ligand_multiplicity'))==(16685263,'C10H14Cl2O4Sn','C5H7O2-',2),'exact Sn named-ligand identity')
        _need(proof.get('existing_component_id')==ACAC_REFERENCE['id'] and proof.get('source_graph_not_cleaved')is True,'existing named acac reference only')
    return True


def validate_named_ligand_components(proof,refs):
    """Validate serialized component references after ordinary model QA."""
    import re
    from pathlib import PurePosixPath
    validate_named_ligand_reference(proof)
    _need(isinstance(refs,list)and refs,'named-ligand component references required')
    count=0
    for ref in refs:
        _need(isinstance(ref,dict)and ref.get('formula')==proof['ligand_formula'],'exact named-ligand component formula')
        n=ref.get('multiplicityInReferenceFormula',1);_need(type(n)is int and n>0,'positive exact ligand multiplicity');count+=n
        path=ref.get('model3dPath');digest=ref.get('model3dSha256')
        _need(isinstance(path,str)and path.startswith('models/')and path.endswith('.json')and '..'not in PurePosixPath(path).parts and not path.startswith('/')and '\\'not in path,'bounded component model path')
        _need(isinstance(digest,str)and re.fullmatch('[0-9a-f]{64}',digest),'component model SHA required')
        if proof['entry_id']==SN_ID:
            _need(all(ref.get(k)==ACAC_REFERENCE[k]for k in ['id','formula','model3dPath','model3dSha256']),'only exact existing acac model is admitted')
    _need(count==proof['ligand_multiplicity'],'component reference counts must equal named ligand counts')
    return True

def _canonical(smiles,Chem):
    m=Chem.MolFromSmiles(smiles);_need(m is not None,'invalid own cached graph')
    return Chem.MolToSmiles(m,isomericSmiles=True)

def _proof(entry_id,properties):
    return {'schema':'MatterSyn-H4-named-ligand-reference/1','entry_id':entry_id,'source_CID':properties['CID'],'source_formula':properties['MolecularFormula'],'reference_scope':REFERENCE_SCOPE,'referenceOnly':True,'trainingEligible':False,'free_ion_claim':False,'solution_speciation_claim':False,'metal_ligand_geometry_assigned':False,'relative_component_geometry_assigned':False}

def prepare_named_ligand_reference(entry,properties,Chem,rdMolDescriptors):
    """Return an exact named-reference plan, never model coordinates or assets."""
    eid=entry.get('id')
    if eid not in{IN_ID,SN_ID}:return None
    is_in=eid==IN_ID;name=IN_NAME if is_in else SN_NAME;cid=140056355 if is_in else 16685263
    formula='C48H93InO6'if is_in else'C10H14Cl2O4Sn';expected=IN_SMILES if is_in else SN_SMILES
    _need(entry.get('name')==name and entry.get('formula','')in('',formula),'exact original own name/formula required')
    _need(properties.get('CID')==cid and properties.get('MolecularFormula')==formula,'exact own cached identity required')
    actual=properties.get('isomericSmiles');_need(isinstance(actual,str)and _canonical(actual,Chem)==_canonical(expected,Chem),'exact own cached graph signature required')
    mol=Chem.MolFromSmiles(actual);_need(rdMolDescriptors.CalcMolFormula(mol)==formula,'input graph composition differs')
    proof=_proof(eid,properties)
    if not is_in:
        proof.update(ligand_formula='C5H7O2-',ligand_multiplicity=2,existing_component_id=ACAC_REFERENCE['id'],source_graph_not_cleaved=True)
        validate_named_ligand_reference(proof)
        return {'kind':'existing_named_ligand','components':[dict(ACAC_REFERENCE)],'proof':proof}
    metals=[a for a in mol.GetAtoms()if a.GetAtomicNum()==49]
    _need(len(metals)==1 and metals[0].GetDegree()==3 and metals[0].GetFormalCharge()==0,'exact one neutral three-linked In center required')
    center=metals[0].GetIdx();bound=[]
    for b in metals[0].GetBonds():
        o=b.GetOtherAtom(metals[0]);_need(str(b.GetBondType())=='SINGLE'and o.GetSymbol()=='O'and o.GetFormalCharge()==0 and o.GetDegree()==2 and o.GetTotalNumHs()==0,'only original singly bound hydrogen-free O links')
        bound.append(o.GetIdx())
    atom_before={a.GetIdx():(a.GetSymbol(),a.GetIsotope(),a.GetFormalCharge(),a.GetTotalNumHs(),a.GetNumRadicalElectrons(),a.GetIsAromatic())for a in mol.GetAtoms()if a.GetIdx()!=center}
    bonds_before={tuple(sorted((b.GetBeginAtomIdx(),b.GetEndAtomIdx()))):(str(b.GetBondType()),str(b.GetStereo()),b.GetIsAromatic())for b in mol.GetBonds()if center not in(b.GetBeginAtomIdx(),b.GetEndAtomIdx())}
    work=Chem.RWMol(mol)
    for a in work.GetAtoms():a.SetIntProp('_H4OriginalIndex',a.GetIdx())
    for i in bound:
        a=work.GetAtomWithIdx(i);a.SetFormalCharge(-1);a.SetNoImplicit(True);a.SetNumExplicitHs(0)
    work.RemoveAtom(center);result=work.GetMol();Chem.SanitizeMol(result)
    fragments=list(Chem.GetMolFrags(result,asMols=True,sanitizeFrags=True));_need(len(fragments)==3,'exact three independent palmitate ligands required')
    atoms_after={};bonds_after={}
    for f in fragments:
        _need(rdMolDescriptors.CalcMolFormula(f)=='C16H31O2-'and Chem.GetFormalCharge(f)==-1,'each named ligand must be C16H31O2-')
        _need(_canonical(Chem.MolToSmiles(f),Chem)==_canonical('CCCCCCCCCCCCCCCC(=O)[O-]',Chem),'exact independent palmitate topology required')
        for a in f.GetAtoms():atoms_after[a.GetIntProp('_H4OriginalIndex')]=(a.GetSymbol(),a.GetIsotope(),a.GetFormalCharge(),a.GetTotalNumHs(),a.GetNumRadicalElectrons(),a.GetIsAromatic())
        for b in f.GetBonds():bonds_after[tuple(sorted((b.GetBeginAtom().GetIntProp('_H4OriginalIndex'),b.GetEndAtom().GetIntProp('_H4OriginalIndex'))))]=(str(b.GetBondType()),str(b.GetStereo()),b.GetIsAromatic())
    _need(set(atoms_after)==set(atom_before)and bonds_after==bonds_before,'all ligand atoms and internal bonds must remain unchanged')
    for i,before in atom_before.items():
        after=atoms_after[i];expected_atom=before[:2]+((-1 if i in bound else before[2]),)+before[3:]
        _need(after==expected_atom,'only formerly In-bound O formal charge may change; no H changes')
    _need(Counter(a[0]for a in atoms_after.values())==Counter({'C':48,'O':6})and sum(a[3]for a in atoms_after.values())==93,'original composition except one omitted In must remain')
    proof.update(ligand_formula='C16H31O2-',ligand_multiplicity=3,removed_In_O_bonds=3,omitted_In_atoms=1,formerly_bound_O_charge=-1,metal_charge_not_assigned=True,ligand_atoms_preserved=True,ligand_bonds_preserved=True,hydrogens_preserved=True,composition_preserved=True)
    validate_named_ligand_reference(proof)
    return {'kind':'derived_named_ligands','components':fragments,'proof':proof}
