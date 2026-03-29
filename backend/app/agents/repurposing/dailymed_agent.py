"""
DailyMed Agent - Fetches FDA drug labeling information.
Uses DailyMed API: https://dailymed.nlm.nih.gov/dailymed/services/
No API key required.
"""

from typing import Dict, List, Any, Optional
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem
from app.services.repurpose.utils.api_clients import AsyncHTTPClient, rate_limited
from app.repurpose_settings import settings


class DailyMedAgent(BaseAgent):
    """Agent for searching DailyMed for FDA drug labeling."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
        self.max_results = self.config.get("max_results", 10)

    @rate_limited(settings.DAILYMED_RATE_LIMIT)
    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch drug labeling from DailyMed.

        Args:
            drug_name: Drug name to search for
            context: Additional search context

        Returns:
            List of SPL (Structured Product Labeling) results
        """
        drug_name = self._sanitize_drug_name(drug_name)
        self.logger.info(f"Searching DailyMed for: {drug_name}")

        results = []

        async with AsyncHTTPClient() as client:
            # Search for SPLs
            spls = await self._search_spls(client, drug_name)

            # Get detailed info for each SPL
            for spl in spls[:self.max_results]:
                spl_details = await self._get_spl_details(client, spl)
                if spl_details:
                    results.append(spl_details)

        self.logger.info(f"Found {len(results)} DailyMed records")
        return results

    async def _search_spls(self, client: AsyncHTTPClient, drug_name: str) -> List[Dict]:
        """Search for SPLs by drug name."""
        try:
            params = {
                "drug_name": drug_name,
                "pagesize": self.max_results
            }
            # DailyMed API requires explicit Accept header
            headers = {"Accept": "application/json"}
            data = await client.get(f"{self.base_url}/spls.json", params=params, headers=headers)
            return data.get("data", [])
        except Exception as e:
            self.logger.warning(f"DailyMed search error: {e}")
            return []

    async def _get_spl_details(self, client: AsyncHTTPClient, spl: Dict) -> Optional[Dict]:
        """Get detailed SPL information."""
        setid = spl.get("setid")
        if not setid:
            return None

        # Skip detailed fetch - DailyMed v2 API has issues with .json detail endpoints
        # Return the search result directly which has enough data for our purposes
        return spl

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """
        Process DailyMed SPL data into evidence items.

        Args:
            raw_data: List of SPL data

        Returns:
            List of EvidenceItem objects
        """
        evidence_items = []

        for spl in raw_data:
            try:
                evidence = self._process_spl(spl)
                if evidence:
                    evidence_items.append(evidence)

            except Exception as e:
                self.logger.warning(f"Failed to process SPL: {e}")
                continue

        return evidence_items

    def _process_spl(self, spl: Dict) -> Optional[EvidenceItem]:
        """Process a single SPL record."""
        setid = spl.get("setid", "")
        title = spl.get("title", "Unknown")

        # Get product info
        products = spl.get("products", [])
        brand_name = products[0].get("brand_name", "Unknown") if products else "Unknown"
        generic_name = products[0].get("generic_name", "") if products else ""

        # Get manufacturer
        labeler = spl.get("labeler", "")

        # Get active ingredients
        active_ingredients = []
        for product in products:
            ingredients = product.get("active_ingredients", [])
            for ing in ingredients:
                name = ing.get("name", "")
                strength = ing.get("strength", "")
                if name:
                    active_ingredients.append(f"{name} {strength}".strip())

        # Extract indication from title or use generic
        indication = self._extract_indication(title)

        summary = f"FDA-approved labeling for {brand_name}"
        if generic_name:
            summary += f" ({generic_name})"
        if labeler:
            summary += f" by {labeler}"

        return EvidenceItem(
            source="dailymed",
            indication=indication,
            summary=self._truncate_text(summary, 300),
            date=spl.get("published_date"),
            url=f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={setid}",
            title=f"DailyMed: {brand_name}",
            metadata={
                "setid": setid,
                "brand_name": brand_name,
                "generic_name": generic_name,
                "labeler": labeler,
                "active_ingredients": active_ingredients,
                "product_type": spl.get("product_type", ""),
                "data_type": "spl"
            },
            relevance_score=0.65
        )

    async def _perform_connection_test(self) -> Dict[str, Any]:
        """Test connection to DailyMed API."""
        async with AsyncHTTPClient() as client:
            # Use a minimal search to test connectivity
            params = {
                "drug_name": "aspirin",
                "pagesize": 1
            }
            headers = {"Accept": "application/json"}
            data = await client.get(f"{self.base_url}/spls.json", params=params, headers=headers)

            total_pages = data.get("metadata", {}).get("total_pages", 0)
            total_elements = data.get("metadata", {}).get("total_elements", 0)

            return {
                "message": "DailyMed API connected successfully",
                "details": {
                    "endpoint": self.base_url,
                    "total_spl_documents": total_elements,
                    "api_responding": True
                }
            }
