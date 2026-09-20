"""Derive versioned private proposal builders without overwriting v1."""
from pathlib import Path
import hashlib,json
B=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
v2=B/'source-extraction-revision-2'
assert sha(v2/'source-extraction-freeze.json')=='e152d9356ba06facf5330a0220f3ad232b23076741a7c30876aa5a953d046ce1'
for kind in ['canonical','reader']:
 src=B/('build_'+kind+'_proposal_v1.py');dst=B/('build_'+kind+'_proposal_v2.py');s=src.read_text(encoding='utf-8')
 s=s.replace("canonical-proposal/v1","canonical-proposal/v2").replace("public-review-proposal/v1","public-review-proposal/v2")
 s=s.replace("B/'source-facts.json'","B/'source-extraction-revision-2/source-facts.json'")
 s=s.replace("B/'source-extraction-freeze.json'","B/'source-extraction-revision-2/source-extraction-freeze.json'")
 s=s.replace('7349d66b2580a48988729aabc6a3f867729ec7ae2198e91674bc0f2ca6719c5e','e152d9356ba06facf5330a0220f3ad232b23076741a7c30876aa5a953d046ce1')
 s=s.replace("'version':1","'version':2")
 dst.write_text(s,encoding='utf-8')
print('Prepared private v2 builders; v1 files unchanged.')
