import test from 'node:test';
import assert from 'node:assert/strict';
import {figureCaptionTexts,appendFigureCaptions,legacyFigureCaptionMetadata} from '../static/figure-captions.mjs';

test('long registered captions remain complete, with no sentence or length truncation',()=>{
 const caption='Synthetic full caption. '+('Long caption detail. '.repeat(100));
 assert.deepEqual(figureCaptionTexts({title:'Figure 1',caption}),[caption.trim()]);
});
test('an explicitly public caption takes precedence and raw quote payloads are not displayed',()=>{
 assert.deepEqual(figureCaptionTexts({public_caption:'Public paraphrase',caption:'Old citation',summary:'Scope',scope:'Scope',quote:'PRIVATE',raw_text:'PRIVATE'}),['Public paraphrase']);
});
test('legacy registered summary captions remain available without inventing a caption',()=>{
 assert.deepEqual(figureCaptionTexts({title:'Figure 2',summary:'Registered source caption'}),['Registered source caption']);
 assert.deepEqual(figureCaptionTexts({title:'Figure 2'}),[]);
});
test('caption and summary duplicates appear once while distinct qualifications remain',()=>{
 assert.deepEqual(figureCaptionTexts({caption:'Caption',summary:'Caption'}),['Caption']);
 assert.deepEqual(figureCaptionTexts({caption:'Caption',summary:'Qualification'}),['Caption','Qualification']);
});
test('cards and enlarged views use the same safe text append interface',()=>{
 const outputs=[];const host={append:node=>outputs.push(node)};
 appendFigureCaptions(host,{caption:'<img onerror=bad>'},(tag,text,cls)=>({tag,text,cls}));
 assert.deepEqual(outputs,[{tag:'p',text:'<img onerror=bad>',cls:'reader-caption-text'}]);
});

test('existing public paraphrases are used before summary and never private quote fields',()=>{
 assert.deepEqual(figureCaptionTexts({caption_paraphrase:'Registered legacy paraphrase',quote:'PRIVATE',raw_text:'PRIVATE'}),['Registered legacy paraphrase']);
 assert.deepEqual(figureCaptionTexts({public_caption:'Public override',caption_paraphrase:'Older paraphrase',summary:'Scope',scope:'Scope'}),['Public override']);
 assert.deepEqual(figureCaptionTexts({caption:'Explicit caption',caption_paraphrase:'Older paraphrase'}),['Explicit caption']);
});

test('concise captions and title dedup remain intact after adding the public fallback',()=>{
 assert.deepEqual(figureCaptionTexts({title:'Figure 1',caption_paraphrase:'Brief TEM image'}),['Brief TEM image']);
 assert.deepEqual(figureCaptionTexts({title:'Brief TEM image',caption_paraphrase:'Brief TEM image'}),[]);
 assert.deepEqual(figureCaptionTexts({title:'Figure 1',quote:'PRIVATE',raw_caption:'PRIVATE'}),[]);
});

test('legacy card/modal normalization retains public description fallback without copying raw fields',()=>{
 const metadata=legacyFigureCaptionMetadata({label:'Figure 2',description:'Existing public description',quote:'PRIVATE',raw_text:'PRIVATE'});
 assert.deepEqual(figureCaptionTexts(metadata),['Existing public description']);
 assert.equal(metadata.title,'Figure 2');
 assert.equal(JSON.stringify(metadata).includes('PRIVATE'),false);
 assert.deepEqual(figureCaptionTexts(legacyFigureCaptionMetadata({label:'Figure 2',caption_paraphrase:'Public paraphrase',description:'Description fallback'})),['Public paraphrase']);
});
