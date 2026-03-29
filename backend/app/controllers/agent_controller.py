from typing import List
from fastapi import HTTPException
from app.models.agent_model import AgentRequest, AgentResponse
from app.schemas.analysis import AnalysisRequest, PharmaQueryContext
from app.services.gemini_service import GeminiService
from app.services.query_parser import parse_fallback
from app.services.clinical_trials_tools import (
    AgentDecision,
    SearchIntent,
    execute_clinical_search,
)

# --- Import Agents ---
# (Adjust these paths if you kept everything in one file, e.g., from app.agents.worker_agents import ...)
from app.agents.master import MasterAgent
from app.agents.market.exim_trends import EXIMTrendAgent
from app.agents.market.iqvia_insights import IQVIAInsightsAgent
from app.agents.patent_trials.clinical_trials import ClinicalTrialAgent
from app.agents.patent_trials.patent_landscape import PatentLandscapeAgent
from app.agents.production.process_design import ProcessDesignAgent
from app.agents.production.techno_economic import TechnoEconomicAgent
from app.agents.demographics.demographic import DemographicAgent
from app.agents.knowledge.internal_knowledge import InternalKnowledgeAgent
from app.agents.knowledge.web_intelligence import WebIntelligenceAgent

# Initialize unified LLM (Gemini and/or Groq). At least one of GEMINI_API_KEY or GROQ_API_KEY must be set.
try:
    gemini_service = GeminiService()
except ValueError as e:
    print(f"LLM configuration error: {e}")
    raise
except Exception as e:
    print(f"Warning: LLM service not initialized: {e}. Set GEMINI_API_KEY or GROQ_API_KEY in .env.")
    gemini_service = None

# Initialize the Master Agent globally to reuse it across requests
# This creates the "Team" of workers.
def build_master_agent() -> MasterAgent:
    # Order matters for Stage 1: IQVIA first so EXIM/Demographics get market size & regions for accuracy
    workers = [
        IQVIAInsightsAgent(gemini_service=gemini_service),
        EXIMTrendAgent(gemini_service=gemini_service),
        ClinicalTrialAgent(gemini_service=gemini_service),
        PatentLandscapeAgent(),
        ProcessDesignAgent(gemini_service=gemini_service),
        TechnoEconomicAgent(gemini_service=gemini_service),
        DemographicAgent(gemini_service=gemini_service),
        InternalKnowledgeAgent(),
        WebIntelligenceAgent(),
    ]
    return MasterAgent(agents=workers, llm_service=gemini_service)

# Instantiate once
master_agent_instance = build_master_agent()

def _map_complexity(level: int | None) -> str:
    """
    Map incoming numeric complexity to a textual hint that worker agents can use.
    """
    mapping = {1: "low", 2: "normal", 3: "high"}
    return mapping.get(level, "normal")

def _query_understanding(
    raw_query: str,
    complexity: str,
    fallback_used_list: List[str] | None = None,
) -> PharmaQueryContext:
    """Extract structured context via Gemini; fallback to rule-based parser if Gemini unavailable or fails."""
    if gemini_service:
        ctx = gemini_service.extract_structured_context(
            user_input=raw_query,
            complexity_hint=complexity,
            fallback_used_list=fallback_used_list,
        )
        if ctx is not None:
            print(f"[Controller] Query understood (LLM): drug={ctx.drug}, disease={ctx.disease}, symptoms={getattr(ctx, 'symptoms', None)}, side_effects={getattr(ctx, 'side_effects', None)}")
            return ctx
        print("[Controller] extract_structured_context returned None; using parse_fallback.")
    ctx = parse_fallback(raw_query, complexity)
    print(f"[Controller] Query understood (fallback): drug={ctx.drug}, disease={ctx.disease}, symptoms={getattr(ctx, 'symptoms', None)}, side_effects={getattr(ctx, 'side_effects', None)}")
    return ctx


