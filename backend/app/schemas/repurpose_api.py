"""
Pydantic models for request/response validation and data structures.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class EvidenceItem(BaseModel):
    """Single piece of evidence from an agent."""
    source: str = Field(..., description="Data source (literature, clinical_trials, bioactivity, patent, internal)")
    indication: Optional[str] = Field(None, description="Disease or indication associated with evidence")
    summary: str = Field(..., description="Brief summary of the evidence")
    date: Optional[str] = Field(None, description="Publication or filing date")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata specific to source")
    relevance_score: Optional[float] = Field(None, description="Relevance score (0-1)")
    url: Optional[str] = Field(None, description="URL link to the original source")
    title: Optional[str] = Field(None, description="Title of the evidence (paper title, trial name, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "literature",
                "indication": "Type 2 Diabetes",
                "summary": "Metformin reduces blood glucose levels through AMPK pathway activation",
                "date": "2023-05-15",
                "metadata": {"pmid": "12345678", "year": 2023, "citations": 150},
                "relevance_score": 0.95,
                "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
                "title": "Metformin and AMPK Pathway Activation in Diabetes Treatment"
            }
        }


class AgentResponse(BaseModel):
    """Response from a single agent execution."""
    agent_name: str = Field(..., description="Name of the agent")
    status: str = Field(..., description="Execution status (success, error, timeout)")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="List of evidence items found")
    error: Optional[str] = Field(None, description="Error message if status is error")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional execution metadata")
    execution_time: Optional[float] = Field(None, description="Time taken in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "LiteratureAgent",
                "status": "success",
                "evidence": [],
                "execution_time": 2.5
            }
        }


class IndicationResult(BaseModel):
    """Repurposing opportunity with aggregated evidence."""
    indication: str = Field(..., description="Disease or indication name")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence score (0-100)")
    evidence_count: int = Field(..., description="Number of supporting evidence items")
    evidence_items: List[EvidenceItem] = Field(..., description="List of supporting evidence")
    supporting_sources: List[str] = Field(..., description="List of data sources supporting this indication")

    class Config:
        json_schema_extra = {
            "example": {
                "indication": "Cardiovascular Disease",
                "confidence_score": 87.5,
                "evidence_count": 12,
                "evidence_items": [],
                "supporting_sources": ["literature", "clinical_trials", "bioactivity"]
            }
        }


class DrugSearchRequest(BaseModel):
    """Request model for drug repurposing search."""
    drug_name: str = Field(..., min_length=2, max_length=100, description="Name of the drug to search")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional search context")
    force_refresh: bool = Field(default=False, description="Force refresh from APIs, bypass cache")
    session_id: Optional[str] = Field(default=None, description="Session ID for WebSocket progress updates")

    class Config:
        json_schema_extra = {
            "example": {
                "drug_name": "Metformin",
                "context": {"disease_area": "metabolic"},
                "force_refresh": False
            }
        }


class SearchResponse(BaseModel):
    """Complete response from drug repurposing search."""
    drug_name: str = Field(..., description="Name of the drug searched")
    search_context: Dict[str, Any] = Field(default_factory=dict, description="Search context used")
    session_id: str = Field(..., description="Session ID for this search")

    # Agent execution results
    agent_results: Dict[str, AgentResponse] = Field(..., description="Results from each agent")
    progress: Dict[str, str] = Field(..., description="Current progress status of each agent")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")

    # Processed results
    all_evidence: List[EvidenceItem] = Field(default_factory=list, description="All evidence collected")
    ranked_indications: List[IndicationResult] = Field(..., description="Ranked list of repurposing opportunities")
    enhanced_indications: List[Dict[str, Any]] = Field(default_factory=list, description="Enhanced indications with composite scoring")
    enhanced_opportunities: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Enhanced opportunity data with comparisons, market segments, and science")

    # LLM synthesis
    synthesis: Optional[str] = Field(None, description="AI-generated synthesis of findings")

    full_report_extensions: Optional[Dict[str, str]] = Field(
        default=None,
        description="Markdown sections: process_design, techno_economic, demographics_sites",
    )

    # Dashboard components (PID, TEA, plant sites) for Results page
    pid_data: Optional[Dict[str, Any]] = Field(default=None, description="Process design / P&ID for diagram")
    tea_data: Optional[Dict[str, Any]] = Field(default=None, description="Techno-economic analysis")
    visual_data: Optional[Dict[str, Any]] = Field(default=None, description="Demographic, market, molecular details")
    query_context: Optional[Dict[str, Any]] = Field(default=None, description="Drug, disease, context for UI")
    grading: Optional[Dict[str, float]] = Field(default=None, description="Dimension scores for GradingSection")

    # Metadata
    timestamp: str = Field(..., description="Search timestamp (ISO format)")
    execution_time: float = Field(..., description="Total execution time in seconds")
    cached: bool = Field(default=False, description="Whether results were served from cache")

    class Config:
        extra = "ignore"  # Ignore extra fields from frontend
        json_schema_extra = {
            "example": {
                "drug_name": "Metformin",
                "search_context": {},
                "session_id": "abc123",
                "agent_results": {},
                "progress": {
                    "literature": "success",
                    "clinical_trials": "success",
                    "bioactivity": "success",
                    "patent": "success",
                    "internal": "success"
                },
                "errors": [],
                "all_evidence": [],
                "ranked_indications": [],
                "synthesis": "Metformin shows promise for...",
                "timestamp": "2024-01-20T10:30:00Z",
                "execution_time": 15.7,
                "cached": False
            }
        }


class ChatRequest(BaseModel):
    """Request model for chat interface."""
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    drug_name: str = Field(..., min_length=1, description="Drug being discussed")
    indications: Optional[List[str]] = Field(default=None, description="List of indication names")
    evidence_summary: Optional[str] = Field(default=None, description="Summary of evidence")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Why is Metformin promising for longevity?",
                "drug_name": "Metformin",
                "indications": ["Type 2 Diabetes", "Longevity"],
                "evidence_summary": "Multiple clinical trials show..."
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat interface."""
    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="AI-generated response")
    drug_name: str = Field(..., description="Drug being discussed")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Why is Metformin promising for longevity?",
                "answer": "Metformin is promising for longevity because...",
                "drug_name": "Metformin"
            }
        }


