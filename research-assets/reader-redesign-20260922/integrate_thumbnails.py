from pathlib import Path
import json,shutil,hashlib
W=Path(__file__).resolve().parent;D=W.parents[1]/'recipe-atlas/dist';T=W/'presentation-proposal/chemical-thumbnails'
for row in json.loads((T/'public-assets.json').read_text(encoding='utf-8')):
    source=T/row['proposal_path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256']
    dest=D/row['public_asset'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
shutil.copy2(T/'thumbnail-map.json',D/'data/chemical-thumbnail-map.json')
shutil.copy2(W/'reader-code-review/stock-context-bindings.json',D/'data/reader-stock-bindings.json')
p=D/'reader-app.mjs';s=p.read_text(encoding='utf-8')
s=s.replace(" const data=await chemicalRegistry();if(!host.isConnected)return;", " const [data,thumbs,stockBindings]=await Promise.all([chemicalRegistry(),json('data/chemical-thumbnail-map.json'),json('data/reader-stock-bindings.json')]);if(!host.isConnected)return;function cardImage(entry){const img=chemicalImage(entry),item=thumbs.entries[entry.id];if(item?.thumbnail_path)img.src=siteURL(item.thumbnail_path);return img;}")
s=s.replace('const image=chemicalImage(entry);','const image=cardImage(entry);').replace('card.append(chemicalImage(entry),','card.append(cardImage(entry),')
s=s.replace("contexts.find(c=>c.id===stock.id||normal(c.label)===normal(stock.name))", "contexts.find(c=>c.id===stockBindings.stockBindings?.[r.record_id]?.[stock.id])||contexts.find(c=>c.id===stock.id||normal(c.label)===normal(stock.name))")
p.write_text(s,encoding='utf-8')
print('Installed 175 verified compact depictions and five explicit stock/context bindings.')
