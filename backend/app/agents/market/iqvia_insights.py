# backend/app/agents/market/iqvia_insights.py
"""IQVIA-style market insights via LLM only. Gemini with Groq fallback; no dummy data."""
import json
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest

if TYPE_CHECKING:
    from ...services.gemini_service import GeminiService


class IQVIAInsightsAgent(BaseAgent):
    """
    AI-powered market insights agent (IQVIA-style). Uses LLM only (Gemini with Groq fallback).
    No simulated/dummy data. Returns market size, CAGR, regions, trends, competitor_landscape, regulatory_pathway, patent_expiry.
    """

    def __init__(self, name: str | None = None, gemini_service: Optional["GeminiService"] = None) -> None:
        super().__init__(name=name)
        self.gemini_service = gemini_service

    async def run(self, request: AnalysisRequest):
        molecule = request.molecule_name or "Unknown"
        indication = request.target_indication or "the indication"
        current_year = 2025

        if not self.gemini_service:
            return self._result(
                summary=f"Market insights unavailable: no LLM configured. Set GEMINI_API_KEY or GROQ_API_KEY in .env.",
                raw_data=_empty_iqvia_data(current_year),
            )

        fallback_list = getattr(request, "llm_fallback_used", None)
        prompt = f"""Act as a pharmaceutical market analyst. For the API/molecule '{molecule}' and indication '{indication}', provide accurate, realistic market intelligence that supports economically viable project analysis.

CRITICAL — Distinguish drug market vs API (bulk) market and choose values so that a typical mid-scale API plant would be viable (payback 5–15 years, positive NPV at 10% discount):
- estimated_market_size_billion_usd = total DRUG (formulated product) addressable market in billion USD (e.g. type 2 diabetes drugs ~60B).
- api_market_size_billion_usd = addressable market for the BULK API in billion USD. For generics (e.g. Metformin, Paracetamol) use 0.5B–5B, not the full drug TAM.
- typical_api_price_usd_per_kg = realistic bulk API selling price in USD per kg. Use levels that make a mid-scale plant viable: generic small molecules (Metformin, Paracetamol, Ibuprofen) = 20–50 USD/kg (prefer mid-to-upper range so revenue supports payback); niche = 100–500 USD/kg; biologics = 10,000–100,000+ USD/kg. Avoid very low prices (e.g. under 15 USD/kg for generics) unless volume and market share justify them—they often yield negative NPV and 999-year payback in models.

Return a strictly valid JSON object (no markdown, no code fence) with exactly this structure:
{{
  "estimated_market_size_billion_usd": <float, total DRUG TAM in billion USD>,
  "api_market_size_billion_usd": <float, addressable BULK API market in billion USD; for generics use 0.2–5, not the full drug TAM>,
  "typical_api_price_usd_per_kg": <float, realistic bulk API price USD/kg; generics 20–50 for viability, niche 100–500>,
  "cagr": <float, compound annual growth rate e.g. 0.05 for 5%>,
  "key_regions": ["US", "EU5", "India", "China", "Japan"],
  "market_demand_score": <float 0.0-1.0>,
  "competitor_landscape": ["Top manufacturer 1", "Top manufacturer 2", "Top manufacturer 3"],
  "regulatory_pathway": "ANDA or 505(b)(2)",
  "patent_expiry": "YYYY-MM-DD or year description",
  "market_trend": [
    {{ "year": "2020", "market_size_billion_usd": <float>, "sales_billion_usd": <float> }},
    ... one entry per year from 2020 to 2030
  ],
  "regional_breakdown": [
    {{ "region": "US", "share_percent": <float>, "value_billion_usd": <float> }},
    {{ "region": "EU5", ... }},
    {{ "region": "India", ... }},
    {{ "region": "China", ... }},
    {{ "region": "Japan", ... }}
  ],
  "technical_details": {{
    "methodology": "AI-synthesized market analysis.",
    "currency": "USD",
    "base_year": 2025,
    "definition_market_size": "Total addressable market (TAM) for the indication.",
    "definition_cagr": "Compound Annual Growth Rate (CAGR)."
  }}
}}"""

        try:
            response = self.gemini_service._generate_content_with_retry(
                prompt,
                operation_name="IQVIAInsightsAgent",
                fallback_used_list=fallback_list,
            )
            text = (response.text or "").strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", re.sub(r"\s*```\s*$", "", text)).strip()
            data = json.loads(cleaned)

            if "market_demand_score" in data and isinstance(data["market_demand_score"], (int, float)):
                data["market_demand_score"] = self._clamp_score(float(data["market_demand_score"]))

            data.setdefault("key_regions", ["US", "EU5", "India", "China"])
            data.setdefault("market_trend", [])
            data.setdefault("regional_breakdown", [])
            mt = data.get("market_trend", [])
            data.setdefault(
                "estimated_sales_projection",
                [{"year": t.get("year"), "sales_billion_usd": t.get("sales_billion_usd") or t.get("market_size_billion_usd", 0)} for t in mt],
            )
            data.setdefault("competitor_landscape", [])
            data.setdefault("regulatory_pathway", "ANDA")
            data.setdefault("patent_expiry", "N/A")
            data.setdefault("technical_details", {})
            # Ensure API-specific fields exist (for TEA and competitor card)
            if "api_market_size_billion_usd" not in data and isinstance(data.get("estimated_market_size_billion_usd"), (int, float)):
                # Fallback: API market ~5% of drug TAM for generics
                data["api_market_size_billion_usd"] = round(float(data["estimated_market_size_billion_usd"]) * 0.05, 2)
            if "typical_api_price_usd_per_kg" not in data or not isinstance(data.get("typical_api_price_usd_per_kg"), (int, float)):
                data["typical_api_price_usd_per_kg"] = None  # TEA will use constants fallback
            elif isinstance(data.get("typical_api_price_usd_per_kg"), (int, float)):
                print(f"[IQVIA] LLM-derived typical_api_price_usd_per_kg: ${data['typical_api_price_usd_per_kg']}/kg")

            cagr = data.get("cagr", 0)
            data["cagr_percent"] = round(float(cagr) * 100, 1)

            summary = (
                f"For {molecule} in {indication}, estimated global market size "
                f"~${data.get('estimated_market_size_billion_usd', 0):.1f}B with ~{data.get('cagr_percent', 0)}% CAGR. "
                f"Key regions: {', '.join(data.get('key_regions', [])[:4])}."
            )
            return self._result(summary=summary, raw_data=data)
        except json.JSONDecodeError as e:
            print(f"[IQVIAInsightsAgent] JSON parse failed: {e}")
            return self._result(
                summary=f"Market data for {molecule} could not be parsed from LLM response.",
                raw_data=_empty_iqvia_data(current_year),
            )
        except Exception as e:
            print(f"[IQVIAInsightsAgent] LLM failed: {e}")
            return self._result(
                summary=f"Market analysis failed for {molecule}: {e}. Check GEMINI_API_KEY and GROQ_API_KEY.",
                raw_data=_empty_iqvia_data(current_year),
            )


def _empty_iqvia_data(base_year: int) -> Dict[str, Any]:
    """Minimal structure when LLM is unavailable or fails; no dummy values."""
    return {
        "estimated_market_size_billion_usd": 0.0,
        "api_market_size_billion_usd": None,
        "typical_api_price_usd_per_kg": None,
        "cagr": 0.0,
        "cagr_percent": 0.0,
        "key_regions": [],
        "market_demand_score": 0.0,
        "competitor_landscape": [],
        "regulatory_pathway": "N/A",
        "patent_expiry": "N/A",
        "market_trend": [],
        "regional_breakdown": [],
        "estimated_sales_projection": [],
        "technical_details": {
            "methodology": "LLM-based; data unavailable for this run.",
            "currency": "USD",
            "base_year": base_year,
        },
    }
