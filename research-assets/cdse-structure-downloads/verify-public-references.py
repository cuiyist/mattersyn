import json,urllib.request,urllib.error
from pathlib import Path
root=Path(__file__).resolve().parent
urls={
 'materials-project-wurtzite':'https://materialsproject.org/materials/mp-1070',
 'materials-project-datacite':'https://api.datacite.org/dois/10.17188/1187302',
 'cod-original':'https://www.crystallography.net/cod/9016056.cif'}
reports=[]
for key,url in urls.items():
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json' if 'datacite' in key else '*/*'})
        with urllib.request.urlopen(req,timeout=30) as response:
            data=response.read();status=response.status;final=response.url
        ext='json' if 'datacite' in key else 'cif' if key=='cod-original' else 'html'
        filename=key+'-public-response.'+ext
        (root/filename).write_bytes(data)
        report={'key':key,'url':url,'status':status,'finalUrl':final,'savedFile':filename,'bytes':len(data)}
        if 'datacite' in key:
            a=json.loads(data)['data']['attributes']
            report.update({k:a.get(k) for k in ['titles','creators','publisher','publicationYear','url','descriptions','relatedIdentifiers']})
        reports.append(report)
    except Exception as exc:
        reports.append({'key':key,'url':url,'error':str(exc)})
(root/'public-reference-fetch-report.json').write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps(reports,indent=2))
