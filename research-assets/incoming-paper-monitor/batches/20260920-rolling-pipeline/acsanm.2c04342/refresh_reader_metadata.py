"""Refresh only affected generated metadata after separately evidenced status deltas."""
from pathlib import Path
import subprocess,sys,shutil
N=Path(__file__).resolve().parent;M=N.parents[4];S=M/'recipe-atlas'
for p in [S/'scripts/build_paper_reviews.py',N/'build_matuhina_inventory.py']:
 subprocess.run([sys.executable,str(p)],cwd=S,check=True)
shutil.copy2(N/'site-integration-proposal/inventory-summary.json',S/'data/inventory-summary.json')
for p in [S/'scripts/build_inventory.py',S/'scripts/check_site.py',M/'research-assets/build_reference_readmes.py']:
 subprocess.run([sys.executable,str(p)],cwd=S,check=True)

