"""
Comparative Analyzer - Analyzes advantages over existing treatments.

Provides:
1. Comparator drug identification (standard of care)
2. Advantage analysis (dosing, administration, safety, etc.)
3. Side effect profile comparison
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Tuple
from app.schemas.repurpose_scoring import (
    ComparatorDrug,
    ComparativeAdvantage,
    SideEffectComparison,
    SideEffectEntry,
)
from app.services.repurpose.utils.logger import get_logger
from app.repurpose_settings import settings

logger = get_logger("scoring.comparative_analyzer")


class ComparativeAnalyzer:
    """Analyzes candidate drug advantages over existing treatments."""

    # Curated comparator data for common indications
    CURATED_COMPARATORS = {
        "type 2 diabetes": [
            ComparatorDrug(
                drug_name="Metformin",
                drug_id="CHEMBL1431",
                mechanism="Biguanide; reduces hepatic glucose production",
                administration_route="oral",
                dosing_frequency="twice daily",
                age_restrictions="Not recommended under 10 years",
                key_side_effects=["Nausea", "Diarrhea", "Abdominal pain", "Lactic acidosis (rare)"],
                contraindications=["Renal impairment", "Metabolic acidosis", "Acute heart failure"],
                average_monthly_cost=15.0,
                approval_year=1995,
                market_share_percent=35.0,
            ),
            ComparatorDrug(
                drug_name="Sitagliptin (Januvia)",
                drug_id="CHEMBL1951155",
                mechanism="DPP-4 inhibitor; increases incretin levels",
                administration_route="oral",
                dosing_frequency="once daily",
                age_restrictions="Adults 18+ years",
                key_side_effects=["Upper respiratory infection", "Headache", "Pancreatitis (rare)"],
                contraindications=["History of pancreatitis"],
                average_monthly_cost=450.0,
                approval_year=2006,
                market_share_percent=12.0,
            ),
            ComparatorDrug(
                drug_name="Semaglutide (Ozempic)",
                drug_id="CHEMBL3545011",
                mechanism="GLP-1 receptor agonist",
                administration_route="subcutaneous injection",
                dosing_frequency="once weekly",
                age_restrictions="Adults 18+ years",
                key_side_effects=["Nausea", "Vomiting", "Diarrhea", "Pancreatitis risk"],
                contraindications=["MTC history", "MEN 2 syndrome", "Pancreatitis history"],
                average_monthly_cost=850.0,
                approval_year=2017,
                market_share_percent=18.0,
            ),
        ],
        "cancer": [
            ComparatorDrug(
                drug_name="Pembrolizumab (Keytruda)",
                drug_id="CHEMBL3137343",
                mechanism="PD-1 checkpoint inhibitor",
                administration_route="IV infusion",
                dosing_frequency="every 3 weeks",
                age_restrictions="Adults and pediatric patients (varies by indication)",
                key_side_effects=["Fatigue", "Immune-mediated reactions", "Pneumonitis", "Colitis"],
                contraindications=["Severe autoimmune disease"],
                average_monthly_cost=15000.0,
                approval_year=2014,
                market_share_percent=25.0,
            ),
            ComparatorDrug(
                drug_name="Paclitaxel",
                drug_id="CHEMBL428647",
                mechanism="Microtubule stabilizer; inhibits cell division",
                administration_route="IV infusion",
                dosing_frequency="weekly or every 3 weeks",
                age_restrictions="Adults",
                key_side_effects=["Neutropenia", "Peripheral neuropathy", "Alopecia", "Nausea"],
                contraindications=["Severe neutropenia", "Hypersensitivity"],
                average_monthly_cost=2500.0,
                approval_year=1992,
                market_share_percent=15.0,
            ),
        ],
        "hypertension": [
            ComparatorDrug(
                drug_name="Lisinopril",
                drug_id="CHEMBL1237021",
                mechanism="ACE inhibitor",
                administration_route="oral",
                dosing_frequency="once daily",
                age_restrictions="Adults; pediatric for certain indications",
                key_side_effects=["Dry cough", "Hyperkalemia", "Angioedema (rare)", "Dizziness"],
                contraindications=["Pregnancy", "Angioedema history", "Bilateral renal artery stenosis"],
                average_monthly_cost=10.0,
                approval_year=1987,
                market_share_percent=20.0,
            ),
            ComparatorDrug(
                drug_name="Amlodipine",
                drug_id="CHEMBL1491",
                mechanism="Calcium channel blocker",
                administration_route="oral",
                dosing_frequency="once daily",
                age_restrictions="Adults 18+ years",
                key_side_effects=["Peripheral edema", "Headache", "Fatigue", "Flushing"],
                contraindications=["Severe aortic stenosis", "Cardiogenic shock"],
                average_monthly_cost=12.0,
                approval_year=1987,
                market_share_percent=18.0,
            ),
        ],
        "depression": [
            ComparatorDrug(
                drug_name="Sertraline (Zoloft)",
                drug_id="CHEMBL809",
                mechanism="Selective serotonin reuptake inhibitor (SSRI)",
                administration_route="oral",
                dosing_frequency="once daily",
                age_restrictions="Adults and children 6+ (OCD)",
                key_side_effects=["Nausea", "Insomnia", "Sexual dysfunction", "Weight changes"],
                contraindications=["MAOIs use", "Pimozide use"],
                average_monthly_cost=15.0,
                approval_year=1991,
                market_share_percent=22.0,
            ),
            ComparatorDrug(
                drug_name="Venlafaxine (Effexor)",
                drug_id="CHEMBL637",
                mechanism="Serotonin-norepinephrine reuptake inhibitor (SNRI)",
                administration_route="oral",
                dosing_frequency="once daily (XR)",
                age_restrictions="Adults 18+ years",
                key_side_effects=["Nausea", "Headache", "Dry mouth", "Withdrawal symptoms"],
                contraindications=["MAOIs use", "Uncontrolled hypertension"],
                average_monthly_cost=25.0,
                approval_year=1993,
                market_share_percent=15.0,
            ),
            ComparatorDrug(
                drug_name="Esketamine (Spravato)",
                drug_id="CHEMBL4297507",
                mechanism="NMDA receptor antagonist",
                administration_route="intranasal",
                dosing_frequency="twice weekly initially",
                age_restrictions="Adults 18+ years",
                key_side_effects=["Dissociation", "Sedation", "Dizziness", "Increased BP"],
                contraindications=["Aneurysmal vascular disease", "AV malformation"],
                average_monthly_cost=2500.0,
                approval_year=2019,
                market_share_percent=3.0,
            ),
        ],
        "alzheimer": [
            ComparatorDrug(
                drug_name="Donepezil (Aricept)",
                drug_id="CHEMBL502",
                mechanism="Acetylcholinesterase inhibitor",
                administration_route="oral",
                dosing_frequency="once daily",
                age_restrictions="Adults",
                key_side_effects=["Nausea", "Diarrhea", "Insomnia", "Muscle cramps"],
                contraindications=["Known hypersensitivity"],
                average_monthly_cost=350.0,
                approval_year=1996,
                market_share_percent=40.0,
            ),
            ComparatorDrug(
                drug_name="Lecanemab (Leqembi)",
                drug_id="CHEMBL4650406",
                mechanism="Anti-amyloid beta antibody",
                administration_route="IV infusion",
                dosing_frequency="every 2 weeks",
                age_restrictions="Adults with early Alzheimer's",
                key_side_effects=["ARIA (brain swelling/bleeding)", "Infusion reactions", "Headache"],
                contraindications=["APOE4 homozygotes (higher ARIA risk)"],
                average_monthly_cost=26500.0,
                approval_year=2023,
                market_share_percent=5.0,
            ),
        ],
        "obesity": [
            ComparatorDrug(
                drug_name="Semaglutide (Wegovy)",
                drug_id="CHEMBL3545011",
                mechanism="GLP-1 receptor agonist",
                administration_route="subcutaneous injection",
                dosing_frequency="once weekly",
                age_restrictions="Adults and adolescents 12+",
                key_side_effects=["Nausea", "Vomiting", "Diarrhea", "Pancreatitis risk"],
                contraindications=["MTC history", "MEN 2 syndrome"],
                average_monthly_cost=1350.0,
                approval_year=2021,
                market_share_percent=50.0,
            ),
            ComparatorDrug(
                drug_name="Phentermine-Topiramate (Qsymia)",
                drug_id="CHEMBL2107830",
                mechanism="Appetite suppressant + anticonvulsant",
                administration_route="oral",
                dosing_frequency="once daily",
                age_restrictions="Adults 18+ years",
                key_side_effects=["Paresthesia", "Dry mouth", "Constipation", "Insomnia"],
                contraindications=["Pregnancy", "Glaucoma", "Hyperthyroidism", "MAOIs"],
                average_monthly_cost=200.0,
                approval_year=2012,
                market_share_percent=15.0,
            ),
        ],
        "rheumatoid arthritis": [
            ComparatorDrug(
                drug_name="Methotrexate",
                drug_id="CHEMBL34259",
                mechanism="Antimetabolite; immunosuppressant",
                administration_route="oral or subcutaneous",
                dosing_frequency="once weekly",
                age_restrictions="Adults; some pediatric indications",
                key_side_effects=["Nausea", "Hepatotoxicity", "Bone marrow suppression", "Mucositis"],
                contraindications=["Pregnancy", "Severe renal impairment", "Active infection"],
                average_monthly_cost=50.0,
                approval_year=1988,
                market_share_percent=30.0,
            ),
            ComparatorDrug(
                drug_name="Adalimumab (Humira)",
                drug_id="CHEMBL1201580",
                mechanism="TNF-alpha inhibitor",
                administration_route="subcutaneous injection",
                dosing_frequency="every 2 weeks",
                age_restrictions="Adults and children 2+",
                key_side_effects=["Injection site reactions", "Infections", "Headache"],
                contraindications=["Active infections", "TB history"],
                average_monthly_cost=6500.0,
                approval_year=2002,
                market_share_percent=25.0,
            ),
        ],
        "asthma": [
            ComparatorDrug(
                drug_name="Fluticasone/Salmeterol (Advair)",
                drug_id="CHEMBL1201831",
                mechanism="Inhaled corticosteroid + LABA",
                administration_route="inhalation",
                dosing_frequency="twice daily",
                age_restrictions="Adults and children 4+",
                key_side_effects=["Oral thrush", "Hoarseness", "Headache"],
                contraindications=["Primary treatment of acute asthma"],
                average_monthly_cost=350.0,
                approval_year=2000,
                market_share_percent=20.0,
            ),
            ComparatorDrug(
                drug_name="Dupilumab (Dupixent)",
                drug_id="CHEMBL3137331",
                mechanism="IL-4/IL-13 inhibitor",
                administration_route="subcutaneous injection",
                dosing_frequency="every 2 weeks",
                age_restrictions="Adults and children 6+",
                key_side_effects=["Injection site reactions", "Conjunctivitis", "Eosinophilia"],
                contraindications=["Known hypersensitivity"],
                average_monthly_cost=3500.0,
                approval_year=2018,
                market_share_percent=10.0,
            ),
        ],
        "pulmonary hypertension": [
            ComparatorDrug(
                drug_name="Bosentan (Tracleer)",
                drug_id="CHEMBL944",
                mechanism="Endothelin receptor antagonist",
                administration_route="oral",
                dosing_frequency="twice daily",
                age_restrictions="Adults and children 3+",
                key_side_effects=["Hepatotoxicity", "Edema", "Anemia", "Headache"],
                contraindications=["Pregnancy", "Severe hepatic impairment"],
                average_monthly_cost=4500.0,
                approval_year=2001,
                market_share_percent=25.0,
            ),
            ComparatorDrug(
                drug_name="Tadalafil (Adcirca)",
                drug_id="CHEMBL779",
                mechanism="PDE5 inhibitor",
                administration_route="oral",
                dosing_frequency="once daily",
                age_restrictions="Adults",
                key_side_effects=["Headache", "Myalgia", "Flushing", "Dyspepsia"],
                contraindications=["Nitrate use", "Severe renal/hepatic impairment"],
                average_monthly_cost=3000.0,
                approval_year=2009,
                market_share_percent=20.0,
            ),
        ],
    }

    # Known drug characteristics for candidate analysis
    DRUG_CHARACTERISTICS = {
        "metformin": {
            "administration_route": "oral",
            "dosing_frequency": "twice daily",
            "age_range": "10-80 years",
            "key_side_effects": ["Nausea", "Diarrhea", "Vitamin B12 deficiency"],
            "mechanism": "Biguanide; reduces hepatic glucose production, improves insulin sensitivity",
        },
        "sildenafil": {
            "administration_route": "oral",
            "dosing_frequency": "as needed or three times daily (PAH)",
            "age_range": "18-65 years (ED), all adults (PAH)",
            "key_side_effects": ["Headache", "Flushing", "Visual disturbances", "Dyspepsia"],
            "mechanism": "PDE5 inhibitor; increases cGMP, causing vasodilation",
        },
        "aspirin": {
            "administration_route": "oral",
            "dosing_frequency": "once daily",
            "age_range": "All ages with caution in children (Reye's syndrome risk)",
            "key_side_effects": ["GI bleeding", "Tinnitus", "Bruising"],
            "mechanism": "COX inhibitor; anti-inflammatory, antiplatelet",
        },
        "thalidomide": {
            "administration_route": "oral",
            "dosing_frequency": "once daily",
            "age_range": "Adults only (severe teratogenicity)",
            "key_side_effects": ["Teratogenicity", "Peripheral neuropathy", "Thromboembolism"],
            "mechanism": "Immunomodulatory; anti-angiogenic, TNF-alpha inhibitor",
        },
        "minoxidil": {
            "administration_route": "topical or oral",
            "dosing_frequency": "twice daily (topical)",
            "age_range": "Adults 18-65 years",
            "key_side_effects": ["Hypertrichosis", "Hypotension", "Edema"],
            "mechanism": "Potassium channel opener; vasodilator",
        },
        "finasteride": {
            "administration_route": "oral",
            "dosing_frequency": "once daily",
            "age_range": "Adult males only",
            "key_side_effects": ["Sexual dysfunction", "Gynecomastia", "Depression (rare)"],
            "mechanism": "5-alpha reductase inhibitor; reduces DHT",
        },
        "gabapentin": {
            "administration_route": "oral",
            "dosing_frequency": "three times daily",
            "age_range": "Adults and children 3+ (seizures)",
            "key_side_effects": ["Dizziness", "Somnolence", "Peripheral edema", "Weight gain"],
            "mechanism": "Calcium channel alpha-2-delta ligand",
        },
        "amantadine": {
            "administration_route": "oral",
            "dosing_frequency": "once or twice daily",
            "age_range": "Adults and children 1+",
            "key_side_effects": ["Livedo reticularis", "Hallucinations", "Insomnia"],
            "mechanism": "NMDA antagonist; dopamine release enhancer",
        },
    }

    def __init__(self):
        """Initialize the comparative analyzer."""
        self.opentargets_url = "https://api.platform.opentargets.org/api/v4/graphql"
        self.openfda_url = "https://api.fda.gov/drug/event.json"

    async def get_comparator_drugs(
        self,
        indication: str,
        max_comparators: int = 5
    ) -> List[ComparatorDrug]:
        """
        Get current standard of care treatments for an indication.

        Args:
            indication: Disease/indication name
            max_comparators: Maximum number of comparators to return

        Returns:
            List of ComparatorDrug objects
        """
        indication_lower = indication.lower()

        # First check curated data
        for key, comparators in self.CURATED_COMPARATORS.items():
            if key in indication_lower or indication_lower in key:
                logger.info(f"Found {len(comparators)} curated comparators for '{indication}'")
                return comparators[:max_comparators]

        # Try to fetch from OpenTargets
        try:
            comparators = await self._fetch_opentargets_comparators(indication)
            if comparators:
                return comparators[:max_comparators]
        except Exception as e:
            logger.warning(f"Failed to fetch OpenTargets comparators: {e}")

        # Return empty list if nothing found
        logger.info(f"No comparators found for '{indication}'")
        return []

    async def _fetch_opentargets_comparators(self, indication: str) -> List[ComparatorDrug]:
        """Fetch approved drugs for an indication from OpenTargets."""
        query = """
        query DiseaseAssociations($disease: String!) {
            search(queryString: $disease, entityNames: ["disease"]) {
                hits {
                    id
                    name
                    entity
                }
            }
        }
        """

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.opentargets_url,
                    json={"query": query, "variables": {"disease": indication}},
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Parse and return comparator drugs
                        # Note: This is a simplified implementation
                        return []
        except Exception as e:
            logger.warning(f"OpenTargets query failed: {e}")

        return []

    def get_candidate_characteristics(self, drug_name: str) -> Dict[str, Any]:
        """Get known characteristics for a candidate drug."""
        drug_lower = drug_name.lower()

        for name, chars in self.DRUG_CHARACTERISTICS.items():
            if name in drug_lower or drug_lower in name:
                return chars

        # Default characteristics
        return {
            "administration_route": "oral",
            "dosing_frequency": "varies",
            "age_range": "Adults",
            "key_side_effects": [],
            "mechanism": "Unknown",
        }

    async def analyze_advantages(
        self,
        drug_name: str,
        indication: str,
        comparators: List[ComparatorDrug]
    ) -> List[ComparativeAdvantage]:
        """
        Analyze specific advantages of candidate drug over comparators.

        Args:
            drug_name: Name of the candidate drug
            indication: Target indication
            comparators: List of comparator drugs

        Returns:
            List of ComparativeAdvantage objects
        """
        advantages = []
        candidate_chars = self.get_candidate_characteristics(drug_name)

        for comparator in comparators:
            # Administration route comparison
            adv = self._compare_administration(drug_name, candidate_chars, comparator)
            if adv:
                advantages.append(adv)

            # Dosing frequency comparison
            adv = self._compare_dosing(drug_name, candidate_chars, comparator)
            if adv:
                advantages.append(adv)

            # Cost comparison
            adv = self._compare_cost(drug_name, comparator)
            if adv:
                advantages.append(adv)

            # Side effect profile comparison
            adv = self._compare_side_effects_briefly(drug_name, candidate_chars, comparator)
            if adv:
                advantages.append(adv)

        # Deduplicate and rank
        return self._deduplicate_advantages(advantages)

    def _compare_administration(
        self,
        drug_name: str,
        candidate_chars: Dict,
        comparator: ComparatorDrug
    ) -> Optional[ComparativeAdvantage]:
        """Compare administration routes."""
        candidate_route = candidate_chars.get("administration_route", "oral")
        comparator_route = comparator.administration_route

        # Define route hierarchy (lower = more convenient for patient)
        route_scores = {
            "oral": 1,
            "topical": 2,
            "inhalation": 3,
            "intranasal": 4,
            "subcutaneous injection": 5,
            "intramuscular injection": 6,
            "iv infusion": 7,
            "iv injection": 7,
        }

        candidate_score = route_scores.get(candidate_route.lower(), 5)
        comparator_score = route_scores.get(comparator_route.lower(), 5)

        if candidate_score < comparator_score:
            impact = "high" if comparator_score - candidate_score >= 3 else "medium"
            return ComparativeAdvantage(
                category="administration",
                advantage_type=f"{candidate_route.title()} vs {comparator_route.title()}",
                description=f"{drug_name} offers more convenient {candidate_route} administration compared to {comparator.drug_name}'s {comparator_route} route, improving patient compliance and reducing healthcare resource utilization.",
                comparator_drug=comparator.drug_name,
                comparator_value=comparator_route,
                candidate_value=candidate_route,
                impact=impact,
                patient_benefit="Improved convenience and adherence",
            )

        return None

    def _compare_dosing(
        self,
        drug_name: str,
        candidate_chars: Dict,
        comparator: ComparatorDrug
    ) -> Optional[ComparativeAdvantage]:
        """Compare dosing frequencies."""
        candidate_freq = candidate_chars.get("dosing_frequency", "daily")
        comparator_freq = comparator.dosing_frequency

        # Define frequency hierarchy (higher = less frequent = better)
        freq_scores = {
            "four times daily": 1,
            "three times daily": 2,
            "twice daily": 3,
            "once daily": 4,
            "daily": 4,
            "every other day": 5,
            "twice weekly": 6,
            "once weekly": 7,
            "weekly": 7,
            "every 2 weeks": 8,
            "every 3 weeks": 9,
            "monthly": 10,
            "once monthly": 10,
        }

        candidate_score = freq_scores.get(candidate_freq.lower(), 4)
        comparator_score = freq_scores.get(comparator_freq.lower(), 4)

        if candidate_score > comparator_score:
            impact = "high" if candidate_score - comparator_score >= 3 else "medium"
            return ComparativeAdvantage(
                category="dosing",
                advantage_type=f"{candidate_freq.title()} vs {comparator_freq.title()}",
                description=f"{drug_name} requires less frequent dosing ({candidate_freq}) compared to {comparator.drug_name} ({comparator_freq}), reducing pill burden and improving patient adherence.",
                comparator_drug=comparator.drug_name,
                comparator_value=comparator_freq,
                candidate_value=candidate_freq,
                impact=impact,
                patient_benefit="Reduced dosing burden",
            )

        return None

    def _compare_cost(
        self,
        drug_name: str,
        comparator: ComparatorDrug
    ) -> Optional[ComparativeAdvantage]:
        """Compare treatment costs."""
        # Most repurposed drugs are generics with lower costs
        if comparator.average_monthly_cost and comparator.average_monthly_cost > 500:
            # Estimate candidate cost (repurposed drugs often much cheaper)
            estimated_cost = 50  # Generic estimate

            savings_percent = ((comparator.average_monthly_cost - estimated_cost) / comparator.average_monthly_cost) * 100

            if savings_percent > 50:
                return ComparativeAdvantage(
                    category="access",
                    advantage_type="Cost Savings",
                    description=f"{drug_name} as a repurposed generic could offer significant cost savings (~{savings_percent:.0f}% reduction) compared to {comparator.drug_name} (${comparator.average_monthly_cost:,.0f}/month), improving patient access.",
                    comparator_drug=comparator.drug_name,
                    comparator_value=f"${comparator.average_monthly_cost:,.0f}/month",
                    candidate_value=f"~${estimated_cost}/month (estimated)",
                    impact="high",
                    patient_benefit="Lower treatment costs, improved access",
                )

        return None

    def _compare_side_effects_briefly(
        self,
        drug_name: str,
        candidate_chars: Dict,
        comparator: ComparatorDrug
    ) -> Optional[ComparativeAdvantage]:
        """Brief comparison of side effect profiles."""
        candidate_effects = set(e.lower() for e in candidate_chars.get("key_side_effects", []))
        comparator_effects = set(e.lower() for e in comparator.key_side_effects)

        # Find effects unique to comparator (potential safety advantage)
        avoided_effects = comparator_effects - candidate_effects

        severe_effects = {"hepatotoxicity", "pancreatitis", "neutropenia", "thromboembolism",
                         "aria", "pneumonitis", "colitis", "lactic acidosis"}

        severe_avoided = avoided_effects.intersection(severe_effects)

        if severe_avoided:
            return ComparativeAdvantage(
                category="safety",
                advantage_type="Improved Safety Profile",
                description=f"{drug_name} may avoid serious adverse effects associated with {comparator.drug_name}: {', '.join(severe_avoided)}.",
                comparator_drug=comparator.drug_name,
                comparator_value=f"Risk of {', '.join(severe_avoided)}",
                candidate_value="Lower risk of these effects",
                impact="high",
                patient_benefit="Potentially safer treatment option",
            )

        return None

    def _deduplicate_advantages(
        self,
        advantages: List[ComparativeAdvantage]
    ) -> List[ComparativeAdvantage]:
        """Remove duplicate advantages and sort by impact."""
        seen = set()
        unique = []

        for adv in advantages:
            key = (adv.category, adv.advantage_type)
            if key not in seen:
                seen.add(key)
                unique.append(adv)

        # Sort by impact (high first)
        impact_order = {"high": 0, "medium": 1, "low": 2}
        unique.sort(key=lambda x: impact_order.get(x.impact, 1))

        return unique

    async def compare_side_effects(
        self,
        candidate_drug: str,
        comparator: Optional[ComparatorDrug],
        indication: str
    ) -> Optional[SideEffectComparison]:
        """
        Compare side effect profiles between candidate and comparator.

        Args:
            candidate_drug: Name of candidate drug
            comparator: Comparator drug to compare against
            indication: Target indication

        Returns:
            SideEffectComparison object or None
        """
        if not comparator:
            return None

        candidate_chars = self.get_candidate_characteristics(candidate_drug)
        candidate_effects = candidate_chars.get("key_side_effects", [])
        comparator_effects = comparator.key_side_effects

        # Find eliminated, shared, and new effects
        candidate_set = set(e.lower() for e in candidate_effects)
        comparator_set = set(e.lower() for e in comparator_effects)

        eliminated = comparator_set - candidate_set
        shared = comparator_set.intersection(candidate_set)
        new_concerns = candidate_set - comparator_set

        # Create side effect entries
        eliminated_entries = [
            SideEffectEntry(effect_name=e.title(), severity="moderate", category="general")
            for e in eliminated
        ]

        new_entries = [
            SideEffectEntry(effect_name=e.title(), severity="moderate", category="general")
            for e in new_concerns
        ]

        # Calculate safety advantage score
        safety_score = (len(eliminated) - len(new_concerns)) / max(len(comparator_effects), 1)
        safety_score = max(-1.0, min(1.0, safety_score))

        # Generate summary
        if safety_score > 0.3:
            summary = f"{candidate_drug} shows a favorable safety profile compared to {comparator.drug_name}, potentially eliminating {len(eliminated)} adverse effects."
        elif safety_score < -0.3:
            summary = f"{candidate_drug} may introduce {len(new_concerns)} new adverse effects compared to {comparator.drug_name}."
        else:
            summary = f"{candidate_drug} has a comparable safety profile to {comparator.drug_name}."

        return SideEffectComparison(
            indication=indication,
            candidate_drug=candidate_drug,
            comparator_drug=comparator.drug_name,
            eliminated_effects=eliminated_entries,
            reduced_effects=[],
            new_concerns=new_entries,
            shared_effects=list(shared),
            safety_advantage_score=safety_score,
            safety_summary=summary,
        )

    async def analyze_full_comparison(
        self,
        drug_name: str,
        indication: str
    ) -> Tuple[List[ComparatorDrug], List[ComparativeAdvantage], Optional[SideEffectComparison]]:
        """
        Perform full comparative analysis for a drug-indication pair.

        Args:
            drug_name: Candidate drug name
            indication: Target indication

        Returns:
            Tuple of (comparators, advantages, side_effect_comparison)
        """
        # Get comparators
        comparators = await self.get_comparator_drugs(indication)

        if not comparators:
            return [], [], None

        # Analyze advantages
        advantages = await self.analyze_advantages(drug_name, indication, comparators)

        # Compare side effects with primary comparator
        side_effect_comparison = await self.compare_side_effects(
            drug_name,
            comparators[0] if comparators else None,
            indication
        )

        return comparators, advantages, side_effect_comparison


# Singleton instance
_analyzer_instance = None


def get_comparative_analyzer() -> ComparativeAnalyzer:
    """Get singleton instance of ComparativeAnalyzer."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ComparativeAnalyzer()
    return _analyzer_instance
