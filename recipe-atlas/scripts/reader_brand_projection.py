"""Finite N1 display projection of authored Reader labels; reviewed inputs stay immutable.

Only exact current-authorship values at the proven metadata categories qualify.
Evidence/quotes, schemas, history, measurements and all other fields are opaque.
"""

CURRENT_AUTHORSHIP = {
    "binding.caption": [
        "DBS-containing route · MatterSyn authored source-qualified sequence; no invented vessel geometry, volume or duration.",
        "MatterSyn authored apparatus schematic; microwave geometry, vessel dimensions, fluid color and fill level are illustrative.",
        "MatterSyn-authored apparatus schematic. A 20 mL glass vial is stirred during CTAC preheat and sequential AgNO3/NaBH4 additions; the 2–3 nm seed range is reported, not a drawn scale.",
        "MatterSyn-authored apparatus schematic. A source-scoped generic reaction-mixture drawing represents Tween-exchanged Ag and Cu(II), without copying standard CTAC, Cu aliquot, temperature or time.",
        "MatterSyn-authored apparatus schematic. After flocculation, the supernatant is centrifuged four times with two 1 wt% and two 0.1 wt% Tween 20 redispersions; spin settings are not reported.",
        "MatterSyn-authored apparatus schematic. Ag and Cu(II) feeds undergo ten cycles of 1 min vacuum sonication followed by argon replenishment, then react under argon; exact inherited aliquots are omitted.",
        "MatterSyn-authored apparatus schematic. BDAC-treated capped vial rests undisturbed in a 30 °C oven after removal of the stir bar; rod/wire flocculate is separated from supernatant.",
        "MatterSyn-authored apparatus schematic. Green QD solution is spin-coated on the AgNS/ITO film; QD preparation follows prior reports, and coating speed/time/volume are not supplied.",
        "MatterSyn-authored apparatus schematic. Green and red QD reference films are shown on bare ITO without AgNSs; control-specific spin conditions are not reported.",
        "MatterSyn-authored apparatus schematic. Red QD solution is spin-coated on the AgNS/ITO film; QD preparation follows prior reports, and coating speed/time/volume are not supplied.",
        "MatterSyn-authored apparatus schematic. SDS/PVP addition precedes the 0.2 µm syringe membrane filter; the filtered sample moves to a 50 mL tube for centrifugation and redispersion.",
        "MatterSyn-authored apparatus schematic. The 460 µL Cu(II) addition is source-labeled for this variant; vessel, concentration and other reaction conditions are not assigned from the 380 µL standard branch.",
        "MatterSyn-authored apparatus schematic. The 580 µL Cu(II) addition is source-labeled for this variant; vessel, concentration and other reaction conditions are not assigned from the 380 µL standard branch.",
        "MatterSyn-authored apparatus schematic. The Cu(I) negative control uses an acetonitrile/water mixture because Cu(I) is not soluble in water; precursor, ratio and dose are unreported.",
        "MatterSyn-authored apparatus schematic. The ITO glass substrate holds a 9 mm × 1.8 mm sticky chamber for 200 µL PVP-AgNS dispersion (OD 80 at 1 cm); drying and wash steps are source-reported.",
        "MatterSyn-authored apparatus schematic. The capped 20 mL glass vial shows the sequential seed/AgTFA addition and later ascorbic-acid growth phase; the cap is source-reported.",
        "MatterSyn-authored apparatus schematic. The control uses AgNP solution before oxidative etching for a film compared with green-QD optical variation; its preparation settings are not inherited from AgNS film.",
        "MatterSyn-authored apparatus schematic. The selected supernatant, rather than the rod/wire flocculate, is transferred to a 50 mL centrifuge tube for two spins and redispersion.",
        "MatterSyn-authored apparatus schematic. The standard branch uses a 20 mL glass vial, 60 °C preheat and Cu(II) addition; no sealed or inert etch atmosphere is implied.",
        "MatterSyn-authored apparatus schematic. This comparative dose schematic separates the source-labeled Cu(II) additions and observed size trend without assigning unreported common conditions or dose–diameter pairs.",
        "MatterSyn-authored aqueous synthesis scene; vessel geometry, liquid levels and scales are illustrative.",
        "MatterSyn-authored conceptual PVP branch diagram; exact masses, times and uncertainties remain in the canonical record.",
        "MatterSyn-authored conceptual assembly: cleaned paired ITO slides are immersed before QD spreading, followed by film transfer and Ag-prism deposition. Immersion depth and apparatus dimensions are not reported; relative photoanneal/deposition order remains unresolved.",
        "MatterSyn-authored conceptual branch diagram; Ag₂Se, partial Ag, PbSe and CuSe paths remain separate in the record.",
        "MatterSyn-authored conceptual branch map; no measured particle or ligand geometry.",
        "MatterSyn-authored conceptual operation illustration; no measured dimensions or unreported conditions.",
        "MatterSyn-authored conceptual operation; vessel geometry and colors are illustrative.",
        "MatterSyn-authored conceptual route overview; exact conditions and conflict remain in the canonical record.",
        "MatterSyn-authored conceptual route overview; five shell and QD branches remain separate in the record.",
        "MatterSyn-authored conceptual seed-to-rod sequence; Au and Au–Cu remain distinct.",
        "MatterSyn-authored conceptual seed-to-rod sequence; no measured particle geometry.",
        "MatterSyn-authored conceptual sequence; wire shapes and vessel geometry are illustrative, not measured.",
        "MatterSyn-authored conceptual source-bound stage schematic; apparatus geometry and colors are illustrative.",
        "MatterSyn-authored conceptual stage scene; dimensions, colors and apparatus geometry are illustrative.",
        "MatterSyn-authored conceptual stage; vessel geometry, liquid levels and particle drawings are illustrative.",
        "MatterSyn-authored evidence branch map; optical states and endpoint diffraction remain distinct.",
        "MatterSyn-authored process schematic; no atomistic interface or repeated aliquot amount asserted.",
        "MatterSyn-authored process summary of chip-wall preparation: piranha cleaning precedes FDTS solution silanization. Based on main p.3 and SI pp.1,3 Figure S1(c); not a device cross-section, measured coating geometry or nanoparticle image. See the unchanged source Figure S1 in the gallery.",
        "MatterSyn-authored source-bound stage illustration; geometry is conceptual and solvent inputs follow the listed operation, not an additional unlisted dose.",
        "MatterSyn-authored source-bound stage illustration; shapes and geometry are conceptual, not measured.",
        "MatterSyn-authored source-bound stage schematic; vessel, color and particle depictions are illustrative.",
        "MatterSyn-authored source-level NC family placeholder; use a separately bound solvent branch for physical redispersion.",
        "MatterSyn-authored stage schematic for cast conductivity films; apparatus geometry is illustrative, not measured.",
        "MatterSyn-authored stage schematic for characterize nc inputs; apparatus geometry is illustrative, not measured.",
        "MatterSyn-authored stage schematic for compare film packing; apparatus geometry is illustrative, not measured.",
        "MatterSyn-authored stage schematic for filter and store nc inputs; apparatus geometry is illustrative, not measured.",
        "MatterSyn-authored stage schematic for grow ag₂te nanocrystals; apparatus geometry is illustrative, not measured.",
        "MatterSyn-authored stage schematic for make thermopower specimens; apparatus geometry is illustrative, not measured.",
        "MatterSyn-authored stage schematic for mix ag₂te and pbte ncs; apparatus geometry is illustrative, not measured.",
        "MatterSyn-authored stage schematic for prepare ag–top stock; apparatus geometry is illustrative, not measured.",
        "MatterSyn-authored stage schematic for prepare top–te stock; apparatus geometry is illustrative, not measured.",
        "MatterSyn-authored stage schematic for quench and purify ag₂te; apparatus geometry is illustrative, not measured.",
        "MatterSyn-authored stage schematic for treat conductivity films; apparatus geometry is illustrative, not measured.",
        "MatterSyn-authored stage schematic; vessel geometry, liquid color and particle drawings are illustrative.",
        "MatterSyn-authored time-resolved flow/SAXS setup schematic; not a source photograph.",
        "MatterSyn-authored, source-grounded schematic. 100 mL Schlenk, argon, CdSe heat/inject/grow sequence; schematic apparatus geometry only. No measured apparatus geometry or ACS figure pixels.",
        "MatterSyn-authored, source-grounded schematic. Ag₂Se drying follows the CdSe method; distinct Ag₂Se settings are not restated. No measured apparatus geometry or ACS figure pixels.",
        "MatterSyn-authored, source-grounded schematic. Ambient fluorescent light, one week undisturbed CdSe wet-gel formation. No measured apparatus geometry or ACS figure pixels.",
        "MatterSyn-authored, source-grounded schematic. Cautious AgNO₃ solution addition to monolith; main 12 h and SI few-hour statements retained separately. No measured apparatus geometry or ACS figure pixels.",
        "MatterSyn-authored, source-grounded schematic. Dark MUA exchange, ethyl acetate purification and final methanolic dispersion. No measured apparatus geometry or ACS figure pixels.",
        "MatterSyn-authored, source-grounded schematic. SPI-DRY boat and source-described CdSe supercritical CO₂ sequence. No measured apparatus geometry or ACS figure pixels.",
        "No-DBS control · MatterSyn authored source-qualified sequence; no invented vessel geometry, volume or duration.",
        "Same stopped-flow instrument type for a distinct 1.4/5 mM DDA series. MatterSyn-authored; not a measured particle image.",
        "Separate feed preparation, 0.45 µm PTFE filtration and helium sparging. MatterSyn-authored; not a measured particle image.",
        "Separate stopped-flow optical setup; figure captions differ 6.67 versus 6.66 mM. MatterSyn-authored; not a measured particle image.",
        "Stage-specific wafer fabrication and bonding context. MatterSyn-authored; not a measured particle image.",
        "Three-inlet chip and Se K-edge observation geometry. MatterSyn-authored; not a measured particle image."
    ],
    "binding.source_locator": [
        "Main PDF p.2, Experimental Section 2-2; MatterSyn-authored symbolic handling"
    ],
    "overview.caption": [
        "MatterSyn-authored process map; original Ag2Te route, external PbTe input and distinct film branches.",
        "MatterSyn-authored route overview; stage-specific apparatus and exact settings are supplied by the separate operation bindings and canonical record."
    ],
    "record_figure.notes": [
        "MatterSyn-authored conceptual diagram; no measured geometry or atom positions.",
        "MatterSyn-authored interpretation, not a measured micrograph or coordinate model."
    ],
    "record_figure.sample_linkage": [
        "MatterSyn-authored, not-to-scale specimen illustration; no measured geometry or atomic positions."
    ],
    "record_figure.sample_scope": [
        "MatterSyn-authored, not-to-scale specimen illustration; no measured geometry or atomic positions."
    ],
    "record_figure.scope": [
        "MatterSyn-authored, not-to-scale specimen illustration; no measured geometry or atomic positions."
    ],
    "record_figure.summary": [
        "MatterSyn-authored conceptual template, AgNO3 loading, TBAB reduction, washing, and drying route.",
        "MatterSyn-authored size bracket explaining the reported 4 nm coherent-domain estimate.",
        "MatterSyn-authored, not-to-scale specimen illustration; no measured geometry or atomic positions."
    ],
    "source_figure.notes": [
        "MatterSyn-authored interpretation, not a measured micrograph or coordinate model."
    ],
    "source_figure.summary": [
        "MatterSyn-authored conceptual template, AgNO3 loading, TBAB reduction, washing, and drying route."
    ]
}


