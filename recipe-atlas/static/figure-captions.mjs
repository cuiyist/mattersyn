/** Display only registered public figure metadata; never read private caption files. */
export function figureCaptionTexts(figure={}) {
 const clean=value=>typeof value==='string'?value.trim():'';
 const primary=clean(figure.public_caption)||clean(figure.caption)||clean(figure.summary);
 const summary=clean(figure.summary),scope=clean(figure.scope_label||figure.scope);
 return [...new Set([primary,summary!==scope?summary:''].filter(text=>text&&text!==clean(figure.title)))];
}
export function appendFigureCaptions(host,figure,element){
 for(const text of figureCaptionTexts(figure))host.append(element('p',text,'reader-caption-text'));
}
