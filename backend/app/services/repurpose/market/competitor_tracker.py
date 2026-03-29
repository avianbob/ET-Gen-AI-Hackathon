"""
Competitor Tracker - Identifies companies working on similar drug repurposing opportunities.
Uses ClinicalTrials.gov data to track competitive landscape.
"""

import asyncio
import json
import ssl
import subprocess
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import aiohttp
from app.services.repurpose.utils.api_clients import AsyncHTTPClient
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("market.competitor")


@dataclass
class CompetitorInfo:
    """Information about a competing drug development program."""
    company_name: str
    drug_name: str
    indication: str
    development_phase: str
    trial_status: str
    trial_id: Optional[str] = None
    expected_completion: Optional[str] = None
    enrollment: Optional[int] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "company_name": self.company_name,
            "drug_name": self.drug_name,
            "indication": self.indication,
            "development_phase": self.development_phase,
            "trial_status": self.trial_status,
            "trial_id": self.trial_id,
            "expected_completion": self.expected_completion,
            "enrollment": self.enrollment,
            "url": self.url
        }


@dataclass
class CompetitiveLandscape:
    """Complete competitive landscape analysis for an indication."""
    indication: str
    total_competitors: int
    active_trials: int
    companies: List[str]
    phase_distribution: Dict[str, int]
    competitive_intensity: str  # "low", "medium", "high"
    time_to_market_advantage: Optional[str] = None
    competitor_details: List[CompetitorInfo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "indication": self.indication,
            "total_competitors": self.total_competitors,
            "active_trials": self.active_trials,
            "companies": self.companies,
            "phase_distribution": self.phase_distribution,
            "competitive_intensity": self.competitive_intensity,
            "time_to_market_advantage": self.time_to_market_advantage,
            "competitor_details": [c.to_dict() for c in self.competitor_details]
        }


