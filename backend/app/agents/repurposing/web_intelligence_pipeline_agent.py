"""
Web Intelligence Pipeline Agent - Wraps WebIntelligenceAgent for the LangGraph pipeline.

Converts web intelligence results (guidelines, RWE, news, publications)
into EvidenceItem format for the pipeline.
"""

from typing import Dict, List, Any
from app.agents.repurposing.base_agent import BaseAgent
from app.schemas.repurpose_api import EvidenceItem
from app.agents.repurposing.web_intelligence_agent import WebIntelligenceAgent
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("agents.web_intel_pipeline")


class WebIntelligencePipelineAgent(BaseAgent):
    """Pipeline wrapper for Web Intelligence Agent."""

    def __init__(self, config=None):
        super().__init__(config)
        self.web_agent = WebIntelligenceAgent()

    async def fetch_data(self, drug_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch web intelligence for a drug."""
        result = await self.web_agent.search(
            query=f"{drug_name} repurposing indications guidelines clinical evidence",
            entities={"drug_names": [drug_name]},
        )
        return result.get("results", [])

    async def process_data(self, raw_data: List[Dict[str, Any]], drug_name: str = "") -> List[EvidenceItem]:
        """Convert web intelligence results into evidence items."""
        evidence = []
        for item in raw_data:
            source_type = item.get("source_type", "web")
            evidence_type_map = {
                "guideline": "clinical_guideline",
                "publication": "literature",
                "rwe": "real_world_evidence",
                "news": "regulatory_news",
            }
            evidence.append(EvidenceItem(
                source="Web Intelligence",
                indication=self._extract_indication(item.get("snippet", "")),
                summary=f"[{source_type.upper()}] {item.get('title', 'Untitled')}: {item.get('snippet', '')}",
                relevance_score=0.7 if item.get("credibility") == "high" else 0.5,
                url=item.get("url", ""),
                publication_date=item.get("date", ""),
                evidence_type=evidence_type_map.get(source_type, "web_intelligence"),
            ))
        return evidence
