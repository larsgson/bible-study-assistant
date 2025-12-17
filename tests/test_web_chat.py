"""Unit tests for web chat adapter and endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bt_servant_engine.adapters.web_messaging import MessageResponse, WebMessagingAdapter
from bt_servant_engine.apps.api.routes.chat import ChatRequest, ChatResponse
from bt_servant_engine.core.models import UserMessage
from bt_servant_engine.services import ServiceContainer


class TestWebMessagingAdapter:
    """Test the web messaging adapter collects responses correctly."""

    @pytest.fixture
    def adapter(self) -> WebMessagingAdapter:
        """Create a fresh web messaging adapter."""
        return WebMessagingAdapter()

    async def test_send_text_message_collects_response(self, adapter: WebMessagingAdapter) -> None:
        """Test that text messages are collected."""
        await adapter.send_text_message("user123", "Hello world")

        responses = adapter.get_responses()
        assert len(responses) == 1
        assert responses[0].content == "Hello world"
        assert responses[0].message_type == "text"

    async def test_send_voice_message_converts_to_text(self, adapter: WebMessagingAdapter) -> None:
        """Test that voice messages are collected as text."""
        await adapter.send_voice_message("user123", "Voice content")

        responses = adapter.get_responses()
        assert len(responses) == 1
        assert responses[0].content == "Voice content"
        assert responses[0].message_type == "text"

    async def test_multiple_responses_collected(self, adapter: WebMessagingAdapter) -> None:
        """Test that multiple messages are collected in order."""
        await adapter.send_text_message("user123", "First message")
        await adapter.send_text_message("user123", "Second message")
        await adapter.send_voice_message("user123", "Third message")

        responses = adapter.get_responses()
        assert len(responses) == 3
        assert responses[0].content == "First message"
        assert responses[1].content == "Second message"
        assert responses[2].content == "Third message"

    async def test_send_typing_indicator_no_op(self, adapter: WebMessagingAdapter) -> None:
        """Test that typing indicators don't create responses."""
        await adapter.send_typing_indicator("msg123")

        responses = adapter.get_responses()
        assert len(responses) == 0

    async def test_transcribe_voice_not_supported(self, adapter: WebMessagingAdapter) -> None:
        """Test that voice transcription raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="not supported in web chat"):
            await adapter.transcribe_voice_message("media123")

    def test_clear_responses(self, adapter: WebMessagingAdapter) -> None:
        """Test that clear_responses removes all collected data."""
        adapter.responses.append(MessageResponse("test", "text"))
        adapter._typing_indicators.append("msg123")

        adapter.clear_responses()

        assert len(adapter.get_responses()) == 0
        assert len(adapter._typing_indicators) == 0


class TestChatEndpoint:
    """Test the web chat API endpoint."""

    @pytest.fixture
    def mock_services(self) -> ServiceContainer:
        """Create mock service container."""
        return ServiceContainer(
            chroma=MagicMock(),
            user_state=MagicMock(),
            messaging=MagicMock(),
            intent_router=MagicMock(),
        )

    @pytest.fixture
    def chat_request(self) -> ChatRequest:
        """Create a sample chat request."""
        return ChatRequest(
            message="What does Genesis 1:1 say?",
            user_id="test-user-123",
            session_id="session-abc",
        )

    async def test_chat_request_model_validation(self) -> None:
        """Test that chat request validates required fields."""
        request = ChatRequest(message="Hello")
        assert request.message == "Hello"
        assert request.user_id is not None
        assert request.session_id is None

    async def test_chat_request_empty_message_fails(self) -> None:
        """Test that empty messages are rejected."""
        with pytest.raises(Exception):
            ChatRequest(message="")

    async def test_chat_response_structure(self) -> None:
        """Test chat response model structure."""
        from bt_servant_engine.apps.api.routes.chat import ChatMessageResponse

        response = ChatResponse(
            user_id="user123",
            message_id="msg456",
            responses=[ChatMessageResponse(content="Response text", type="text")],
            processing_time_seconds=1.5,
            session_id="session789",
        )

        assert response.user_id == "user123"
        assert response.message_id == "msg456"
        assert len(response.responses) == 1
        assert response.responses[0].content == "Response text"
        assert response.processing_time_seconds == 1.5
        assert response.session_id == "session789"

    @patch("bt_servant_engine.apps.api.routes.chat.process_message")
    async def test_chat_endpoint_processes_message(
        self,
        mock_process: AsyncMock,
        chat_request: ChatRequest,
        mock_services: ServiceContainer,
    ) -> None:
        """Test that chat endpoint calls process_message."""
        from bt_servant_engine.apps.api.routes.chat import chat_endpoint

        mock_process.return_value = None

        with patch(
            "bt_servant_engine.apps.api.routes.chat.WebMessagingAdapter"
        ) as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter.get_responses.return_value = [
                MessageResponse(content="Test response", message_type="text")
            ]
            mock_adapter_class.return_value = mock_adapter

            response = await chat_endpoint(chat_request, mock_services)

            assert response.user_id == chat_request.user_id
            assert response.session_id == chat_request.session_id
            assert len(response.responses) == 1
            assert response.responses[0].content == "Test response"
            assert response.processing_time_seconds > 0

            mock_process.assert_called_once()
            call_args = mock_process.call_args
            user_message = call_args[0][0]
            assert isinstance(user_message, UserMessage)
            assert user_message.text == chat_request.message
            assert user_message.user_id == chat_request.user_id

    @patch("bt_servant_engine.apps.api.routes.chat.process_message")
    async def test_chat_endpoint_handles_errors(
        self,
        mock_process: AsyncMock,
        chat_request: ChatRequest,
        mock_services: ServiceContainer,
    ) -> None:
        """Test that chat endpoint handles processing errors."""
        from fastapi import HTTPException

        from bt_servant_engine.apps.api.routes.chat import chat_endpoint

        mock_process.side_effect = RuntimeError("Processing failed")

        with pytest.raises(HTTPException) as exc_info:
            await chat_endpoint(chat_request, mock_services)

        assert exc_info.value.status_code == 500
        assert "Failed to process chat message" in exc_info.value.detail


class TestMessageResponse:
    """Test MessageResponse model."""

    def test_message_response_creation(self) -> None:
        """Test creating a message response."""
        msg = MessageResponse(content="Hello", message_type="text")
        assert msg.content == "Hello"
        assert msg.message_type == "text"

    def test_message_response_defaults(self) -> None:
        """Test message response default values."""
        msg = MessageResponse(content="Test")
        assert msg.message_type == "text"
