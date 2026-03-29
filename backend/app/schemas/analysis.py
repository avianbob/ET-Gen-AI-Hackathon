from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# --- Structured context: shared across all agents for complex query handling ---
class PharmaQueryContext(BaseModel):
    """Structured fields extracted from user query, used by master and all helper agents."""
    drug: Optional[str] = None          # Drug/molecule name
    disease: Optional[str] = None       # Disease or therapeutic indication
    diseases: Optional[List[str]] = None  # Multiple diseases/conditions (from query or enriched from trials)
    symptoms: Optional[List[str]] = None  # Relevant symptoms (from query or enriched from trials)
    side_effects: Optional[List[str]] = None  # Side effects (from query or enriched from trials)
    regions: Optional[List[str]] = None   # Geography (e.g. US, EU5, India)
    phase: Optional[str] = None         # Development phase (preclinical, Phase I/II/III, launched)
    raw_query: str = ""                 # Original user input
    complexity: str = "normal"          # low | normal | high
    query_type: str = "analysis"        # "analysis" | "alternatives" (user wants alternatives to a drug)
    reference_drug: Optional[str] = None  # When query_type=alternatives, the drug to find alternatives for

# --- Request Models ---
class AnalysisRequest(BaseModel):
    molecule_name: str
    target_indication: Optional[str] = None
    complexity: Optional[str] = "normal"  # Mapping from your AgentRequest
    # Structured context used by all agents (optional; populated by query understanding)
    context: Optional[PharmaQueryContext] = None
    # Pipeline context: set by MasterAgent between stages (do not set in controller)
    target_production_volume_kg_per_year: Optional[float] = None  # From Stage 1 (market/demand)
    injected_pid_data: Optional[Dict[str, Any]] = None  # From Stage 2, for TechnoEconomicAgent only
    # Explicit fields for agents that read them directly (synced from context when present)
    symptoms: Optional[List[str]] = None
    diseases: Optional[List[str]] = None
    side_effects: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    phase: Optional[str] = None
    # Mutable list shared with controller: when Groq fallback is used, operation names are appended
    llm_fallback_used: Optional[List[str]] = None
    # Hint for Process Design when re-running after poor economics (cost_reduction, etc.)
    optimization_focus: Optional[str] = None
    # Parsed intelligence from Stage 1 agents (market, EXIM, demographics, etc.) – set by MasterAgent
    parsed_intelligence: Optional[Dict[str, Any]] = None

# --- Result Models ---
@dataclass
class AgentResult:
    agent_name: str
    summary: str
    raw_data: Dict[str, Any]

@dataclass
class GradingBreakdown:
    market_demand: float
    production_feasibility: float
    demographics: float
    patents_and_trials: float
    competition: float
    overall_score: float

class AnalysisResponse(BaseModel):
    run_id: str
    report_content: str
    status: str
    grading: Optional[Dict[str, float]] = None
    results: Optional[List[Dict[str, Any]]] = None
    # Structured context (clean drug name, indication, etc.) – single source of truth for frontend
    context: Optional[PharmaQueryContext] = None

    class Config:
        # Allow dataclass conversion
        arbitrary_types_allowed = True