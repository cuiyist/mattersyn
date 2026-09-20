"""Independent source-text token inventory prepared before author-table comparison.
The auditor separately viewed every source page; this script is a consistency aid,
not a replacement for native-page scientific inspection.
"""
from pathlib import Path
import json,re,hashlib,decimal
P=Path(__file__).resolve().parents[1]; A=P/'source-independent-audit'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
num=re.compile(r'^(-?\d+(?:\.\d+)?)(?:\((\d+)\))?$')
atom=re.compile(r'^(?:Sb|Cl|N|C)[0-9A-Z]{2,3}$')
def cell(raw,scale):
    m=num.fullmatch(raw); assert m, raw
    x=decimal.Decimal(m[1]); u=decimal.Decimal(m[2])*(decimal.Decimal(10)**x.as_tuple().exponent) if m[2] else None
    return {'raw':raw,'central_value_in_printed_units':float(x),'standard_uncertainty_in_printed_units':float(u) if u is not None else None,'scale_to_normalized_unit':scale,'normalized_value':float(x*decimal.Decimal(str(scale))),'normalized_standard_uncertainty':float(u*decimal.Decimal(str(scale))) if u is not None else None}
tables={f'S{i}':{'id':f'S{i}','sample':'bulk-A' if i%2==0 else 'bulk-B','rows':[]} for i in range(2,10)}
tables['S4']['sample']='bulk-A';tables['S5']['sample']='bulk-B'
tid=None;bindings=[]
for page in range(13,27):
    path=P/'private/text'/f'si-{page:02d}.txt';bindings.append({'path':str(path),'sha256':sha(path)})
    for line in path.read_text(encoding='utf-8').splitlines():
        m=re.match(r'Table (S\d+)\.',line)
        if m:tid=m[1];continue
        tok=line.split()
        if tid not in tables or not tok or not atom.fullmatch(tok[0]):continue
        t=int(tid[1:])
        if t in (2,3):
            assert len(tok) in (3,6), (tid,page,tok)
            for col,j in enumerate(range(0,len(tok),3)):
                assert atom.fullmatch(tok[j]) and atom.fullmatch(tok[j+1])
                tables[tid]['rows'].append({'source_pdf_page':page,'physical_column':col+1,'atom_labels':tok[j:j+2],'value':cell(tok[j+2],1),'unit':'angstrom'})
        elif t in (4,5):
            assert len(tok)==8,(tid,page,tok)
            for col,j in enumerate((0,4)):
                assert all(atom.fullmatch(a) for a in tok[j:j+3])
                tables[tid]['rows'].append({'source_pdf_page':page,'physical_column':col+1,'atom_labels':tok[j:j+3],'value':cell(tok[j+3],1),'unit':'degree'})
        elif t in (6,7):
            assert len(tok)==5,(tid,page,tok)
            tables[tid]['rows'].append({'source_pdf_page':page,'atom_label':tok[0],'cells':{k:{**cell(v,s),'normalized_unit':u} for k,v,s,u in zip(['x','y','z','Ueq'],tok[1:],[1e-4,1e-4,1e-4,1e-3],['fractional_coordinate']*3+['angstrom^2'])}})
        else:
            assert len(tok)==7,(tid,page,tok)
            tables[tid]['rows'].append({'source_pdf_page':page,'atom_label':tok[0],'cells':{k:{**cell(v,1e-3),'normalized_unit':'angstrom^2'} for k,v in zip(['U11','U22','U33','U23','U13','U12'],tok[1:])}})
expected={'S2':29,'S3':32,'S4':38,'S5':40,'S6':32,'S7':36,'S8':32,'S9':36}
for t,n in expected.items():assert len(tables[t]['rows'])==n,(t,len(tables[t]['rows']))
for a,b in [('S6','S8'),('S7','S9')]:assert [x['atom_label'] for x in tables[a]['rows']]==[x['atom_label'] for x in tables[b]['rows']]
count=sum(sum(len(r.get('cells',{'value':r.get('value')})) for r in t['rows']) for t in tables.values())
assert count==819,count
d={'schema':'mattersyn.independent_table_token_inventory.v1','reader':'/root/norberg2004_extract','author_typed_extraction_opened':False,'basis':'Original-derived SI text independently read against every original table page image, not author tables. Includes only S2–S9. S1 read separately in independent-reading-v1.md.','source_bound_files':bindings,'tables':list(tables.values()),'counts':{'tables':8,'numeric_tokens':count,'rows_by_table':expected},'scientific_scope':'Bulk A/B non-H and bond tables. Values normalized here solely for later independent scale comparison; this is not a public structure model, CIF or exact synthesis–structure pair.'}
out=A/'independent-table-tokens-v1.json';assert not out.exists();out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'path':str(out),'sha256':sha(out),'numeric_tokens':count,'rows':expected}))
