"""Apply the auditor's single-cell finding while preserving the author revision."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,shutil,subprocess,sys
B=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
names=['si-pages03-04-author-blocks.json','si-pages03-04-reflections.tsv',
       'si-pages03-04-transcription.json','si-pages03-04-author-checkpoint.json']
revision=B/'si-pages03-04-author-revision-1'
revision.mkdir(exist_ok=False)
before={n:sha(B/n) for n in names}
assert before['si-pages03-04-author-checkpoint.json']=='1e7e30f29fef10f3cddb2b292c120c6d3df913e660a4e9b3a36756ba814c5237'
for n in names:shutil.copy2(B/n,revision/n)
raw=B/names[0];d=json.loads(raw.read_text(encoding='utf-8'))
old='1 15 17 238818.06 255019.38 21244.19 o'
new='1 15 17 238818.06 255019.39 21244.19 o'
assert d['4L'][32]==old
d['4L'][32]=new
raw.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,'-X','utf8',str(B/'build_si_chunk.py'),'--chunk','pages03-04',
                '--author','/root','--replace-author-draft'],check=True)
before_d=json.loads((revision/names[2]).read_text(encoding='utf-8'))
after_d=json.loads((B/names[2]).read_text(encoding='utf-8'))
changes=[]
for br,ar in zip(before_d['rows'],after_d['rows']):
    for bc,ac in zip(br['cells'],ar['cells']):
        if bc['raw_text']!=ac['raw_text']:
            changes.append({'cell_id':bc['cell_id'],'before':bc['raw_text'],'after':ac['raw_text']})
assert changes==[{'cell_id':'si-p04-L-r033-Fobs2','before':'255019.38','after':'255019.39'}]
auditor=B/'si-pages03-04-auditor-visual-reading.json'
history={'schema':'mattersyn-si-numerical-correction-history/1','source_id':'heo2003','author':'/root',
    'auditor':'/root/backlog_eta','corrected_at':datetime.now(timezone.utc).isoformat(),
    'reason':'Distinct auditor read all 1,260 printed tokens and found the final digit in Fobs² at SI PDF p.4, printed p.44, left body row33, hkl(1,15,17). Root reopened the native left-bottom crop and confirmed .39.',
    'changes':changes,'prior_revision_directory':str(revision),'before_sha256':before,
    'after_sha256':{n:sha(B/n) for n in names},'auditor_reading_path':str(auditor),
    'auditor_reading_sha256':sha(auditor),'other_printed_tokens_unchanged':1259,
    'source_and_original_crops_unchanged':True,'previous_pages01_02_unchanged':True,
    'independent_audit':'pending_corrected_hash_recheck'}
(B/'si-pages03-04-correction-history.json').write_text(json.dumps(history,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'changes':changes,'new_checkpoint_sha256':sha(B/names[3]),'correction_history_sha256':sha(B/'si-pages03-04-correction-history.json')}))