def _rename(value, category):
    return value.replace('MatterSyn', 'NanoXtalSyn') if isinstance(value, str) and value in CURRENT_AUTHORSHIP.get(category, ()) else value


def _items(items, project):
    if not isinstance(items, list): return items
    changed = [project(item) for item in items]
    return items if all(a is b for a, b in zip(items, changed)) else changed


def _fields(value, category, names, notes=False):
    if not isinstance(value, dict): return value
    changes = {}
    for name in names:
        before = value.get(name); after = _rename(before, category + '.' + name)
        if after is not before: changes[name] = after
    if notes and 'notes' in value:
        before = value['notes']; after = _items(before, lambda item: _rename(item, category + '.notes'))
        if after is not before: changes['notes'] = after
    return {**value, **changes} if changes else value


def _record(value):
    if not isinstance(value, dict): return value
    changes = {}
    if 'figures' in value:
        before = value['figures']; after = _items(before, lambda row: _fields(row, 'record_figure', ('summary', 'scope', 'sample_scope', 'sample_linkage'), notes=True))
        if after is not before: changes['figures'] = after
    art = value.get('protocol_art')
    if isinstance(art, dict):
        art_changes = {}
        if 'bindings' in art:
            before = art['bindings']; after = _items(before, lambda row: _fields(row, 'binding', ('caption', 'source_locator')))
            if after is not before: art_changes['bindings'] = after
        if 'overview' in art:
            before = art['overview']; after = _fields(before, 'overview', ('caption',))
            if after is not before: art_changes['overview'] = after
        if art_changes: changes['protocol_art'] = {**art, **art_changes}
    return {**value, **changes} if changes else value


def _table(value, project):
    if not isinstance(value, dict): return value
    changed = {key: project(item) for key, item in value.items()}
    return value if all(changed[key] is item for key, item in value.items()) else changed


def project_reader_branding(view):
    """Copy on change before public serialization; never mutate the sidecar."""
    if not isinstance(view, dict): return view
    changes = {}
    before = view.get('records'); after = _table(before, _record)
    if after is not before: changes['records'] = after
    before = view.get('figures_by_source')
    after = _table(before, lambda rows: _items(rows, lambda row: _fields(row, 'source_figure', ('summary',), notes=True)))
    if after is not before: changes['figures_by_source'] = after
    return {**view, **changes} if changes else view
