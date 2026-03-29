"""
Semantic Scholar Agent - Enhanced literature search with citation metrics.
Uses Semantic Scholar API: https://api.semanticscholar.org/
Optional API key for higher rate limits.
"""

import asyncio
from typing import Dict, List, Any, Optional
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem
from app.services.repurpose.utils.api_clients import AsyncHTTPClient, rate_limited
from app.repurpose_settings import settings


class SemanticScholarAgent(BaseAgent):
    """Agent for searching Semantic Scholar for papers with citation analysis."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.max_results = self.config.get("max_results", 50)
        self.api_key = settings.SEMANTIC_SCHOLAR_API_KEY

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers, including API key if available."""
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch papers from Semantic Scholar with citation data.

        Args:
            drug_name: Drug name to search for
            context: Additional search context

        Returns:
            List of paper results with citation information
        """
        drug_name = self._sanitize_drug_name(drug_name)
        self.logger.info(f"Searching Semantic Scholar for: {drug_name}")

        # Add initial delay to avoid rate limits when running with other agents
        # Semantic Scholar has strict rate limits (~100 req/5 min without API key)
        if not self.api_key:
            await asyncio.sleep(3.0)  # Small initial delay without API key

        results = []

        async with AsyncHTTPClient() as client:
            # Search for repurposing-related papers
            # Use a single consolidated query to reduce API calls and avoid rate limiting
            search_queries = [
                f"{drug_name} drug repurposing repositioning"
            ]

            # Only add more queries if we have an API key (higher rate limits)
            if self.api_key:
                search_queries.extend([
                    f"{drug_name} repositioning therapeutic",
                    f"{drug_name} new indication"
                ])

            for i, query in enumerate(search_queries):
                # Add delay between queries to avoid 429 rate limiting
                if i > 0:
                    await asyncio.sleep(5.0)

                papers = await self._search_papers(client, query)
                results.extend(papers)

        # Deduplicate by paper ID
        seen_ids = set()
        unique_results = []
        for paper in results:
            paper_id = paper.get("paperId")
            if paper_id and paper_id not in seen_ids:
                seen_ids.add(paper_id)
                unique_results.append(paper)

        self.logger.info(f"Found {len(unique_results)} unique papers")
        return unique_results

    async def _search_papers(self, client: AsyncHTTPClient, query: str) -> List[Dict]:
        """Search for papers matching the query with rate limit retry."""
        params = {
            "query": query,
            "limit": min(self.max_results, 100),
            "fields": "paperId,title,abstract,year,citationCount,influentialCitationCount,authors,venue,url,publicationTypes,openAccessPdf,fieldsOfStudy"
        }

        headers = self._get_headers()

        # Retry with exponential backoff for rate limits
        max_retries = 3
        base_delay = 10  # Start with 10 seconds for rate limit errors

        for attempt in range(max_retries):
            try:
                response = await client.get(
                    f"{self.base_url}/paper/search",
                    params=params,
                    headers=headers,
                    retry=False  # We handle retries ourselves for rate limits
                )

                papers = response.get("data", [])
                self.logger.debug(f"Search '{query}' returned {len(papers)} papers")
                return papers

            except Exception as http_err:
                error_str = str(http_err)

                # Handle rate limit (429) with exponential backoff
                if "429" in error_str:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # 10s, 20s, 40s
                        self.logger.warning(
                            f"Semantic Scholar rate limit hit (attempt {attempt + 1}/{max_retries}), "
                            f"waiting {delay}s before retry..."
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        self.logger.warning(f"Semantic Scholar rate limit - max retries reached for: {query}")
                        return []

                # For other errors, log and return empty
                self.logger.warning(f"Semantic Scholar search error: {http_err}")
                return []

        return []

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """
        Process Semantic Scholar papers into evidence items.

        Args:
            raw_data: List of paper data

        Returns:
            List of EvidenceItem objects
        """
        evidence_items = []

        for paper in raw_data:
            try:
                evidence = self._process_paper(paper)
                if evidence:
                    evidence_items.append(evidence)

            except Exception as e:
                self.logger.warning(f"Failed to process paper: {e}")
                continue

        # Sort by relevance score and return top results
        evidence_items.sort(key=lambda x: x.relevance_score, reverse=True)
        return evidence_items[:self.max_results]

    def _process_paper(self, paper: Dict) -> Optional[EvidenceItem]:
        """Process a single paper into an evidence item."""
        paper_id = paper.get("paperId")
        title = paper.get("title") or "Unknown Title"
        abstract = paper.get("abstract") or ""  # Ensure None becomes empty string
        year = paper.get("year")
        citation_count = paper.get("citationCount") or 0
        influential_citations = paper.get("influentialCitationCount") or 0
        venue = paper.get("venue") or ""
        url = paper.get("url") or f"https://www.semanticscholar.org/paper/{paper_id}"

        # Extract authors (handle None)
        authors = paper.get("authors") or []
        author_names = [a.get("name", "") for a in authors[:5] if a]  # First 5 authors
        author_str = ", ".join(filter(None, author_names))  # Filter out empty strings
        if len(authors) > 5:
            author_str += " et al."

        # Extract fields of study (handle None)
        fields = paper.get("fieldsOfStudy") or []

        # Extract indication from abstract
        indication = self._extract_indication(abstract) if abstract else "Unknown Indication"

        # Check for open access PDF
        open_access = paper.get("openAccessPdf", {})
        pdf_url = open_access.get("url") if open_access else None

        # Create summary
        if abstract:
            summary = self._truncate_text(abstract, 300)
        else:
            summary = f"Paper: {title}"

        if citation_count > 0:
            summary += f" [{citation_count} citations"
            if influential_citations > 0:
                summary += f", {influential_citations} influential"
            summary += "]"

        return EvidenceItem(
            source="semantic_scholar",
            indication=indication,
            summary=summary,
            date=str(year) if year else None,
            url=url,
            title=title,
            metadata={
                "paper_id": paper_id,
                "authors": author_str,
                "venue": venue,
                "year": year,
                "citation_count": citation_count,
                "influential_citations": influential_citations,
                "fields_of_study": fields,
                "pdf_url": pdf_url,
                "data_type": "paper"
            },
            relevance_score=self._calculate_relevance(paper)
        )

    def _calculate_relevance(self, paper: Dict) -> float:
        """
        Calculate relevance score based on citations, recency, and content.

        Args:
            paper: Paper data dictionary

        Returns:
            Relevance score (0-1)
        """
        score = 0.4  # Base score

        # Citation boost (up to +0.25)
        citations = paper.get("citationCount", 0)
        if citations > 500:
            score += 0.25
        elif citations > 200:
            score += 0.2
        elif citations > 100:
            score += 0.15
        elif citations > 50:
            score += 0.1
        elif citations > 10:
            score += 0.05

        # Influential citations boost (up to +0.15)
        influential = paper.get("influentialCitationCount", 0)
        if influential > 50:
            score += 0.15
        elif influential > 20:
            score += 0.1
        elif influential > 5:
            score += 0.05

        # Recency boost (up to +0.15)
        year = paper.get("year")
        if year:
            if year >= 2023:
                score += 0.15
            elif year >= 2020:
                score += 0.12
            elif year >= 2018:
                score += 0.08
            elif year >= 2015:
                score += 0.05

        # Abstract relevance boost (up to +0.1)
        abstract = (paper.get("abstract") or "").lower()
        relevance_keywords = [
            "repurposing", "repositioning", "repurposed",
            "new indication", "novel use", "off-label",
            "therapeutic potential", "clinical trial",
            "mechanism of action", "drug target"
        ]
        keyword_matches = sum(1 for kw in relevance_keywords if kw in abstract)
        score += min(keyword_matches * 0.02, 0.1)

        return min(score, 1.0)

    def _extract_indication(self, text: str) -> str:
        """Extract disease indication from abstract text."""
        if not text:
            return "Unknown Indication"

        # First try base class method
        indication = super()._extract_indication(text)

        # If found a specific indication, return it
        if indication != "Unknown Indication":
            return indication

        # Additional disease patterns for drug repurposing literature
        additional_patterns = {
            "covid": "COVID-19",
            "sars-cov": "COVID-19",
            "coronavirus": "COVID-19",
            "malaria": "Malaria",
            "tuberculosis": "Tuberculosis",
            "hiv": "HIV/AIDS",
            "aids": "HIV/AIDS",
            "leukemia": "Leukemia",
            "lymphoma": "Lymphoma",
            "glioblastoma": "Glioblastoma",
            "breast cancer": "Breast Cancer",
            "lung cancer": "Lung Cancer",
            "prostate cancer": "Prostate Cancer",
            "colorectal": "Colorectal Cancer",
            "pancreatic": "Pancreatic Cancer",
            "melanoma": "Melanoma",
            "rheumatoid": "Rheumatoid Arthritis",
            "osteoarthritis": "Osteoarthritis",
            "lupus": "Lupus",
            "inflammatory bowel": "Inflammatory Bowel Disease",
            "ulcerative colitis": "Ulcerative Colitis",
            "multiple sclerosis": "Multiple Sclerosis",
            "parkinson": "Parkinson's Disease",
            "huntington": "Huntington's Disease",
            "amyotrophic lateral": "ALS",
            "als": "ALS",
            "duchenne": "Duchenne Muscular Dystrophy",
            "cystic fibrosis": "Cystic Fibrosis",
            "sickle cell": "Sickle Cell Disease",
            "thalassemia": "Thalassemia",
            "hemophilia": "Hemophilia"
        }

        text_lower = text.lower()
        for pattern, indication_name in additional_patterns.items():
            if pattern in text_lower:
                return indication_name

        return "Unknown Indication"
