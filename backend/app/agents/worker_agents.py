# backend/app/agents/market/exim_trends.py
from typing import Any, Dict
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest


class EXIMTrendAgent(BaseAgent):
    """
    Simulated EXIM trade trend agent.
    """

    async def run(self, request: AnalysisRequest):
        data: Dict[str, Any] = {
            "import_dependency_score": 0.3,   # lower is better (less dependency)
            "export_opportunity_score": 0.75,
            "overall_market_demand_score": 0.78,
        }

        summary = (
            "EXIM analysis suggests moderate import dependency and strong export opportunities, "
            "indicating a favourable landscape for generic manufacturing."
        )

        return self._result(summary=summary, raw_data=data)
    
# backend/app/agents/market/iqvia_insights.py
from typing import Any, Dict
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest


class IQVIAInsightsAgent(BaseAgent):
    """
    Simulated agent for IQVIA-like market insights.
    In a real system this would call external APIs.
    """

    async def run(self, request: AnalysisRequest):
        molecule = request.molecule_name or "the molecule"
        indication = request.target_indication or "the indication"

        data: Dict[str, Any] = {
            "estimated_market_size_billion_usd": 1.8,
            "cagr": 0.09,
            "key_regions": ["US", "EU5", "India"],
            # 0–1 score reflecting demand strength (hard-coded heuristic)
            "market_demand_score": 0.82,
        }

        summary = (
            f"For {molecule} in {indication}, the estimated global market size is "
            f"~${data['estimated_market_size_billion_usd']}B with ~{int(data['cagr'] * 100)}% CAGR. "
            f"Strong demand is observed in {', '.join(data['key_regions'])}."
        )

        return self._result(summary=summary, raw_data=data)
# backend/app/agents/patents_trials/clinical_trials.py
from typing import Any, Dict
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest


class ClinicalTrialAgent(BaseAgent):
    """
    Looks at ongoing trials / label expansions (simulated).
    """

    async def run(self, request: AnalysisRequest):
        data: Dict[str, Any] = {
            "ongoing_trials_count": 12,
            "indication_expansion_potential_score": 0.7,
            "safety_signal_risk_score": 0.2,
            "patents_and_trials_score": 0.68,
        }

        summary = (
            "Clinical trial activity is healthy with multiple ongoing studies and limited safety concerns, "
            "supporting sustainable long-term demand for the molecule."
        )

        return self._result(summary=summary, raw_data=data)

# backend/app/agents/patents_trials/patent_landscape.py
from typing import Any, Dict
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest


class PatentLandscapeAgent(BaseAgent):
    """
    Evaluates FTO (freedom to operate) based on a simplified heuristic.
    """

    async def run(self, request: AnalysisRequest):
        data: Dict[str, Any] = {
            "primary_patents_expired": True,
            "secondary_patent_risk_score": 0.35,  # 0–1, higher = more risk
            "litigation_risk_score": 0.25,
            "patent_overall_score": 0.72,        # higher = safer
        }

        summary = (
            "Patent landscape analysis indicates that core patents are largely expired with manageable "
            "secondary and litigation risks, suggesting reasonable freedom to operate."
        )

        return self._result(summary=summary, raw_data=data)
# backend/app/agents/production/process_design.py
from typing import Any, Dict
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest


class ProcessDesignAgent(BaseAgent):
    """
    Evaluates process complexity, scalability, and continuous manufacturing fit.
    """

    async def run(self, request: AnalysisRequest):
        data: Dict[str, Any] = {
            "process_complexity_score": 0.65,      # 0–1, higher = more complex
            "scalability_score": 0.8,             # 0–1, higher = easier to scale
            "continuous_manufacturing_fit": 0.7,  # 0–1
            "production_feasibility_score": 0.76,
        }

        summary = (
            "Process design assessment indicates moderate complexity but good scalability potential. "
            "The molecule is reasonably suited for continuous manufacturing with appropriate optimisation."
        )

        return self._result(summary=summary, raw_data=data)
# backend/app/agents/production/techno_economic.py
from typing import Any, Dict
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest


class TechnoEconomicAgent(BaseAgent):
    """
    Performs a simple techno-economic assessment (placeholder logic).
    """

    async def run(self, request: AnalysisRequest):
        data: Dict[str, Any] = {
            "capex_million_usd": 25.0,
            "opex_million_usd_per_year": 6.0,
            "payback_period_years": 4.5,
            "internal_rate_of_return": 0.23,  # 23%
            "production_feasibility_score": 0.81,
        }

        summary = (
            "Techno-economic analysis suggests acceptable CAPEX and OPEX with a payback period of "
            f"{data['payback_period_years']} years and an IRR of {int(data['internal_rate_of_return'] * 100)}%, "
            "indicating strong economic feasibility for plant investment."
        )

        return self._result(summary=summary, raw_data=data)
