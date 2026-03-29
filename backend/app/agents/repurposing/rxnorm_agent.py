"""
RxNorm Agent - Fetches drug normalization and relationship data from NLM RxNorm API.
Provides standardized drug naming and identifies related drugs/formulations.
"""

from typing import List, Dict, Any, Optional
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem, AgentResponse
from app.services.repurpose.utils.api_clients import AsyncHTTPClient
from app.services.repurpose.utils.logger import get_logger
from app.repurpose_settings import settings

logger = get_logger("agents.rxnorm")


class RxNormAgent(BaseAgent):
    """
    Agent for fetching drug normalization data from NLM RxNorm API.
    RxNorm provides normalized drug naming and relationships.
    """

    name = "RxNormAgent"
    description = "Fetches drug normalization and relationship data from RxNorm"

    # RxNorm API base URL (free, no authentication required)
    RXNORM_BASE = "https://rxnav.nlm.nih.gov/REST"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.rate_limit = getattr(settings, 'RXNORM_RATE_LIMIT', 5.0)

    async def fetch_data(self, drug_name: str, context: Dict[str, Any] = None) -> List[Dict]:
        """
        Fetch drug data from RxNorm API.

        Args:
            drug_name: Name of the drug to search
            context: Optional search context

        Returns:
            List of raw data from RxNorm API
        """
        self.logger.info(f"Fetching RxNorm data for: {drug_name}")
        results = []

        async with AsyncHTTPClient() as client:
            # 1. Find RxCUI (RxNorm Concept Unique Identifier)
            rxcui = await self._get_rxcui(client, drug_name)
            if not rxcui:
                self.logger.warning(f"No RxCUI found for {drug_name}")
                return results

            # 2. Get drug properties
            properties = await self._get_drug_properties(client, rxcui)
            if properties:
                results.append({
                    "type": "properties",
                    "rxcui": rxcui,
                    "data": properties
                })

            # 3. Get related drugs (same ingredient, different formulations)
            related = await self._get_related_drugs(client, rxcui)
            if related:
                results.append({
                    "type": "related_drugs",
                    "rxcui": rxcui,
                    "data": related
                })

            # 4. Get drug interactions
            interactions = await self._get_drug_interactions(client, rxcui)
            if interactions:
                results.append({
                    "type": "interactions",
                    "rxcui": rxcui,
                    "data": interactions
                })

            # 5. Get drug classes (therapeutic classification)
            classes = await self._get_drug_classes(client, rxcui)
            if classes:
                results.append({
                    "type": "drug_classes",
                    "rxcui": rxcui,
                    "data": classes
                })

        self.logger.info(f"Fetched {len(results)} data categories from RxNorm")
        return results

    async def _get_rxcui(self, client: AsyncHTTPClient, drug_name: str) -> Optional[str]:
        """Get RxCUI for a drug name."""
        try:
            url = f"{self.RXNORM_BASE}/rxcui.json"
            params = {"name": drug_name, "search": 1}

            response = await client.get(url, params=params)

            if response and "idGroup" in response:
                rxnorm_id = response["idGroup"].get("rxnormId")
                if rxnorm_id:
                    return rxnorm_id[0] if isinstance(rxnorm_id, list) else rxnorm_id

            # Try approximate match
            url = f"{self.RXNORM_BASE}/approximateTerm.json"
            params = {"term": drug_name, "maxEntries": 1}

            response = await client.get(url, params=params)

            if response and "approximateGroup" in response:
                candidates = response["approximateGroup"].get("candidate", [])
                if candidates:
                    return candidates[0].get("rxcui")

            return None

        except Exception as e:
            self.logger.error(f"Error getting RxCUI: {e}")
            return None

    async def _get_drug_properties(self, client: AsyncHTTPClient, rxcui: str) -> Optional[Dict]:
        """Get drug properties from RxNorm."""
        try:
            url = f"{self.RXNORM_BASE}/rxcui/{rxcui}/properties.json"
            response = await client.get(url)

            if response and "properties" in response:
                return response["properties"]

            return None

        except Exception as e:
            self.logger.error(f"Error getting drug properties: {e}")
            return None

    async def _get_related_drugs(self, client: AsyncHTTPClient, rxcui: str) -> Optional[List[Dict]]:
        """Get related drugs (same ingredient, different formulations)."""
        try:
            # Use the allrelated endpoint which doesn't need tty parameter
            url = f"{self.RXNORM_BASE}/rxcui/{rxcui}/allrelated.json"

            response = await client.get(url)

            if response and "relatedGroup" in response:
                concept_groups = response["relatedGroup"].get("conceptGroup", [])
                related = []
                for group in concept_groups:
                    for prop in group.get("conceptProperties", [])[:5]:
                        related.append({
                            "rxcui": prop.get("rxcui"),
                            "name": prop.get("name"),
                            "tty": prop.get("tty"),
                            "synonym": prop.get("synonym")
                        })
                return related

            return None

        except Exception as e:
            self.logger.error(f"Error getting related drugs: {e}")
            return None

    async def _get_drug_interactions(self, client: AsyncHTTPClient, rxcui: str) -> Optional[List[Dict]]:
        """Get known drug interactions using the RxNorm Interaction API."""
        try:
            # Use the correct interaction endpoint
            # Note: The Interaction API is at /interaction/interaction.json (not /interaction/list.json)
            url = f"{self.RXNORM_BASE}/interaction/interaction.json"
            params = {"rxcui": rxcui}

            try:
                response = await client.get(url, params=params, retry=False)
            except Exception as http_err:
                # Some drugs may not have interaction data - this is normal
                error_str = str(http_err)
                if "404" in error_str or "400" in error_str:
                    self.logger.debug(f"No interaction data available for RxCUI {rxcui}")
                    return None
                raise

            if response and "interactionTypeGroup" in response:
                interactions = []
                for group in response.get("interactionTypeGroup", []):
                    for itype in group.get("interactionType", []):
                        for pair in itype.get("interactionPair", [])[:10]:
                            interacting_concept = pair.get("interactionConcept", [{}])
                            if interacting_concept and len(interacting_concept) > 0:
                                interacting_name = interacting_concept[0].get("minConceptItem", {}).get("name")
                            else:
                                interacting_name = "Unknown"
                            interactions.append({
                                "severity": pair.get("severity"),
                                "description": pair.get("description"),
                                "interacting_drug": interacting_name
                            })
                return interactions

            return None

        except Exception as e:
            self.logger.error(f"Error getting drug interactions: {e}")
            return None

    async def _get_drug_classes(self, client: AsyncHTTPClient, rxcui: str) -> Optional[List[Dict]]:
        """Get drug therapeutic classes."""
        try:
            # Use the RxClass API endpoint
            url = f"{self.RXNORM_BASE}/rxclass/class/byRxcui.json"
            params = {"rxcui": rxcui}

            response = await client.get(url, params=params)

            if response and "rxclassDrugInfoList" in response:
                classes = []
                for info in response["rxclassDrugInfoList"].get("rxclassDrugInfo", [])[:10]:
                    class_info = info.get("rxclassMinConceptItem", {})
                    classes.append({
                        "class_id": class_info.get("classId"),
                        "class_name": class_info.get("className"),
                        "class_type": class_info.get("classType")
                    })
                return classes

            return None

        except Exception as e:
            self.logger.error(f"Error getting drug classes: {e}")
            return None

    async def process_data(self, raw_data: List[Dict], drug_name: str) -> List[EvidenceItem]:
        """
        Process RxNorm data into evidence items.

        Args:
            raw_data: Raw data from RxNorm API
            drug_name: Name of the drug

        Returns:
            List of evidence items
        """
        evidence_items = []

        for item in raw_data:
            data_type = item.get("type")
            data = item.get("data")
            rxcui = item.get("rxcui")

            if data_type == "properties" and data:
                drug_name_normalized = data.get('name', drug_name)
                evidence_items.append(EvidenceItem(
                    source="rxnorm",
                    summary=f"RxNorm standardized properties for {drug_name_normalized} (RxCUI: {rxcui})",
                    title=f"RxNorm Drug Properties: {drug_name_normalized}",
                    description=f"Standardized drug information. TTY: {data.get('tty', 'Unknown')}, "
                                f"Synonym: {data.get('synonym', 'N/A')}",
                    url=f"https://mor.nlm.nih.gov/RxNav/search?searchBy=RXCUI&searchTerm={rxcui}",
                    relevance_score=0.8,
                    indication="Drug Normalization",
                    metadata={
                        "data_type": "properties",
                        "rxcui": rxcui,
                        "name": drug_name_normalized,
                        "tty": data.get("tty"),
                        "synonym": data.get("synonym"),
                        "language": data.get("language")
                    }
                ))

            elif data_type == "related_drugs" and data:
                for related in data[:5]:
                    related_name = related.get('name', 'Unknown')
                    evidence_items.append(EvidenceItem(
                        source="rxnorm",
                        summary=f"Related drug formulation: {related_name}",
                        title=f"Related Formulation: {related_name}",
                        description=f"Related drug formulation with RxCUI {related.get('rxcui')}. "
                                    f"Type: {related.get('tty', 'Unknown')}",
                        url=f"https://mor.nlm.nih.gov/RxNav/search?searchBy=RXCUI&searchTerm={related.get('rxcui')}",
                        relevance_score=0.6,
                        indication="Drug Formulations",
                        metadata={
                            "data_type": "related_drug",
                            "rxcui": related.get("rxcui"),
                            "name": related_name,
                            "tty": related.get("tty")
                        }
                    ))

            elif data_type == "interactions" and data:
                for interaction in data[:5]:
                    interacting_drug = interaction.get('interacting_drug', 'Unknown')
                    severity = interaction.get('severity', 'Unknown')
                    evidence_items.append(EvidenceItem(
                        source="rxnorm",
                        summary=f"Drug interaction: {drug_name} with {interacting_drug} (Severity: {severity})",
                        title=f"Drug Interaction: {drug_name} + {interacting_drug}",
                        description=f"{interaction.get('description', 'Potential drug interaction')}. "
                                    f"Severity: {severity}",
                        url=f"https://mor.nlm.nih.gov/RxNav/search?searchBy=RXCUI&searchTerm={rxcui}",
                        relevance_score=0.7,
                        indication="Drug Safety",
                        metadata={
                            "data_type": "interaction",
                            "severity": severity,
                            "interacting_drug": interacting_drug,
                            "description": interaction.get("description")
                        }
                    ))

            elif data_type == "drug_classes" and data:
                for drug_class in data[:5]:
                    class_name = drug_class.get("class_name", "Unknown Class")
                    evidence_items.append(EvidenceItem(
                        source="rxnorm",
                        summary=f"{drug_name} belongs to therapeutic class: {class_name}",
                        title=f"Therapeutic Class: {class_name}",
                        description=f"{drug_name} belongs to therapeutic class: {class_name}. "
                                    f"Classification type: {drug_class.get('class_type', 'Unknown')}",
                        url=f"https://mor.nlm.nih.gov/RxClass/",
                        relevance_score=0.7,
                        indication=class_name,
                        metadata={
                            "data_type": "drug_class",
                            "class_id": drug_class.get("class_id"),
                            "class_name": class_name,
                            "class_type": drug_class.get("class_type")
                        }
                    ))

        self.logger.info(f"Processed {len(evidence_items)} evidence items from RxNorm")
        return evidence_items

    async def _perform_connection_test(self) -> Dict[str, Any]:
        """Test connection to RxNorm API."""
        async with AsyncHTTPClient() as client:
            # Use version endpoint to test connectivity
            url = f"{self.RXNORM_BASE}/version.json"
            response = await client.get(url)

            version_info = response.get("version", {})

            return {
                "message": "RxNorm API connected successfully",
                "details": {
                    "endpoint": self.RXNORM_BASE,
                    "version": version_info if version_info else "API responding"
                }
            }
