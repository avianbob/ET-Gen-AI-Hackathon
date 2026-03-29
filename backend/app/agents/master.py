# backend/app/agents/master.py
import uuid
from typing import List, Optional, TYPE_CHECKING
from .base import BaseAgent
from .grading import GradingAgent
from .report_generator import ReportGeneratorAgent
from ..schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    AgentResult,
)
if TYPE_CHECKING:
    from ..services.gemini_service import GeminiService


def _derive_target_volume_kg_per_year(stage1_results: List[AgentResult]) -> float | None:
    """
    Derive target production volume (kg API/year) from Stage 1 intelligence.
    Prefers API market size and typical_api_price_usd_per_kg from IQVIA for realistic scale.
    """
    for r in stage1_results:
        if not getattr(r, "raw_data", None) or r.agent_name != "IQVIAInsightsAgent":
            continue
        raw = r.raw_data
        # Prefer API market size (bulk API) and LLM-derived typical price
        api_market_b = raw.get("api_market_size_billion_usd")
        price_per_kg = raw.get("typical_api_price_usd_per_kg")
        if isinstance(price_per_kg, (int, float)) and price_per_kg > 0:
            # Use API market size when available for volume scale
            if isinstance(api_market_b, (int, float)) and api_market_b > 0:
                try:
                    kg_per_year = (float(api_market_b) * 1e9) / float(price_per_kg)
                    return max(1000.0, min(kg_per_year, 1e6))
                except (TypeError, ZeroDivisionError):
                    pass
            # Else use drug TAM with this price for a plausible volume
            market_b_usd = raw.get("estimated_market_size_billion_usd")
            if isinstance(market_b_usd, (int, float)) and market_b_usd > 0:
                try:
                    # API revenue ~2-5% of drug TAM for generics
                    api_share = 0.03
                    kg_per_year = (float(market_b_usd) * 1e9 * api_share) / float(price_per_kg)
                    return max(1000.0, min(kg_per_year, 1e6))
                except (TypeError, ZeroDivisionError):
                    pass
        # Fallback: drug TAM with generic price assumption
        market_b_usd = raw.get("estimated_market_size_billion_usd")
        if market_b_usd is None:
            continue
        price_per_kg_usd = 50.0  # generic default (e.g. Metformin range)
        try:
            kg_per_year = (float(market_b_usd) * 1e9 * 0.02) / price_per_kg_usd  # 2% API share
            return max(1000.0, min(kg_per_year, 1e6))
        except (TypeError, ZeroDivisionError):
            pass
    return None


def _build_parsed_intelligence(results: List[AgentResult]) -> dict:
    """
    Extract and normalize key data from agent results so downstream agents can use it.
    Used to pass market, EXIM, demographic, and other intelligence across the pipeline.
    """
    out: dict = {}
    for r in results:
        raw = getattr(r, "raw_data", None) or {}
        if not isinstance(raw, dict):
            continue
        name = getattr(r, "agent_name", "") or ""
        if "IQVIAInsightsAgent" in name:
            out["estimated_market_size_billion_usd"] = raw.get("estimated_market_size_billion_usd")
            out["api_market_size_billion_usd"] = raw.get("api_market_size_billion_usd")
            out["typical_api_price_usd_per_kg"] = raw.get("typical_api_price_usd_per_kg")
            out["market_demand_score"] = raw.get("market_demand_score")
            out["key_regions"] = raw.get("key_regions") or []
            out["cagr"] = raw.get("cagr")
            out["market_trend"] = raw.get("market_trend") or []
        elif "EXIMTrendAgent" in name:
            out["import_dependency_score"] = raw.get("import_dependency_score")
            out["export_opportunity_score"] = raw.get("export_opportunity_score")
            out["overall_market_demand_score"] = raw.get("overall_market_demand_score")
            out["trade_trend"] = raw.get("trade_trend") or []
            out["regional_trade"] = raw.get("regional_trade") or []
        elif "DemographicAgent" in name:
            out["demographic_overall_score"] = raw.get("demographic_overall_score")
            out["disease_burden_score"] = raw.get("disease_burden_score")
            out["plant_site_recommendations"] = raw.get("plant_site_recommendations") or []
        elif "ClinicalTrialAgent" in name:
            out["clinical_trials_decision"] = raw.get("clinical_trials_decision")
            out["clinical_trials_analytics"] = raw.get("clinical_trials_analytics")
        elif "PatentLandscapeAgent" in name:
            out["patent_landscape_summary"] = raw.get("patent_landscape_summary")
            out["freedom_to_operate_score"] = raw.get("freedom_to_operate_score")
    return out


