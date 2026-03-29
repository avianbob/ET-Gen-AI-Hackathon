"""
KEGG Agent - Fetches pathway and disease association data.
Uses KEGG REST API: https://rest.kegg.jp/
No API key required.
"""

from typing import Dict, List, Any, Optional
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem
from app.services.repurpose.utils.api_clients import AsyncHTTPClient, rate_limited
from app.repurpose_settings import settings


class KEGGAgent(BaseAgent):
    """Agent for searching KEGG for pathway and disease data."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = "https://rest.kegg.jp"

    @rate_limited(settings.KEGG_RATE_LIMIT)
    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch pathway and disease data from KEGG.

        Args:
            drug_name: Drug name to search for
            context: Additional search context

        Returns:
            List of KEGG data results
        """
        drug_name = self._sanitize_drug_name(drug_name)
        self.logger.info(f"Searching KEGG for: {drug_name}")

        results = []

        async with AsyncHTTPClient() as client:
            # Search for drug in KEGG
            drug_ids = await self._search_drug(client, drug_name)

            if not drug_ids:
                self.logger.info(f"No KEGG drug found for: {drug_name}")
                return []

            # Get details for each drug
            for drug_id in drug_ids[:3]:  # Limit to top 3
                drug_data = await self._get_drug_details(client, drug_id)
                if drug_data:
                    drug_data["kegg_id"] = drug_id

                    # Get linked pathways
                    pathways = await self._get_linked_pathways(client, drug_id)
                    drug_data["pathways"] = pathways

                    # Get linked diseases
                    diseases = await self._get_linked_diseases(client, drug_id)
                    drug_data["diseases"] = diseases

                    results.append(drug_data)

        self.logger.info(f"Found {len(results)} KEGG records")
        return results

    async def _search_drug(self, client: AsyncHTTPClient, drug_name: str) -> List[str]:
        """Search for drug in KEGG database."""
        try:
            # KEGG returns plain text, use get_text instead of get
            response = await client.get_text(
                f"{self.base_url}/find/drug/{drug_name}",
                headers={"Accept": "text/plain"}
            )

            drug_ids = []
            if response and response.strip():
                for line in response.strip().split("\n"):
                    if line and "\t" in line:
                        drug_id = line.split("\t")[0]
                        drug_ids.append(drug_id)
            return drug_ids
        except Exception as e:
            self.logger.warning(f"KEGG drug search error: {e}")
            return []

    async def _get_drug_details(self, client: AsyncHTTPClient, drug_id: str) -> Optional[Dict]:
        """Get detailed drug information."""
        try:
            # KEGG returns plain text, use get_text instead of get
            response = await client.get_text(
                f"{self.base_url}/get/{drug_id}",
                headers={"Accept": "text/plain"}
            )

            if response and response.strip():
                return self._parse_kegg_flat(response)
            return None
        except Exception as e:
            self.logger.debug(f"Failed to get KEGG drug details: {e}")
            return None

    async def _get_linked_pathways(self, client: AsyncHTTPClient, drug_id: str) -> List[Dict]:
        """Get pathways linked to the drug."""
        try:
            # KEGG returns plain text, use get_text instead of get
            response = await client.get_text(
                f"{self.base_url}/link/pathway/{drug_id}",
                headers={"Accept": "text/plain"}
            )

            pathways = []
            if response and response.strip():
                for line in response.strip().split("\n"):
                    if "\t" in line:
                        parts = line.split("\t")
                        if len(parts) >= 2:
                            pathway_id = parts[1]
                            pathway_name = await self._get_pathway_name(client, pathway_id)
                            pathways.append({
                                "id": pathway_id,
                                "name": pathway_name
                            })
            return pathways[:10]  # Limit to 10 pathways
        except Exception as e:
            self.logger.debug(f"Failed to get linked pathways: {e}")
            return []

    async def _get_linked_diseases(self, client: AsyncHTTPClient, drug_id: str) -> List[Dict]:
        """Get diseases linked to the drug."""
        try:
            # KEGG returns plain text, use get_text instead of get
            response = await client.get_text(
                f"{self.base_url}/link/disease/{drug_id}",
                headers={"Accept": "text/plain"}
            )

            diseases = []
            if response and response.strip():
                for line in response.strip().split("\n"):
                    if "\t" in line:
                        parts = line.split("\t")
                        if len(parts) >= 2:
                            disease_id = parts[1]
                            disease_name = await self._get_disease_name(client, disease_id)
                            diseases.append({
                                "id": disease_id,
                                "name": disease_name
                            })
            return diseases[:15]  # Limit to 15 diseases
        except Exception as e:
            self.logger.debug(f"Failed to get linked diseases: {e}")
            return []

    async def _get_pathway_name(self, client: AsyncHTTPClient, pathway_id: str) -> str:
        """Get pathway name from ID."""
        try:
            # KEGG returns plain text, use get_text instead of get
            response = await client.get_text(
                f"{self.base_url}/get/{pathway_id}",
                headers={"Accept": "text/plain"}
            )
            if response and response.strip():
                data = self._parse_kegg_flat(response)
                return data.get("NAME", [pathway_id])[0] if data.get("NAME") else pathway_id
            return pathway_id
        except Exception:
            return pathway_id

    async def _get_disease_name(self, client: AsyncHTTPClient, disease_id: str) -> str:
        """Get disease name from ID."""
        try:
            # KEGG returns plain text, use get_text instead of get
            response = await client.get_text(
                f"{self.base_url}/get/{disease_id}",
                headers={"Accept": "text/plain"}
            )
            if response and response.strip():
                data = self._parse_kegg_flat(response)
                return data.get("NAME", [disease_id])[0] if data.get("NAME") else disease_id
            return disease_id
        except Exception:
            return disease_id

    def _parse_kegg_flat(self, text: str) -> Dict:
        """Parse KEGG flat file format."""
        data = {}
        current_key = None
        current_values = []

        for line in text.split("\n"):
            if not line or line.startswith("///"):
                continue

            if line[0] != " ":
                # New field
                if current_key and current_values:
                    data[current_key] = current_values

                parts = line.split(None, 1)
                current_key = parts[0] if parts else None
                current_values = [parts[1].strip()] if len(parts) > 1 else []
            else:
                # Continuation of previous field
                current_values.append(line.strip())

        if current_key and current_values:
            data[current_key] = current_values

        return data

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """
        Process KEGG data into evidence items.

        Args:
            raw_data: List of KEGG drug data

        Returns:
            List of EvidenceItem objects
        """
        evidence_items = []

        for drug_data in raw_data:
            try:
                kegg_id = drug_data.get("kegg_id", "")
                drug_name = drug_data.get("NAME", ["Unknown"])[0] if drug_data.get("NAME") else "Unknown"

                # Create evidence for each linked disease
                diseases = drug_data.get("diseases", [])
                for disease in diseases:
                    evidence = self._create_disease_evidence(kegg_id, drug_name, disease, drug_data)
                    if evidence:
                        evidence_items.append(evidence)

                # Create evidence for pathways (as mechanism insight)
                pathways = drug_data.get("pathways", [])
                if pathways:
                    evidence = self._create_pathway_evidence(kegg_id, drug_name, pathways)
                    if evidence:
                        evidence_items.append(evidence)

            except Exception as e:
                self.logger.warning(f"Failed to process KEGG record: {e}")
                continue

        return evidence_items

    def _create_disease_evidence(self, kegg_id: str, drug_name: str, disease: Dict, drug_data: Dict) -> Optional[EvidenceItem]:
        """Create evidence item for disease association."""
        disease_name = disease.get("name", "Unknown")
        disease_id = disease.get("id", "")

        # Extract indication
        indication = self._normalize_disease_name(disease_name)

        return EvidenceItem(
            source="kegg",
            indication=indication,
            summary=f"KEGG database links {drug_name} to {disease_name}. "
                    f"This association is based on pathway analysis and known drug-disease relationships.",
            date=None,
            url=f"https://www.kegg.jp/entry/{kegg_id}",
            title=f"KEGG: {drug_name} - {disease_name}",
            metadata={
                "kegg_drug_id": kegg_id,
                "disease_id": disease_id,
                "disease_name": disease_name,
                "data_type": "disease_link"
            },
            relevance_score=0.6
        )

    def _create_pathway_evidence(self, kegg_id: str, drug_name: str, pathways: List[Dict]) -> Optional[EvidenceItem]:
        """Create evidence item for pathway associations."""
        pathway_names = [p.get("name", p.get("id", "")) for p in pathways[:5]]

        return EvidenceItem(
            source="kegg",
            indication="Pathway Mechanism",
            summary=f"KEGG shows {drug_name} is involved in pathways: {', '.join(pathway_names)}. "
                    f"These pathways may suggest additional therapeutic applications.",
            date=None,
            url=f"https://www.kegg.jp/entry/{kegg_id}",
            title=f"KEGG Pathways: {drug_name}",
            metadata={
                "kegg_drug_id": kegg_id,
                "pathways": pathways,
                "pathway_count": len(pathways),
                "data_type": "pathway"
            },
            relevance_score=0.55
        )

    def _normalize_disease_name(self, disease_name: str) -> str:
        """Normalize KEGG disease name to standard format."""
        # Remove KEGG-specific formatting
        name = disease_name.split(";")[0].strip()

        # Try to extract indication using base class method
        indication = self._extract_indication(name)
        if indication != "Unknown Indication":
            return indication

        return name.title() if name else "Unknown Indication"

    async def _perform_connection_test(self) -> Dict[str, Any]:
        """Test connection to KEGG REST API."""
        async with AsyncHTTPClient() as client:
            # Use info endpoint to test connectivity
            response = await client.get_text(
                f"{self.base_url}/info/kegg",
                headers={"Accept": "text/plain"}
            )

            # Parse the info response
            lines = response.strip().split("\n") if response else []
            info_dict = {}
            for line in lines:
                if "\t" in line:
                    key, value = line.split("\t", 1)
                    info_dict[key.strip()] = value.strip()

            return {
                "message": "KEGG REST API connected successfully",
                "details": {
                    "endpoint": self.base_url,
                    "database_info": info_dict.get("kegg", "KEGG database"),
                    "api_responding": True
                }
            }
