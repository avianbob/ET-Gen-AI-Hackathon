"""
FDA Orange Book Agent - Fetches patent and exclusivity data.
Uses FDA Orange Book data files and API.
No API key required.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem
from app.services.repurpose.utils.api_clients import AsyncHTTPClient, rate_limited
from app.repurpose_settings import settings


class OrangeBookAgent(BaseAgent):
    """Agent for searching FDA Orange Book for patent and exclusivity data."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        # OpenFDA provides Orange Book data
        self.base_url = "https://api.fda.gov/drug"
        self.max_results = self.config.get("max_results", 20)

    @rate_limited(settings.ORANGE_BOOK_RATE_LIMIT)
    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch patent and exclusivity data from FDA sources.

        Args:
            drug_name: Drug name to search for
            context: Additional search context

        Returns:
            List of patent/exclusivity records
        """
        drug_name = self._sanitize_drug_name(drug_name)
        self.logger.info(f"Searching FDA Orange Book for: {drug_name}")

        results = []

        async with AsyncHTTPClient() as client:
            # Search drugsfda endpoint for application data
            app_data = await self._search_applications(client, drug_name)
            results.extend(app_data)

        self.logger.info(f"Found {len(results)} Orange Book records")
        return results

    async def _search_applications(self, client: AsyncHTTPClient, drug_name: str) -> List[Dict]:
        """Search for drug applications with patent/exclusivity info."""
        try:
            params = {
                "search": f'openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}"',
                "limit": self.max_results
            }

            data = await client.get(f"{self.base_url}/drugsfda.json", params=params)
            results = data.get("results", [])

            # Enrich with exclusivity data
            enriched_results = []
            for result in results:
                enriched = await self._enrich_with_exclusivity(result)
                enriched_results.append(enriched)

            return enriched_results

        except Exception as e:
            self.logger.warning(f"FDA application search error: {e}")
            return []

    async def _enrich_with_exclusivity(self, app_data: Dict) -> Dict:
        """Enrich application data with patent and exclusivity information."""
        # Extract patent information from products
        products = app_data.get("products", [])
        patents = []
        exclusivities = []

        for product in products:
            # Get active ingredients
            active_ingredients = product.get("active_ingredients", [])

            # Check for patent/exclusivity in product
            te_code = product.get("te_code", "")  # Therapeutic Equivalence code

            app_data["_enriched"] = {
                "active_ingredients": active_ingredients,
                "te_code": te_code
            }

        return app_data

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """
        Process Orange Book data into evidence items.

        Args:
            raw_data: List of application records

        Returns:
            List of EvidenceItem objects
        """
        evidence_items = []

        for app_data in raw_data:
            try:
                evidence = self._process_application(app_data)
                if evidence:
                    evidence_items.extend(evidence)

            except Exception as e:
                self.logger.warning(f"Failed to process Orange Book record: {e}")
                continue

        return evidence_items

    def _process_application(self, app_data: Dict) -> List[EvidenceItem]:
        """Process a single drug application record."""
        evidence_items = []

        application_number = app_data.get("application_number", "")
        sponsor_name = app_data.get("sponsor_name", "Unknown")

        openfda = app_data.get("openfda", {})
        brand_names = openfda.get("brand_name", [])
        brand_name = brand_names[0] if brand_names else "Unknown"

        generic_names = openfda.get("generic_name", [])
        generic_name = generic_names[0] if generic_names else ""

        # Get submission information
        submissions = app_data.get("submissions", [])

        for submission in submissions:
            submission_type = submission.get("submission_type", "")
            submission_status = submission.get("submission_status", "")
            submission_date = submission.get("submission_status_date", "")

            # Get application docs (may contain indication info)
            app_docs = submission.get("application_docs", [])

            # Extract indication from application documents
            indication = "Unknown Indication"
            for doc in app_docs:
                doc_type = doc.get("type", "")
                if "label" in doc_type.lower():
                    # Labels contain indication info
                    indication = self._extract_indication(doc.get("title", ""))
                    if indication == "Unknown Indication":
                        indication = doc.get("title", "Unknown Indication")
                    break

            # Create summary based on submission type
            if submission_type == "ORIG":
                summary = f"Original NDA/ANDA {application_number} for {brand_name}"
            elif submission_type == "SUPPL":
                summary = f"Supplemental application for {brand_name}"
            else:
                summary = f"FDA application {application_number} for {brand_name}"

            if generic_name:
                summary += f" ({generic_name})"
            summary += f" by {sponsor_name}. Status: {submission_status}"

            evidence_items.append(EvidenceItem(
                source="orange_book",
                indication=indication,
                summary=summary,
                date=submission_date,
                url=f"https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo={application_number.replace('NDA', '').replace('ANDA', '')}",
                title=f"FDA {submission_type}: {brand_name}",
                metadata={
                    "application_number": application_number,
                    "brand_name": brand_name,
                    "generic_name": generic_name,
                    "sponsor": sponsor_name,
                    "submission_type": submission_type,
                    "submission_status": submission_status,
                    "data_type": "fda_application"
                },
                relevance_score=self._calculate_relevance(submission)
            ))

        return evidence_items

    def _calculate_relevance(self, submission: Dict) -> float:
        """Calculate relevance score based on submission data."""
        score = 0.5  # Base score

        status = submission.get("submission_status", "").upper()

        # Boost for approved submissions
        if "AP" in status or "APPROVED" in status:
            score += 0.25
        elif "TA" in status or "TENTATIVE" in status:
            score += 0.15

        # Boost for original applications (new drug)
        submission_type = submission.get("submission_type", "")
        if submission_type == "ORIG":
            score += 0.15

        # Boost for recent submissions
        date_str = submission.get("submission_status_date", "")
        if date_str:
            try:
                year = int(date_str.split("-")[0])
                current_year = datetime.now().year
                if year >= current_year - 2:
                    score += 0.1
                elif year >= current_year - 5:
                    score += 0.05
            except (ValueError, IndexError):
                pass

        return min(score, 1.0)
