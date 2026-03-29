"""
IQVIA Pipeline Agent - Wraps MarketAnalyzer for the LangGraph pipeline.

Provides market size, CAGR, unmet need, and commercial viability data
as EvidenceItems so IQVIA data flows through the same pipeline as all agents.
"""

from typing import Dict, List, Any
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem
from app.services.repurpose.market.market_analyzer import MarketAnalyzer
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("agents.iqvia_pipeline")

# Top therapeutic areas to scan for a general drug analysis
SCAN_INDICATIONS = [
    "Type 2 Diabetes", "Cancer", "Alzheimer's Disease", "Cardiovascular Disease",
    "Obesity", "NASH", "Chronic Pain", "Depression", "Rheumatoid Arthritis",
    "Parkinson's Disease", "Asthma", "COPD", "Multiple Sclerosis", "Psoriasis",
]


class IQVIAPipelineAgent(BaseAgent):
    """Pipeline wrapper for IQVIA/Market Insights Agent."""

    def __init__(self, config=None):
        super().__init__(config)
        self.market_analyzer = MarketAnalyzer()

    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch market data for common therapeutic areas."""
        results = []
        for indication in SCAN_INDICATIONS:
            try:
                opp = await self.market_analyzer.analyze_market(
                    indication=indication, drug_name=drug_name
                )
                if opp and opp.estimated_market_size_usd > 0:
                    results.append({
                        "indication": indication,
                        "market_size_usd": opp.estimated_market_size_usd,
                        "cagr": opp.cagr_percent,
                        "unmet_need": opp.unmet_need_score,
                        "patient_population": getattr(opp, "patient_population", 0),
                    })
            except Exception:
                continue
        return results

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """Convert market data into evidence items."""
        evidence = []
        for item in raw_data:
            market_b = item["market_size_usd"] / 1_000_000_000
            evidence.append(EvidenceItem(
                source="IQVIA Market Intelligence",
                indication=item["indication"],
                summary=(
                    f"Market: ${market_b:.1f}B, CAGR: {item['cagr']:.1f}%, "
                    f"Unmet Need Score: {item['unmet_need']}/100"
                ),
                relevance_score=0.6,
                evidence_type="market_data",
            ))
        return evidence