class ExportRequest(BaseModel):
    """Request model for PDF export."""
    search_result: SearchResponse = Field(..., description="Search results to export")
    include_synthesis: bool = Field(default=True, description="Include LLM synthesis in PDF")
    include_charts: bool = Field(default=True, description="Include visualizations")

    class Config:
        json_schema_extra = {
            "example": {
                "search_result": {},
                "include_synthesis": True,
                "include_charts": True
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    version: str = Field(default="1.0.0", description="API version")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "timestamp": "2024-01-20T10:30:00Z",
                "version": "1.0.0"
            }
        }


# ============================================================
# Conversational Chat Models (ET Techathon Master Agent System)
# ============================================================

class TableData(BaseModel):
    """Structured table data for chat responses."""
    title: str = Field("", description="Table title")
    columns: List[Dict[str, str]] = Field(..., description="Column definitions [{key, label}]")
    rows: List[Dict[str, Any]] = Field(..., description="Row data")

class ChartData(BaseModel):
    """Chart configuration for chat responses."""
    chart_type: str = Field(..., description="Chart type: bar, line, radar, pie, heatmap")
    title: str = Field("", description="Chart title")
    labels: List[str] = Field(default_factory=list, description="X-axis or category labels")
    datasets: List[Dict[str, Any]] = Field(default_factory=list, description="Chart datasets [{label, data, color}]")
    # Heatmap-specific fields
    heatmap_data: Optional[List[List[int]]] = Field(None, description="2D matrix of values for heatmap")
    row_labels: Optional[List[str]] = Field(None, description="Row labels for heatmap")
    col_labels: Optional[List[str]] = Field(None, description="Column labels for heatmap")

class AgentActivity(BaseModel):
    """Tracks which worker agent is active during processing."""
    agent_name: str = Field(..., description="ET display name of the agent")
    status: str = Field("pending", description="pending, working, done, error")
    message: str = Field("", description="Status message")

class ConversationMessage(BaseModel):
    """A single message in a conversation."""
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message text")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    tables: List[TableData] = Field(default_factory=list, description="Tables in this message")
    charts: List[ChartData] = Field(default_factory=list, description="Charts in this message")
    pdf_url: Optional[str] = Field(None, description="Download URL for generated PDF")
    excel_url: Optional[str] = Field(None, description="Download URL for generated Excel")
    agent_activities: List[AgentActivity] = Field(default_factory=list, description="Agent activities")
    suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extra metadata")

class ConversationRequest(BaseModel):
    """Request to send a message in a conversation."""
    message: str = Field(..., min_length=1, max_length=2000, description="User's message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID (None for new)")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Previous messages [{role, content}]")
    uploaded_file_ids: List[str] = Field(default_factory=list, description="IDs of uploaded files to reference")
    session_id: Optional[str] = Field(None, description="WebSocket session ID for real-time agent progress")

class ConversationResponse(BaseModel):
    """Rich response from the conversational chat."""
    conversation_id: str = Field(..., description="Conversation ID")
    message: ConversationMessage = Field(..., description="The assistant's response message")
    intent: str = Field("general", description="Detected intent of the user's query")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities (drugs, indications, etc.)")
    pipeline_metadata: Optional[Dict[str, Any]] = Field(None, description="Pipeline result metadata for frontend history tracking")

class FileUploadResponse(BaseModel):
    """Response from file upload."""
    file_id: str = Field(..., description="Unique file ID")
    filename: str = Field(..., description="Original filename")
    size_bytes: int = Field(..., description="File size in bytes")
    status: str = Field("processed", description="uploaded, processing, processed, error")
    chunks: int = Field(0, description="Number of text chunks stored")
    summary: Optional[str] = Field(None, description="Auto-generated summary")
