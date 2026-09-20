"""Bounded private reader/table/source mapping checks; no Site writes."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib,re
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ptr(v,p):
 for k in p.split('/')[1:]:v=v[int(k)] if isinstance(v,list) else v[k.replace('~1','/').replace('~0','~')]
 return v
def numbers(v):return re.findall(r'\d+(?:\.\d+)?',str(v))
def main():
 l=read(B/'veinot1997.json');a=read(B.parent/'source-audit.json');cov=read(B/'source-item-coverage.json');items={i['id']:i for s in l['reader_sections'] for i in s['items']};units={u['id']:u for u in a['units']};checks=[]
 def check(n,ok,detail=''):checks.append({'name':n,'passed':bool(ok),'detail':detail})
 records={x['id']:read(B.parent/'canonical-drafts'/f'{x["id"]}.json') for x in l['recipe_inventory']}
 check('Six full main pages and SI unverified',len(l['documents'])==1 and l['documents'][0]['page_count']==6 and all(p['text_read'] and p['visual_review'] for p in l['documents'][0]['pages']) and l['review_scope']=='supplied_main_only_si_unverified' and l['supporting_information']['status']=='not_located_or_verified')
 check('No private status promotion',not l['source_review_promoted'] and not l['training_eligible'] and l['publication_status']=='private_proposal_not_published')
 check('21records with actual types',len(records)==21 and Counter(r['record_type'] for r in records.values())==Counter(literature_protocol=6,procedure=11,protocol_variant=1,observation=3))
 for row in l['recipe_inventory']:check(row['id']+' actual type',row['record_type']==records[row['id']]['record_type'])
 for key,i in items.items():
  check(key+' sourced, scoped, not automatic training',bool(i['evidence']) and bool(i['claim_type']) and bool(i['sample_scope']['link_limit']) and not i['training_eligible'] and all(e['source_id']=='veinot1997' and 1<=e['pdf_page']<=6 for e in i['evidence']))
  check(key+' canonical record links',all(c['record_id'] in records for c in i['canonical_links']))
  for s in i['sample_scope'].get('canonical_sample_links',[]):check(key+'/'+s['sample_id']+' compound pointer',ptr(records[s['record_id']],s['json_pointer'])['sample_id']==s['sample_id'] and 'compound-class' in s['relation'])
 check('All141source units explicitly mapped',len(cov['source_audit_unit_map'])==141 and {m['source_audit_id'] for m in cov['source_audit_unit_map']}==set(units))
 for m in cov['source_audit_unit_map']:check(m['source_audit_id']+' complete target resolution',ptr(a,m['source_audit_pointer'])['id']==m['source_audit_id'] and all(bool(ptr(l,p)) for p in m['public_targets']))
 check('101reader items and112totalreaderasset units',len(items)==101 and len(cov['reader_units'])==112)
 for m in cov['reader_units']:check(m['source_item_id']+' reader pointer',ptr(l,m['target'])['id']==m['source_item_id'])
 tables={t['id']:t for t in l['tables']}
 check('All23 table rows retained',[len(tables[t]['structured_rows']) for t in ['table-1','table-2','table-3']]==[11,6,6])
 for row in tables['table-1']['structured_rows']:
  c=row['compound'];u=units['table1-'+c]
  check('Table1/'+c+' complete NMR numeric signals',numbers(row['nmr'])==numbers(u['nmr']['signals']),repr([numbers(row['nmr']),numbers(u['nmr']['signals'])]))
  check('Table1/'+c+' percentage and role',row['yield_or_conversion_percent']==u['yield_or_conversion_percent'] and (c=='1' or ('conversion' in row['quantity_role'].lower())==(c.startswith('2'))))
  actual_min=row['reaction_time_h']*60 if row.get('reaction_time_h') is not None else row['reaction_time_min']
  expected_min=u['reaction_time']['value']*(60 if u['reaction_time']['unit']=='h' else 1)
  check('Table1/'+c+' time value and dimension',actual_min==expected_min)
 for row in tables['table-2']['structured_rows']:
  c=row['compound'];u=units['table2-'+c]
  check('Table2/'+c+' all numeric band positions retained',numbers(row['bands_and_assignments'])==numbers(u['signals']),repr([numbers(row['bands_and_assignments']),numbers(u['signals'])]))
 for row in tables['table-3']['structured_rows']:
  c=row['compound'];u=units['table3-'+c]
  check('Table3/'+c+' source numerical fields',numbers(row['absorption_nm'])==numbers(u['wavelength_nm']) and row['tight_binding_diameter_A']==u['author_calculated_diameter_angstrom'] and row['TEM_diameter_A']==u['TEM_diameter_angstrom'])
  if c=='2c':check('Pyrene feature is not CdS optical size',row['tight_binding_diameter_A'] is None and 'Pyrene' in row['feature'])
 assets=[*l['figures'],*l['tables'],*l['schemes']]
 check('Eleven originals with one numbered scheme and one compound illustration',[len(l[k]) for k in ['figures','tables','schemes','equations']]==[6,3,2,0] and Counter(x['source_asset_type'] for x in l['schemes'])==Counter(scheme=1,compound_illustration=1))
 for x in assets:check(x['id']+' exact original crop bytes',sha(B.parent/'crop-assets'/Path(x['public_asset']).name)==x['public_asset_sha256'] and bool(x['sample_scope']) and bool(x['quantitative_context']) and not x['training_eligible'])
 orig=items['compound-identities']['original_assets'][0]
 check('Original compound illustration linked from source item',sha(B.parent/'crop-assets'/Path(orig['public_asset']).name)==orig['sha256'])
 check('All15reference contexts,2directnotes',len(l['referenced_methods'])==15 and [r['reference_number'] for r in l['referenced_methods'] if r['direct_source_note_reviewed']]==[10,15] and all(not r['import_experimental_evidence'] and not r['cited_work_independently_reviewed_in_this_task'] for r in l['referenced_methods']))
 check('No invented equation','no corresponding numbered equation' in next(x for x in l['evidence_conflicts'] if x['id']=='conflict-12')['text'].lower() and not l['equations'])
 check('Only2a quantified esterification','Only the acetyl example' in items['esterification-stocks']['text'] and '300 mg' in items['esterification-stocks']['text'] and '170 mg' in items['esterification-stocks']['text'])
 check('QDOH volume does not become total volume','150 mL is not the total batch' in items['qdoh-feeds']['text'])
 check('QDOH missing synthesis temperature explicit','reaction temperature' in items['qdoh-mixing']['text'] and 'not given' in items['qdoh-mixing']['text'])
 check('Thiol fraction conflict20vs34 present',all(v in items['cap-gravimetry']['text'] for v in ['20 mol%','34 mol%']))
 check('Preparation absorption295305vs390 retained',all(v in items['qdoh-absorption-conflict']['text'] for v in ['295 nm','305 nm','390 nm']))
 check('Methods IR3302and1734 not lost',all(v in items['qdoh-ir']['text'] for v in ['3302','3301','1734','1730','2580']))
 check('3b time conflict retained',all(v in items['anhydride-acylimidazoles']['text'] for v in ['15 min','30 min']))
 check('TEM7 is uncertainty and15isreference','superscript 15 after 7 is a reference' in items['tem-diameter-series']['text'])
 check('Aggregate dimensions not silently corrected',all(v in items['aggregation']['text'] for v in ['1100 Å','6 nm','without measuring or silently correcting']))
 check('PriorIRbands not merged intoQDOH',all(v in items['prior-ir-comparison']['text'] for v in ['686','734','1730','1950','must not be added']))
 check('No stale pending canonical link strings',all('pending' not in c['relation'] for i in items.values() for c in i['canonical_links']))
 failures=[c for c in checks if not c['passed']]
 result={'status':'passed_private_proposal_checks' if not failures else 'findings','checked_utc':datetime.now(timezone.utc).isoformat(),'checks_passed':len(checks)-len(failures),'check_count':len(checks),'failures':failures,'scope':'Private reader links, full independent source-unit map, compound pointers, table numerical signals and original bytes. Canonical scientific audit, actual-reader rendering and publication remain separate.','proposal_sha256':sha(B/'veinot1997.json'),'coverage_sha256':sha(B/'source-item-coverage.json'),'checks':checks}
 (B/'proposal-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:result[k] for k in ['status','checks_passed','check_count','failures','proposal_sha256']},ensure_ascii=False))
 return bool(failures)
if __name__=='__main__':raise SystemExit(main())
