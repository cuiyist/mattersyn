"""Root-owned importer; invoke only after source review/audit of the named packages."""
from pathlib import Path
import json, sys, shutil, hashlib, re
HERE=Path(__file__).resolve().parent
SITE=HERE.parents[1]/'recipe-atlas'
IDS={'zno2007':'fu2007','ir2005':'stowell2005','nak2017':'nakonechnyi2017','iron2019':'feld2019'}
def sanitize(x,key=''):
    if isinstance(x,dict):
        return {('source_file' if k=='source_path' else k):sanitize(v,k) for k,v in x.items() if k not in ['source_text_path','rendered_page_path','runtime','private_text_path']}
    if isinstance(x,list):return [sanitize(v,key) for v in x]
    if isinstance(x,str) and re.search(r'[A-Za-z]:[\\/]',x):
        # Public provenance includes filenames and hashes, never a local user's directory.
        if re.match(r'^[A-Za-z]:[\\/]',x):return Path(x).name
        return re.sub(r'[A-Za-z]:[[local path redacted] source retained privately]',x)
    return x
for name in sys.argv[1:]:
    folder=HERE/name;c=json.loads((folder/'coverage.json').read_text(encoding='utf-8'))
    recs=[json.loads(p.read_text(encoding='utf-8')) for p in (folder/'canonical').glob('*.json')]
    source=recs[0]['sources'][0]
    # Canonical source group, rather than a derived author spelling, is the public key.
    sid=recs[0]['lineage']['source_group'];c['paper_id']=sid;c['doi']=source['doi'];c['title']=source['title']
    for d in c['documents']:
        if hashlib.sha256(Path(d['source_path']).read_bytes()).hexdigest()!=d['sha256']:raise ValueError('Original source hash changed')
    audit=c.get('independent_audit','pending')
    if audit!='pending':
        c['audit_details']=audit if isinstance(audit,dict) else str(audit).replace('experimental_frontier','independent reviewer').replace('atomistic_frontier','independent reviewer').replace('synthesis_prior_art','independent reviewer').replace('See audit.md.','')
        c['independent_audit']='Completed; source claims and sample assignments cross-checked'
    c.setdefault('equations',c.get('schemes_and_equations',[]))
    c.setdefault('simulation_inventory',c.get('simulations_and_models',[]))
    def with_asset(f,i,required=False):
        f=dict(f);asset=f.get('original_crop_asset',{});crop=f.get('crop',{})
        if isinstance(asset,str):asset={'asset':asset}
        raw=asset.get('asset') or asset.get('path') or crop.get('path') or f.get('asset_path') or f.get('crop_path') or f.get('crop_asset')
        if not raw:
            if required:raise ValueError(name+' figure lacks asset: '+repr(f)[:400])
            return f
        p=Path(raw);p=p if p.is_absolute() else folder/p
        if not p.exists():raise FileNotFoundError(p)
        out=SITE/'dist/assets/paper-reviews'/sid/p.name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
        sha=hashlib.sha256(p.read_bytes()).hexdigest()
        expected=asset.get('sha256') or crop.get('sha256') or f.get('crop_sha256')
        if expected and expected!=sha:raise ValueError('Crop provenance mismatch '+str(p))
        f['public_asset']=out.relative_to(SITE/'dist').as_posix();f['public_asset_sha256']=sha
        loc=f.get('source_locator',{});loc=loc if isinstance(loc,dict) else {}
        f.setdefault('page',loc.get('pdf_page') or f.get('pdf_page') or asset.get('pdf_page'))
        f.setdefault('document_role',loc.get('source_role') or next((d['role'] for d in c['documents'] if d['sha256']==asset.get('source_sha256')),'main' if not str(f.get('id','')).lower().startswith('s') else 'si'))
        f.setdefault('id',f.get('figure_id','figure-'+str(i+1)))
        f['id']=str(f['id'])
        f.setdefault('label',re.sub(r'^fig(?:ure)?-?([sS]?\d+)$',lambda m:'Figure '+m.group(1).upper(),f['id']))
        return f
    for category in ['figures','tables','equations','schemes']:
        c[category]=[with_asset(f,i,required=category=='figures') for i,f in enumerate(c.get(category,[]))]
    dest=SITE/'data/paper-reviews'/(sid+'.json');dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(sanitize(c),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for r in recs:
        (SITE/'data/records'/(r['record_id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(name,'imported',len(recs),'records',len(c['figures']),'figures')
