"""Shared message processing logic for web chat and other interfaces."""

from __future__ import annotations

import asyncio
import time
from contextvars import copy_context
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Awaitable, Callable, Optional, cast

import httpx

from bt_servant_engine.apps.api.state import get_brain, set_brain
from bt_servant_engine.core.config import config
from bt_servant_engine.core.logging import (
    bind_client_ip,
    bind_correlation_id,
    bind_log_user_id,
    get_logger,
    reset_client_ip,
    reset_correlation_id,
    reset_log_user_id,
)
from bt_servant_engine.core.models import UserMessage
from bt_servant_engine.core.ports import MessagingPort, UserStatePort
from bt_servant_engine.services import ServiceContainer, status_messages
from bt_servant_engine.services.brain_orchestrator import create_brain
from utils.identifiers import get_log_safe_user_id
from utils.perf import set_current_trace, time_block

logger = get_logger(__name__)

user_locks: dict[str, asyncio.Lock] = {}


def _get_user_lock(user_id: str) -> asyncio.Lock:
    """Get or create a lock for a specific user."""
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    return user_locks[user_id]


def _require_messaging(services: ServiceContainer) -> MessagingPort:
    """Extract messaging port from services or raise error."""
    if services.messaging is None:
        raise RuntimeError("MessagingPort is required but not provided in services")
    return services.messaging


def _require_user_state(services: ServiceContainer) -> UserStatePort:
    """Extract user state port from services or raise error."""
    if services.user_state is None:
        raise RuntimeError("UserStatePort is required but not provided in services")
    return services.user_state


def _compute_agentic_strengths(
    user_id: str,
    user_state: UserStatePort,
) -> tuple[str, Optional[str]]:
    """Return effective agentic strength and stored user preference (if any)."""
    user_pref = user_state.get_agentic_strength(user_id=user_id)
    system_pref = str(getattr(config, "AGENTIC_STRENGTH", "low"))
    effective = user_pref if user_pref is not None else system_pref
    return effective, user_pref


def _compute_dev_agentic_mcp(
    user_id: str,
    user_state: UserStatePort,
) -> tuple[bool, Optional[bool]]:
    """Return effective dev MCP flag and stored user preference (if any)."""
    user_pref = user_state.get_dev_agentic_mcp(user_id=user_id)
    system_pref = bool(getattr(config, "BT_DEV_AGENTIC_MCP", False))
    effective = user_pref if user_pref is not None else system_pref
    return effective, user_pref


@dataclass(slots=True)
class _MessageProcessingContext:
    """Context for processing a single user message."""

    user_message: UserMessage
    messaging: MessagingPort
    user_state: UserStatePort
    log_user_id: str
    brain: Any
    start_time: float
    correlation_id: Optional[str]
    client_ip: Optional[str]


class _ProcessingGuard:
    """Async context manager to handle message processing cleanup and fallback."""

    def __init__(self, context: _MessageProcessingContext) -> None:
        self._context = context

    async def __aenter__(self) -> _MessageProcessingContext:
        return self._context

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        try:
            if exc is None:
                return False
            if isinstance(exc, asyncio.CancelledError):
                return False
            logger.error(
                "Unhandled error during process_message; sending fallback to user.",
                exc_info=True,
            )
            await _handle_processing_failure(self._context)
            return True
        finally:
            _finalize_processing(self._context)


async def process_message(
    user_message: UserMessage,
    services: ServiceContainer,
    *,
    correlation_id: str | None,
    client_ip: str | None,
) -> None:
    """Serialize user processing per user id and send responses back."""
    user_lock = _get_user_lock(user_message.user_id)
    async with user_lock:
        token_correlation = bind_correlation_id(correlation_id)
        token_client_ip = bind_client_ip(client_ip)
        set_current_trace(user_message.message_id)
        context = _create_processing_context(
            user_message,
            services,
            correlation_id=correlation_id,
            client_ip=client_ip,
        )
        token = bind_log_user_id(context.log_user_id)
        try:
            async with _ProcessingGuard(context):
                await _process_with_brain(context)
        finally:
            reset_log_user_id(token)
            reset_client_ip(token_client_ip)
            reset_correlation_id(token_correlation)


