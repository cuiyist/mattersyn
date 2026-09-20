from pathlib import Path
import sys,json,hashlib,datetime,re
B=Path(__file__).resolve().parent
sys.path[:0]=[r'[local path redacted]',r'[local path redacted]',r'[local path redacted]']
import fitz,gemmi
from PIL import Image,ImageDraw
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,obj):Path(p).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
prep=json.loads((B/'source-preparation.json').read_text('utf-8'));now=datetime.datetime.now(datetime.timezone.utc).isoformat()
for d in prep['documents']:assert sha(d['source_path'])==d['sha256']
src=Path(prep['documents'][2]['source_path']);raw=src.read_text('utf-8')
strict={}
try:
 g=gemmi.cif.read_file(str(src));strict={'status':'parsed_original','blocks':[b.name for b in g]}
except Exception as ex:strict={'status':'original_rejected','exception':str(ex)}
# Lexical preservation accepts the source's out-of-block reference field explicitly.
token_pattern=re.compile(r"(?m)^;[^\n]*\n[\s\S]*?^;[^\n]*|(?:'[^'\n]*(?:'(?!\s|$)[^'\n]*)*'|\"[^\"\n]*(?:\"(?!\s|$)[^\"\n]*)*\"|[^\s#]+)|#[^\n]*")
tokens=[]
for match in token_pattern.finditer(raw):
 t=match.group()
 if t.startswith('#'):continue
 if t.startswith(';'):value=t[1:t.rfind(';')]
 elif t[0:1] in ["'",'"'] and t[-1:]==t[0]:value=t[1:-1]
 else:value=t
 tokens.append({'raw_token':t,'value':value,'line_start':raw.count('\n',0,match.start())+1,'line_end':raw.count('\n',0,match.end())+1})
scalars=[];loops=[];blocks=[];i=0;block=None
def reserved(t):return t['raw_token']=='loop_' or t['raw_token'].startswith(('data_','save_','_'))
while i<len(tokens):
 t=tokens[i]
 if t['raw_token'].startswith('data_'):block=t['raw_token'][5:];blocks.append({'name':block,'line':t['line_start']});i+=1
 elif t['raw_token']=='loop_':
  start=t['line_start'];i+=1;tags=[]
  while i<len(tokens) and tokens[i]['raw_token'].startswith('_'):tags.append(tokens[i]);i+=1
  values=[]
  while i<len(tokens) and not reserved(tokens[i]):values.append(tokens[i]);i+=1
  assert tags and len(values)%len(tags)==0,(tags,len(values))
  rows=[values[j:j+len(tags)] for j in range(0,len(values),len(tags))]
  loops.append({'id':f'cif-loop-{len(loops)+1}','block':block,'line_start':start,'tags':[x['value'] for x in tags],'tag_tokens':tags,'row_count':len(rows),'rows':[{tag['value']:v for tag,v in zip(tags,row)} for row in rows]})
 elif t['raw_token'].startswith('_'):
  assert i+1<len(tokens) and not reserved(tokens[i+1]),t
  scalars.append({'id':f'cif-scalar-{len(scalars)+1}','block':block,'tag':t['value'],'tag_line':t['line_start'],'token':tokens[i+1]});i+=2
 else:raise AssertionError(('unhandled CIF token',t))
# Valid data-block content is parsed independently without changing/writing original.
body=raw[raw.index('data_krace01'):]
body_doc=gemmi.cif.read_string(body);g=body_doc.sole_block()
for s in scalars:
 if s['block'] is not None:
  expected=s['token']['value'].strip('\r\n')
  native=g.find_value(s['tag']);observed=native if native in ['?','.'] else gemmi.cif.as_string(native)
  assert observed.strip('\r\n')==expected,(s['tag'],repr(observed),repr(expected))
for l in loops:
 for tag in l['tags']:
  native=list(g.find_values(tag));assert len(native)==l['row_count']
  assert [x if x in ['?','.'] else gemmi.cif.as_string(x) for x in native]==[row[tag]['value'] for row in l['rows']],tag
