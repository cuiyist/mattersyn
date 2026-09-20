from pathlib import Path
S=Path(__file__).resolve().parents[4]/'recipe-atlas'
for folder,patterns in [(S/'dist',['*.html','*.mjs']),(S/'scripts',['*.py'])]:
    for pattern in patterns:
        for p in folder.rglob(pattern):
            text=p.read_text(encoding='utf-8')
            revised=text.replace('?v=0.4.0-r1','?v=0.5.0-r1')
            if revised!=text:p.write_text(revised,encoding='utf-8')
p=S/'dist/illustrated-guide.css'
text=p.read_text(encoding='utf-8')
if '.measurement-conditions{' not in text:text+='\n.source-record-provenance small{display:block}.measurement-conditions{font-size:.9rem;color:#465f70}.measurement-source{margin:.3rem 0 1rem}\n'
p.write_text(text,encoding='utf-8')
print('Updated versioned reader imports and measurement detail styles.')
