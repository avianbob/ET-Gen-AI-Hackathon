"""
Regulatory Pathway Advisor

Rules-based advisor that recommends FDA regulatory pathways for drug repurposing
opportunities based on evidence type, indication characteristics, and competitive data.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Indications commonly associated with orphan drug designation (< 200,000 US patients)
ORPHAN_KEYWORDS = [
    "rare", "orphan", "lysosomal", "muscular dystrophy", "cystic fibrosis",
    "huntington", "als", "amyotrophic", "sickle cell", "thalassemia",
    "gaucher", "fabry", "pompe", "niemann-pick", "wilson disease",
    "pulmonary arterial hypertension", "idiopathic pulmonary fibrosis",
    "glioblastoma", "neuroblastoma", "retinoblastoma", "mesothelioma",
    "cholangiocarcinoma", "myelofibrosis", "mastocytosis",
]

# Serious conditions eligible for Fast Track designation
SERIOUS_CONDITION_KEYWORDS = [
    "cancer", "oncology", "tumor", "carcinoma", "leukemia", "lymphoma", "melanoma",
    "heart failure", "stroke", "myocardial infarction", "sepsis", "septic",
    "hiv", "aids", "hepatitis", "tuberculosis", "malaria",
    "alzheimer", "parkinson", "dementia", "epilepsy", "multiple sclerosis",
    "renal failure", "kidney disease", "liver failure", "cirrhosis",
    "diabetes", "diabetic", "copd", "respiratory failure",
    "crohn", "ulcerative colitis", "lupus", "rheumatoid arthritis",
    "amyloidosis", "sarcoidosis",
]


class RegulatoryAdvisor:
    """Recommends FDA regulatory pathways for drug repurposing opportunities."""

    def analyze(
        self,
        drug_name: str,
        indication: str,
        evidence_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze and recommend regulatory pathway for a drug-indication pair.

        Args:
            drug_name: Name of the drug being repurposed
            indication: Target therapeutic indication
            evidence_data: Optional dict with keys:
                - evidence_count: int
                - evidence_types: list of str (e.g., "clinical_trial", "patent")
                - comparative_data: dict with advantages/safety info
                - scientific_score: float (0-100)
                - feasibility_score: float (0-100)

        Returns:
            Dict with pathway recommendation and eligibility assessments
        """
        evidence_data = evidence_data or {}

        pathway = self._determine_pathway(drug_name, indication, evidence_data)
        orphan = self._check_orphan_eligibility(indication)
        fast_track = self._check_fast_track(indication, evidence_data)
        breakthrough = self._check_breakthrough(indication, evidence_data)
        timeline = self._estimate_timeline(pathway, orphan, fast_track)
        considerations = self._compile_considerations(
            pathway, orphan, fast_track, breakthrough, evidence_data
        )

        rationale = self._build_rationale(
            drug_name, indication, pathway, orphan, fast_track, breakthrough
        )

        return {
            "drug_name": drug_name,
            "indication": indication,
            "recommended_pathway": pathway,
            "orphan_drug_eligible": orphan,
            "fast_track_eligible": fast_track,
            "breakthrough_eligible": breakthrough,
            "estimated_timeline_years": timeline,
            "rationale": rationale,
            "key_considerations": considerations,
        }

    def _determine_pathway(
        self, drug_name: str, indication: str, evidence_data: Dict
    ) -> str:
        """Determine the recommended NDA pathway."""
        evidence_types = evidence_data.get("evidence_types", [])
        scientific_score = evidence_data.get("scientific_score", 0)

        # If strong existing clinical data, 505(b)(2) is most likely
        has_clinical = any(
            t in str(evidence_types).lower()
            for t in ["clinical_trial", "clinical", "phase"]
        )
        has_safety_data = evidence_data.get("has_safety_data", has_clinical)

        # Generic pathway: rarely applicable for repurposing (different indication)
        # 505(j) requires same indication, so almost never for repurposing
        # Default to 505(b)(2) for repurposing with existing safety data

        if has_safety_data and scientific_score >= 40:
            return "505(b)(2)"
        elif has_safety_data:
            return "505(b)(2)"
        elif scientific_score >= 70:
            return "505(b)(2)"  # Strong evidence suggests existing literature
        else:
            return "Full NDA"

    def _check_orphan_eligibility(self, indication: str) -> bool:
        """Check if indication may qualify for Orphan Drug Designation."""
        indication_lower = indication.lower()
        return any(kw in indication_lower for kw in ORPHAN_KEYWORDS)

    def _check_fast_track(
        self, indication: str, evidence_data: Dict
    ) -> bool:
        """Check if eligible for Fast Track designation (serious condition + unmet need)."""
        indication_lower = indication.lower()
        is_serious = any(kw in indication_lower for kw in SERIOUS_CONDITION_KEYWORDS)

        # Unmet need indicators
        feasibility_score = evidence_data.get("feasibility_score", 0)
        has_few_competitors = evidence_data.get("competitor_count", 5) <= 2

        return is_serious and (has_few_competitors or feasibility_score >= 60)

    def _check_breakthrough(
        self, indication: str, evidence_data: Dict
    ) -> bool:
        """
        Check if eligible for Breakthrough Therapy designation.
        Requires substantial improvement over existing therapy.
        """
        comparative = evidence_data.get("comparative_data", {})
        advantages = comparative.get("advantages", [])
        safety_improvement = comparative.get("safety_improvement", False)
        scientific_score = evidence_data.get("scientific_score", 0)

        has_substantial_advantage = len(advantages) >= 2 or safety_improvement
        strong_evidence = scientific_score >= 70

        return has_substantial_advantage and strong_evidence

    def _estimate_timeline(
        self, pathway: str, orphan: bool, fast_track: bool
    ) -> int:
        """Estimate development timeline in years."""
        base_timelines = {
            "505(b)(2)": 4,
            "505(j)": 2,
            "Full NDA": 8,
        }
        timeline = base_timelines.get(pathway, 6)

        # Accelerations
        if orphan:
            timeline = max(timeline - 1, 2)
        if fast_track:
            timeline = max(timeline - 1, 2)

        return timeline

    def _compile_considerations(
        self,
        pathway: str,
        orphan: bool,
        fast_track: bool,
        breakthrough: bool,
        evidence_data: Dict,
    ) -> List[str]:
        """Compile key regulatory considerations."""
        considerations = []

        if pathway == "505(b)(2)":
            considerations.append(
                "505(b)(2) allows reliance on FDA's previous findings of safety/efficacy, "
                "reducing the need for full clinical program."
            )
            considerations.append(
                "A Right of Reference or literature-based submission strategy should be evaluated."
            )
        elif pathway == "Full NDA":
            considerations.append(
                "Full NDA pathway requires comprehensive clinical trial program "
                "including Phase I-III studies."
            )
            considerations.append(
                "Consider generating preliminary safety/efficacy data to potentially "
                "transition to 505(b)(2) pathway."
            )

        if orphan:
            considerations.append(
                "Orphan Drug Designation provides 7-year market exclusivity, "
                "tax credits for clinical trials, and FDA fee waivers."
            )

        if fast_track:
            considerations.append(
                "Fast Track designation enables rolling review and more frequent "
                "FDA interactions during development."
            )

        if breakthrough:
            considerations.append(
                "Breakthrough Therapy designation provides intensive FDA guidance, "
                "organizational commitment, and potential for rolling review."
            )

        evidence_count = evidence_data.get("evidence_count", 0)
        if evidence_count < 5:
            considerations.append(
                "Limited evidence base — additional preclinical or Phase I data "
                "may be needed before regulatory engagement."
            )

        return considerations

    def _build_rationale(
        self,
        drug_name: str,
        indication: str,
        pathway: str,
        orphan: bool,
        fast_track: bool,
        breakthrough: bool,
    ) -> str:
        """Build a summary rationale string."""
        designations = []
        if orphan:
            designations.append("Orphan Drug Designation")
        if fast_track:
            designations.append("Fast Track")
        if breakthrough:
            designations.append("Breakthrough Therapy")

        designation_text = ""
        if designations:
            designation_text = (
                f" Additionally eligible for: {', '.join(designations)}."
            )

        return (
            f"For repurposing {drug_name} in {indication}, the recommended pathway is "
            f"{pathway} based on available evidence and existing safety profile."
            f"{designation_text}"
        )
