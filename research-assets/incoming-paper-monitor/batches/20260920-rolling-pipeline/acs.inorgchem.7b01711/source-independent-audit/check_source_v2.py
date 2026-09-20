"""Independent mechanical support for a source-and-image scientific audit.

The expected table tokens below were read from the original main/SI pages and
checked again against all eight selected table images. This is not an author
validator import. Writes are confined to this independent audit directory.
"""
from pathlib import Path
import json, hashlib, re, math
from datetime import datetime, timezone

O=Path(__file__).resolve().parent
P=O.parent
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]
def ck(name,ok,detail=None):
    checks.append({'check':name,'passed':bool(ok),**({'detail':detail} if detail is not None else {})})
def eq(a,b):
    return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10) if isinstance(a,(int,float)) and isinstance(b,(int,float)) else a==b

labels='Cd(1) S(1) S(2) S(3) S(4) N(1) N(2) C(1) C(2) C(3) C(4) C(5) C(6) C(7) C(8) C(9) C(10) C(11) C(12) C(13) C(14) O(1S) C(1S) C(2S) C(3S) C(4S)'.split()
s1='''4726(1) 2453(1) 4664(1) 10(1)
5053(1) 5824(1) 3986(1) 10(1)
3327(1) 4254(1) 4304(1) 14(1)
5094(1) 852(1) 3308(1) 11(1)
6164(1) 483(1) 4751(1) 10(1)
3616(1) 7477(1) 3630(1) 11(1)
6642(1) -756(1) 3407(1) 10(1)
3935(1) 5954(1) 3945(1) 10(1)
2763(1) 8078(1) 3483(1) 11(1)
2668(1) 9932(1) 3344(1) 13(1)
1868(1) 10645(2) 3144(1) 17(1)
1159(1) 9512(2) 3072(1) 18(1)
1254(1) 7669(2) 3214(1) 17(1)
2049(1) 6937(2) 3423(1) 14(1)
6003(1) 81(1) 3763(1) 10(1)
6713(1) -1140(1) 2603(1) 10(1)
7498(1) -744(1) 2264(1) 13(1)
7621(1) -1144(2) 1487(1) 17(1)
6964(1) -1938(2) 1053(1) 17(1)
6187(1) -2345(1) 1397(1) 15(1)
6054(1) -1956(1) 2175(1) 13(1)
8243(1) 8548(1) 4137(1) 17(1)
8376(1) 8663(2) 4958(1) 16(1)
8951(1) 7070(2) 5155(1) 18(1)
9554(1) 7056(2) 4465(1) 21(1)
8972(1) 7675(2) 3795(1) 16(1)'''
s2='''10 9 12 0 1 1
8 9 12 0 1 0
9 11 22 5 2 -1
9 12 11 0 0 2
9 10 10 0 1 0
9 10 14 1 0 0
8 13 10 -1 0 2
10 9 10 -1 0 0
10 13 10 0 0 1
12 14 14 2 1 2
16 19 15 4 2 6
12 28 15 4 0 6
10 26 15 -1 -1 -1
11 16 16 -1 -1 0
9 9 11 0 2 -1
11 10 11 0 2 1
11 14 14 -1 3 0
16 18 16 -1 6 1
22 17 12 -2 3 3
17 14 14 -3 -1 2
12 13 13 -2 1 0
12 25 14 -1 -1 7
16 19 14 -1 0 3
15 23 17 4 1 4
13 30 20 2 1 6
13 18 16 0 2 3'''
hl='H(1) H(2) H(3) H(4) H(5) H(6) H(7) H(10) H(11) H(12) H(13) H(14) H(1SA) H(1SB) H(2SA) H(2SB) H(3SA) H(3SB) H(4SA) H(4SB)'.split()
s3='''4017(10) 8200(20) 3520(10) 24(4)
7092(9) -980(20) 3664(9) 17(4)
3153 10711 3386 16
1806 11910 3057 20
613 9994 2927 22
767 6895 3168 21
2106 5676 3523 17
7948 -203 2562 16
8155 -874 1253 20
7045 -2202 520 20
5740 -2896 1099 18
5523 -2244 2410 15
7824 8573 5232 20
8659 9820 5101 20
8619 5929 5188 22
9271 7268 5649 22
10040 7905 4546 25
9783 5825 4371 25
9282 8533 3457 19
8784 6623 3479 19'''
s4='''0.847(14) 2.603(14) 3.4396(9) 170.0(16)
0.841(13) 1.984(13) 2.8195(12) 172.1(16)
0.95 3.02 3.8342(11) 144.0
0.95 2.54 3.1760(11) 124.6
0.99 2.87 3.6577(12) 137.0'''
s4l=['N(1)–H(1)…S(3)#3','N(2)–H(2)…O(1S)#4','C(3)–H(3)…S(3)#3','C(7)–H(7)…S(2)','C(1S)–H(1SA)…S(2)#1']
t1=[('empirical formula','C18H20CdN2OS4'),('formula weight','521.00'),('temperature','100(2)'),('wavelength','0.71073'),('crystal system','monoclinic'),('space group','P21/n'),('a','15.5501(6)'),('b','7.3761(3)'),('c','17.2620(7)'),('alpha','90'),('beta','90.915(2)'),('gamma','90'),('volume','1979.68(14)'),('Z','4'),('density calculated','1.748'),('absorption coefficient','1.535'),('F(000)','1048'),('crystal size1','0.598'),('crystal size2','0.121'),('crystal size3','0.075'),('theta lower','1.749'),('theta upper','45.000'),('h lower','-28'),('h upper','30'),('k lower','-9'),('k upper','14'),('l lower','-34'),('l upper','34'),('collected reflections','66935'),('independent reflections','16292'),('R(int)','0.0464'),('completeness','99.7'),('completeness theta','25.242'),('absorption correction','semiempirical from equivalents'),('max transmission','0.4481'),('min transmission','0.3434'),('refinement method','full-matrix least-squares on F^2'),('data','16292'),('restraints','1'),('parameters','243'),('goodness of fit on F2','1.002'),('R1 I>2sigma(I)','0.0309'),('wR2 I>2sigma(I)','0.0554'),('R1 all data','0.0583'),('wR2 all data','0.0632'),('largest difference peak','0.914'),('largest difference hole','-1.026')]
t2l=['Cd1–S1','Cd1–S4′','Cd1–S1′','Cd1–S2','Cd1–S3','Cd1–S4','S1–Cd–S1′','S1–Cd–S2','S1–Cd–S3','S1–Cd–S4','S3–Cd1–S4','S1–Cd–S4′']
t2='2.7992(3) 2.7691(3) 2.6719(3) 2.6149(3) 2.6917(3) 2.6687(3) 85.461(8) 66.752(8) 89.032(8) 110.441(8) 160.512(8) 67.689(8)'.split()
def matrix(s): return [x.split() for x in s.splitlines()]
expected={
 'table-s1':list(zip(labels,matrix(s1))),
 'table-s2':list(zip(labels,[[v+'(1)' for v in row] for row in matrix(s2)])),
 'table-s3':list(zip(hl,matrix(s3))),
 'table-s4':list(zip(s4l,matrix(s4))),
 'table-1':[(l,[v]) for l,v in t1],
 'table-2':[(l,[v]) for l,v in zip(t2l,t2)],
 'table-s5':list(zip(['C','H','N','S'],matrix('2.83 2.41 2.47\n0.61 <0.5 0.50\n<0.5 <0.5 <0.5\n21.32 - 20.01'))),
 'figure-s7-eds-table':list(zip(['S K','S L','Cd L','Cd M','Total'],matrix('14119 190 --- 1.030 23.99 0.32 52.53 0.71\n0 371 --- --- --- --- --- ---\n26583 440 --- 1.732 76.01 1.26 47.47 0.79\n0 61 --- --- --- --- --- ---\n--- --- --- --- 100.00 --- 100.00 ---')))
}
freeze=read(P/'package-freeze.json')
for path,h in freeze['bound_files'].items():
    ck('frozen_file:'+path,Path(path).exists() and sha(path)==h)