# backend/app/agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from ..schemas.analysis import AnalysisRequest, AgentResult


class BaseAgent(ABC):
    """
    Base class for all domain agents.
    Every agent returns an AgentResult.
    """

    def __init__(self, name: str | None = None) -> None:
        self.name = name or self.__class__.__name__

    @abstractmethod
    async def run(self, request: AnalysisRequest) -> AgentResult:
        ...

    def _result(self, summary: str, raw_data: Dict[str, Any] | None = None) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            summary=summary,
            raw_data=raw_data or {},
        )
# backend/app/agents/grading.py
from dataclasses import dataclass
from typing import List, Dict
from ..schemas.analysis import AgentResult, GradingBreakdown


@dataclass
class GradingWeights:
    """
    Weightage for each group, reflecting your concept note.
    Adjust these numbers to tune the final grade.
    """
    market_demand: float = 0.25
    production_feasibility: float = 0.25
    demographics: float = 0.15
    patents_and_trials: float = 0.2
    competition: float = 0.15


class GradingAgent:
    """
    Converts agent outputs into a single composite grade (0–1).
    """

    def __init__(self, weights: GradingWeights | None = None) -> None:
        self.weights = weights or GradingWeights()

    def _extract_scores(self, results: List[AgentResult]) -> Dict[str, float]:
        """
        Reads raw_data fields from agents and computes average scores per dimension.
        This is where your 'beautiful mathematical formula' can become sophisticated.
        """

        market_scores = []
        production_scores = []
        demo_scores = []
        patents_scores = []
        competition_scores = []

        for r in results:
            rd = r.raw_data
            name = r.agent_name.lower()

            # Market, Sales & Demand group
            if "iqvia" in name or "exim" in name:
                if "market_demand_score" in rd:
                    market_scores.append(rd["market_demand_score"])
                if "overall_market_demand_score" in rd:
                    market_scores.append(rd["overall_market_demand_score"])

            # Production / Chemical Engineering group
            if "processdesign" in name or "process design" in name:
                if "production_feasibility_score" in rd:
                    production_scores.append(rd["production_feasibility_score"])
            if "techno" in name:
                if "production_feasibility_score" in rd:
                    production_scores.append(rd["production_feasibility_score"])

            # Demographic group
            if "demographic" in name:
                if "demographic_overall_score" in rd:
                    demo_scores.append(rd["demographic_overall_score"])

            # Patent & Trials group
            if "patent" in name:
                if "patent_overall_score" in rd:
                    patents_scores.append(rd["patent_overall_score"])
            if "clinical" in name:
                if "patents_and_trials_score" in rd:
                    patents_scores.append(rd["patents_and_trials_score"])

            # Competition group
            if "competition" in name:
                if "competition_overall_score" in rd:
                    competition_scores.append(rd["competition_overall_score"])

        def avg(lst: List[float], default: float = 0.5) -> float:
            return sum(lst) / len(lst) if lst else default

        scores = {
            "market_demand": avg(market_scores),
            "production_feasibility": avg(production_scores),
            "demographics": avg(demo_scores),
            "patents_and_trials": avg(patents_scores),
            "competition": avg(competition_scores),
        }

        return scores

    def grade(self, results: List[AgentResult]) -> GradingBreakdown:
        scores = self._extract_scores(results)

        overall = (
            scores["market_demand"] * self.weights.market_demand
            + scores["production_feasibility"] * self.weights.production_feasibility
            + scores["demographics"] * self.weights.demographics
            + scores["patents_and_trials"] * self.weights.patents_and_trials
            + scores["competition"] * self.weights.competition
        )

        return GradingBreakdown(
            market_demand=scores["market_demand"],
            production_feasibility=scores["production_feasibility"],
            demographics=scores["demographics"],
            patents_and_trials=scores["patents_and_trials"],
            competition=scores["competition"],
            overall_score=overall,
        )
# backend/app/agents/master.py
import asyncio
import uuid
from typing import List
from .base import BaseAgent
from .grading import GradingAgent
from .report_generator import ReportGeneratorAgent
from ..schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    AgentResult,
)
from ..core.config import get_settings


class MasterAgent:
    """
    Orchestrates all domain agents, grading, and report generation.
    """

    def __init__(self, agents: List[BaseAgent]) -> None:
        self.agents = agents
        self.grading_agent = GradingAgent()
        self.report_generator = ReportGeneratorAgent()
        self.settings = get_settings()

    async def _run_agents_parallel(self, request: AnalysisRequest) -> List[AgentResult]:
        coros = [agent.run(request) for agent in self.agents]
        results: List[AgentResult] = await asyncio.gather(*coros)
        return results

    async def run_pipeline(self, request: AnalysisRequest) -> AnalysisResponse:
        # 1. Generate a run ID
        run_id = str(uuid.uuid4())

        # 2. Fan out to all agents (parallel)
        agent_results = await self._run_agents_parallel(request)

        # 3. Compute grading from agent outputs
        grading = self.grading_agent.grade(agent_results)

        # 4. Generate report content (string)
        report_content = self.report_generator.generate_report(
            request=request,
            grading=grading,
            results=agent_results,
        )

        # 5. (Optional) Persist to DB or enqueue for PDF conversion here

        # 6. Return a full response
        return AnalysisResponse(
            run_id=run_id,
            grading=grading,
            results=agent_results,
            report_content=report_content,
            status="COMPLETED",
        )
