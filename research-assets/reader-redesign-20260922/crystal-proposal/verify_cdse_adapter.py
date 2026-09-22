from pathlib import Path
import sys,json
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'runtime'))
import gemmi
base=ROOT/'cdse-adapter-assets/crystal-references'
stem='cdse-zinc-blende-existing-ideal-reference'
b=gemmi.cif.read_file(str(base/(stem+'.cif'))).sole_block()
s=gemmi.make_small_structure_from_block(b)
model=json.loads((base/'models'/(stem+'.json')).read_text())
assert s.spacegroup_number==1
assert len(s.sites)==len(s.get_all_unit_cell_sites())==8
error=0
for a,atom in zip(s.sites,model['atoms']):
 assert a.element.name==atom['element']
 xyz=s.cell.orthogonalize(a.fract)
 error=max(error,*[abs(getattr(xyz,k)-atom[k]) for k in ['x','y','z']])
assert error<1e-10
p=ROOT/'cdse-bindings-validation.json'
d=json.loads(p.read_text());d['cubic_cif_roundtrip']={'parser':'Gemmi '+gemmi.__version__,'export_space_group':1,'expanded_sites':8,'max_coordinate_error_angstrom':error}
p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
print(json.dumps(d['cubic_cif_roundtrip']))
