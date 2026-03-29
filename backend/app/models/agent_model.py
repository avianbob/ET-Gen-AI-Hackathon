from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class AgentRequest(BaseModel):
    query: str
    complexity: int | None = 2

class AgentResponse(BaseModel):
    agent_id: str
    analysis: str
    recommendation: str
    grading: Dict[str, float]
    visual_data: Dict[str, Any]
    pid_data: Dict[str, Any] | None = None
    tea_data: Dict[str, Any] | None = None
    # Query context (drug, disease, symptoms, regions) for UI
    query_context: Dict[str, Any] | None = None
    # ClinicalTrials.gov data: decision, analytics, results (symptoms/conditions/trial history)
    clinical_trials_data: Dict[str, Any] | None = None
    # When Gemini returns 429, Groq fallback may be used; list of operation names that used Groq
    llm_fallback_used: List[str] | None = None