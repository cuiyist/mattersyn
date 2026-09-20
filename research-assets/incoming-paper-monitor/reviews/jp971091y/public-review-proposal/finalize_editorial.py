"""Scoped private prose cleanup; no identifiers, locators, values or source quotes."""
import re

TEXT_KEYS={'title','label','text','scope','state','link_limit','relation','notes','facts','basis','caption_paraphrase','sample_scope','quantitative_context','sample_linkage','data_role','remaining_gaps','training_note','record_formulation_scope_note'}
WORDS=('Dissolve Heat Add Cool For Approximately Rhodamine Murray Figure Figures Fig Table Note note reference Reference Equation equation contains then add over through approximately near below above between within around across under into about at of is are from to with in uses gives has bare coated parameter ratios ratio only beyond all All sample time after by than before and or CdS ZnS WDS SAXS WAXS TEM XPS photon energy radius diameter coverage concentration excitation thickness peak peaks film solution temperature temperature-dependent normalized initial nominal core sizes size').split()

def prose(s):
    # Only known prose tokens; chemical formulas, orbital labels, instrument
    # model identifiers, numbers and punctuation remain intact.
    s=re.sub(r'([,;:])(?=[A-Za-z0-9])',r'\1 ',s)
    s=re.sub(r'\b('+ '|'.join(sorted(map(re.escape,WORDS),key=len,reverse=True))+r')(?=\d)',r'\1 ',s)
    s=re.sub(r'(?<=\d)(?=(?:°C|Å|ML|mL|min|nm|mm|µm|µmol|mol|keV|eV|meV|kV|mA|mg|wt|h|s)\b)',' ',s)
    s=re.sub(r'\b(and)(?=\d)',r'\1 ',s)
    s=re.sub(r'(?<=[a-z])(?=\()', ' ',s)
    return s

def finalize(ledger,audit):
    assert audit['status'].startswith('passed') and audit['open_must_fix_count']==0
    changes=[]
    def walk(v,p='',enabled=False):
        if isinstance(v,dict):
            return {k:walk(x,p+'/'+k,k in TEXT_KEYS) for k,x in v.items()}
        if isinstance(v,list):return [walk(x,p+'/'+str(i),enabled) for i,x in enumerate(v)]
        if isinstance(v,str) and enabled:
            out=prose(v)
            if out!=v:
                assert re.sub(r'\s','',out)==re.sub(r'\s','',v)
                changes.append({'pointer':p,'before':v,'after':out,'change':'whitespace_only'})
            return out
        return v
    ledger=walk(ledger)
    for sec in ledger['reader_sections']:
        for item in sec['items']:
            for link in item['canonical_links']:
                if link['relation']=='Proposed source-context link pending independent canonical audit.':
                    link['relation']='Independently audited source-context link; the stated cohort and specimen limitations still apply.'
    for item in ledger['recipe_inventory']:
        item['status']='independent_canonical_audit_complete_main_only'
        item['gaps']=[g for g in item['gaps'] if g!='Canonical sample/operation/measurement joins pending independent audit.']
    ledger['coverage_status']='All 13 supplied main pages read and visually inspected; independent source and canonical audits complete. Reader acceptance and publication remain separate.'
    ledger['independent_audit']='Independent supplied-main scientific reading, visual review and canonical operation/sample/measurement audit complete; no matched SI reviewed. Final reader acceptance and publication remain separate.'
    ledger['remaining_gaps']=[g.replace('Independent canonical joins,reader visual review and publication remain pending.','Final reader visual review and publication remain pending.').replace('Independent canonical joins, reader visual review and publication remain pending.','Final reader visual review and publication remain pending.') for g in ledger['remaining_gaps']]
    return ledger,changes
