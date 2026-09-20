from pathlib import Path
import json,re,ast,tokenize,io,hashlib
B=Path(__file__).resolve().parent
p=B/'build_records.py';src=p.read_text(encoding='utf8')
replacements=json.loads((B/'prose-replacements.json').read_text(encoding='utf-8-sig'))['replacements']
# Longer explicit phrases win; replacements are applied once to each original literal.
mapping={r['old']:r['new'] for r in replacements}
pattern=re.compile('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)))
lines=src.splitlines(keepends=True);offsets=[0]
for l in lines:offsets.append(offsets[-1]+len(l))
edits=[]
for tok in tokenize.generate_tokens(io.StringIO(src).readline):
 if tok.type!=tokenize.STRING:continue
 updated=pattern.sub(lambda m:mapping[m.group()],tok.string)
 if updated!=tok.string:
  edits.append((offsets[tok.start[0]-1]+tok.start[1],offsets[tok.end[0]-1]+tok.end[1],updated,tok.string))
for start,end,new,old in reversed(edits):src=src[:start]+new+src[end:]
ast.parse(src)
before={f.name:json.loads(f.read_text(encoding='utf8')) for f in (B/'canonical-drafts').glob('*.json')}
(B/'canonical-before-prose-cleanup.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf8')
p.write_text(src,encoding='utf8')
(B/'prose-cleanup-log.json').write_text(json.dumps({'changed_python_string_literals':len(edits),'changes':[{'before':old,'after':new} for _,_,new,old in edits],'script_sha256':hashlib.sha256(p.read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf8')
print(len(edits),'human-readable literals updated; validate canonical before/after separately')
