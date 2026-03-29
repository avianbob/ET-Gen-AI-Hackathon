"""
Bioactivity Agent - Fetches molecular and bioactivity data from ChEMBL.
Uses ChEMBL REST API.
"""

from typing import Dict, List, Any, Optional
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem
from app.services.repurpose.utils.api_clients import AsyncHTTPClient, rate_limited
from app.repurpose_settings import settings


class BioactivityAgent(BaseAgent):
    """Agent for querying ChEMBL for bioactivity data."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = "https://www.ebi.ac.uk/chembl/api/data"
        self.max_activities = self.config.get("max_activities", 100)

    @rate_limited(settings.CHEMBL_RATE_LIMIT)
    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch bioactivity data from ChEMBL API.

        Args:
            drug_name: Drug name to search for
            context: Additional search context

        Returns:
            List of bioactivity dictionaries
        """
        drug_name = self._sanitize_drug_name(drug_name)

        self.logger.info(f"Searching ChEMBL for: {drug_name}")

        try:
            async with AsyncHTTPClient() as client:
                # Step 1: Search for molecule by name
                chembl_id = await self._get_chembl_id(client, drug_name)

                if not chembl_id:
                    self.logger.warning(f"No ChEMBL ID found for: {drug_name}")
                    return []

                self.logger.info(f"Found ChEMBL ID: {chembl_id}")

                # Step 2: Get bioactivity data
                activities = await self._get_bioactivities(client, chembl_id)

                # Step 3: Get target information
                enriched_activities = await self._enrich_with_targets(client, activities)

                return enriched_activities

        except Exception as e:
            self.logger.error(f"ChEMBL API error: {e}")
            raise

    async def _get_chembl_id(self, client: AsyncHTTPClient, drug_name: str) -> Optional[str]:
        """
        Get ChEMBL ID from drug name.

        Args:
            client: HTTP client
            drug_name: Drug name

        Returns:
            ChEMBL ID or None
        """
        try:
            url = f"{self.base_url}/molecule/search.json"
            params = {"q": drug_name, "limit": 1}

            data = await client.get(url, params=params)
            molecules = data.get("molecules", [])

            if molecules:
                return molecules[0].get("molecule_chembl_id")

            return None

        except Exception as e:
            self.logger.warning(f"Failed to get ChEMBL ID: {e}")
            return None

    async def _get_bioactivities(
        self,
        client: AsyncHTTPClient,
        chembl_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get bioactivity data for a ChEMBL ID.

        Args:
            client: HTTP client
            chembl_id: ChEMBL molecule ID

        Returns:
            List of activity dictionaries
        """
        try:
            url = f"{self.base_url}/activity.json"
            params = {
                "molecule_chembl_id": chembl_id,
                "limit": self.max_activities
            }

            data = await client.get(url, params=params)
            activities = data.get("activities", [])

            self.logger.info(f"Found {len(activities)} bioactivity records")
            return activities

        except Exception as e:
            self.logger.warning(f"Failed to get bioactivities: {e}")
            return []

    async def _enrich_with_targets(
        self,
        client: AsyncHTTPClient,
        activities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich activities with target protein information.

        Args:
            client: HTTP client
            activities: List of activity dictionaries

        Returns:
            Enriched activity dictionaries
        """
        enriched = []

        # Get unique target ChEMBL IDs
        target_ids = set()
        for activity in activities:
            target_id = activity.get("target_chembl_id")
            if target_id:
                target_ids.add(target_id)

        # Fetch target information (limit to avoid too many requests)
        target_cache = {}
        for target_id in list(target_ids)[:20]:  # Limit to 20 targets
            try:
                url = f"{self.base_url}/target/{target_id}.json"
                target_data = await client.get(url)
                target_cache[target_id] = target_data
            except Exception as e:
                self.logger.warning(f"Failed to fetch target {target_id}: {e}")
                continue

        # Enrich activities with target info
        for activity in activities:
            target_id = activity.get("target_chembl_id")
            if target_id in target_cache:
                activity["target_info"] = target_cache[target_id]

            enriched.append(activity)

        return enriched

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """
        Process bioactivity data into evidence items.

        Args:
            raw_data: List of activity dictionaries

        Returns:
            List of EvidenceItem objects
        """
        evidence_items = []

        # Group activities by target
        target_groups = {}
        for activity in raw_data:
            target_id = activity.get("target_chembl_id", "unknown")
            if target_id not in target_groups:
                target_groups[target_id] = []
            target_groups[target_id].append(activity)

        # Create evidence items from target groups
        for target_id, activities in target_groups.items():
            try:
                # Use first activity for target info
                first_activity = activities[0]
                target_info = first_activity.get("target_info", {})

                target_name = target_info.get("pref_name", "Unknown Target")
                target_type = target_info.get("target_type", "")

                # Extract disease associations
                target_components = target_info.get("target_components", [])
                diseases = []
                for component in target_components:
                    component_diseases = component.get("target_component_synonyms", [])
                    diseases.extend([d.get("syn_type") for d in component_diseases if d.get("syn_type")])

                # Infer indication from target or use generic
                indication = diseases[0] if diseases else self._infer_indication_from_target(target_name)

                # Calculate activity stats
                ic50_values = []
                for activity in activities:
                    standard_type = activity.get("standard_type", "")
                    if standard_type in ["IC50", "EC50", "Ki", "Kd"]:
                        try:
                            value = float(activity.get("standard_value", 0))
                            if value > 0:
                                ic50_values.append(value)
                        except (ValueError, TypeError):
                            continue

                avg_ic50 = sum(ic50_values) / len(ic50_values) if ic50_values else None

                # Create summary
                summary = f"Active against {target_name}"
                if avg_ic50:
                    summary += f" (avg IC50: {avg_ic50:.2f} nM)"
                summary += f". {len(activities)} bioactivity records."

                # Create evidence item
                evidence = EvidenceItem(
                    source="bioactivity",
                    indication=indication,
                    summary=summary,
                    date="",
                    url=f"https://www.ebi.ac.uk/chembl/target_report_card/{target_id}/" if target_id else None,
                    title=f"Bioactivity against {target_name}",
                    metadata={
                        "target_chembl_id": target_id,
                        "target_name": target_name,
                        "target_type": target_type,
                        "activity_count": len(activities),
                        "avg_ic50_nm": avg_ic50
                    },
                    relevance_score=self._calculate_relevance(avg_ic50, len(activities))
                )

                evidence_items.append(evidence)

            except Exception as e:
                self.logger.warning(f"Failed to process target group: {e}")
                continue

        return evidence_items

    def _infer_indication_from_target(self, target_name: str) -> str:
        """
        Infer disease indication from target name.

        Args:
            target_name: Target protein name

        Returns:
            Inferred indication
        """
        target_lower = target_name.lower()

        # Common target-disease associations
        associations = {
            "cancer": ["tumor", "oncogene", "carcinoma", "kinase"],
            "diabetes": ["insulin", "glucose", "glut", "incretin"],
            "cardiovascular": ["cardiac", "heart", "vascular", "blood pressure"],
            "inflammation": ["inflammatory", "cytokine", "interleukin", "tnf"],
            "neurodegenerative": ["amyloid", "tau", "alpha-synuclein", "huntingtin"],
            "pain": ["opioid", "pain", "nociceptor"],
            "infection": ["viral", "bacterial", "pathogen", "antimicrobial"]
        }

        for indication, keywords in associations.items():
            for keyword in keywords:
                if keyword in target_lower:
                    return indication.title()

        return "Multiple Indications"

    def _calculate_relevance(self, avg_ic50: Optional[float], activity_count: int) -> float:
        """
        Calculate relevance score based on bioactivity data.

        Args:
            avg_ic50: Average IC50 value (nM)
            activity_count: Number of activity records

        Returns:
            Relevance score (0-1)
        """
        score = 0.5  # Base score

        # Boost for strong activity (low IC50)
        if avg_ic50:
            if avg_ic50 < 100:  # Very potent
                score += 0.3
            elif avg_ic50 < 1000:  # Potent
                score += 0.2
            elif avg_ic50 < 10000:  # Moderate
                score += 0.1

        # Boost for multiple activity records (more confidence)
        if activity_count >= 10:
            score += 0.2
        elif activity_count >= 5:
            score += 0.1

        return min(score, 1.0)

    async def _perform_connection_test(self) -> Dict[str, Any]:
        """Test connection to ChEMBL API with a status check."""
        async with AsyncHTTPClient() as client:
            # Get ChEMBL API status
            url = f"{self.base_url}/status.json"
            data = await client.get(url)

            return {
                "message": "ChEMBL API connected successfully",
                "details": {
                    "status": data.get("status", "OK"),
                    "endpoint": self.base_url,
                    "version": data.get("chembl_db_version", "Unknown")
                }
            }