inventory={'schema':'mattersyn-lossless-cif-source-inventory/1','source_id':'evans2010','author':'/root/norberg2004_extract','created_at':now,'source_path':str(src),'source_sha256':sha(src),'scope':'Reported single-crystal molecular species9 only; not a PbSe/CdSe quantum-dot coordinate pair.','raw_file_original_unchanged':True,'parser':{'gemmi_version':gemmi.__version__,'original_file':strict,'data_block_only_in_memory':'parsed by Gemmi with scalar and every loop-cell lexical comparison; original prefix retained separately, no repaired CIF file written'},'blocks':blocks,'scalar_count':len(scalars),'loop_count':len(loops),'loop_rows':{l['id']:l['row_count'] for l in loops},'total_loop_cells':sum(l['row_count']*len(l['tags']) for l in loops),'scalars':scalars,'loops':loops,'raw_lexical_token_count':len(tokens),'missing_value_policy':'All ?, . and parenthesized uncertainties remain literal source tokens. No occupancy/coordinate/sign inferred. H atoms labelled calc/R in original are refinement-model positions, not independently located measurements.','independent_scientific_audit':'pending','eligible_training':False}
save(B/'cif-source-inventory.json',inventory)

O=B/'reader-assets'/'selected-originals';O.mkdir(exist_ok=True)
spec=[('figure-1','main',1,[302,161,551,317]),('table-1','main',1,[302,319,551,535]),('scheme-1','main',2,[39,38,287,249]),('scheme-2','main',2,[302,38,551,146]),('figure-2','main',3,[39,39,551,260])]
for n,page,top,bottom in [(1,3,68,586),(2,4,80,301),(3,5,67,638),(4,6,219,682),(5,7,330,592),(6,9,81,601),(7,10,81,633),(8,11,67,525),(9,12,67,282),(10,13,81,508),(11,14,67,334),(12,15,231,488),(13,17,32,350),(14,18,67,346),(15,20,67,404),(16,20,405,712)]:spec.append((f'figure-S{n}','si',page,[85,top,537,bottom]))
spec += [('scheme-S1','si',16,[103,67,509,319]),('scheme-S13-unnumbered','si',13,[85,546,339,608]),('table-S7-composition','si',7,[85,68,535,173]),('calculation-S21-yield','si',21,[85,80,535,486])]
pdfs={'main':fitz.open(prep['documents'][0]['source_path']),'si':fitz.open(prep['documents'][1]['source_path'])};assets=[]
for ident,role,page,rect in spec:
 p=pdfs[role][page-1];pix=p.get_pixmap(matrix=fitz.Matrix(220/72,220/72),clip=fitz.Rect(rect),alpha=False)
 target=O/(ident+'.png');pix.save(target)
 assets.append({'id':ident,'source_role':role,'pdf_page':page,'printed_page':str(10972+page) if role=='main' else f'S{page}','source_path':prep['documents'][0 if role=='main' else 1]['source_path'],'source_sha256':prep['documents'][0 if role=='main' else 1]['sha256'],'path':str(target),'sha256':sha(target),'crop_pdf_points':rect,'dpi':220,'renderer':'PyMuPDF '+fitz.version[0],'pixel_dimensions':[pix.width,pix.height],'pixel_policy':'Original PDF crop; no redraw, artificial enhancement or data reconstruction.','author_visual_inspection':'pending'})
save(B/'selected-original-assets.json',{'schema':'mattersyn-original-evidence-assets/1','source_id':'evans2010','created_at':now,'assets':assets,'counts':{'figure_table_scheme_items':23,'additional_inline_table_and_calculation':2,'total_assets':25},'independent_audit':'pending'})
contacts=[]
for start in range(0,len(assets),5):
 subset=assets[start:start+5];sheet=Image.new('RGB',(1500,1000),'#e8edf2');dr=ImageDraw.Draw(sheet)
 for j,a in enumerate(subset):
  x=(j%3)*500;y=(j//3)*500
  im=Image.open(a['path']).convert('RGB');im.thumbnail((480,455));sheet.paste(im,(x+(500-im.width)//2,y+30));dr.text((x+10,y+10),a['id'],fill='black')
 p=O/f'contact-{start//5+1}.png';sheet.save(p);contacts.append({'path':str(p),'sha256':sha(p),'items':[a['id'] for a in subset]})
save(B/'selected-original-contact-sheets.json',{'contacts':contacts})
print(json.dumps({'cif_scalars':len(scalars),'cif_loops':[(l['tags'][0],l['row_count'],len(l['tags'])) for l in loops],'original_parser':strict,'assets':len(assets),'contacts':len(contacts)},indent=2))
