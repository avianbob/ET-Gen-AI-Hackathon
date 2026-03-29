"""
ClinicalTrials.gov API v2 helper agent using intent-based search (same prompts as ClinicalTrails.gov).
Uses shared LLM (Gemini/Groq) to classify intent then calls API.
"""
from typing import Any, Dict, Optional, TYPE_CHECKING
from ..base import BaseAgent
from ...schemas.analysis import AnalysisRequest
from ...services.clinical_trials_tools import (
    AgentDecision,
    SearchIntent,
    execute_clinical_search,
)
if TYPE_CHECKING:
    from ...services.gemini_service import GeminiService


class ClinicalTrialAgent(BaseAgent):
    """
    Fetches trials from ClinicalTrials.gov API v2 using intent-based search.
    Classifies user intent via shared LLM (Gemini with Groq fallback), then queries the API.
    """

    def __init__(self, name: str | None = None, gemini_service: Optional["GeminiService"] = None) -> None:
        super().__init__(name=name)
        self.gemini_service = gemini_service

    async def run(self, request: AnalysisRequest):
        molecule = request.molecule_name or "Unknown"
        indication = request.target_indication
        raw_query = getattr(request.context, "raw_query", None) if request.context else None
        user_prompt = raw_query or (f"{molecule} for {indication}" if indication else molecule)

        print(f"[ClinicalTrialAgent] run started: molecule={molecule}, indication={indication}, user_prompt={user_prompt[:60]}...")

        decision = None
        if self.gemini_service:
            try:
                decision = self.gemini_service.get_clinical_trial_decision(
                    user_prompt,
                    fallback_used_list=getattr(request, "llm_fallback_used", None),
                )
            except Exception as e:
                print(f"[ClinicalTrialAgent] LLM decision error: {e}")
        if decision is None:
            decision = AgentDecision(
                drug=molecule,
                disease=indication,
                intent=SearchIntent.BROAD,
                reasoning="Fallback: no LLM; using BROAD search with molecule/indication.",
            )
            print(f"[ClinicalTrialAgent] Using fallback decision: drug={decision.drug}, disease={decision.disease}, intent=BROAD")
        else:
            print(f"[ClinicalTrialAgent] Using LLM decision: intent={decision.intent}, drug={decision.drug}, disease={decision.disease}")

        search_result = execute_clinical_search(decision)
        print(f"[ClinicalTrialAgent] execute_clinical_search returned keys: {list(search_result.keys())}")

        if "error" in search_result:
            print(f"[ClinicalTrialAgent] API error in search_result: {search_result['error']}")
            count = 0
            trial_titles = [f"Error: {search_result['error']}"]
            analytics = {}
            results_list = []
        else:
            results_list = search_result.get("results", [])
            analytics = search_result.get("analytics", {})
            count = analytics.get("total_found", len(results_list))
            trial_titles = [r.get("title", "Unknown Trial") for r in results_list[:5]]
            print(f"[ClinicalTrialAgent] total_found={count}, phase_distribution={analytics.get('phase_distribution')}")

        score = min(0.3 + (count * 0.1), 0.95) if count > 0 else 0.4
        final_score = self._apply_complexity(score, request.complexity)

        data: Dict[str, Any] = {
            "ongoing_trials_count": count,
            "top_trials": trial_titles[:3],
            "indication_expansion_potential_score": 0.75 if count > 2 else 0.4,
            "patents_and_trials_score": final_score,
            "clinical_trials_decision": decision.model_dump(mode="json") if hasattr(decision, "model_dump") else {"drug": decision.drug, "disease": decision.disease, "intent": decision.intent.value, "reasoning": decision.reasoning},
            "clinical_trials_analytics": analytics,
            "clinical_trials_results": results_list,
        }

        phase_note = f" (phase focus: {request.phase})" if request.phase else ""
        summary = (
            f"Found {count} trials for {molecule}{phase_note} (intent: {decision.intent.value}). "
            f"Key studies: {', '.join(trial_titles[:2])}."
        )
        print(f"[ClinicalTrialAgent] run completed: count={count}, score={final_score:.2f}")
        return self._result(summary=summary, raw_data=data)
