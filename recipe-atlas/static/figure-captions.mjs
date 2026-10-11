/** Display only registered public figure metadata; never read private caption files. */
export function figureCaptionTexts(figure={}) {
 const clean=value=>typeof value==='string'?value.trim():'';
 const primary=clean(figure.public_caption)||clean(figure.caption)||clean(figure.caption_paraphrase)||clean(figure.summary);
 const summary=clean(figure.summary),scope=clean(figure.scope_label||figure.scope);
 return [...new Set([primary,summary!==scope?summary:''].filter(text=>text&&text!==clean(figure.title)))];
}
export function appendFigureCaptions(host,figure,element){
 for(const text of figureCaptionTexts(figure))host.append(element('p',text,'reader-caption-text'));
}

/** Normalize already-public legacy caption fields; do not read original quotes. */
export function legacyFigureCaptionMetadata(figure={}) {
 return {
  title:figure.label||figure.id||'Figure',
  public_caption:figure.public_caption,
  caption:figure.caption||figure.caption_paraphrase||figure.description,
  caption_paraphrase:figure.caption_paraphrase,
  summary:figure.summary,
  scope_label:figure.scope_label,
  scope:figure.scope
 };
}
