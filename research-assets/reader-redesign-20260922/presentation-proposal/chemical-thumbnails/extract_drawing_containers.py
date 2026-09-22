from pathlib import Path
import json,hashlib,copy,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent
R=Path('[local path redacted]')
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((R/'registry.json').read_bytes());rows=[]
for sub in ['drawing-containers','svg','previews','contacts']:(P/sub).mkdir(exist_ok=True)
def tag(x):return x.tag.split('}')[-1]
def ischem(x):return any(k in x.get('class','') for k in ['atom-','bond-'])
def signature(x):return [tag(x),dict(x.attrib),x.text or '',[signature(c) for c in x]]
for e in reg['entries']:
 p=R/e['svgPath'];root=ET.fromstring(p.read_bytes());original_sha=sha(p)
 assert original_sha==e['assetHashes']['svgPath'],e['id']
 chemical=[x for x in root.iter() if ischem(x)]
 row={'id':e['id'],'name':e['name'],'depictionKind':e.get('depictionKind'),
  'original_svg':'assets/chemical-registry/'+e['svgPath'],'original_sha256':original_sha,
  'thumbnail_path':'assets/chemical-registry/'+e['svgPath'],'status':'original_retained',
  'reason':'No unambiguous path-based molecular container was selected.'}
 selected=None
 if chemical and e.get('model2dPath') and e.get('depictionKind') in ['molecule','ionic_components','ionic']:
  groups=[x for x in root if tag(x)=='g' and any(ischem(c) for c in x.iter())]
  if len(groups)==1:
   g=groups[0]
   backgrounds=[x for x in g if tag(x)=='rect' and 'width' in x.attrib and 'height' in x.attrib]
   width=float(root.get('viewBox','0 0 0 0').split()[2])
   # Partial ionic-component diagrams can place counterions, hydration counts or
   # multipliers outside the RDKit group. Keep the complete original plate unless
   # the group has an explicit near-full-width drawing canvas.
   complete_canvas=any(float(x.get('width',0))>=.75*width for x in backgrounds)
   if complete_canvas and all(x in list(g.iter()) for x in chemical) and not any(tag(x) in ['text','image','foreignObject','script'] for x in g.iter()):
    selected=[g];row['selection']='single_original_drawing_group'
   else:row['reason']='Partial or uncertain drawing container; original retains any outer counterions, multipliers, hydration and qualifications.'
  elif not groups and not any(tag(x) in ['text','image','foreignObject','script','g'] for x in root.iter()):
   # Flat RDKit canvases contain atom/bond paths and highlights, with no prose text.
   if all(ischem(x) or tag(x) in ['svg','title','desc','defs','style','rect','metadata'] for x in root.iter()):
    selected=list(root);row['selection']='standalone_original_rdkit_canvas'
 if selected is not None:
  projected=ET.Element(root.tag,dict(root.attrib))
  for x in selected:projected.append(copy.deepcopy(x))
  assert [signature(x) for x in projected]==[signature(x) for x in selected]
  assert [signature(x) for x in projected.iter() if ischem(x)]==[signature(x) for x in chemical]
  out=P/'drawing-containers'/f"{e['id']}.svg"
  ET.ElementTree(projected).write(out,encoding='utf-8',xml_declaration=True)
  row.update({'status':'candidate_compact','container_path':out.relative_to(P).as_posix(),
    'container_sha256':sha(out),'chemical_element_count':len(chemical),
    'chemical_signature_sha256':hashlib.sha256(json.dumps([signature(x) for x in chemical],sort_keys=True).encode()).hexdigest(),
    'all_chemical_nodes_preserved':True,'removed_content':'Outer prose/title/card decoration only; full original still used in detail viewer.'})
 rows.append(row)
out={'registry_sha256':sha(R/'registry.json'),'entries':rows,'status':'private_candidates'}
(P/'container-manifest.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n','utf8')
print('entries',len(rows),'selected',sum(x['status']=='candidate_compact' for x in rows))
