"""
DrugBank Agent - Fetches comprehensive drug data from DrugBank.
Requires DrugBank API key for full access. Falls back to curated data if unavailable.
"""

from typing import List, Dict, Any, Optional
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem, AgentResponse
from app.services.repurpose.utils.api_clients import AsyncHTTPClient
from app.services.repurpose.utils.logger import get_logger
from app.repurpose_settings import settings

logger = get_logger("agents.drugbank")


class DrugBankAgent(BaseAgent):
    """
    Agent for fetching comprehensive drug data from DrugBank.
    Falls back to curated data if API key is not available.
    """

    name = "DrugBankAgent"
    description = "Fetches comprehensive drug, target, and interaction data from DrugBank"

    # DrugBank API base URL
    DRUGBANK_API_BASE = "https://api.drugbank.com/v1"

    # Curated drug data for common drugs (fallback when API unavailable)
    CURATED_DRUGS = {
        "metformin": {
            "drugbank_id": "DB00331",
            "cas_number": "657-24-9",
            "drug_type": "small molecule",
            "groups": ["approved"],
            "categories": ["Hypoglycemic Agents", "Biguanides"],
            "targets": [
                {"name": "AMP-activated protein kinase", "gene": "PRKAA1", "action": "activator"},
                {"name": "Mitochondrial complex I", "gene": "MT-ND1", "action": "inhibitor"}
            ],
            "indications": ["Type 2 Diabetes Mellitus", "Polycystic Ovary Syndrome", "Prediabetes"],
            "mechanism": "Decreases hepatic glucose production and increases insulin sensitivity",
            "half_life": "4-8.7 hours",
            "bioavailability": "50-60%",
            "toxicity": "LD50 > 5000 mg/kg (oral, mouse). Lactic acidosis is a rare but serious adverse effect."
        },
        "aspirin": {
            "drugbank_id": "DB00945",
            "cas_number": "50-78-2",
            "drug_type": "small molecule",
            "groups": ["approved"],
            "categories": ["Anti-Inflammatory Agents", "Platelet Aggregation Inhibitors", "Antipyretics"],
            "targets": [
                {"name": "Cyclooxygenase-1", "gene": "PTGS1", "action": "inhibitor"},
                {"name": "Cyclooxygenase-2", "gene": "PTGS2", "action": "inhibitor"}
            ],
            "indications": ["Pain", "Fever", "Inflammation", "Myocardial Infarction Prevention", "Stroke Prevention"],
            "mechanism": "Irreversibly inhibits cyclooxygenase, reducing prostaglandin synthesis",
            "half_life": "15-20 minutes (aspirin), 2-3 hours (salicylate)",
            "bioavailability": "80-100%",
            "toxicity": "LD50 200 mg/kg (oral, rat). GI bleeding and Reye's syndrome risks."
        },
        "atorvastatin": {
            "drugbank_id": "DB01076",
            "cas_number": "134523-00-5",
            "drug_type": "small molecule",
            "groups": ["approved"],
            "categories": ["HMG-CoA Reductase Inhibitors", "Anticholesteremic Agents"],
            "targets": [
                {"name": "HMG-CoA reductase", "gene": "HMGCR", "action": "inhibitor"}
            ],
            "indications": ["Hypercholesterolemia", "Cardiovascular Disease Prevention", "Dyslipidemia"],
            "mechanism": "Competitively inhibits HMG-CoA reductase, reducing cholesterol biosynthesis",
            "half_life": "14 hours",
            "bioavailability": "12%",
            "toxicity": "Myopathy and rhabdomyolysis are rare but serious adverse effects."
        },
        "omeprazole": {
            "drugbank_id": "DB00338",
            "cas_number": "73590-58-6",
            "drug_type": "small molecule",
            "groups": ["approved"],
            "categories": ["Proton Pump Inhibitors", "Anti-Ulcer Agents"],
            "targets": [
                {"name": "Potassium-transporting ATPase alpha chain 1", "gene": "ATP4A", "action": "inhibitor"}
            ],
            "indications": ["GERD", "Peptic Ulcer Disease", "H. pylori Eradication", "Zollinger-Ellison Syndrome"],
            "mechanism": "Irreversibly inhibits H+/K+-ATPase in gastric parietal cells",
            "half_life": "0.5-1 hour",
            "bioavailability": "30-40%",
            "toxicity": "Long-term use associated with vitamin B12 deficiency and bone fractures."
        },
        "lisinopril": {
            "drugbank_id": "DB00722",
            "cas_number": "83915-83-7",
            "drug_type": "small molecule",
            "groups": ["approved"],
            "categories": ["ACE Inhibitors", "Antihypertensive Agents"],
            "targets": [
                {"name": "Angiotensin-converting enzyme", "gene": "ACE", "action": "inhibitor"}
            ],
            "indications": ["Hypertension", "Heart Failure", "Diabetic Nephropathy", "Post-MI"],
            "mechanism": "Inhibits ACE, reducing angiotensin II and aldosterone production",
            "half_life": "12 hours",
            "bioavailability": "25%",
            "toxicity": "Angioedema, hyperkalemia, and fetal toxicity are important risks."
        },
        "gabapentin": {
            "drugbank_id": "DB00996",
            "cas_number": "60142-96-3",
            "drug_type": "small molecule",
            "groups": ["approved"],
            "categories": ["Anticonvulsants", "Analgesics"],
            "targets": [
                {"name": "Voltage-gated calcium channel subunit alpha-2/delta-1", "gene": "CACNA2D1", "action": "modulator"}
            ],
            "indications": ["Epilepsy", "Neuropathic Pain", "Postherpetic Neuralgia", "Restless Legs Syndrome"],
            "mechanism": "Binds to alpha-2-delta subunit of voltage-gated calcium channels",
            "half_life": "5-7 hours",
            "bioavailability": "27-60%",
            "toxicity": "CNS depression, respiratory depression when combined with opioids."
        },
        "sildenafil": {
            "drugbank_id": "DB00203",
            "cas_number": "139755-83-2",
            "drug_type": "small molecule",
            "groups": ["approved"],
            "categories": ["Phosphodiesterase 5 Inhibitors", "Vasodilator Agents"],
            "targets": [
                {"name": "Phosphodiesterase 5A", "gene": "PDE5A", "action": "inhibitor"}
            ],
            "indications": ["Erectile Dysfunction", "Pulmonary Arterial Hypertension"],
            "mechanism": "Inhibits PDE5, increasing cGMP and promoting smooth muscle relaxation",
            "half_life": "3-5 hours",
            "bioavailability": "41%",
            "toxicity": "Contraindicated with nitrates. Vision and hearing changes reported."
        },
        "doxycycline": {
            "drugbank_id": "DB00254",
            "cas_number": "564-25-0",
            "drug_type": "small molecule",
            "groups": ["approved"],
            "categories": ["Tetracyclines", "Anti-Bacterial Agents"],
            "targets": [
                {"name": "30S ribosomal subunit", "gene": "rpsL", "action": "inhibitor"}
            ],
            "indications": ["Bacterial Infections", "Acne", "Rosacea", "Malaria Prophylaxis", "Lyme Disease"],
            "mechanism": "Inhibits bacterial protein synthesis by binding 30S ribosomal subunit",
            "half_life": "18-22 hours",
            "bioavailability": "93-100%",
            "toxicity": "Photosensitivity, esophageal irritation, contraindicated in pregnancy."
        },
        "ibuprofen": {
            "drugbank_id": "DB01050",
            "cas_number": "15687-27-1",
            "drug_type": "small molecule",
            "groups": ["approved"],
            "categories": ["NSAIDs", "Anti-Inflammatory Agents", "Cyclooxygenase Inhibitors", "Antipyretics"],
            "targets": [
                {"name": "Cyclooxygenase-1", "gene": "PTGS1", "action": "inhibitor"},
                {"name": "Cyclooxygenase-2", "gene": "PTGS2", "action": "inhibitor"}
            ],
            "indications": ["Pain", "Fever", "Inflammation", "Rheumatoid Arthritis", "Osteoarthritis", "Dysmenorrhea", "Headache", "Dental Pain"],
            "mechanism": "Reversibly inhibits cyclooxygenase-1 and 2 (COX-1 and COX-2) enzymes, reducing prostaglandin synthesis",
            "half_life": "1.8-2 hours",
            "bioavailability": "87-100%",
            "toxicity": "GI bleeding, cardiovascular events with long-term use, renal toxicity. LD50 636 mg/kg (oral, mouse)."
        },
        "naproxen": {
            "drugbank_id": "DB00788",
            "cas_number": "22204-53-1",
            "drug_type": "small molecule",
            "groups": ["approved"],
            "categories": ["NSAIDs", "Anti-Inflammatory Agents", "Cyclooxygenase Inhibitors"],
            "targets": [
                {"name": "Cyclooxygenase-1", "gene": "PTGS1", "action": "inhibitor"},
                {"name": "Cyclooxygenase-2", "gene": "PTGS2", "action": "inhibitor"}
            ],
            "indications": ["Pain", "Inflammation", "Rheumatoid Arthritis", "Osteoarthritis", "Ankylosing Spondylitis", "Gout"],
            "mechanism": "Inhibits prostaglandin synthesis by blocking COX enzymes",
            "half_life": "12-17 hours",
            "bioavailability": "95%",
            "toxicity": "GI bleeding, cardiovascular risk, renal impairment with chronic use."
        },
        "acetaminophen": {
            "drugbank_id": "DB00316",
            "cas_number": "103-90-2",
            "drug_type": "small molecule",
            "groups": ["approved"],
            "categories": ["Analgesics", "Antipyretics"],
            "targets": [
                {"name": "Cyclooxygenase-3", "gene": "PTGS3", "action": "inhibitor"},
                {"name": "Cyclooxygenase-1", "gene": "PTGS1", "action": "weak inhibitor"}
            ],
            "indications": ["Pain", "Fever", "Headache", "Osteoarthritis"],
            "mechanism": "Inhibits prostaglandin synthesis in the CNS, weak peripheral anti-inflammatory effect",
            "half_life": "1-4 hours",
            "bioavailability": "63-89%",
            "toxicity": "Hepatotoxicity with overdose. LD50 338 mg/kg (oral, mouse). Leading cause of acute liver failure."
        },
        "paracetamol": {
            "drugbank_id": "DB00316",
            "cas_number": "103-90-2",
            "drug_type": "small molecule",
            "groups": ["approved"],
            "categories": ["Analgesics", "Antipyretics"],
            "targets": [
                {"name": "Cyclooxygenase-3", "gene": "PTGS3", "action": "inhibitor"},
                {"name": "Cyclooxygenase-1", "gene": "PTGS1", "action": "weak inhibitor"}
            ],
            "indications": ["Pain", "Fever", "Headache", "Osteoarthritis"],
            "mechanism": "Inhibits prostaglandin synthesis in the CNS, weak peripheral anti-inflammatory effect",
            "half_life": "1-4 hours",
            "bioavailability": "63-89%",
            "toxicity": "Hepatotoxicity with overdose. LD50 338 mg/kg (oral, mouse). Leading cause of acute liver failure."
        }
    }

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.rate_limit = getattr(settings, 'DRUGBANK_RATE_LIMIT', 1.0)
        self.api_key = getattr(settings, 'DRUGBANK_API_KEY', None)

    async def fetch_data(self, drug_name: str, context: Dict[str, Any] = None) -> List[Dict]:
        """
        Fetch drug data from DrugBank API or curated data.

        Args:
            drug_name: Name of the drug to search
            context: Optional search context

        Returns:
            List of DrugBank data items
        """
        self.logger.info(f"Fetching DrugBank data for: {drug_name}")
        results = []

        # Try API if key available
        if self.api_key:
            api_results = await self._fetch_from_api(drug_name)
            if api_results:
                return api_results

        # Fall back to curated data
        drug_key = drug_name.lower().strip()
        if drug_key in self.CURATED_DRUGS:
            results.append({
                "type": "drug_info",
                "data": self.CURATED_DRUGS[drug_key]
            })
            self.logger.info(f"Using curated DrugBank data for {drug_name}")
        else:
            # Check for partial matches
            for name, data in self.CURATED_DRUGS.items():
                if drug_key in name or name in drug_key:
                    results.append({
                        "type": "drug_info",
                        "data": data,
                        "matched_name": name
                    })
                    self.logger.info(f"Using curated DrugBank data (partial match: {name})")
                    break

        return results

    async def _fetch_from_api(self, drug_name: str) -> Optional[List[Dict]]:
        """Fetch data from DrugBank API."""
        try:
            async with AsyncHTTPClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json"
                }

                # Search for drug
                search_url = f"{self.DRUGBANK_API_BASE}/drugs"
                params = {"q": drug_name}

                response = await client.get(search_url, headers=headers, params=params)

                if response and isinstance(response, list) and len(response) > 0:
                    drug_data = response[0]
                    return [{
                        "type": "drug_info",
                        "data": drug_data,
                        "from_api": True
                    }]

                return None

        except Exception as e:
            self.logger.warning(f"DrugBank API request failed: {e}")
            return None

    async def process_data(self, raw_data: List[Dict], drug_name: str) -> List[EvidenceItem]:
        """
        Process DrugBank data into evidence items.

        Args:
            raw_data: Raw DrugBank data
            drug_name: Name of the drug

        Returns:
            List of evidence items
        """
        evidence_items = []

        for item in raw_data:
            data = item.get("data", {})
            drugbank_id = data.get("drugbank_id", "Unknown")

            # Main drug info
            evidence_items.append(EvidenceItem(
                source="drugbank",
                summary=f"DrugBank pharmacological profile for {drug_name}: {data.get('drug_type', 'small molecule')}",
                title=f"DrugBank Entry: {drug_name}",
                description=f"DrugBank ID: {drugbank_id}. Type: {data.get('drug_type', 'Unknown')}. "
                            f"Groups: {', '.join(data.get('groups', []))}. "
                            f"Mechanism: {data.get('mechanism', 'Unknown')}",
                url=f"https://go.drugbank.com/drugs/{drugbank_id}",
                relevance_score=0.85,
                indication="Drug Information",
                metadata={
                    "data_type": "drug_info",
                    "drugbank_id": drugbank_id,
                    "cas_number": data.get("cas_number"),
                    "drug_type": data.get("drug_type"),
                    "groups": data.get("groups"),
                    "half_life": data.get("half_life"),
                    "bioavailability": data.get("bioavailability")
                }
            ))

            # Drug targets
            targets = data.get("targets", [])
            for target in targets[:5]:
                target_name = target.get('name', 'Unknown')
                target_action = target.get('action', 'modulator')
                evidence_items.append(EvidenceItem(
                    source="drugbank",
                    summary=f"{drug_name} targets {target_name} as {target_action}",
                    title=f"Drug Target: {target_name}",
                    description=f"{drug_name} acts as {target_action} on "
                                f"{target_name} (Gene: {target.get('gene', 'Unknown')})",
                    url=f"https://go.drugbank.com/drugs/{drugbank_id}",
                    relevance_score=0.8,
                    indication="Target Mechanism",
                    metadata={
                        "data_type": "target",
                        "target_name": target_name,
                        "target_gene": target.get("gene"),
                        "action": target_action
                    }
                ))

            # Indications
            indications = data.get("indications", [])
            for ind in indications:
                evidence_items.append(EvidenceItem(
                    source="drugbank",
                    summary=f"DrugBank indication: {drug_name} is indicated for {ind}",
                    title=f"DrugBank Indication: {ind}",
                    description=f"{drug_name} is indicated for {ind} according to DrugBank",
                    url=f"https://go.drugbank.com/drugs/{drugbank_id}",
                    relevance_score=0.9,
                    indication=ind,
                    metadata={
                        "data_type": "indication",
                        "drugbank_id": drugbank_id,
                        "indication": ind
                    }
                ))

            # Drug categories
            categories = data.get("categories", [])
            if categories:
                evidence_items.append(EvidenceItem(
                    source="drugbank",
                    summary=f"{drug_name} belongs to categories: {', '.join(categories[:3])}",
                    title=f"Drug Categories: {drug_name}",
                    description=f"Therapeutic categories: {', '.join(categories)}",
                    url=f"https://go.drugbank.com/drugs/{drugbank_id}",
                    relevance_score=0.7,
                    indication="Drug Classification",
                    metadata={
                        "data_type": "categories",
                        "categories": categories
                    }
                ))

            # Toxicity info (important for feasibility)
            toxicity = data.get("toxicity")
            if toxicity:
                evidence_items.append(EvidenceItem(
                    source="drugbank",
                    summary=f"Toxicity profile for {drug_name}: known safety considerations",
                    title=f"Toxicity Profile: {drug_name}",
                    description=toxicity,
                    url=f"https://go.drugbank.com/drugs/{drugbank_id}",
                    relevance_score=0.75,
                    indication="Drug Safety",
                    metadata={
                        "data_type": "toxicity",
                        "toxicity_info": toxicity
                    }
                ))

        self.logger.info(f"Processed {len(evidence_items)} evidence items from DrugBank")
        return evidence_items

    async def _perform_connection_test(self) -> Dict[str, Any]:
        """Test connection to DrugBank API or verify curated data is available."""
        if self.api_key:
            # Test API connection
            try:
                async with AsyncHTTPClient() as client:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Accept": "application/json"
                    }
                    # Use a minimal API call
                    search_url = f"{self.DRUGBANK_API_BASE}/drugs"
                    params = {"q": "aspirin", "limit": 1}
                    response = await client.get(search_url, headers=headers, params=params)

                    return {
                        "message": "DrugBank API connected successfully",
                        "details": {
                            "endpoint": self.DRUGBANK_API_BASE,
                            "api_key_configured": True,
                            "results_found": len(response) if isinstance(response, list) else 0
                        }
                    }
            except Exception as e:
                # API failed, fall back to curated data
                return {
                    "message": "DrugBank API unavailable, using curated data",
                    "details": {
                        "api_error": str(e),
                        "api_key_configured": True,
                        "curated_drugs_available": len(self.CURATED_DRUGS),
                        "fallback_mode": True
                    }
                }
        else:
            # No API key, using curated data
            return {
                "message": "DrugBank curated data available (no API key configured)",
                "details": {
                    "api_key_configured": False,
                    "curated_drugs_available": len(self.CURATED_DRUGS),
                    "sample_drugs": list(self.CURATED_DRUGS.keys())[:5]
                }
            }
