"""
EXIM Pipeline Agent - Wraps EXIMAgent for the LangGraph pipeline.

Converts EXIM trade data into EvidenceItem format so it integrates
with the 15-agent pipeline and 4D scoring system.
"""

from typing import Dict, List, Any
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem
from app.agents.repurposing.exim_agent import EXIMAgent
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("agents.exim_pipeline")


class EXIMPipelineAgent(BaseAgent):
    """Pipeline wrapper for EXIM Trade Agent."""

    def __init__(self, config=None):
        super().__init__(config)
        self.exim = EXIMAgent()

    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch EXIM trade data."""
        result = await self.exim.get_trade_data(drug_name)
        data = result.get("data", {})
        if not data or data.get("molecule") == "Unknown":
            return []
        return [data]

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """Convert EXIM trade data into evidence items."""
        evidence = []
        if not raw_data:
            return evidence

        data = raw_data[0]

        # Create evidence for overall trade profile
        evidence.append(EvidenceItem(
            source="EXIM Trade Data",
            indication="Drug Repurposing (General)",
            summary=(
                f"Global trade: {data.get('global_trade_volume_mt', 0):,.0f} MT, "
                f"${data.get('global_trade_value_usd', 0):,.0f} value. "
                f"5-year CAGR: {data.get('cagr_5yr', 0)}%. "
                f"Trend: {data.get('trend', 'N/A')}"
            ),
            relevance_score=0.6,
            evidence_type="market_data",
        ))

        # Create evidence for each insight
        for insight in data.get("insights", []):
            evidence.append(EvidenceItem(
                source="EXIM Trade Data",
                indication="Drug Repurposing (General)",
                summary=insight,
                relevance_score=0.5,
                evidence_type="market_data",
            ))

        # Create evidence for top exporters
        for exporter in data.get("top_exporters", [])[:3]:
            evidence.append(EvidenceItem(
                source="EXIM Trade Data",
                indication="Drug Repurposing (General)",
                summary=(
                    f"{exporter['country']}: {exporter['volume_mt']:,.0f} MT exported, "
                    f"${exporter['value_usd']:,.0f} value, "
                    f"{exporter['share_pct']}% market share, "
                    f"{exporter['yoy_growth']:+.1f}% YoY growth"
                ),
                relevance_score=0.5,
                evidence_type="market_data",
            ))

        return evidence
