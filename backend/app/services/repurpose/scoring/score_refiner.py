"""
Score Refiner - Adjusts composite scores using enhanced comparative, market segment,
and scientific analysis data. Runs after analyze_comparatives to incorporate deeper
insights into the numerical scores.

Each dimension score can be adjusted by up to +/- 20 points based on the enhanced data.
"""

from typing import Dict, List, Tuple, Any, Optional
from app.schemas.repurpose_scoring import (
    SubScore, CompositeScore, ConfidenceLevel,
    EnhancedIndicationResult, EnhancedOpportunityData,
    ScientificDetails, MarketSegment, SideEffectComparison,
    ComparativeAdvantage,
)
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("scoring.refiner")

REFINEMENT_CAP = 20  # Max +/- adjustment per dimension


class ScoreRefiner:
    """
    Refines composite scores using enhanced opportunity data.

    The base composite scorer uses raw evidence, market estimates, and competitor data.
    This refiner applies bounded adjustments based on deeper analysis:
    - Scientific: binding affinity, pathways, publications, biomarkers
    - Market: segment-level unmet need, growth rate, competitive intensity
    - Competitive: comparative advantages vs standard of care, safety profile
    - Feasibility: safety advantage, biomarker-guided trials, preclinical models
    """

    def refine_scores(
        self,
        enhanced_indications: List[EnhancedIndicationResult],
        enhanced_opportunities: Dict[str, EnhancedOpportunityData],
    ) -> List[EnhancedIndicationResult]:
        """
        Apply refinements to all enhanced indications and re-sort by overall score.

        Returns a new list of EnhancedIndicationResult with adjusted scores.
        """
        if not enhanced_opportunities:
            return enhanced_indications

        refined = []
        for result in enhanced_indications:
            indication = result.indication
            enhanced_data = enhanced_opportunities.get(indication)

            if not enhanced_data:
                refined.append(result)
                continue

            try:
                refined_result = self._refine_indication(result, enhanced_data)
                refined.append(refined_result)
            except Exception as e:
                logger.warning(f"Refinement failed for {indication}: {e}")
                refined.append(result)

        # Re-sort by overall score descending
        refined.sort(key=lambda r: r.composite_score.overall_score, reverse=True)

        return refined

    def _refine_indication(
        self,
        result: EnhancedIndicationResult,
        enhanced_data: EnhancedOpportunityData,
    ) -> EnhancedIndicationResult:
        """Refine a single indication's composite score."""
        refinements = self._calculate_refinements(enhanced_data)
        cs = result.composite_score

        # Refine each dimension
        new_sci = self._refine_subscore(
            cs.scientific_evidence,
            *refinements["scientific_evidence"]
        )
        new_mkt = self._refine_subscore(
            cs.market_opportunity,
            *refinements["market_opportunity"]
        )
        new_comp = self._refine_subscore(
            cs.competitive_landscape,
            *refinements["competitive_landscape"]
        )
        new_feas = self._refine_subscore(
            cs.development_feasibility,
            *refinements["development_feasibility"]
        )

        # Recalculate overall score
        new_overall = round(
            new_sci.weighted_score
            + new_mkt.weighted_score
            + new_comp.weighted_score
            + new_feas.weighted_score,
            1,
        )
        new_overall = min(new_overall, 100.0)

        # Recalculate data completeness
        new_completeness = round(
            (
                new_sci.data_completeness
                + new_mkt.data_completeness
                + new_comp.data_completeness
                + new_feas.data_completeness
            ) / 4,
            2,
        )

        new_composite = CompositeScore(
            indication=cs.indication,
            overall_score=new_overall,
            confidence_level=ConfidenceLevel.from_score(new_overall),
            scientific_evidence=new_sci,
            market_opportunity=new_mkt,
            competitive_landscape=new_comp,
            development_feasibility=new_feas,
            key_strengths=cs.key_strengths,
            key_risks=cs.key_risks,
            recommended_next_steps=cs.recommended_next_steps,
            evidence_count=cs.evidence_count,
            data_completeness=new_completeness,
            scored_at=cs.scored_at,
        )

        return EnhancedIndicationResult(
            indication=result.indication,
            confidence_score=new_overall,
            composite_score=new_composite,
            evidence_count=result.evidence_count,
            supporting_sources=result.supporting_sources,
        )

    def _refine_subscore(
        self,
        subscore: SubScore,
        total_points: float,
        factor_details: Dict[str, float],
    ) -> SubScore:
        """Apply a bounded refinement to a single SubScore."""
        clamped = max(-REFINEMENT_CAP, min(REFINEMENT_CAP, total_points))
        new_score = max(0, min(100, round(subscore.score + clamped, 1)))
        new_weighted = round(new_score * subscore.weight, 1)

        # Track refinement in factors
        updated_factors = dict(subscore.factors)
        updated_factors["_base_score"] = subscore.score
        updated_factors["_refinement_total"] = round(clamped, 1)
        for key, val in factor_details.items():
            updated_factors[f"_ref_{key}"] = round(val, 1)

        # Update notes
        updated_notes = list(subscore.notes)
        if clamped > 0:
            updated_notes.append(f"Enhanced analysis bonus: +{clamped:.1f}")
        elif clamped < 0:
            updated_notes.append(f"Enhanced analysis penalty: {clamped:.1f}")

        # Bump data completeness slightly (we have more data now)
        new_completeness = min(subscore.data_completeness + 0.05, 1.0)

        return SubScore(
            dimension=subscore.dimension,
            score=new_score,
            weight=subscore.weight,
            weighted_score=new_weighted,
            confidence=ConfidenceLevel.from_score(new_score),
            factors=updated_factors,
            data_completeness=round(new_completeness, 2),
            notes=updated_notes,
            competitors=subscore.competitors,
        )

    def _calculate_refinements(
        self, enhanced_data: EnhancedOpportunityData
    ) -> Dict[str, Tuple[float, Dict[str, float]]]:
        """
        Calculate refinement points for all 4 dimensions.

        Returns: {dimension: (total_points, {factor: points})}
        """
        return {
            "scientific_evidence": self._calc_scientific(enhanced_data.scientific_details),
            "market_opportunity": self._calc_market(enhanced_data.market_segment),
            "competitive_landscape": self._calc_competitive(
                enhanced_data.comparative_advantages,
                enhanced_data.side_effect_comparison,
            ),
            "development_feasibility": self._calc_feasibility(
                enhanced_data.side_effect_comparison,
                enhanced_data.scientific_details,
            ),
        }

    # ------------------------------------------------------------------
    # Dimension-specific refinement calculators
    # ------------------------------------------------------------------

    def _calc_scientific(
        self, sci: Optional[ScientificDetails]
    ) -> Tuple[float, Dict[str, float]]:
        """Scientific evidence refinement based on mechanism and publication data."""
        factors: Dict[str, float] = {}
        if not sci:
            return (0.0, factors)

        # Binding affinity
        if sci.binding_affinity_nm is not None:
            if sci.binding_affinity_nm < 10:
                factors["binding_affinity"] = 8
            elif sci.binding_affinity_nm < 100:
                factors["binding_affinity"] = 5
            elif sci.binding_affinity_nm < 1000:
                factors["binding_affinity"] = 2
            elif sci.binding_affinity_nm > 10000:
                factors["binding_affinity"] = -3

        # Pathway relevance
        pathway_count = len(sci.pathways) if sci.pathways else 0
        if pathway_count >= 4:
            factors["pathway_relevance"] = 5
        elif pathway_count >= 2:
            factors["pathway_relevance"] = 3

        # Publication quality (highest-cited paper)
        max_citations = 0
        if sci.key_publications:
            max_citations = max(
                (p.citation_count or 0) for p in sci.key_publications
            )
        if max_citations >= 500:
            factors["publication_quality"] = 6
        elif max_citations >= 100:
            factors["publication_quality"] = 3

        # Mechanistic rationale
        if sci.mechanistic_rationale:
            rationale_lower = sci.mechanistic_rationale.lower()
            mechanism_keywords = [
                "pathway", "modulates", "inhibits", "activates",
                "targets", "overlaps", "receptor", "signaling",
            ]
            if any(kw in rationale_lower for kw in mechanism_keywords):
                factors["mechanistic_rationale"] = 4

        # Biomarker availability
        biomarker_count = len(sci.biomarkers) if sci.biomarkers else 0
        if biomarker_count >= 3:
            factors["biomarker_availability"] = 4
        elif biomarker_count >= 1:
            factors["biomarker_availability"] = 2
        else:
            factors["biomarker_availability"] = -2

        total = sum(factors.values())
        return (total, factors)

    def _calc_market(
        self, segment: Optional[MarketSegment]
    ) -> Tuple[float, Dict[str, float]]:
        """Market opportunity refinement based on target segment analysis."""
        factors: Dict[str, float] = {}
        if not segment:
            return (0.0, factors)

        # Segment unmet need level
        unmet_map = {"very_high": 8, "high": 4, "moderate": 0, "low": -5}
        factors["segment_unmet_need"] = unmet_map.get(
            segment.unmet_need_level, 0
        )

        # Segment growth rate
        if segment.growth_rate_percent is not None:
            if segment.growth_rate_percent >= 20:
                factors["segment_growth"] = 7
            elif segment.growth_rate_percent >= 12:
                factors["segment_growth"] = 4
            elif segment.growth_rate_percent >= 8:
                factors["segment_growth"] = 2
            elif segment.growth_rate_percent < 5:
                factors["segment_growth"] = -3

        # Segment competitive intensity
        intensity_map = {"low": 7, "medium": 2, "high": -4}
        factors["segment_competition"] = intensity_map.get(
            segment.competitive_intensity, 0
        )

        total = sum(factors.values())
        return (total, factors)

    def _calc_competitive(
        self,
        advantages: Optional[List[ComparativeAdvantage]],
        side_fx: Optional[SideEffectComparison],
    ) -> Tuple[float, Dict[str, float]]:
        """Competitive landscape refinement based on advantages vs standard of care."""
        factors: Dict[str, float] = {}

        if advantages:
            # High-impact advantage count
            high_count = sum(1 for a in advantages if a.impact == "high")
            if high_count >= 3:
                factors["high_impact_advantages"] = 8
            elif high_count == 2:
                factors["high_impact_advantages"] = 5
            elif high_count == 1:
                factors["high_impact_advantages"] = 3

            # Advantage category breadth
            categories = set(a.category for a in advantages)
            if len(categories) >= 3:
                factors["advantage_breadth"] = 4
            elif len(categories) == 2:
                factors["advantage_breadth"] = 2

        if side_fx:
            score = side_fx.safety_advantage_score
            if score >= 0.5:
                factors["safety_advantage"] = 8
            elif score >= 0.2:
                factors["safety_advantage"] = 4
            elif score >= -0.2:
                factors["safety_advantage"] = 0
            elif score >= -0.5:
                factors["safety_advantage"] = -5
            else:
                factors["safety_advantage"] = -10

        total = sum(factors.values())
        return (total, factors)

    def _calc_feasibility(
        self,
        side_fx: Optional[SideEffectComparison],
        sci: Optional[ScientificDetails],
    ) -> Tuple[float, Dict[str, float]]:
        """Development feasibility refinement based on safety and trial readiness."""
        factors: Dict[str, float] = {}

        # Safety advantage for regulatory path
        if side_fx:
            score = side_fx.safety_advantage_score
            if score >= 0.3:
                factors["safety_for_development"] = 7
            elif score >= 0.0:
                factors["safety_for_development"] = 2
            else:
                factors["safety_for_development"] = -4

        if sci:
            # Biomarker-guided trial design
            biomarker_count = len(sci.biomarkers) if sci.biomarkers else 0
            if biomarker_count >= 3:
                factors["biomarker_trial_design"] = 7
            elif biomarker_count >= 1:
                factors["biomarker_trial_design"] = 3

            # Preclinical model availability
            model_count = len(sci.preclinical_models) if sci.preclinical_models else 0
            if model_count >= 3:
                factors["preclinical_models"] = 6
            elif model_count >= 1:
                factors["preclinical_models"] = 3
            else:
                factors["preclinical_models"] = -2

            # Selectivity profile
            if sci.selectivity_profile:
                sel_lower = sci.selectivity_profile.lower()
                if "non-selective" in sel_lower or "nonselective" in sel_lower:
                    factors["selectivity"] = -2
                elif "selective" in sel_lower:
                    factors["selectivity"] = 3

        total = sum(factors.values())
        return (total, factors)
