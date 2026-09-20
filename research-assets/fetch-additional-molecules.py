import concurrent.futures,json,time,urllib.request,urllib.parse,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RAW=ROOT/'new-molecular-assets';RAW.mkdir(exist_ok=True)
specs=[('tms2se','bis(trimethylsilyl)selenide','C6H18SeSi2'),('hexane','hexane','C6H14'),('pyridine','pyridine','C5H5N'),('chloroform','chloroform','CHCl3'),('thf','tetrahydrofuran','C4H8O'),('tmscl','chlorotrimethylsilane','C3H9ClSi'),('lithium-triethylborohydride','lithium triethylborohydride','C6H16BLi'),('argon','argon','Ar')]
BASE='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound'
def get(url):
    for trial in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'MatterSyn reference asset preparation'}),timeout=45) as r:return r.read()
        except urllib.error.HTTPError as ex:
            if ex.code not in [429,500,502,503] or trial==3:raise
            time.sleep(1+trial)
def fetch(spec):
    ident,name,expected=spec
    nameurl=BASE+'/name/'+urllib.parse.quote(name,safe='')+'/cids/JSON'
    lookup=json.loads(get(nameurl));cids=lookup['IdentifierList']['CID']
    if ident=='lithium-triethylborohydride':
        cids=[23664628]+[i for i in cids if i!=23664628]
    chosen=None
    for cid in cids:
        url=BASE+f'/cid/{cid}/property/MolecularFormula,IUPACName,CanonicalSMILES/JSON'
        data=get(url);p=json.loads(data)['PropertyTable']['Properties'][0]
        if p['MolecularFormula']==expected:
            chosen=(cid,url,p,data);break
    assert chosen,(ident,expected,cids)
    cid,url,prop,data=chosen
    (RAW/f'{ident}-pubchem-identity.json').write_bytes(data)
    rec={'id':ident,'nameQuery':name,'pubchemCid':cid,'expectedFormula':expected,'property':prop,'propertyUrl':url,'nameLookupUrl':nameurl,'nameLookup':lookup}
    for dim in ['3d','2d']:
        u=BASE+f'/cid/{cid}/SDF?record_type={dim}'
        file=f'{ident}-pubchem-{cid}-{dim}.sdf'
        if (RAW/file).exists():
            rec[dim]={'file':file,'url':u,'status':'available'}
            continue
        try:
            sdf=get(u)
            file=f'{ident}-pubchem-{cid}-{dim}.sdf';(RAW/file).write_bytes(sdf)
            rec[dim]={'file':file,'url':u,'status':'available'}
        except urllib.error.HTTPError as ex:rec[dim]={'url':u,'status':ex.code}
    print(ident,cid,prop['MolecularFormula'],rec['3d']['status'],rec['2d']['status'],flush=True)
    (RAW/f'{ident}-retrieval.json').write_text(json.dumps(rec,indent=2)+'\n')
    return rec
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(fetch,specs))
(ROOT/'new-molecular-pubchem-identities.json').write_text(json.dumps(results,indent=2)+'\n')
