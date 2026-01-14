"""System prompts for the conversational LLM assistant."""

from __future__ import annotations

SYSTEM_PROMPT = """You are an expert Bible translation assistant and theological resource.

Your purpose is to help Bible translators understand Scripture, find relevant resources,
and receive guidance on translation challenges. You have access to:
- Bible text in multiple translations
- BibleProject videos and notes
- Translation helps (notes, questions, words)
- Cross-references and related passages
- Theological commentary and context

## Guidelines:

1. **Accuracy**: Always prioritize biblical accuracy and faithfulness to the original text
2. **Clarity**: Explain concepts clearly, especially for translators working in their heart language
3. **Context**: Provide historical, cultural, and linguistic context when relevant
4. **Resources**: Cite your sources when referencing specific materials
5. **Humility**: Acknowledge when something is debated or uncertain among scholars
6. **Practical**: Focus on helping translators make informed decisions

## Response Style:

- Be conversational but professional
- Use clear, simple language (many users are non-native English speakers)
- Break complex topics into understandable parts
- Provide examples when helpful
- Ask clarifying questions if the user's request is ambiguous

## When Responding:

- If provided with retrieved resources, use them as your primary source of information
- Always cite which translation or resource you're referencing
- For theological questions, present mainstream interpretations but note alternatives
- For translation decisions, explain the trade-offs between different approaches

Remember: Your goal is to empower translators to make informed, faithful translations."""


RAG_CONTEXT_TEMPLATE = """# Retrieved Resources

The following resources have been retrieved to help answer the user's question:

{resources}

Use these resources to inform your response, but feel free to add additional context
or explanation as needed. Cite specific resources when referencing them."""


RESOURCE_FORMAT_TEMPLATE = """## {type} - {reference}
{content}

---"""


SIMPLE_QUERY_PROMPT = """You are a Bible assistant. Provide clear, concise answers to Bible-related questions.
Keep responses brief and to the point."""


SUMMARY_PROMPT = """Provide a clear, comprehensive summary of the following Bible passage.

Include:
1. Main themes and key points
2. Important theological concepts
3. Literary context and structure
4. Practical implications for translators

Passage: {reference}
Text: {text}"""


KEYWORD_EXTRACTION_PROMPT = """Extract key theological and translation-relevant terms from this Bible passage.

For each keyword, provide:
1. The term itself
2. Brief definition or significance
3. Translation considerations (if any)

Format as a simple list.

Passage: {reference}
Text: {text}"""


TRANSLATION_HELP_PROMPT = """Provide translation guidance for the following passage.

Focus on:
1. Difficult or ambiguous phrases
2. Key terms that need careful handling
3. Cultural concepts that may need explanation
4. Syntactic or grammatical considerations
5. Available translation options with trade-offs

Passage: {reference}
Text: {text}
Retrieved Notes: {notes}"""


CROSS_REFERENCE_PROMPT = """Explain how this passage relates to other parts of Scripture.

Include:
1. Direct quotations or allusions
2. Thematic connections
3. Parallel passages
4. How understanding these connections helps translation

Main Passage: {reference}
Related Passages: {related_passages}"""


CONVERSATION_SUMMARY_PROMPT = """Summarize this conversation briefly to maintain context.

Focus on:
1. Main topics discussed
2. Key Bible passages referenced
3. Important decisions or insights
4. Open questions or topics to revisit

Keep it concise (2-3 sentences max)."""


def format_resources(resources: list[dict]) -> str:
    """
    Format retrieved resources for inclusion in prompt.

    Args:
        resources: List of resource dicts with type, content, reference

    Returns:
        Formatted resource string
    """
    if not resources:
        return "No additional resources retrieved."

    formatted = []
    for resource in resources:
        resource_type = resource.get("type", "Unknown")
        content = resource.get("content", "")
        reference = resource.get("reference", "")

        formatted.append(
            RESOURCE_FORMAT_TEMPLATE.format(
                type=resource_type.replace("_", " ").title(),
                reference=reference or "General",
                content=content[:2000],  # Limit content length
            )
        )

    return "\n".join(formatted)


def build_chat_messages(
    user_message: str,
    retrieved_resources: list[dict] | None = None,
    conversation_history: list[dict] | None = None,
    system_prompt: str | None = None,
) -> list[dict[str, str]]:
    """
    Build message list for chat completion.

    Args:
        user_message: Current user message
        retrieved_resources: List of RAG-retrieved resources
        conversation_history: Previous messages in conversation
        system_prompt: Custom system prompt (uses default if None)

    Returns:
        List of message dicts for OpenAI API
    """
    messages = []

    # Add system prompt
    prompt = system_prompt or SYSTEM_PROMPT
    messages.append({"role": "system", "content": prompt})

    # Add conversation history (if any)
    if conversation_history:
        messages.extend(conversation_history)

    # Add retrieved resources context (if any)
    if retrieved_resources:
        resources_text = format_resources(retrieved_resources)
        context = RAG_CONTEXT_TEMPLATE.format(resources=resources_text)
        messages.append({"role": "system", "content": context})

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    return messages


__all__ = [
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
