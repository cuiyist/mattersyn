"""Cross-level identity, evidence provenance and publication-boundary checks."""
import json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    idx=read(DIST/'data/materials-index.json')['materials'];lib=read(DIST/'data/library-index.json');manifest=read(DIST/'data/dataset-manifest.json')
    ids={m['id'] for m in idx};assert len(ids)==len(idx)
    canonical={r['record_id'] for r in manifest['records']}
    for m in idx:
        v=read(DIST/'data/materials'/(m['id']+'.json'))
        assert set(v['record_ids'])<=canonical
        assert m['reviewed_records']==sum(r['record_type']!='procedure' and r['collection']=='reviewed_literature' for r in v['records'])
        for p in v['papers']:assert (DIST/'data/papers'/(p['id']+'.json')).exists()
    core='nakonechnyi-2017-zb-cdse-cds-seeded-growth'
    for f in ['CdSe','CdS']:
        m=next(m for m in idx if m['formula']==f)
        assert core in read(DIST/'data/materials'/(m['id']+'.json'))['record_ids']
    assert sum(r['record_id']==core for r in manifest['records'])==1
    for p in lib['papers']:
        if p['reviewStatus']=='indexed_awaiting_review':assert not p['reviewedRecordIds'] and not p['benchmarkRecordIds']
    audit=read(DIST/'data/paper-evidence/murray1993.json')
    assert len(audit['figures'])==15 and {f['figure'] for f in audit['figures']}==set(range(1,16))
    figures=audit['figures']+[audit['related_paper_saed_check']['nakonechnyi2017']['saed']]
    for f in figures:
        assert f['eligible_training'] is False
        a=f['original_figure_asset'];p=DIST/a['file'];assert p.exists()
        assert hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256']
    assert [p['product'] for p in figures[-1]['panels']]==['wz-CdSe/CdS','zb-CdSe/CdS','wz-CdSe/ZnSe','zb-CdSe/ZnSe']
    for p in (DIST/'data').rglob('*.json'):
        assert not re.search(r'C:[/\\]+Users',p.read_text(encoding='utf-8')),p
    assert lib['summary']['processedDocuments']==lib['summary']['sourceDocumentCount']==7373
    assert lib['summary']['pipelineComplete'] is True
    print(f'Passed atlas: {len(idx)} collections; {len(lib["papers"])} paper groups; 16 figure hashes; component identity; indexed/curated boundary; public JSON privacy.')
if __name__=='__main__':main()