async def process_agent_task(data: AgentRequest) -> AgentResponse:
    """
    Orchestrates the analysis pipeline:
    1. Query understanding via LLM (Gemini or Groq)
    2. Build AnalysisRequest with context for all agents
    3. Run MasterAgent (agents in series: Stage 1 → 2 → 3)
    4. Return formatted AgentResponse with real analysis (no dummy data).
    """
    if gemini_service is None:
        raise HTTPException(
            status_code=503,
            detail="No LLM configured. Set GEMINI_API_KEY or GROQ_API_KEY in .env and restart the server.",
        )
    original_query = data.query or ""
    complexity = _map_complexity(data.complexity)
    print(f"Controller processing query: {original_query}")
    llm_fallback_used: List[str] = []

    # 1. Query understanding: structured params used across all agents
    context = _query_understanding(original_query, complexity, fallback_used_list=llm_fallback_used)
    _get_ctx = lambda k: getattr(context, k, None)
    print(f"[Controller] Query context after understanding: drug={_get_ctx('drug')}, disease={_get_ctx('disease')}, symptoms={_get_ctx('symptoms')}, diseases={_get_ctx('diseases')}, side_effects={_get_ctx('side_effects')}")

    # 2. ALTERNATIVES FLOW: user asked for "alternatives to X" -> find other drugs for same indication
    if _get_ctx("query_type") == "alternatives" and (_get_ctx("reference_drug") or context.drug):
        reference_drug = _get_ctx("reference_drug") or context.drug
        print(f"[Controller] Alternatives flow: reference_drug={reference_drug}")
        indication = None
        if gemini_service:
            indication = gemini_service.get_indication_for_drug(
                reference_drug,
                fallback_used_list=llm_fallback_used,
            )
            if indication:
                print(f"[Controller] Indication for {reference_drug}: {indication}")
        if not indication:
            indication = "Pain"  # fallback for common case (e.g. Paracetamol)
        indication_clean = (indication or "").strip().split(",")[0].strip() or "Pain"
        decision = AgentDecision(
            drug=None,
            disease=indication_clean,
            intent=SearchIntent.REVERSE_DISCOVERY,
            reasoning=f"User asked for alternatives to {reference_drug}; searching drugs for indication: {indication_clean}",
        )
        search_result = execute_clinical_search(decision)
        if "error" in search_result:
            alternatives_report = f"Could not fetch alternatives for {reference_drug}: {search_result['error']}."
            clinical_trials_data_alt = None
        else:
            results_list = search_result.get("results", [])
            lines = [
                f"# Alternatives to {reference_drug}",
                f"Indication: {indication_clean}",
                "",
                f"Found {len(results_list)} trials for this indication. Below are candidate alternatives (from ClinicalTrials.gov):",
                "",
            ]
            for i, r in enumerate(results_list[:15], 1):
                title = r.get("title", "Unknown")
                nct = r.get("id", "")
                conditions = r.get("conditions", [])
                cond_str = ", ".join(conditions[:3]) if conditions else "—"
                lines.append(f"{i}. **{title}**")
                lines.append(f"   NCT: {nct} | Conditions: {cond_str}")
                lines.append("")
            alternatives_report = "\n".join(lines)
            clinical_trials_data_alt = {
                "decision": decision.model_dump(mode="json"),
                "analytics": search_result.get("analytics"),
                "results": results_list,
            }
        query_context_alt = {
            "drug": reference_drug,
            "disease": indication,
            "diseases": _get_ctx("diseases"),
            "symptoms": _get_ctx("symptoms"),
            "side_effects": _get_ctx("side_effects"),
            "regions": _get_ctx("regions"),
            "phase": _get_ctx("phase"),
            "raw_query": original_query,
            "query_type": "alternatives",
            "reference_drug": reference_drug,
        }
        return AgentResponse(
            agent_id=str(__import__("uuid").uuid4()),
            analysis=alternatives_report,
            recommendation=f"Consider the listed alternatives to {reference_drug} for {indication}. Review each trial (NCT ID) on ClinicalTrials.gov for details.",
            grading={
                "market_demand": 0.5,
                "production_feasibility": 0.5,
                "demographics": 0.5,
                "patents_and_trials": 0.6,
                "competition": 0.5,
                "overall_score": 0.52,
            },
            visual_data={},
            pid_data=None,
            tea_data=None,
            query_context=query_context_alt,
            clinical_trials_data=clinical_trials_data_alt,
            llm_fallback_used=llm_fallback_used,
        )

    # 3. Build AnalysisRequest from structured context (normal analysis flow)
    # Use a display-friendly molecule name: avoid raw query string when it looks like free text
    def _looks_like_raw_query(s: str) -> bool:
        if not s or len(s) > 60:
            return True
        s_lower = s.lower()
        if s_lower.strip() == (original_query or "").strip().lower():
            return True
        if any(w in s_lower for w in ("find", "repurposing", "medicine for", "drug for", "treatment for", "search")):
            return True
        return False
    if context.drug and not _looks_like_raw_query(context.drug):
        molecule_name = context.drug
    elif context.disease:
        molecule_name = f"treatment for {context.disease}"
    else:
        molecule_name = original_query.strip() or "API"
    analysis_req = AnalysisRequest(
        molecule_name=molecule_name,
        target_indication=context.disease,
        complexity=context.complexity,
        context=context,
        symptoms=context.symptoms,
        diseases=context.diseases,
        side_effects=context.side_effects,
        regions=context.regions,
        phase=context.phase,
        llm_fallback_used=llm_fallback_used,
    )

    # 4. Run Pipeline (Async)
    pipeline_result = await master_agent_instance.run_pipeline(analysis_req)
    
    # Store enhanced query for report generation (if needed)
    # The agents use original_query, but we can use enhanced_query for report context

    # 5. Extract grading dict (already converted in master.py)
    grading_dict = pipeline_result.grading or {}

    # 6. Initialize visual data (only real data from pipeline; no dummy defaults)
    visual_data = {}

    # 7. Extract PID, TEA, Clinical Trials, Market (IQVIA), EXIM, and Demographic (plant sites) data
    pid_data = None
    tea_data = None
    clinical_trials_data = None
    market_data = None
    exim_data = None
    demographic_data = None
    if pipeline_result.results:
        for result in pipeline_result.results:
            if isinstance(result, dict):
                agent_name = result.get("agent_name", "").lower()
                raw_data = result.get("raw_data", {}) or {}
                if isinstance(raw_data, dict):
                    if "process" in agent_name and "design" in agent_name:
                        pid_data = raw_data.get("pid_data")
                        if pid_data:
                            continue
                    elif "techno" in agent_name or "economic" in agent_name:
                        tea_data = raw_data
                        continue
                    elif "clinical" in agent_name and "trial" in agent_name:
                        clinical_trials_data = {
                            "decision": raw_data.get("clinical_trials_decision"),
                            "analytics": raw_data.get("clinical_trials_analytics"),
                            "results": raw_data.get("clinical_trials_results"),
                            "ongoing_trials_count": raw_data.get("ongoing_trials_count"),
                        }
                        continue
                    elif "iqvia" in agent_name:
                        market_data = raw_data
                        continue
                    elif "exim" in agent_name:
                        exim_data = raw_data
                        continue
                    elif "demographic" in agent_name:
                        demographic_data = raw_data
                        continue
            elif hasattr(result, "agent_name"):
                agent_name = result.agent_name.lower()
                raw_data = getattr(result, "raw_data", None) or {}
                if isinstance(raw_data, dict):
                    if "process" in agent_name and "design" in agent_name:
                        pid_data = raw_data.get("pid_data")
                        if pid_data:
                            continue
                    elif "techno" in agent_name or "economic" in agent_name:
                        tea_data = raw_data
                        continue
                    elif "clinical" in agent_name and "trial" in agent_name:
                        clinical_trials_data = {
                            "decision": raw_data.get("clinical_trials_decision"),
                            "analytics": raw_data.get("clinical_trials_analytics"),
                            "results": raw_data.get("clinical_trials_results"),
                            "ongoing_trials_count": raw_data.get("ongoing_trials_count"),
                        }
                        continue
                    elif "iqvia" in agent_name:
                        market_data = raw_data
                        continue
                    elif "exim" in agent_name:
                        exim_data = raw_data
                        continue
                    elif "demographic" in agent_name:
                        demographic_data = raw_data
                        continue

    # Use pipeline molecule_name as display drug so P&ID and UI never show raw query string
    display_drug = analysis_req.molecule_name
    # Normalize PID payload so diagram always shows molecule name, not raw query
    if pid_data and isinstance(pid_data, dict):
        mh = pid_data.get("material_handling")
        if isinstance(mh, dict):
            mh["target_molecule"] = display_drug
    def _safe_str(v):
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip() or None
        if isinstance(v, dict):
            return None  # avoid sending objects (e.g. {step_1, step_2}) to frontend
        return str(v).strip() or None

    def _safe_str_list(v):
        if not isinstance(v, list):
            return None
        return [x for x in v if isinstance(x, str) and x.strip()] or None

    if analysis_req.context:
        ctx = analysis_req.context
        _get = lambda k: ctx.get(k) if isinstance(ctx, dict) else getattr(ctx, k, None)
        query_context = {
            "drug": display_drug,
            "disease": _safe_str(_get("disease")) or analysis_req.target_indication,
            "diseases": _safe_str_list(_get("diseases")),
            "symptoms": _safe_str_list(_get("symptoms")),
            "side_effects": _safe_str_list(_get("side_effects")),
            "regions": _safe_str_list(_get("regions")),
            "phase": _safe_str(_get("phase")),
            "raw_query": _safe_str(_get("raw_query")),
            "query_type": _safe_str(_get("query_type")) or "analysis",
            "reference_drug": _safe_str(_get("reference_drug")),
        }
    else:
        query_context = {
            "drug": display_drug,
            "disease": analysis_req.target_indication,
            "diseases": None,
            "symptoms": None,
            "side_effects": None,
            "regions": None,
            "phase": None,
            "raw_query": None,
            "query_type": "analysis",
            "reference_drug": None,
        }

    print(f"[Controller] query_context before enrichment: drug={query_context.get('drug')}, disease={query_context.get('disease')}, symptoms={query_context.get('symptoms')}, side_effects={query_context.get('side_effects')}")

    # Enrich query_context from clinical trials response via Gemini (symptoms, diseases, side_effects)
    if clinical_trials_data and clinical_trials_data.get("results") and gemini_service:
        try:
            drug_for_insights = query_context.get("drug") or analysis_req.molecule_name
            insights = gemini_service.extract_clinical_trials_insights(
                clinical_trials_data["results"],
                drug_name=drug_for_insights,
                fallback_used_list=llm_fallback_used,
            )
            if insights:
                # Merge: prefer existing from query, then add from trials (dedupe)
                def _merge_list(existing, new):
                    seen = set()
                    out = []
                    for x in (existing or []):
                        x = (x or "").strip()
                        if x and x.lower() not in seen:
                            seen.add(x.lower())
                            out.append(x)
                    for x in (new or []):
                        x = (x or "").strip()
                        if x and x.lower() not in seen:
                            seen.add(x.lower())
                            out.append(x)
                    return out

                query_context["symptoms"] = _merge_list(query_context.get("symptoms"), insights.get("symptoms", []))
                query_context["diseases"] = _merge_list(query_context.get("diseases"), insights.get("diseases", []))
                query_context["side_effects"] = _merge_list(query_context.get("side_effects"), insights.get("side_effects", []))
                clinical_trials_data["extracted_insights"] = insights
                print(f"[Controller] Enriched query_context from trials: symptoms={len(query_context['symptoms'])}, diseases={len(query_context['diseases'])}, side_effects={len(query_context['side_effects'])}")
        except Exception as e:
            print(f"[Controller] Failed to extract clinical trials insights: {e}")

    # 8. Generate revenue projection from TEA data if available
    if tea_data:
        revenue = tea_data.get("revenue_million_usd_per_year", 0)
        opex = tea_data.get("total_opex_million_usd_per_year", 0)
        project_life = tea_data.get("project_life_years", 10)
        
        # Generate year-by-year projection
        revenue_projection = []
        for year in range(1, project_life + 1):
            year_revenue = revenue * (1.05 ** (year - 1))  # 5% growth
            year_opex = opex * (1.03 ** (year - 1))  # 3% inflation
            revenue_projection.append({
                "year": str(2025 + year - 1),
                "revenue": round(year_revenue, 1),
                "cost": round(year_opex, 1),
                "profit": round(year_revenue - year_opex, 1)
            })
        visual_data["revenue_projection"] = revenue_projection

    # 8b. Attach market (IQVIA), EXIM, and demographic (plant sites) data for UI
    if market_data:
        visual_data["market_data"] = market_data
    if exim_data:
        visual_data["exim_data"] = exim_data
    if demographic_data:
        visual_data["demographic_data"] = demographic_data

    # 8c. Molecular details (name, family, weight, structure image, brief details) via Gemini/Groq
    if gemini_service and display_drug:
        try:
            mol_details = gemini_service.get_molecular_details(
                display_drug,
                fallback_used_list=llm_fallback_used,
            )
            if mol_details:
                visual_data["molecular_details"] = mol_details
        except Exception as e:
            print(f"[Controller] Molecular details failed: {e}")

    # 9. Map Output - Return formatted AgentResponse with all required fields
    print(f"[Controller] Final query_context for frontend: drug={query_context.get('drug')}, disease={query_context.get('disease')}, symptoms={query_context.get('symptoms')}, side_effects={query_context.get('side_effects')}")

    return AgentResponse(
        agent_id=pipeline_result.run_id,
        analysis=pipeline_result.report_content,
        recommendation=extract_recommendation(pipeline_result.report_content),
        grading=grading_dict,
        visual_data=visual_data,
        pid_data=pid_data,
        tea_data=tea_data,
        query_context=query_context,
        clinical_trials_data=clinical_trials_data,
        llm_fallback_used=llm_fallback_used,
    )

def extract_recommendation(report_text: str) -> str:
    """
    Helper to extract the conclusion or generate a simple recommendation string.
    """
    if "highly attractive" in report_text:
        return "High Priority: Proceed with detailed feasibility."
    elif "moderately attractive" in report_text:
        return "Medium Priority: Further due diligence required."
    else:
        return "Low Priority: Evaluate risks carefully before proceeding."