from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


class UnsupportedLanguageError(ValueError):
    """Raised when an unrecognized or unsupported programming language is requested."""

    def __init__(self, language: str):
        super().__init__(
            f"Unsupported programming language '{language}'. "
            "Supported languages are: python, cpp, javascript, java."
        )
        self.language = language


@dataclass(frozen=True)
class LanguageConfig:
    id: str
    display_name: str
    extension: str
    filename: str
    is_compiled: bool
    docker_image: str
    comment_prefix: str


class LanguageRegistry:
    """Canonical registry and routing for programming languages in DevLens."""

    _CANONICAL_LANGUAGES: ClassVar[dict[str, LanguageConfig]] = {
        "python": LanguageConfig(
            id="python",
            display_name="Python",
            extension=".py",
            filename="main.py",
            is_compiled=False,
            docker_image="python:3.12-alpine",
            comment_prefix="#",
        ),
        "cpp": LanguageConfig(
            id="cpp",
            display_name="C++",
            extension=".cpp",
            filename="main.cpp",
            is_compiled=True,
            docker_image="gcc:14.2.0",
            comment_prefix="//",
        ),
        "javascript": LanguageConfig(
            id="javascript",
            display_name="JavaScript",
            extension=".js",
            filename="main.js",
            is_compiled=False,
            docker_image="node:20-alpine",
            comment_prefix="//",
        ),
        "java": LanguageConfig(
            id="java",
            display_name="Java",
            extension=".java",
            filename="Main.java",
            is_compiled=True,
            docker_image="eclipse-temurin:21-alpine",
            comment_prefix="//",
        ),
    }

    _ALIASES: ClassVar[dict[str, str]] = {
        "python": "python",
        "python3": "python",
        "py": "python",
        "cpp": "cpp",
        "c++": "cpp",
        "cplusplus": "cpp",
        "c": "cpp",
        "javascript": "javascript",
        "js": "javascript",
        "node": "javascript",
        "nodejs": "javascript",
        "java": "java",
    }

    @classmethod
    def normalize(cls, language: str) -> str:
        """Normalizes any accepted alias to its canonical language ID.

        Raises UnsupportedLanguageError if not recognized.
        Never silently falls back to a default language like Python.
        """
        if not language or not isinstance(language, str):
            raise UnsupportedLanguageError(str(language))

        cleaned = language.strip().lower()
        if cleaned in cls._ALIASES:
            return cls._ALIASES[cleaned]

        raise UnsupportedLanguageError(language)

    @classmethod
    def is_supported(cls, language: str) -> bool:
        if not language or not isinstance(language, str):
            return False
        return language.strip().lower() in cls._ALIASES

    @classmethod
    def get(cls, language: str) -> LanguageConfig:
        """Returns the canonical LanguageConfig for the specified language or alias."""
        canonical_id = cls.normalize(language)
        return cls._CANONICAL_LANGUAGES[canonical_id]

    @classmethod
    def supported_languages(cls) -> list[str]:
        return list(cls._CANONICAL_LANGUAGES.keys())

    @classmethod
    def resolve_language(
        cls,
        *,
        explicit_language: str | None = None,
        confirmed_language: str | None = None,
        detected_language: str | None = None,
    ) -> str:
        """Enforces language priority order:

        1. Explicit user selection (never guessed after user selects it)
        2. User-confirmed detected language
        3. Automatic detection
        Raises UnsupportedLanguageError if specified language is invalid.
        """
        if explicit_language:
            return cls.normalize(explicit_language)

        if confirmed_language:
            return cls.normalize(confirmed_language)

        if detected_language:
            return cls.normalize(detected_language)

        raise UnsupportedLanguageError("No programming language specified or detected.")
