"""LLM client and prompt management."""

from bs_assistant.core.llm.client import LLMClient, llm_client
from bs_assistant.core.llm.prompts import (
    CONVERSATION_SUMMARY_PROMPT,
    CROSS_REFERENCE_PROMPT,
    KEYWORD_EXTRACTION_PROMPT,
    RAG_CONTEXT_TEMPLATE,
    SIMPLE_QUERY_PROMPT,
    SUMMARY_PROMPT,
    SYSTEM_PROMPT,
    TRANSLATION_HELP_PROMPT,
    build_chat_messages,
    format_resources,
)

__all__ = [
    "LLMClient",
    "llm_client",
    "SYSTEM_PROMPT",
    "RAG_CONTEXT_TEMPLATE",
    "SIMPLE_QUERY_PROMPT",
    "SUMMARY_PROMPT",
    "KEYWORD_EXTRACTION_PROMPT",
    "TRANSLATION_HELP_PROMPT",
    "CROSS_REFERENCE_PROMPT",
    "CONVERSATION_SUMMARY_PROMPT",
    "format_resources",
    "build_chat_messages",
]
