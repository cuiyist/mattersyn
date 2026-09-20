from pathlib import Path
import json,hashlib,sys,re,decimal,math,datetime
P=Path(__file__).resolve().parents[1]; A=P/'source-independent-audit'; ROOT=Path('[local path redacted]')
sys.path.insert(0,str(ROOT/'research-assets/corpus-20260917/runtime'))
sys.path.insert(0,str(ROOT/'research-assets/rdkit-runtime'))
import pymupdf
from PIL import Image,ImageChops
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(ok,label,detail=None):
    checks.append({'check':label,'passed':bool(ok),**({'detail':detail} if not ok else {})})
def close(a,b):return (a is None and b is None) or (isinstance(a,(int,float)) and isinstance(b,(int,float)) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12))
freeze=read(P/'package-freeze.json');D=read(P/'source-facts.json');I=read(P/'source-inventory.json');T=read(P/'source-tables.json');M=read(P/'original-assets-manifest.json');ind=read(A/'independent-table-tokens-v1.json')
bound=dict(freeze['bound_files']);bound[str(P/'package-freeze.json')]=sha(P/'package-freeze.json')
for p,h in bound.items():check(Path(p).exists() and sha(Path(p))==h,'bound file '+p)
source_paths={x['role']:Path(x['path']) for x in read(A/'independent-reading-v1.json')['sources']}
source_hashes={k:sha(v) for k,v in source_paths.items()}
for k,v in source_paths.items():bound[str(v)]=source_hashes[k]
check(source_hashes=={'main':'4a351221c8398d31f804d2af3d9f8327931c43e6e275e481ce84d7a67522a692','si':'a98d80fda37e0d7fd148e5da33b318ba382dd179117613c80f04b01c52659bf4'},'original PDF identities')
check(D['tables']==T['tables'],'all embedded table objects identical to source-tables')
for key in ['materials','stocks','protocols','samples','figures','schemes','equations','references','conflicts','gaps']:
    check(D[key]==I[key],key+' inventory mirrors facts')
    ids=[x['id'] for x in D[key]];check(len(ids)==len(set(ids)),key+' unique IDs')
tabs={t['id']:t for t in T['tables']}
cell_count=0
for it in ind['tables']:
    t=tabs['table-'+it['id'].lower()];n=int(it['id'][1:]);check(len(t['rows'])==len(it['rows']),it['id']+' row count')
    if n<6:
        actual={tuple(r['atoms']):r for r in t['rows']}
        for r in it['rows']:
            key=tuple(r['atom_labels']);check(key in actual,it['id']+' atom tuple '+str(key));ar=actual[key];c=ar['cells'][0];v=r['value'];cell_count+=1
            for target,source in [('raw_text','raw'),('value','normalized_value'),('uncertainty','normalized_standard_uncertainty'),('printed_to_value_scale','scale_to_normalized_unit')]:
                check(close(c[target],v[source]) if isinstance(v[source],(int,float)) or v[source] is None else c[target]==v[source],c['id']+' '+target)
            check(c['unit']==('angstrom' if n<4 else 'deg'),c['id']+' unit')
            check(c['evidence'][0]['pdf_page']==r['source_pdf_page'],c['id']+' page')
            check(ar['printed_block']==('left' if r['physical_column']==1 else 'right'),c['id']+' printed column')
    else:
        actual={r['row_label']:r for r in t['rows']}
        check(set(actual)=={r['atom_label'] for r in it['rows']},it['id']+' complete site labels')
        for r in it['rows']:
            ar=actual[r['atom_label']];check([c['column'] for c in ar['cells']]==list(r['cells']),it['id']+r['atom_label']+' column order')
            for c in ar['cells']:
                v=r['cells'][c['column']];cell_count+=1
                for target,source in [('raw_text','raw'),('value','normalized_value'),('uncertainty','normalized_standard_uncertainty'),('printed_to_value_scale','scale_to_normalized_unit')]:
                    check(close(c[target],v[source]) if isinstance(v[source],(int,float)) or v[source] is None else c[target]==v[source],c['id']+' '+target)
                check(c['unit']==v['normalized_unit'],c['id']+' unit')
                check(c['evidence'][0]['pdf_page']==r['source_pdf_page'],c['id']+' page')