def _create_processing_context(
    user_message: UserMessage,
    services: ServiceContainer,
    *,
    correlation_id: str | None,
    client_ip: str | None,
) -> _MessageProcessingContext:
    messaging = _require_messaging(services)
    user_state = _require_user_state(services)
    log_user_id = get_log_safe_user_id(
        user_message.user_id,
        secret=config.LOG_PSEUDONYM_SECRET,
    )
    brain_instance = get_brain()
    if brain_instance is None:
        logger.warning("Brain not initialized at message time; initializing lazily.")
        brain_instance = create_brain()
        set_brain(brain_instance)
    if brain_instance is None:
        raise RuntimeError("Brain instance should be initialized before invocation")
    return _MessageProcessingContext(
        user_message=user_message,
        messaging=messaging,
        user_state=user_state,
        log_user_id=log_user_id,
        brain=brain_instance,
        start_time=time.time(),
        correlation_id=correlation_id,
        client_ip=client_ip,
    )


async def _process_with_brain(context: _MessageProcessingContext) -> None:
    async with time_block("bt_servant:process_message"):
        await _send_typing_indicator(context)
        progress_sender = _build_progress_sender(context)
        user_query = await _resolve_user_text(context, progress_sender)
        result = await _invoke_brain(context, user_query, progress_sender)
        full_response_text = await _deliver_responses(context, result, progress_sender)
        context.user_state.append_chat_history(
            context.user_message.user_id,
            context.user_message.text,
            full_response_text,
        )


async def _send_typing_indicator(context: _MessageProcessingContext) -> None:
    try:
        await context.messaging.send_typing_indicator(context.user_message.message_id)
    except httpx.HTTPError as exc:
        logger.warning("Failed to send typing indicator: %s", exc)
    except NotImplementedError:
        pass


def _build_progress_sender(
    context: _MessageProcessingContext,
) -> Callable[[status_messages.LocalizedProgressMessage], Awaitable[None]]:
    async def _send(message: status_messages.LocalizedProgressMessage) -> None:
        if not config.PROGRESS_MESSAGES_ENABLED:
            return
        try:
            text_msg = message.get("text", "")
            if not text_msg:
                logger.debug("Empty progress message text, skipping send")
                return
            await context.messaging.send_text_message(
                context.user_message.user_id,
                text_msg,
            )
        except httpx.HTTPError:
            logger.warning("Failed to send progress message", exc_info=True)

    return _send


async def _resolve_user_text(
    context: _MessageProcessingContext,
    progress_sender: Callable[[status_messages.LocalizedProgressMessage], Awaitable[None]],
) -> str:
    if context.user_message.message_type != "audio":
        return context.user_message.text
    minimal_state = {
        "user_response_language": context.user_state.get_response_language(
            user_id=context.user_message.user_id
        )
    }
    transcribe_msg = status_messages.get_progress_message(
        status_messages.TRANSCRIBING_VOICE,
        minimal_state,
    )
    await progress_sender(transcribe_msg)
    return await context.messaging.transcribe_voice_message(context.user_message.media_id)


async def _invoke_brain(
    context: _MessageProcessingContext,
    user_query: str,
    progress_sender: Callable[[status_messages.LocalizedProgressMessage], Awaitable[None]],
) -> dict[str, Any]:
    effective_agentic_strength, user_agentic_strength = _compute_agentic_strengths(
        context.user_message.user_id,
        context.user_state,
    )
    effective_dev_agentic_mcp, user_dev_agentic_mcp = _compute_dev_agentic_mcp(
        context.user_message.user_id,
        context.user_state,
    )
    brain_payload: dict[str, Any] = {
        "user_id": context.user_message.user_id,
        "user_query": user_query,
        "user_chat_history": context.user_state.get_chat_history(
            user_id=context.user_message.user_id
        ),
        "user_response_language": context.user_state.get_response_language(
            user_id=context.user_message.user_id
        ),
        "agentic_strength": effective_agentic_strength,
        "dev_agentic_mcp": effective_dev_agentic_mcp,
        "perf_trace_id": context.user_message.message_id,
        "progress_enabled": config.PROGRESS_MESSAGES_ENABLED,
        "progress_messenger": progress_sender,
        "progress_throttle_seconds": config.PROGRESS_MESSAGE_MIN_INTERVAL,
        "last_progress_time": 0,
    }
    if user_agentic_strength is not None:
        brain_payload["user_agentic_strength"] = user_agentic_strength
    if user_dev_agentic_mcp is not None:
        brain_payload["user_dev_agentic_mcp"] = user_dev_agentic_mcp
    loop = asyncio.get_event_loop()
    ctx = copy_context()

    def _invoke_sync() -> dict[str, Any]:
        return cast(dict[str, Any], ctx.run(context.brain.invoke, cast(Any, brain_payload)))

    return await loop.run_in_executor(None, _invoke_sync)


