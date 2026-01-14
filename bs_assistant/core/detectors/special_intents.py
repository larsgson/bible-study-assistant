"""Special intent detectors for non-conversational features."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


@dataclass
class TTSRequest:
    """Text-to-speech request detection result."""

    detected: bool
    reference: str | None = None
    language: str | None = None


@dataclass
class SettingsRequest:
    """Settings change request detection result."""

    detected: bool
    setting_type: Literal["language", "translation", "voice", "other"] | None = None
    setting_value: str | None = None


class SpecialIntentDetector:
    """Detects special intents that need non-conversational handling."""

    def __init__(self) -> None:
        """Initialize detector with patterns."""
        # TTS patterns
        self.tts_patterns = [
            re.compile(
                r"\b(?:read|speak|say|audio|listen|hear)\b.*\b(?:to me|aloud|out loud)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(?:play|read)\s+(?:me\s+)?(?:the\s+)?(?:passage|verse|chapter|scripture)\b",
                re.IGNORECASE,
            ),
            re.compile(r"\bwhat\s+does\s+(?:it|that|this)\s+sound\s+like\b", re.IGNORECASE),
            re.compile(r"\b(?:audio|voice|tts|text.to.speech)\b", re.IGNORECASE),
        ]

        # Settings patterns
        self.settings_patterns = {
            "language": [
                re.compile(
                    r"\b(?:change|switch|set|use)\s+(?:the\s+)?language\s+to\s+(\w+)", re.IGNORECASE
                ),
                re.compile(r"\bspeak\s+(?:in\s+)?(\w+)\b", re.IGNORECASE),
                re.compile(
                    r"\b(?:translate|show)\s+(?:everything\s+)?(?:in|to)\s+(\w+)", re.IGNORECASE
                ),
            ],
            "translation": [
                re.compile(
                    r"\b(?:change|switch|set|use)\s+(?:the\s+)?(?:bible\s+)?translation\s+to\s+([\w\-]+)",
                    re.IGNORECASE,
                ),
                re.compile(
                    r"\buse\s+(?:the\s+)?(ESV|NIV|KJV|NASB|NLT|NKJV|[\w\-]+)\s+(?:translation|version|bible)",
                    re.IGNORECASE,
                ),
            ],
            "voice": [
                re.compile(
                    r"\b(?:change|switch|set|use)\s+(?:the\s+)?voice\s+to\s+(\w+)", re.IGNORECASE
                ),
                re.compile(r"\buse\s+(?:a\s+)?(male|female|[\w]+)\s+voice\b", re.IGNORECASE),
            ],
        }

    def detect_tts(self, text: str) -> TTSRequest:
        """
        Detect if text is requesting text-to-speech.

        Args:
            text: User message text

        Returns:
            TTSRequest with detection result
        """
        for pattern in self.tts_patterns:
            if pattern.search(text):
                return TTSRequest(detected=True)

        return TTSRequest(detected=False)

    def detect_settings(self, text: str) -> SettingsRequest:
        """
        Detect if text is requesting settings change.

        Args:
            text: User message text

        Returns:
            SettingsRequest with detection result
        """
        # Check each setting type
        for setting_type, patterns in self.settings_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    # Extract the setting value from the first capture group
                    value = match.group(1) if match.groups() else None
                    return SettingsRequest(
                        detected=True,
                        setting_type=setting_type,  # type: ignore[arg-type]
                        setting_value=value,
                    )

        # Generic settings keywords without specific patterns
        settings_keywords = [
            "settings",
            "preferences",
            "configuration",
            "options",
            "configure",
            "setup",
            "customize",
        ]

        text_lower = text.lower()
        if any(keyword in text_lower for keyword in settings_keywords):
            return SettingsRequest(detected=True, setting_type="other")

        return SettingsRequest(detected=False)

    def has_special_intent(self, text: str) -> bool:
        """
        Check if text has any special intent.

        Args:
            text: User message text

        Returns:
            True if any special intent detected
        """
        return self.detect_tts(text).detected or self.detect_settings(text).detected


# Global instance
detector = SpecialIntentDetector()


def detect_tts_request(text: str) -> TTSRequest:
    """
    Convenience function to detect TTS requests.

    Args:
        text: User message text

    Returns:
        TTSRequest with detection result
    """
    return detector.detect_tts(text)


def detect_settings_request(text: str) -> SettingsRequest:
    """
    Convenience function to detect settings requests.

    Args:
        text: User message text

    Returns:
        SettingsRequest with detection result
    """
    return detector.detect_settings(text)


__all__ = [
    "TTSRequest",
    "SettingsRequest",
    "SpecialIntentDetector",
    "detect_tts_request",
    "detect_settings_request",
]