check(cell_count==819,'S2–S9 all 819 numeric positions checked')
# Independently source-read S1 transcription. Paired raw tokens keep printed precision.
s1raw=[('C24H56Cl5N2Sb','C12H28Cl4NSb'),('671.7','449.9'),('296.05(10)','296.25(10)'),('triclinic','monoclinic'),('P-1','P21/c'),('10.7745(3)','18.19840(10)'),('10.8437(2)','15.74030(10)'),('16.3565(3)','13.67940(10)'),('76.301(2)','90'),('75.451(2)','91.5970(10)'),('72.701(2)','90'),('1738.68(7)','3916.92(4)'),('2','8'),('1.283','1.526'),('9.92','16.08'),('5.67','4.858'),('147.82','147.98'),('-13','-13'),('13','22'),('-13','-19'),('13','19'),('-20','-16'),('20','17'),('20675','48777'),('6814','7852'),('0.0383','0.0698'),('6814','7852'),('0','0'),('297','334'),('1.045','1.028'),('0.0313','0.0331'),('0.0812','0.0879'),('0.0320','0.0363'),('0.0819','0.0900'),('0.49','0.94'),('-1.24','-0.74')]
num=re.compile(r'^(-?\d+(?:\.\d+)?)(?:\((\d+)\))?$')
check(len(tabs['table-s1']['rows'])==len(s1raw),'S1 all36 expanded properties')
for rn,(r,expected) in enumerate(zip(tabs['table-s1']['rows'],s1raw),1):
    check([c['column'] for c in r['cells']]==['A','B'],f'S1 row{rn} column identity')
    for c,raw in zip(r['cells'],expected):
        check(c['raw_text']==raw,c['id']+' source raw token')
        match=num.fullmatch(raw)
        if match:
            val=decimal.Decimal(match[1]); unc=decimal.Decimal(match[2])*(decimal.Decimal(10)**val.as_tuple().exponent) if match[2] else None
            check(close(c['value'],float(val)),c['id']+' numeric value');check(close(c['uncertainty'],float(unc) if unc is not None else None),c['id']+' uncertainty')
        else:check(c['value'] is None,c['id']+' categorical not numeric')
        if rn in [16,17]:check(c['comparison']==('>' if rn==16 else '<'),c['id']+' strict bound')
        if rn in range(18,24):check(c['comparison']==('>=' if rn%2==0 else '<='),c['id']+' inclusive hkl bound')
        check(c['evidence'][0]['pdf_page']==(13 if rn<18 else 14),c['id']+' source page')
# All evidence references must name the actual source and a supplied page.
evidence_count=0
def walk(x,p=''):
    global evidence_count
    if isinstance(x,dict):
        if 'source_sha256' in x and 'document_role' in x and 'pdf_page' in x:
            evidence_count+=1;role=x['document_role'];check(x['source_sha256']==source_hashes.get(role),p+' source hash');check(isinstance(x['pdf_page'],int) and 1<=x['pdf_page']<=({'main':8,'si':26}.get(role,0)),p+' valid page')
        for k,v in x.items():walk(v,p+'/'+k)
    elif isinstance(x,list):
        for n,v in enumerate(x):walk(v,p+'/'+str(n))
walk(D)
def pointer(doc,p):
    for key in p.split('/')[1:]:doc=doc[int(key)] if isinstance(doc,list) else doc[key.replace('~1','/').replace('~0','~')]
    return doc
for u in I['inventory_units']:
    o=pointer(D,u['json_pointer']);check(o['id']==u['id'],'inventory pointer '+u['id'])
check(len(I['inventory_units'])==len(set(u['id'] for u in I['inventory_units'])),'unique inventory units')
factids={x['id']:x for x in D['facts']}
for route in D['protocols']:
    for op in route['operations']:
        for fid in op['source_fact_ids']:check(fid in factids,op['id']+' fact reference '+fid)
        for q in op['quantities']:check(any(q in factids[f]['quantities'] for f in op['source_fact_ids']),op['id']+' source quantity '+q['meaning'])
for st in D['stocks']:
    for q in st['quantities']:check(q in factids[st['source_fact_id']]['quantities'],st['id']+' source quantity '+q['meaning'])
