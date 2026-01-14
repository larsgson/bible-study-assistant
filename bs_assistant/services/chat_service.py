"""Main chat service orchestrating RAG retrieval and LLM response generation."""

from __future__ import annotations

from typing import Any

from bs_assistant.config import settings
from bs_assistant.core.detectors import (
    detect_settings_request,
    detect_tts_request,
    extract_bible_reference,
)
from bs_assistant.core.llm import build_chat_messages, llm_client
from bs_assistant.core.rag import retriever
from bs_assistant.models import ChatRequest, ChatResponse, RetrievedResource
from bs_assistant.services.conversation_service import conversation_service


class ChatService:
    """Main chat service orchestrating all components."""

    def __init__(self) -> None:
        """Initialize chat service."""
        self.retriever = retriever
        self.llm_client = llm_client
        self.conversation_service = conversation_service

    def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Process a user message and generate response.

        Args:
            request: Chat request with user message

        Returns:
            Chat response with generated text and metadata
        """
        # Get or create session ID
        session_id = self.conversation_service.get_or_create_session_id(
            request.user_id, request.session_id
        )

        # Step 1: Check for special intents (TTS, settings)
        special_response = self._handle_special_intents(request)
        if special_response:
            return ChatResponse(
                response=special_response,
                session_id=session_id,
                retrieved_resources=[],
            )

        # Step 2: Detect Bible references
        bible_ref = extract_bible_reference(request.message)

        # Step 3: Retrieve relevant resources via RAG
        retrieved_resources = self.retriever.retrieve(
            query=request.message,
            bible_ref=bible_ref,
            language=request.language,
            translation=request.translation_id or "bsb",
            max_results=settings.MAX_RETRIEVAL_RESULTS,
        )

        # Step 4: Get conversation history
        conversation_history = self.conversation_service.get_history(
            request.user_id,
            session_id,
            limit=settings.CONVERSATION_HISTORY_MAX_MESSAGES,
        )

        # Step 5: Build messages for LLM
        messages = build_chat_messages(
            user_message=request.message,
            retrieved_resources=self._format_resources_for_llm(retrieved_resources),
            conversation_history=conversation_history,
        )

        # Step 6: Determine if this is a simple query
        is_simple = self._is_simple_query(request.message, bible_ref, retrieved_resources)

        # Step 7: Select model based on complexity
        model = self.llm_client.select_model(is_simple=is_simple)

        # Step 8: Generate response with LLM
        response_text, input_tokens, output_tokens, cost = self.llm_client.chat_completion(
            messages=messages,
            model=model,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
        )

        # Step 9: Store conversation history
        self.conversation_service.add_message(
            user_id=request.user_id,
            role="user",
            content=request.message,
            session_id=session_id,
        )
        self.conversation_service.add_message(
            user_id=request.user_id,
            role="assistant",
            content=response_text,
            session_id=session_id,
        )

        # Step 10: Return response
        total_tokens = input_tokens + output_tokens
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            retrieved_resources=retrieved_resources,
            model_used=model,
            tokens_used=total_tokens,
            cost_usd=cost,
        )

    def _handle_special_intents(self, request: ChatRequest) -> str | None:
        """
        Handle special intents that need non-conversational handling.

        Args:
            request: Chat request

        Returns:
            Response text if special intent handled, None otherwise
        """
        # Check for TTS request
        tts_req = detect_tts_request(request.message)
        if tts_req.detected:
            # TODO: Implement TTS handler in Phase 5
            return (
                "Text-to-speech feature is not yet implemented. "
                "I can help you understand the passage through text instead."
            )

        # Check for settings request
        settings_req = detect_settings_request(request.message)
        if settings_req.detected:
            # TODO: Implement settings handler in Phase 5
            setting_type = settings_req.setting_type or "general"
            return (
                f"Settings management for {setting_type} is not yet implemented. "
                "Please continue asking your Bible questions!"
            )

        return None

    def _is_simple_query(
        self,
        message: str,
        bible_ref: Any,
        retrieved_resources: list[RetrievedResource],
    ) -> bool:
        """
        Determine if query is simple enough for cheaper model.

        Args:
            message: User message
            bible_ref: Detected Bible reference
            retrieved_resources: Retrieved resources

        Returns:
            True if query is simple
        """
        message_lower = message.lower()

        # Simple patterns
        simple_patterns = [
            "show me",
            "read",
            "what does",
            "what is",
            "tell me about",
        ]

        # If it's just asking for a verse, it's simple
        if bible_ref and any(pattern in message_lower for pattern in simple_patterns):
            return True

        # If very few resources retrieved and short message, it's simple
        if len(retrieved_resources) <= 3 and len(message.split()) < 15:
            return True

        # If asking for verse with no complex keywords, it's simple
        complex_keywords = [
            "explain",
            "why",
            "how",
            "compare",
            "analyze",
            "interpret",
            "mean",
            "significance",
            "context",
            "summarize",
            "relate",
        ]

        has_complex = any(keyword in message_lower for keyword in complex_keywords)

        # Simple if it has a reference and no complex keywords
        if bible_ref and not has_complex:
            return True

        return False

    def _format_resources_for_llm(self, resources: list[RetrievedResource]) -> list[dict[str, Any]]:
        """
        Format retrieved resources for LLM prompt.

        Args:
            resources: List of retrieved resources

        Returns:
            List of resource dicts for prompt formatting
        """
        formatted = []
        for resource in resources:
            formatted.append(
                {
                    "type": resource.type,
                    "content": resource.content,
                    "reference": resource.reference,
                    "score": resource.score,
                }
            )
        return formatted


# Global instance
chat_service = ChatService()


__all__ = ["ChatService", "chat_service"]
