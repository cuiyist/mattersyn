from pathlib import Path
import sys, collections
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'runtime'))
import gemmi
for p in sorted((ROOT/'source-cache').glob('*.cif')):
 b=gemmi.cif.read_file(str(p)).sole_block()
 s=gemmi.make_small_structure_from_block(b)
 sites=s.get_all_unit_cell_sites()
 count=collections.Counter()
 for a in sites: count[a.element.name]+=a.occ
 print(p.name,s.spacegroup_hm,s.spacegroup_number,len(s.sites),len(sites),dict(count),[s.cell.a,s.cell.b,s.cell.c],b.find_value('_chemical_formula_sum'),b.find_value('_cell_formula_units_Z'))
