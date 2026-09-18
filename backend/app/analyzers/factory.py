from __future__ import annotations

from app.analyzers.base import AnalyzerProvider
from app.analyzers.ollama import OllamaAnalyzer
from app.analyzers.rule_based import RuleBasedAnalyzer
from app.config import Settings


def get_analyzer(settings: Settings) -> AnalyzerProvider:
    if settings.llm_provider == "ollama":
        return OllamaAnalyzer(settings)
    return RuleBasedAnalyzer()

