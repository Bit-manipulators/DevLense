from __future__ import annotations

import logging

from app.analyzers.base import AnalysisFinding, AnalyzerProvider
from app.analyzers.rule_based import RuleBasedAnalyzer

logger = logging.getLogger("devlens.analysis")


class AnalysisService:
    """Coordinates the configured analyzer and guaranteed safe fallback."""

    def __init__(self, analyzer: AnalyzerProvider):
        self.analyzer = analyzer
        self.fallback = RuleBasedAnalyzer()

    async def analyze(
        self, language: str, code: str, error_message: str = "", question: str = ""
    ) -> AnalysisFinding:
        try:
            return await self.analyzer.analyze(language, code, error_message, question)
        except Exception as exc:
            # Providers are optional. The product remains usable without an LLM.
            logger.warning(
                "Configured analyzer (%s) failed, falling back to rule-based analyzer: %s",
                type(self.analyzer).__name__,
                exc,
            )
            return await self.fallback.analyze(language, code, error_message, question)