# backend/app/agents/report_generator.py
from typing import List
from ..schemas.analysis import AnalysisRequest, AgentResult, GradingBreakdown


class ReportGeneratorAgent:
    """
    Builds a human-readable report string based on all agents + grading.
    In production this can be converted to PDF by a separate worker.
    """

    def generate_report(
        self,
        request: AnalysisRequest,
        grading: GradingBreakdown,
        results: List[AgentResult],
    ) -> str:
        lines: list[str] = []

        title = f"Generic Opportunity Report for {request.molecule_name or 'Selected Molecule'}"
        lines.append(title)
        lines.append("=" * len(title))
        lines.append("")

        lines.append("1. Executive Summary")
        lines.append(
            f"- Overall feasibility grade: {grading.overall_score * 100:.1f} / 100"
        )
        lines.append(
            f"- Market Demand: {grading.market_demand * 100:.1f} / 100"
        )
        lines.append(
            f"- Production Feasibility: {grading.production_feasibility * 100:.1f} / 100"
        )
        lines.append(
            f"- Demographic Fit: {grading.demographics * 100:.1f} / 100"
        )
        lines.append(
            f"- Patents & Trials: {grading.patents_and_trials * 100:.1f} / 100"
        )
        lines.append(
            f"- Competition Landscape: {grading.competition * 100:.1f} / 100"
        )
        lines.append("")

        lines.append("2. Detailed Agent Insights")
        for idx, r in enumerate(results, start=1):
            lines.append(f"{idx}. {r.agent_name}")
            lines.append("-" * (len(r.agent_name) + 3))
            lines.append(r.summary)
            lines.append("")

        lines.append("3. Conclusion")
        if grading.overall_score >= 0.75:
            conclusion = (
                "The molecule presents a highly attractive opportunity for generic manufacturing, "
                "with strong scores across most dimensions."
            )
        elif grading.overall_score >= 0.55:
            conclusion = (
                "The molecule presents a moderately attractive opportunity. "
                "It can be considered with further due diligence on weaker dimensions."
            )
        else:
            conclusion = (
                "The molecule currently appears to have limited attractiveness for generic manufacturing. "
                "Significant risks or constraints have been identified."
            )
        lines.append(conclusion)

        return "\n".join(lines)
# backend/app/agents/demographics/demographic.py
from typing import Any, Dict
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest


class DemographicAgent(BaseAgent):
    """
    Estimates disease burden and access fit in key markets.
    """

    async def run(self, request: AnalysisRequest):
        data: Dict[str, Any] = {
            "disease_burden_score": 0.85,
            "age_distribution_fit_score": 0.8,
            "access_affordability_score": 0.75,
            "demographic_overall_score": 0.8,
        }

        summary = (
            "Demographic analysis indicates a high disease burden with good alignment to target age groups "
            "and reasonable affordability potential in emerging and developed markets."
        )

        return self._result(summary=summary, raw_data=data)
# backend/app/agents/knowledge/internal_knowledge.py
from typing import Any, Dict
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest


class InternalKnowledgeAgent(BaseAgent):
    """
    Simulated agent for internal portfolio / capability alignment.
    """

    async def run(self, request: AnalysisRequest):
        data: Dict[str, Any] = {
            "manufacturing_capability_fit_score": 0.83,
            "portfolio_synergy_score": 0.78,
            "historical_success_in_therapy_area": True,
        }

        summary = (
            "Internal capability assessment suggests strong fit with existing manufacturing know-how "
            "and good synergy with the current portfolio in this therapy area."
        )

        return self._result(summary=summary, raw_data=data)
# backend/app/agents/knowledge/web_intelligence.py
from typing import Any, Dict
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest


class WebIntelligenceAgent(BaseAgent):
    """
    Placeholder agent for general web / literature intelligence.
    """

    async def run(self, request: AnalysisRequest):
        data: Dict[str, Any] = {
            "sentiment_score": 0.74,
            "key_themes": [
                "cost pressure",
                "supply chain resilience",
                "regulatory scrutiny"
            ],
        }

        summary = (
            "Web and literature signals highlight positive sentiment around generic entry, "
            "with themes focused on cost savings and supply resilience."
        )

        return self._result(summary=summary, raw_data=data)