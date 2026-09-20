"""Preserve source v1 and apply five bounded independently requested corrections."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,subprocess,sys
P=Path(__file__).resolve().parent;OLD=P/'source-extraction-revision-1';H='18e1e1e2c220c108f74e079043bad72a44551f798be9fb28ded314b49e1622c6'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha(P/'package-freeze.json')==H and not OLD.exists(),'Preserve revisions; do not repeat mutations.'
old=read(P/'package-freeze.json');OLD.mkdir();mapping={}
for path,h in old['bound_files'].items():
 src=Path(path);assert sha(src)==h,path;dst=OLD/src.relative_to(P);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(dst)==h;mapping[path]={'archive_path':str(dst),'sha256':h}
shutil.copy2(P/'package-freeze.json',OLD/'package-freeze.json');write(OLD/'preserved-file-map.json',mapping)
def edit(name,pairs):
 p=P/name;s=p.read_text(encoding='utf-8')
 for before,after in pairs:assert before in s,(name,before);s=s.replace(before,after)
 p.write_text(s,encoding='utf-8')
edit('source_author_data.py',[
('low crystallinity/yield','low yield'),
("F('d4-solution',2,'Figure 4 and preceding discussion'","F('d4-solution',2,'Al-only precursor paragraph before the Figure 3 discussion'"),
("F('d2-size',3,'Figure 3 discussion'","F('d2-size',3,'Discussion below Figure 4: reciprocal-space ZnO dimensions'"),
("F('mw-middle-outcome',5,'Laboratory Synthesis and Figure 8'","F('mw-middle-outcome',5,'Laboratory Synthesis and Figure 9 inset'"),
('This workup is not automatically assigned to D-series solutions or in situ capillary observations.','Apply this workup separately to the microwave, SCF and autoclave powders; these are alternative specimens, never a pooled charge. This workup is not automatically assigned to D-series solutions or in situ capillary observations.')])
with (P/'source_author_data.py').open('a',encoding='utf-8')as out:out.write("\nF('cited-zno-heating',3,'Discussion below Figure 4, cited reference 42','Cited ZnO formation-temperature context','The authors cite prior ZnO formation on heating aqueous Zn(NO3)2/NaOH at 150-350 °C. This range belongs to cited literature, not a demonstrated heating condition of the current room-temperature D2 solution; the cited full paper was not independently read.','literature-zno-formation',[Q('cited ZnO formation-temperature interval','150-350','degC')],['G4'],kind='cited_context')\n")
edit('build_extraction.py',[
("for stock,idx in [(stocks[1],0),(stocks[2],1),(stocks[3],2)]:stock['quantities']=[stock['quantities'][idx]]", "for stock,idx in [(stocks[1],0),(stocks[2],1),(stocks[3],2)]:stock['quantities']=[stock['quantities'][idx]]\nbase_stock=next(s for s in stocks if s['id']=='insitu-base-solutions')\nbase_stock['quantities']=[q for q in base_stock['quantities']if q['meaning']=='NaOH solution aliquot']\nbase_stock['notes']+=' Only the 1.00 mL NaOH-solution aliquot applies to this stock entry; the nitrate aliquot and final Zn/Al concentrations belong to the mixed reaction, retained in sommer2020-insitu-mix and the insitu-mix operation.'\nbase_stock['mixed_reaction_context']={'source_fact_id':SID+'-insitu-mix','protocol_id':'insitu-nitrate','operation_id':'insitu-mix'}"),
("'id':i,'title':title,'kind':kind,'sample_ids':sids,'operations':operations,'source_table_ids'", "'id':i,'title':title,'kind':kind,'sample_ids':sids,'operations':operations,'specimen_application':'Each listed specimen is processed separately; grouped reactor-family inputs are alternatives, never a pooled physical charge.','source_table_ids'")])
edit('validate_and_freeze.py',[("'revision':1,'status'","'revision':2,'status'")])
subprocess.run([sys.executable,'-B','-X','utf8',str(P/'build_extraction.py')],check=True)
before=read(OLD/'source-facts.json');after=read(P/'source-facts.json')
def diff(a,b,path=''):
 if type(a)!=type(b):return[{'pointer':path,'before':a,'after':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   ptr=path+'/'+str(k).replace('~','~0').replace('/','~1')
   if k not in a:out.append({'pointer':ptr,'before_absent':True,'after':b[k]})
   elif k not in b:out.append({'pointer':ptr,'before':a[k],'after_absent':True})
   else:out+=diff(a[k],b[k],ptr)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return[{'pointer':path,'before':a,'after':b}]
  return[d for i,(x,y)in enumerate(zip(a,b))for d in diff(x,y,path+'/'+str(i))]
 return[]if a==b else[{'pointer':path,'before':a,'after':b}]
def strip_es(x):
 if isinstance(x,dict):return{k:strip_es(v)for k,v in x.items()if k not in['evidence']}
 if isinstance(x,list):return[strip_es(v)for v in x]
 return x
assert len(after['facts'])==len(before['facts'])+1
for a,b in zip(before['facts'],after['facts']):assert strip_es(a['quantities'])==strip_es(b['quantities']),a['id']
assert read(OLD/'source-tables.json')['tables']==read(P/'source-tables.json')['tables']
for k in ['equations','figures','materials','sample_contexts','references','conflicts','missingness']:assert before[k]==after[k],k
for a,b in zip(before['protocols'],after['protocols']):
 assert a['id']==b['id']
 for x,y in zip(a['operations'],b['operations']):assert strip_es(x['quantities'])==strip_es(y['quantities']),x['id']
for a in read(OLD/'original-assets-manifest.json')['assets']:assert sha(a['path'])==a['sha256'],a['id']
history={'schema':'mattersyn-source-correction-history/1','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'from_revision':1,'to_revision':2,'prior_freeze_sha256':H,'prior_archive':str(OLD),'requesting_auditor':'/root/norberg2004_extract','requesting_audit_path':str(P/'source-independent-audit/independent-audit-v1.json'),'requesting_audit_sha256':sha(P/'source-independent-audit/independent-audit-v1.json'),'categories':['Remove unsupported low-crystallinity wording; retain low yield.','Retain only NaOH aliquot in base-stock quantities; keep existing mixed-reaction amounts and add explicit context link.','Correct three source locator labels and derived evidence copies.','Add one clearly cited-context 150-350 °C ZnO formation range; no current D2 synthesis inference.','Explicitly apply workup to separate source specimens; never pool grouped reactor products.'],'source_facts_delta':diff(before,after),'invariants':{'all_existing_136_fact_quantity_values_and_types_unchanged':True,'all_existing_operation_quantity_values_and_types_unchanged':True,'all_222_table_body_cells_unchanged':True,'all_20_crop_bytes_unchanged':True,'all_formulas_figures_materials_contexts_references_conflicts_gaps_unchanged':True},'counts_before':old['counts'],'counts_after':read(P/'source-inventory.json')['counts']}
write(P/'source-correction-history.json',history)
subprocess.run([sys.executable,'-B','-X','utf8',str(P/'validate_and_freeze.py')],check=True)
new=read(P/'package-freeze.json');new.update(previous_revision={'path':str(OLD/'package-freeze.json'),'sha256':H},correction_history_sha256=sha(P/'source-correction-history.json'));write(P/'package-freeze.json',new)
print('FINAL_FREEZE',sha(P/'package-freeze.json'));print('HISTORY',sha(P/'source-correction-history.json'))
