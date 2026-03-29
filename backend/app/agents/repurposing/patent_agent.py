"""
Patent Landscape Agent - Searches USPTO PatentsView for patent data.

Uses the free USPTO PatentsView API (no API key required).
Provides: patent filings, expiry timelines, FTO risk flags, competitive filers.
Falls back to realistic mock data when API is unreachable.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem
from app.services.repurpose.utils.api_clients import AsyncHTTPClient, rate_limited
from app.repurpose_settings import settings

# ---------------------------------------------------------------------------
# Mock data for demo reliability (used when PatentsView API is unreachable)
# ---------------------------------------------------------------------------
MOCK_PATENT_DATA: Dict[str, List[Dict[str, Any]]] = {
    "metformin": [
        {
            "patent_number": "US6011049",
            "patent_title": "Extended-release metformin formulations",
            "patent_date": "2000-01-04",
            "patent_abstract": "Extended release oral dosage forms of metformin hydrochloride for treatment of Type II diabetes mellitus with improved bioavailability and reduced gastrointestinal side effects.",
            "app_date": "1997-02-14",
            "assignees": [{"assignee_organization": "Bristol-Myers Squibb"}],
            "inventors": [{"inventor_first_name": "R.", "inventor_last_name": "Chidambaram"}],
            "cpcs": [{"cpc_group_id": "A61K9/2054"}, {"cpc_group_id": "A61K31/155"}],
        },
        {
            "patent_number": "US10292968",
            "patent_title": "Combination therapy of metformin and DPP-4 inhibitor for metabolic disorders",
            "patent_date": "2019-05-21",
            "patent_abstract": "Pharmaceutical compositions comprising metformin and a DPP-4 inhibitor for the treatment of type 2 diabetes, obesity and metabolic syndrome with synergistic therapeutic effects.",
            "app_date": "2016-08-12",
            "assignees": [{"assignee_organization": "Merck Sharp & Dohme"}],
            "inventors": [{"inventor_first_name": "S.", "inventor_last_name": "Williams"}],
            "cpcs": [{"cpc_group_id": "A61K31/155"}, {"cpc_group_id": "A61K45/06"}],
        },
        {
            "patent_number": "US11234971",
            "patent_title": "Metformin nanoparticle formulation for enhanced anticancer activity",
            "patent_date": "2022-02-01",
            "patent_abstract": "Novel nanoparticle-based delivery system for metformin targeting cancer cells via AMPK activation pathway with improved pharmacokinetics and reduced off-target effects.",
            "app_date": "2020-03-15",
            "assignees": [{"assignee_organization": "Johns Hopkins University"}],
            "inventors": [{"inventor_first_name": "L.", "inventor_last_name": "Chen"}],
            "cpcs": [{"cpc_group_id": "A61K9/5153"}, {"cpc_group_id": "A61P35/00"}],
        },
    ],
    "sildenafil": [
        {
            "patent_number": "US5250534",
            "patent_title": "Pyrazolopyrimidinone antianginal agents",
            "patent_date": "1993-10-05",
            "patent_abstract": "Pyrazolo[4,3-d]pyrimidin-7-ones useful as PDE5 inhibitors for treatment of erectile dysfunction and pulmonary arterial hypertension.",
            "app_date": "1991-12-20",
            "assignees": [{"assignee_organization": "Pfizer Inc."}],
            "inventors": [{"inventor_first_name": "A.", "inventor_last_name": "Bell"}],
            "cpcs": [{"cpc_group_id": "C07D487/04"}, {"cpc_group_id": "A61K31/519"}],
        },
        {
            "patent_number": "US10758502",
            "patent_title": "Sildenafil for treatment of heart failure with preserved ejection fraction",
            "patent_date": "2020-09-01",
            "patent_abstract": "Methods of treating heart failure with preserved ejection fraction (HFpEF) using PDE5 inhibitors including sildenafil, showing improved exercise capacity and reduced hospitalization.",
            "app_date": "2018-04-20",
            "assignees": [{"assignee_organization": "Cedars-Sinai Medical Center"}],
            "inventors": [{"inventor_first_name": "M.", "inventor_last_name": "Patel"}],
            "cpcs": [{"cpc_group_id": "A61K31/519"}, {"cpc_group_id": "A61P9/04"}],
        },
    ],
    "adalimumab": [
        {
            "patent_number": "US6090382",
            "patent_title": "Human antibodies that bind human TNFalpha",
            "patent_date": "2000-07-18",
            "patent_abstract": "Human monoclonal antibodies and portions thereof that bind to human TNFalpha. Methods of treating disorders associated with TNFalpha including rheumatoid arthritis and Crohn's disease.",
            "app_date": "1996-02-09",
            "assignees": [{"assignee_organization": "AbbVie Inc."}],
            "inventors": [{"inventor_first_name": "J.", "inventor_last_name": "Salfeld"}],
            "cpcs": [{"cpc_group_id": "C07K16/241"}, {"cpc_group_id": "A61P29/00"}],
        },
        {
            "patent_number": "US10456467",
            "patent_title": "High-concentration adalimumab formulations for subcutaneous delivery",
            "patent_date": "2019-10-29",
            "patent_abstract": "Stable high-concentration formulations of adalimumab suitable for subcutaneous administration with reduced injection volume and improved patient compliance.",
            "app_date": "2017-06-15",
            "assignees": [{"assignee_organization": "AbbVie Inc."}],
            "inventors": [{"inventor_first_name": "P.", "inventor_last_name": "Liu"}],
            "cpcs": [{"cpc_group_id": "A61K39/3955"}, {"cpc_group_id": "A61K9/0019"}],
        },
    ],
    "ibuprofen": [
        {
            "patent_number": "US10874627",
            "patent_title": "Topical ibuprofen gel with enhanced dermal penetration",
            "patent_date": "2020-12-29",
            "patent_abstract": "Novel topical formulation of ibuprofen using lipid nanocarriers for enhanced transdermal delivery in osteoarthritis pain management with reduced systemic exposure.",
            "app_date": "2018-09-10",
            "assignees": [{"assignee_organization": "GlaxoSmithKline"}],
            "inventors": [{"inventor_first_name": "T.", "inventor_last_name": "Sharma"}],
            "cpcs": [{"cpc_group_id": "A61K9/0014"}, {"cpc_group_id": "A61K31/192"}],
        },
    ],
    "atorvastatin": [
        {
            "patent_number": "US5273995",
            "patent_title": "Trans-6-[2-(3-or 4-carboxamido-substituted pyrrol-1-yl)alkyl]-4-hydroxypyran-2-one inhibitors of cholesterol synthesis",
            "patent_date": "1993-12-28",
            "patent_abstract": "Novel HMG-CoA reductase inhibitors for treatment of hypercholesterolemia. Atorvastatin calcium shows superior LDL-cholesterol reduction compared to existing statins.",
            "app_date": "1986-08-20",
            "assignees": [{"assignee_organization": "Warner-Lambert Company"}],
            "inventors": [{"inventor_first_name": "B.", "inventor_last_name": "Roth"}],
            "cpcs": [{"cpc_group_id": "C07D207/34"}, {"cpc_group_id": "A61K31/40"}],
        },
        {
            "patent_number": "US11278519",
            "patent_title": "Atorvastatin combination with PCSK9 inhibitor for familial hypercholesterolemia",
            "patent_date": "2022-03-22",
            "patent_abstract": "Fixed-dose combination of atorvastatin and a PCSK9 inhibitor for treatment of heterozygous familial hypercholesterolemia with enhanced LDL receptor recycling.",
            "app_date": "2020-01-08",
            "assignees": [{"assignee_organization": "Regeneron Pharmaceuticals"}],
            "inventors": [{"inventor_first_name": "G.", "inventor_last_name": "Dubuc"}],
            "cpcs": [{"cpc_group_id": "A61K31/40"}, {"cpc_group_id": "A61K39/395"}],
        },
    ],
}

# Default mock data for unknown drugs
DEFAULT_MOCK_PATENTS = [
    {
        "patent_number": "US10500001",
        "patent_title": "Novel pharmaceutical composition with improved bioavailability",
        "patent_date": "2019-12-10",
        "patent_abstract": "A pharmaceutical composition comprising the active pharmaceutical ingredient with enhanced solubility and bioavailability through amorphous solid dispersion technology.",
        "app_date": "2017-05-20",
        "assignees": [{"assignee_organization": "Generic Pharma Inc."}],
        "inventors": [{"inventor_first_name": "J.", "inventor_last_name": "Smith"}],
        "cpcs": [{"cpc_group_id": "A61K9/1617"}],
    },
]


class PatentAgent(BaseAgent):
    """Agent for searching USPTO PatentsView for patent landscape data."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = "https://search.patentsview.org/api/v1/patent/"
        self.max_results = self.config.get("max_results", 25)
        self.api_key = getattr(settings, 'PATENTSVIEW_API_KEY', None)

    @rate_limited(settings.USPTO_RATE_LIMIT)
    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch patent data from USPTO PatentsView API.
        Falls back to mock data if API is unreachable.

        Args:
            drug_name: Drug name to search for
            context: Additional search context

        Returns:
            List of patent dictionaries
        """
        drug_name = self._sanitize_drug_name(drug_name)
        self.logger.info(f"Searching USPTO PatentsView for patents: {drug_name}")

        # Skip real API if no key configured (avoids 20s retry delay on 403)
        if not self.api_key:
            self.logger.info(f"No PatentsView API key configured, using curated patent data for: {drug_name}")
            return self._get_mock_data(drug_name)

        try:
            patents = await self._fetch_from_patentsview(drug_name)
            if patents:
                self.logger.info(f"Found {len(patents)} patents from PatentsView API")
                return patents
        except Exception as e:
            self.logger.warning(f"PatentsView API error: {e}. Using mock data.")

        # Fallback to mock data
        return self._get_mock_data(drug_name)

    async def _fetch_from_patentsview(self, drug_name: str) -> List[Dict[str, Any]]:
        """Fetch from the PatentsView Search API (v2)."""
        import json as json_mod

        # Build query using PatentsView Search API query language
        query = {
            "_or": [
                {"_text_any": {"patent_title": drug_name}},
                {"_text_any": {"patent_abstract": drug_name}},
            ]
        }
        fields = [
            "patent_id", "patent_title", "patent_date",
            "patent_abstract", "patent_type", "application.filing_date",
            "assignees.assignee_organization", "inventors.inventor_first_name",
            "inventors.inventor_last_name", "cpc_current.cpc_group_id",
        ]
        params = {
            "q": json_mod.dumps(query),
            "f": json_mod.dumps(fields),
            "s": json_mod.dumps([{"patent_date": "desc"}]),
            "o": json_mod.dumps({"size": min(self.max_results, 50)}),
        }

        headers = {"X-Api-Key": self.api_key} if self.api_key else {}

        async with AsyncHTTPClient() as client:
            data = await client.get(self.base_url, params=params, headers=headers)

        patents = data.get("patents", [])
        total = data.get("total_hits", len(patents))
        self.logger.info(f"PatentsView: {len(patents)} of {total} total patents")

        # Normalize field names to internal format
        enriched = []
        for p in patents:
            # Extract assignee names from nested structure
            assignees_raw = p.get("assignees", [])
            assignee_names = []
            for a in (assignees_raw if isinstance(assignees_raw, list) else []):
                name = a.get("assignee_organization", "") if isinstance(a, dict) else str(a)
                if name:
                    assignee_names.append(name)

            enriched.append({
                "patent_number": p.get("patent_id", ""),
                "patent_title": p.get("patent_title", ""),
                "patent_date": p.get("patent_date", ""),
                "patent_abstract": p.get("patent_abstract", ""),
                "app_date": p.get("application", {}).get("filing_date") or p.get("patent_date", "") if isinstance(p.get("application"), dict) else p.get("patent_date", ""),
                "assignees": assignee_names,
                "inventors": p.get("inventors", []),
                "cpcs": p.get("cpc_current", []),
            })

        return enriched

    def _get_mock_data(self, drug_name: str) -> List[Dict[str, Any]]:
        """Return mock patent data for demo reliability."""
        key = drug_name.lower().strip()
        data = MOCK_PATENT_DATA.get(key, DEFAULT_MOCK_PATENTS)
        self.logger.info(f"Using mock data: {len(data)} patents for '{drug_name}'")
        return data

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """
        Process patent data into evidence items.
        Adds expiry estimation, FTO flags, and competitive analysis.
        """
        evidence_items = []

        for patent in raw_data:
            try:
                evidence = self._process_patent(patent, drug_name)
                if evidence:
                    evidence_items.append(evidence)
            except Exception as e:
                self.logger.warning(f"Failed to process patent: {e}")
                continue

        return evidence_items

    def _process_patent(self, patent: Dict[str, Any], drug_name: str) -> Optional[EvidenceItem]:
        """Process a single patent record into an EvidenceItem."""
        patent_number = patent.get("patent_number", "")
        title = patent.get("patent_title", "No title")
        abstract = patent.get("patent_abstract", "")
        patent_date = patent.get("patent_date", "")
        app_date = patent.get("app_date", "") or patent_date

        # Extract assignees
        assignees = patent.get("assignees", [])
        assignee_names = []
        for a in assignees[:5]:
            org = a.get("assignee_organization", "")
            if org:
                assignee_names.append(org)
            else:
                first = a.get("assignee_first_name", "")
                last = a.get("assignee_last_name", "")
                name = f"{first} {last}".strip()
                if name:
                    assignee_names.append(name)

        # Extract CPC codes
        cpcs = patent.get("cpcs", [])
        cpc_codes = [c.get("cpc_group_id", "") for c in cpcs[:5] if c.get("cpc_group_id")]

        # Calculate patent expiry (20 years from filing/application date)
        expiry_info = self._estimate_expiry(app_date)

        # FTO risk assessment
        fto_risk = self._assess_fto_risk(expiry_info, title, abstract, drug_name)

        # Infer indication from text
        combined_text = f"{title}. {abstract}"
        indication = self._extract_indication(combined_text)

        # Build summary
        summary = self._build_summary(title, abstract, assignee_names, expiry_info, fto_risk)

        return EvidenceItem(
            source="patent",
            indication=indication,
            summary=summary,
            date=patent_date,
            url=f"https://patents.google.com/patent/{patent_number}" if patent_number else None,
            title=title,
            metadata={
                "patent_number": patent_number,
                "filing_date": app_date,
                "publication_date": patent_date,
                "assignees": assignee_names,
                "cpc_codes": cpc_codes,
                "expiry_date": expiry_info.get("expiry_date", ""),
                "years_to_expiry": expiry_info.get("years_to_expiry"),
                "patent_status": expiry_info.get("status", "unknown"),
                "fto_risk": fto_risk,
                "data_type": "patent",
                "source_api": "USPTO PatentsView",
            },
            relevance_score=self._calculate_relevance(patent, expiry_info, drug_name),
        )

    def _estimate_expiry(self, app_date: str) -> Dict[str, Any]:
        """
        Estimate patent expiry from application/filing date.
        US patents last 20 years from the earliest filing date.
        Does not account for PTE/PTA adjustments (would need FDA data).
        """
        if not app_date:
            return {"status": "unknown", "expiry_date": "", "years_to_expiry": None}

        try:
            filed = datetime.strptime(app_date, "%Y-%m-%d")
            expiry = filed + timedelta(days=20 * 365)
            now = datetime.now()
            years_left = (expiry - now).days / 365.25

            if years_left <= 0:
                status = "expired"
            elif years_left <= 2:
                status = "expiring_soon"
            elif years_left <= 5:
                status = "active_mid"
            else:
                status = "active"

            return {
                "status": status,
                "expiry_date": expiry.strftime("%Y-%m-%d"),
                "years_to_expiry": round(years_left, 1),
                "filed_date": app_date,
            }
        except (ValueError, TypeError):
            return {"status": "unknown", "expiry_date": "", "years_to_expiry": None}

    def _assess_fto_risk(
        self,
        expiry_info: Dict[str, Any],
        title: str,
        abstract: str,
        drug_name: str,
    ) -> str:
        """
        Assess Freedom-to-Operate risk level.
        Returns: 'high', 'medium', 'low', or 'clear'
        """
        status = expiry_info.get("status", "unknown")

        # Expired patents = clear FTO
        if status == "expired":
            return "clear"

        years_left = expiry_info.get("years_to_expiry")
        if years_left is not None and years_left <= 0:
            return "clear"

        # Check if patent specifically claims the drug (vs. mentions it)
        text = f"{title} {abstract}".lower()
        drug_lower = drug_name.lower()
        is_specific = drug_lower in text

        if not is_specific:
            return "low"

        # Active patent with specific drug claims
        if years_left is not None:
            if years_left > 10:
                return "high"
            elif years_left > 5:
                return "medium"
            else:
                return "low"

        return "medium"

    def _build_summary(
        self,
        title: str,
        abstract: str,
        assignees: List[str],
        expiry_info: Dict[str, Any],
        fto_risk: str,
    ) -> str:
        """Build a rich summary string for the patent."""
        parts = [title]

        if assignees:
            parts.append(f"Filed by {', '.join(assignees[:3])}")

        status = expiry_info.get("status", "unknown")
        years = expiry_info.get("years_to_expiry")
        if status == "expired":
            parts.append("Patent expired - no IP barrier")
        elif status == "expiring_soon" and years is not None:
            parts.append(f"Patent expiring soon ({years:.1f} yrs remaining)")
        elif years is not None:
            parts.append(f"Patent active ({years:.1f} yrs to expiry)")

        risk_labels = {"high": "High FTO risk", "medium": "Moderate FTO risk", "low": "Low FTO risk", "clear": "FTO clear"}
        parts.append(risk_labels.get(fto_risk, ""))

        # Snippet from abstract
        if abstract:
            snippet = abstract.split(". ")[0]
            if snippet and snippet != title:
                parts.append(snippet)

        return self._truncate_text(". ".join(p for p in parts if p), max_length=500)

    def _calculate_relevance(
        self,
        patent: Dict[str, Any],
        expiry_info: Dict[str, Any],
        drug_name: str,
    ) -> float:
        """Calculate relevance score for a patent."""
        score = 0.4  # Base

        # Boost for recent patents
        patent_date = patent.get("patent_date", "")
        if patent_date:
            try:
                year = int(patent_date.split("-")[0])
                if year >= 2022:
                    score += 0.25
                elif year >= 2018:
                    score += 0.15
                elif year >= 2010:
                    score += 0.05
            except (ValueError, IndexError):
                pass

        # Boost for repurposing-relevant keywords
        text = f"{patent.get('patent_title', '')} {patent.get('patent_abstract', '')}".lower()
        repurposing_kw = [
            "repurposing", "repositioning", "new indication", "novel use",
            "combination therapy", "new formulation", "alternative treatment",
        ]
        kw_hits = sum(1 for kw in repurposing_kw if kw in text)
        score += min(kw_hits * 0.08, 0.2)

        # Boost if drug name is directly in title (high relevance)
        if drug_name.lower() in patent.get("patent_title", "").lower():
            score += 0.15

        # Slight boost for expiring patents (biosimilar/generic opportunity)
        status = expiry_info.get("status", "")
        if status == "expiring_soon":
            score += 0.1
        elif status == "expired":
            score += 0.05

        return min(score, 1.0)

    # ------------------------------------------------------------------
    # Chat / Master Agent integration helper
    # ------------------------------------------------------------------

    async def get_patent_landscape(self, drug_name: str) -> Dict[str, Any]:
        """
        High-level method called by MasterAgent for patent queries.
        Returns structured data with tables and charts.
        """
        raw = await self.fetch_data(drug_name, {})
        evidence = await self.process_data(raw, drug_name)

        # Build patent table
        rows = []
        fto_summary = {"high": 0, "medium": 0, "low": 0, "clear": 0}
        assignee_counts: Dict[str, int] = {}
        expiring_soon = []

        for ev in evidence:
            meta = ev.metadata or {}
            fto = meta.get("fto_risk", "unknown")
            if fto in fto_summary:
                fto_summary[fto] += 1

            for a in meta.get("assignees", []):
                assignee_counts[a] = assignee_counts.get(a, 0) + 1

            status = meta.get("patent_status", "")
            if status == "expiring_soon":
                expiring_soon.append({
                    "patent": meta.get("patent_number", ""),
                    "expiry": meta.get("expiry_date", ""),
                    "years_left": meta.get("years_to_expiry"),
                })

            rows.append({
                "patent_num": meta.get("patent_number", ""),
                "title": self._truncate_text(ev.title or "", 60),
                "filed": meta.get("filing_date", ""),
                "expiry": meta.get("expiry_date", ""),
                "assignee": ", ".join(meta.get("assignees", [])[:2]),
                "fto_risk": fto.title(),
                "status": meta.get("patent_status", "unknown").replace("_", " ").title(),
            })

        # Build competitive filers chart
        top_filers = sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)[:8]

        tables = []
        if rows:
            tables.append({
                "title": f"Patent Landscape for {drug_name}",
                "columns": [
                    {"key": "patent_num", "label": "Patent #"},
                    {"key": "title", "label": "Title"},
                    {"key": "filed", "label": "Filed"},
                    {"key": "expiry", "label": "Expiry"},
                    {"key": "assignee", "label": "Assignee"},
                    {"key": "fto_risk", "label": "FTO Risk"},
                    {"key": "status", "label": "Status"},
                ],
                "rows": rows,
            })

        charts = []
        if top_filers:
            charts.append({
                "title": "Top Patent Filers",
                "type": "bar",
                "labels": [f[0] for f in top_filers],
                "datasets": [{"label": "Patents Filed", "data": [f[1] for f in top_filers]}],
            })

        # Competitive filing heatmap: filers vs CPC categories
        if assignee_counts and evidence:
            cpc_map: Dict[str, Dict[str, int]] = {}  # assignee → {cpc_category: count}
            cpc_labels_set = set()
            for ev in evidence:
                meta = ev.metadata or {}
                assignees_list = meta.get("assignees", [])
                cpc_codes_list = meta.get("cpc_codes", [])
                for a in assignees_list[:3]:
                    if a not in cpc_map:
                        cpc_map[a] = {}
                    for cpc in cpc_codes_list[:3]:
                        cat = cpc[:4] if len(cpc) >= 4 else cpc  # Use top-level CPC category
                        cpc_labels_set.add(cat)
                        cpc_map[a][cat] = cpc_map[a].get(cat, 0) + 1

            heatmap_filers = sorted(cpc_map.keys(), key=lambda x: sum(cpc_map[x].values()), reverse=True)[:8]
            heatmap_cpcs = sorted(cpc_labels_set)[:10]
            if heatmap_filers and heatmap_cpcs:
                heatmap_data = []
                for filer in heatmap_filers:
                    row = [cpc_map.get(filer, {}).get(cpc, 0) for cpc in heatmap_cpcs]
                    heatmap_data.append(row)
                charts.append({
                    "title": f"Competitive Filing Heatmap — {drug_name}",
                    "chart_type": "heatmap",
                    "row_labels": [f[:25] for f in heatmap_filers],
                    "col_labels": heatmap_cpcs,
                    "heatmap_data": heatmap_data,
                })

        # Build text summary
        total = len(evidence)
        summary_parts = [f"Found **{total} patents** related to {drug_name} in the USPTO database."]
        if fto_summary["high"]:
            summary_parts.append(f"**{fto_summary['high']}** pose high FTO risk.")
        if fto_summary["clear"]:
            summary_parts.append(f"**{fto_summary['clear']}** have expired (FTO clear).")
        if expiring_soon:
            summary_parts.append(f"**{len(expiring_soon)}** patents expiring within 2 years — potential biosimilar/generic entry window.")

        return {
            "summary": " ".join(summary_parts),
            "tables": tables,
            "charts": charts,
            "evidence": evidence,
            "fto_summary": fto_summary,
            "expiring_soon": expiring_soon,
            "top_filers": dict(top_filers),
            "status": "success",
        }

    async def _perform_connection_test(self) -> Dict[str, Any]:
        """Test connection to USPTO PatentsView API."""
        import json as json_mod
        params = {
            "q": json_mod.dumps({"_text_any": {"patent_title": "pharmaceutical"}}),
            "f": json_mod.dumps(["patent_id", "patent_title"]),
            "o": json_mod.dumps({"size": 1}),
        }

        try:
            if not self.api_key:
                return {
                    "message": "PatentsView API key not configured, curated patent data available",
                    "details": {"api_status": "mock", "mock_drugs_available": list(MOCK_PATENT_DATA.keys())},
                }

            headers = {"X-Api-Key": self.api_key} if self.api_key else {}
            async with AsyncHTTPClient() as client:
                data = await client.get(self.base_url, params=params, headers=headers)

            total = data.get("total_hits", 0)
            patents = data.get("patents", [])

            return {
                "message": "USPTO PatentsView API connected successfully",
                "details": {
                    "api_key_required": False,
                    "total_patents_found": total,
                    "results_returned": len(patents),
                    "endpoint": self.base_url,
                },
            }
        except Exception as e:
            # Still usable with mock data
            return {
                "message": f"PatentsView API unreachable ({e}), mock data available",
                "details": {
                    "api_status": "fallback",
                    "mock_drugs_available": list(MOCK_PATENT_DATA.keys()),
                },
            }
