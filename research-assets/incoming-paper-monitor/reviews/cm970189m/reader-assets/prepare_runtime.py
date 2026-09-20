"""Prepare the scoped DOM harness from the verified predecessor; private only."""
from pathlib import Path
B=Path(__file__).resolve().parent
old=B.parent.parent/'jp971091y/reader-assets/check_reader_runtime.mjs'
s=old.read_text(encoding='utf-8').replace('dabbousi1997','veinot1997')
s=s.replace("check('16 original figure cards',figCards.length===16);","check('6 original figure cards',figCards.length===6);")
s=s.replace("check('25 unique original assets accessible',filenames.length===25);","check('11 unique original assets accessible',filenames.length===11);")
s=s.replace("check('Table1 measured major axis and percentage spread render',allText.includes('tem major axis A: 39')&&allText.includes('tem relative spread percent: 8.2'));","check('Table3 model and TEM columns render separately',allText.includes('tight binding diameter A: 24')&&allText.includes('TEM diameter A: 30.4'));")
s=s.replace("check('Original source note22 reader link visible',cardMap.get('size-temperature-pairs').textContent.includes('Original source note 22')&&filenames.includes('source-note-22.png'));","check('Original compound illustration reader link visible',cardMap.get('compound-identities').textContent.includes('Original compound-family illustration')&&filenames.includes('compound-family-illustration.png'));")
(B/'check_reader_runtime.mjs').write_text(s,encoding='utf-8')
print('Prepared check_reader_runtime.mjs; execution awaits integrated Site.')
