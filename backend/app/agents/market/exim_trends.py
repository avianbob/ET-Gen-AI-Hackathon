# backend/app/agents/market/exim_trends.py
"""EXIM (Export–Import) trade trends via LLM only. Gemini with Groq fallback; no dummy data."""
import json
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest

if TYPE_CHECKING:
    from ...services.gemini_service import GeminiService


class EXIMTrendAgent(BaseAgent):
    """
    AI-powered EXIM trade trend agent. Uses LLM only (Gemini with Groq fallback).
    No simulated/dummy data. Returns chart-ready trade_trend, regional_trade, scores.
    """

    def __init__(self, name: str | None = None, gemini_service: Optional["GeminiService"] = None) -> None:
        super().__init__(name=name)
        self.gemini_service = gemini_service

    async def run(self, request: AnalysisRequest):
        molecule = request.molecule_name or "Unknown"

        if not self.gemini_service:
            return self._result(
                summary=f"EXIM analysis unavailable: no LLM configured. Set GEMINI_API_KEY or GROQ_API_KEY in .env.",
                raw_data=_empty_exim_data(),
            )

        fallback_list = getattr(request, "llm_fallback_used", None)
        prompt = f"""Act as a pharmaceutical trade analyst. Analyze the Import/Export (EXIM) trends for the API '{molecule}'.

Use realistic magnitudes: for high-volume generics (e.g. Metformin, Paracetamol) global trade in this API is hundreds of millions to low single-digit billions USD; import_value_billion_usd and export_value_billion_usd should be in 0.1–2.0 range for such APIs. For niche APIs use lower values (0.01–0.5). Indices are base-100 (e.g. 2020 = 100); later years can be 95–120. Regional shares should sum to sensible totals.

Return a strictly valid JSON object (no markdown, no code fence) with exactly this structure:
{{
  "import_dependency_score": <float 0.0-1.0, 1.0 = high dependency>,
  "export_opportunity_score": <float 0.0-1.0, 1.0 = high opportunity>,
  "overall_market_demand_score": <float 0.0-1.0>,
  "supply_chain_risk": "High|Medium|Low",
  "tariff_impact": "<short sentence>",
  "trade_trend": [
    {{ "year": "2020", "import_index": 100, "export_index": 100, "import_value_billion_usd": <float>, "export_value_billion_usd": <float> }},
    {{ "year": "2021", ... }},
    {{ "year": "2022", ... }},
    {{ "year": "2023", ... }},
    {{ "year": "2024", ... }}
  ],
  "regional_trade": [
    {{ "region": "China", "import_share_percent": <float>, "export_share_percent": <float> }},
    {{ "region": "India", ... }},
    {{ "region": "USA", ... }},
    {{ "region": "EU", ... }}
  ],
  "technical_details": {{
    "methodology": "AI-synthesized trade analysis.",
    "currency": "USD",
    "definition_import_dependency": "Ratio of domestic consumption met by imports.",
    "definition_export_opportunity": "Growth potential in regulated markets."
  }}
}}"""

        try:
            response = self.gemini_service._generate_content_with_retry(
                prompt,
                operation_name="EXIMTrendAgent",
                fallback_used_list=fallback_list,
            )
            text = (response.text or "").strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", re.sub(r"\s*```\s*$", "", text)).strip()
            data = json.loads(cleaned)

            for key in ("import_dependency_score", "export_opportunity_score", "overall_market_demand_score"):
                if key in data and isinstance(data[key], (int, float)):
                    data[key] = self._clamp_score(float(data[key]))

            data.setdefault("trade_trend", [])
            data.setdefault("regional_trade", [])
            data.setdefault("technical_details", {})
            data.setdefault("supply_chain_risk", "Medium")
            data.setdefault("tariff_impact", "Potential tariff changes may affect cross-border API trade.")

            regions_preview = ", ".join([r.get("region", "") for r in data.get("regional_trade", [])[:2]])
            summary = (
                f"EXIM analysis for {molecule}: import dependency {data.get('import_dependency_score', 0):.2f}, "
                f"export opportunity {data.get('export_opportunity_score', 0):.2f}. "
                f"Supply chain risk: {data.get('supply_chain_risk', 'N/A')}. Key regions: {regions_preview or 'N/A'}."
            )
            return self._result(summary=summary, raw_data=data)
        except json.JSONDecodeError as e:
            print(f"[EXIMTrendAgent] JSON parse failed: {e}")
            return self._result(
                summary=f"EXIM data for {molecule} could not be parsed from LLM response.",
                raw_data=_empty_exim_data(),
            )
        except Exception as e:
            print(f"[EXIMTrendAgent] LLM failed: {e}")
            return self._result(
                summary=f"EXIM analysis failed for {molecule}: {e}. Check GEMINI_API_KEY and GROQ_API_KEY.",
                raw_data=_empty_exim_data(),
            )


def _empty_exim_data() -> Dict[str, Any]:
    """Minimal structure when LLM is unavailable or fails; no dummy values."""
    return {
        "import_dependency_score": 0.0,
        "export_opportunity_score": 0.0,
        "overall_market_demand_score": 0.0,
        "supply_chain_risk": "N/A",
        "tariff_impact": "Data unavailable.",
        "trade_trend": [],
        "regional_trade": [],
        "technical_details": {
            "methodology": "LLM-based; data unavailable for this run.",
            "currency": "USD",
        },
    }
