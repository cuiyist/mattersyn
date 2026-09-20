"""Read small author-hosted dataset in memory; persist aggregate audit only, not recipes."""
import io,json,urllib.request,hashlib,collections,csv
from pathlib import Path
import openpyxl
ROOT=Path(__file__).resolve().parent
BASE='https://raw.githubusercontent.com/Sharpiless/Nanocrystals-Deep-Learning/main/'
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'MatterSyn-research-source-audit'})
    return urllib.request.urlopen(req,timeout=60).read()
out={'repository':'https://github.com/Sharpiless/Nanocrystals-Deep-Learning','paperDoi':'10.1021/acsnano.5c09134','auditDate':'2026-09-16','downloadPolicy':'Small structured source workbook inspected in memory; no recipe rows or full external corpus republished.'}
repo=json.loads(get('https://api.github.com/repos/Sharpiless/Nanocrystals-Deep-Learning'))
out['githubLicenseMetadata']=repo.get('license')
tree=json.loads(get('https://api.github.com/repos/Sharpiless/Nanocrystals-Deep-Learning/git/trees/main?recursive=1'))
out['commitSha']=tree['sha'];out['licensePaths']=[x['path'] for x in tree['tree'] if 'license' in x['path'].lower()]
out['relevantDataFiles']=[{'path':x['path'],'size':x.get('size'),'sha':x['sha']} for x in tree['tree'] if x['type']=='blob' and (x['path'].startswith('Source data/') or x['path'].startswith('data/'))]
readme=get(BASE+'README.md').decode();out['readmeLicenseText']=readme[readme.lower().find('license'):][:1500]
data=get(BASE+'Source%20data/Raw%20recipe%20dataset.xlsx')
out['workbook']={'url':BASE+'Source%20data/Raw%20recipe%20dataset.xlsx','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'sheets':[]}
wb=openpyxl.load_workbook(io.BytesIO(data),read_only=True,data_only=True)
for sh in wb:
    rows=list(sh.iter_rows(values_only=True));nonempty=[r for r in rows if any(v is not None for v in r)]
    header=list(nonempty[0]) if nonempty else []
    # Header labels and aggregate column statistics; no full records.
    stats=[]
    for j,h in enumerate(header):
        vals=[r[j] if j<len(r) else None for r in nonempty[1:]]
        nums=[v for v in vals if isinstance(v,(int,float))]
        strings=[str(v) for v in vals if v is not None]
        stats.append({'column':h,'nonempty':sum(v is not None for v in vals),'numeric':len(nums),'zero':sum(v==0 for v in nums),'min':min(nums) if nums else None,'max':max(nums) if nums else None,'distinctCount':len(set(strings))})
    out['workbook']['sheets'].append({'name':sh.title,'physicalRows':sh.max_row,'physicalColumns':sh.max_column,'nonemptyRows':len(nonempty),'header':header,'columnStats':stats})
csvdata=get(BASE+'data/0309_classification_and_reg-raw-v3.csv');rows=list(csv.DictReader(io.StringIO(csvdata.decode('utf-8-sig'))))
out['modelCsv']={'url':BASE+'data/0309_classification_and_reg-raw-v3.csv','bytes':len(csvdata),'sha256':hashlib.sha256(csvdata).hexdigest(),'rows':len(rows),'columns':list(rows[0]) if rows else [],'columnsWithDoiInName':[c for c in rows[0] if 'doi' in c.lower()] if rows else []}
out['loaderFiles']=[x['path'] for x in tree['tree'] if x['type']=='blob' and x['path'].startswith('utils/')]
(ROOT/'gu2025-repository-audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2,ensure_ascii=False))
