from pathlib import Path
import json,hashlib,datetime
A=Path(__file__).parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
text='''M1|1.5|280|1:2:6.25|124.5|30
M2|1.7|280|1:2:7.09|124.5|30
M3|2.0|280|1:2:8.34|124.5|30
M4|1.7|250|1:2:7.09|39.5|30
M5|1.7|250|1:2:7.09|99.5|90
M6|1.7|250|1:2:7.09|189.5|180
M7|1.7|280|1:2:7.09|94.5|0
M8|1.7|260|1:2:7.09|124.5|50
M9|1.7|270|1:2:7.09|124.5|40
S1|0.18|450|1:2:7|~1|0
S2|0.18|380|1:2:7|~1|0
A1|1.5|220|1:2:6.25|17 days|17 days
A2|1.7|220|1:2:7.09|17 days|17 days
A3|2.0|220|1:2:8.34|17 days|17 days
A4|1.5|220|1:2:6.25|1 day|1 day
A5|1.7|220|1:2:7.09|1 day|1 day
A6|2.0|220|1:2:8.34|1 day|1 day
I1|6.0|350|1:2:6.25|0–40|0–40
I2|6.0|400|1:2:6.25|0–40|0–40
I3|6.0|430|1:2:6.25|0–40|0–40
I4|7.0|350|1:2:7.30|0–40|0–40
I5|7.0|400|1:2:7.30|0–40|0–40
I6|7.0|430|1:2:7.30|0–40|0–40
I7|7.5|350|1:2:7.81|0–40|0–40
I8|7.5|400|1:2:7.81|0–40|0–40
I9|8.0|350|1:2:8.34|0–40|0–40
I10|8.0|400|1:2:8.34|0–40|0–40
I11|8.0|430|1:2:8.34|0–40|0–40
I12|0|450|1:2:0|0–40|0–40
I13|0|475|1:2:0|0–40|0–40
I14|0|400|1:2:0|0–40|0–40
I15|0|425|1:2:0|0–40|0–40
I16|0|400|1:2:0|0–40|0–40
D1|0|RT|1:2:0|3.3|3.3
D2|8.0|RT|1:2:8|3.3|3.3
D3|0|RT|1:0:0|3.3|3.3
D4|0|RT|0:2:0|3.3|3.3'''
rows=[s.split('|') for s in text.splitlines()]
assert len(rows)==37 and all(len(r)==6 for r in rows)
out={'reviewer':'/root/norberg2004_extract','basis':'Independent manual comparison of all printed Table1 cells on original main PDF p4, before reading author facts; raw spelling uses ASCII tilde for printed approximation only.','headers':['sample','C(NaOH) (M)','Trxn (degC)','Zn:Al:OH','trxn (min except explicit day text)','tdwell (min except explicit day text)'],'rows':rows,'row_count':37,'cell_count':222,'source_sha256':'ca731728f443477c041c370f3e6de6df63d8659cf61bfc47c07582750ce59b97'}
(A/'independent-table1.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
inputs=json.loads((A/'reading-inputs.json').read_text())
for p in inputs['pages']:p['read_status']='text_read_and_original_page_visually_inspected'
inputs.update({'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'source_reading_complete_author_comparison_pending','main_pages_read':11,'si_pages_read':0,'supporting_information':'declared_but_unlocated_unverified','local_filename_search':{'roots':['[local path redacted]','[local path redacted]'],'patterns':['*9b01519*','*Atomic*Scale*Design*','*Sommer*'],'matches':[c['path'] for c in inputs['original_copies']]},'manual_counts':{'main_figures':13,'main_tables':1,'main_table_rows':37,'main_table_cells':222,'numbered_references':65},'bound_files':[{'path':str(p),'sha256':sha(p)} for p in [A/'reading-inputs.json',A/'independent-reading-notes.md',A/'independent-table1.json',A/'prepare_reading.py',Path(__file__)]]})
(A/'independent-reading-checkpoint.json').write_text(json.dumps(inputs,indent=2),encoding='utf-8')
print(sha(A/'independent-reading-checkpoint.json'))
