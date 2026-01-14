"""Test script to verify the new bs_assistant system."""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from bs_assistant.config import settings

        print("✓ Config imported")

        from bs_assistant.models import ChatRequest, ChatResponse

        print("✓ Models imported")

        from bs_assistant.core.detectors import extract_bible_reference

        print("✓ Detectors imported")

        from bs_assistant.core.llm import build_chat_messages, llm_client

        print("✓ LLM client imported")

        from bs_assistant.core.rag import retriever, vector_store

        print("✓ RAG components imported")

        from bs_assistant.services import bible_service, chat_service, conversation_service

        print("✓ Services imported")

        print("\n✅ All imports successful!\n")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}\n")
        return False


def test_bible_reference_detection():
    """Test Bible reference detection."""
    print("Testing Bible reference detection...")

    from bs_assistant.core.detectors import extract_bible_reference

    test_cases = [
        ("Show me John 3:16", "John 3:16"),
        ("What does Romans 8:28 say?", "Romans 8:28"),
        ("Explain Genesis 1:1-3", "Genesis 1:1-3"),
        ("Tell me about Psalm 23", "Psalms 23"),
    ]

    for text, expected in test_cases:
        ref = extract_bible_reference(text)
        if ref:
            print(f"✓ '{text}' -> {ref}")
        else:
            print(f"✗ '{text}' -> None (expected {expected})")

    print()


def test_special_intent_detection():
    """Test special intent detection."""
    print("Testing special intent detection...")

    from bs_assistant.core.detectors import detect_settings_request, detect_tts_request

    # Test TTS
    tts_tests = [
        ("Read Romans 8 to me", True),
        ("Play John 3:16", True),
        ("What does it mean?", False),
    ]

    for text, should_detect in tts_tests:
        result = detect_tts_request(text)
        status = "✓" if result.detected == should_detect else "✗"
        print(f"{status} TTS: '{text}' -> {result.detected}")

    # Test Settings
    settings_tests = [
        ("Change language to Spanish", True),
        ("Use ESV translation", True),
        ("What is grace?", False),
    ]

    for text, should_detect in settings_tests:
        result = detect_settings_request(text)
        status = "✓" if result.detected == should_detect else "✗"
        print(f"{status} Settings: '{text}' -> {result.detected}")

    print()


def test_configuration():
    """Test configuration loading."""
    print("Testing configuration...")

    from bs_assistant.config import settings

    print(f"✓ Default model: {settings.DEFAULT_MODEL}")
    print(f"✓ Simple query model: {settings.SIMPLE_QUERY_MODEL}")
    print(f"✓ Temperature: {settings.TEMPERATURE}")
    print(f"✓ Max tokens: {settings.MAX_TOKENS}")
    print(f"✓ Vector store path: {settings.VECTOR_STORE_PATH}")
    print(f"✓ Max retrieval results: {settings.MAX_RETRIEVAL_RESULTS}")
    print()


def test_models():
    """Test Pydantic models."""
    print("Testing Pydantic models...")

    from bs_assistant.models import ChatRequest, ChatResponse, RetrievedResource

    # Test ChatRequest
    request = ChatRequest(
        message="What does John 3:16 mean?",
        user_id="test_user",
        language="en",
    )
    print(f"✓ ChatRequest created: {request.message[:30]}...")

    # Test RetrievedResource
    resource = RetrievedResource(
        type="verse",
        content="For God so loved the world...",
        reference="John 3:16",
        score=1.0,
    )
    print(f"✓ RetrievedResource created: {resource.reference}")

    # Test ChatResponse
    response = ChatResponse(
        response="John 3:16 is often called...",
        session_id="session-123",
        retrieved_resources=[resource],
    )
    print(f"✓ ChatResponse created with {len(response.retrieved_resources)} resources")
    print()


def test_conversation_service():
    """Test conversation service."""
    print("Testing conversation service...")

    from bs_assistant.services import conversation_service

    user_id = "test_user_123"

    # Add messages
    conversation_service.add_message(user_id, "user", "Hello")
    conversation_service.add_message(user_id, "assistant", "Hi there!")

    # Get history
    history = conversation_service.get_history(user_id)
    print(f"✓ Added 2 messages, retrieved {len(history)} messages")

    # Clear history
    conversation_service.clear_history(user_id)
    history_after = conversation_service.get_history(user_id)
    print(f"✓ Cleared history, now has {len(history_after)} messages")
    print()


def test_bible_service():
    """Test Bible service."""
    print("Testing Bible service...")

    from bs_assistant.core.detectors import BibleReference
    from bs_assistant.services import bible_service

    # Check available languages
    languages = bible_service.list_available_languages()
    print(f"✓ Found {len(languages)} available languages: {languages}")

    # Check available translations
    if languages:
        translations = bible_service.list_available_translations(languages[0])
        print(f"✓ Found {len(translations)} translations for '{languages[0]}': {translations}")

    print()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Bible Study Assistant v2.0 - System Test")
    print("=" * 60)
    print()

    # Run tests
    if not test_imports():
        print("❌ Import test failed. Please install dependencies:")
        print("   pip install -e .")
        return

    test_configuration()
    test_models()
    test_bible_reference_detection()
    test_special_intent_detection()
    test_conversation_service()
    test_bible_service()

    print("=" * 60)
    print("✅ All basic tests passed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Install dependencies: pip install -e .")
    print("2. Set up .env file with your OpenAI API key")
    print("3. Add Bible data to sources/bible_data/")
    print("4. Run the server: python bs_assistant/main.py")
    print()


if __name__ == "__main__":
    main()
