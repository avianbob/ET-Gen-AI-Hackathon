"""
Chat API Routes - Conversational AI for pharmaceutical planning.

Includes both the original Q&A endpoint and the new Master Agent conversational endpoint.
"""

import uuid
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.schemas.repurpose_api import (
    ChatRequest, ChatResponse,
    ConversationRequest, ConversationResponse,
    ConversationMessage, AgentActivity,
)
from app.agents.repurposing.master_agent import MasterAgent, ET_AGENT_NAMES
from app.services.repurpose.llm.llm_factory import LLMFactory
from app.services.repurpose.chat.conversation_manager import ConversationManager
from app.routes.repurpose.websocket import manager as ws_manager
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("api.chat")
router = APIRouter()

# Singletons
_master_agent = MasterAgent()
_conv_manager = ConversationManager()


@router.post("/chat/message", response_model=ConversationResponse)
async def conversational_chat(request: ConversationRequest) -> ConversationResponse:
    """
    Main conversational endpoint powered by the Master Agent.

    The Master Agent interprets the user's query, routes to appropriate
    worker agents (IQVIA, EXIM, Patent, Clinical Trials, etc.),
    and synthesizes a rich response with tables, charts, and PDF links.
    """
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        conversation_id = request.conversation_id or f"conv-{uuid.uuid4().hex[:12]}"
        logger.info(f"[{conversation_id}] Chat message: {request.message[:100]}...")

        # Step 1: Master Agent interprets the query
        classification = await _master_agent.interpret_query(
            message=request.message,
            conversation_history=request.conversation_history
        )

        intent = classification.get("intent", "general_question")
        entities = classification.get("entities", {})
        agents_needed = classification.get("agents_needed", [])
        clarification_questions = classification.get("clarification_questions", [])

        logger.info(f"[{conversation_id}] Intent: {intent}, Agents: {agents_needed}, Entities: {entities}")

        # Step 2: If clarification needed, return questions
        if intent == "clarification_needed" and clarification_questions:
            clarification_text = "I'd like to help, but could you clarify:\n\n"
            for i, q in enumerate(clarification_questions, 1):
                clarification_text += f"{i}. {q}\n"
            clarification_text += "\nPlease provide more details so I can route your query to the right agents."

            return ConversationResponse(
                conversation_id=conversation_id,
                message=ConversationMessage(
                    role="assistant",
                    content=clarification_text,
                    suggestions=clarification_questions[:3],
                ),
                intent=intent,
                entities=entities,
            )

        # Step 3: Build agent activity list for UI
        agent_activities = []
        ws_session = request.session_id
        for agent_key in agents_needed:
            display_name = ET_AGENT_NAMES.get(agent_key, agent_key)
            agent_activities.append(AgentActivity(
                agent_name=display_name,
                status="working",
                message=f"Querying {display_name}..."
            ))

        # Send real-time progress via WebSocket (if session connected)
        if ws_session:
            try:
                await ws_manager.send_message(ws_session, {
                    "type": "chat_agents_info",
                    "agents_needed": agents_needed,
                    "agent_names": {k: ET_AGENT_NAMES.get(k, k) for k in agents_needed},
                })
                for agent_key in agents_needed:
                    display_name = ET_AGENT_NAMES.get(agent_key, agent_key)
                    # Report agent starts after pipeline, so mark as pending initially
                    if agent_key == "report":
                        await ws_manager.send_agent_progress(
                            ws_session, agent_key, "pending", "Waiting for pipeline..."
                        )
                    else:
                        await ws_manager.send_agent_progress(
                            ws_session, agent_key, "running", f"Querying {display_name}..."
                        )
            except Exception as ws_err:
                logger.debug(f"WebSocket progress send failed (non-blocking): {ws_err}")

        # Step 4: Execute worker agents
        agent_results = await _master_agent.execute_agents(
            intent=intent,
            entities=entities,
            agents_needed=agents_needed,
            message=request.message,
            uploaded_file_ids=request.uploaded_file_ids,
            session_id=ws_session,
            conversation_id=conversation_id,
        )

        # Build pipeline metadata for frontend history tracking
        pipeline_metadata = None
        if "pipeline" in agents_needed:
            pipeline_result = agent_results.get("pipeline", {})
            if isinstance(pipeline_result, dict) and pipeline_result.get("status") == "success":
                pipe_data = pipeline_result.get("data", {})
                pipeline_metadata = {
                    "drug_name": pipe_data.get("drug_name", ""),
                    "opportunity_count": pipe_data.get("opportunities", 0),
                    "evidence_count": pipe_data.get("evidence_count", 0),
                    "source": "chat",
                }

        # Update agent activities to done + send WebSocket completion
        for activity in agent_activities:
            activity.status = "done"
            activity.message = "Complete"

        if ws_session:
            try:
                for agent_key in agents_needed:
                    if agent_key != "pipeline":  # Pipeline sends its own per-agent updates
                        result = agent_results.get(agent_key, {})
                        status = "error" if isinstance(result, dict) and "error" in result else "success"
                        await ws_manager.send_agent_progress(ws_session, agent_key, status, "Complete")
                await ws_manager.send_workflow_status(ws_session, "synthesize", "running", "Synthesizing response...")
            except Exception as ws_err:
                logger.debug(f"WebSocket completion send failed (non-blocking): {ws_err}")

        # Step 5: Synthesize response
        synthesis = await _master_agent.synthesize_response(
            message=request.message,
            intent=intent,
            agent_results=agent_results,
            entities=entities
        )

        # Step 6: Build response message
        tables_data = synthesis.get("tables", [])
        charts_data = synthesis.get("charts", [])

        response_message = ConversationMessage(
            role="assistant",
            content=synthesis.get("content", "I couldn't generate a response. Please try again."),
            tables=[
                {"title": t.get("title", ""), "columns": t.get("columns", []), "rows": t.get("rows", [])}
                for t in tables_data
            ] if tables_data else [],
            charts=[
                {**c, "chart_type": c.get("chart_type") or c.get("type", "bar")}
                for c in charts_data
            ] if charts_data else [],
            pdf_url=synthesis.get("pdf_url"),
            excel_url=synthesis.get("excel_url"),
            agent_activities=agent_activities,
            suggestions=synthesis.get("suggestions", []),
        )

        logger.info(f"[{conversation_id}] Response: {len(synthesis.get('content', ''))} chars, {len(tables_data)} tables, {len(charts_data)} charts")

        # Signal completion via WebSocket
        if ws_session:
            try:
                await ws_manager.send_message(ws_session, {
                    "type": "complete",
                    "status": "success",
                })
            except Exception:
                pass

        # Persist conversation messages with all rich data
        try:
            _conv_manager.save_message(conversation_id, "user", request.message)
            _conv_manager.save_message(
                conversation_id, "assistant",
                synthesis.get("content", ""),
                metadata={"intent": intent},
                tables=[
                    {"title": t.get("title", ""), "columns": t.get("columns", []), "rows": t.get("rows", [])}
                    for t in tables_data
                ] if tables_data else None,
                charts=[
                    {**c, "chart_type": c.get("chart_type") or c.get("type", "bar")}
                    for c in charts_data
                ] if charts_data else None,
                suggestions=synthesis.get("suggestions") or None,
                agent_activities=agent_activities or None,
                pdf_url=synthesis.get("pdf_url"),
                excel_url=synthesis.get("excel_url"),
            )
        except Exception as persist_err:
            logger.warning(f"Failed to persist conversation (non-blocking): {persist_err}")

        return ConversationResponse(
            conversation_id=conversation_id,
            message=response_message,
            intent=intent,
            entities=entities,
            pipeline_metadata=pipeline_metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversational chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# =====================================================
# Original Q&A endpoint (kept for backward compatibility)
# =====================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Answer questions about drug repurposing search results (legacy endpoint).
    """
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        logger.info(f"Chat request: {request.question[:100]}...")

        llm = LLMFactory.get_llm()
        if llm is None:
            raise HTTPException(
                status_code=503,
                detail="LLM service unavailable. Please check Gemini API key or Ollama installation."
            )

        prompt = _build_chat_prompt(
            question=request.question,
            drug_name=request.drug_name,
            indications=request.indications,
            evidence_summary=request.evidence_summary
        )

        answer = await llm.generate(prompt)

        return ChatResponse(
            question=request.question,
            answer=answer,
            drug_name=request.drug_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


def _build_chat_prompt(question, drug_name, indications=None, evidence_summary=None):
    """Build a context-aware prompt for the chat LLM."""
    prompt_parts = [
        "You are a pharmaceutical research assistant helping users understand drug repurposing opportunities.",
        f"\n## Context\n",
        f"Drug: {drug_name}",
    ]

    if indications:
        prompt_parts.append(f"\nIdentified Repurposing Opportunities:")
        for i, indication in enumerate(indications[:5], 1):
            prompt_parts.append(f"{i}. {indication}")

    if evidence_summary:
        prompt_parts.append(f"\n## Evidence Summary\n{evidence_summary}")

    prompt_parts.append(f"\n## User Question\n{question}")
    prompt_parts.append(
        "\n## Instructions\n"
        "Provide a clear, accurate answer based on the context above. "
        "If the question asks about information not in the context, say so. "
        "Keep your answer concise (2-4 paragraphs) and scientific. "
        "Cite specific evidence when possible."
    )

    return "\n".join(prompt_parts)


@router.get("/chat/conversations")
async def list_conversations(limit: int = 50) -> Dict[str, Any]:
    """Get list of all saved conversations (most recent first)."""
    try:
        conversations = _conv_manager.list_conversations(limit=limit)
        return {"total": len(conversations), "conversations": conversations}
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> Dict[str, Any]:
    """Get full conversation by ID with all messages."""
    conversation = _conv_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/chat/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str) -> Dict[str, Any]:
    """Delete a conversation."""
    success = _conv_manager.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "success", "message": f"Conversation {conversation_id} deleted"}


@router.get("/chat/health")
async def chat_health() -> Dict[str, Any]:
    """Check if chat service (LLM) is available."""
    try:
        llm = LLMFactory.get_llm()
        if llm is None:
            return {"status": "unavailable", "message": "No LLM provider available"}

        model_name = getattr(llm, 'model', 'unknown')
        return {
            "status": "available",
            "provider": llm.__class__.__name__,
            "model": model_name,
            "master_agent": "active"
        }
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        return {"status": "error", "message": str(e)}
