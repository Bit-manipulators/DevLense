from __future__ import annotations

from typing import Type

from app.analyzers.base import AnalyzerProvider
from app.analyzers.languages import (
    CppAnalyzer,
    JavaAnalyzer,
    JavaScriptAnalyzer,
    LanguageAnalyzer,
    PythonAnalyzer,
)
from app.analyzers.ollama import OllamaAnalyzer
from app.analyzers.rule_based import RuleBasedAnalyzer
from app.config import Settings
from app.schemas.analysis import LANGUAGE_ALIASES, SupportedLanguage


class AnalyzerFactory:
    """Factory for selecting language-specific diagnostic analyzers and providers."""

    _LANGUAGE_ANALYZERS: dict[SupportedLanguage, Type[LanguageAnalyzer]] = {
        "python": PythonAnalyzer,
        "cpp": CppAnalyzer,
        "javascript": JavaScriptAnalyzer,
        "java": JavaAnalyzer,
    }

    @classmethod
    def get_language_analyzer(cls, language: str) -> LanguageAnalyzer:
        """Resolves a language string (with aliases) and returns the corresponding language analyzer."""
        from app.languages.registry import LanguageRegistry, UnsupportedLanguageError

        canonical = LanguageRegistry.normalize(language)
        analyzer_cls = cls._LANGUAGE_ANALYZERS.get(canonical)  # type: ignore[arg-type]
        if not analyzer_cls:
            raise UnsupportedLanguageError(language)
        return analyzer_cls()

    @classmethod
    def normalize_language(cls, language: str) -> SupportedLanguage:
        from app.languages.registry import LanguageRegistry

        return LanguageRegistry.normalize(language)  # type: ignore[return-value]

    @classmethod
    def get_provider(cls, settings: Settings) -> AnalyzerProvider:
        if settings.llm_provider in ("auto", "ollama"):
            return OllamaAnalyzer(settings)
        return RuleBasedAnalyzer()


def get_analyzer(settings: Settings) -> AnalyzerProvider:
    return AnalyzerFactory.get_provider(settings)
