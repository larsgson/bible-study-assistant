"""Web messaging adapter for collecting responses without external API calls."""

from __future__ import annotations

from typing import Literal

from bt_servant_engine.core.logging import get_logger
from bt_servant_engine.core.ports import MessagingPort

logger = get_logger(__name__)


class MessageResponse:
    """A single response message collected during processing."""

    def __init__(
        self,
        content: str,
        message_type: Literal["text", "voice"] = "text",
    ) -> None:
        self.content = content
        self.message_type = message_type


class WebMessagingAdapter(MessagingPort):
    """Messaging adapter that collects responses in memory for web chat."""

    def __init__(self) -> None:
        self.responses: list[MessageResponse] = []
        self._typing_indicators: list[str] = []

    async def send_text_message(self, user_id: str, text: str) -> None:
        """Collect a text message response."""
        logger.info("Web chat collecting text response for user=%s", user_id)
        self.responses.append(MessageResponse(content=text, message_type="text"))

    async def send_voice_message(self, user_id: str, text: str) -> None:
        """Collect voice content as text (voice not supported in web chat)."""
        logger.info("Web chat collecting voice-as-text response for user=%s", user_id)
        self.responses.append(MessageResponse(content=text, message_type="text"))

    async def send_typing_indicator(self, message_id: str) -> None:
        """Record typing indicator (no-op for web, but tracked for debugging)."""
        logger.debug("Web chat typing indicator for message_id=%s", message_id)
        self._typing_indicators.append(message_id)

    async def transcribe_voice_message(self, media_id: str) -> str:
        """Voice transcription not supported in web chat."""
        raise NotImplementedError("Voice message transcription not supported in web chat")

    def get_responses(self) -> list[MessageResponse]:
        """Return all collected responses."""
        return self.responses

    def clear_responses(self) -> None:
        """Clear collected responses."""
        self.responses.clear()
        self._typing_indicators.clear()


__all__ = ["WebMessagingAdapter", "MessageResponse"]
