"""Pure formula check AFTER independently established CID/name/connectivity identity.

This helper does not establish identity, choose a CID, compare isomers, alter the
input strings, or create a molecular graph. The caller must keep every existing
identity/connectivity/stereochemistry check. It compares exact integer elemental
composition (including explicit bracketed isotopes) and net written charge.

Supported: element order, nested integer groups, middle-dot hydrates and explicit
charges such as NH4+, Fe+3, Fe^3+, and SO4^2-. Ambiguous Fe3+/O2+ and digit-dot-digit
ASCII forms are not interpreted. Ac/OAc shorthand, fractions and variable counts
are unsupported. An identical nonblank input string remains equal even when this
conservative parser does not understand it; no normalization broadens that fallback.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import NamedTuple

# Ac/OAc shorthand is conservatively unsupported here.
ELEMENTS=frozenset(('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og').split())
MAX_LENGTH=512
MAX_DEPTH=16
MAX_INTEGER=1_000_000

class FormulaKey(NamedTuple):
    atoms: tuple[tuple[str, int, int], ...]  # (element, explicit isotope or0, count)
    charge: int

class UnsupportedFormula(ValueError):
    pass

def _positive_integer(text: str) -> int:
    if not text or len(text)>7 or not re.fullmatch(r'[1-9][0-9]*',text):
        raise UnsupportedFormula('nonpositive_or_ambiguous_count')
    value=int(text)
    if not 0<value<=MAX_INTEGER:
        raise UnsupportedFormula('count_out_of_bounds')
    return value

class _Parser:
    def __init__(self, text: str):
        self.text=text
        self.i=0

    def multiplier(self) -> int:
        start=self.i
        while self.i<len(self.text) and self.text[self.i].isascii() and self.text[self.i].isdigit():
            self.i+=1
        return _positive_integer(self.text[start:self.i]) if self.i>start else 1

    def sequence(self, closing: str | None=None, depth: int=0) -> Counter:
        if depth>MAX_DEPTH:
            raise UnsupportedFormula('group_depth')
        atoms=Counter()
        units=0
        while self.i<len(self.text):
            char=self.text[self.i]
            if closing and char==closing:
                self.i+=1
                if not units:
                    raise UnsupportedFormula('empty_group')
                return atoms
            if char in '([':
                if char=='[':
                    isotope=re.match(r'\[(\d+)([A-Z][a-z]?)\]',self.text[self.i:])
                    if isotope:
                        mass=_positive_integer(isotope[1]);element=isotope[2]
                        if element not in ELEMENTS:
                            raise UnsupportedFormula('unsupported_element_or_shorthand')
                        self.i+=len(isotope[0]);atoms[element,mass]+=self.multiplier();units+=1
                        continue
                self.i+=1
                group=self.sequence(')' if char=='(' else ']',depth+1)
                scale=self.multiplier()
                for key,count in group.items():
                    atoms[key]+=count*scale
                units+=1
                continue
            match=re.match(r'[A-Z][a-z]?',self.text[self.i:])
            if not match or match[0] not in ELEMENTS:
                raise UnsupportedFormula('unsupported_token')
            self.i+=len(match[0]);atoms[match[0],0]+=self.multiplier();units+=1
        if closing:
            raise UnsupportedFormula('unclosed_group')
        if not units:
            raise UnsupportedFormula('empty_formula')
        return atoms

def _charge(text: str) -> tuple[str,int]:
    # Caret disambiguates the magnitude from any atomic/group subscript.
    marked=re.search(r'\^(?:(\d+)([+-])|([+-])(\d*))$',text)
    if marked:
        magnitude=_positive_integer(marked[1] or marked[4]) if (marked[1] or marked[4]) else 1
        sign=marked[2] or marked[3]
        return text[:marked.start()],magnitude*(1 if sign=='+' else -1)
    suffix=re.search(r'([+-])(\d*)$',text)
    if not suffix:
        return text,0
    core=text[:suffix.start()]
    if not suffix[2] and (re.fullmatch(r'[A-Z][a-z]?\d+',core) or re.search(r'[)\]]\d+$',core)):
        raise UnsupportedFormula('ambiguous_charge_subscript')
    magnitude=_positive_integer(suffix[2]) if suffix[2] else 1
    return core,magnitude*(1 if suffix[1]=='+' else -1)

def parse_formula(formula: str) -> FormulaKey | None:
    """Return a strict composition key, or None for any unsupported/ambiguous form."""
    if not isinstance(formula,str) or not formula.strip() or len(formula)>MAX_LENGTH:
        return None
    text=formula.strip()
    # Never read decimal/fractional stoichiometry as an ASCII hydrate separator.
    if re.search(r'\d\.\d',text):
        return None
    parts=re.split(r'[.\u00b7]',text)
    if any(not part.strip() for part in parts):
        return None
    total=Counter();charge=0
    try:
        for index,part in enumerate(parts):
            part=part.strip()
            if re.search(r'\s',part):
                raise UnsupportedFormula('internal_whitespace')
            coefficient=1
            leading=re.match(r'\d+',part)
            if leading:
                if index==0:
                    raise UnsupportedFormula('ambiguous_leading_coefficient_or_isotope')
                coefficient=_positive_integer(leading[0]);part=part[len(leading[0]):]
            body,part_charge=_charge(part)
            parser=_Parser(body);atoms=parser.sequence()
            for key,count in atoms.items():
                value=count*coefficient
                if value>MAX_INTEGER:
                    raise UnsupportedFormula('total_count_out_of_bounds')
                total[key]+=value
                if total[key]>MAX_INTEGER:
                    raise UnsupportedFormula('total_count_out_of_bounds')
            charge+=coefficient*part_charge
        return FormulaKey(tuple((element,isotope,count) for (element,isotope),count in sorted(total.items())),charge)
    except (UnsupportedFormula,ValueError,TypeError,RecursionError):
        return None

def formula_equivalent(left: str, right: str) -> bool:
    """Check only formula consistency for an ALREADY independently identified entity.

    Equal formula keys are never evidence that different CIDs, isomers, stereo
    forms, connectivity, separate-ion graphs, or unidentified materials are equal.
    """
    if not isinstance(left,str) or not isinstance(right,str) or not left.strip() or not right.strip():
        return False
    if left==right:
        return True
    a=parse_formula(left);b=parse_formula(right)
    return a is not None and b is not None and a==b
