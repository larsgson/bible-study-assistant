"""Example usage of the Bible Study Assistant web chat API.

This demonstrates how to interact with the /api/chat endpoint
to send messages and receive responses from the RAG-powered assistant.
"""

import asyncio
import json
from typing import Any

import httpx


async def send_chat_message(
    message: str,
    user_id: str = "example-user-123",
    session_id: str | None = None,
    base_url: str = "http://localhost:8000",
) -> dict[str, Any]:
    """Send a message to the web chat API and return the response.

    Args:
        message: The user's question or message
        user_id: Unique identifier for the user (persists state/preferences)
        session_id: Optional session identifier for grouping conversations
        base_url: Base URL of the API server

    Returns:
        Dictionary containing the assistant's responses and metadata
    """
    url = f"{base_url}/api/chat/"
    payload = {
        "message": message,
        "user_id": user_id,
        "session_id": session_id,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


async def main() -> None:
    """Run example chat interactions."""
    user_id = "demo-user-001"
    session_id = "demo-session-alpha"

    print("=" * 70)
    print("Bible Study Assistant - Web Chat API Demo")
    print("=" * 70)
    print()

    # Example 1: Scripture retrieval
    print("Example 1: Retrieving Scripture")
    print("-" * 70)
    message1 = "Show me Genesis 1:1-3"
    print(f"User: {message1}")
    print()

    try:
        result1 = await send_chat_message(message1, user_id, session_id)
        print(f"Message ID: {result1['message_id']}")
        print(f"Processing Time: {result1['processing_time_seconds']:.2f}s")
        print()
        print("Assistant Response(s):")
        for i, resp in enumerate(result1["responses"], 1):
            print(f"\n[Response {i}]")
            print(resp["content"])
        print("\n" + "=" * 70 + "\n")
    except httpx.HTTPError as e:
        print(f"Error: {e}")
        print("\n" + "=" * 70 + "\n")

    # Example 2: Translation help
    print("Example 2: Translation Assistance")
    print("-" * 70)
    message2 = "What are the key terms in John 3:16?"
    print(f"User: {message2}")
    print()

    try:
        result2 = await send_chat_message(message2, user_id, session_id)
        print(f"Message ID: {result2['message_id']}")
        print(f"Processing Time: {result2['processing_time_seconds']:.2f}s")
        print()
        print("Assistant Response(s):")
        for i, resp in enumerate(result2["responses"], 1):
            print(f"\n[Response {i}]")
            print(resp["content"])
        print("\n" + "=" * 70 + "\n")
    except httpx.HTTPError as e:
        print(f"Error: {e}")
        print("\n" + "=" * 70 + "\n")

    # Example 3: RAG consultation
    print("Example 3: Consulting Translation Resources")
    print("-" * 70)
    message3 = "What resources are available about covenant in the Old Testament?"
    print(f"User: {message3}")
    print()

    try:
        result3 = await send_chat_message(message3, user_id, session_id)
        print(f"Message ID: {result3['message_id']}")
        print(f"Processing Time: {result3['processing_time_seconds']:.2f}s")
        print()
        print("Assistant Response(s):")
        for i, resp in enumerate(result3["responses"], 1):
            print(f"\n[Response {i}]")
            print(resp["content"])
        print("\n" + "=" * 70 + "\n")
    except httpx.HTTPError as e:
        print(f"Error: {e}")
        print("\n" + "=" * 70 + "\n")


async def interactive_chat() -> None:
    """Run an interactive chat session."""
    user_id = "interactive-user"
    session_id = "interactive-session"

    print("=" * 70)
    print("Interactive Bible Study Assistant")
    print("=" * 70)
    print("Type your questions below. Type 'quit' or 'exit' to end.")
    print()

    while True:
        try:
            message = input("You: ").strip()
            if not message:
                continue
            if message.lower() in ("quit", "exit"):
                print("\nGoodbye!")
                break

            print("\nProcessing...\n")
            result = await send_chat_message(message, user_id, session_id)

            print("Assistant:")
            for resp in result["responses"]:
                print(resp["content"])
            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    import sys

    print("\nStarting Bible Study Assistant Web Chat Demo...")
    print("Make sure the API server is running on http://localhost:8000\n")

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_chat())
    else:
        asyncio.run(main())
        print("\nTo run in interactive mode: python web_chat_usage.py interactive\n")