for ref in D['references']:
    e=ref['evidence'][0];txt=(P/'private/text'/f"{e['document_role']}-{e['pdf_page']:02d}.txt").read_text('utf8')
    check(re.sub(r'\s+','',ref['raw_text']) in re.sub(r'\s+','',txt),ref['id']+' source-text inclusion');check(ref['full_text_read'] is False,ref['id']+' does not claim referenced-paper full text read')
check([x['number'] for x in D['references'] if x['document_role']=='main']==list(range(1,28)),'all27main reference entries')
check([x['number'] for x in D['references'] if x['document_role']=='si']==[1,2,3],'all3SI reference entries')
# Preserve null source unit finding correction and all defining parameter boundaries.
mw=next(q for q in factids['lian2021-chemicals']['quantities'] if q['meaning']=='PS average Mw')
check(mw['unit'] is None and mw['value']==280000 and mw['approximate'] is True,'PS Mw no unreported unit')
expected={'lian2021-bulk-a-charge':[2,1,800],'lian2021-bulk-b-variant':[1,1,800,4],'lian2021-nc-stock':[1,.5,2000],'lian2021-nc-injection':[500,5,500],'lian2021-nc-recovery':[7000,3],'lian2021-spincoat-stock':[2,1,1000],'lian2021-spincoat-deposit':[200,2000,40,80,30],'lian2021-a-blue-decay':[459,.89,3.99,2.29],'lian2021-a-yellow-decay':[612,.6,10.04,9.82],'lian2021-nc-yellow-decay':[614,.7,10,9.72],'lian2021-nc-blue-decay':[465,1.18,12.89,2.56],'lian2021-dft-gaps':[3.4,3.47,4.4,4.46],'lian2021-acquisition-beta':[.4,16,400]}
for fid,vals in expected.items():check([q['value'] for q in factids[fid]['quantities']]==vals,'independent source recipe/outcome fixture '+fid)
check([x['blue_yellow_mass_parts'] for x in D['samples'] if x['id'].startswith('film-blend-')]==[[1,0],[1,3],[1,2],[2,3],[0,1]],'five exact weight-ratio scopes')
# Fresh source rendering proves selected crops retain actual original pixels/bounds.
docs={r:pymupdf.open(p) for r,p in source_paths.items()};cache={};pixel_count=0
for asset in M['assets']:
    p=Path(asset['path']);check(sha(p)==asset['sha256'],asset['id']+' image hash');check(asset['whole_source_page'] is False,asset['id']+' selected source crop only')
    key=(asset['source_role'],asset['pdf_page'],asset['render_scale'])
    if key not in cache:
        pix=docs[key[0]][key[1]-1].get_pixmap(matrix=pymupdf.Matrix(key[2],key[2]),alpha=False)
        cache[key]=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
    fresh=cache[key].crop(tuple(asset['bbox_pixels_at_render']));im=Image.open(p).convert('RGB')
    check(fresh.size==im.size,asset['id']+' actual dimensions')
    same=fresh.size==im.size and ImageChops.difference(fresh,im).getbbox() is None
    check(same,asset['id']+' original pixel replay');pixel_count+=int(same)
for d in docs.values():d.close()
fail=[x for x in checks if not x['passed']]
result={'schema':'mattersyn.independent_extraction_checks.v1','auditor':'/root/norberg2004_extract','source_author':'/root/backlog_eta','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'proposal_freeze_sha256':sha(P/'package-freeze.json'),'revision':freeze['revision'],'status':'passed_mechanical_checks' if not fail else 'open_mechanical_findings','counts':{'checks':len(checks),'failed':len(fail),'S2_to_S9_numeric_tokens':cell_count,'table_cells':sum(len(r['cells']) for t in T['tables'] for r in t['rows']),'source_evidence_occurrences':evidence_count,'inventory_units':len(I['inventory_units']),'original_crop_pixel_replays':pixel_count},'failed_checks':fail,'bound_files':bound,'checks':checks,'manual_scope_separate':'Actual manual all34pages and53crops inspected; scientific findings and their resolution appear in independent-audit, not inferred from this script.'}
out=A/f"mechanical-checks-v{freeze['revision']}.json";out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':str(out),'sha256':sha(out),'counts':result['counts'],'failed':fail},ensure_ascii=False))
