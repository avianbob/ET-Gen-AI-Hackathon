"""
OpenTargets Agent - Fetches target validation and disease associations.
Uses OpenTargets Platform GraphQL API: https://platform.opentargets.org/api
No API key required.
"""

from typing import Dict, List, Any, Optional
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem
from app.services.repurpose.utils.api_clients import AsyncHTTPClient, rate_limited
from app.repurpose_settings import settings


class OpenTargetsAgent(BaseAgent):
    """Agent for searching OpenTargets Platform for drug-disease associations."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        # OpenTargets Platform GraphQL API endpoint
        self.graphql_url = "https://api.platform.opentargets.org/api/v4/graphql"
        # GraphQL requests require explicit Content-Type header
        self.graphql_headers = {"Content-Type": "application/json"}

    @rate_limited(settings.OPENTARGETS_RATE_LIMIT)
    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch drug-disease associations from OpenTargets GraphQL API.

        Args:
            drug_name: Drug name to search for
            context: Additional search context

        Returns:
            List of drug-disease association results
        """
        drug_name = self._sanitize_drug_name(drug_name)
        self.logger.info(f"Searching OpenTargets for: {drug_name}")

        results = []

        async with AsyncHTTPClient() as client:
            # First search for the drug
            drug_data = await self._search_drug(client, drug_name)

            if drug_data:
                results.append(drug_data)

        self.logger.info(f"Found {len(results)} OpenTargets records")
        return results

    async def _search_drug(self, client: AsyncHTTPClient, drug_name: str) -> Optional[Dict]:
        """Search for drug and get its associations."""
        query = """
        query DrugSearch($drugName: String!) {
            search(queryString: $drugName, entityNames: ["drug"], page: {size: 5, index: 0}) {
                total
                hits {
                    id
                    name
                    entity
                    description
                }
            }
        }
        """

        try:
            response = await client.post(
                self.graphql_url,
                json={"query": query, "variables": {"drugName": drug_name}},
                headers=self.graphql_headers
            )

            hits = response.get("data", {}).get("search", {}).get("hits", [])

            if not hits:
                self.logger.info(f"No drug found for: {drug_name}")
                return None

            # Get the first matching drug
            drug_hit = None
            for hit in hits:
                if hit.get("entity") == "drug":
                    drug_hit = hit
                    break

            if not drug_hit:
                return None

            drug_id = drug_hit.get("id")
            self.logger.info(f"Found drug: {drug_hit.get('name')} (ID: {drug_id})")

            # Get detailed drug info with indications
            drug_details = await self._get_drug_details(client, drug_id)

            return {
                "drug_id": drug_id,
                "drug_name": drug_hit.get("name"),
                "description": drug_hit.get("description"),
                "details": drug_details
            }

        except Exception as e:
            self.logger.error(f"OpenTargets search error: {e}")
            return None

    async def _get_drug_details(self, client: AsyncHTTPClient, drug_id: str) -> Dict:
        """Get detailed drug information including indications and mechanisms."""
        # Simplified query to avoid API compatibility issues
        query = """
        query DrugDetails($chemblId: String!) {
            drug(chemblId: $chemblId) {
                id
                name
                drugType
                maximumClinicalTrialPhase
                hasBeenWithdrawn
                mechanismsOfAction {
                    rows {
                        mechanismOfAction
                        actionType
                        targets {
                            id
                            approvedSymbol
                            approvedName
                        }
                    }
                }
                indications {
                    count
                    rows {
                        disease {
                            id
                            name
                        }
                        maxPhaseForIndication
                    }
                }
            }
        }
        """

        try:
            response = await client.post(
                self.graphql_url,
                json={"query": query, "variables": {"chemblId": drug_id}},
                headers=self.graphql_headers
            )

            # Handle potential errors in the response
            if "errors" in response:
                self.logger.warning(f"OpenTargets GraphQL errors: {response.get('errors')}")
                return {}

            return response.get("data", {}).get("drug", {})

        except Exception as e:
            self.logger.warning(f"Failed to get drug details: {e}")
            return {}

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """
        Process OpenTargets data into evidence items.

        Args:
            raw_data: List of drug data from OpenTargets

        Returns:
            List of EvidenceItem objects
        """
        evidence_items = []

        for drug_data in raw_data:
            try:
                drug_name = drug_data.get("drug_name", "Unknown")
                drug_id = drug_data.get("drug_id", "")
                details = drug_data.get("details", {})

                # Process indications
                indications = details.get("indications", {}).get("rows", [])
                for ind in indications:
                    evidence = self._process_indication(drug_name, drug_id, ind)
                    if evidence:
                        evidence_items.append(evidence)

                # Process mechanisms of action
                mechanisms = details.get("mechanismsOfAction", {}).get("rows", [])
                for moa in mechanisms:
                    evidence = self._process_mechanism(drug_name, drug_id, moa)
                    if evidence:
                        evidence_items.append(evidence)

                # Process linked diseases (lower confidence)
                linked_diseases = details.get("linkedDiseases", {}).get("rows", [])
                for disease in linked_diseases[:10]:  # Limit to top 10
                    evidence = self._process_linked_disease(drug_name, drug_id, disease)
                    if evidence:
                        evidence_items.append(evidence)

            except Exception as e:
                self.logger.warning(f"Failed to process OpenTargets record: {e}")
                continue

        return evidence_items

    def _process_indication(self, drug_name: str, drug_id: str, indication: Dict) -> Optional[EvidenceItem]:
        """Process an approved/clinical indication."""
        disease = indication.get("disease", {})
        disease_name = disease.get("name", "Unknown")
        disease_id = disease.get("id", "")
        max_phase = indication.get("maxPhaseForIndication", 0)

        # Get therapeutic areas
        therapeutic_areas = disease.get("therapeuticAreas", [])
        ta_names = [ta.get("name") for ta in therapeutic_areas if ta.get("name")]

        phase_text = self._phase_to_text(max_phase)

        return EvidenceItem(
            source="opentargets",
            indication=disease_name,
            summary=f"OpenTargets: {drug_name} has reached {phase_text} for {disease_name}. "
                    f"Target validation data available.",
            date=None,
            url=f"https://platform.opentargets.org/drug/{drug_id}",
            title=f"OpenTargets: {drug_name} - {disease_name}",
            metadata={
                "drug_id": drug_id,
                "disease_id": disease_id,
                "max_phase": max_phase,
                "therapeutic_areas": ta_names,
                "data_type": "indication"
            },
            relevance_score=self._phase_to_relevance(max_phase)
        )

    def _process_mechanism(self, drug_name: str, drug_id: str, mechanism: Dict) -> Optional[EvidenceItem]:
        """Process mechanism of action data."""
        moa_text = mechanism.get("mechanismOfAction", "Unknown mechanism")
        action_type = mechanism.get("actionType", "")
        targets = mechanism.get("targets", [])

        if not targets:
            return None

        target = targets[0]
        target_symbol = target.get("approvedSymbol", "Unknown")
        target_name = target.get("approvedName", "")
        target_id = target.get("id", "")

        return EvidenceItem(
            source="opentargets",
            indication="Target Mechanism",
            summary=f"{drug_name} acts on {target_symbol} ({target_name}) via {moa_text}. "
                    f"This target may be relevant for additional indications.",
            date=None,
            url=f"https://platform.opentargets.org/target/{target_id}",
            title=f"Mechanism: {moa_text}",
            metadata={
                "drug_id": drug_id,
                "target_id": target_id,
                "target_symbol": target_symbol,
                "target_name": target_name,
                "mechanism": moa_text,
                "action_type": action_type,
                "data_type": "mechanism"
            },
            relevance_score=0.6
        )

    def _process_linked_disease(self, drug_name: str, drug_id: str, disease: Dict) -> Optional[EvidenceItem]:
        """Process linked disease (association score based)."""
        disease_name = disease.get("name", "Unknown")
        disease_id = disease.get("id", "")
        score = disease.get("score", 0)

        if score < 0.1:  # Skip very low associations
            return None

        return EvidenceItem(
            source="opentargets",
            indication=disease_name,
            summary=f"OpenTargets association: {drug_name} linked to {disease_name} "
                    f"with association score {score:.2f}.",
            date=None,
            url=f"https://platform.opentargets.org/disease/{disease_id}",
            title=f"Association: {drug_name} - {disease_name}",
            metadata={
                "drug_id": drug_id,
                "disease_id": disease_id,
                "association_score": score,
                "data_type": "linked_disease"
            },
            relevance_score=min(score, 0.8)  # Cap at 0.8 for linked diseases
        )

    def _phase_to_text(self, phase: int) -> str:
        """Convert numeric phase to text."""
        phase_map = {
            4: "Phase 4 (Approved)",
            3: "Phase 3",
            2: "Phase 2",
            1: "Phase 1",
            0: "Preclinical"
        }
        return phase_map.get(phase, f"Phase {phase}")

    def _phase_to_relevance(self, phase: int) -> float:
        """Convert clinical phase to relevance score."""
        phase_scores = {
            4: 0.95,  # Approved
            3: 0.85,  # Phase 3
            2: 0.75,  # Phase 2
            1: 0.65,  # Phase 1
            0: 0.5    # Preclinical
        }
        return phase_scores.get(phase, 0.5)

    async def _perform_connection_test(self) -> Dict[str, Any]:
        """Test connection to OpenTargets GraphQL API with a minimal query."""
        query = """
        query TestConnection {
            meta {
                apiVersion {
                    x
                    y
                    z
                }
                dataVersion {
                    year
                    month
                }
            }
        }
        """

        async with AsyncHTTPClient() as client:
            response = await client.post(
                self.graphql_url,
                json={"query": query},
                headers=self.graphql_headers
            )

            meta = response.get("data", {}).get("meta", {})
            api_version = meta.get("apiVersion", {})
            data_version = meta.get("dataVersion", {})

            version_str = f"{api_version.get('x', 0)}.{api_version.get('y', 0)}.{api_version.get('z', 0)}"
            data_str = f"{data_version.get('year', 'Unknown')}.{data_version.get('month', 'Unknown')}"

            return {
                "message": "OpenTargets Platform API connected successfully",
                "details": {
                    "api_version": version_str,
                    "data_version": data_str,
                    "endpoint": self.graphql_url
                }
            }
