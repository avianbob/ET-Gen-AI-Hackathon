"""
Literature Agent - Searches PubMed for scientific publications about drug repurposing.
Uses NCBI Entrez E-utilities API via BioPython.
"""

from typing import Dict, List, Any
from datetime import datetime
import asyncio
from Bio import Entrez
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem
from app.services.repurpose.utils.api_clients import rate_limited
from app.repurpose_settings import settings

# Set email for NCBI (required by Entrez)
Entrez.email = "drug-repurposing-platform@example.com"


class LiteratureAgent(BaseAgent):
    """Agent for searching PubMed/NCBI literature."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.max_results = self.config.get("max_results", 50)
        self.database = "pubmed"

    @rate_limited(settings.PUBMED_RATE_LIMIT)
    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch literature from PubMed using Entrez API.

        Args:
            drug_name: Drug name to search for
            context: Additional search context

        Returns:
            List of publication dictionaries
        """
        drug_name = self._sanitize_drug_name(drug_name)

        # Construct search query
        search_term = f"{drug_name} AND (repurposing OR repositioning OR new indication OR off-label)"

        self.logger.info(f"Searching PubMed with query: {search_term}")

        try:
            # Run Entrez search in thread pool (Entrez is synchronous)
            loop = asyncio.get_event_loop()
            articles = await loop.run_in_executor(
                None,
                self._search_pubmed_sync,
                search_term
            )

            return articles

        except Exception as e:
            self.logger.error(f"PubMed search failed: {e}")
            raise

    def _search_pubmed_sync(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Synchronous PubMed search using Entrez (to be run in thread pool).

        Args:
            search_term: Search query

        Returns:
            List of article dictionaries
        """
        try:
            # Step 1: Search for PMIDs
            handle = Entrez.esearch(
                db=self.database,
                term=search_term,
                retmax=self.max_results,
                sort="relevance"
            )
            search_results = Entrez.read(handle)
            handle.close()

            pmids = search_results.get("IdList", [])

            if not pmids:
                self.logger.warning(f"No results found for query: {search_term}")
                return []

            self.logger.info(f"Found {len(pmids)} PMIDs")

            # Step 2: Fetch article details
            handle = Entrez.efetch(
                db=self.database,
                id=",".join(pmids),
                rettype="medline",
                retmode="xml"
            )
            records = Entrez.read(handle)
            handle.close()

            # Parse articles
            articles = []
            for article_data in records.get("PubmedArticle", []):
                try:
                    article = self._parse_article(article_data)
                    if article:
                        articles.append(article)
                except Exception as e:
                    self.logger.warning(f"Failed to parse article: {e}")
                    continue

            return articles

        except Exception as e:
            self.logger.error(f"Entrez API error: {e}")
            raise

    def _parse_article(self, article_data: Dict) -> Dict[str, Any]:
        """
        Parse article data from Entrez XML format.

        Args:
            article_data: Raw article data from Entrez

        Returns:
            Parsed article dictionary
        """
        try:
            medline = article_data.get("MedlineCitation", {})
            article_info = medline.get("Article", {})

            # Extract PMID
            pmid = str(medline.get("PMID", ""))

            # Extract title
            title = article_info.get("ArticleTitle", "No title")

            # Extract abstract
            abstract_data = article_info.get("Abstract", {})
            abstract_texts = abstract_data.get("AbstractText", [])

            if isinstance(abstract_texts, list):
                abstract = " ".join(str(text) for text in abstract_texts)
            else:
                abstract = str(abstract_texts) if abstract_texts else ""

            # Extract publication date
            pub_date = article_info.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
            year = pub_date.get("Year", "")

            # Extract authors
            author_list = article_info.get("AuthorList", [])
            authors = []
            for author in author_list[:3]:  # First 3 authors
                last_name = author.get("LastName", "")
                if last_name:
                    authors.append(last_name)

            return {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "year": year,
                "authors": authors,
                "full_text": f"{title}. {abstract}"
            }

        except Exception as e:
            self.logger.warning(f"Failed to parse article: {e}")
            return None

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """
        Process PubMed articles into evidence items.

        Args:
            raw_data: List of article dictionaries

        Returns:
            List of EvidenceItem objects
        """
        evidence_items = []

        for article in raw_data:
            try:
                # Extract indication from title and abstract
                full_text = article.get("full_text", "")
                indication = self._extract_indication(full_text)

                pmid = article.get("pmid", "")
                article_title = article.get("title", "")
                authors_list = article.get("authors", [])
                authors_str = ",".join(authors_list) if authors_list else ""

                # Create evidence item
                evidence = EvidenceItem(
                    source="literature",
                    indication=indication,
                    summary=self._create_summary(article),
                    date=article.get("year", ""),
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                    title=article_title,
                    metadata={
                        "pmid": pmid,
                        "year": article.get("year", ""),
                        "authors": authors_str,
                        "title": article_title
                    },
                    relevance_score=self._calculate_relevance(article)
                )

                evidence_items.append(evidence)

            except Exception as e:
                self.logger.warning(f"Failed to process article: {e}")
                continue

        return evidence_items

    def _create_summary(self, article: Dict[str, Any]) -> str:
        """
        Create concise summary from article.

        Args:
            article: Article dictionary

        Returns:
            Summary string
        """
        title = article.get("title", "")
        abstract = article.get("abstract", "")

        # Use abstract first sentence or title if no abstract
        if abstract:
            # Take first 2 sentences from abstract
            sentences = abstract.split(". ")[:2]
            summary = ". ".join(sentences)
            if not summary.endswith("."):
                summary += "."
        else:
            summary = title

        return self._truncate_text(summary, max_length=300)

    def _calculate_relevance(self, article: Dict[str, Any]) -> float:
        """
        Calculate relevance score for article.

        Args:
            article: Article dictionary

        Returns:
            Relevance score (0-1)
        """
        score = 0.5  # Base score

        # Boost for recent publications
        year = article.get("year", "")
        if year:
            try:
                year_int = int(year)
                current_year = datetime.now().year
                years_ago = current_year - year_int

                if years_ago <= 3:
                    score += 0.3
                elif years_ago <= 5:
                    score += 0.2
                elif years_ago <= 10:
                    score += 0.1
            except ValueError:
                pass

        # Boost for repurposing keywords in title
        title_lower = article.get("title", "").lower()
        repurposing_keywords = ["repurposing", "repositioning", "new indication", "off-label", "novel use"]

        for keyword in repurposing_keywords:
            if keyword in title_lower:
                score += 0.1
                break

        return min(score, 1.0)

    async def _perform_connection_test(self) -> Dict[str, Any]:
        """Test connection to PubMed/NCBI Entrez API."""
        loop = asyncio.get_event_loop()

        def _test_entrez():
            # Use einfo to get database info - minimal API call
            handle = Entrez.einfo(db="pubmed")
            result = Entrez.read(handle)
            handle.close()
            return result

        result = await loop.run_in_executor(None, _test_entrez)
        db_info = result.get("DbInfo", {})

        return {
            "message": "PubMed/NCBI Entrez API connected successfully",
            "details": {
                "database": "pubmed",
                "description": db_info.get("Description", "PubMed database"),
                "record_count": db_info.get("Count", "Unknown"),
                "last_update": db_info.get("LastUpdate", "Unknown")
            }
        }
