"""
Query understanding: rule-based fallback when Gemini is unavailable.
Returns structured PharmaQueryContext from raw query string.
"""
import re
from typing import List, Optional
from ..schemas.analysis import PharmaQueryContext


# Common region keywords (case-insensitive)
REGION_PATTERNS = [
    r"\b(US|USA|United States)\b",
    r"\b(EU|EU5|Europe)\b",
    r"\b(UK|United Kingdom)\b",
    r"\b(India|China|Japan)\b",
    r"\b(APAC|Asia)\b",
    r"\b(LATAM|Latin America)\b",
]

# Development phase keywords
PHASE_PATTERNS = [
    (r"\b(preclinical|pre-clinical)\b", "preclinical"),
    (r"\bphase\s*I\b", "Phase I"),
    (r"\bphase\s*II\b", "Phase II"),
    (r"\bphase\s*III\b", "Phase III"),
    (r"\blaunched\b", "launched"),
    (r"\b(approved|approval)\b", "approved"),
]

# Simple "for X" / "in Y" patterns for disease/indication
FOR_INDICATION = re.compile(r"\bfor\s+(?:treating\s+)?([^,\.;]+?)(?:\s+in\s+|\s+symptoms?|\s+market|,|\.|$)", re.I)
IN_REGION = re.compile(r"\bin\s+(the\s+)?(US|USA|EU|EU5|India|China|Japan|UK|Europe|APAC)\b", re.I)

# "alternative(s) of X" / "alternatives to X" / "substitute for X"
ALTERNATIVES_OF = re.compile(r"alternatives?\s+(?:of|to)\s+(.+)", re.I)
SUBSTITUTE_FOR = re.compile(r"substitute\s+for\s+(.+)", re.I)
INSTEAD_OF = re.compile(r"(?:what\s+)?(?:can\s+i\s+use\s+)?instead\s+of\s+(.+)", re.I)

# "X medicine" / "medicine for X" / "X medication" -> disease=X, drug=null (user wants treatments for condition X)
MEDICINE_FOR = re.compile(r"(?:medicine|medication|mediciene|drugs?|treatment)\s+for\s+(.+)", re.I)
X_MEDICINE = re.compile(r"(.+?)\s+(?:medicine|medication|mediciene)\s*$", re.I)

# Common condition typos
TYPO_DISEASE = {"asthama": "Asthma", "astma": "Asthma", "diabetis": "Diabetes", "diabates": "Diabetes"}


def parse_fallback(raw_query: str, complexity: str = "normal") -> PharmaQueryContext:
    """
    Extract structured fields from raw query using regex/keywords.
    Used when Gemini is not available or extraction fails.
    """
    raw = (raw_query or "").strip()
    drug: Optional[str] = None
    disease: Optional[str] = None
    symptoms: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    phase: Optional[str] = None
    query_type: str = "analysis"
    reference_drug: Optional[str] = None

    # "alternatives to X" / "alternative of X" / "substitute for X"
    for pattern in (ALTERNATIVES_OF, SUBSTITUTE_FOR, INSTEAD_OF):
        m = pattern.search(raw)
        if m:
            reference_drug = m.group(1).strip()
            if reference_drug:
                reference_drug = reference_drug.rstrip("?.!,")
                query_type = "alternatives"
                drug = reference_drug
            break

    # Regions
    found_regions: List[str] = []
    for pat in REGION_PATTERNS:
        for m in re.finditer(pat, raw, re.I):
            r = m.group(1).strip()
            if r and r not in found_regions:
                found_regions.append(r)
    if found_regions:
        regions = found_regions

    # Phase
    for pat, label in PHASE_PATTERNS:
        if re.search(pat, raw, re.I):
            phase = label
            break

    # "medicine for X" / "medication for X" -> disease=X, drug=null
    m = MEDICINE_FOR.search(raw)
    if m:
        disease_cand = m.group(1).strip().rstrip("?.!,")
        if disease_cand:
            disease = TYPO_DISEASE.get(disease_cand.lower(), disease_cand)
            drug = None
    # "X medicine" / "X medication" at end (e.g. "Asthama Mediciene") -> disease=X, drug=null
    if disease is None and drug is None:
        m = X_MEDICINE.search(raw)
        if m:
            condition = m.group(1).strip().rstrip("?.!,")
            if condition and condition.lower() not in ("the", "a", "some", "any"):
                disease = TYPO_DISEASE.get(condition.lower(), condition)
                drug = None
    # "for <indication/disease>" and drug = text before " for "
    if disease is None:
        m = FOR_INDICATION.search(raw)
        if m:
            disease = m.group(1).strip()
            before_for = raw[: m.start()].strip()
            if before_for and drug is None:
                drug = before_for
    # "in <region>"
    for m in IN_REGION.finditer(raw):
        reg = m.group(2).strip()
        if reg and (not regions or reg not in regions):
            regions = regions or []
            if reg not in regions:
                regions.append(reg)

    # Drug: if not set yet and not a "X medicine" query, use first token(s) as molecule name
    if not drug and raw and disease is None:
        parts = raw.split()
        if len(parts) >= 1:
            drug = parts[0]
            if len(parts) >= 2 and parts[1].lower() not in ("for", "in", "and", "the", "market", "analysis"):
                drug = " ".join(parts[:2])
            if len(parts) >= 3 and parts[2].lower() not in ("for", "in", "and", "the", "market", "analysis"):
                drug = " ".join(parts[:3])
    if not drug and not disease:
        drug = raw.split(" for ")[0].strip() if " for " in raw else (raw.split(",")[0].strip() or raw)

    # Symptoms: simple "symptoms: X" or "symptoms X"
    sym_match = re.search(r"\bsymptoms?\s*[:\-]?\s*([^,\.]+)", raw, re.I)
    if sym_match:
        symptom_str = sym_match.group(1).strip()
        symptoms = [s.strip() for s in re.split(r"[,;]", symptom_str) if s.strip()]

    # When we inferred disease from "X medicine", keep drug=null so trials search by condition
    drug_out = drug if drug is not None else (None if disease else (raw or None))
    # Ensure diseases and side_effects are set (fallback parser does not extract them; use empty list)
    return PharmaQueryContext(
        drug=drug_out,
        disease=disease,
        diseases=None,
        symptoms=symptoms,
        side_effects=None,
        regions=regions,
        phase=phase,
        raw_query=raw,
        complexity=complexity or "normal",
        query_type=query_type,
        reference_drug=reference_drug,
    )
