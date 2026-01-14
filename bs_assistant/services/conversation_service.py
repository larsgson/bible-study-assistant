"""Conversation service for managing chat history."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from bs_assistant.config import settings
from bs_assistant.models import ChatMessage


class ConversationService:
    """Service for managing conversation history."""

    def __init__(self) -> None:
        """Initialize conversation service."""
        self.store_type = settings.CONVERSATION_STORE
        self.max_messages = settings.CONVERSATION_HISTORY_MAX_MESSAGES

        # In-memory storage
        self._memory_store: dict[str, list[dict[str, Any]]] = {}

        # File-based storage path
        self._file_path = settings.CONVERSATION_HISTORY_PATH
        if self.store_type == "tinydb":
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._load_from_file()

    def _load_from_file(self) -> None:
        """Load conversations from file if it exists."""
        if not self._file_path.exists():
            return

        try:
            with self._file_path.open("r", encoding="utf-8") as f:
                self._memory_store = json.load(f)
        except Exception:
            # Start fresh if file is corrupted
            self._memory_store = {}

    def _save_to_file(self) -> None:
        """Save conversations to file."""
        if self.store_type != "tinydb":
            return

        try:
            with self._file_path.open("w", encoding="utf-8") as f:
                json.dump(self._memory_store, f, indent=2)
        except Exception:
            # Silently fail if we can't save
            pass

    def _get_session_key(self, user_id: str, session_id: str | None = None) -> str:
        """
        Generate session key.

        Args:
            user_id: User identifier
            session_id: Optional session identifier

        Returns:
            Session key
        """
        if session_id:
            return f"{user_id}:{session_id}"
        return user_id

    def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        session_id: str | None = None,
    ) -> None:
        """
        Add a message to conversation history.

        Args:
            user_id: User identifier
            role: Message role (user, assistant, system)
            content: Message content
            session_id: Optional session identifier
        """
        session_key = self._get_session_key(user_id, session_id)

        if session_key not in self._memory_store:
            self._memory_store[session_key] = []

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._memory_store[session_key].append(message)

        # Truncate if exceeds max
        if len(self._memory_store[session_key]) > self.max_messages:
            # Keep system messages and last N messages
            messages = self._memory_store[session_key]
            system_messages = [m for m in messages if m["role"] == "system"]
            recent_messages = [m for m in messages if m["role"] != "system"][-self.max_messages :]
            self._memory_store[session_key] = system_messages + recent_messages

        # Save if using file storage
        if self.store_type == "tinydb":
            self._save_to_file()

    def get_history(
        self,
        user_id: str,
        session_id: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, str]]:
        """
        Get conversation history.

        Args:
            user_id: User identifier
            session_id: Optional session identifier
            limit: Optional limit on number of messages

        Returns:
            List of message dicts with role and content
        """
        session_key = self._get_session_key(user_id, session_id)

        if session_key not in self._memory_store:
            return []

        messages = self._memory_store[session_key]

        if limit:
            # Keep system messages and limit others
            system_messages = [m for m in messages if m["role"] == "system"]
            other_messages = [m for m in messages if m["role"] != "system"][-limit:]
            messages = system_messages + other_messages

        # Return only role and content (strip timestamp)
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    def clear_history(
        self,
        user_id: str,
        session_id: str | None = None,
    ) -> None:
        """
        Clear conversation history.

        Args:
            user_id: User identifier
            session_id: Optional session identifier
        """
        session_key = self._get_session_key(user_id, session_id)

        if session_key in self._memory_store:
            del self._memory_store[session_key]

        # Save if using file storage
        if self.store_type == "tinydb":
            self._save_to_file()

    def get_or_create_session_id(
        self,
        user_id: str,
        session_id: str | None = None,
    ) -> str:
        """
        Get existing session ID or create new one.

        Args:
            user_id: User identifier
            session_id: Optional session identifier

        Returns:
            Session identifier
        """
        if session_id:
            return session_id

        # Generate new session ID based on timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"session-{user_id}-{timestamp}"

    def list_sessions(self, user_id: str) -> list[str]:
        """
        List all sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            List of session IDs
        """
        sessions = []
        for key in self._memory_store.keys():
            if key.startswith(f"{user_id}:"):
                session_id = key.split(":", 1)[1]
                sessions.append(session_id)
            elif key == user_id:
                sessions.append("default")

        return sessions

    def get_session_summary(
        self,
        user_id: str,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Get summary of a session.

        Args:
            user_id: User identifier
            session_id: Optional session identifier

        Returns:
            Summary dict with message count, first/last timestamps
        """
        history = self.get_history(user_id, session_id)

        if not history:
            return {
                "message_count": 0,
                "first_timestamp": None,
                "last_timestamp": None,
            }

        session_key = self._get_session_key(user_id, session_id)
        full_messages = self._memory_store.get(session_key, [])

        return {
            "message_count": len(full_messages),
            "first_timestamp": full_messages[0].get("timestamp") if full_messages else None,
            "last_timestamp": full_messages[-1].get("timestamp") if full_messages else None,
        }


# Global instance
conversation_service = ConversationService()


__all__ = ["ConversationService", "conversation_service"]
