"""
Conversation Manager - Persists chat conversations to filesystem JSON files.
Pattern: Similar to CacheManager and ReportArchiveManager.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, List, Dict

from app.services.repurpose.utils.logger import get_logger

logger = get_logger("conversations")


class ConversationManager:
    """Manages persistence of chat conversations using JSON files."""

    def __init__(self, conversations_dir: Optional[str] = None):
        self.conversations_dir = Path(conversations_dir or "data/conversations")
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Conversation manager initialized: {self.conversations_dir}")

    def _get_file(self, conversation_id: str) -> Path:
        return self.conversations_dir / f"{conversation_id}.json"

    def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tables: Optional[List[Dict[str, Any]]] = None,
        charts: Optional[List[Dict[str, Any]]] = None,
        suggestions: Optional[List[str]] = None,
        agent_activities: Optional[List[Any]] = None,
        pdf_url: Optional[str] = None,
        excel_url: Optional[str] = None,
    ):
        """Append a message to a conversation (creates file if new)."""
        file_path = self._get_file(conversation_id)

        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    conversation = json.load(f)
            except Exception:
                conversation = self._new_conversation(conversation_id)
        else:
            conversation = self._new_conversation(conversation_id)

        message_data = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        # Include rich data if present (for assistant messages)
        if tables:
            message_data["tables"] = tables
        if charts:
            message_data["charts"] = charts
        if suggestions:
            message_data["suggestions"] = suggestions
        if agent_activities:
            message_data["agent_activities"] = [
                a if isinstance(a, dict) else {"agent_name": a.agent_name, "status": a.status, "message": a.message}
                for a in agent_activities
            ]
        if pdf_url:
            message_data["pdf_url"] = pdf_url
        if excel_url:
            message_data["excel_url"] = excel_url

        conversation["messages"].append(message_data)
        conversation["updated_at"] = datetime.now().isoformat()

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(conversation, f, indent=2, default=str)

    def _new_conversation(self, conversation_id: str) -> Dict[str, Any]:
        return {
            "conversation_id": conversation_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": [],
        }

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        file_path = self._get_file(conversation_id)
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load conversation {conversation_id}: {e}")
            return None

    def list_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List conversations (most recent first) with summary info."""
        conversations = []
        for fp in self.conversations_dir.glob("*.json"):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    conv = json.load(f)
                messages = conv.get("messages", [])
                # Get first user message as preview
                preview = ""
                for msg in messages:
                    if msg.get("role") == "user":
                        preview = msg["content"][:120]
                        break
                conversations.append({
                    "conversation_id": conv["conversation_id"],
                    "created_at": conv["created_at"],
                    "updated_at": conv["updated_at"],
                    "message_count": len(messages),
                    "preview": preview,
                })
            except Exception as e:
                logger.error(f"Failed to read {fp.name}: {e}")

        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        return conversations[:limit]

    def delete_conversation(self, conversation_id: str) -> bool:
        file_path = self._get_file(conversation_id)
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted conversation: {conversation_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False
