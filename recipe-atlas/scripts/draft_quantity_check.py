"""Conservative checks for scalar local-model drafts; never scientific approval.

An exact source quote can contain both a mass/volume and an amount of substance.
Matching the quote alone does not establish which number belongs to a field.
Unsupported notation stays unresolved for a source reviewer.
"""
from decimal import Decimal,InvalidOperation
import re,unicodedata

NUMBER=r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
UNITS={
 'g':('g',),'mg':('mg',),'kg':('kg',),
 'L':('L',),'mL':('mL',),'uL':('uL','µL','μL'),'µL':('uL','µL','μL'),
 'mol':('mol',),'mmol':('mmol',),'umol':('umol','µmol','μmol'),
 's':('s',),'min':('min',),'h':('h',),'rpm':('rpm',),
 'degC':('°C','° C'),'nm':('nm',),'angstrom':('Å',),
}

def normalize(text):
    text=unicodedata.normalize('NFKC',text).replace('−','-')
    text=re.sub(r'(?<=\w)-\r?\n[ \t]*(?=\w)','',text)
    return re.sub(r'\s+',' ',text).strip()

def check_scalar_quote(value,unit,quote,source_page):
    """Check typed number + adjacent unit in an exact page span, without conversions.

    A passing result does not check the reagent, operation, sample or completeness.
    A null value reports only draft missingness; it does not prove source absence.
    """
    result={'scientific_approval':False,'source_absence_verified':False}
    if value is None:
        return {**result,'status':'missing_value_unverified','quote_present':False}
    if isinstance(value,bool) or not isinstance(value,(int,float,Decimal)):
        return {**result,'status':'invalid_numeric_type','quote_present':False}
    try:
        target=Decimal(str(value))
        if not target.is_finite():raise InvalidOperation
    except (InvalidOperation,ValueError):
        return {**result,'status':'invalid_numeric_value','quote_present':False}
    span=normalize(quote);page=normalize(source_page)
    present=bool(span) and span in page
    if not present:return {**result,'status':'quote_not_in_page','quote_present':False}
    aliases=UNITS.get(unit)
    if not aliases:return {**result,'status':'unit_not_supported','quote_present':True}
    alternatives='|'.join(re.escape(normalize(x)) for x in aliases)
    # Numeric/unit boundaries prevent matching 1 mmol inside 11 mmol or mL as L.
    pattern=re.compile(r'(?<![\w.])('+NUMBER+r')\s*(?:'+alternatives+r')(?![\w])')
    values=[]
    for match in pattern.finditer(span):
        try:values.append(Decimal(match.group(1)))
        except InvalidOperation:pass
    supported=target in values
    return {**result,'status':'numeric_unit_span_supported' if supported else 'numeric_unit_span_not_supported','quote_present':True,'quantity_unit_supported':supported}
