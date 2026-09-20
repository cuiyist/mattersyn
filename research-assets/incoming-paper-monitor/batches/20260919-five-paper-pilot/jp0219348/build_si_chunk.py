"""Package a manually transcribed SI chunk without replacing earlier audit evidence.

No OCR or numerical inference is performed here. A different person/agent must
visually compare every printed cell before independent approval is recorded.
"""
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
import argparse, csv, hashlib, json

B = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p, obj): Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chunk', required=True, help='For example pages03-04')
    ap.add_argument('--author', required=True)
    ap.add_argument('--replace-author-draft', action='store_true')
    args = ap.parse_args()
    stem = 'si-'+args.chunk
    out = [B/(stem+s) for s in ['-reflections.tsv', '-transcription.json', '-author-checkpoint.json']]
    if any(p.exists() for p in out) and not args.replace_author_draft:
        raise SystemExit('Existing outputs are frozen by default; deliberate author correction requires --replace-author-draft and a separate correction log.')
    old_output_hashes = {str(p): sha(p) for p in out if p.exists()}
    preserved_names = [
        'source-inventory.json','source-facts.json','page-coverage.json','source-scientific-audit.json',
        'main-tables.json','main-table-assets.json','source-review-checkpoint.json',
        'si-reflections-pages01-02.tsv','si-reflections-transcription.json',
        'si-numerical-verification-checkpoint.json','si-pages-1-2-independent-audit.json',
        'si-pages-1-2-independent-audit.md','si-numerical-correction-history.json']
    preserved = {str(B/n): sha(B/n) for n in preserved_names}
    doc = read(B/'source-inventory.json')['source_documents']['si']
    assets = read(B/(stem+'-assets.json'))
    raw_blocks = read(B/(stem+'-author-blocks.json'))
    asset_map = {a['id']: a for a in assets['assets']}
    assert sha(doc['path']) == doc['sha256'] == assets['source_sha256']
    assert all(sha(a['path']) == a['sha256'] for a in assets['assets'])
    columns = ['h','k','l','Fcal2','Fobs2','sigma_Fobs2','marker']
    labels = {'h':'h','k':'k','l':'l','Fcal2':'Fcal^2','Fobs2':'Fobs^2',
              'sigma_Fobs2':'σ(Fobs^2)','marker':'unheaded trailing open-circle/o-like marker'}
    checks = []
    def check(name, ok):
        checks.append({'check':name,'passed':bool(ok)})
        assert ok, name
    keys = sorted(raw_blocks, key=lambda s: (int(s[:-1]),s[-1]))
    pages = sorted({int(k[:-1]) for k in keys})
    check('Two complete column blocks per chunk page',keys == [str(p)+b for p in pages for b in ['L','R']])
    check('This author-verified chunk covers pages 3 and 4 only',pages == [3,4])
    data=[]; tsv=[]; negatives=[]; cell_ids=[]
    for key in keys:
        page=int(key[:-1]); block=key[-1]
        check(key+' has 45 visually counted rows',len(raw_blocks[key])==45)
        for rn, line in enumerate(raw_blocks[key],1):
            tokens=line.split()
            check(f'{key} row {rn}: seven printed tokens',len(tokens)==7)
            raw=dict(zip(columns,tokens)); rid=f'si-p{page:02d}-{block}-r{rn:03d}'
            crop=f'si-{page:02d}-'+('left' if block=='L' else 'right')+('-top' if rn<=23 else '-bottom')
            check(rid+' has source crop',crop in asset_map)
            hkl=[int(raw[c]) for c in ['h','k','l']]
            cells=[]
            for c in columns:
                cid=rid+'-'+c; cell_ids.append(cid)
                n=None
                if c!='marker':
                    dec=Decimal(raw[c]); check(cid+' finite',dec.is_finite())
                    n=int(raw[c]) if c in ['h','k','l'] else float(dec)
                    check(cid+' decimal round trip',Decimal(str(n))==dec)
                else:
                    check(cid+' uninterpreted marker retained',raw[c]=='o')
                evidence={'source_id':'heo2003-si','source_path':doc['path'],'source_sha256':doc['sha256'],
                    'supporting_table':1,'pdf_page':page,'printed_page':40+page,'column_block':block,
                    'row_in_block':rn,'column_key':c,'printed_column_label':labels[c],
                    'locator':f'SI PDF p. {page} (printed p. {40+page}), Supporting Table 1, '+
                        ('left' if block=='L' else 'right')+f' block, body row {rn}, {labels[c]}',
                    'original_crop_id':crop,'original_crop_path':asset_map[crop]['path'],
                    'original_crop_sha256':asset_map[crop]['sha256']}
                cells.append({'cell_id':cid,'raw_text':raw[c],'numeric_value':n,'unit':None,
                    'unit_status':'not_applicable_index' if c in ['h','k','l'] else 'not_applicable_marker' if c=='marker' else 'unreported',
                    'transcription_status':'manually_transcribed_from_original_scan',
                    'source_comparison_status':'visually_compared_by_transcription_author',
                    'independent_numerical_audit':'pending','evidence':evidence})
                if c=='Fobs2' and n<0:
                    negatives.append({'cell_id':cid,'raw_text':raw[c],'numeric_value':n})
            data.append({'row_id':rid,'source_sample_label':'In66-X, as Supporting Table 1 title',
                         'hkl':hkl,'raw_cells':raw,'cells':cells})
            tsv.append({'page':page,'block':block,'row':rn,**raw})
    check('180 distinct rows / 1260 distinct printed cells',len(data)==180 and len(set(cell_ids))==1260)
    check('All eight negative observations retained',[(n['cell_id'],n['raw_text']) for n in negatives]==[
        ('si-p03-L-r029-Fobs2','-1552.61'),('si-p03-R-r005-Fobs2','-1164.21'),
        ('si-p03-R-r020-Fobs2','-822.08'),('si-p03-R-r030-Fobs2','-6004.99'),
        ('si-p03-R-r045-Fobs2','-7683.63'),('si-p04-L-r001-Fobs2','-9313.55'),
        ('si-p04-L-r008-Fobs2','-1927.47'),('si-p04-R-r038-Fobs2','-5900.29')])
    previous=read(B/'si-reflections-transcription.json')
    prior_indices={tuple(r['hkl']) for r in previous['rows']}
    current_indices={tuple(r['hkl']) for r in data}
    check('180 unique new printed hkl, no overlap with prior 170; no merging applied',
          len(current_indices)==180 and not current_indices.intersection(prior_indices))
    check('Prior source and audit artifacts remain byte-identical',all(sha(p)==h for p,h in preserved.items()))
    with out[0].open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['page','block','row']+columns,delimiter='\t',lineterminator='\n')
        writer.writeheader();writer.writerows(tsv)
    now=datetime.now(timezone.utc).isoformat()
    policy={'numeric_precision':'Raw decimal strings are authoritative; no rescaling, unit inference, truncation, symmetry expansion or merging.',
            'marker':'ASCII o represents the scanned open-circle/lowercase-o-like glyph. Meaning and exact Unicode identity unverified; not numeric zero or acceptance status.',
            'scientific_scope':'Reflection hkl and squared structure factors with esds, not atomic coordinates, CIF or a DFT-ready ordered crystal.',
            'source_identity_caveat':'SI prints ©2002 ACS, J. Phys. Chem. A, Heo jp0219348. Preserve audited content/DOI pairing and source header discrepancy.'}
    write(out[1],{'schema':'mattersyn-si-reflection-transcription-chunk/1','source_id':'heo2003',
        'title_as_printed':'Observed and Calculated Structure Factors Squared with Esds for In66-X',
        'author':args.author,'created_at':now,'pages':pages,'source_path':doc['path'],'source_sha256':doc['sha256'],
        'status':'author_transcribed_source_compared_independent_numerical_audit_pending',
        'field_order':columns,'original_header_labels':labels,'rows':data,'negative_observations':negatives,
        'policies':policy,'unresolved_numeric_tokens_in_chunk':[],'complete_document_transcription':False,
        'independent_audit_passed':False,'training_eligible':False,'published':False})
    files=[B/(stem+'-author-blocks.json'),B/(stem+'-assets.json'),B/'prepare_si_pages03_04.py',Path(__file__),out[0],out[1]]
    write(out[2],{'schema':'mattersyn-si-numerical-chunk-author-checkpoint/1','source_id':'heo2003','author':args.author,
        'created_at':now,'status':'author_source_comparison_complete_independent_numerical_audit_pending',
        'actual_scope':{'pages_transcribed':pages,'native_crop_pages_visually_read':pages,
                       'rows':180,'numeric_cells':1080,'marker_cells':180,'total_cells':1260,'negative_Fobs2':8,
                       'rows_per_page_block':{k:len(raw_blocks[k]) for k in keys}},
        'manual_source_comparison':'The author read all 180 printed rows and seven fields per row in native original scan crops. This is an author source comparison, not independent audit.',
        'prior_chunk':{'pages':[1,2],'independent_audit_path':str(B/'si-pages-1-2-independent-audit.json'),
                       'independent_audit_sha256':sha(B/'si-pages-1-2-independent-audit.json'),'rows':170},
        'complete_document_transcription':False,'remaining_untranscribed_pages':list(range(5,15)),
        'remaining_row_count':None,'remaining_count_note':'Every printed body cell on pages 5–14 still requires numerical transcription and independent audit; null is unknown, not zero.',
        'policies':policy,'programmatic_check_count':len(checks),'programmatic_checks':checks,
        'preserved_prior_files':preserved,'replaced_author_output_hashes':old_output_hashes,
        'source_pdf_sha256':doc['sha256'],'bound_files':{str(p):sha(p) for p in files},
        'bound_original_evidence':{a['path']:a['sha256'] for a in assets['assets']},
        'independent_audit_passed':False,'training_eligible':False,'published':False})
    print(json.dumps({'chunk':args.chunk,'rows':180,'numeric_cells':1080,'markers':180,'negative_values':8,
        'author_checks':len(checks),'checkpoint_sha256':sha(out[2]),'independent_audit':'pending','remaining_pages':list(range(5,15))}))

if __name__=='__main__': main()
