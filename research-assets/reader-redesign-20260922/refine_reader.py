from pathlib import Path
import json,shutil
DIST=Path(__file__).resolve().parents[2]/'recipe-atlas/dist'
p=DIST/'reader-app.mjs';s=p.read_text(encoding='utf-8')
s=s.replace("uM:'µM'","uM:'µM',volume_parts:'volume parts',mass_percent:'wt%',volume_percent:'vol%'")
s=s.replace("m.formula||entry?.formula", "entry?.displayFormula||entry?.formula||m.formula")
s=s.replace("el('span','Reader edition 0.34','reader-version')", "el('span','Reviewed synthesis and evidence','reader-version')")
s=s.replace("r.sources[0].authors.split(',')[0]", "r.sources[0].authors.split(/[,;]/)[0]+' et al.'")
s=s.replace("if(materialId)url.searchParams.set('method',rid);", "url.searchParams.set('method',rid);")
s=s.replace("await mountReader(main,{recordId:r.record_id});", "await mountReader(main,{recordId:new URLSearchParams(location.search).get('method')||r.record_id});")
s=s.replace("recordId:params.get('method')||undefined", "recordId:params.get('method')||document.body.dataset.recordId||undefined")
# Retain the complete caption in a disclosure while the reader sees a short complete sentence.
s=s.replace("if(f.summary&&f.summary!==f.title)caption.append(el('p',f.summary));", "if(f.summary&&f.summary!==f.title){const first=f.summary.match(/^.{1,300}?[.!?](?:\\s|$)/)?.[0]?.trim();if(first)caption.append(el('p',first));caption.append(disclosure('Full source caption and qualifications',el('p',f.summary)));}")
s=s.replace("export function figureGallery(host,figures,r,category){", "function reviewURL(r,p={},anchor=''){const base=p.data_links?.full_review||('paper-review.html?id='+encodeURIComponent(r.lineage.source_group));return base+(base.startsWith('paper-review.html')?anchor:'');}\nexport function figureGallery(host,figures,r,category,presentation={}){")
s=s.replace("'paper-review.html?id='+encodeURIComponent(source)+'#source-'+(category==='property'?'properties':'structures')", "reviewURL(r,presentation,'#source-'+(category==='property'?'properties':'structures'))")
s=s.replace("figureGallery(sections[2],figs,r,'structure');", "figureGallery(sections[2],figs,r,'structure',presentation);")
s=s.replace("figureGallery(sections[3],figs,r,'property');", "figureGallery(sections[3],figs,r,'property',presentation);")
s=s.replace("'paper-review.html?id='+r.lineage.source_group+'#source-intuition'", "reviewURL(r,presentation,'#source-intuition')")
s=s.replace("link('Paper and SI review →','paper-review.html?id='+source.id)", "link('Source review →',source.id===r.lineage.source_group?reviewURL(r,presentation):sourceURL(source))")
# Source figure descriptions whose original image has not been verified stay explicit.
s=s.replace("const rows=[...unique.values()];if(!rows.length)return 0;", "const rows=[...unique.values()];const textOnly=figures.filter(f=>(f.category===category||f.categories?.includes(category))&&!(f.public_asset||f.asset));for(const f of textOnly)host.append(disclosure((f.title||f.id)+' · original image unavailable',el('p',f.summary||''),link('Source evidence →',reviewURL(r,presentation),'reader-data-link')));if(!rows.length)return textOnly.length;")
p.write_text(s,encoding='utf-8')
# Older named links receive the same shared Reader, while complete earlier editions remain reachable.
legacy={'murray-1993-method-1':'murray-1993-cdse-method1','murray-1993-method-2':'murray-1993-cdse-method2','alivisatos-2000':'peng-2000-cdse-typical','nakonechnyi-2017':'nakonechnyi-2017-zb-cdse-core'}
shell=(DIST/'material.html').read_text(encoding='utf-8')
for stem,rid in legacy.items():
    original=DIST/(stem+'.html');arch=DIST/(stem+'-evidence.html')
    if not arch.exists():shutil.copy2(original,arch)
    original.write_text(shell.replace('data-reader-page="material"','data-reader-page="material" data-record-id="'+rid+'"'),encoding='utf-8')
p=DIST/'data/reader-presentation.json';v=json.loads(p.read_text(encoding='utf-8'))
v['status']='integrated_reader_metadata'
for r in v['records'].values():
    if r['source_id']=='peng2000':r['data_links']['full_review']='alivisatos-2000-evidence.html'
p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Update shared-version imports so an already-open published site reloads the changed code.
p=DIST/'illustrated-record.mjs';s=p.read_text(encoding='utf-8').replace('0.33.0-r1','0.34.0');p.write_text(s,encoding='utf-8')
print('Reader refinements and preserved legacy evidence routes applied.')
