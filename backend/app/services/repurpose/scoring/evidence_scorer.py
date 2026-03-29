"""
Evidence Scorer - Scores and ranks drug repurposing opportunities.
Uses weighted algorithm to assess evidence quality from multiple sources.
"""

from typing import List, Dict
from collections import defaultdict
import numpy as np
from app.schemas.repurpose_api import EvidenceItem, IndicationResult
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("scoring")


class EvidenceScorer:
    """Scores and ranks evidence for drug repurposing opportunities."""

    def __init__(self):
        """Initialize scorer with evidence source weights."""
        # Base scores for each data source (out of 100)
        # These represent the inherent value of evidence from each source
        self.source_base_scores = {
            # Original agents
            "clinical_trials": 70,  # Clinical validation is most valuable
            "literature": 60,       # Peer-reviewed research
            "bioactivity": 55,      # Molecular/experimental data
            "patent": 50,           # Commercial interest indicator
            "internal": 50,         # Proprietary data
            # Tier 1 agents (Phase 2)
            "openfda": 65,          # FDA safety data is critical
            "opentargets": 65,      # Validated disease associations
            "semantic_scholar": 60, # Enhanced literature with citations
            # Tier 2 agents (Phase 2)
            "dailymed": 55,         # FDA labeling information
            "kegg": 50,             # Pathway and disease links
            "uniprot": 50,          # Protein target data
            "orange_book": 55,      # Patent/exclusivity data
            # Tier 3 agents (Phase 2)
            "rxnorm": 50,           # Drug normalization data
            "who": 55,              # WHO Essential Medicines
            "drugbank": 60          # Comprehensive drug database
        }

    def score_evidence(self, evidence: EvidenceItem) -> float:
        """
        Calculate confidence score (0-100) for a single evidence item.

        Args:
            evidence: Evidence item to score

        Returns:
            Confidence score (0-100)
        """
        # Base score from source type
        base_score = self.source_base_scores.get(evidence.source, 50)

        # Apply quality multipliers based on source-specific factors
        if evidence.source == "clinical_trials":
            base_score = self._score_clinical_trial(evidence, base_score)
        elif evidence.source == "literature":
            base_score = self._score_literature(evidence, base_score)
        elif evidence.source == "bioactivity":
            base_score = self._score_bioactivity(evidence, base_score)
        elif evidence.source == "patent":
            base_score = self._score_patent(evidence, base_score)
        elif evidence.source == "internal":
            base_score = self._score_internal(evidence, base_score)
        # Tier 1 agents (Phase 2)
        elif evidence.source == "openfda":
            base_score = self._score_openfda(evidence, base_score)
        elif evidence.source == "opentargets":
            base_score = self._score_opentargets(evidence, base_score)
        elif evidence.source == "semantic_scholar":
            base_score = self._score_semantic_scholar(evidence, base_score)
        # Tier 2 agents (Phase 2)
        elif evidence.source == "dailymed":
            base_score = self._score_dailymed(evidence, base_score)
        elif evidence.source == "kegg":
            base_score = self._score_kegg(evidence, base_score)
        elif evidence.source == "uniprot":
            base_score = self._score_uniprot(evidence, base_score)
        elif evidence.source == "orange_book":
            base_score = self._score_orange_book(evidence, base_score)
        # Tier 3 agents (Phase 2)
        elif evidence.source == "rxnorm":
            base_score = self._score_rxnorm(evidence, base_score)
        elif evidence.source == "who":
            base_score = self._score_who(evidence, base_score)
        elif evidence.source == "drugbank":
            base_score = self._score_drugbank(evidence, base_score)

        # Add bonus for high relevance score (additive, not multiplicative)
        if evidence.relevance_score and evidence.relevance_score > 0:
            # Add up to 15 points for high relevance
            relevance_bonus = evidence.relevance_score * 15
            base_score += relevance_bonus

        return min(base_score, 100.0)

    def _score_clinical_trial(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score clinical trial evidence."""
        metadata = evidence.metadata

        # Boost for completed trials (+15 points)
        status = metadata.get("status", "").lower()
        if "completed" in status:
            base_score += 15
        elif "active" in status or "recruiting" in status:
            base_score += 10

        # Boost for later phase trials
        phase = metadata.get("phase", "").lower()
        if "phase 4" in phase or "phase iv" in phase or "4" in phase:
            base_score += 20  # Phase 4 = post-market, very high confidence
        elif "phase 3" in phase or "phase iii" in phase or "3" in phase:
            base_score += 15  # Phase 3 = efficacy trials
        elif "phase 2" in phase or "phase ii" in phase or "2" in phase:
            base_score += 10  # Phase 2 = dose-finding
        elif "phase 1" in phase or "phase i" in phase or "1" in phase:
            base_score += 5   # Phase 1 = safety

        return base_score

    def _score_literature(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score literature evidence."""
        metadata = evidence.metadata

        # Boost for recent publications
        year = metadata.get("year")
        if year:
            try:
                year_int = int(year)
                if year_int >= 2023:
                    base_score += 20  # Very recent
                elif year_int >= 2020:
                    base_score += 15  # Recent
                elif year_int >= 2015:
                    base_score += 10  # Moderately recent
                elif year_int >= 2010:
                    base_score += 5   # Older but still relevant
            except (ValueError, TypeError):
                pass

        # Boost for high-impact papers (using citations as proxy)
        citations = metadata.get("citations", 0)
        if citations > 100:
            base_score += 10
        elif citations > 50:
            base_score += 5

        return base_score

    def _score_bioactivity(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score bioactivity evidence."""
        metadata = evidence.metadata

        # Boost for strong activity (low IC50)
        ic50 = metadata.get("avg_ic50_nm")
        if ic50:
            try:
                ic50_float = float(ic50)
                if ic50_float < 100:  # Very potent (<100nM)
                    base_score += 25
                elif ic50_float < 1000:  # Potent (<1uM)
                    base_score += 15
                elif ic50_float < 10000:  # Moderate (<10uM)
                    base_score += 10
            except (ValueError, TypeError):
                pass

        # Boost for multiple activity records
        activity_count = metadata.get("activity_count", 0)
        if activity_count >= 10:
            base_score += 10
        elif activity_count >= 5:
            base_score += 5

        return base_score

    def _score_patent(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score patent evidence."""
        metadata = evidence.metadata

        # Boost for recent patents
        filing_date = metadata.get("filing_date", "")
        if filing_date:
            try:
                year = int(filing_date.split("-")[0])
                if year >= 2022:
                    base_score += 20
                elif year >= 2020:
                    base_score += 15
                elif year >= 2015:
                    base_score += 10
            except (ValueError, IndexError):
                pass

        # Boost for multiple applicants (broader interest)
        applicants = metadata.get("applicants", [])
        if len(applicants) >= 3:
            base_score += 10
        elif len(applicants) >= 2:
            base_score += 5

        return base_score

    def _score_internal(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score internal evidence."""
        metadata = evidence.metadata

        # Boost based on priority
        priority = metadata.get("priority", "low")
        if priority == "high":
            base_score += 20
        elif priority == "medium":
            base_score += 10
        # Low priority gets no bonus

        return base_score

    def _score_openfda(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score OpenFDA evidence (adverse events, labels, recalls)."""
        metadata = evidence.metadata
        data_type = metadata.get("data_type", "")

        if data_type == "adverse_event":
            # Higher adverse event counts suggest more usage/interest
            count = metadata.get("count", 0)
            if count > 10000:
                base_score += 15
            elif count > 5000:
                base_score += 10
            elif count > 1000:
                base_score += 5

        elif data_type == "label":
            # Labels with approved indications are highly relevant
            base_score += 15

        elif data_type == "recall":
            # Recalls are important safety signals (boost for awareness)
            classification = metadata.get("classification", "")
            if classification == "Class I":
                base_score += 10  # Most serious
            elif classification == "Class II":
                base_score += 5

        return base_score

    def _score_opentargets(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score OpenTargets evidence (indications, mechanisms, associations)."""
        metadata = evidence.metadata
        data_type = metadata.get("data_type", "")

        if data_type == "indication":
            # Boost based on clinical phase
            max_phase = metadata.get("max_phase", 0)
            if max_phase >= 4:
                base_score += 25  # Approved
            elif max_phase >= 3:
                base_score += 20  # Phase 3
            elif max_phase >= 2:
                base_score += 15  # Phase 2
            elif max_phase >= 1:
                base_score += 10  # Phase 1

        elif data_type == "mechanism":
            # Mechanism data is valuable for understanding
            base_score += 10

        elif data_type == "linked_disease":
            # Association score boost
            assoc_score = metadata.get("association_score", 0)
            if assoc_score > 0.7:
                base_score += 15
            elif assoc_score > 0.5:
                base_score += 10
            elif assoc_score > 0.3:
                base_score += 5

        return base_score

    def _score_semantic_scholar(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score Semantic Scholar evidence (papers with citations)."""
        metadata = evidence.metadata

        # Boost for high citation count
        citations = metadata.get("citation_count", 0)
        if citations > 500:
            base_score += 20
        elif citations > 200:
            base_score += 15
        elif citations > 100:
            base_score += 10
        elif citations > 50:
            base_score += 5

        # Boost for influential citations
        influential = metadata.get("influential_citations", 0)
        if influential > 50:
            base_score += 10
        elif influential > 20:
            base_score += 5

        # Boost for recency
        year = metadata.get("year")
        if year:
            try:
                year_int = int(year)
                if year_int >= 2023:
                    base_score += 15
                elif year_int >= 2020:
                    base_score += 10
                elif year_int >= 2018:
                    base_score += 5
            except (ValueError, TypeError):
                pass

        return base_score

    def _score_dailymed(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score DailyMed evidence (FDA drug labeling)."""
        metadata = evidence.metadata

        # DailyMed provides official FDA labeling
        data_type = metadata.get("data_type", "")

        if data_type == "spl":
            # SPL with full labeling is valuable
            base_score += 15

            # Boost for specific product types
            product_type = metadata.get("product_type", "").lower()
            if "prescription" in product_type:
                base_score += 5

        return base_score

    def _score_kegg(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score KEGG evidence (pathways and disease links)."""
        metadata = evidence.metadata
        data_type = metadata.get("data_type", "")

        if data_type == "disease_link":
            # Direct disease links are valuable
            base_score += 15

        elif data_type == "pathway":
            # Pathway information provides mechanistic insight
            pathway_count = metadata.get("pathway_count", 0)
            if pathway_count >= 5:
                base_score += 15
            elif pathway_count >= 3:
                base_score += 10
            elif pathway_count >= 1:
                base_score += 5

        return base_score

    def _score_uniprot(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score UniProt evidence (protein target data)."""
        metadata = evidence.metadata
        data_type = metadata.get("data_type", "")

        if data_type == "disease_association":
            # Disease associations from UniProt are well-curated
            base_score += 15

        elif data_type == "function":
            # Function information provides context
            base_score += 10

        return base_score

    def _score_orange_book(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score Orange Book evidence (FDA approvals, patents, exclusivity)."""
        metadata = evidence.metadata

        # Boost based on submission status
        submission_status = metadata.get("submission_status", "").upper()
        if "AP" in submission_status or "APPROVED" in submission_status:
            base_score += 20
        elif "TA" in submission_status:  # Tentative approval
            base_score += 10

        # Boost for original applications (new drug)
        submission_type = metadata.get("submission_type", "")
        if submission_type == "ORIG":
            base_score += 10

        return base_score

    def _score_rxnorm(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score RxNorm evidence (drug normalization, interactions, classes)."""
        metadata = evidence.metadata
        data_type = metadata.get("data_type", "")

        if data_type == "properties":
            # Core drug normalization data
            base_score += 10

        elif data_type == "drug_class":
            # Therapeutic classification is valuable
            base_score += 15

        elif data_type == "interaction":
            # Drug interactions are important for safety
            severity = metadata.get("severity", "").lower()
            if severity == "high" or severity == "severe":
                base_score += 15
            elif severity == "moderate":
                base_score += 10
            else:
                base_score += 5

        elif data_type == "related_drug":
            # Related formulations are useful
            base_score += 5

        return base_score

    def _score_who(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score WHO evidence (Essential Medicines, disease burden)."""
        metadata = evidence.metadata
        data_type = metadata.get("data_type", "")

        if data_type == "essential_medicine":
            # WHO Essential Medicine status is highly valuable
            base_score += 25
            if metadata.get("core"):
                base_score += 10  # Additional bonus for core list

        elif data_type == "disease_burden":
            # WHO disease burden data
            who_priority = metadata.get("who_priority", "").lower()
            if who_priority == "high":
                base_score += 15
            elif who_priority == "medium":
                base_score += 10
            else:
                base_score += 5

        elif data_type == "similar_essential_medicine":
            # Related essential medicines
            base_score += 5

        return base_score

    def _score_drugbank(self, evidence: EvidenceItem, base_score: float) -> float:
        """Score DrugBank evidence (drug info, targets, indications)."""
        metadata = evidence.metadata
        data_type = metadata.get("data_type", "")

        if data_type == "drug_info":
            # Comprehensive drug information
            base_score += 15
            # Boost for approved drugs
            groups = metadata.get("groups", [])
            if "approved" in groups:
                base_score += 10

        elif data_type == "target":
            # Drug target information is valuable
            base_score += 15
            # Bonus for specific action types
            action = metadata.get("action", "").lower()
            if action in ["inhibitor", "activator", "agonist", "antagonist"]:
                base_score += 5

        elif data_type == "indication":
            # Direct indications from DrugBank
            base_score += 20

        elif data_type == "categories":
            # Therapeutic categories
            base_score += 10

        elif data_type == "toxicity":
            # Toxicity data is important for feasibility
            base_score += 10

        return base_score

    def rank_indications(self, evidence_list: List[EvidenceItem]) -> List[IndicationResult]:
        """
        Group evidence by indication and rank by confidence.

        Args:
            evidence_list: List of all evidence items

        Returns:
            Ranked list of indications with aggregated evidence
        """
        logger.info(f"Ranking {len(evidence_list)} evidence items...")

        # Group evidence by indication (skip items without proper indication)
        indication_map = defaultdict(list)
        skipped_count = 0

        for evidence in evidence_list:
            indication = evidence.indication
            # Skip evidence without a valid indication
            if not indication or indication.lower() == "unknown indication":
                skipped_count += 1
                continue
            score = self.score_evidence(evidence)
            indication_map[indication].append((evidence, score))

        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} evidence items without valid indication")

        # Aggregate scores per indication
        results = []
        for indication, items in indication_map.items():
            evidence_items = [e for e, _ in items]
            scores = [s for _, s in items]

            # Calculate combined confidence
            if scores:
                # Use weighted combination of max, mean, and count bonuses
                max_score = max(scores)
                mean_score = float(np.mean(scores))

                # Start with weighted average favoring the best evidence
                base_confidence = (max_score * 0.6) + (mean_score * 0.4)
            else:
                base_confidence = 0.0

            # Evidence count bonus: more evidence = higher confidence
            evidence_count = len(evidence_items)
            if evidence_count >= 10:
                count_bonus = 15
            elif evidence_count >= 5:
                count_bonus = 10
            elif evidence_count >= 3:
                count_bonus = 5
            else:
                count_bonus = 0

            # Diversity bonus: reward evidence from multiple sources
            unique_sources = len(set(e.source for e in evidence_items))
            diversity_bonus = min(unique_sources * 5, 20)  # Max +20 for 4+ sources

            # Calculate final confidence
            confidence = min(base_confidence + count_bonus + diversity_bonus, 100.0)

            results.append(IndicationResult(
                indication=indication,
                confidence_score=round(confidence, 1),
                evidence_count=len(evidence_items),
                evidence_items=evidence_items,
                supporting_sources=list(set(e.source for e in evidence_items))
            ))

        # Sort by confidence score (descending)
        ranked_results = sorted(results, key=lambda x: x.confidence_score, reverse=True)

        logger.info(f"Identified {len(ranked_results)} unique indications")
        if ranked_results:
            logger.info(f"Top indication: {ranked_results[0].indication} with score {ranked_results[0].confidence_score}")

        return ranked_results
