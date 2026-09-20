"""Create a new bounded builder, preserving the prior frozen builder exactly."""
from pathlib import Path
B=Path(__file__).resolve().parent
src=(B/'build_si_pages05_06.py').read_text(encoding='utf8')
target=B/'build_si_pages07_08.py'
assert not target.exists()
src=src.replace('pages5–6','pages7–8').replace('pages05-06','pages07-08').replace('pages05_06','pages07_08')
src=src.replace("['5L','5R','6L','6R']","['7L','7R','8L','8R']").replace('[5,6]','[7,8]')
a=src.index('expected_negative=');b=src.index('\nexpected=',a)
src=src[:a]+"expected_negative={'7L':{4:'-3376.68',10:'-1513.71',14:'-402.11',18:'-6421',21:'-1237.99',44:'-3012.84'},'7R':{9:'-3525.26',20:'-5571.09',24:'-9055.25'},'8L':{13:'-2669.78',18:'-3160.58',27:'-7783.89',31:'-3825.71',42:'-4171.98',43:'-6588.8'},'8R':{6:'-6416.11',8:'-5941.85',14:'-9989.62',16:'-4540.39',33:'-6744.26',42:'-6997.27'}}"+src[b:]
src=src.replace('All20negative','All21negative').replace("'negative_Fobs2':20","'negative_Fobs2':21")
src=src.replace("previous=read(B/'si-reflections-transcription.json')['rows']+read(B/'si-pages03-04-transcription.json')['rows']", "previous=read(B/'si-reflections-transcription.json')['rows']+read(B/'si-pages03-04-transcription.json')['rows']+read(B/'si-pages05-06-transcription.json')['rows']")
src=src.replace('no prior350overlap','no prior530overlap')
src=src.replace("'remaining_untranscribed_pages':list(range(7,15))", "'remaining_untranscribed_pages':list(range(9,15))")
src=src.replace("preserved={str(B/n):sha(B/n) for n in names}", "names += ['si-pages05-06-author-blocks.json','si-pages05-06-assets.json','si-pages05-06-reflections.tsv','si-pages05-06-transcription.json','si-pages05-06-author-checkpoint.json']\npreserved={str(B/n):sha(B/n) for n in names}")
target.write_text(src,encoding='utf8')
print(str(target))
