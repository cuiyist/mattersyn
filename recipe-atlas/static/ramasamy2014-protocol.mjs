const stages={
  "solvent-pretreatment": {
    "asset": "assets/reader-schematics/ramasamy2014cusb/solvent-pretreatment.svg",
    "caption": "Solvents are dried over molecular sieves and purged with high-purity Ar for 30 min. Sieve specification, apparatus and flow rate are not stated."
  },
  "prepare-metal-mixture": {
    "asset": "assets/reader-schematics/ramasamy2014cusb/prepare-metal-mixture.svg",
    "caption": "The metal precursor mixture is degassed for 15 min at room temperature and backfilled with N2 for 15 min. Vessel geometry is illustrative; the source supplies no quantitative pressure."
  },
  "prepare-sulfur-stock": {
    "asset": "assets/reader-schematics/ramasamy2014cusb/prepare-sulfur-stock.svg",
    "caption": "Elemental S/OLA and mixed-thiol/OLA are separate sulfur-source alternatives. Only the S/OLA stock has reported charges and three degassing cycles. Thiol amounts and ratio remain unreported."
  },
  "hot-injection": {
    "asset": "assets/reader-schematics/ramasamy2014cusb/hot-injection.svg",
    "caption": "Rapid sulfur-source injection into the heated metal mixture. Temperature is the selected condition-map cell; the general synthesis gives 10–30 min, not an individually measured dwell for every cell. Heater and syringe geometry are conceptual."
  },
  "precipitation-and-wash": {
    "asset": "assets/reader-schematics/ramasamy2014cusb/precipitation-and-wash.svg",
    "caption": "Hexane and ethanol precipitation; centrifugation at 4000 rpm for 5 min and three wash cycles. Rotor dimensions and relative centrifugal force are not reported; geometry is illustrative."
  }
};
export function buildRamasamy2014Scene(o,r){return r.lineage?.source_group==='ramasamy2014cusb'?stages[o.id]||null:null;}
export function createRamasamy2014Art(o,r,prefix=''){const s=buildRamasamy2014Scene(o,r);if(!s)return null;const d=document.createElement('div'),img=document.createElement('img');d.className='protocol-art protocol-art-ramasamy2014';img.src=prefix+s.asset;img.alt=o.label+' · conceptual source-stage illustration';img.style.width='100%';img.style.height='100%';img.style.objectFit='contain';d.append(img);return d;}