async def _deliver_responses(
    context: _MessageProcessingContext,
    result: dict[str, Any],
    progress_sender: Callable[[status_messages.LocalizedProgressMessage], Awaitable[None]],
) -> str:
    responses = list(result["translated_responses"])
    full_response_text = "\n\n".join(responses).rstrip()
    send_voice = bool(result.get("send_voice_message")) or (
        context.user_message.message_type == "audio"
    )
    voice_text = result.get("voice_message_text")
    if send_voice:
        if voice_text or full_response_text:
            await progress_sender(
                status_messages.get_progress_message(
                    status_messages.PACKAGING_VOICE_RESPONSE,
                    result,
                )
            )
        voice_payload = voice_text or full_response_text
        if voice_payload:
            try:
                await context.messaging.send_voice_message(
                    context.user_message.user_id,
                    voice_payload,
                )
            except NotImplementedError:
                logger.debug("Voice messages not supported by this adapter")
    should_send_text = True
    if send_voice and voice_text is None and context.user_message.message_type == "audio":
        should_send_text = False
    response_language: Optional[str] = None
    if should_send_text and responses:
        response_language = _resolve_response_language(result, context)
        previous_language = context.user_state.get_last_response_language(
            user_id=context.user_message.user_id
        )
        indicator = _partial_support_indicator(previous_language, response_language)
        for response in _format_indicator_responses(responses, indicator):
            logger.info("Response from bt_servant: %s", response)
            try:
                await context.messaging.send_text_message(
                    context.user_message.user_id,
                    response,
                )
            except httpx.HTTPError as exc:
                logger.error("Failed to send text message: %s", exc)
                raise
    if response_language:
        context.user_state.set_last_response_language(
            user_id=context.user_message.user_id,
            language=response_language,
        )
    return full_response_text


def _resolve_response_language(
    result: dict[str, Any],
    context: _MessageProcessingContext,
) -> str:
    response_language = result.get("response_language")
    if response_language:
        return str(response_language)
    return context.user_state.get_response_language(user_id=context.user_message.user_id) or "en"


def _partial_support_indicator(
    previous_language: Optional[str],
    response_language: Optional[str],
) -> str:
    if not response_language or response_language == "en":
        return ""
    if previous_language == response_language:
        return ""
    return f"\n\n_Response language: {response_language}_"


def _format_indicator_responses(
    responses: list[str],
    indicator: str,
) -> list[str]:
    if not indicator:
        return responses
    if not responses:
        return []
    output = list(responses)
    output[-1] = output[-1] + indicator
    return output


async def _handle_processing_failure(context: _MessageProcessingContext) -> None:
    try:
        fallback_state = {
            "user_response_language": context.user_state.get_response_language(
                user_id=context.user_message.user_id
            )
        }
        fallback_msg = status_messages.get_status_message(
            status_messages.PROCESSING_ERROR,
            fallback_state,
        )
        fallback_text = (
            fallback_msg
            if isinstance(fallback_msg, str)
            else fallback_msg.get("text", "An error occurred. Please try again.")
        )
        await context.messaging.send_text_message(
            context.user_message.user_id,
            fallback_text,
        )
    except Exception:
        logger.error("Failed to send fallback message", exc_info=True)


def _finalize_processing(context: _MessageProcessingContext) -> None:
    elapsed = time.time() - context.start_time
    logger.info(
        "Message processing completed for user=%s in %.2fs",
        context.log_user_id,
        elapsed,
    )


__all__ = ["process_message"]
