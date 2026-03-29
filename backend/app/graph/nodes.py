"""
LangGraph Workflow Nodes - Implementation of each workflow step.
Each node processes the state and passes it to the next node.
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, Any
from app.graph.state import AgentState
from app.agents.repurposing.literature_agent import LiteratureAgent
from app.agents.repurposing.clinical_trials_agent import ClinicalTrialsAgent
from app.agents.repurposing.bioactivity_agent import BioactivityAgent
from app.agents.repurposing.patent_agent import PatentAgent
from app.agents.repurposing.internal_agent import InternalAgent
# Tier 1 agents (Phase 2)
from app.agents.repurposing.openfda_agent import OpenFDAAgent
from app.agents.repurposing.opentargets_agent import OpenTargetsAgent
from app.agents.repurposing.semantic_scholar_agent import SemanticScholarAgent
# Tier 2 agents (Phase 2)
from app.agents.repurposing.dailymed_agent import DailyMedAgent
from app.agents.repurposing.kegg_agent import KEGGAgent
from app.agents.repurposing.uniprot_agent import UniProtAgent
from app.agents.repurposing.orange_book_agent import OrangeBookAgent
# Tier 3 agents (Phase 2)
from app.agents.repurposing.rxnorm_agent import RxNormAgent
from app.agents.repurposing.who_agent import WHOAgent
from app.agents.repurposing.drugbank_agent import DrugBankAgent
from app.agents.repurposing.market_data_agent import MarketDataAgent
# ET Worker Agent wrappers (IQVIA + EXIM Trade + Web Intelligence)
from app.agents.repurposing.iqvia_pipeline_agent import IQVIAPipelineAgent
from app.agents.repurposing.exim_pipeline_agent import EXIMPipelineAgent
from app.agents.repurposing.web_intelligence_pipeline_agent import WebIntelligencePipelineAgent
from app.services.repurpose.llm.llm_factory import LLMFactory, get_synthesis_prompt, get_enhanced_synthesis_prompt
from app.services.repurpose.scoring.evidence_scorer import EvidenceScorer
from app.services.repurpose.scoring.composite_scorer import CompositeScorer
from app.services.repurpose.scoring.comparative_analyzer import get_comparative_analyzer
from app.services.repurpose.scoring.scientific_extractor import get_scientific_extractor
from app.services.repurpose.market.market_analyzer import MarketAnalyzer
from app.services.repurpose.market.competitor_tracker import CompetitorTracker
from app.services.repurpose.market.segment_analyzer import get_segment_analyzer
from app.schemas.repurpose_scoring import EnhancedOpportunityData
from app.routes.repurpose.websocket import manager as ws_manager
from app.services.repurpose.utils.logger import get_logger
from app.services.repurpose.utils.full_report_templates import template_full_report_extensions

logger = get_logger("graph.nodes")


async def _send_ws_status(state, stage, status="running", message=None):
    """Helper to send workflow status via WebSocket, silently ignoring errors."""
    session_id = state.get("session_id", "")
    if session_id:
        try:
            await ws_manager.send_workflow_status(session_id, stage, status, message)
        except Exception:
            pass


async def initialize_search(state: AgentState) -> AgentState:
    """
    Initialize the search workflow.
    Sets up initial state and progress tracking.

    Args:
        state: Current workflow state

    Returns:
        Updated state with initialization complete
    """
    logger.info(f"Initializing search for drug: {state['drug_name']}")

    # Initialize progress tracking for all agents
    state["progress"] = {
        # Original agents
        "LiteratureAgent": "pending",
        "ClinicalTrialsAgent": "pending",
        "BioactivityAgent": "pending",
        "PatentAgent": "pending",
        "InternalAgent": "pending",
        # Tier 1 agents (Phase 2)
        "OpenFDAAgent": "pending",
        "OpenTargetsAgent": "pending",
        "SemanticScholarAgent": "pending",
        # Tier 2 agents (Phase 2)
        "DailyMedAgent": "pending",
        "KEGGAgent": "pending",
        "UniProtAgent": "pending",
        "OrangeBookAgent": "pending",
        # Tier 3 agents (Phase 2)
        "RxNormAgent": "pending",
        "WHOAgent": "pending",
        "DrugBankAgent": "pending",
        # ET Worker Agent wrappers
        "IQVIAPipelineAgent": "pending",
        "EXIMPipelineAgent": "pending",
        "WebIntelligencePipelineAgent": "pending",
        "ProcessDesignAgent": "pending",
        "TechnoEconomicAgent": "pending",
        "DemographicsPlantAgent": "pending",
        "ReportGenerator": "pending",
    }

    # Initialize result containers
    state["agent_results"] = {}
    state["errors"] = []
    state["all_evidence"] = []
    state["ranked_indications"] = []
    state["enhanced_indications"] = []  # Composite scoring results

    # Set timestamp
    state["timestamp"] = datetime.now().isoformat()

    logger.info("Search initialized successfully")

    await _send_ws_status(state, "initializing", "running", "Initializing analysis...")

    return state


async def run_agents_parallel(state: AgentState) -> AgentState:
    """
    Execute all agents in parallel for maximum speed.
    Uses asyncio.gather to run agents concurrently.

    Args:
        state: Current workflow state

    Returns:
        Updated state with agent results
    """
    logger.info("Running all agents in parallel...")

    session_id = state.get("session_id", "")
    await _send_ws_status(state, "agents_running", "running", "Master Agent dispatching worker agents...")

    # Instantiate all agents
    agents = {
        # Original agents
        "LiteratureAgent": LiteratureAgent(),
        "ClinicalTrialsAgent": ClinicalTrialsAgent(),
        "BioactivityAgent": BioactivityAgent(),
        "PatentAgent": PatentAgent(),
        "InternalAgent": InternalAgent(),
        # Tier 1 agents (Phase 2)
        "OpenFDAAgent": OpenFDAAgent(),
        "OpenTargetsAgent": OpenTargetsAgent(),
        "SemanticScholarAgent": SemanticScholarAgent(),
        # Tier 2 agents (Phase 2)
        "DailyMedAgent": DailyMedAgent(),
        "KEGGAgent": KEGGAgent(),
        "UniProtAgent": UniProtAgent(),
        "OrangeBookAgent": OrangeBookAgent(),
        # Tier 3 agents (Phase 2)
        "RxNormAgent": RxNormAgent(),
        "WHOAgent": WHOAgent(),
        "DrugBankAgent": DrugBankAgent(),
        # ET Worker Agent wrappers
        "IQVIAPipelineAgent": IQVIAPipelineAgent(),
        "EXIMPipelineAgent": EXIMPipelineAgent(),
        "WebIntelligencePipelineAgent": WebIntelligencePipelineAgent(),
    }

    async def run_single_agent(name: str, agent):
        """
        Run a single agent and update progress.

        Args:
            name: Agent name
            agent: Agent instance

        Returns:
            Tuple of (agent_name, result)
        """
        try:
            # Update progress to running
            state["progress"][name] = "running"
            logger.info(f"{name} started")

            # Send running status via WebSocket
            if session_id:
                try:
                    await ws_manager.send_agent_progress(
                        session_id, name, "running", f"Searching {agent.name}..."
                    )
                except Exception:
                    pass

            # Run the agent
            result = await agent.run(
                drug_name=state["drug_name"],
                context=state.get("search_context", {})
            )

            # Update progress based on result
            state["progress"][name] = result.status
            evidence_count = len(result.evidence)
            logger.info(f"{name} {result.status} - found {evidence_count} evidence items")

            # Send completion status via WebSocket
            if session_id:
                try:
                    await ws_manager.send_agent_progress(
                        session_id, name, result.status,
                        f"Found {evidence_count} evidence items",
                        evidence_count
                    )
                except Exception:
                    pass

            return (name, result)

        except Exception as e:
            logger.error(f"{name} failed with exception: {e}", exc_info=True)
            state["progress"][name] = "error"
            state["errors"].append(f"{name}: {str(e)}")

            # Send error status via WebSocket
            if session_id:
                try:
                    await ws_manager.send_agent_progress(
                        session_id, name, "error", str(e)
                    )
                except Exception:
                    pass

            # Return error response
            from app.schemas.repurpose_api import AgentResponse
            return (name, AgentResponse(
                agent_name=name,
                status="error",
                evidence=[],
                error=str(e)
            ))

    # Run all agents concurrently
    tasks = [run_single_agent(name, agent) for name, agent in agents.items()]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    # Collect results into state
    for agent_name, agent_result in results:
        state["agent_results"][agent_name] = agent_result

    # Log summary
    total_evidence = sum(len(r.evidence) for r in state["agent_results"].values())
    logger.info(f"All agents complete. Total evidence items: {total_evidence}")

    await _send_ws_status(state, "agents_complete", "running", f"All agents complete. {total_evidence} evidence items collected.")

    return state


async def aggregate_evidence(state: AgentState) -> AgentState:
    """
    Aggregate evidence from all agents into a single list.

    Args:
        state: Current workflow state

    Returns:
        Updated state with aggregated evidence
    """
    logger.info("Aggregating evidence from all agents...")
    await _send_ws_status(state, "aggregating", "running", "Aggregating evidence from all sources...")

    all_evidence = []

    for agent_name, agent_response in state["agent_results"].items():
        if agent_response.status == "success":
            evidence_items = agent_response.evidence
            all_evidence.extend(evidence_items)
            logger.debug(f"Added {len(evidence_items)} items from {agent_name}")

    state["all_evidence"] = all_evidence
    logger.info(f"Aggregated {len(all_evidence)} total evidence items")

    return state


async def score_evidence(state: AgentState) -> AgentState:
    """
    Score and rank evidence to identify top repurposing opportunities.
    Uses both basic scoring (backward compatible) and composite scoring (enhanced).

    Args:
        state: Current workflow state

    Returns:
        Updated state with ranked indications and composite scores
    """
    logger.info("Scoring and ranking evidence...")
    await _send_ws_status(state, "scoring", "running", "Scoring opportunities across 4 dimensions...")

    try:
        # Basic scoring (backward compatible)
        basic_scorer = EvidenceScorer()
        ranked_indications = basic_scorer.rank_indications(state["all_evidence"])

        # Safety filter: remove any "Unknown Indication" that slipped through
        ranked_indications = [
            r for r in ranked_indications
            if r.indication and r.indication.lower() != "unknown indication"
        ]

        state["ranked_indications"] = ranked_indications
        logger.info(f"Basic scoring identified {len(ranked_indications)} opportunities")

        # Enhanced composite scoring with market and competitive data
        logger.info("Running enhanced composite scoring...")

        # Get indications sorted by evidence count (most evidence first)
        # This ensures we analyze competitive landscape for the ACTUAL top indications
        from collections import Counter
        indication_counts = Counter(
            e.indication for e in state["all_evidence"]
            if e.indication and e.indication.lower() != "unknown indication"
        )
        # Sort by count descending, then alphabetically for ties
        sorted_indications = sorted(
            indication_counts.keys(),
            key=lambda x: (-indication_counts[x], x.lower())
        )

        # Fetch market and competitor data for top indications (limit to top 15 for better coverage)
        market_data_map = {}
        competitor_data_map = {}

        if sorted_indications:
            market_analyzer = MarketAnalyzer()
            competitor_tracker = CompetitorTracker()
            free_market_agent = MarketDataAgent()  # Free fallback for market data

            # Log top indications being analyzed
            top_15 = sorted_indications[:15]
            logger.info(f"Analyzing market/competition for top {len(top_15)} indications by evidence count:")
            for i, ind in enumerate(top_15[:5], 1):
                logger.info(f"  {i}. {ind} ({indication_counts[ind]} evidence items)")

            # Analyze market for top indications (sorted by evidence count)
            for indication in top_15:
                try:
                    market_opportunity = await market_analyzer.analyze_market(
                        indication=indication,
                        drug_name=state["drug_name"]
                    )
                    if market_opportunity:
                        from app.schemas.repurpose_scoring import MarketData
                        market_data_map[indication.lower()] = MarketData(
                            indication=indication,
                            market_size_usd_billions=market_opportunity.estimated_market_size_usd / 1_000_000_000,
                            cagr_percent=market_opportunity.cagr_percent,
                            unmet_need_score=market_opportunity.unmet_need_score
                        )
                except Exception as e:
                    logger.debug(f"Premium market analysis skipped for {indication}: {e}")

            # Fallback to free market data agent for indications without premium data
            indications_needing_free_data = [
                ind for ind in top_15
                if ind.lower() not in market_data_map
            ]

            if indications_needing_free_data:
                logger.info(f"Fetching free market data for {len(indications_needing_free_data)} indications...")
                try:
                    free_market_data = await free_market_agent.batch_fetch(indications_needing_free_data)
                    from app.schemas.repurpose_scoring import MarketData

                    for indication, data in free_market_data.items():
                        if data and data.get("patient_population_millions"):
                            market_data_map[indication.lower()] = MarketData(
                                indication=indication,
                                market_size_usd_billions=data.get("estimated_market_size_billions"),
                                patient_population_millions=data.get("patient_population_millions"),
                                unmet_need_score=50  # Default moderate unmet need
                            )
                            logger.debug(f"Free market data added for {indication}")
                except Exception as e:
                    logger.warning(f"Free market data fetch failed: {e}")

            # Analyze competition for top indications (sorted by evidence count)
            for indication in top_15:
                try:
                    competitive_landscape = await competitor_tracker.get_competitive_landscape(
                        indication=indication,
                        drug_name=state["drug_name"]
                    )
                    if competitive_landscape:
                        from app.schemas.repurpose_scoring import CompetitorData, CompetitorInfoDisplay
                        phase_dist = competitive_landscape.phase_distribution

                        # Convert competitor details to display format
                        competitor_list = []
                        for comp in competitive_landscape.competitor_details[:10]:
                            # Normalize phase name for frontend display
                            phase = comp.development_phase
                            if phase:
                                phase = phase.replace("PHASE", "Phase ").replace("_", " ").title()
                            competitor_list.append(CompetitorInfoDisplay(
                                company=comp.company_name,
                                drug=comp.drug_name,
                                phase=phase or "Unknown"
                            ))

                        competitor_data_map[indication.lower()] = CompetitorData(
                            indication=indication,
                            total_competitors=competitive_landscape.total_competitors,
                            phase3_trials_count=phase_dist.get("PHASE3", 0) + phase_dist.get("Phase 3", 0),
                            phase2_trials_count=phase_dist.get("PHASE2", 0) + phase_dist.get("Phase 2", 0),
                            phase1_trials_count=phase_dist.get("PHASE1", 0) + phase_dist.get("Phase 1", 0),
                            competitor_list=competitor_list
                        )
                except Exception as e:
                    logger.debug(f"Competition analysis skipped for {indication}: {e}")

        # Run composite scoring
        composite_scorer = CompositeScorer()
        enhanced_indications = composite_scorer.rank_indications(
            evidence_list=state["all_evidence"],
            market_data_map=market_data_map,
            competitor_data_map=competitor_data_map
        )

        # Safety filter: remove any "Unknown Indication" that slipped through
        enhanced_indications = [
            r for r in enhanced_indications
            if r.indication and r.indication.lower() != "unknown indication"
        ]

        state["enhanced_indications"] = enhanced_indications
        logger.info(f"Composite scoring identified {len(enhanced_indications)} opportunities")

        # Log top 3 with composite details
        for i, indication in enumerate(ranked_indications[:3], 1):
            logger.info(
                f"  {i}. {indication.indication} "
                f"(confidence: {indication.confidence_score:.1f}, "
                f"evidence: {indication.evidence_count})"
            )

        # Log composite scores for top 3
        if enhanced_indications:
            logger.info("Enhanced composite scores:")
            for i, result in enumerate(enhanced_indications[:3], 1):
                cs = result.composite_score
                logger.info(
                    f"  {i}. {result.indication}: {cs.overall_score:.1f} "
                    f"[Sci:{cs.scientific_evidence.score:.0f} "
                    f"Mkt:{cs.market_opportunity.score:.0f} "
                    f"Comp:{cs.competitive_landscape.score:.0f} "
                    f"Feas:{cs.development_feasibility.score:.0f}]"
                )

    except Exception as e:
        logger.error(f"Scoring failed: {e}", exc_info=True)
        state["ranked_indications"] = []
        state["enhanced_indications"] = []
        state["errors"].append(f"Scoring failed: {str(e)}")

    return state


async def analyze_comparatives(state: AgentState) -> AgentState:
    """
    Analyze comparative advantages over existing treatments.
    Enriches top opportunities with comparator drugs, advantages, side effects,
    market segments, and detailed scientific data.

    Args:
        state: Current workflow state

    Returns:
        Updated state with enhanced opportunity data
    """
    logger.info("Analyzing comparative advantages over existing treatments...")
    await _send_ws_status(state, "analyzing_comparatives", "running", "Comparing against standard of care treatments...")

    try:
        # Get analyzers
        comparative_analyzer = get_comparative_analyzer()
        segment_analyzer = get_segment_analyzer()
        scientific_extractor = get_scientific_extractor()

        enhanced_opportunities = {}

        # Process top 10 indications
        top_indications = state.get("enhanced_indications", [])[:10]

        for indication_result in top_indications:
            indication = indication_result.indication

            try:
                logger.debug(f"Analyzing comparative data for: {indication}")

                # 1. Get comparator drugs (standard of care)
                comparators = await comparative_analyzer.get_comparator_drugs(indication)

                # 2. Analyze advantages over comparators
                advantages = []
                if comparators:
                    advantages = await comparative_analyzer.analyze_advantages(
                        state["drug_name"],
                        indication,
                        comparators
                    )

                # 3. Compare side effect profiles
                side_effect_comparison = None
                if comparators:
                    side_effect_comparison = await comparative_analyzer.compare_side_effects(
                        state["drug_name"],
                        comparators[0],  # Compare with primary comparator
                        indication
                    )

                # 4. Identify target market segment
                market_segment = await segment_analyzer.identify_segment(
                    indication,
                    state.get("all_evidence", []),
                    comparative_analyzer.get_candidate_characteristics(state["drug_name"])
                )

                # 5. Extract detailed scientific data
                scientific_details = await scientific_extractor.extract_details(
                    state["drug_name"],
                    indication,
                    [e for e in state.get("all_evidence", [])
                     if getattr(e, "indication", "").lower() == indication.lower()]
                )

                # 6. Generate key benefits summary
                key_benefits = []
                for adv in advantages[:5]:
                    key_benefits.append(f"{adv.advantage_type}: {adv.description[:100]}...")

                if side_effect_comparison and side_effect_comparison.safety_advantage_score > 0:
                    eliminated_count = len(side_effect_comparison.eliminated_effects)
                    if eliminated_count > 0:
                        key_benefits.append(f"Potentially avoids {eliminated_count} side effect(s) associated with current treatments")

                # Build enhanced opportunity data
                enhanced_opportunities[indication] = EnhancedOpportunityData(
                    indication=indication,
                    composite_score=indication_result.composite_score,
                    comparator_drugs=comparators,
                    comparative_advantages=advantages,
                    side_effect_comparison=side_effect_comparison,
                    market_segment=market_segment,
                    scientific_details=scientific_details,
                    key_benefits_summary=key_benefits[:5],
                    positioning_statement=_generate_positioning_statement(
                        state["drug_name"],
                        indication,
                        advantages,
                        market_segment
                    ),
                )

                logger.debug(f"Enhanced data complete for {indication}: "
                            f"{len(comparators)} comparators, {len(advantages)} advantages")

            except Exception as e:
                logger.warning(f"Failed to analyze comparatives for {indication}: {e}")
                # Continue with other indications

        state["enhanced_opportunities"] = enhanced_opportunities
        logger.info(f"Comparative analysis complete for {len(enhanced_opportunities)} indications")

    except Exception as e:
        logger.error(f"Comparative analysis failed: {e}", exc_info=True)
        state["enhanced_opportunities"] = {}
        state["errors"].append(f"Comparative analysis failed: {str(e)}")

    return state


def _generate_positioning_statement(
    drug_name: str,
    indication: str,
    advantages: list,
    market_segment
) -> str:
    """Generate a strategic positioning statement for the opportunity."""
    if not advantages and not market_segment:
        return f"{drug_name} shows potential for repurposing in {indication}."

    parts = [f"{drug_name}"]

    if market_segment and market_segment.segment_name:
        parts.append(f"targets the {market_segment.segment_name} segment")
    else:
        parts.append(f"addresses {indication}")

    if advantages:
        top_advantage = advantages[0]
        parts.append(f"with key differentiation: {top_advantage.advantage_type.lower()}")

    if market_segment and market_segment.unmet_need_level in ["high", "very_high"]:
        parts.append("in a market with significant unmet need")

    return " ".join(parts) + "."


async def refine_scores(state: AgentState) -> AgentState:
    """
    Refine composite scores using enhanced comparative/scientific/market data.
    Applies bounded adjustments (+/-20 per dimension) based on deeper analysis.

    Args:
        state: Current workflow state (must have enhanced_opportunities and enhanced_indications)

    Returns:
        Updated state with refined scores
    """
    logger.info("Refining scores with enhanced analysis data...")
    await _send_ws_status(state, "refining_scores", "running", "Refining scores with comparative & scientific data...")

    enhanced_opportunities = state.get("enhanced_opportunities", {})
    enhanced_indications = state.get("enhanced_indications", [])

    if not enhanced_opportunities or not enhanced_indications:
        logger.info("No enhanced data available, skipping score refinement")
        state["refinement_applied"] = False
        return state

    try:
        from app.services.repurpose.scoring.score_refiner import ScoreRefiner
        refiner = ScoreRefiner()

        refined_indications = refiner.refine_scores(
            enhanced_indications, enhanced_opportunities
        )

        state["enhanced_indications"] = refined_indications
        state["refinement_applied"] = True

        # Also update the composite_score reference inside enhanced_opportunities
        for result in refined_indications:
            if result.indication in enhanced_opportunities:
                enhanced_opportunities[result.indication].composite_score = result.composite_score
        state["enhanced_opportunities"] = enhanced_opportunities

        # Log top changes
        for i, result in enumerate(refined_indications[:3], 1):
            cs = result.composite_score
            base_sci = cs.scientific_evidence.factors.get("_base_score", cs.scientific_evidence.score)
            ref_total = cs.scientific_evidence.factors.get("_refinement_total", 0)
            logger.info(
                f"  {i}. {result.indication}: {cs.overall_score:.1f} "
                f"(sci refinement: {ref_total:+.1f})"
            )

        logger.info(f"Score refinement complete for {len(refined_indications)} indications")

    except Exception as e:
        logger.error(f"Score refinement failed: {e}", exc_info=True)
        state["refinement_applied"] = False

    return state


def _top_indication_names(state: AgentState, limit: int = 5) -> str:
    """Comma-separated indication names from enhanced_indications for LLM context."""
    enhanced = state.get("enhanced_indications") or []
    names: list[str] = []
    for item in enhanced[:limit]:
        if hasattr(item, "indication"):
            ind = getattr(item, "indication", None) or ""
        elif isinstance(item, dict):
            ind = str(item.get("indication") or "")
        else:
            ind = ""
        if ind.strip():
            names.append(ind.strip())
    return ", ".join(names) if names else "general repurposing hypotheses"


def _parse_extension_json(raw: str) -> Dict[str, str]:
    """Parse LLM JSON with keys process_design, techno_economic, demographics_sites."""
    text = (raw or "").strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return {}
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return {}
    out: Dict[str, str] = {}
    for k in ("process_design", "techno_economic", "demographics_sites"):
        v = data.get(k)
        if v is not None and str(v).strip():
            out[k] = str(v).strip()
    return out


async def _agent_progress_pulse(
    state: AgentState,
    agent_name: str,
    running_msg: str,
    success_msg: str,
) -> None:
    session_id = state.get("session_id", "")
    state["progress"][agent_name] = "running"
    if session_id:
        try:
            await ws_manager.send_agent_progress(session_id, agent_name, "running", running_msg)
        except Exception:
            pass
    state["progress"][agent_name] = "success"
    if session_id:
        try:
            await ws_manager.send_agent_progress(session_id, agent_name, "success", success_msg)
        except Exception:
            pass


async def _llm_text_with_fallbacks(prompt: str) -> str | None:
    """Single-shot text generation with same fallback order as synthesis."""
    llm = LLMFactory.get_llm()
    if llm is None:
        return None
    try:
        return await llm.generate(prompt)
    except BaseException as e:
        logger.warning("LLM generate failed, trying fallbacks: %s", e)
    for provider in ("groq", "ollama"):
        alt = LLMFactory.get_llm(force_provider=provider)
        if alt is None:
            continue
        try:
            return await alt.generate(prompt)
        except BaseException as e2:
            logger.warning("%s fallback failed: %s", provider, e2)
    LLMFactory.reset()
    gem = LLMFactory.get_llm(force_provider="gemini")
    if gem is not None:
        try:
            return await gem.generate(prompt)
        except BaseException as e3:
            logger.warning("Gemini after reset failed: %s", e3)
    return None


def _inject_fallback_market_exim(state: AgentState) -> None:
    """Build minimal market_data and exim_data from repurpose state when app agents unavailable."""
    vd = state.get("visual_data") or {}

    # Aggregate market size from IQVIA-style evidence
    evidence = state.get("all_evidence") or []
    market_sizes = []
    for e in evidence:
        if isinstance(e, dict) and e.get("source", "").lower().find("iqvia") >= 0:
            meta = e.get("metadata") or {}
            ms = meta.get("market_size_usd") or meta.get("market_size_billion_usd")
            if ms:
                market_sizes.append(ms / 1e9 if ms > 1e6 else ms)
        elif hasattr(e, "metadata") and e.metadata:
            ms = e.metadata.get("market_size_usd") or e.metadata.get("market_size_billion_usd")
            if ms:
                market_sizes.append(ms / 1e9 if ms > 1e6 else ms)
    tam = sum(market_sizes) / len(market_sizes) if market_sizes else 2.0

    base_year = 2024
    years = [str(y) for y in range(base_year - 4, base_year + 7)]
    growth = 1.05
    val = tam * 0.7
    market_trend = []
    for i, yr in enumerate(years):
        val = val * growth if i > 0 else val
        market_trend.append({
            "year": yr,
            "market_size_billion_usd": round(val, 2),
            "sales_billion_usd": round(val * 0.85, 2),
        })

    mkt = vd.get("market_data") or {}
    if not (mkt.get("market_trend") or mkt.get("estimated_market_size_billion_usd") is not None):
        vd["market_data"] = {
            "estimated_market_size_billion_usd": round(tam, 1),
            "cagr": 0.05,
            "cagr_percent": 5.0,
            "market_demand_score": 0.65,
            "market_trend": market_trend,
            "regional_breakdown": [
                {"region": "US", "share_percent": 45, "value_billion_usd": round(tam * 0.45, 1)},
                {"region": "EU5", "share_percent": 25, "value_billion_usd": round(tam * 0.25, 1)},
                {"region": "Asia-Pacific", "share_percent": 20, "value_billion_usd": round(tam * 0.20, 1)},
                {"region": "Rest of World", "share_percent": 10, "value_billion_usd": round(tam * 0.10, 1)},
            ],
        }
    exim = vd.get("exim_data") or {}
    if not (exim.get("trade_trend") or exim.get("import_dependency_score") is not None):
        vd["exim_data"] = {
            "import_dependency_score": 0.4,
            "export_opportunity_score": 0.6,
            "trade_trend": [{"year": str(y), "import_value_billion_usd": round(tam * 0.15 * (1.02 ** (y - base_year)), 2), "export_value_billion_usd": round(tam * 0.22 * (1.03 ** (y - base_year)), 2)} for y in range(base_year - 4, base_year + 3)],
            "regional_trade": [{"region": r, "import_share_percent": p, "export_share_percent": p + 5} for r, p in [("China", 25), ("India", 20), ("USA", 18), ("EU", 15)]],
        }
    state["visual_data"] = vd


async def fetch_dashboard_components(state: AgentState) -> AgentState:
    """
    Fetch PID, TEA, demographics for dashboard-style report components (ProfessionalPID, TeaSection, PlantSiteMap).
    Runs ProcessDesignAgent and TechnoEconomicAgent from the legacy PharmAI pipeline.
    """
    logger.info("Fetching dashboard components (PID, TEA, demographics)...")
    await _send_ws_status(
        state,
        "fetch_dashboard",
        "running",
        "Generating process design, techno-economics & site analysis...",
    )

    from urllib.parse import quote
    drug = state.get("drug_name", "Unknown")
    top_indication = _top_indication_names(state, limit=1) or None

    state["pid_data"] = {}
    state["tea_data"] = {}
    state["visual_data"] = {}
    # Add 2D structure image from PubChem (no LLM needed)
    safe_name = quote((drug or "").strip())
    if safe_name:
        state["visual_data"]["molecular_details"] = {
            "molecular_name": drug,
            "structure_image_url": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{safe_name}/PNG?image_size=400x400",
        }
    state["query_context"] = {"drug": drug, "disease": top_indication, "raw_query": drug}
    state["grading"] = {}

    try:
        from app.schemas.analysis import AnalysisRequest, PharmaQueryContext
        from app.agents.production.process_design import ProcessDesignAgent
        from app.agents.production.techno_economic import TechnoEconomicAgent
        from app.agents.demographics.demographic import DemographicAgent
        from app.agents.market.iqvia_insights import IQVIAInsightsAgent
        from app.agents.market.exim_trends import EXIMTrendAgent
    except ImportError as e:
        logger.warning("Dashboard agents not available (app not in path): %s", e)
        # Fallback: build minimal market_data and exim_data from repurpose evidence so charts show
        _inject_fallback_market_exim(state)
        await _send_ws_status(state, "fetch_dashboard", "success", "Skipped (agents unavailable)")
        return state

    gemini_service = None
    try:
        from app.services.gemini_service import GeminiService
        gemini_service = GeminiService()
    except Exception:
        pass

    try:
        ctx = PharmaQueryContext(
            drug=drug,
            disease=top_indication,
            raw_query=drug,
            complexity="normal",
        )
        analysis_req = AnalysisRequest(
            molecule_name=drug,
            target_indication=top_indication,
            complexity="normal",
            context=ctx,
        )

        # 1. ProcessDesignAgent -> pid_data
        process_agent = ProcessDesignAgent(gemini_service=gemini_service)
        process_result = await process_agent.run(analysis_req)
        pid_data = None
        if process_result and hasattr(process_result, "raw_data"):
            raw = process_result.raw_data or {}
            pid_data = raw.get("pid_data")
        if isinstance(pid_data, dict):
            state["pid_data"] = pid_data
            if pid_data.get("material_handling") is None:
                state["pid_data"]["material_handling"] = {"target_molecule": drug}
            elif isinstance(pid_data["material_handling"], dict):
                state["pid_data"]["material_handling"]["target_molecule"] = drug

        # 2. TechnoEconomicAgent with injected PID
        if pid_data:
            analysis_req.injected_pid_data = pid_data
        tea_agent = TechnoEconomicAgent(gemini_service=gemini_service)
        tea_result = await tea_agent.run(analysis_req)
        tea_data = None
        if tea_result and hasattr(tea_result, "raw_data"):
            tea_data = tea_result.raw_data
        if isinstance(tea_data, dict):
            state["tea_data"] = tea_data

        # 3. DemographicAgent for plant sites
        demographic_agent = DemographicAgent(gemini_service=gemini_service)
        demo_result = await demographic_agent.run(analysis_req)
        demo_data = None
        if demo_result and hasattr(demo_result, "raw_data"):
            demo_data = demo_result.raw_data
        if isinstance(demo_data, dict):
            state["visual_data"]["demographic_data"] = demo_data

        # 4. IQVIAInsightsAgent for market_data (sales, market demand)
        iqvia_agent = IQVIAInsightsAgent(gemini_service=gemini_service)
        iqvia_result = await iqvia_agent.run(analysis_req)
        if iqvia_result and hasattr(iqvia_result, "raw_data") and isinstance(iqvia_result.raw_data, dict):
            state["visual_data"]["market_data"] = iqvia_result.raw_data

        # 5. EXIMTrendAgent for exim_data (export/import)
        exim_agent = EXIMTrendAgent(gemini_service=gemini_service)
        exim_result = await exim_agent.run(analysis_req)
        if exim_result and hasattr(exim_result, "raw_data") and isinstance(exim_result.raw_data, dict):
            state["visual_data"]["exim_data"] = exim_result.raw_data

        # Fallback if IQVIA/EXIM returned empty (LLM failure, rate limit, etc.)
        mkt = state["visual_data"].get("market_data") or {}
        exim = state["visual_data"].get("exim_data") or {}
        need_mkt = not (mkt.get("market_trend") or mkt.get("estimated_market_size_billion_usd") is not None)
        need_exim = not (exim.get("trade_trend") or exim.get("import_dependency_score") is not None)
        if need_mkt or need_exim:
            _inject_fallback_market_exim(state)

        # 6. Build grading from composite scores + TEA
        enhanced = state.get("enhanced_indications") or []
        tea = state.get("tea_data") or {}
        scores = {}

        def _get_sub_score(r: Any, dim: str) -> float | None:
            cs = getattr(r, "composite_score", None) or (r.get("composite_score") if isinstance(r, dict) else None)
            if not cs:
                return None
            sub = getattr(cs, dim, None) or (cs.get(dim) if isinstance(cs, dict) else None)
            if not sub:
                return None
            v = getattr(sub, "score", None) or (sub.get("score") if isinstance(sub, dict) else None)
            return float(v) if v is not None else None

        if enhanced:
            import statistics
            sci = [x for r in enhanced if (x := _get_sub_score(r, "scientific_evidence")) is not None]
            mkt = [x for r in enhanced if (x := _get_sub_score(r, "market_opportunity")) is not None]
            comp = [x for r in enhanced if (x := _get_sub_score(r, "competitive_landscape")) is not None]
            feas = [x for r in enhanced if (x := _get_sub_score(r, "development_feasibility")) is not None]
            scores["patents_and_trials"] = statistics.mean(sci) / 100.0 if sci else 0.5
            scores["market_demand"] = statistics.mean(mkt) / 100.0 if mkt else 0.5
            scores["competition"] = statistics.mean(comp) / 100.0 if comp else 0.5
            scores["production_feasibility"] = statistics.mean(feas) / 100.0 if feas else 0.5
            scores["demographics"] = 0.5
        if tea.get("production_feasibility_score") is not None:
            scores["production_feasibility"] = min(1.0, max(0, tea["production_feasibility_score"]))
        if scores:
            scores["overall_score"] = sum(scores.values()) / len(scores) if scores else 0.5
            state["grading"] = {
                "market_demand": scores.get("market_demand", 0.5),
                "production_feasibility": scores.get("production_feasibility", 0.5),
                "demographics": scores.get("demographics", 0.5),
                "patents_and_trials": scores.get("patents_and_trials", 0.5),
                "competition": scores.get("competition", 0.5),
                "overall_score": scores.get("overall_score", 0.5),
            }

        await _agent_progress_pulse(state, "ProcessDesignAgent", "PID generated", "Process design complete")
        await _agent_progress_pulse(state, "TechnoEconomicAgent", "TEA computed", "Techno-economics complete")
        await _agent_progress_pulse(state, "DemographicsPlantAgent", "Sites analyzed", "Demographics complete")
    except Exception as e:
        logger.warning("Dashboard components fetch failed: %s", e, exc_info=True)
        state["errors"].append(f"Dashboard fetch: {str(e)}")

    await _send_ws_status(state, "fetch_dashboard", "success", "Dashboard components ready")
    return state


async def generate_full_report_extensions(state: AgentState) -> AgentState:
    """
    Process design, techno-economics, demographics / plant siting for the unified search report.
    """
    logger.info("Generating full-report extensions (process, TEA, demographics)...")
    await _send_ws_status(
        state,
        "full_report_extensions",
        "running",
        "Synthesizing process design, techno-economics, and site insights...",
    )

    drug = state.get("drug_name", "Unknown")
    tops = _top_indication_names(state)

    defaults: Dict[str, str] = dict(template_full_report_extensions(drug, tops))

    session_id = state.get("session_id", "")
    state["progress"]["ReportGenerator"] = "running"
    if session_id:
        try:
            await ws_manager.send_agent_progress(
                session_id,
                "ReportGenerator",
                "running",
                "Synthesizing process, TEA, and site sections for the unified report...",
            )
        except Exception:
            pass

    ext_prompt = (
        f'You are a pharma CMC and strategy assistant. For drug "{drug}" and repurposing focus areas: {tops}, '
        "return ONLY a valid JSON object with exactly three string keys: "
        '"process_design", "techno_economic", "demographics_sites". '
        "Each value is Markdown (2–4 short paragraphs) covering: "
        "(1) process route, key unit operations, scale-up, QbD / quality hooks; "
        "(2) TEA snapshot—COGS and capex sensitivities at a high level, explicitly not investment advice; "
        "(3) patient or disease burden touchpoints and India manufacturing site / cluster considerations. "
        "No markdown code fences and no text outside the JSON object."
    )
    raw = await _llm_text_with_fallbacks(ext_prompt)
    if raw:
        try:
            parsed = _parse_extension_json(raw)
            for k, v in parsed.items():
                defaults[k] = v
        except Exception as e:
            logger.warning("Full-report extension JSON parse failed, using stubs: %s", e)
            state["errors"].append(f"Full-report extension parse: {str(e)}")
    else:
        logger.warning("No LLM output for full-report extensions; using template stubs")

    await _agent_progress_pulse(
        state,
        "ProcessDesignAgent",
        "Finalizing process & CMC narrative...",
        "Process design section ready",
    )
    await _agent_progress_pulse(
        state,
        "TechnoEconomicAgent",
        "Finalizing techno-economic snapshot...",
        "Techno-economic section ready",
    )
    await _agent_progress_pulse(
        state,
        "DemographicsPlantAgent",
        "Finalizing demographics & site insights...",
        "Demographics & sites section ready",
    )

    state["progress"]["ReportGenerator"] = "success"
    if session_id:
        try:
            await ws_manager.send_agent_progress(
                session_id,
                "ReportGenerator",
                "success",
                "Unified report sections assembled",
            )
        except Exception:
            pass

    state["full_report_extensions"] = defaults
    await _send_ws_status(state, "full_report_extensions", "success", "Full report extensions complete")
    return state


async def _synthesize_with_llm_fallbacks(prompt: str) -> tuple[str, str | None]:
    """
    Run synthesis with Gemini (or Gemini+Groq+Ollama chain). If that fails,
    explicitly try Groq, Ollama, then a fresh Gemini client after factory reset
    so deprecated model singletons or missing chain still recover when keys exist.
    """
    first_error: BaseException | None = None
    llm = LLMFactory.get_llm()
    if llm is None:
        raise RuntimeError("No LLM configured")

    try:
        text = await llm.generate(prompt)
        return text, None
    except BaseException as e:
        first_error = e
        logger.warning("Primary synthesis generate failed: %s", e)

    for provider in ("groq", "ollama"):
        alt = LLMFactory.get_llm(force_provider=provider)
        if alt is None:
            continue
        try:
            text = await alt.generate(prompt)
            logger.info("Synthesis succeeded via explicit %s fallback", provider)
            return text, provider
        except BaseException as e2:
            logger.warning("%s synthesis fallback failed: %s", provider, e2)

    LLMFactory.reset()
    gem = LLMFactory.get_llm(force_provider="gemini")
    if gem is not None:
        try:
            text = await gem.generate(prompt)
            logger.info("Synthesis succeeded via Gemini after LLMFactory.reset()")
            return text, "gemini"
        except BaseException as e3:
            logger.warning("Gemini after reset failed: %s", e3)

    if first_error is not None:
        raise first_error
    raise RuntimeError("Synthesis failed")


async def synthesize_results(state: AgentState) -> AgentState:
    """
    Use LLM to synthesize findings into a coherent summary.
    Uses enhanced prompt with comparative data when available.

    Args:
        state: Current workflow state

    Returns:
        Updated state with synthesis
    """
    logger.info("Synthesizing results with LLM...")
    await _send_ws_status(state, "synthesizing", "running", "Generating AI-powered analysis...")

    try:
        # Get LLM instance
        llm = LLMFactory.get_llm()

        if llm is None:
            logger.warning("No LLM available, skipping synthesis")
            state["synthesis"] = (
                "LLM synthesis unavailable. Please review the ranked indications "
                "and evidence details for repurposing opportunities."
            )
            return state

        # Use enhanced prompt if comparative data is available
        enhanced_opportunities = state.get("enhanced_opportunities", {})

        if enhanced_opportunities:
            logger.info("Using enhanced synthesis prompt with comparative data")
            prompt = get_enhanced_synthesis_prompt(
                drug_name=state["drug_name"],
                agent_results=state["agent_results"],
                enhanced_opportunities=enhanced_opportunities
            )
        else:
            logger.info("Using basic synthesis prompt (no comparative data)")
            prompt = get_synthesis_prompt(
                drug_name=state["drug_name"],
                agent_results=state["agent_results"]
            )

        # Generate synthesis (Groq/Ollama/Gemini retry if primary wrapper fails)
        synthesis, used_fallback = await _synthesize_with_llm_fallbacks(prompt)
        state["synthesis"] = synthesis
        if used_fallback:
            state["errors"].append(f"Synthesis used LLM fallback: {used_fallback}")

        logger.info("Generated synthesis (%s characters)%s", len(synthesis), f" via {used_fallback}" if used_fallback else "")

    except Exception as e:
        logger.error(f"Synthesis failed: {e}", exc_info=True)
        state["synthesis"] = f"Synthesis error: {str(e)}"
        state["errors"].append(f"LLM synthesis failed: {str(e)}")

    return state


async def finalize_results(state: AgentState) -> AgentState:
    """
    Finalize the workflow by adding metadata and cleaning up.

    Args:
        state: Current workflow state

    Returns:
        Final state with complete results
    """
    logger.info("Finalizing results...")

    # Ensure molecular_details with 2D structure URL (fallback if fetch_dashboard missed it)
    from urllib.parse import quote
    drug = state.get("drug_name", "").strip() or "Unknown"
    vd = state.get("visual_data") or {}
    if not vd.get("molecular_details") and drug:
        safe_name = quote(drug)
        vd["molecular_details"] = {
            "molecular_name": drug,
            "structure_image_url": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{safe_name}/PNG?image_size=400x400",
        }
        state["visual_data"] = vd

    # Calculate execution time
    start_time = datetime.fromisoformat(state["timestamp"])
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()

    state["execution_time"] = execution_time

    # Log final summary
    logger.info("=" * 60)
    logger.info(f"Search Complete: {state['drug_name']}")
    logger.info(f"Execution Time: {execution_time:.2f}s")
    logger.info(f"Total Evidence: {len(state['all_evidence'])} items")
    logger.info(f"Repurposing Opportunities: {len(state['ranked_indications'])}")
    logger.info(f"Enhanced Opportunities: {len(state.get('enhanced_indications', []))}")
    logger.info(f"Errors: {len(state['errors'])}")
    logger.info("=" * 60)

    # Send completion via WebSocket
    session_id = state.get("session_id", "")
    if session_id:
        try:
            await ws_manager.send_complete(session_id, {
                "drug_name": state["drug_name"],
                "execution_time": round(execution_time, 2),
                "total_evidence": len(state["all_evidence"]),
                "opportunities": len(state.get("enhanced_indications", []) or state.get("ranked_indications", [])),
            })
        except Exception:
            pass

    return state
