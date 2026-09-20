"""Add exact raw first-page-text projection fields; retain source metadata."""
from pathlib import Path
import subprocess,json,hashlib,collections
B=Path(__file__).resolve().parent
R=Path(r'[local path redacted]')
C=['git','-c','safe.directory='+R.as_posix(),'-C',str(R)]
report=B/'public-repository-exclusion-proposal-20260920.json'
d=json.loads(report.read_text(encoding='utf-8'))
assert subprocess.check_output(C+['rev-parse','HEAD'],text=True).strip()==d['head']
paths=[p for p in subprocess.check_output(C+['grep','-l','-z','-F','firstPagePreviewPrivate'],text=True,encoding='utf-8').split('\0')if p]
fields=[];complete=[];files=[]
for p in paths:
 if not p.endswith(('.json','.jsonl','.tmp')):continue
 raw=(R/p).read_bytes()
 try:
  objects=[json.loads(x) for x in raw.decode('utf-8-sig').splitlines() if x.strip()] if p.endswith('.jsonl') else [json.loads(raw)]
 except (ValueError,UnicodeError):continue
 count=0
 def walk(v,ptr=''):
  global count
  if isinstance(v,dict):
   for k,x in v.items():
    path=ptr+'/'+k.replace('~','~0').replace('/','~1')
    if k=='firstPagePreviewPrivate' and isinstance(x,str):
     count+=1;fields.append({'path':p,'json_pointer':path,'value_characters':len(x),'action':'omit_raw_first_page_text_field_in_public_projection','preserve_parent_metadata':True})
     if v.get('pageCount')==1 and len(x)>=v.get('characterCount',10**20) and v.get('characterCount',0)>0:
      complete.append({'path':p,'json_pointer':path,'document_extracted_characters':v['characterCount'],'field_characters':len(x)})
    else:walk(x,path)
  elif isinstance(v,list):
   for i,x in enumerate(v):walk(x,ptr+'/'+str(i))
 for i,obj in enumerate(objects):walk(obj,('/jsonl-row/'+str(i+1)) if p.endswith('.jsonl') else '')
 if count:files.append({'path':p,'fields':count,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})

add={'schema':'mattersyn-raw-source-page-field-exclusions/1','head':d['head'],'field_name':'firstPagePreviewPrivate',
 'current_files_with_field':len(files),'current_field_instances':len(fields),
 'raw_first_page_text_characters':sum(x['value_characters'] for x in fields),
 'one_page_whole_extracted_document_instances':len(complete),
 'one_page_whole_extracted_document_unique_cache_records':sum('/private/content-cache/'in x['path']for x in complete),
 'action':'Omit only this raw source-text field in the public projection of every historical JSON object; retain metadata, hash/page locators, structured fact records and audit reports unchanged in the local evidence archive.',
 'history_policy':'Apply field-name projection recursively to every historical tree, not just current HEAD. Exact paths/pointers below are current-state evidence; field predicate covers earlier payload versions too.',
 'files':files,'fields':fields,'whole_single_page_examples':complete,
 'scope_limit':'First-page raw text can equal the entire extracted text for one-page documents. Character equality is a source-equivalence check, not proof OCR captured every visible glyph. This does not certify arbitrary other embedded-text payload names.'}
p=B/'public-repository-raw-page-fields-20260920.json';p.write_text(json.dumps(add,indent=2)+'\n',encoding='utf-8')
archive=B/'public-repository-exclusion-proposal-20260920-before-embedded-field-addendum.json'
if not archive.exists():archive.write_bytes(report.read_bytes())
d['raw_source_text_embedded_field_projection']={k:v for k,v in add.items()if k not in ('files','fields','whole_single_page_examples')}
d['raw_source_text_embedded_field_projection']['exact_manifest']={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
d['metadata_sample_inspection_note']='Retain metadata JSON, but initial sample inspection was insufficient: firstPagePreviewPrivate stores raw first-page text, occasionally an entire one-page source. The exact field projection addendum supersedes any blanket retain-metadata assumption.'
d['future_sync_policy']['required_extra_rules'].append('Recursively omit firstPagePreviewPrivate raw-text fields in public JSON projections, including cached manifests and historical versions; do not delete parent metadata.')
report.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=B/'public-repository-exclusion-proposal-20260920.md'
with md.open('a',encoding='utf-8')as f:f.write(f'''\nEmbedded-text correction: **{len(fields):,} `firstPagePreviewPrivate` fields in {len(files):,} current files** contain raw first-page text ({add['raw_first_page_text_characters']:,} characters). **61 unique cache records** have a one-page source whose entire extracted text is stored in this field; copies occur in aggregate manifests. Omit this field recursively in every public historical JSON projection while retaining parent metadata. The exact path/pointer manifest is `public-repository-raw-page-fields-20260920.json`; it supersedes the initial sampled-metadata blanket retention statement. This is a field-only projection requirement in addition to the path exclusions.\n''')
print(json.dumps({k:add[k]for k in ['current_files_with_field','current_field_instances','raw_first_page_text_characters','one_page_whole_extracted_document_instances','one_page_whole_extracted_document_unique_cache_records']},indent=2))
print('FINAL_REPORT_SHA256',hashlib.sha256(report.read_bytes()).hexdigest())
print('FIELD_MANIFEST_SHA256',hashlib.sha256(p.read_bytes()).hexdigest())
