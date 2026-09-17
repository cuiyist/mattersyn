"""Import only the public bibliographic manifest, never private extraction text."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    source=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT.parent/'research-assets/corpus-20260917/public-bibliographic-manifest.json'
    corpus=json.loads(source.read_text(encoding='utf-8'))
    assert corpus['summary']['pipelineComplete'], 'Wait for a completed extraction snapshot'
    docs={d['id']:d for d in corpus.get('documents',[])}
    for p in corpus['papers']:
        p['coverage']['documentRoleMismatchCount']=sum(bool(docs.get(d,{}).get('roleMismatchFlag')) for d in p['documentIds'])
    target=ROOT/'data/corpus/library-source.json';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps({'summary':corpus['summary'],'papers':corpus['papers']},ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(f'Imported public bibliographic metadata for {len(corpus["papers"])} DOI candidates.')
if __name__=='__main__':main()
