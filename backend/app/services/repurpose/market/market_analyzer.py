"""
Market Analyzer - Estimates market opportunity for drug repurposing indications.
Uses publicly available data from WHO, CDC, and curated sources.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("market.analyzer")


class MarketSize(str, Enum):
    """Market size classification."""
    MEGA = "mega"           # >$50B
    LARGE = "large"         # $10-50B
    MEDIUM = "medium"       # $1-10B
    SMALL = "small"         # $100M-1B
    NICHE = "niche"         # <$100M


@dataclass
class MarketOpportunity:
    """Complete market opportunity assessment for a drug-indication pair."""
    indication: str
    drug_name: str
    estimated_market_size_usd: int
    market_size_category: MarketSize
    patient_population_global: int
    patient_population_us: int
    cagr_percent: float
    unmet_need_score: float  # 0-100
    existing_treatments_count: int
    average_treatment_cost_usd: int
    potential_price_premium: float
    geographic_hotspots: List[str] = field(default_factory=list)
    key_competitors: List[str] = field(default_factory=list)
    market_drivers: List[str] = field(default_factory=list)
    market_barriers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "indication": self.indication,
            "drug_name": self.drug_name,
            "estimated_market_size_usd": self.estimated_market_size_usd,
            "market_size_category": self.market_size_category.value,
            "patient_population_global": self.patient_population_global,
            "patient_population_us": self.patient_population_us,
            "cagr_percent": self.cagr_percent,
            "unmet_need_score": self.unmet_need_score,
            "existing_treatments_count": self.existing_treatments_count,
            "average_treatment_cost_usd": self.average_treatment_cost_usd,
            "potential_price_premium": self.potential_price_premium,
            "geographic_hotspots": self.geographic_hotspots,
            "key_competitors": self.key_competitors,
            "market_drivers": self.market_drivers,
            "market_barriers": self.market_barriers
        }


class MarketAnalyzer:
    """
    Analyzes market opportunity for drug repurposing indications.
    Uses a combination of publicly available data sources.
    """

    # Pre-compiled market data for common indications (based on public sources)
    INDICATION_MARKET_DATA = {
        "cancer": {
            "market_size_usd": 250_000_000_000,
            "patient_population_global": 19_300_000,
            "patient_population_us": 1_900_000,
            "cagr": 7.5,
            "unmet_need": 75,
            "existing_treatments": 200,
            "avg_treatment_cost": 150_000,
            "drivers": ["Aging population", "Precision medicine advances", "Immunotherapy breakthroughs"],
            "barriers": ["High development costs", "Regulatory complexity", "Pricing pressure"],
            "competitors": ["Roche", "Merck", "Bristol-Myers Squibb", "AstraZeneca", "Pfizer"]
        },
        "cardiovascular": {
            "market_size_usd": 180_000_000_000,
            "patient_population_global": 523_000_000,
            "patient_population_us": 126_900_000,
            "cagr": 4.5,
            "unmet_need": 55,
            "existing_treatments": 150,
            "avg_treatment_cost": 12_000,
            "drivers": ["Rising obesity rates", "Aging population", "Lifestyle factors"],
            "barriers": ["Generic competition", "Prevention focus", "Price sensitivity"],
            "competitors": ["Novartis", "Pfizer", "Bayer", "Boehringer Ingelheim", "AstraZeneca"]
        },
        "diabetes": {
            "market_size_usd": 95_000_000_000,
            "patient_population_global": 537_000_000,
            "patient_population_us": 37_300_000,
            "cagr": 6.8,
            "unmet_need": 60,
            "existing_treatments": 80,
            "avg_treatment_cost": 9_600,
            "drivers": ["Obesity epidemic", "GLP-1 innovations", "Emerging markets growth"],
            "barriers": ["Biosimilar competition", "Access issues", "Adherence challenges"],
            "competitors": ["Novo Nordisk", "Eli Lilly", "Sanofi", "Merck", "AstraZeneca"]
        },
        "alzheimer": {
            "market_size_usd": 15_000_000_000,
            "patient_population_global": 55_000_000,
            "patient_population_us": 6_700_000,
            "cagr": 12.5,
            "unmet_need": 95,
            "existing_treatments": 8,
            "avg_treatment_cost": 28_000,
            "drivers": ["Aging population", "Recent FDA approvals", "High unmet need"],
            "barriers": ["Trial failures", "Diagnostic challenges", "Reimbursement uncertainty"],
            "competitors": ["Biogen", "Eisai", "Eli Lilly", "Roche", "Novartis"]
        },
        "liver": {
            "market_size_usd": 28_000_000_000,
            "patient_population_global": 1_500_000_000,
            "patient_population_us": 4_500_000,
            "cagr": 8.2,
            "unmet_need": 70,
            "existing_treatments": 25,
            "avg_treatment_cost": 84_000,
            "drivers": ["NASH epidemic", "Hepatitis burden", "Alcohol-related disease"],
            "barriers": ["Complex pathophysiology", "Endpoint challenges", "Competition"],
            "competitors": ["Gilead", "Intercept", "Madrigal", "Viking Therapeutics", "89bio"]
        },
        "inflammation": {
            "market_size_usd": 120_000_000_000,
            "patient_population_global": 400_000_000,
            "patient_population_us": 54_000_000,
            "cagr": 5.5,
            "unmet_need": 50,
            "existing_treatments": 100,
            "avg_treatment_cost": 35_000,
            "drivers": ["JAK inhibitor expansion", "IL-targeting biologics", "Autoimmune prevalence"],
            "barriers": ["Biosimilar erosion", "Safety concerns", "Price pressure"],
            "competitors": ["AbbVie", "Johnson & Johnson", "Amgen", "Bristol-Myers Squibb", "Pfizer"]
        },
        "stroke": {
            "market_size_usd": 8_000_000_000,
            "patient_population_global": 101_000_000,
            "patient_population_us": 7_600_000,
            "cagr": 6.0,
            "unmet_need": 80,
            "existing_treatments": 15,
            "avg_treatment_cost": 45_000,
            "drivers": ["Thrombectomy advances", "Neuroprotection research", "Prevention"],
            "barriers": ["Time-critical treatment", "Limited options", "Recovery challenges"],
            "competitors": ["Boehringer Ingelheim", "Bristol-Myers Squibb", "Pfizer", "Bayer"]
        },
        "asthma": {
            "market_size_usd": 25_000_000_000,
            "patient_population_global": 262_000_000,
            "patient_population_us": 25_000_000,
            "cagr": 4.0,
            "unmet_need": 45,
            "existing_treatments": 60,
            "avg_treatment_cost": 4_500,
            "drivers": ["Biologics for severe asthma", "Environmental factors", "Precision medicine"],
            "barriers": ["Generic competition", "Inhaler commoditization", "Adherence"],
            "competitors": ["GSK", "AstraZeneca", "Boehringer Ingelheim", "Novartis", "Sanofi"]
        },
        "infection": {
            "market_size_usd": 65_000_000_000,
            "patient_population_global": 2_000_000_000,
            "patient_population_us": 50_000_000,
            "cagr": 5.0,
            "unmet_need": 85,
            "existing_treatments": 200,
            "avg_treatment_cost": 3_000,
            "drivers": ["AMR crisis", "Pandemic preparedness", "New modalities"],
            "barriers": ["Low reimbursement", "Stewardship", "Market failures"],
            "competitors": ["Pfizer", "Merck", "GSK", "Johnson & Johnson", "Gilead"]
        },
        "neurological": {
            "market_size_usd": 45_000_000_000,
            "patient_population_global": 1_000_000_000,
            "patient_population_us": 100_000_000,
            "cagr": 6.5,
            "unmet_need": 75,
            "existing_treatments": 70,
            "avg_treatment_cost": 50_000,
            "drivers": ["Gene therapy advances", "BBB crossing tech", "Biomarker development"],
            "barriers": ["CNS complexity", "Trial design", "Regulatory hurdles"],
            "competitors": ["Biogen", "Roche", "Novartis", "Teva", "AbbVie"]
        },
        "obesity": {
            "market_size_usd": 50_000_000_000,
            "patient_population_global": 650_000_000,
            "patient_population_us": 100_000_000,
            "cagr": 15.0,
            "unmet_need": 70,
            "existing_treatments": 15,
            "avg_treatment_cost": 15_000,
            "drivers": ["GLP-1 revolution", "Rising prevalence", "Metabolic health focus"],
            "barriers": ["Cost concerns", "Side effects", "Chronic therapy needs"],
            "competitors": ["Novo Nordisk", "Eli Lilly", "Amgen", "Pfizer", "Viking Therapeutics"]
        },
        "pain": {
            "market_size_usd": 80_000_000_000,
            "patient_population_global": 1_500_000_000,
            "patient_population_us": 50_000_000,
            "cagr": 4.0,
            "unmet_need": 65,
            "existing_treatments": 100,
            "avg_treatment_cost": 8_000,
            "drivers": ["Non-opioid alternatives", "Chronic pain prevalence", "Nerve growth factor inhibitors"],
            "barriers": ["Opioid crisis legacy", "Generic competition", "Efficacy challenges"],
            "competitors": ["Pfizer", "Eli Lilly", "Teva", "AbbVie", "Johnson & Johnson"]
        }
    }

    def __init__(self):
        self.logger = get_logger("market.analyzer")

    async def analyze_market(self, indication: str, drug_name: str = "") -> MarketOpportunity:
        """
        Analyze market opportunity for a given indication.

        Args:
            indication: Disease/indication name
            drug_name: Name of the drug being repurposed

        Returns:
            MarketOpportunity with market analysis
        """
        self.logger.info(f"Analyzing market for indication: {indication}")

        # Normalize indication name
        indication_key = self._normalize_indication(indication)

        # Get base market data
        market_data = self.INDICATION_MARKET_DATA.get(
            indication_key,
            self._get_default_market_data(indication)
        )

        return MarketOpportunity(
            indication=indication,
            drug_name=drug_name,
            estimated_market_size_usd=market_data["market_size_usd"],
            market_size_category=self._categorize_market(market_data["market_size_usd"]),
            patient_population_global=market_data["patient_population_global"],
            patient_population_us=market_data["patient_population_us"],
            cagr_percent=market_data["cagr"],
            unmet_need_score=market_data["unmet_need"],
            existing_treatments_count=market_data["existing_treatments"],
            average_treatment_cost_usd=market_data["avg_treatment_cost"],
            potential_price_premium=self._calculate_price_premium(market_data),
            geographic_hotspots=["United States", "Europe", "Japan", "China"],
            key_competitors=market_data.get("competitors", [])[:5],
            market_drivers=market_data["drivers"],
            market_barriers=market_data["barriers"]
        )

    def _normalize_indication(self, indication: str) -> str:
        """Normalize indication name to match our data keys."""
        indication_lower = indication.lower()

        mappings = {
            "cancer": ["cancer", "tumor", "tumour", "oncology", "carcinoma", "lymphoma", "leukemia", "melanoma", "neoplasm"],
            "cardiovascular": ["cardiovascular", "heart", "cardiac", "hypertension", "atherosclerosis", "coronary", "atrial"],
            "diabetes": ["diabetes", "diabetic", "glycemic", "insulin", "hyperglycemia", "hypoglycemia"],
            "alzheimer": ["alzheimer", "dementia", "cognitive decline", "memory loss"],
            "liver": ["liver", "hepatic", "hepatitis", "cirrhosis", "nash", "nafld", "fatty liver"],
            "inflammation": ["inflammation", "inflammatory", "autoimmune", "arthritis", "psoriasis", "ibd", "crohn", "colitis", "lupus"],
            "stroke": ["stroke", "cerebrovascular", "ischemic brain", "cerebral"],
            "asthma": ["asthma", "respiratory", "copd", "pulmonary", "bronchial"],
            "infection": ["infection", "infectious", "bacterial", "viral", "antimicrobial", "antibiotic", "antiviral"],
            "neurological": ["neurological", "neurodegeneration", "parkinson", "ms", "multiple sclerosis", "epilepsy", "neuropathy"],
            "obesity": ["obesity", "overweight", "weight loss", "metabolic", "bmi"],
            "pain": ["pain", "analgesic", "nociceptive", "neuropathic pain", "chronic pain"]
        }

        for key, keywords in mappings.items():
            if any(kw in indication_lower for kw in keywords):
                return key

        return "unknown"

    def _categorize_market(self, size_usd: int) -> MarketSize:
        """Categorize market by size."""
        if size_usd >= 50_000_000_000:
            return MarketSize.MEGA
        elif size_usd >= 10_000_000_000:
            return MarketSize.LARGE
        elif size_usd >= 1_000_000_000:
            return MarketSize.MEDIUM
        elif size_usd >= 100_000_000:
            return MarketSize.SMALL
        return MarketSize.NICHE

    def _calculate_price_premium(self, market_data: dict) -> float:
        """Calculate potential price premium for repurposed drug."""
        unmet_need = market_data["unmet_need"]
        existing_treatments = market_data["existing_treatments"]

        # Higher unmet need + fewer treatments = higher premium potential
        if unmet_need > 80 and existing_treatments < 20:
            return 1.5  # 50% premium possible
        elif unmet_need > 60 and existing_treatments < 50:
            return 1.2  # 20% premium possible
        elif unmet_need > 40:
            return 1.0  # Market rate
        return 0.8  # May need to compete on price

    def _get_default_market_data(self, indication: str) -> dict:
        """Default market data for unknown indications."""
        return {
            "market_size_usd": 5_000_000_000,
            "patient_population_global": 50_000_000,
            "patient_population_us": 5_000_000,
            "cagr": 5.0,
            "unmet_need": 50,
            "existing_treatments": 30,
            "avg_treatment_cost": 20_000,
            "drivers": ["Unmet medical need", "Research advances"],
            "barriers": ["Competition", "Development costs"],
            "competitors": ["Various pharmaceutical companies"]
        }

    def calculate_opportunity_score(self, market_opportunity: MarketOpportunity) -> float:
        """
        Calculate overall opportunity score (0-100) based on market factors.

        Args:
            market_opportunity: MarketOpportunity object

        Returns:
            Opportunity score (0-100)
        """
        score = 0.0

        # Market size contribution (max 30 points)
        if market_opportunity.market_size_category == MarketSize.MEGA:
            score += 30
        elif market_opportunity.market_size_category == MarketSize.LARGE:
            score += 25
        elif market_opportunity.market_size_category == MarketSize.MEDIUM:
            score += 20
        elif market_opportunity.market_size_category == MarketSize.SMALL:
            score += 10
        else:
            score += 5

        # CAGR contribution (max 20 points)
        cagr = market_opportunity.cagr_percent
        if cagr >= 10:
            score += 20
        elif cagr >= 7:
            score += 15
        elif cagr >= 5:
            score += 10
        else:
            score += 5

        # Unmet need contribution (max 30 points)
        score += (market_opportunity.unmet_need_score / 100) * 30

        # Price premium potential (max 20 points)
        premium = market_opportunity.potential_price_premium
        if premium >= 1.5:
            score += 20
        elif premium >= 1.2:
            score += 15
        elif premium >= 1.0:
            score += 10
        else:
            score += 5

        return min(score, 100.0)