class MasterAgent:
    """
    Orchestrates domain agents in a context-aware staged pipeline:
    Stage 1 (Intelligence): market, clinical, demographics, etc. → target volume & molecule context.
    Stage 2 (Technical): ProcessDesign uses drug + target volume → P&ID.
    Stage 3 (Economics): TechnoEconomic uses P&ID equipment → CAPEX/OPEX.
    """

    def __init__(self, agents: List[BaseAgent], llm_service: Optional["GeminiService"] = None) -> None:
        self.agents = agents
        self.grading_agent = GradingAgent()
        self.report_generator = ReportGeneratorAgent(llm_service=llm_service)

    def _stage1_agents(self) -> List[BaseAgent]:
        return [a for a in self.agents if a.name != "ProcessDesignAgent" and a.name != "TechnoEconomicAgent"]

    def _stage2_agents(self) -> List[BaseAgent]:
        return [a for a in self.agents if a.name == "ProcessDesignAgent"]

    def _stage3_agents(self) -> List[BaseAgent]:
        return [a for a in self.agents if a.name == "TechnoEconomicAgent"]

    async def _run_agents_series(
        self,
        request: AnalysisRequest,
        agents: List[BaseAgent],
        accumulate_parsed: bool = False,
    ) -> List[AgentResult]:
        """
        Run agents one after another. If accumulate_parsed is True, after each agent
        we inject parsed_intelligence from all results so far so later agents can use prior data.
        """
        results: List[AgentResult] = []
        current_req = request
        for agent in agents:
            result = await agent.run(current_req)
            results.append(result)
            if accumulate_parsed:
                parsed = _build_parsed_intelligence(results)
                current_req = current_req.model_copy(
                    update={"parsed_intelligence": parsed if parsed else None},
                    deep=True,
                )
        return results

    async def run_pipeline(self, request: AnalysisRequest) -> AnalysisResponse:
        run_id = str(uuid.uuid4())
        all_results: List[AgentResult] = []

        # Stage 1: Intelligence (What & How Much) – run in series with parsed data passed between agents
        stage1 = self._stage1_agents()
        print(f"[{run_id}] Starting Stage 1: Intelligence Gathering...")
        if stage1:
            stage1_results = await self._run_agents_series(
                request, stage1, accumulate_parsed=True
            )
            all_results.extend(stage1_results)
        else:
            stage1_results = []

        # Build parsed intelligence from full Stage 1 for use in Stage 2 & 3
        parsed_intelligence = _build_parsed_intelligence(stage1_results)

        # Derive target production volume for Process Design
        target_volume = _derive_target_volume_kg_per_year(stage1_results)
        if target_volume is not None:
            print(f"[{run_id}] Derived Target Volume: {target_volume:,.0f} kg/year")
        current_request = request.model_copy(
            update={
                "target_production_volume_kg_per_year": target_volume,
                "parsed_intelligence": parsed_intelligence if parsed_intelligence else None,
            },
            deep=True,
        )

        # Stage 2 & 3: Technical + Economic iteration loop (self-correction on poor ROI)
        MAX_ITERATIONS = 2
        for attempt in range(MAX_ITERATIONS):
            print(f"[{run_id}] Engineering Loop Iteration {attempt + 1}/{MAX_ITERATIONS}")
            # Stage 2: Process Design (with optional cost-reduction hint on re-run)
            stage2 = self._stage2_agents()
            if stage2:
                stage2_results = await self._run_agents_series(current_request, stage2)
                pid_data = None
                for r in stage2_results:
                    if getattr(r, "raw_data", None) and isinstance(r.raw_data, dict):
                        pid_data = r.raw_data.get("pid_data")
                        if pid_data is not None:
                            break
            else:
                stage2_results = []
                pid_data = None

            # Stage 3: Techno-Economics with P&ID from Stage 2
            request_stage3 = current_request.model_copy(
                update={"injected_pid_data": pid_data}, deep=True
            )
            stage3 = self._stage3_agents()
            if stage3:
                stage3_results = await self._run_agents_series(request_stage3, stage3)
            else:
                stage3_results = []

            # Self-correction: if IRR < 15% and we have retries left, re-run with cost focus
            eco_result = next(
                (r for r in stage3_results if r.agent_name == "TechnoEconomicAgent"),
                None,
            )
            irr = None
            if eco_result and getattr(eco_result, "raw_data", None):
                irr = eco_result.raw_data.get("internal_rate_of_return")
            print(f"[{run_id}] Engineering Loop Iteration {attempt + 1}/{MAX_ITERATIONS} Result: IRR = {(irr if irr is not None else 0):.1%}")
            if eco_result and getattr(eco_result, "raw_data", None) and attempt < MAX_ITERATIONS - 1:
                if irr is not None and irr < 0.15:
                    print(f"[{run_id}] IRR < 15%. Triggering Cost Optimization strategy.")
                    current_request = current_request.model_copy(
                        update={
                            "complexity": "low",
                            "optimization_focus": "cost_reduction",
                        },
                        deep=True,
                    )
                    continue
            print(f"[{run_id}] Viability threshold met or max iterations reached.")

            # Keep these stage results and exit loop
            all_results.extend(stage2_results)
            all_results.extend(stage3_results)
            break

        grading = self.grading_agent.grade(all_results)
        report_content = self.report_generator.generate_report(
            request=current_request,
            grading=grading,
            results=all_results,
            fallback_used_list=getattr(request, "llm_fallback_used", None),
        )

        from dataclasses import asdict
        grading_dict = asdict(grading) if grading else None
        results_dict = [asdict(r) for r in all_results] if all_results else None

        return AnalysisResponse(
            run_id=run_id,
            grading=grading_dict,
            results=results_dict,
            report_content=report_content,
            status="COMPLETED",
            context=request.context,
        )