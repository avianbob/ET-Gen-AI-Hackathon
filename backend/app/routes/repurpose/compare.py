"""
Drug Comparison Endpoint

Compares 2-3 drugs using cached pipeline results.
Returns overlapping indications, score comparisons, evidence breakdowns,
per-indication score matrix, dimension leaders, and LLM strategic summary.
"""

import logging
from typing import List, Dict, Any, Optional
from collections import Counter

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from app.services.repurpose.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)
router = APIRouter()

cache_manager = CacheManager()


# --- Request/Response Models ---

class CompareRequest(BaseModel):
    """Drug comparison request."""
    drug_names: List[str]

    @field_validator("drug_names")
    @classmethod
    def validate_drug_names(cls, v):
        if len(v) < 2 or len(v) > 3:
            raise ValueError("Must provide 2-3 drug names")
        return [name.strip() for name in v if name.strip()]


class DrugScores(BaseModel):
    """Average 4D scores for a drug."""
    overall: float = 0
    scientific_evidence: float = 0
    market_opportunity: float = 0
    competitive_landscape: float = 0
    development_feasibility: float = 0


class IndicationScore(BaseModel):
    """Score breakdown for a single indication."""
    indication: str
    overall_score: float = 0
    scientific: float = 0
    market: float = 0
    competitive: float = 0
    feasibility: float = 0
    evidence_count: int = 0


class DrugComparisonItem(BaseModel):
    """Comparison data for a single drug."""
    drug_name: str
    cached: bool = False
    indication_count: int = 0
    evidence_count: int = 0
    scores: DrugScores = DrugScores()
    indications: List[str] = []
    evidence_by_source: Dict[str, int] = {}
    top_indications: List[IndicationScore] = []


class CompareResponse(BaseModel):
    """Drug comparison response."""
    drugs: List[DrugComparisonItem]
    overlapping_indications: List[str] = []
    unique_indications: Dict[str, List[str]] = {}
    indication_scores: Dict[str, Dict[str, float]] = {}
    dimension_leaders: Dict[str, str] = {}
    comparison_summary: str = ""


# --- Helpers ---

def _compute_avg_scores(enhanced_indications: List[Dict]) -> DrugScores:
    """Compute average 4D scores from enhanced indications."""
    if not enhanced_indications:
        return DrugScores()

    def avg(field: str, is_subscore: bool = True) -> float:
        values = []
        for ind in enhanced_indications:
            cs = ind.get("composite_score", {})
            if not cs:
                continue
            if is_subscore:
                sub = cs.get(field, {})
                if isinstance(sub, dict):
                    val = sub.get("score", 0)
                elif isinstance(sub, (int, float)):
                    val = sub
                else:
                    continue
            else:
                val = cs.get(field, 0)
            if isinstance(val, (int, float)):
                values.append(val)
        return round(sum(values) / len(values), 1) if values else 0

    return DrugScores(
        overall=avg("overall_score", is_subscore=False),
        scientific_evidence=avg("scientific_evidence"),
        market_opportunity=avg("market_opportunity"),
        competitive_landscape=avg("competitive_landscape"),
        development_feasibility=avg("development_feasibility"),
    )


def _extract_indications(cached_result: Dict) -> List[str]:
    """Extract indication names from cached result."""
    enhanced = cached_result.get("enhanced_indications", [])
    if enhanced:
        return [ind.get("indication", "") for ind in enhanced if ind.get("indication")]

    ranked = cached_result.get("ranked_indications", [])
    return [ind.get("indication", "") for ind in ranked if ind.get("indication")]