class CompetitorTracker:
    """
    Tracks pharmaceutical companies working on similar drug repurposing opportunities.
    Uses ClinicalTrials.gov API to gather competitive intelligence.
    """

    CT_GOV_BASE = "https://clinicaltrials.gov/api/v2/studies"

    # Known pharmaceutical company patterns
    PHARMA_KEYWORDS = [
        "pharma", "therapeutics", "biosciences", "biotech", "medicines",
        "oncology", "healthcare", "laboratories", "inc.", "ltd", "gmbh",
        "pfizer", "novartis", "roche", "merck", "sanofi", "astrazeneca",
        "bristol", "johnson", "abbvie", "gilead", "amgen", "biogen",
        "eli lilly", "lilly", "bayer", "boehringer", "gsk", "glaxo", "takeda",
        "regeneron", "vertex", "moderna", "biontech", "seagen", "jazz"
    ]

    def __init__(self):
        self.logger = get_logger("market.competitor")

    async def _fetch_with_aiohttp(self, url: str) -> Dict[str, Any]:
        """
        Fetch data using aiohttp with browser-like configuration.
        This can bypass restrictions that httpx triggers.
        """
        # Create SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Full browser-like headers including Sec-Ch-Ua
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        }

        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 403:
                    raise Exception(f"403 Forbidden - API blocking requests")
                response.raise_for_status()
                return await response.json()

    async def _fetch_with_curl(self, url: str) -> Dict[str, Any]:
        """Fallback method using curl to bypass TLS fingerprinting."""
        def run_curl():
            """Run curl synchronously."""
            try:
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

                if sys.platform == "win32":
                    cmd = [
                        'curl', '-s', '-L',
                        '-A', user_agent,
                        '-H', 'Accept: application/json',
                        '-H', 'Accept-Language: en-US,en;q=0.9',
                        url
                    ]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        encoding='utf-8',
                        errors='replace'
                    )
                else:
                    result = subprocess.run(
                        [
                            "curl", "-s", "-L",
                            "-A", user_agent,
                            "-H", "Accept: application/json",
                            "-H", "Accept-Language: en-US,en;q=0.9",
                            url
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                if result is None:
                    raise Exception("curl subprocess returned None")

                stdout = result.stdout or ""
                stderr = result.stderr or ""

                if result.returncode != 0:
                    raise Exception(f"curl failed (code {result.returncode}): {stderr}")

                if not stdout.strip():
                    raise Exception(f"curl returned empty response. stderr: {stderr}")

                return json.loads(stdout)
            except subprocess.TimeoutExpired:
                raise Exception("curl timed out after 30 seconds")
            except json.JSONDecodeError as e:
                raise Exception(f"Invalid JSON from curl: {e}")
            except FileNotFoundError:
                raise Exception("curl not available on this system")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, run_curl)

    async def find_competitors(
        self,
        indication: str,
        exclude_drug: Optional[str] = None
    ) -> List[CompetitorInfo]:
        """
        Find companies with active programs in the same indication.

        Args:
            indication: Disease/indication to search for
            exclude_drug: Optional drug name to exclude from results

        Returns:
            List of competitor information
        """
        self.logger.info(f"Finding competitors for indication: {indication}")
        competitors = []

        try:
            # Build URL with params
            from urllib.parse import quote, urlencode
            params = {
                "query.cond": indication,
                "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING,ENROLLING_BY_INVITATION",
                "countTotal": "true",
                "pageSize": 50,
                "fields": "NCTId,BriefTitle,Condition,InterventionName,LeadSponsorName,Phase,OverallStatus,PrimaryCompletionDate,EnrollmentInfo"
            }
            url = f"{self.CT_GOV_BASE}?{urlencode(params)}"

            response = None

            # Method 1: Try aiohttp first (better at bypassing bot detection)
            try:
                response = await self._fetch_with_aiohttp(url)
            except Exception as aiohttp_error:
                self.logger.debug(f"aiohttp failed: {aiohttp_error}")

            # Method 2: Try curl (bypasses TLS fingerprinting)
            if response is None:
                try:
                    response = await self._fetch_with_curl(url)
                except Exception as curl_error:
                    self.logger.debug(f"curl failed: {curl_error}")

            # Method 3: Fall back to AsyncHTTPClient (last resort)
            if response is None:
                try:
                    async with AsyncHTTPClient() as client:
                        response = await client.get(self.CT_GOV_BASE, params=params)
                except Exception as httpx_error:
                    self.logger.debug(f"httpx failed: {httpx_error}")

            if response and "studies" in response:
                studies = response.get("studies", [])

                for study in studies:
                    competitor = self._parse_study(study, exclude_drug)
                    if competitor:
                        competitors.append(competitor)

        except Exception as e:
            self.logger.error(f"Error fetching competitor data: {e}")

        # Deduplicate by company
        seen_companies = set()
        unique_competitors = []
        for comp in competitors:
            if comp.company_name not in seen_companies:
                seen_companies.add(comp.company_name)
                unique_competitors.append(comp)

        self.logger.info(f"Found {len(unique_competitors)} unique competitors")
        return unique_competitors[:15]  # Return top 15

    def _parse_study(self, study: Dict, exclude_drug: Optional[str]) -> Optional[CompetitorInfo]:
        """Parse a clinical trial study into competitor info."""
        try:
            protocol = study.get("protocolSection", {})

            # Get sponsor
            sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
            sponsor = sponsor_module.get("leadSponsor", {}).get("name", "Unknown")

            # Filter to pharmaceutical companies
            if not self._is_pharma_company(sponsor):
                return None

            # Get identification
            id_module = protocol.get("identificationModule", {})
            nct_id = id_module.get("nctId", "")
            title = id_module.get("briefTitle", "")

            # Get status
            status_module = protocol.get("statusModule", {})
            overall_status = status_module.get("overallStatus", "Unknown")
            completion_date = status_module.get("primaryCompletionDateStruct", {}).get("date", "")

            # Get phase
            design_module = protocol.get("designModule", {})
            phases = design_module.get("phases", [])
            phase = phases[0] if phases else "Unknown"

            # Get interventions (drug names)
            arms_module = protocol.get("armsInterventionsModule", {})
            interventions = arms_module.get("interventions", [])
            drug_names = [
                i.get("name", "")
                for i in interventions
                if i.get("type", "").upper() == "DRUG"
            ]
            drug_name = ", ".join(drug_names) if drug_names else "Undisclosed"

            # Exclude if matches the drug we're analyzing
            if exclude_drug and exclude_drug.lower() in drug_name.lower():
                return None

            # Get enrollment
            enrollment_info = protocol.get("designModule", {}).get("enrollmentInfo", {})
            enrollment = enrollment_info.get("count")

            # Get conditions
            conditions_module = protocol.get("conditionsModule", {})
            conditions = conditions_module.get("conditions", [])
            indication = conditions[0] if conditions else "Unknown"

            return CompetitorInfo(
                company_name=sponsor,
                drug_name=drug_name,
                indication=indication,
                development_phase=phase,
                trial_status=overall_status,
                trial_id=nct_id,
                expected_completion=completion_date,
                enrollment=enrollment,
                url=f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else None
            )

        except Exception as e:
            self.logger.debug(f"Failed to parse study: {e}")
            return None

    def _is_pharma_company(self, sponsor: str) -> bool:
        """Check if sponsor is likely a pharmaceutical company."""
        sponsor_lower = sponsor.lower()
        return any(kw in sponsor_lower for kw in self.PHARMA_KEYWORDS)

    async def get_competitive_landscape(
        self,
        indication: str,
        drug_name: Optional[str] = None
    ) -> CompetitiveLandscape:
        """
        Get complete competitive landscape analysis for an indication.

        Args:
            indication: Disease/indication to analyze
            drug_name: Optional drug to exclude from analysis

        Returns:
            CompetitiveLandscape with full analysis
        """
        self.logger.info(f"Analyzing competitive landscape for: {indication}")

        # Get competitor details
        competitors = await self.find_competitors(indication, exclude_drug=drug_name)

        # Count unique companies
        companies = list(set(c.company_name for c in competitors))

        # Calculate phase distribution
        phase_distribution = {}
        for comp in competitors:
            phase = comp.development_phase
            phase_distribution[phase] = phase_distribution.get(phase, 0) + 1

        # Count active trials
        active_trials = len(competitors)

        # Determine competitive intensity
        competitive_intensity = self._calculate_intensity(len(companies), phase_distribution)

        return CompetitiveLandscape(
            indication=indication,
            total_competitors=len(companies),
            active_trials=active_trials,
            companies=companies[:10],
            phase_distribution=phase_distribution,
            competitive_intensity=competitive_intensity,
            competitor_details=competitors[:10]
        )

    def _calculate_intensity(
        self,
        num_companies: int,
        phase_distribution: Dict[str, int]
    ) -> str:
        """
        Calculate competitive intensity level.

        Args:
            num_companies: Number of unique competitor companies
            phase_distribution: Distribution of trials by phase

        Returns:
            "low", "medium", or "high"
        """
        # Check for late-stage competition
        late_stage = sum(
            phase_distribution.get(p, 0)
            for p in ["PHASE3", "PHASE4", "Phase 3", "Phase 4", "NA"]
        )

        if num_companies >= 10 or late_stage >= 3:
            return "high"
        elif num_companies >= 5 or late_stage >= 1:
            return "medium"
        return "low"

    def calculate_competitive_score(self, landscape: CompetitiveLandscape) -> float:
        """
        Calculate competitive landscape score (0-100).
        Higher score = LESS competition (more attractive).

        Args:
            landscape: CompetitiveLandscape object

        Returns:
            Score (0-100), higher is better (less competition)
        """
        score = 100.0

        # Deduct for number of competitors (up to -40)
        if landscape.total_competitors >= 10:
            score -= 40
        elif landscape.total_competitors >= 5:
            score -= 25
        elif landscape.total_competitors >= 2:
            score -= 15
        elif landscape.total_competitors >= 1:
            score -= 5

        # Deduct for late-stage competition (up to -30)
        phase_dist = landscape.phase_distribution
        phase3_count = phase_dist.get("PHASE3", 0) + phase_dist.get("Phase 3", 0)
        phase4_count = phase_dist.get("PHASE4", 0) + phase_dist.get("Phase 4", 0)

        if phase4_count > 0:
            score -= 30  # Approved competitors
        elif phase3_count >= 3:
            score -= 25
        elif phase3_count >= 1:
            score -= 15

        # Deduct for intensity
        if landscape.competitive_intensity == "high":
            score -= 20
        elif landscape.competitive_intensity == "medium":
            score -= 10

        return max(score, 10.0)  # Minimum 10
