"""
LangGraph State Definition - Defines the state structure for the workflow.
State flows through all nodes and accumulates results.
"""

from typing import TypedDict, List, Dict, Any
from app.schemas.repurpose_api import AgentResponse, EvidenceItem, IndicationResult
from app.schemas.repurpose_scoring import EnhancedIndicationResult, EnhancedOpportunityData


class AgentState(TypedDict, total=False):
    """
    State structure for the drug repurposing workflow.

    The state flows through all nodes in the LangGraph workflow,
    accumulating results from each agent and processing step.
    """

    # Input parameters
    drug_name: str  # Name of the drug to analyze
    search_context: Dict[str, Any]  # Optional additional context
    session_id: str  # Unique session identifier for WebSocket updates

    # Agent execution tracking
    agent_results: Dict[str, AgentResponse]  # Results from each agent (keyed by agent name)
    progress: Dict[str, str]  # Current status of each agent (pending/running/success/error)
    errors: List[str]  # List of errors encountered during execution

    # Evidence processing
    all_evidence: List[EvidenceItem]  # All evidence items collected from agents
    ranked_indications: List[IndicationResult]  # Ranked list of repurposing opportunities
    enhanced_indications: List[EnhancedIndicationResult]  # Composite scored opportunities

    # Enhanced comparative analysis (Phase 3)
    enhanced_opportunities: Dict[str, EnhancedOpportunityData]  # Full comparative data by indication

    # Score refinement
    refinement_applied: bool  # Whether enhanced-data score refinement was applied

    # LLM synthesis
    synthesis: str  # AI-generated synthesis of findings

    # Unified report (process / TEA / demographics) for Results "Full report" tab
    full_report_extensions: Dict[str, str]

    # Dashboard components (PID diagram, TEA, plant sites) for Results page
    pid_data: Dict[str, Any]
    tea_data: Dict[str, Any]
    visual_data: Dict[str, Any]
    query_context: Dict[str, Any]
    grading: Dict[str, float]

    # Metadata
    timestamp: str  # ISO format timestamp of search start
    execution_time: float  # Total execution time in seconds
