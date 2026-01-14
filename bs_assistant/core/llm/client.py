"""OpenAI LLM client with cost tracking and token management."""

from __future__ import annotations

import json
from typing import Any

import tiktoken
from openai import AsyncOpenAI, OpenAI

from bs_assistant.config import settings


class LLMClient:
    """OpenAI client with cost tracking and model selection."""

    def __init__(self) -> None:
        """Initialize the LLM client."""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.async_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.pricing = json.loads(settings.OPENAI_PRICING_JSON)
        self._tokenizers: dict[str, Any] = {}

    def _get_tokenizer(self, model: str) -> Any:
        """Get or create tokenizer for model."""
        if model not in self._tokenizers:
            try:
                # Try to get model-specific encoding
                self._tokenizers[model] = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to cl100k_base (used by gpt-4, gpt-3.5-turbo)
                self._tokenizers[model] = tiktoken.get_encoding("cl100k_base")
        return self._tokenizers[model]

    def count_tokens(self, text: str, model: str = "gpt-4o") -> int:
        """
        Count tokens in text for given model.

        Args:
            text: Text to count tokens for
            model: Model name for tokenization

        Returns:
            Number of tokens
        """
        tokenizer = self._get_tokenizer(model)
        return len(tokenizer.encode(text))

    def count_message_tokens(self, messages: list[dict[str, str]], model: str = "gpt-4o") -> int:
        """
        Count tokens in message list.

        Args:
            messages: List of message dicts with role and content
            model: Model name for tokenization

        Returns:
            Number of tokens
        """
        tokenizer = self._get_tokenizer(model)
        num_tokens = 0

        # Every message follows <im_start>{role/name}\n{content}<im_end>\n
        for message in messages:
            num_tokens += 4  # Every message has 4 tokens overhead
            for value in message.values():
                num_tokens += len(tokenizer.encode(str(value)))

        num_tokens += 2  # Every reply is primed with <im_start>assistant

        return num_tokens

    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str = "gpt-4o") -> float:
        """
        Calculate cost in USD for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name

        Returns:
            Cost in USD
        """
        if model not in self.pricing:
            return 0.0

        price_info = self.pricing[model]
        input_cost = (input_tokens / 1_000_000) * price_info["input_per_million"]
        output_cost = (output_tokens / 1_000_000) * price_info["output_per_million"]

        return input_cost + output_cost

    def select_model(self, is_simple: bool = False) -> str:
        """
        Select appropriate model based on query complexity.

        Args:
            is_simple: Whether this is a simple query

        Returns:
            Model name to use
        """
        if is_simple:
            return settings.SIMPLE_QUERY_MODEL
        return settings.DEFAULT_MODEL

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> tuple[str, int, int, float]:
        """
        Create chat completion with cost tracking.

        Args:
            messages: List of message dicts
            model: Model to use (defaults to DEFAULT_MODEL)
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            **kwargs: Additional OpenAI API parameters

        Returns:
            Tuple of (response_text, input_tokens, output_tokens, cost_usd)
        """
        model = model or settings.DEFAULT_MODEL
        temperature = temperature if temperature is not None else settings.TEMPERATURE
        max_tokens = max_tokens or settings.MAX_TOKENS

        # Count input tokens
        input_tokens = self.count_message_tokens(messages, model)

        # Make API call
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Extract response
        response_text = response.choices[0].message.content or ""

        # Get token usage from response
        usage = response.usage
        if usage:
            actual_input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
        else:
            actual_input_tokens = input_tokens
            output_tokens = self.count_tokens(response_text, model)

        # Calculate cost
        cost = self.calculate_cost(actual_input_tokens, output_tokens, model)

        return response_text, actual_input_tokens, output_tokens, cost

    async def achat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> tuple[str, int, int, float]:
        """
        Async version of chat_completion.

        Args:
            messages: List of message dicts
            model: Model to use (defaults to DEFAULT_MODEL)
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            **kwargs: Additional OpenAI API parameters

        Returns:
            Tuple of (response_text, input_tokens, output_tokens, cost_usd)
        """
        model = model or settings.DEFAULT_MODEL
        temperature = temperature if temperature is not None else settings.TEMPERATURE
        max_tokens = max_tokens or settings.MAX_TOKENS

        # Count input tokens
        input_tokens = self.count_message_tokens(messages, model)

        # Make API call
        response = await self.async_client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Extract response
        response_text = response.choices[0].message.content or ""

        # Get token usage from response
        usage = response.usage
        if usage:
            actual_input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
        else:
            actual_input_tokens = input_tokens
            output_tokens = self.count_tokens(response_text, model)

        # Calculate cost
        cost = self.calculate_cost(actual_input_tokens, output_tokens, model)

        return response_text, actual_input_tokens, output_tokens, cost


# Global instance
llm_client = LLMClient()


__all__ = ["LLMClient", "llm_client"]
