"""
Composite Scorer - Multi-dimensional scoring system for drug repurposing opportunities.
Combines Scientific Evidence (40%), Market Opportunity (25%), Competitive Landscape (20%),
and Development Feasibility (15%) into a single actionable score.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import numpy as np

from app.schemas.repurpose_api import EvidenceItem, IndicationResult
from app.schemas.repurpose_scoring import (
    ConfidenceLevel, InsightCategory, SubScore, Insight,
    CompositeScore, EnhancedIndicationResult, MarketData, CompetitorData, PatentData
)
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("scoring.composite")


class CompositeScorer:
    """
    Multi-dimensional scorer for drug repurposing opportunities.
    Combines scientific, market, competitive, and feasibility assessments.
    """

    # Dimension weights (must sum to 1.0)
    WEIGHTS = {
        "scientific_evidence": 0.40,
        "market_opportunity": 0.25,
        "competitive_landscape": 0.20,
        "development_feasibility": 0.15
    }

    # Source base scores for scientific evidence
    SOURCE_BASE_SCORES = {
        "clinical_trials": 70,
        "literature": 60,
        "bioactivity": 55,
        "patent": 50,
        "internal": 50,
        "openfda": 65,
        "opentargets": 65,
        "semantic_scholar": 60,
        "dailymed": 55,
        "kegg": 50,
        "uniprot": 50,
        "orange_book": 55,
        "rxnorm": 50,
        "who": 55,
        "drugbank": 60
    }

    def __init__(self):
        self.logger = get_logger("scoring.composite")

    def score_indication(
        self,
        indication: str,
        evidence_items: List[EvidenceItem],
        market_data: Optional[MarketData] = None,
        competitor_data: Optional[CompetitorData] = None,
        patent_data: Optional[PatentData] = None
    ) -> CompositeScore:
        """
        Calculate composite score for a single indication.

        Args:
            indication: Disease/indication name
            evidence_items: List of evidence items for this indication
            market_data: Optional market data
            competitor_data: Optional competitor data
            patent_data: Optional patent/regulatory data

        Returns:
            CompositeScore with all dimensions
        """
        # Calculate sub-scores
        scientific = self._calculate_scientific_score(evidence_items)
        market = self._calculate_market_score(indication, market_data)
        competitive = self._calculate_competitive_score(indication, competitor_data, evidence_items)
        feasibility = self._calculate_feasibility_score(indication, evidence_items, patent_data)

        # Calculate weighted overall score
        overall = (
            scientific.weighted_score +
            market.weighted_score +
            competitive.weighted_score +
            feasibility.weighted_score
        )

        # Determine confidence level
        confidence_level = ConfidenceLevel.from_score(overall)

        # Calculate data completeness
        data_completeness = np.mean([
            scientific.data_completeness,
            market.data_completeness,
            competitive.data_completeness,
            feasibility.data_completeness
        ])

        # Generate insights
        strengths, risks, recommendations = self._generate_insights(
            scientific, market, competitive, feasibility, evidence_items, indication
        )

        return CompositeScore(
            indication=indication,
            overall_score=round(overall, 1),
            confidence_level=confidence_level,
            scientific_evidence=scientific,
            market_opportunity=market,
            competitive_landscape=competitive,
            development_feasibility=feasibility,
            key_strengths=strengths,
            key_risks=risks,
            recommended_next_steps=recommendations,
            evidence_count=len(evidence_items),
            data_completeness=round(data_completeness, 2),
            scored_at=datetime.now().isoformat()
        )

    def rank_indications(
        self,
        evidence_list: List[EvidenceItem],
        market_data_map: Optional[Dict[str, MarketData]] = None,
        competitor_data_map: Optional[Dict[str, CompetitorData]] = None
    ) -> List[EnhancedIndicationResult]:
        """
        Group evidence by indication and rank by composite score.

        Args:
            evidence_list: List of all evidence items
            market_data_map: Optional dict mapping indication to market data
            competitor_data_map: Optional dict mapping indication to competitor data

        Returns:
            Ranked list of enhanced indication results
        """
        self.logger.info(f"Ranking {len(evidence_list)} evidence items with composite scoring...")

        market_data_map = market_data_map or {}
        competitor_data_map = competitor_data_map or {}

        # Group evidence by indication (skip items without proper indication)
        indication_map = defaultdict(list)
        skipped_count = 0
        for evidence in evidence_list:
            indication = evidence.indication
            # Skip evidence without a valid indication
            if not indication or indication.lower() == "unknown indication":
                skipped_count += 1
                continue
            indication_map[indication].append(evidence)

        if skipped_count > 0:
            self.logger.info(f"Skipped {skipped_count} evidence items without valid indication")

        # Score each indication
        results = []
        for indication, items in indication_map.items():
            try:
                composite = self.score_indication(
                    indication=indication,
                    evidence_items=items,
                    market_data=market_data_map.get(indication.lower()),
                    competitor_data=competitor_data_map.get(indication.lower())
                )

                results.append(EnhancedIndicationResult(
                    indication=indication,
                    confidence_score=composite.overall_score,
                    composite_score=composite,
                    evidence_count=len(items),
                    supporting_sources=list(set(e.source for e in items))
                ))
            except Exception as e:
                self.logger.warning(f"Failed to score indication {indication}: {e}")
                continue

        # Sort by overall score
        results.sort(key=lambda x: x.confidence_score, reverse=True)

        self.logger.info(f"Scored {len(results)} indications")
        if results:
            self.logger.info(f"Top indication: {results[0].indication} with score {results[0].confidence_score}")

        return results

    def _calculate_scientific_score(self, evidence_items: List[EvidenceItem]) -> SubScore:
        """Calculate scientific evidence score."""
        if not evidence_items:
            return SubScore(
                dimension="scientific_evidence",
                score=0,
                weight=self.WEIGHTS["scientific_evidence"],
                weighted_score=0,
                confidence=ConfidenceLevel.VERY_LOW,
                factors={"no_evidence": 0},
                data_completeness=0,
                notes=["No evidence found"]
            )

        factors = {}
        notes = []

        # Evidence quantity (max 25 points)
        count = len(evidence_items)
        if count >= 20:
            factors["evidence_quantity"] = 25
            notes.append(f"Strong evidence base ({count} items)")
        elif count >= 10:
            factors["evidence_quantity"] = 20
            notes.append(f"Good evidence base ({count} items)")
        elif count >= 5:
            factors["evidence_quantity"] = 15
            notes.append(f"Moderate evidence base ({count} items)")
        else:
            factors["evidence_quantity"] = count * 3
            notes.append(f"Limited evidence ({count} items)")

        # Source diversity (max 20 points)
        sources = set(e.source for e in evidence_items)
        diversity_score = min(len(sources) * 4, 20)
        factors["source_diversity"] = diversity_score
        notes.append(f"Evidence from {len(sources)} sources")

        # Clinical trial evidence (max 25 points)
        clinical_items = [e for e in evidence_items if e.source == "clinical_trials"]
        if clinical_items:
            phases = [e.metadata.get("phase", "") for e in clinical_items]
            if any("4" in str(p) or "IV" in str(p).upper() for p in phases):
                factors["clinical_phase"] = 25
                notes.append("Phase 4 clinical evidence")
            elif any("3" in str(p) or "III" in str(p).upper() for p in phases):
                factors["clinical_phase"] = 20
                notes.append("Phase 3 clinical evidence")
            elif any("2" in str(p) or "II" in str(p).upper() for p in phases):
                factors["clinical_phase"] = 15
                notes.append("Phase 2 clinical evidence")
            else:
                factors["clinical_phase"] = 10
                notes.append("Early phase clinical evidence")
        else:
            factors["clinical_phase"] = 0

        # Evidence quality (max 15 points) - average relevance score
        relevance_scores = [e.relevance_score for e in evidence_items if e.relevance_score]
        if relevance_scores:
            avg_relevance = np.mean(relevance_scores)
            factors["evidence_quality"] = avg_relevance * 15
        else:
            factors["evidence_quality"] = 7.5  # Default mid-range

        # Mechanistic support (max 15 points) - bioactivity/target data
        mechanistic_sources = ["bioactivity", "opentargets", "kegg", "uniprot"]
        mechanistic_items = [e for e in evidence_items if e.source in mechanistic_sources]
        if len(mechanistic_items) >= 5:
            factors["mechanistic_support"] = 15
        elif len(mechanistic_items) >= 2:
            factors["mechanistic_support"] = 10
        elif len(mechanistic_items) >= 1:
            factors["mechanistic_support"] = 5
        else:
            factors["mechanistic_support"] = 0

        # Calculate total score
        total_score = sum(factors.values())
        total_score = min(total_score, 100)

        return SubScore(
            dimension="scientific_evidence",
            score=round(total_score, 1),
            weight=self.WEIGHTS["scientific_evidence"],
            weighted_score=round(total_score * self.WEIGHTS["scientific_evidence"], 1),
            confidence=ConfidenceLevel.from_score(total_score),
            factors={k: round(v, 1) for k, v in factors.items()},
            data_completeness=min(count / 10, 1.0),
            notes=notes
        )

    def _calculate_market_score(
        self,
        indication: str,
        market_data: Optional[MarketData]
    ) -> SubScore:
        """Calculate market opportunity score."""
        factors = {}
        notes = []
        data_completeness = 0.3  # Default low if no data

        if market_data:
            data_completeness = 0.9

            # Market size (max 30 points)
            if market_data.market_size_usd_billions:
                size = market_data.market_size_usd_billions
                # Store raw value for frontend display
                factors["market_size_raw_billions"] = size
                if size >= 50:
                    factors["market_size"] = 30
                    notes.append(f"Mega market (${size:.0f}B)")
                elif size >= 10:
                    factors["market_size"] = 25
                    notes.append(f"Large market (${size:.0f}B)")
                elif size >= 1:
                    factors["market_size"] = 20
                    notes.append(f"Medium market (${size:.0f}B)")
                else:
                    factors["market_size"] = 10
                    notes.append(f"Small market (${size:.1f}B)")
            else:
                factors["market_size"] = 15  # Default moderate
                factors["market_size_raw_billions"] = None

            # CAGR (max 20 points)
            if market_data.cagr_percent:
                cagr = market_data.cagr_percent
                # Store raw value for frontend display
                factors["cagr_percent_raw"] = cagr
                if cagr >= 10:
                    factors["growth_rate"] = 20
                    notes.append(f"High growth ({cagr:.1f}% CAGR)")
                elif cagr >= 7:
                    factors["growth_rate"] = 15
                elif cagr >= 5:
                    factors["growth_rate"] = 10
                else:
                    factors["growth_rate"] = 5
            else:
                factors["growth_rate"] = 10
                factors["cagr_percent_raw"] = None

            # Unmet need (max 30 points)
            if market_data.unmet_need_score:
                # Store raw value for frontend display
                factors["unmet_need_raw"] = market_data.unmet_need_score
                factors["unmet_need"] = (market_data.unmet_need_score / 100) * 30
                if market_data.unmet_need_score >= 70:
                    notes.append("High unmet medical need")
            else:
                factors["unmet_need"] = 15
                factors["unmet_need_raw"] = None

            # Patient population (store raw value)
            if market_data.patient_population_millions:
                factors["patient_population_millions"] = market_data.patient_population_millions
            else:
                factors["patient_population_millions"] = None

            # Pricing potential (max 20 points)
            if market_data.pricing_potential:
                factors["pricing_potential_raw"] = market_data.pricing_potential
                if market_data.pricing_potential == "premium":
                    factors["pricing_potential"] = 20
                elif market_data.pricing_potential == "standard":
                    factors["pricing_potential"] = 15
                else:
                    factors["pricing_potential"] = 10
            else:
                factors["pricing_potential"] = 12
                factors["pricing_potential_raw"] = None

        else:
            # Default scores when no market data - use indication-based estimates
            estimated_data = self._estimate_market_data(indication)
            factors["market_size"] = 15
            factors["growth_rate"] = 10
            factors["unmet_need"] = 15
            factors["pricing_potential"] = 10
            # Store estimated raw values
            factors["market_size_raw_billions"] = estimated_data.get("market_size_billions")
            factors["cagr_percent_raw"] = estimated_data.get("cagr_percent")
            factors["unmet_need_raw"] = estimated_data.get("unmet_need")
            factors["patient_population_millions"] = estimated_data.get("patient_population_millions")
            factors["pricing_potential_raw"] = estimated_data.get("pricing_potential")
            notes.append("Using estimated market data")

        # Calculate total score (exclude raw values from sum)
        score_factors = ["market_size", "growth_rate", "unmet_need", "pricing_potential"]
        total_score = sum(factors.get(k, 0) for k in score_factors if factors.get(k) is not None)
        total_score = min(total_score, 100)

        # Round factor scores but preserve raw values
        rounded_factors = {}
        for k, v in factors.items():
            if v is None:
                rounded_factors[k] = None
            elif "_raw" in k or "_millions" in k or "_billions" in k:
                rounded_factors[k] = v  # Keep raw values as-is
            else:
                rounded_factors[k] = round(v, 1)

        return SubScore(
            dimension="market_opportunity",
            score=round(total_score, 1),
            weight=self.WEIGHTS["market_opportunity"],
            weighted_score=round(total_score * self.WEIGHTS["market_opportunity"], 1),
            confidence=ConfidenceLevel.from_score(total_score),
            factors=rounded_factors,
            data_completeness=data_completeness,
            notes=notes
        )

    # Medical abbreviation mappings to canonical indication names
    ABBREVIATION_MAP = {
        # Diabetes
        "t2dm": "type 2 diabetes",
        "t1dm": "type 1 diabetes",
        "dm2": "type 2 diabetes",
        "dm1": "type 1 diabetes",
        "niddm": "type 2 diabetes",
        "iddm": "type 1 diabetes",
        # Cancer
        "nsclc": "lung cancer",
        "sclc": "lung cancer",
        "hcc": "liver cancer",
        "crc": "colorectal cancer",
        "rcc": "kidney cancer",
        "aml": "leukemia",
        "cml": "leukemia",
        "all": "leukemia",
        "cll": "leukemia",
        "dlbcl": "lymphoma",
        "nhl": "lymphoma",
        "hl": "lymphoma",
        "gist": "gastrointestinal cancer",
        "gbm": "brain cancer",
        # Autoimmune/Inflammatory
        "ra": "rheumatoid arthritis",
        "sle": "lupus",
        "ibd": "inflammatory bowel disease",
        "uc": "ulcerative colitis",
        "cd": "crohn's disease",
        "as": "ankylosing spondylitis",
        "psa": "psoriatic arthritis",
        "oa": "osteoarthritis",
        # Neurological
        "ms": "multiple sclerosis",
        "als": "amyotrophic lateral sclerosis",
        "ad": "alzheimer",
        "pd": "parkinson",
        "hd": "huntington's disease",
        # Cardiovascular
        "chf": "heart failure",
        "hf": "heart failure",
        "af": "atrial fibrillation",
        "afib": "atrial fibrillation",
        "cad": "coronary artery disease",
        "mi": "myocardial infarction",
        "dvt": "deep vein thrombosis",
        "pe": "pulmonary embolism",
        "pah": "pulmonary hypertension",
        # Respiratory
        "copd": "copd",
        "ipf": "pulmonary fibrosis",
        "cf": "cystic fibrosis",
        "ards": "acute respiratory distress",
        # Metabolic/Liver
        "nafld": "fatty liver",
        "nash": "fatty liver",
        "ckd": "chronic kidney disease",
        "esrd": "chronic kidney disease",
        # Infectious
        "hiv": "hiv",
        "aids": "hiv",
        "hcv": "hepatitis c",
        "hbv": "hepatitis b",
        "tb": "tuberculosis",
        "covid": "covid-19",
        "sars": "covid-19",
        # Other
        "mdd": "depression",
        "gad": "anxiety",
        "ptsd": "post-traumatic stress",
        "adhd": "attention deficit disorder",
        "ocd": "obsessive compulsive disorder",
    }

    # Comprehensive market estimates for 50+ indications (based on GBD 2023, WHO, market reports)
    MARKET_ESTIMATES = {
        # Metabolic/Endocrine
        "diabetes": {"market_size_billions": 65.0, "cagr_percent": 8.5, "unmet_need": 60, "patient_population_millions": 537, "pricing_potential": "standard"},
        "type 2 diabetes": {"market_size_billions": 55.0, "cagr_percent": 8.0, "unmet_need": 55, "patient_population_millions": 462, "pricing_potential": "standard"},
        "type 1 diabetes": {"market_size_billions": 10.0, "cagr_percent": 7.0, "unmet_need": 65, "patient_population_millions": 9, "pricing_potential": "premium"},
        "obesity": {"market_size_billions": 12.0, "cagr_percent": 20.0, "unmet_need": 85, "patient_population_millions": 650, "pricing_potential": "premium"},
        "hyperlipidemia": {"market_size_billions": 18.0, "cagr_percent": 4.0, "unmet_need": 40, "patient_population_millions": 400, "pricing_potential": "generic"},
        "gout": {"market_size_billions": 3.5, "cagr_percent": 8.0, "unmet_need": 55, "patient_population_millions": 41, "pricing_potential": "standard"},
        "thyroid disorders": {"market_size_billions": 4.0, "cagr_percent": 5.0, "unmet_need": 35, "patient_population_millions": 200, "pricing_potential": "generic"},
        "fatty liver": {"market_size_billions": 8.0, "cagr_percent": 25.0, "unmet_need": 90, "patient_population_millions": 115, "pricing_potential": "premium"},

        # Oncology
        "cancer": {"market_size_billions": 185.0, "cagr_percent": 12.0, "unmet_need": 75, "patient_population_millions": 19, "pricing_potential": "premium"},
        "breast cancer": {"market_size_billions": 22.0, "cagr_percent": 10.0, "unmet_need": 65, "patient_population_millions": 2.3, "pricing_potential": "premium"},
        "lung cancer": {"market_size_billions": 25.0, "cagr_percent": 11.0, "unmet_need": 80, "patient_population_millions": 2.2, "pricing_potential": "premium"},
        "colorectal cancer": {"market_size_billions": 15.0, "cagr_percent": 9.0, "unmet_need": 60, "patient_population_millions": 1.9, "pricing_potential": "premium"},
        "prostate cancer": {"market_size_billions": 12.0, "cagr_percent": 8.0, "unmet_need": 50, "patient_population_millions": 1.4, "pricing_potential": "premium"},
        "liver cancer": {"market_size_billions": 6.0, "cagr_percent": 12.0, "unmet_need": 85, "patient_population_millions": 0.9, "pricing_potential": "premium"},
        "pancreatic cancer": {"market_size_billions": 4.0, "cagr_percent": 15.0, "unmet_need": 95, "patient_population_millions": 0.5, "pricing_potential": "premium"},
        "kidney cancer": {"market_size_billions": 5.0, "cagr_percent": 8.0, "unmet_need": 60, "patient_population_millions": 0.4, "pricing_potential": "premium"},
        "leukemia": {"market_size_billions": 15.0, "cagr_percent": 10.0, "unmet_need": 70, "patient_population_millions": 0.5, "pricing_potential": "premium"},
        "lymphoma": {"market_size_billions": 12.0, "cagr_percent": 9.0, "unmet_need": 65, "patient_population_millions": 0.6, "pricing_potential": "premium"},
        "melanoma": {"market_size_billions": 8.0, "cagr_percent": 12.0, "unmet_need": 55, "patient_population_millions": 0.3, "pricing_potential": "premium"},
        "brain cancer": {"market_size_billions": 3.0, "cagr_percent": 10.0, "unmet_need": 95, "patient_population_millions": 0.3, "pricing_potential": "premium"},
        "ovarian cancer": {"market_size_billions": 4.0, "cagr_percent": 11.0, "unmet_need": 80, "patient_population_millions": 0.3, "pricing_potential": "premium"},
        "gastric cancer": {"market_size_billions": 3.5, "cagr_percent": 8.0, "unmet_need": 75, "patient_population_millions": 1.1, "pricing_potential": "premium"},
        "bladder cancer": {"market_size_billions": 5.0, "cagr_percent": 9.0, "unmet_need": 60, "patient_population_millions": 0.6, "pricing_potential": "premium"},
        "gastrointestinal cancer": {"market_size_billions": 8.0, "cagr_percent": 10.0, "unmet_need": 70, "patient_population_millions": 1.5, "pricing_potential": "premium"},

        # Neurology
        "alzheimer": {"market_size_billions": 8.0, "cagr_percent": 15.0, "unmet_need": 95, "patient_population_millions": 55, "pricing_potential": "premium"},
        "parkinson": {"market_size_billions": 5.5, "cagr_percent": 7.0, "unmet_need": 70, "patient_population_millions": 10, "pricing_potential": "premium"},
        "multiple sclerosis": {"market_size_billions": 28.0, "cagr_percent": 3.0, "unmet_need": 65, "patient_population_millions": 2.8, "pricing_potential": "premium"},
        "epilepsy": {"market_size_billions": 8.0, "cagr_percent": 5.0, "unmet_need": 55, "patient_population_millions": 50, "pricing_potential": "standard"},
        "migraine": {"market_size_billions": 6.0, "cagr_percent": 15.0, "unmet_need": 60, "patient_population_millions": 1000, "pricing_potential": "premium"},
        "amyotrophic lateral sclerosis": {"market_size_billions": 1.5, "cagr_percent": 12.0, "unmet_need": 98, "patient_population_millions": 0.3, "pricing_potential": "premium"},
        "huntington's disease": {"market_size_billions": 0.8, "cagr_percent": 10.0, "unmet_need": 95, "patient_population_millions": 0.04, "pricing_potential": "premium"},
        "neuropathy": {"market_size_billions": 4.0, "cagr_percent": 6.0, "unmet_need": 65, "patient_population_millions": 30, "pricing_potential": "standard"},
        "stroke": {"market_size_billions": 8.0, "cagr_percent": 7.0, "unmet_need": 70, "patient_population_millions": 101, "pricing_potential": "standard"},
        "dementia": {"market_size_billions": 12.0, "cagr_percent": 10.0, "unmet_need": 90, "patient_population_millions": 55, "pricing_potential": "premium"},

        # Psychiatry
        "depression": {"market_size_billions": 15.0, "cagr_percent": 6.0, "unmet_need": 60, "patient_population_millions": 280, "pricing_potential": "standard"},
        "anxiety": {"market_size_billions": 8.0, "cagr_percent": 5.5, "unmet_need": 55, "patient_population_millions": 275, "pricing_potential": "standard"},
        "schizophrenia": {"market_size_billions": 10.0, "cagr_percent": 4.0, "unmet_need": 70, "patient_population_millions": 24, "pricing_potential": "premium"},
        "bipolar disorder": {"market_size_billions": 6.0, "cagr_percent": 5.0, "unmet_need": 65, "patient_population_millions": 45, "pricing_potential": "standard"},
        "post-traumatic stress": {"market_size_billions": 2.5, "cagr_percent": 8.0, "unmet_need": 75, "patient_population_millions": 77, "pricing_potential": "standard"},
        "attention deficit disorder": {"market_size_billions": 18.0, "cagr_percent": 7.0, "unmet_need": 45, "patient_population_millions": 85, "pricing_potential": "standard"},
        "obsessive compulsive disorder": {"market_size_billions": 1.5, "cagr_percent": 5.0, "unmet_need": 60, "patient_population_millions": 28, "pricing_potential": "standard"},

        # Autoimmune/Inflammatory
        "inflammation": {"market_size_billions": 45.0, "cagr_percent": 7.0, "unmet_need": 50, "patient_population_millions": 500, "pricing_potential": "standard"},
        "rheumatoid arthritis": {"market_size_billions": 28.0, "cagr_percent": 5.0, "unmet_need": 55, "patient_population_millions": 18, "pricing_potential": "premium"},
        "lupus": {"market_size_billions": 3.0, "cagr_percent": 10.0, "unmet_need": 80, "patient_population_millions": 5, "pricing_potential": "premium"},
        "crohn's disease": {"market_size_billions": 8.0, "cagr_percent": 6.0, "unmet_need": 60, "patient_population_millions": 3.5, "pricing_potential": "premium"},
        "ulcerative colitis": {"market_size_billions": 7.0, "cagr_percent": 6.5, "unmet_need": 55, "patient_population_millions": 5, "pricing_potential": "premium"},
        "inflammatory bowel disease": {"market_size_billions": 15.0, "cagr_percent": 6.0, "unmet_need": 58, "patient_population_millions": 8.5, "pricing_potential": "premium"},
        "psoriasis": {"market_size_billions": 18.0, "cagr_percent": 8.0, "unmet_need": 50, "patient_population_millions": 125, "pricing_potential": "premium"},
        "eczema": {"market_size_billions": 10.0, "cagr_percent": 12.0, "unmet_need": 55, "patient_population_millions": 230, "pricing_potential": "standard"},
        "ankylosing spondylitis": {"market_size_billions": 5.0, "cagr_percent": 7.0, "unmet_need": 60, "patient_population_millions": 3.5, "pricing_potential": "premium"},
        "psoriatic arthritis": {"market_size_billions": 6.0, "cagr_percent": 8.0, "unmet_need": 55, "patient_population_millions": 2, "pricing_potential": "premium"},
        "osteoarthritis": {"market_size_billions": 8.0, "cagr_percent": 5.0, "unmet_need": 60, "patient_population_millions": 528, "pricing_potential": "standard"},

        # Cardiovascular
        "cardiovascular": {"market_size_billions": 70.0, "cagr_percent": 6.0, "unmet_need": 50, "patient_population_millions": 523, "pricing_potential": "standard"},
        "hypertension": {"market_size_billions": 30.0, "cagr_percent": 5.0, "unmet_need": 40, "patient_population_millions": 1280, "pricing_potential": "generic"},
        "heart failure": {"market_size_billions": 12.0, "cagr_percent": 8.0, "unmet_need": 70, "patient_population_millions": 64, "pricing_potential": "premium"},
        "atrial fibrillation": {"market_size_billions": 16.0, "cagr_percent": 9.0, "unmet_need": 55, "patient_population_millions": 37, "pricing_potential": "premium"},
        "coronary artery disease": {"market_size_billions": 20.0, "cagr_percent": 5.0, "unmet_need": 45, "patient_population_millions": 200, "pricing_potential": "standard"},
        "myocardial infarction": {"market_size_billions": 8.0, "cagr_percent": 4.0, "unmet_need": 50, "patient_population_millions": 32, "pricing_potential": "standard"},
        "deep vein thrombosis": {"market_size_billions": 4.0, "cagr_percent": 6.0, "unmet_need": 40, "patient_population_millions": 10, "pricing_potential": "standard"},
        "pulmonary embolism": {"market_size_billions": 3.0, "cagr_percent": 7.0, "unmet_need": 50, "patient_population_millions": 0.9, "pricing_potential": "premium"},

        # Respiratory
        "asthma": {"market_size_billions": 25.0, "cagr_percent": 6.5, "unmet_need": 45, "patient_population_millions": 262, "pricing_potential": "standard"},
        "copd": {"market_size_billions": 18.0, "cagr_percent": 5.0, "unmet_need": 60, "patient_population_millions": 384, "pricing_potential": "standard"},
        "pulmonary fibrosis": {"market_size_billions": 4.0, "cagr_percent": 15.0, "unmet_need": 90, "patient_population_millions": 5, "pricing_potential": "premium"},
        "pulmonary hypertension": {"market_size_billions": 8.0, "cagr_percent": 10.0, "unmet_need": 75, "patient_population_millions": 1, "pricing_potential": "premium"},
        "cystic fibrosis": {"market_size_billions": 6.0, "cagr_percent": 8.0, "unmet_need": 65, "patient_population_millions": 0.1, "pricing_potential": "premium"},
        "acute respiratory distress": {"market_size_billions": 2.0, "cagr_percent": 12.0, "unmet_need": 85, "patient_population_millions": 3, "pricing_potential": "premium"},

        # Infectious
        "hiv": {"market_size_billions": 30.0, "cagr_percent": 4.0, "unmet_need": 40, "patient_population_millions": 38, "pricing_potential": "premium"},
        "hepatitis": {"market_size_billions": 12.0, "cagr_percent": -2.0, "unmet_need": 50, "patient_population_millions": 296, "pricing_potential": "premium"},
        "hepatitis c": {"market_size_billions": 8.0, "cagr_percent": -5.0, "unmet_need": 40, "patient_population_millions": 58, "pricing_potential": "premium"},
        "hepatitis b": {"market_size_billions": 4.0, "cagr_percent": 5.0, "unmet_need": 70, "patient_population_millions": 296, "pricing_potential": "premium"},
        "tuberculosis": {"market_size_billions": 1.5, "cagr_percent": 4.0, "unmet_need": 65, "patient_population_millions": 10, "pricing_potential": "standard"},
        "malaria": {"market_size_billions": 1.0, "cagr_percent": 3.0, "unmet_need": 70, "patient_population_millions": 247, "pricing_potential": "generic"},
        "covid-19": {"market_size_billions": 50.0, "cagr_percent": -10.0, "unmet_need": 30, "patient_population_millions": 700, "pricing_potential": "standard"},
        "influenza": {"market_size_billions": 6.0, "cagr_percent": 5.0, "unmet_need": 45, "patient_population_millions": 1000, "pricing_potential": "standard"},
        "pneumonia": {"market_size_billions": 3.0, "cagr_percent": 4.0, "unmet_need": 50, "patient_population_millions": 450, "pricing_potential": "standard"},

        # Renal
        "chronic kidney disease": {"market_size_billions": 15.0, "cagr_percent": 8.0, "unmet_need": 75, "patient_population_millions": 850, "pricing_potential": "premium"},

        # Pain/Musculoskeletal
        "pain": {"market_size_billions": 35.0, "cagr_percent": 4.0, "unmet_need": 65, "patient_population_millions": 1500, "pricing_potential": "standard"},
        "chronic pain": {"market_size_billions": 25.0, "cagr_percent": 5.0, "unmet_need": 70, "patient_population_millions": 1100, "pricing_potential": "standard"},
        "osteoporosis": {"market_size_billions": 12.0, "cagr_percent": 4.0, "unmet_need": 50, "patient_population_millions": 200, "pricing_potential": "standard"},

        # Women's Health
        "endometriosis": {"market_size_billions": 3.0, "cagr_percent": 10.0, "unmet_need": 80, "patient_population_millions": 190, "pricing_potential": "premium"},

        # Eye
        "macular degeneration": {"market_size_billions": 10.0, "cagr_percent": 7.0, "unmet_need": 60, "patient_population_millions": 196, "pricing_potential": "premium"},
        "glaucoma": {"market_size_billions": 6.0, "cagr_percent": 5.0, "unmet_need": 45, "patient_population_millions": 80, "pricing_potential": "standard"},
        "diabetic retinopathy": {"market_size_billions": 4.0, "cagr_percent": 8.0, "unmet_need": 55, "patient_population_millions": 103, "pricing_potential": "premium"},
    }

    # Default estimates for unknown indications
    DEFAULT_MARKET_ESTIMATES = {
        "market_size_billions": 5.0,
        "cagr_percent": 6.0,
        "unmet_need": 50,
        "patient_population_millions": 10,
        "pricing_potential": "standard"
    }

    def _estimate_market_data(self, indication: str) -> Dict[str, Any]:
        """
        Estimate market data for indications when real data unavailable.
        Uses abbreviation mapping and fuzzy matching for better coverage.
        """
        indication_lower = indication.lower().strip()

        # Step 1: Check for abbreviation mapping
        for abbrev, canonical in self.ABBREVIATION_MAP.items():
            if abbrev in indication_lower or indication_lower == abbrev:
                if canonical in self.MARKET_ESTIMATES:
                    return self.MARKET_ESTIMATES[canonical]

        # Step 2: Try exact/substring match
        for key, data in self.MARKET_ESTIMATES.items():
            if key in indication_lower:
                return data

        # Step 3: Try reverse match (indication in key)
        for key, data in self.MARKET_ESTIMATES.items():
            if indication_lower in key:
                return data

        # Step 4: Try fuzzy matching with common variations
        # Handle roman numerals
        indication_normalized = indication_lower.replace(" ii ", " 2 ").replace(" iii ", " 3 ").replace(" iv ", " 4 ")
        indication_normalized = indication_normalized.replace("type ii", "type 2").replace("type iii", "type 3")
        indication_normalized = indication_normalized.replace("phase ii", "phase 2").replace("phase iii", "phase 3")

        for key, data in self.MARKET_ESTIMATES.items():
            if key in indication_normalized:
                return data

        # Step 5: Try word-based partial matching for compound conditions
        indication_words = set(indication_lower.split())
        best_match = None
        best_score = 0

        for key, data in self.MARKET_ESTIMATES.items():
            key_words = set(key.split())
            # Calculate Jaccard-like similarity
            common_words = indication_words & key_words
            if common_words:
                score = len(common_words) / max(len(indication_words), len(key_words))
                if score > best_score and score >= 0.5:  # At least 50% word overlap
                    best_score = score
                    best_match = data

        if best_match:
            return best_match

        # Step 6: Try category-based fallback for partial matches
        category_keywords = {
            "cancer": "cancer",
            "tumor": "cancer",
            "carcinoma": "cancer",
            "sarcoma": "cancer",
            "lymphoma": "lymphoma",
            "leukemia": "leukemia",
            "diabetes": "diabetes",
            "diabetic": "diabetes",
            "heart": "cardiovascular",
            "cardiac": "cardiovascular",
            "liver": "hepatitis",
            "hepatic": "hepatitis",
            "kidney": "chronic kidney disease",
            "renal": "chronic kidney disease",
            "lung": "copd",
            "pulmonary": "copd",
            "brain": "dementia",
            "neuro": "neuropathy",
            "arthritis": "rheumatoid arthritis",
            "colitis": "ulcerative colitis",
        }

        for keyword, mapped_indication in category_keywords.items():
            if keyword in indication_lower:
                if mapped_indication in self.MARKET_ESTIMATES:
                    return self.MARKET_ESTIMATES[mapped_indication]

        # Return default estimates for truly unknown indications
        return self.DEFAULT_MARKET_ESTIMATES

    def _calculate_competitive_score(
        self,
        indication: str,
        competitor_data: Optional[CompetitorData],
        evidence_items: List[EvidenceItem]
    ) -> SubScore:
        """Calculate competitive landscape score (higher = less competition = better)."""
        factors = {}
        notes = []
        score = 80  # Start high, deduct for competition

        data_completeness = 0.3 if not competitor_data else 0.9

        if competitor_data:
            # Deduct for number of competitors (up to -40)
            if competitor_data.total_competitors >= 10:
                score -= 40
                factors["competitor_count"] = -40
                notes.append(f"Crowded space ({competitor_data.total_competitors}+ competitors)")
            elif competitor_data.total_competitors >= 5:
                score -= 25
                factors["competitor_count"] = -25
                notes.append(f"Competitive space ({competitor_data.total_competitors} competitors)")
            elif competitor_data.total_competitors >= 2:
                score -= 15
                factors["competitor_count"] = -15
            else:
                factors["competitor_count"] = 0
                notes.append("Limited competition")

            # Deduct for late-stage competition (up to -30)
            if competitor_data.approved_drugs_count > 0:
                score -= 30
                factors["approved_competition"] = -30
                notes.append("Approved competitors exist")
            elif competitor_data.phase3_trials_count >= 3:
                score -= 25
                factors["approved_competition"] = -25
            elif competitor_data.phase3_trials_count >= 1:
                score -= 15
                factors["approved_competition"] = -15
            else:
                factors["approved_competition"] = 0

            # Deduct for big pharma (up to -20)
            if competitor_data.big_pharma_involved:
                score -= 20
                factors["big_pharma"] = -20
                notes.append("Big pharma competitors")
            else:
                factors["big_pharma"] = 0
        else:
            # Infer competition from clinical trial evidence
            clinical_items = [e for e in evidence_items if e.source == "clinical_trials"]
            if len(clinical_items) > 10:
                score -= 20
                factors["inferred_competition"] = -20
                notes.append("Active clinical interest suggests competition")
            else:
                factors["inferred_competition"] = 0

        score = max(score, 10)  # Minimum 10

        # Get competitor list for display
        competitors = []
        if competitor_data and competitor_data.competitor_list:
            competitors = competitor_data.competitor_list

        return SubScore(
            dimension="competitive_landscape",
            score=round(score, 1),
            weight=self.WEIGHTS["competitive_landscape"],
            weighted_score=round(score * self.WEIGHTS["competitive_landscape"], 1),
            confidence=ConfidenceLevel.from_score(score),
            factors={k: round(v, 1) for k, v in factors.items()},
            data_completeness=data_completeness,
            notes=notes if notes else ["Competitive landscape appears favorable"],
            competitors=competitors
        )

    def _calculate_feasibility_score(
        self,
        indication: str,
        evidence_items: List[EvidenceItem],
        patent_data: Optional[PatentData]
    ) -> SubScore:
        """Calculate development feasibility score."""
        factors = {}
        notes = []
        score = 50  # Start at mid-range

        # Check for safety data from OpenFDA
        fda_items = [e for e in evidence_items if e.source == "openfda"]
        if fda_items:
            score += 20
            factors["safety_data"] = 20
            notes.append("Established safety profile (FDA data)")
        else:
            factors["safety_data"] = 0

        # Check for approved indications (505(b)(2) pathway potential)
        label_items = [e for e in evidence_items if e.source == "dailymed" or
                       (e.source == "openfda" and e.metadata.get("data_type") == "label")]
        if label_items:
            score += 15
            factors["regulatory_pathway"] = 15
            notes.append("Existing labeling supports 505(b)(2) pathway")
        else:
            factors["regulatory_pathway"] = 5

        # Check patent/exclusivity data
        if patent_data:
            if patent_data.patent_status == "expired":
                score += 15
                factors["patent_status"] = 15
                notes.append("Patent expired - generic entry possible")
            elif patent_data.patent_status == "expiring":
                score += 10
                factors["patent_status"] = 10
            else:
                factors["patent_status"] = 0

            if patent_data.orphan_drug_potential:
                score += 10
                factors["orphan_drug"] = 10
                notes.append("Orphan drug potential")
            else:
                factors["orphan_drug"] = 0
        else:
            # Check Orange Book evidence for patent info
            ob_items = [e for e in evidence_items if e.source == "orange_book"]
            if ob_items:
                factors["patent_status"] = 5
            else:
                factors["patent_status"] = 0
            factors["orphan_drug"] = 0

        score = min(score, 100)

        return SubScore(
            dimension="development_feasibility",
            score=round(score, 1),
            weight=self.WEIGHTS["development_feasibility"],
            weighted_score=round(score * self.WEIGHTS["development_feasibility"], 1),
            confidence=ConfidenceLevel.from_score(score),
            factors={k: round(v, 1) for k, v in factors.items()},
            data_completeness=0.5 if not patent_data else 0.8,
            notes=notes if notes else ["Standard development pathway expected"]
        )

    def _generate_insights(
        self,
        scientific: SubScore,
        market: SubScore,
        competitive: SubScore,
        feasibility: SubScore,
        evidence_items: List[EvidenceItem],
        indication: str = "this indication"
    ) -> Tuple[List[Insight], List[Insight], List[Insight]]:
        """Generate strengths, risks, and recommendations with indication-specific details."""
        strengths = []
        risks = []
        recommendations = []

        clinical_count = len([e for e in evidence_items if e.source == "clinical_trials"])
        source_count = len(set(e.source for e in evidence_items))

        # Scientific strengths/risks
        if scientific.factors.get("clinical_phase", 0) >= 20:
            strengths.append(Insight(
                category=InsightCategory.STRENGTH,
                title="Advanced Clinical Validation",
                description=f"Phase 3+ clinical trials exist for {indication}, providing strong efficacy evidence with {clinical_count} clinical trial record(s)",
                severity="high",
                source_dimension="scientific_evidence"
            ))
        elif scientific.factors.get("clinical_phase", 0) == 0:
            risks.append(Insight(
                category=InsightCategory.RISK,
                title="No Clinical Evidence",
                description=f"No clinical trial data found for {indication}",
                severity="high",
                source_dimension="scientific_evidence"
            ))
            recommendations.append(Insight(
                category=InsightCategory.RECOMMENDATION,
                title="Initiate Clinical Validation",
                description=f"Consider proof-of-concept study to validate efficacy for {indication}",
                severity="high",
                source_dimension="scientific_evidence"
            ))

        if scientific.factors.get("source_diversity", 0) >= 16:
            strengths.append(Insight(
                category=InsightCategory.STRENGTH,
                title="Multi-Source Validation",
                description=f"Evidence from {source_count} independent sources supports {indication}, increasing confidence in the repurposing hypothesis",
                severity="medium",
                source_dimension="scientific_evidence"
            ))

        # Market strengths/risks
        if market.factors.get("unmet_need", 0) >= 24:
            unmet_raw = market.factors.get("unmet_need_raw")
            unmet_desc = f" (unmet need score: {unmet_raw:.0f}/100)" if unmet_raw else ""
            strengths.append(Insight(
                category=InsightCategory.STRENGTH,
                title=f"High Unmet Need in {indication}",
                description=f"Significant patient population with inadequate treatment options for {indication}{unmet_desc}",
                severity="high",
                source_dimension="market_opportunity"
            ))

        if market.factors.get("market_size", 0) >= 25:
            market_size_raw = market.factors.get("market_size_raw_billions")
            size_desc = f" (estimated ${market_size_raw:.1f}B)" if market_size_raw else ""
            strengths.append(Insight(
                category=InsightCategory.STRENGTH,
                title="Large Market Opportunity",
                description=f"Substantial commercial potential in the {indication} therapeutic area{size_desc}",
                severity="medium",
                source_dimension="market_opportunity"
            ))

        # Competitive risks
        if competitive.score < 50:
            comp_detail = competitive.notes[0] if competitive.notes else "Multiple competitors"
            risks.append(Insight(
                category=InsightCategory.RISK,
                title="Significant Competition",
                description=f"{comp_detail} in the {indication} space",
                severity="high",
                source_dimension="competitive_landscape"
            ))
            recommendations.append(Insight(
                category=InsightCategory.RECOMMENDATION,
                title="Develop Differentiation Strategy",
                description=f"Identify unique positioning for {indication} (patient subgroup, combination, delivery)",
                severity="high",
                source_dimension="competitive_landscape"
            ))

        # Feasibility strengths/risks
        if feasibility.factors.get("safety_data", 0) >= 15:
            fda_count = len([e for e in evidence_items if e.source == "openfda"])
            strengths.append(Insight(
                category=InsightCategory.STRENGTH,
                title="Established Safety Profile",
                description=f"Extensive real-world safety data ({fda_count} FDA record(s)) reduces development risk for {indication}",
                severity="high",
                source_dimension="development_feasibility"
            ))

        if feasibility.factors.get("regulatory_pathway", 0) >= 10:
            strengths.append(Insight(
                category=InsightCategory.STRENGTH,
                title="Favorable Regulatory Pathway",
                description=f"Existing approvals may enable 505(b)(2) or accelerated pathway for {indication}",
                severity="medium",
                source_dimension="development_feasibility"
            ))

        # Limit to top insights
        return strengths[:5], risks[:5], recommendations[:5]
