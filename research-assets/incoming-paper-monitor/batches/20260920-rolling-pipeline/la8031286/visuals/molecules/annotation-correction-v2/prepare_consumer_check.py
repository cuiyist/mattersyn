from pathlib import Path
O=Path(__file__).resolve().parent;A=O.parent
s=(A/'check_consumer.mjs').read_text('utf-8')
old="const O=path.dirname(fileURLToPath(import.meta.url)),A=O,P=path.join(A,'../..');"
assert s.count(old)==1
s=s.replace(old,"const O=path.dirname(fileURLToPath(import.meta.url)),A=path.dirname(O),P=path.join(A,'../..');")
old="const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\\ufeff/,''));"
assert s.count(old)==1
s=s.replace(old,"const effective=JSON.parse(fs.readFileSync(path.join(O,'effective-file-map.json'),'utf8'));\nconst read=p=>JSON.parse(fs.readFileSync(path.dirname(p)===A&&effective[path.basename(p)]?effective[path.basename(p)].path:p,'utf8').replace(/^\\ufeff/,''));")
old="const bound_files=Object.fromEntries([modulePath,path.join(A,'registry-additions.json'),path.join(A,'bindings-proposal.json'),path.join(A,'solution-components-proposal.json'),path.join(A,'stock-component-map.json'),fileURLToPath(import.meta.url)].map(p=>[path.resolve(p),sha(p)]));"
assert s.count(old)==1
s=s.replace(old,"const bound_files=Object.fromEntries([modulePath,...Object.values(effective).map(x=>x.path),fileURLToPath(import.meta.url),path.join(O,'effective-file-map.json')].map(p=>[path.resolve(p),sha(p)]));")
(O/'check_consumer.mjs').write_text(s,'utf-8')
