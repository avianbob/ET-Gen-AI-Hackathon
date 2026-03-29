"""
Decision Rules Engine - Identifies strategic pharmaceutical opportunities.

Implements pharma portfolio planning logic:
- Whitespace detection (high burden + low trials)
- Biosimilar opportunity (patent expiry)
- Formulation opportunity (oral vs injectable)
- Geographic arbitrage (import dependence)
"""

from typing import Dict, Any, List, Optional
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("decision.rules")


class RulesEngine:
    """Applies pharma strategy rules to identify opportunities."""

    def analyze(
        self,
        market_data: Dict[str, Any] = None,
        patent_data: Dict[str, Any] = None,
        trial_data: Dict[str, Any] = None,
        exim_data: Dict[str, Any] = None,
        drug_name: str = "",
        indication: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Run all decision rules and return identified opportunities.

        Returns list of opportunity dicts with:
        - opportunity_type: whitespace | biosimilar | formulation | geographic
        - confidence: high | medium | low
        - title: Short opportunity title
        - reasoning: Why this is an opportunity
        - recommendation: Suggested next step
        """
        opportunities = []

        if market_data and trial_data:
            opp = self.detect_whitespace(market_data, trial_data, indication)
            if opp:
                opportunities.append(opp)

        if patent_data:
            opp = self.detect_biosimilar_opportunity(patent_data, drug_name)
            if opp:
                opportunities.append(opp)

        if exim_data:
            opp = self.detect_geographic_arbitrage(exim_data, drug_name)
            if opp:
                opportunities.append(opp)

        if market_data:
            opp = self.detect_unmet_need(market_data, indication)
            if opp:
                opportunities.append(opp)

        return opportunities

    def detect_whitespace(
        self,
        market_data: Dict[str, Any],
        trial_data: Dict[str, Any],
        indication: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Rule: High disease burden + Low trial activity = Whitespace opportunity.
        """
        burden_score = market_data.get("unmet_need_score", 0)
        patient_pop = market_data.get("patient_population_millions", 0)
        trial_count = trial_data.get("trial_count", 0)

        if isinstance(trial_count, str):
            try:
                trial_count = int(trial_count)
            except ValueError:
                trial_count = 0

        # High burden: unmet need > 60 OR patient pop > 100M
        high_burden = burden_score > 60 or patient_pop > 100

        # Low activity: fewer than 15 active trials
        low_activity = trial_count < 15

        if high_burden and low_activity:
            confidence = "high" if burden_score > 75 and trial_count < 5 else "medium"
            return {
                "opportunity_type": "whitespace",
                "confidence": confidence,
                "title": f"Whitespace in {indication or 'this indication'}",
                "reasoning": (
                    f"High disease burden (unmet need score: {burden_score}/100, "
                    f"{patient_pop}M patients) combined with low clinical trial activity "
                    f"({trial_count} active trials) indicates an underserved market."
                ),
                "recommendation": (
                    "Initiate early-stage feasibility study. Low competitive intensity "
                    "creates first-mover advantage for a repurposed molecule."
                ),
                "data": {
                    "burden_score": burden_score,
                    "patient_population_millions": patient_pop,
                    "trial_count": trial_count,
                }
            }
        return None

    def detect_biosimilar_opportunity(
        self,
        patent_data: Dict[str, Any],
        drug_name: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Rule: Patent expiry within 2 years = Biosimilar/generic entry opportunity.
        """
        years_to_expiry = patent_data.get("years_to_expiry", None)
        expiry_date = patent_data.get("expiry_date", "")
        is_biologic = patent_data.get("is_biologic", False)

        if years_to_expiry is not None and years_to_expiry <= 2:
            entry_type = "biosimilar" if is_biologic else "generic"
            confidence = "high" if years_to_expiry <= 1 else "medium"

            return {
                "opportunity_type": "biosimilar",
                "confidence": confidence,
                "title": f"{entry_type.title()} entry for {drug_name or 'this drug'}",
                "reasoning": (
                    f"Patent expires in {years_to_expiry:.1f} years ({expiry_date}). "
                    f"This creates a {entry_type} entry opportunity. "
                    f"{'Biosimilar development takes 5-8 years; timing is critical.' if is_biologic else 'ANDA filing can be prepared for Day-1 launch.'}"
                ),
                "recommendation": (
                    f"Begin {entry_type} development immediately. "
                    f"{'File biosimilar application with FDA.' if is_biologic else 'Prepare ANDA/505(b)(2) submission.'} "
                    f"First-to-file advantage can capture 40-60% of post-patent market."
                ),
                "data": {
                    "years_to_expiry": years_to_expiry,
                    "expiry_date": expiry_date,
                    "entry_type": entry_type,
                }
            }
        return None

    def detect_geographic_arbitrage(
        self,
        exim_data: Dict[str, Any],
        drug_name: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Rule: High import volume + concentrated supply = Local manufacturing opportunity.
        """
        top_importers = exim_data.get("top_importers", [])
        top_exporters = exim_data.get("top_exporters", [])

        if not top_importers or not top_exporters:
            return None

        # Check if top 2 exporters control >60% of supply
        top_2_share = sum(e.get("share_pct", 0) for e in top_exporters[:2])
        concentrated = top_2_share > 60

        # Check if any importer has high volume
        high_import = any(i.get("share_pct", 0) > 20 for i in top_importers)

        if concentrated and high_import:
            top_importer = top_importers[0]
            return {
                "opportunity_type": "geographic",
                "confidence": "medium",
                "title": f"Supply chain opportunity for {drug_name or 'this API'}",
                "reasoning": (
                    f"Supply is concentrated: top 2 exporters control {top_2_share:.0f}% of global supply. "
                    f"{top_importer['country']} imports {top_importer.get('share_pct', 0)}% of global volume. "
                    f"This creates dependency risk and opportunity for local manufacturing."
                ),
                "recommendation": (
                    f"Evaluate local API manufacturing in {top_importer['country']} or alternative sourcing. "
                    f"Supply diversification reduces risk and may qualify for government incentives."
                ),
                "data": {
                    "supply_concentration": top_2_share,
                    "top_importer": top_importer.get("country", ""),
                    "import_share": top_importer.get("share_pct", 0),
                }
            }
        return None

    def detect_unmet_need(
        self,
        market_data: Dict[str, Any],
        indication: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Rule: Very high unmet need + large market = Priority target.
        """
        unmet_need = market_data.get("unmet_need_score", 0)
        market_size = market_data.get("market_size_billions", 0)
        cagr = market_data.get("cagr_percent", 0)

        if unmet_need >= 75 and market_size >= 10:
            return {
                "opportunity_type": "unmet_need",
                "confidence": "high",
                "title": f"High unmet need in {indication or 'this indication'}",
                "reasoning": (
                    f"Unmet need score of {unmet_need}/100 in a ${market_size}B market "
                    f"growing at {cagr}% CAGR. This represents a significant commercial "
                    f"opportunity for value-added differentiated products."
                ),
                "recommendation": (
                    "Prioritize this indication for repurposing candidates. "
                    "Focus on differentiation through novel formulations, "
                    "alternative dosage forms, or targeting underserved patient populations."
                ),
                "data": {
                    "unmet_need_score": unmet_need,
                    "market_size_billions": market_size,
                    "cagr_percent": cagr,
                }
            }
        return None
