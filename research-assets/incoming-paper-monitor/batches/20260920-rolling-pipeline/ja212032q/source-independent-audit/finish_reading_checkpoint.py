from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
A=Path(__file__).resolve().parent
G=A.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

copies=[]
for item in read(G/'complete-source-payloads.json')['source_copies']:
 actual=sha(item['source_path']);assert actual==item['sha256']
 copies.append({'path':item['source_path'],'sha256':actual,'role':item['role_candidate'],'collection':item['source_collection']})
detail=read(A/'si05-caption-native-300dpi.json')
resolution={
 'reviewer':'/root/norberg2004_extract',
 'status':'reading_checkpoint_not_extraction_approval',
 'created_at':datetime.now(timezone.utc).isoformat(),
 'original_copies_reverified':copies,
 'source_pages_read_and_viewed':19,
 'author_extraction_files_opened':False,
 'source_caption_detail':{
  'metadata_path':str(A/'si05-caption-native-300dpi.json'),
  'metadata_sha256':sha(A/'si05-caption-native-300dpi.json'),
  'render_path':detail['path'],'render_sha256':sha(detail['path']),
  'actually_viewed':True,
  'resolution':'Original 300 dpi pixels clearly read di-octyl amine. An apparent spelling issue in the downscaled full-page display was rejected. The genuine next-sentence oleylamine/NH2 assignment conflict remains.'
 },
 'bound_files':{str(A/p):sha(A/p) for p in ['independent-reading-checkpoint.json','independent-table-reading.json','prepare_reading_checkpoint.py']},
 'next_action':'Compare the author frozen complete extraction, facts, quantities, tables, figure/sample bindings and all selected crops; preserve and recheck any correction before issuing separate scientific audit.',
 'independent_scientific_audit_status':'pending_author_freeze',
 'canonical_approval':False,'publication_approval':False
}
write(A/'reading-checkpoint-final.json',resolution)
(A/'reading-checkpoint.md').write_text('''# Ghosh 2012 independent reading checkpoint

The reviewer independently read the text and visually inspected all 10 main-paper pages and nine SI pages. All four retained source copies match the generation-2 intake hashes. The main/SI title, authors, content and cited figures support their pairing.

The private independent table reading preserves all 180 Table S1 cells plus Tables 1–3 and the Fig. S2 characteristic-stretch inset. It precedes any comparison with the author's extraction. Source figures are not claimed to be raw curve data.

The main issues to preserve are the distinct core-growth branches; optimized versus comparison anneal times; reaction-volume aliquot removal versus precursor excess; moderate-shell Table 3 TEM versus thick-shell QY; FTIR ligand assignment in Fig. S6; and the separate 16.9-ML Fig. S7/S8 and 15.57-ML Table S1 contexts. The 7-nm core-only controls do not include a complete recipe. Author mechanistic hypotheses and semi-quantitative phase estimates remain separate from measured atomic coordinates.

A 300-dpi original Fig. S6 caption detail resolves an apparent downscaled spelling issue as “di-octyl amine.” It does not resolve the actual caption's subsequent oleylamine/NH2 assignment conflict.

This checkpoint is source reading and independent pairing evidence only. The author's extraction and crop package are not yet frozen, so source-to-extraction comparison and scientific approval remain pending. No canonical, visual, browser, training or publication approval is issued.
''',encoding='utf-8')
print(json.dumps({'checkpoint':str(A/'reading-checkpoint-final.json'),'sha256':sha(A/'reading-checkpoint-final.json'),'source_copies':len(copies)}))
