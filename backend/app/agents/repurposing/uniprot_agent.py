"""
UniProt Agent - Fetches protein target data and disease associations.
Uses UniProt REST API: https://rest.uniprot.org/
No API key required.
"""

from typing import Dict, List, Any, Optional
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem
from app.services.repurpose.utils.api_clients import AsyncHTTPClient, rate_limited
from app.repurpose_settings import settings


class UniProtAgent(BaseAgent):
    """Agent for searching UniProt for protein target data."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = "https://rest.uniprot.org/uniprotkb"
        self.max_results = self.config.get("max_results", 20)

    @rate_limited(settings.UNIPROT_RATE_LIMIT)
    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch protein target data from UniProt.

        Args:
            drug_name: Drug name to search for
            context: Additional search context

        Returns:
            List of protein records
        """
        drug_name = self._sanitize_drug_name(drug_name)
        self.logger.info(f"Searching UniProt for: {drug_name}")

        results = []

        async with AsyncHTTPClient() as client:
            # Search for proteins associated with the drug
            proteins = await self._search_proteins(client, drug_name)
            results.extend(proteins)

        self.logger.info(f"Found {len(results)} UniProt records")
        return results

    async def _search_proteins(self, client: AsyncHTTPClient, drug_name: str) -> List[Dict]:
        """Search for proteins associated with the drug."""
        try:
            # Use simplified full-text query - UniProt REST API field names have changed
            # Search for drug name in annotations
            query = f'("{drug_name}")'

            # Use only currently valid fields (removed deprecated cc_pharmaceutical, ft_binding, xref_drugbank)
            params = {
                "query": query,
                "format": "json",
                "fields": "accession,id,protein_name,gene_names,organism_name,cc_disease,cc_function,cc_pathway",
                "size": self.max_results
            }

            headers = {"Accept": "application/json"}
            response = await client.get(
                f"{self.base_url}/search",
                params=params,
                headers=headers
            )

            if isinstance(response, dict):
                return response.get("results", [])
            return []

        except Exception as e:
            self.logger.warning(f"UniProt search error: {e}")

            # Fallback: try an even simpler search without quotes
            try:
                params = {
                    "query": drug_name,
                    "format": "json",
                    "fields": "accession,id,protein_name,gene_names,organism_name,cc_disease,cc_function",
                    "size": min(self.max_results, 10)
                }

                headers = {"Accept": "application/json"}
                response = await client.get(
                    f"{self.base_url}/search",
                    params=params,
                    headers=headers
                )

                if isinstance(response, dict):
                    return response.get("results", [])
            except Exception:
                pass

            return []

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """
        Process UniProt protein data into evidence items.

        Args:
            raw_data: List of protein records

        Returns:
            List of EvidenceItem objects
        """
        evidence_items = []

        for protein in raw_data:
            try:
                # Process disease associations
                disease_evidence = self._process_disease_associations(protein)
                evidence_items.extend(disease_evidence)

                # Process function information
                function_evidence = self._process_function(protein)
                if function_evidence:
                    evidence_items.append(function_evidence)

            except Exception as e:
                self.logger.warning(f"Failed to process UniProt record: {e}")
                continue

        return evidence_items

    def _process_disease_associations(self, protein: Dict) -> List[EvidenceItem]:
        """Process disease associations from protein record."""
        evidence_items = []

        accession = protein.get("primaryAccession", "")
        protein_name = self._get_protein_name(protein)
        gene_names = protein.get("genes", [])
        gene_name = gene_names[0].get("geneName", {}).get("value", "") if gene_names else ""

        # Get disease comments
        comments = protein.get("comments", [])
        disease_comments = [c for c in comments if c.get("commentType") == "DISEASE"]

        for disease in disease_comments:
            disease_info = disease.get("disease", {})
            disease_name = disease_info.get("diseaseId", "Unknown")
            disease_description = disease_info.get("description", "")

            # Extract indication
            indication = self._extract_indication(disease_name + " " + disease_description)
            if indication == "Unknown Indication":
                indication = disease_name

            evidence_items.append(EvidenceItem(
                source="uniprot",
                indication=indication,
                summary=f"UniProt: Protein {protein_name} ({gene_name}) is associated with {disease_name}. "
                        f"{self._truncate_text(disease_description, 150)}",
                date=None,
                url=f"https://www.uniprot.org/uniprotkb/{accession}",
                title=f"UniProt: {gene_name} - {disease_name}",
                metadata={
                    "accession": accession,
                    "protein_name": protein_name,
                    "gene_name": gene_name,
                    "disease_id": disease_info.get("diseaseAccession", ""),
                    "disease_name": disease_name,
                    "data_type": "disease_association"
                },
                relevance_score=0.65
            ))

        return evidence_items

    def _process_function(self, protein: Dict) -> Optional[EvidenceItem]:
        """Process protein function information."""
        accession = protein.get("primaryAccession", "")
        protein_name = self._get_protein_name(protein)
        gene_names = protein.get("genes", [])
        gene_name = gene_names[0].get("geneName", {}).get("value", "") if gene_names else ""

        # Get function comments
        comments = protein.get("comments", [])
        function_comments = [c for c in comments if c.get("commentType") == "FUNCTION"]

        if not function_comments:
            return None

        function_text = ""
        for fc in function_comments:
            texts = fc.get("texts", [])
            for t in texts:
                function_text += t.get("value", "") + " "

        function_text = function_text.strip()
        if not function_text:
            return None

        # Try to extract indication from function
        indication = self._extract_indication(function_text)

        return EvidenceItem(
            source="uniprot",
            indication=indication,
            summary=f"UniProt: {protein_name} ({gene_name}) function: {self._truncate_text(function_text, 250)}",
            date=None,
            url=f"https://www.uniprot.org/uniprotkb/{accession}",
            title=f"UniProt Function: {gene_name}",
            metadata={
                "accession": accession,
                "protein_name": protein_name,
                "gene_name": gene_name,
                "function": function_text,
                "data_type": "function"
            },
            relevance_score=0.55
        )

    def _get_protein_name(self, protein: Dict) -> str:
        """Extract protein name from record."""
        protein_desc = protein.get("proteinDescription", {})
        recommended = protein_desc.get("recommendedName", {})
        full_name = recommended.get("fullName", {})
        return full_name.get("value", protein.get("primaryAccession", "Unknown"))

    async def _perform_connection_test(self) -> Dict[str, Any]:
        """Test connection to UniProt REST API."""
        async with AsyncHTTPClient() as client:
            # Use a minimal search to test connectivity
            params = {
                "query": "insulin",
                "format": "json",
                "fields": "accession",
                "size": 1
            }

            headers = {"Accept": "application/json"}
            response = await client.get(
                f"{self.base_url}/search",
                params=params,
                headers=headers
            )

            results = response.get("results", []) if isinstance(response, dict) else []

            return {
                "message": "UniProt REST API connected successfully",
                "details": {
                    "endpoint": self.base_url,
                    "test_query_results": len(results),
                    "api_responding": True
                }
            }
