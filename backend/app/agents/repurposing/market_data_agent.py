"""
Market Data Agent - Fetches free epidemiology data from public APIs.
Sources: WHO Global Health Observatory, Wikidata SPARQL, Europe PMC
"""

import asyncio
from typing import Dict, List, Any, Optional
import aiohttp
import re
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("agents.market_data")


class MarketDataAgent:
    """
    Fetches free epidemiology and market data from public APIs.
    Used to supplement built-in market estimates with real-time data.
    """

    # WHO GHO API endpoints
    WHO_GHO_BASE = "https://ghoapi.azureedge.net/api"

    # Wikidata SPARQL endpoint
    WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

    # Europe PMC API endpoint
    EUROPE_PMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"

    # Disease name to ICD-10 code mapping for WHO queries
    DISEASE_ICD10_MAP = {
        "diabetes": "E10-E14",
        "type 2 diabetes": "E11",
        "type 1 diabetes": "E10",
        "cancer": "C00-C97",
        "breast cancer": "C50",
        "lung cancer": "C33-C34",
        "colorectal cancer": "C18-C21",
        "cardiovascular": "I00-I99",
        "hypertension": "I10-I15",
        "heart failure": "I50",
        "stroke": "I60-I69",
        "copd": "J44",
        "asthma": "J45",
        "alzheimer": "G30",
        "parkinson": "G20",
        "depression": "F32-F33",
        "anxiety": "F40-F41",
        "hiv": "B20-B24",
        "tuberculosis": "A15-A19",
        "malaria": "B50-B54",
    }

    # Wikidata disease entity IDs
    DISEASE_WIKIDATA_MAP = {
        "diabetes": "Q12206",
        "type 2 diabetes": "Q3025883",
        "cancer": "Q12078",
        "breast cancer": "Q128581",
        "lung cancer": "Q47912",
        "alzheimer": "Q11081",
        "parkinson": "Q11085",
        "depression": "Q42844",
        "hypertension": "Q41861",
        "asthma": "Q35869",
        "copd": "Q199804",
        "hiv": "Q15787",
        "stroke": "Q12202",
        "heart failure": "Q181754",
        "obesity": "Q12174",
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = get_logger("agents.MarketDataAgent")
        self.timeout = aiohttp.ClientTimeout(total=30)
        self._cache = {}  # Simple in-memory cache

    async def fetch_market_data(self, indication: str) -> Dict[str, Any]:
        """
        Fetch market/epidemiology data from multiple free sources.

        Args:
            indication: Disease/indication name

        Returns:
            Dict with prevalence, incidence, and market estimates
        """
        indication_lower = indication.lower().strip()

        # Check cache first
        if indication_lower in self._cache:
            self.logger.debug(f"Cache hit for {indication}")
            return self._cache[indication_lower]

        self.logger.info(f"Fetching market data for: {indication}")

        # Fetch from multiple sources in parallel
        results = await asyncio.gather(
            self._fetch_who_data(indication_lower),
            self._fetch_wikidata_prevalence(indication_lower),
            self._fetch_europepmc_epidemiology(indication_lower),
            return_exceptions=True
        )

        who_data = results[0] if not isinstance(results[0], Exception) else {}
        wikidata = results[1] if not isinstance(results[1], Exception) else {}
        pmc_data = results[2] if not isinstance(results[2], Exception) else {}

        # Combine data from all sources
        combined = self._combine_market_data(indication_lower, who_data, wikidata, pmc_data)

        # Cache the result
        self._cache[indication_lower] = combined

        return combined

    async def _fetch_who_data(self, indication: str) -> Dict[str, Any]:
        """
        Fetch disease burden data from WHO Global Health Observatory.
        Returns DALYs, mortality rates, prevalence estimates.
        """
        try:
            # Find ICD-10 code for indication
            icd_code = None
            for disease, code in self.DISEASE_ICD10_MAP.items():
                if disease in indication or indication in disease:
                    icd_code = code
                    break

            if not icd_code:
                return {}

            # WHO GHO indicator codes
            # DALY_0000091 = DALYs by cause
            # MORT_0000091 = Deaths by cause
            url = f"{self.WHO_GHO_BASE}/DALY_0000091"

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params={"$filter": f"contains(Dim1, '{icd_code}')"}) as response:
                    if response.status != 200:
                        self.logger.warning(f"WHO GHO API returned {response.status}")
                        return {}

                    data = await response.json()

                    if not data.get("value"):
                        return {}

                    # Extract global burden estimates
                    total_dalys = 0
                    for item in data["value"]:
                        if item.get("SpatialDim") == "GLOBAL":
                            total_dalys += float(item.get("NumericValue", 0) or 0)

                    return {
                        "source": "WHO_GHO",
                        "dalys_millions": round(total_dalys / 1_000_000, 2) if total_dalys else None,
                        "icd_code": icd_code
                    }

        except Exception as e:
            self.logger.warning(f"WHO GHO fetch failed: {e}")
            return {}

    async def _fetch_wikidata_prevalence(self, indication: str) -> Dict[str, Any]:
        """
        Query Wikidata for disease prevalence and patient population.
        """
        try:
            # Find Wikidata entity ID
            entity_id = None
            for disease, qid in self.DISEASE_WIKIDATA_MAP.items():
                if disease in indication or indication in disease:
                    entity_id = qid
                    break

            if not entity_id:
                # Try searching Wikidata for the disease
                entity_id = await self._search_wikidata_entity(indication)

            if not entity_id:
                return {}

            # SPARQL query for disease prevalence and epidemiology
            query = f"""
            SELECT ?prevalence ?incidence ?population WHERE {{
              OPTIONAL {{ wd:{entity_id} wdt:P1193 ?prevalence . }}
              OPTIONAL {{ wd:{entity_id} wdt:P3457 ?incidence . }}
              OPTIONAL {{ wd:{entity_id} wdt:P1538 ?population . }}
            }}
            LIMIT 1
            """

            headers = {
                "User-Agent": "RepurposeAI/1.0 (Drug Repurposing Research Platform)",
                "Accept": "application/sparql-results+json"
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    self.WIKIDATA_SPARQL,
                    params={"query": query, "format": "json"},
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return {}

                    data = await response.json()
                    bindings = data.get("results", {}).get("bindings", [])

                    if not bindings:
                        return {}

                    result = bindings[0]
                    prevalence = result.get("prevalence", {}).get("value")
                    incidence = result.get("incidence", {}).get("value")
                    population = result.get("population", {}).get("value")

                    return {
                        "source": "Wikidata",
                        "entity_id": entity_id,
                        "prevalence_rate": float(prevalence) if prevalence else None,
                        "incidence_rate": float(incidence) if incidence else None,
                        "affected_population": int(float(population)) if population else None
                    }

        except Exception as e:
            self.logger.warning(f"Wikidata fetch failed: {e}")
            return {}

    async def _search_wikidata_entity(self, term: str) -> Optional[str]:
        """Search Wikidata for a disease entity by name."""
        try:
            url = "https://www.wikidata.org/w/api.php"
            params = {
                "action": "wbsearchentities",
                "search": term,
                "language": "en",
                "type": "item",
                "limit": 5,
                "format": "json"
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()
                    results = data.get("search", [])

                    # Look for disease-related entities
                    for result in results:
                        desc = result.get("description", "").lower()
                        if any(kw in desc for kw in ["disease", "disorder", "syndrome", "condition", "illness"]):
                            return result.get("id")

                    return results[0]["id"] if results else None

        except Exception as e:
            self.logger.warning(f"Wikidata search failed: {e}")
            return None

    async def _fetch_europepmc_epidemiology(self, indication: str) -> Dict[str, Any]:
        """
        Search Europe PMC for epidemiology statistics from research literature.
        Extracts prevalence/incidence mentions from abstracts.
        """
        try:
            # Search for epidemiology studies
            query = f'"{indication}" AND (prevalence OR incidence OR epidemiology) AND ("million" OR "billion")'

            url = f"{self.EUROPE_PMC_BASE}/search"
            params = {
                "query": query,
                "format": "json",
                "pageSize": 10,
                "resultType": "lite"
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return {}

                    data = await response.json()
                    results = data.get("resultList", {}).get("result", [])

                    if not results:
                        return {}

                    # Extract prevalence numbers from abstracts
                    prevalence_mentions = []
                    for article in results[:5]:
                        abstract = article.get("abstractText", "")
                        if abstract:
                            # Look for patterns like "X million patients" or "prevalence of X%"
                            patterns = [
                                r'(\d+(?:\.\d+)?)\s*million\s*(?:patients|people|individuals|cases)',
                                r'prevalence\s*(?:of|is|was)?\s*(\d+(?:\.\d+)?)\s*%',
                                r'(\d+(?:\.\d+)?)\s*%\s*(?:prevalence|of the population)',
                                r'affects?\s*(\d+(?:\.\d+)?)\s*million',
                            ]

                            for pattern in patterns:
                                matches = re.findall(pattern, abstract.lower())
                                prevalence_mentions.extend(matches)

                    # Estimate patient population from mentions
                    patient_millions = None
                    if prevalence_mentions:
                        try:
                            numbers = [float(m) for m in prevalence_mentions if float(m) < 10000]
                            if numbers:
                                patient_millions = max(numbers)  # Take highest credible estimate
                        except ValueError:
                            pass

                    return {
                        "source": "EuropePMC",
                        "studies_found": len(results),
                        "patient_population_millions": patient_millions
                    }

        except Exception as e:
            self.logger.warning(f"Europe PMC fetch failed: {e}")
            return {}

    def _combine_market_data(
        self,
        indication: str,
        who_data: Dict,
        wikidata: Dict,
        pmc_data: Dict
    ) -> Dict[str, Any]:
        """
        Combine data from multiple sources into unified market data estimate.
        """
        combined = {
            "indication": indication,
            "sources_used": [],
            "patient_population_millions": None,
            "prevalence_rate": None,
            "dalys_millions": None,
            "estimated_market_size_billions": None,
            "data_quality": "low"
        }

        # WHO data - DALYs
        if who_data and who_data.get("dalys_millions"):
            combined["dalys_millions"] = who_data["dalys_millions"]
            combined["sources_used"].append("WHO_GHO")

        # Wikidata - prevalence and population
        if wikidata:
            if wikidata.get("prevalence_rate"):
                combined["prevalence_rate"] = wikidata["prevalence_rate"]
            if wikidata.get("affected_population"):
                combined["patient_population_millions"] = wikidata["affected_population"] / 1_000_000
            combined["sources_used"].append("Wikidata")

        # Europe PMC - patient population from literature
        if pmc_data and pmc_data.get("patient_population_millions"):
            # Use PMC data if no Wikidata population available
            if not combined["patient_population_millions"]:
                combined["patient_population_millions"] = pmc_data["patient_population_millions"]
            combined["sources_used"].append("EuropePMC")

        # Estimate market size based on patient population (rough heuristic)
        if combined["patient_population_millions"]:
            pop = combined["patient_population_millions"]
            # Rough estimate: $1000-5000 per patient per year treatment cost
            # Market size = population * avg treatment cost * treatment rate
            combined["estimated_market_size_billions"] = round(pop * 0.003, 1)  # Conservative estimate

        # Assess data quality
        source_count = len(combined["sources_used"])
        if source_count >= 2:
            combined["data_quality"] = "high"
        elif source_count == 1:
            combined["data_quality"] = "medium"
        else:
            combined["data_quality"] = "low"

        self.logger.info(f"Combined market data for {indication}: {source_count} sources, quality={combined['data_quality']}")

        return combined

    async def batch_fetch(self, indications: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch market data for multiple indications in parallel.

        Args:
            indications: List of indication names

        Returns:
            Dict mapping indication to market data
        """
        tasks = [self.fetch_market_data(ind) for ind in indications]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            ind: (result if not isinstance(result, Exception) else {})
            for ind, result in zip(indications, results)
        }

    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache = {}