d=read(P/'source-facts.json');inv=read(P/'source-inventory.json');tabs=read(P/'source-tables.json')['tables']
ck('table_embedded_copies',d['tables']==tabs)
numeric=0;non_numeric=0
for table in tabs:
    tid=table['id']; exp=expected[tid]
    ck(tid+':row_count',len(table['rows'])==len(exp))
    for ri,(row,(label,tokens)) in enumerate(zip(table['rows'],exp)):
        ck(f'{tid}:{ri}:row_label',row['row_label']==label)
        ck(f'{tid}:{ri}:cell_count',len(row['cells'])==len(tokens))
        for ci,(cell,raw) in enumerate(zip(row['cells'],tokens)):
            key=f'{tid}:{ri+1}:{ci+1}'
            ck(key+':raw',cell['raw_text'].replace('−','-')==raw)
            scale=(.001 if tid=='table-s2' or (tid in ['table-s1','table-s3'] and ci==3) else .0001 if tid in ['table-s1','table-s3'] else 1)
            ck(key+':scale',cell['printed_to_value_scale']==scale)
            m=re.fullmatch(r'([<>]=?)?(-?\d+(?:\.\d+)?)(?:\((\d+)\))?',raw)
            if m:
                numeric+=1
                bound,num,su=m.groups();value=float(num)*scale
                uncertainty=int(su)*10**(-len(num.split('.')[1]) if '.' in num else 0)*scale if su else None
                ck(key+':value',eq(cell['value'],value))
                ck(key+':uncertainty',eq(cell['uncertainty'],uncertainty))
                ck(key+':comparison',cell['comparison']==bound)
            else:
                non_numeric+=1
                ck(key+':no_invented_value',cell['value'] is None)
            ck(key+':evidence',len(cell['evidence'])>0 and all(e['locator'] for e in cell['evidence']))
    if tid in ['table-s1','table-s2','table-s3','table-s4','table-1','table-2']:
        ck(tid+':precursor_only',table['sample_scope']=='precursor-crystal')

