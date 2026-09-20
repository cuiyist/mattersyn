from pathlib import Path
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
for name in ['protocol-visuals.mjs','material-guide.mjs','material-hub.mjs']:
 p=S/'dist'/name;t=p.read_text(encoding='utf-8')
 if "from './quantity-value.mjs'" not in t:t="import {quantityValue} from './quantity-value.mjs';\n"+t
 if name=='protocol-visuals.mjs':
  old="q.value??(q.minimum!==null&&q.minimum!==undefined?`${q.minimum}–${q.maximum}`:null)"
  assert old in t;t=t.replace(old,'quantityValue(q)')
 elif name=='material-guide.mjs':
  t=t.replace("q.value===null&&q.minimum===null","quantityValue(q)===null")
  t=t.replace("q.value??`${q.minimum}–${q.maximum}`","quantityValue(q)")
 else:
  t=t.replace("value.value===null&&value.minimum===null","quantityValue(value)===null")
  t=t.replace("value.value??`${value.minimum}–${value.maximum}`","quantityValue(value)")
 p.write_text(t,encoding='utf-8')
p=B/'build_records.py';t=p.read_text(encoding='utf-8').replace("r['schema_version']='1.2.0'","r['schema_version']='1.3.0'")
t=t.replace("Q(.1,'s',qualifier='strictly less than',raw_text='<0.1 s')","Q(u='s',maximum=.1,maximum_exclusive=True,raw_text='<0.1 s')")
t=t.replace("Q(.1,'s',e=IN,qualifier='strictly less than',raw_text='<0.1 s')","Q(u='s',e=IN,maximum=.1,maximum_exclusive=True,raw_text='<0.1 s')")
t=t.replace("Q(300,'degC',e=CD+DISC,basis='300 °C after injection; discussion refers to the growth temperature')","Q(300,'degC',e=CD+DISC,status='inferred',basis='Nominal growth temperature inferred from the post-injection 300 °C; a maintained hold is not independently reported')")
t=t.replace("C('argon','atmosphere')]","C('argon','atmosphere'),C('methanol','antisolvent',stage='workup',notes=['For timed aliquots only; not a whole-batch isolation charge.']),C('toluene','optical solvent',stage='characterization',notes=['For purified aliquot redissolution.'])]")
t=t.replace("C('tms3as','nonmetal_precursor',e=IN)]","C('tms3as','nonmetal_precursor',e=IN),C('toluene','optical solvent',stage='characterization',e=IN,notes=['For timed aliquot dilution; volume unreported.'])]")
p.write_text(t,encoding='utf-8')
print('Updated one-sided bound display and source-scoped draft quantities/inventories.')
