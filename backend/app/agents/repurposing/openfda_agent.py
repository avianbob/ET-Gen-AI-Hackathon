"""
OpenFDA Agent - Fetches drug adverse events, labels, and recalls from FDA.
Uses OpenFDA API: https://open.fda.gov/apis/
No API key required, rate limit: 240 requests/minute.
"""

from typing import Dict, List, Any
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem
from app.services.repurpose.utils.api_clients import AsyncHTTPClient, rate_limited
from app.repurpose_settings import settings


class OpenFDAAgent(BaseAgent):
    """Agent for searching OpenFDA for adverse events, labels, and recalls."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = "https://api.fda.gov/drug"
        self.max_results = self.config.get("max_results", 20)

    @rate_limited(settings.OPENFDA_RATE_LIMIT)
    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch adverse events, labels, and recalls from OpenFDA.

        Args:
            drug_name: Drug name to search for
            context: Additional search context

        Returns:
            List of combined results from all endpoints
        """
        drug_name = self._sanitize_drug_name(drug_name)
        results = []

        self.logger.info(f"Searching OpenFDA for: {drug_name}")

        async with AsyncHTTPClient() as client:
            # Fetch adverse events
            ae_results = await self._fetch_adverse_events(client, drug_name)
            results.extend(ae_results)

            # Fetch drug labels
            label_results = await self._fetch_labels(client, drug_name)
            results.extend(label_results)

            # Fetch recalls
            recall_results = await self._fetch_recalls(client, drug_name)
            results.extend(recall_results)

        self.logger.info(f"Found {len(results)} total OpenFDA records")
        return results

    async def _fetch_adverse_events(self, client: AsyncHTTPClient, drug_name: str) -> List[Dict]:
        """Fetch adverse event reports from FAERS."""
        try:
            params = {
                "search": f'patient.drug.medicinalproduct:"{drug_name}"',
                "count": "patient.reaction.reactionmeddrapt.exact",
                "limit": self.max_results
            }
            data = await client.get(f"{self.base_url}/event.json", params=params)
            results = data.get("results", [])

            # Tag results with data type
            for r in results:
                r["_data_type"] = "adverse_event"

            self.logger.debug(f"Found {len(results)} adverse event records")
            return results
        except Exception as e:
            self.logger.warning(f"OpenFDA adverse events error: {e}")
            return []

    async def _fetch_labels(self, client: AsyncHTTPClient, drug_name: str) -> List[Dict]:
        """Fetch drug labels (prescribing information)."""
        try:
            params = {
                "search": f'openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}"',
                "limit": 5
            }
            data = await client.get(f"{self.base_url}/label.json", params=params)
            results = data.get("results", [])

            # Tag results with data type
            for r in results:
                r["_data_type"] = "label"

            self.logger.debug(f"Found {len(results)} label records")
            return results
        except Exception as e:
            self.logger.warning(f"OpenFDA labels error: {e}")
            return []

    async def _fetch_recalls(self, client: AsyncHTTPClient, drug_name: str) -> List[Dict]:
        """Fetch drug recalls and enforcement actions."""
        try:
            params = {
                "search": f'product_description:"{drug_name}"',
                "limit": 10
            }
            data = await client.get(f"{self.base_url}/enforcement.json", params=params)
            results = data.get("results", [])

            # Tag results with data type
            for r in results:
                r["_data_type"] = "recall"

            self.logger.debug(f"Found {len(results)} recall records")
            return results
        except Exception as e:
            self.logger.warning(f"OpenFDA recalls error: {e}")
            return []

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """
        Process OpenFDA data into evidence items.

        Args:
            raw_data: List of OpenFDA results

        Returns:
            List of EvidenceItem objects
        """
        evidence_items = []

        for record in raw_data:
            try:
                data_type = record.get("_data_type", "unknown")

                if data_type == "adverse_event":
                    evidence = self._process_adverse_event(record)
                elif data_type == "label":
                    evidence = self._process_label(record)
                elif data_type == "recall":
                    evidence = self._process_recall(record)
                else:
                    continue

                if evidence:
                    evidence_items.append(evidence)

            except Exception as e:
                self.logger.warning(f"Failed to process OpenFDA record: {e}")
                continue

        return evidence_items

    def _process_adverse_event(self, record: Dict) -> EvidenceItem:
        """Process adverse event count record."""
        reaction = record.get("term", "Unknown reaction")
        count = record.get("count", 0)

        # Extract potential indication from reaction
        indication = self._extract_indication_from_reaction(reaction)

        return EvidenceItem(
            source="openfda",
            indication=indication,
            summary=f"FDA FAERS reports {count:,} cases involving '{reaction}'. "
                    f"High reporting rates may indicate off-label usage patterns worth investigating.",
            date=None,
            url="https://open.fda.gov/data/faers/",
            title=f"FAERS: {reaction}",
            metadata={
                "reaction": reaction,
                "count": count,
                "data_type": "adverse_event"
            },
            relevance_score=self._calculate_ae_relevance(count)
        )

    def _process_label(self, record: Dict) -> EvidenceItem:
        """Process drug label record."""
        openfda = record.get("openfda", {})
        brand_names = openfda.get("brand_name", ["Unknown"])
        brand_name = brand_names[0] if brand_names else "Unknown"

        indications = record.get("indications_and_usage", [""])
        indication_text = indications[0] if indications else ""

        # Extract the primary indication
        indication = self._extract_indication(indication_text) if indication_text else "Unknown Indication"

        return EvidenceItem(
            source="openfda",
            indication=indication,
            summary=f"FDA-approved labeling for {brand_name}: {self._truncate_text(indication_text, 300)}",
            date=None,
            url=f"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query={brand_name}",
            title=f"FDA Label: {brand_name}",
            metadata={
                "brand_name": brand_name,
                "generic_names": openfda.get("generic_name", []),
                "manufacturer": openfda.get("manufacturer_name", []),
                "data_type": "label"
            },
            relevance_score=0.7
        )

    def _process_recall(self, record: Dict) -> EvidenceItem:
        """Process recall/enforcement record."""
        reason = record.get("reason_for_recall", "Unknown reason")
        status = record.get("status", "Unknown")
        classification = record.get("classification", "Unknown")
        recall_date = record.get("recall_initiation_date", "")
        product = record.get("product_description", "Unknown product")

        return EvidenceItem(
            source="openfda",
            indication="Safety Alert",
            summary=f"FDA {classification} recall ({status}): {self._truncate_text(reason, 200)}",
            date=recall_date,
            url="https://www.fda.gov/drugs/drug-safety-and-availability",
            title=f"FDA Recall: {self._truncate_text(product, 50)}",
            metadata={
                "reason": reason,
                "status": status,
                "classification": classification,
                "product_description": product,
                "data_type": "recall"
            },
            relevance_score=self._calculate_recall_relevance(classification)
        )

    def _extract_indication_from_reaction(self, reaction: str) -> str:
        """Map adverse event reaction terms to therapeutic areas."""
        reaction_mapping = {
            "neoplasm": "Cancer",
            "tumour": "Cancer",
            "tumor": "Cancer",
            "malignant": "Cancer",
            "carcinoma": "Cancer",
            "cardiac": "Cardiovascular",
            "heart": "Cardiovascular",
            "myocardial": "Cardiovascular",
            "arrhythmia": "Cardiovascular",
            "hepatic": "Liver Disease",
            "liver": "Liver Disease",
            "hepatotoxicity": "Liver Disease",
            "renal": "Kidney Disease",
            "kidney": "Kidney Disease",
            "nephro": "Kidney Disease",
            "neurological": "Neurological",
            "seizure": "Neurological",
            "neuropathy": "Neurological",
            "psychiatric": "Psychiatric",
            "depression": "Psychiatric",
            "anxiety": "Psychiatric",
            "respiratory": "Respiratory",
            "pulmonary": "Respiratory",
            "dyspnoea": "Respiratory",
            "gastrointestinal": "Gastrointestinal",
            "nausea": "Gastrointestinal",
            "diarrhoea": "Gastrointestinal",
            "dermatological": "Dermatological",
            "rash": "Dermatological",
            "pruritus": "Dermatological",
            "musculoskeletal": "Musculoskeletal",
            "arthralgia": "Musculoskeletal",
            "myalgia": "Musculoskeletal",
            "infection": "Infectious Disease",
            "sepsis": "Infectious Disease",
            "diabetes": "Diabetes",
            "hyperglycaemia": "Diabetes",
            "hypoglycaemia": "Diabetes",
            "hypertension": "Cardiovascular",
            "hypotension": "Cardiovascular"
        }

        reaction_lower = reaction.lower()
        for keyword, indication in reaction_mapping.items():
            if keyword in reaction_lower:
                return indication
        return "Unknown Indication"

    def _calculate_ae_relevance(self, count: int) -> float:
        """Calculate relevance score based on adverse event count."""
        if count > 10000:
            return 0.85
        elif count > 5000:
            return 0.75
        elif count > 1000:
            return 0.65
        elif count > 500:
            return 0.55
        elif count > 100:
            return 0.45
        return 0.35

    def _calculate_recall_relevance(self, classification: str) -> float:
        """Calculate relevance score based on recall classification."""
        classification_scores = {
            "Class I": 0.9,    # Most serious
            "Class II": 0.7,
            "Class III": 0.5   # Least serious
        }
        return classification_scores.get(classification, 0.5)

    async def _perform_connection_test(self) -> Dict[str, Any]:
        """Test connection to OpenFDA API with a minimal query."""
        async with AsyncHTTPClient() as client:
            # Use a minimal query to test connectivity
            params = {
                "search": 'patient.drug.medicinalproduct:"aspirin"',
                "limit": 1
            }
            data = await client.get(f"{self.base_url}/event.json", params=params)
            total = data.get("meta", {}).get("results", {}).get("total", 0)
            return {
                "message": f"OpenFDA API connected successfully",
                "details": {
                    "endpoint": "drug/event",
                    "total_records_available": total,
                    "api_version": data.get("meta", {}).get("disclaimer", "")[:50]
                }
            }