def resolve(obj,pointer):
    for bit in pointer.strip('/').split('/'):
        bit=bit.replace('~1','/').replace('~0','~')
        obj=obj[int(bit)] if isinstance(obj,list) else obj[bit]
    return obj
unit_ids=[]
for unit in inv['source_units']:
    unit_ids.append(unit['id'])
    if 'extraction_pointer' in unit:
        x=resolve(d,unit['extraction_pointer'])
        ck('unit_pointer:'+unit['id'],x['id']==unit['id'])
    for ev in unit['evidence']:
        role=ev['document_role'];page=ev['pdf_page'];h=freeze['main_sha256'] if role=='main' else freeze['si_sha256']
        ck('unit_source:'+unit['id'],role in ['main','si'] and 1<=page<=(10 if role=='main' else 17) and ev['source_sha256']==h)
ck('unique_units',len(unit_ids)==len(set(unit_ids)))
ck('reference_count',len(d['references'])==52)
ck('no_reference_namespace_merging',set(x['id'] for x in d['references'])==set([f'main-reference-{i}' for i in range(1,51)]+[f'si-reference-{i}' for i in range(1,3)]))
ck('source_training_gates_false',not freeze['training_admission'] and not freeze['published'] and not freeze['independent_audit_approved'])

assets=read(P/'original-assets-manifest.json')['assets']
for asset in assets:
    ck('asset_hash:'+asset['id'],sha(asset['path'])==asset['sha256'])
    ck('asset_not_fullpage:'+asset['id'],asset['complete_page'] is False and asset['original_selected_excerpt'] is True)
    ck('asset_bounds:'+asset['id'],all(0<=v<=1 for v in asset['crop_normalized']))
ck('all_30_assets',len(assets)==30)
for fig in d['figures']:
    ck('figure_asset:'+fig['id'],fig['asset_id'] in {x['id'] for x in assets})

report={'schema':'mattersyn.independent-source-mechanical-checks.v1','reviewer':'/root/peng1998_reader_assets','at':datetime.now(timezone.utc).isoformat(),'source_package_sha256':sha(P/'package-freeze.json'),'expected_table_basis':'Independent visual reading of original full pages and selected table crops; no imported author validator. Exact expected tokens embedded in this script.','table_counts':{'tables':len(tabs),'rows':sum(len(x['rows']) for x in tabs),'cells':numeric+non_numeric,'numeric_or_bound':numeric,'null_or_text':non_numeric},'check_count':len(checks),'failures':[x for x in checks if not x['passed']],'checks':checks,'manual_scientific_audit_separate':True}
(O/'mechanical-checks-v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(O/'independent-table-tokens-v2.json').write_text(json.dumps({'basis':report['expected_table_basis'],'tables':expected},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
