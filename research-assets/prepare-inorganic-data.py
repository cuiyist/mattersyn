"""Expand verified COD reference unit cells into small display crops.

Source CIFs are retained verbatim beside this script. Crops are not particle models.
"""
import json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def write_model(model, repeats, cutoff):
    atoms=[]
    vectors=model['latticeVectors']
    for i in range(repeats[0]):
        for j in range(repeats[1]):
            for k in range(repeats[2]):
                for atom in model['fractionalAtoms']:
                    frac=[atom['x']+i,atom['y']+j,atom['z']+k]
                    point=[sum(frac[t]*vectors[t][axis] for t in range(3)) for axis in range(3)]
                    atoms.append({'index':len(atoms),'element':atom['element'],
                                  'x':point[0],'y':point[1],'z':point[2]})
    center=[sum(a[key] for a in atoms)/len(atoms) for key in ['x','y','z']]
    for atom in atoms:
        for axis,key in enumerate(['x','y','z']): atom[key]=round(atom[key]-center[axis],7)
    bonds=[]
    for i,a in enumerate(atoms):
        for j,b in enumerate(atoms[i+1:],i+1):
            if model['formula']=='CdO' and a['element']==b['element']: continue
            d=math.sqrt(sum((a[q]-b[q])**2 for q in ['x','y','z']))
            if .1<d<cutoff:
                bonds.append({'a':i,'b':j,'order':1,'distance':round(d,6)})
    assert atoms and bonds
    model['displayModel']={'repeats':repeats,'atoms':atoms,'bonds':bonds,
                           'indexConvention':'zero-based','coordinateUnits':'angstrom',
                           'bondMeaning':'Nearest-neighbor connectivity; order 1 is a renderer convention, not a molecular bond-order assignment.',
                           'caption':'Repeated reference cells cropped for display; the open boundaries are not a modeled particle surface.'}
    output=ROOT/(model['id']+'-reference.json')
    output.write_text(json.dumps(model,indent=2)+'\n',encoding='utf-8')
    print(output.name,len(atoms),'atoms',len(bonds),'connections',
          'distance range',min(b['distance'] for b in bonds),max(b['distance'] for b in bonds))

a=4.6963
fcc=[(0,0,0),(0,.5,.5),(.5,0,.5),(.5,.5,0)]
cd=[{'element':'Cd','x':x,'y':y,'z':z} for x,y,z in fcc]
oxygen=[{'element':'O','x':(x+.5)%1,'y':(y+.5)%1,'z':(z+.5)%1} for x,y,z in fcc]
write_model({
    'id':'cdo-rocksalt','name':'Cadmium oxide rock-salt reference','formula':'CdO',
    'modelType':'Symmetry-expanded experimental bulk crystal reference from COD 9006671',
    'caption':'CdO rock-salt crystal reference; not an isolated CdO molecule.',
    'a':a,'b':a,'c':a,'alpha':90,'beta':90,'gamma':90,
    'spaceGroup':'Fm-3m','spaceGroupNumber':225,'cellType':'conventional cubic',
    'formulaUnitsPerCell':4,'coordinateUnits':'angstrom',
    'latticeVectors':[[a,0,0],[0,a,0],[0,0,a]],
    'sourceAsymmetricUnit':[{'element':'Cd','x':0,'y':0,'z':0},{'element':'O','x':.5,'y':.5,'z':.5}],
    'fractionalAtoms':cd+oxygen,
    'source':{'citation':'J. Zhang, Room temperature compressibilities of MnO and CdO: further examination of the role of cation type in bulk modulus systematics, Physics and Chemistry of Minerals 26 (1999), 644–648',
              'doi':'10.1007/s002690050229','url':'https://www.crystallography.net/cod/9006671.html',
              'cifUrl':'https://www.crystallography.net/cod/9006671.cif','localCif':'cdo-rocksalt-cod-9006671.cif',
              'conditions':'Room temperature, Run 1, 0.00 GPa at beginning of experiment'},
    'notes':['Rock-salt CdO is an extended lattice with sixfold nearest-neighbor coordination.',
             'Nearest Cd-O distance in this reference is a/2 = 2.34815 angstrom.',
             'Do not use a diatomic Cd-O model to represent CdO powder.']
},[2,2,2],2.5)

a,c,u=4.3662,4.9536,.22540
write_model({
    'id':'selenium-trigonal','name':'Trigonal selenium crystal reference','formula':'Se',
    'modelType':'Symmetry-expanded experimental bulk crystal reference from COD 9012501',
    'caption':'Trigonal selenium reference; the black powder allotrope is unspecified.',
    'a':a,'b':a,'c':c,'alpha':90,'beta':90,'gamma':120,
    'spaceGroup':'P3121','spaceGroupNumber':152,'cellType':'primitive hexagonal setting',
    'formulaUnitsPerCell':3,'coordinateUnits':'angstrom',
    'latticeVectors':[[a,0,0],[-a/2,math.sqrt(3)*a/2,0],[0,0,c]],
    'sourceAsymmetricUnit':[{'element':'Se','x':u,'y':0,'z':.33333}],
    'fractionalAtoms':[{'element':'Se','x':u,'y':0,'z':1/3},
                       {'element':'Se','x':0,'y':u,'z':2/3},
                       {'element':'Se','x':1-u,'y':1-u,'z':0}],
    'source':{'citation':'P. Cherin and P. Unger, The crystal structure of trigonal selenium, Inorganic Chemistry 6 (1967), 1589–1591',
              'doi':'10.1021/ic50054a037','url':'https://www.crystallography.net/cod/9012501.html',
              'cifUrl':'https://www.crystallography.net/cod/9012501.cif','localCif':'selenium-trigonal-cod-9012501.cif'},
    'notes':['Source CIF rounds symmetry-fixed z=1/3 to 0.33333. Exact thirds are restored when expanding the three symmetry-related positions.',
             'Trigonal selenium has helical Se chains; rods in the display connect the nearest chain neighbors.',
             'Powder describes physical form, not allotrope. This is not evidence that the recipe black selenium powder has the trigonal structure.',
             'Do not represent the powder as isolated monatomic Se or assume it consists of Se8 molecules.']
},[3,3,3],2.6)
