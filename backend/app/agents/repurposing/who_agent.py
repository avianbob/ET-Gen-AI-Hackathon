"""
WHO Agent - Checks WHO Essential Medicines List and global health data.
Provides information about drug's global health significance.
"""

from typing import List, Dict, Any, Optional
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem, AgentResponse
from app.services.repurpose.utils.logger import get_logger
from app.repurpose_settings import settings

logger = get_logger("agents.who")


class WHOAgent(BaseAgent):
    """
    Agent for checking WHO Essential Medicines List status.
    Also provides global health burden information for indications.
    """

    name = "WHOAgent"
    description = "Checks WHO Essential Medicines List and global health significance"

    # WHO Essential Medicines List (EML) 2023 - Curated subset of common drugs
    # Full list at: https://list.essentialmeds.org/
    ESSENTIAL_MEDICINES = {
        "metformin": {
            "eml_section": "18.5",
            "category": "Medicines used in diabetes",
            "formulations": ["tablet 500mg", "tablet 850mg", "oral liquid 500mg/5ml"],
            "core": True,
            "notes": "First-line treatment for type 2 diabetes"
        },
        "aspirin": {
            "eml_section": "2.1",
            "category": "Anti-inflammatory and antirheumatic medicines",
            "formulations": ["tablet 100mg to 500mg"],
            "core": True,
            "notes": "Also used as antiplatelet agent"
        },
        "ibuprofen": {
            "eml_section": "2.1",
            "category": "Anti-inflammatory and antirheumatic medicines",
            "formulations": ["tablet 200mg", "tablet 400mg"],
            "core": True,
            "notes": "NSAID for pain and inflammation"
        },
        "omeprazole": {
            "eml_section": "17.1",
            "category": "Medicines for peptic ulcer",
            "formulations": ["capsule 20mg"],
            "core": True,
            "notes": "Proton pump inhibitor"
        },
        "atorvastatin": {
            "eml_section": "12.6",
            "category": "Lipid-lowering agents",
            "formulations": ["tablet 10mg", "tablet 20mg", "tablet 40mg"],
            "core": True,
            "notes": "HMG-CoA reductase inhibitor for cardiovascular prevention"
        },
        "amlodipine": {
            "eml_section": "12.3",
            "category": "Antihypertensive medicines",
            "formulations": ["tablet 5mg"],
            "core": True,
            "notes": "Calcium channel blocker"
        },
        "lisinopril": {
            "eml_section": "12.3",
            "category": "Antihypertensive medicines",
            "formulations": ["tablet 5mg", "tablet 10mg"],
            "core": True,
            "notes": "ACE inhibitor"
        },
        "prednisone": {
            "eml_section": "8.3",
            "category": "Hormones and antihormones",
            "formulations": ["tablet 5mg", "tablet 25mg"],
            "core": True,
            "notes": "Corticosteroid for inflammation and immunosuppression"
        },
        "doxycycline": {
            "eml_section": "6.2.2",
            "category": "Antibacterials - Tetracyclines",
            "formulations": ["capsule 100mg"],
            "core": True,
            "notes": "Broad-spectrum antibiotic"
        },
        "amoxicillin": {
            "eml_section": "6.2.1",
            "category": "Antibacterials - Beta-lactams",
            "formulations": ["capsule 250mg", "capsule 500mg"],
            "core": True,
            "notes": "First-line antibiotic for many infections"
        },
        "ciprofloxacin": {
            "eml_section": "6.2.4",
            "category": "Antibacterials - Fluoroquinolones",
            "formulations": ["tablet 250mg", "tablet 500mg"],
            "core": True,
            "notes": "Broad-spectrum fluoroquinolone"
        },
        "levothyroxine": {
            "eml_section": "18.8",
            "category": "Thyroid hormones and antithyroid medicines",
            "formulations": ["tablet 25mcg to 200mcg"],
            "core": True,
            "notes": "Thyroid hormone replacement"
        },
        "losartan": {
            "eml_section": "12.3",
            "category": "Antihypertensive medicines",
            "formulations": ["tablet 25mg", "tablet 50mg"],
            "core": True,
            "notes": "Angiotensin receptor blocker"
        },
        "gabapentin": {
            "eml_section": "5",
            "category": "Anticonvulsants/Antiepileptics",
            "formulations": ["capsule 100mg", "capsule 300mg", "capsule 400mg"],
            "core": False,
            "notes": "Also used for neuropathic pain"
        },
        "sildenafil": {
            "eml_section": "12.5",
            "category": "Medicines used in pulmonary arterial hypertension",
            "formulations": ["tablet 25mg"],
            "core": True,
            "notes": "Phosphodiesterase inhibitor"
        }
    }

    # Global Disease Burden data (WHO estimates)
    DISEASE_BURDEN = {
        "diabetes": {
            "global_prevalence_millions": 537,
            "deaths_per_year_millions": 1.5,
            "dalys_millions": 67,
            "trend": "increasing",
            "who_priority": "high"
        },
        "cardiovascular": {
            "global_prevalence_millions": 523,
            "deaths_per_year_millions": 17.9,
            "dalys_millions": 393,
            "trend": "stable",
            "who_priority": "high"
        },
        "cancer": {
            "global_prevalence_millions": 50,
            "deaths_per_year_millions": 10,
            "dalys_millions": 250,
            "trend": "increasing",
            "who_priority": "high"
        },
        "respiratory": {
            "global_prevalence_millions": 545,
            "deaths_per_year_millions": 4,
            "dalys_millions": 112,
            "trend": "stable",
            "who_priority": "medium"
        },
        "mental_health": {
            "global_prevalence_millions": 970,
            "deaths_per_year_millions": 0.7,
            "dalys_millions": 125,
            "trend": "increasing",
            "who_priority": "high"
        },
        "infectious": {
            "global_prevalence_millions": 2000,
            "deaths_per_year_millions": 13,
            "dalys_millions": 500,
            "trend": "decreasing",
            "who_priority": "high"
        },
        "neurological": {
            "global_prevalence_millions": 1000,
            "deaths_per_year_millions": 9,
            "dalys_millions": 276,
            "trend": "increasing",
            "who_priority": "medium"
        }
    }

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.rate_limit = getattr(settings, 'WHO_RATE_LIMIT', 1.0)

    async def fetch_data(self, drug_name: str, context: Dict[str, Any] = None) -> List[Dict]:
        """
        Check drug against WHO Essential Medicines List.

        Args:
            drug_name: Name of the drug to search
            context: Optional search context

        Returns:
            List of WHO data items
        """
        self.logger.info(f"Checking WHO data for: {drug_name}")
        results = []

        # Normalize drug name for lookup
        drug_key = drug_name.lower().strip()

        # Check Essential Medicines List
        eml_data = self._check_essential_medicines(drug_key)
        if eml_data:
            results.append({
                "type": "essential_medicine",
                "data": eml_data
            })

        # Get therapeutic category disease burden
        if eml_data:
            category = eml_data.get("category", "").lower()
            burden_data = self._get_disease_burden(category)
            if burden_data:
                results.append({
                    "type": "disease_burden",
                    "data": burden_data
                })

        # Check for similar drugs in EML
        similar_drugs = self._find_similar_drugs(drug_key)
        if similar_drugs:
            results.append({
                "type": "similar_essential_medicines",
                "data": similar_drugs
            })

        self.logger.info(f"Found {len(results)} WHO data items")
        return results

    def _check_essential_medicines(self, drug_name: str) -> Optional[Dict]:
        """Check if drug is on WHO Essential Medicines List."""
        # Direct match
        if drug_name in self.ESSENTIAL_MEDICINES:
            return {**self.ESSENTIAL_MEDICINES[drug_name], "drug_name": drug_name}

        # Partial match
        for name, data in self.ESSENTIAL_MEDICINES.items():
            if drug_name in name or name in drug_name:
                return {**data, "drug_name": name}

        return None

    def _get_disease_burden(self, category: str) -> Optional[Dict]:
        """Get WHO disease burden data for a therapeutic category."""
        category_lower = category.lower()

        mappings = {
            "diabetes": ["diabetes", "glycemic", "insulin"],
            "cardiovascular": ["cardiovascular", "heart", "hypertensive", "lipid"],
            "cancer": ["cancer", "antineoplastic", "oncology"],
            "respiratory": ["respiratory", "asthma", "copd", "pulmonary"],
            "mental_health": ["mental", "psychiatric", "depression", "anxiety", "psychotic"],
            "infectious": ["antibacterial", "antiviral", "antibiotic", "antimicrobial", "infection"],
            "neurological": ["neurological", "anticonvulsant", "antiepileptic", "parkinson"]
        }

        for burden_key, keywords in mappings.items():
            if any(kw in category_lower for kw in keywords):
                return {**self.DISEASE_BURDEN[burden_key], "category": burden_key}

        return None

    def _find_similar_drugs(self, drug_name: str) -> List[Dict]:
        """Find similar drugs in the Essential Medicines List."""
        similar = []

        # Get the category of the input drug if known
        input_category = None
        if drug_name in self.ESSENTIAL_MEDICINES:
            input_category = self.ESSENTIAL_MEDICINES[drug_name].get("category")

        # Find drugs in the same category
        for name, data in self.ESSENTIAL_MEDICINES.items():
            if name != drug_name:
                if input_category and data.get("category") == input_category:
                    similar.append({
                        "drug_name": name,
                        "category": data.get("category"),
                        "core": data.get("core")
                    })

        return similar[:5]

    async def process_data(self, raw_data: List[Dict], drug_name: str) -> List[EvidenceItem]:
        """
        Process WHO data into evidence items.

        Args:
            raw_data: Raw WHO data
            drug_name: Name of the drug

        Returns:
            List of evidence items
        """
        evidence_items = []

        for item in raw_data:
            data_type = item.get("type")
            data = item.get("data")

            if data_type == "essential_medicine" and data:
                core_status = "Core" if data.get("core") else "Complementary"
                evidence_items.append(EvidenceItem(
                    source="who",
                    summary=f"{drug_name} is a WHO {core_status.lower()} essential medicine for {data.get('category', 'various conditions')}",
                    title=f"WHO Essential Medicine: {drug_name}",
                    description=f"{drug_name} is on the WHO Model List of Essential Medicines. "
                                f"Section: {data.get('eml_section')}. Category: {data.get('category')}. "
                                f"Status: {core_status} list. {data.get('notes', '')}",
                    url="https://list.essentialmeds.org/",
                    relevance_score=0.9,
                    indication="Essential Medicine",
                    metadata={
                        "data_type": "essential_medicine",
                        "eml_section": data.get("eml_section"),
                        "category": data.get("category"),
                        "formulations": data.get("formulations"),
                        "core": data.get("core"),
                        "notes": data.get("notes")
                    }
                ))

            elif data_type == "disease_burden" and data:
                category = data.get('category', 'Unknown')
                evidence_items.append(EvidenceItem(
                    source="who",
                    summary=f"WHO disease burden data: {data.get('global_prevalence_millions', 0)}M affected globally for {category}",
                    title=f"WHO Disease Burden: {category.title()}",
                    description=f"Global disease burden for {category}: "
                                f"{data.get('global_prevalence_millions', 0)}M affected globally, "
                                f"{data.get('deaths_per_year_millions', 0)}M deaths/year, "
                                f"{data.get('dalys_millions', 0)}M DALYs. "
                                f"Trend: {data.get('trend', 'unknown')}. "
                                f"WHO Priority: {data.get('who_priority', 'unknown')}",
                    url="https://www.who.int/data/gho",
                    relevance_score=0.75,
                    indication=category.title(),
                    metadata={
                        "data_type": "disease_burden",
                        "category": category,
                        "global_prevalence_millions": data.get("global_prevalence_millions"),
                        "deaths_per_year_millions": data.get("deaths_per_year_millions"),
                        "dalys_millions": data.get("dalys_millions"),
                        "trend": data.get("trend"),
                        "who_priority": data.get("who_priority")
                    }
                ))

            elif data_type == "similar_essential_medicines" and data:
                for similar in data[:3]:
                    similar_name = similar.get('drug_name', 'Unknown')
                    similar_category = similar.get('category', 'Unknown')
                    evidence_items.append(EvidenceItem(
                        source="who",
                        summary=f"Related WHO essential medicine: {similar_name} in {similar_category}",
                        title=f"Related Essential Medicine: {similar_name}",
                        description=f"Related drug in same therapeutic category: {similar_category}. "
                                    f"{'Core' if similar.get('core') else 'Complementary'} essential medicine.",
                        url="https://list.essentialmeds.org/",
                        relevance_score=0.5,
                        indication=similar_category,
                        metadata={
                            "data_type": "similar_essential_medicine",
                            "drug_name": similar_name,
                            "category": similar_category,
                            "core": similar.get("core")
                        }
                    ))

        self.logger.info(f"Processed {len(evidence_items)} evidence items from WHO data")
        return evidence_items
