"""Detectors for Bible references and special intents."""

from bs_assistant.core.detectors.bible_ref import (
    BibleReference,
    BibleReferenceDetector,
    extract_bible_reference,
    extract_bible_references,
)
from bs_assistant.core.detectors.special_intents import (
    SettingsRequest,
    SpecialIntentDetector,
    TTSRequest,
    detect_settings_request,
    detect_tts_request,
)

__all__ = [
    "BibleReference",
    "BibleReferenceDetector",
    "extract_bible_reference",
    "extract_bible_references",
    "TTSRequest",
    "SettingsRequest",
    "SpecialIntentDetector",
    "detect_tts_request",
    "detect_settings_request",
]
