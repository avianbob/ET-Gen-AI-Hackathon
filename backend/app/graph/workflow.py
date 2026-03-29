"""
LangGraph Workflow - Assembles all nodes into a complete workflow.
This is the main orchestrator for the multi-agent drug repurposing system.
"""

from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes import (
    initialize_search,
    run_agents_parallel,
    aggregate_evidence,
    score_evidence,
    analyze_comparatives,
    refine_scores,
    fetch_dashboard_components,
    generate_full_report_extensions,
    synthesize_results,
    finalize_results
)
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("graph.workflow")


def create_repurposing_workflow():
    """
    Create the LangGraph workflow for drug repurposing.

    The workflow follows this sequence:
    1. initialize_search - Set up initial state
    2. run_agents_parallel - Execute all 15 agents concurrently
    3. aggregate_evidence - Combine evidence from all agents
    4. score_evidence - Rank repurposing opportunities (base 4D scoring)
    5. analyze_comparatives - Compare against existing treatments
    6. refine_scores - Adjust scores using enhanced comparative/scientific/market data
    7. fetch_dashboard_components - PID, TEA, demographics for ProfessionalPID, TeaSection, PlantSiteMap
    8. generate_full_report_extensions - Process design, TEA, demographics (markdown for Full report tab)
    9. synthesize_results - Generate AI summary with LLM
    10. finalize_results - Add metadata and complete

    Returns:
        Compiled LangGraph workflow
    """
    logger.info("Creating drug repurposing workflow...")

    # Create state graph
    workflow = StateGraph(AgentState)

    # Add nodes to the graph
    workflow.add_node("initialize", initialize_search)
    workflow.add_node("run_agents", run_agents_parallel)
    workflow.add_node("aggregate", aggregate_evidence)
    workflow.add_node("score", score_evidence)
    workflow.add_node("analyze_comparatives", analyze_comparatives)
    workflow.add_node("refine_scores", refine_scores)
    workflow.add_node("fetch_dashboard", fetch_dashboard_components)
    workflow.add_node("full_report_extensions", generate_full_report_extensions)
    workflow.add_node("synthesize", synthesize_results)
    workflow.add_node("finalize", finalize_results)

    # Define edges (execution flow)
    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "run_agents")
    workflow.add_edge("run_agents", "aggregate")
    workflow.add_edge("aggregate", "score")
    workflow.add_edge("score", "analyze_comparatives")
    workflow.add_edge("analyze_comparatives", "refine_scores")
    workflow.add_edge("refine_scores", "fetch_dashboard")
    workflow.add_edge("fetch_dashboard", "full_report_extensions")
    workflow.add_edge("full_report_extensions", "synthesize")
    workflow.add_edge("synthesize", "finalize")
    workflow.add_edge("finalize", END)

    # Compile the workflow
    compiled_workflow = workflow.compile()

    logger.info("Workflow created successfully")
    logger.info(
        "Workflow steps: initialize -> run_agents -> aggregate -> score -> "
        "analyze_comparatives -> refine_scores -> fetch_dashboard -> full_report_extensions -> synthesize -> finalize"
    )

    return compiled_workflow


# Create a singleton instance of the workflow
_workflow_instance = None


def get_workflow():
    """
    Get the compiled workflow instance (singleton pattern).

    Returns:
        Compiled LangGraph workflow
    """
    global _workflow_instance

    if _workflow_instance is None:
        _workflow_instance = create_repurposing_workflow()

    return _workflow_instance


def reset_workflow():
    """Clear compiled graph (call on app startup after code changes)."""
    global _workflow_instance
    _workflow_instance = None
