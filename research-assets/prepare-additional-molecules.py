import collections,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
records=json.loads((ROOT/'new-molecular-pubchem-identities.json').read_text())
names={'tms2se':'Bis(trimethylsilyl)selenide','hexane':'n-Hexane','pyridine':'Pyridine','chloroform':'Chloroform','thf':'Tetrahydrofuran (THF)','tmscl':'Chlorotrimethylsilane (TMSCl)','lithium-triethylborohydride':'Lithium triethylborohydride','argon':'Argon'}
results=[];validation=[]
for r in records:
    ident=r['id'];p=r['property'];cid=r['pubchemCid']
    dim='3d' if r['3d']['status']=='available' else '2d'
    source=r[dim];file=ROOT/'new-molecular-assets'/source['file']
    lines=file.read_text().splitlines();na,nb=int(lines[3][:3]),int(lines[3][3:6])
    assert 'V2000' in lines[3]
    chargeMap={0:0,1:3,2:2,3:1,5:-1,6:-2,7:-3}
    atoms=[{'index':i,'element':s[31:34].strip(),'x':float(s[:10]),'y':float(s[10:20]),'z':float(s[20:30]),'formalCharge':chargeMap.get(int(s[36:39]),0)} for i,s in enumerate(lines[4:4+na])]
    bonds=[{'a':int(s[:3])-1,'b':int(s[3:6])-1,'order':int(s[6:9])} for s in lines[4+na:4+na+nb]]
    for s in lines[4+na+nb:]:
        if s.startswith('M  CHG'):
            parts=s.split();n=int(parts[2]);assert len(parts)==3+2*n
            for j in range(n):atoms[int(parts[3+2*j])-1]['formalCharge']=int(parts[4+2*j])
    assert all(math.isfinite(a[k]) for a in atoms for k in ['x','y','z'])
    counts=collections.Counter(a['element'] for a in atoms)
    order=['C','H']+sorted(set(counts)-{'C','H'}) if 'C' in counts else sorted(counts)
    formula=''.join(e+(str(counts[e]) if counts[e]>1 else '') for e in order if counts[e])
    assert formula==p['MolecularFormula']==r['expectedFormula'],(ident,formula)
    adjacency=[set() for _ in atoms]
    for b in bonds:
        assert 0<=b['a']<na and 0<=b['b']<na and b['a']!=b['b']
        adjacency[b['a']].add(b['b']);adjacency[b['b']].add(b['a'])
    seen=set();components=[]
    for i in range(na):
        if i in seen:continue
        stack=[i];group=[]
        while stack:
            j=stack.pop()
            if j in seen:continue
            seen.add(j);group.append(j);stack.extend(adjacency[j]-seen)
        components.append(sorted(group))
    if dim=='3d':assert len(components)==1
    def group(label,ids):
        ids=set(ids)
        return {'label':label,'atomIndices':sorted(ids),'bondIndices':[i for i,b in enumerate(bonds) if b['a'] in ids and b['b'] in ids]}
    get=lambda el:[a['index'] for a in atoms if a['element']==el]
    groups=[]
    if ident=='tms2se':groups=[group('Si-Se-Si precursor linkage',get('Si')+get('Se'))]
    if ident=='hexane':groups=[group('Alkane carbon framework; no polar head group',get('C'))]
    if ident=='pyridine':groups=[group('Pyridine nitrogen donor site',get('N'))]
    if ident=='chloroform':groups=[group('Chlorinated carbon center',get('C')+get('Cl'))]
    if ident=='thf':
        o=get('O')[0];groups=[group('Ether oxygen and adjacent carbons',[o]+list(adjacency[o]))]
    if ident=='tmscl':groups=[group('Si-Cl bond',get('Si')+get('Cl'))]
    if ident=='lithium-triethylborohydride':
        boron=get('B')[0];hydrogen=[i for i in adjacency[boron] if atoms[i]['element']=='H']
        assert len(hydrogen)==1 and len(components)==2
        assert atoms[boron]['formalCharge']==-1 and atoms[get('Li')[0]]['formalCharge']==1
        groups=[group('Borohydride B-H site',[boron]+hydrogen),group('Lithium counterion',get('Li'))]
    if ident=='argon':groups=[group('Argon reference atom',get('Ar'))]
    representation=dim if ident!='argon' else 'single-atom'
    notes=['Free component reference only; separate solvent and solute models do not establish a unique solvated complex or stock-solution speciation.']
    entry={'id':ident,'name':names[ident],'formula':formula,'iupacName':p.get('IUPACName'),
     'pubchemCid':cid,'source':f'https://pubchem.ncbi.nlm.nih.gov/compound/{cid}','sdfUrl':source['url'],
     'assetFile':str(file.relative_to(ROOT)).replace('\\','/'),'indexConvention':'zero-based','representation':representation,
     'has3D':dim=='3d','allowRotation':dim=='3d','coordinateUnits':'angstrom' if dim=='3d' else '2D depiction units; not physical distances',
     'modelType':'PubChem computed 3D conformer' if dim=='3d' else 'PubChem 2D connectivity depiction',
     'caption':'PubChem computed conformer; not an experimental or unique solution-state geometry.' if dim=='3d' else 'PubChem 2D connectivity; no physical 3D coordinates claimed.',
     'coordinateSource':'PubChem3D' if dim=='3d' else 'PubChem2D','connectivitySmiles':p.get('ConnectivitySMILES'),
     'atoms':atoms,'bonds':bonds,'functionalGroups':groups,'componentCount':len(components),'componentAtomIndices':components,'notes':notes}
    if ident=='tms2se':notes.append('Official PubChem 3D request returned 404. No locally generated conformer is supplied; Si-Se-Si is a connectivity depiction.')
    if ident=='lithium-triethylborohydride':
        entry.update({'modelType':'PubChem ionic 2D connectivity depiction','schematicFormula':'Li⁺ [HB(C₂H₅)₃]⁻','caption':'Ionic connectivity: Li⁺ and triethylborohydride anion; positions do not represent a solution complex.'})
        notes.extend(['Use verified CID 23664628, C6H16BLi, preserving its B-H bond. The name-search CID 23712863 is not used because its standardized record lacks that hydrogen.',
          'Disconnected ions are intentional for this ionic formula. No Li-B bond, coordination number, ion-pair separation or solvation geometry is inferred.',
          'FDA GSRS identifies PubChem CID 23664628 for this substance.'])
        entry['identityVerificationSource']='https://precision.fda.gov/ginas/app/ui/substances/ead4516a-b19a-4e17-9f96-b7b38fa40a17'
    if ident=='argon':
        entry.update({'modelType':'Single argon atom reference','coordinateUnits':'arbitrary origin; no molecular geometry','caption':'Argon atom reference; monatomic inert-gas component.','has3D':False,'allowRotation':False})
        notes.append('A single atom has no internal geometry; its origin is arbitrary.')
    validation.append({'id':ident,'pubchemCid':cid,'formula':formula,'formulaMatchesIdentityAndExpected':True,'atomCount':na,'bondCount':nb,'componentCount':len(components),'formalChargeSum':sum(a['formalCharge'] for a in atoms),
       'functionalGroupIndicesValid':all(all(0<=i<na for i in g['atomIndices']) and all(0<=i<nb for i in g['bondIndices']) for g in groups),'finiteCoordinates':True,'representation':representation,'sourceSdfSha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    results.append(entry)
(ROOT/'new-molecular-structures.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(ROOT/'new-molecular-validation.json').write_text(json.dumps(validation,indent=2)+'\n',encoding='utf-8')
for v in validation:print(v['id'],v['pubchemCid'],v['formula'],v['representation'],v['atomCount'],v['componentCount'])
