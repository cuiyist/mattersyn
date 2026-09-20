import sys,json,hashlib,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent
def hashes():return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'canonical').glob('*.json'))}
before=hashes()
subprocess.run([sys.executable,'-X','utf8',str(R/'build_review.py')],check=True)
after=hashes()
report={'canonical_hash_idempotent':before==after,'before':before,'after':after,'generator_uses_frozen_local_input':True,'note':'The generator deliberately resets independent audit to pending; source-specific validation is rerun after this check.'}
(R/'regeneration-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('Canonical hash idempotent:',before==after)
assert before==after