def _extract_evidence_by_source(cached_result: Dict) -> Dict[str, int]:
    """Count evidence items by source agent."""
    all_evidence = cached_result.get("all_evidence", [])
    counts: Dict[str, int] = {}
    for ev in all_evidence:
        src = ev.get("source", "unknown") if isinstance(ev, dict) else getattr(ev, "source", "unknown")
        counts[src] = counts.get(src, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def _extract_top_indications(cached_result: Dict, limit: int = 5) -> List[IndicationScore]:
    """Extract top N indications with per-dimension scores."""
    enhanced = cached_result.get("enhanced_indications", [])
    if not enhanced:
        return []

    results = []
    for ind in enhanced[:limit]:
        cs = ind.get("composite_score", {})
        if not cs:
            continue

        def get_dim(key: str) -> float:
            sub = cs.get(key, {})
            if isinstance(sub, dict):
                return sub.get("score", 0)
            elif isinstance(sub, (int, float)):
                return float(sub)
            return 0

        all_evidence = cached_result.get("all_evidence", [])
        indication_name = ind.get("indication", "")
        ev_count = sum(
            1 for ev in all_evidence
            if (ev.get("indication", "") if isinstance(ev, dict) else getattr(ev, "indication", "")).lower() == indication_name.lower()
        )

        results.append(IndicationScore(
            indication=indication_name,
            overall_score=round(cs.get("overall_score", 0), 1),
            scientific=round(get_dim("scientific_evidence"), 1),
            market=round(get_dim("market_opportunity"), 1),
            competitive=round(get_dim("competitive_landscape"), 1),
            feasibility=round(get_dim("development_feasibility"), 1),
            evidence_count=ev_count,
        ))

    return results


def _build_indication_score_map(cached_result: Dict, drug_name: str) -> Dict[str, float]:
    """Build {indication: overall_score} map for a drug."""
    enhanced = cached_result.get("enhanced_indications", [])
    score_map = {}
    for ind in enhanced:
        name = ind.get("indication", "")
        cs = ind.get("composite_score", {})
        if name and cs:
            score_map[name.lower()] = round(cs.get("overall_score", 0), 1)
    return score_map


async def _generate_llm_summary(drug_items: List[DrugComparisonItem], overlapping: List[str]) -> str:
    """Generate strategic comparison summary using LLM."""
    try:
        from app.services.repurpose.llm.llm_factory import LLMFactory

        client = LLMFactory.get_llm()
        if client is None:
            return ""

        drug_summaries = []
        for d in drug_items:
            top_inds = ", ".join(i.indication for i in d.top_indications[:3]) if d.top_indications else "no scored indications"
            drug_summaries.append(
                f"- {d.drug_name}: overall score {d.scores.overall}, "
                f"{d.indication_count} indications, {d.evidence_count} evidence items, "
                f"top indications: {top_inds}"
            )

        prompt = f"""You are a pharma strategy analyst. Compare these drugs for repurposing potential.
Write 3-4 concise sentences comparing their strengths, weaknesses, and strategic positioning.
Focus on actionable insights for a pharma planning team.

Drugs:
{chr(10).join(drug_summaries)}

Overlapping therapeutic areas: {', '.join(overlapping) if overlapping else 'None'}

Be specific about which drug is stronger in which dimension and why.
Do NOT use markdown formatting. Plain text only."""

        summary = await client.generate(prompt)
        return summary.strip()
    except Exception as e:
        logger.warning(f"LLM comparison summary failed (using fallback): {e}")
        return ""


# --- Endpoint ---

@router.post("/compare", response_model=CompareResponse)
async def compare_drugs(request: CompareRequest):
    """
    Compare 2-3 drugs using cached pipeline results.

    Returns overlapping indications, score comparisons, evidence breakdowns,
    per-indication score matrix, dimension leaders, and strategic summary.
    """
    drug_items = []
    drug_score_maps: Dict[str, Dict[str, float]] = {}  # drug_name → {indication: score}

    for drug_name in request.drug_names:
        cached = await cache_manager.get_cached_result(drug_name)

        if cached:
            enhanced = cached.get("enhanced_indications", [])
            all_evidence = cached.get("all_evidence", [])
            indications = _extract_indications(cached)
            scores = _compute_avg_scores(enhanced)
            evidence_by_source = _extract_evidence_by_source(cached)
            top_indications = _extract_top_indications(cached, limit=5)
            drug_score_maps[drug_name] = _build_indication_score_map(cached, drug_name)

            drug_items.append(DrugComparisonItem(
                drug_name=drug_name,
                cached=True,
                indication_count=len(indications),
                evidence_count=len(all_evidence),
                scores=scores,
                indications=indications,
                evidence_by_source=evidence_by_source,
                top_indications=top_indications,
            ))
        else:
            drug_items.append(DrugComparisonItem(
                drug_name=drug_name,
                cached=False,
            ))
            drug_score_maps[drug_name] = {}

    # Find overlapping indications (appear in 2+ drugs)
    all_indications = []
    for item in drug_items:
        all_indications.extend([ind.lower() for ind in item.indications])

    indication_counts = Counter(all_indications)
    overlapping = [
        ind for ind, count in indication_counts.items() if count >= 2
    ]

    # Find unique indications per drug
    unique_indications = {}
    overlap_set = set(overlapping)
    for item in drug_items:
        unique = [
            ind for ind in item.indications
            if ind.lower() not in overlap_set
        ]
        unique_indications[item.drug_name] = unique

    # Build per-indication score matrix for overlapping indications
    indication_scores: Dict[str, Dict[str, float]] = {}
    for ind_lower in overlapping:
        row: Dict[str, float] = {}
        for item in drug_items:
            score_map = drug_score_maps.get(item.drug_name, {})
            row[item.drug_name] = score_map.get(ind_lower, 0)
        indication_scores[ind_lower] = row

    # Determine dimension leaders
    dimensions = ["scientific_evidence", "market_opportunity", "competitive_landscape", "development_feasibility"]
    dimension_leaders = {}
    for dim in dimensions:
        best_drug = max(drug_items, key=lambda d: getattr(d.scores, dim, 0))
        if getattr(best_drug.scores, dim, 0) > 0:
            dimension_leaders[dim] = best_drug.drug_name

    # Build fallback summary
    cached_count = sum(1 for d in drug_items if d.cached)
    fallback_parts = [
        f"Compared {len(drug_items)} drugs ({cached_count} with cached data)."
    ]
    if overlapping:
        fallback_parts.append(f"Found {len(overlapping)} overlapping indication(s).")
    if any(d.scores.overall > 0 for d in drug_items):
        best = max(drug_items, key=lambda d: d.scores.overall)
        fallback_parts.append(f"Highest overall score: {best.drug_name} ({best.scores.overall}).")
    fallback_summary = " ".join(fallback_parts)

    # Try LLM summary
    llm_summary = await _generate_llm_summary(drug_items, overlapping)
    summary = llm_summary if llm_summary else fallback_summary

    return CompareResponse(
        drugs=drug_items,
        overlapping_indications=overlapping,
        unique_indications=unique_indications,
        indication_scores=indication_scores,
        dimension_leaders=dimension_leaders,
        comparison_summary=summary,
    )
