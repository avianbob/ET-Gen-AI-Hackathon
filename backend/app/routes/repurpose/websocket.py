"""
WebSocket Handler - Real-time agent progress updates.
Allows frontend to display live status of all 5 agents during search.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any
from datetime import datetime
import json
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("websocket")


# ET agent group mapping: internal agent name → ET display group
ET_AGENT_DISPLAY = {
    "LiteratureAgent": "Web Intelligence Agent",
    "ClinicalTrialsAgent": "Clinical Trials Agent",
    "BioactivityAgent": "Web Intelligence Agent",
    "PatentAgent": "Patent Landscape Agent",
    "InternalAgent": "Internal Knowledge Agent",
    "OpenFDAAgent": "Clinical Trials Agent",
    "OpenTargetsAgent": "Web Intelligence Agent",
    "SemanticScholarAgent": "Web Intelligence Agent",
    "DailyMedAgent": "Clinical Trials Agent",
    "KEGGAgent": "Web Intelligence Agent",
    "UniProtAgent": "Web Intelligence Agent",
    "OrangeBookAgent": "Patent Landscape Agent",
    "RxNormAgent": "Clinical Trials Agent",
    "WHOAgent": "Web Intelligence Agent",
    "DrugBankAgent": "Web Intelligence Agent",
    "MarketDataAgent": "IQVIA Insights Agent",
    "EXIMAgent": "EXIM Trade Agent",
    "IQVIAPipelineAgent": "IQVIA Insights Agent",
    "EXIMPipelineAgent": "EXIM Trade Agent",
    "WebIntelligencePipelineAgent": "Web Intelligence Agent",
    "ProcessDesignAgent": "Process Design Agent",
    "TechnoEconomicAgent": "Techno-Economic Agent",
    "DemographicsPlantAgent": "Demographics & Plant Siting Agent",
    "ReportGenerator": "Report Generator Agent",
}


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        """Initialize connection manager."""
        # Map of session_id -> WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        logger.info("WebSocket ConnectionManager initialized")

    async def connect(self, session_id: str, websocket: WebSocket):
        """
        Accept and store a new WebSocket connection.

        Args:
            session_id: Unique session identifier
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

        # Send connection confirmation
        await self.send_message(session_id, {
            "type": "connection",
            "status": "connected",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })

    def disconnect(self, session_id: str):
        """
        Remove a WebSocket connection.

        Args:
            session_id: Session to disconnect
        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")

    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """
        Send a message to a specific session.

        Args:
            session_id: Target session
            message: Message dictionary to send
        """
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
                logger.debug(f"Message sent to {session_id}: {message.get('type')}")
            except Exception as e:
                logger.error(f"Failed to send message to {session_id}: {e}")
                self.disconnect(session_id)

    async def send_agent_progress(
        self,
        session_id: str,
        agent_name: str,
        status: str,
        message: str = None,
        evidence_count: int = None
    ):
        """
        Send agent progress update to frontend.

        Args:
            session_id: Session identifier
            agent_name: Name of the agent (e.g., "LiteratureAgent")
            status: Agent status ("pending", "running", "success", "error")
            message: Optional status message
            evidence_count: Number of evidence items found
        """
        payload = {
            "type": "agent_progress",
            "agent": agent_name,
            "display_name": ET_AGENT_DISPLAY.get(agent_name, agent_name),
            "status": status,
            "timestamp": datetime.now().isoformat()
        }

        if message:
            payload["message"] = message

        if evidence_count is not None:
            payload["evidence_count"] = evidence_count

        await self.send_message(session_id, payload)

    async def send_workflow_status(
        self,
        session_id: str,
        stage: str,
        status: str,
        message: str = None
    ):
        """
        Send workflow stage update.

        Args:
            session_id: Session identifier
            stage: Workflow stage (e.g., "initialize", "run_agents", "score")
            status: Stage status
            message: Optional status message
        """
        payload = {
            "type": "workflow_status",
            "stage": stage,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }

        if message:
            payload["message"] = message

        await self.send_message(session_id, payload)

    async def send_error(self, session_id: str, error: str):
        """
        Send error message to frontend.

        Args:
            session_id: Session identifier
            error: Error message
        """
        await self.send_message(session_id, {
            "type": "error",
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    async def send_complete(self, session_id: str, result_summary: Dict[str, Any]):
        """
        Send completion notification with result summary.

        Args:
            session_id: Session identifier
            result_summary: Summary of search results
        """
        await self.send_message(session_id, {
            "type": "complete",
            "summary": result_summary,
            "timestamp": datetime.now().isoformat()
        })


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint handler.

    Args:
        websocket: WebSocket connection
        session_id: Unique session identifier from URL path
    """
    await manager.connect(session_id, websocket)

    try:
        # Keep connection alive and handle incoming messages
        while True:
            # Receive messages from client (for heartbeat/ping)
            data = await websocket.receive_text()

            # Handle ping/pong for connection keep-alive
            if data == "ping":
                await websocket.send_text("pong")
            else:
                # Echo back any other messages (for debugging)
                logger.debug(f"Received from {session_id}: {data}")

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"Client disconnected: {session_id}")

    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
        manager.disconnect(session_id)
