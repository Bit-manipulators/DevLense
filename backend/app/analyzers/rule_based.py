from __future__ import annotations

from app.analyzers.base import AnalysisFinding, AnalyzerProvider
from app.analyzers.languages import (
    CppAnalyzer,
    JavaAnalyzer,
    JavaScriptAnalyzer,
    PythonAnalyzer,
)


class RuleBasedAnalyzer(AnalyzerProvider):
    """Deterministic first-pass diagnostics that work without a model or API key.

    Delegates to modular, language-specific analyzers via AnalyzerFactory.
    """

    def __init__(self) -> None:
        self.python_analyzer = PythonAnalyzer()
        self.cpp_analyzer = CppAnalyzer()
        self.javascript_analyzer = JavaScriptAnalyzer()
        self.java_analyzer = JavaAnalyzer()

    async def analyze(
        self, language: str, code: str, error_message: str = "", question: str = ""
    ) -> AnalysisFinding:
        from app.analyzers.factory import AnalyzerFactory

        analyzer = AnalyzerFactory.get_language_analyzer(language)
        return analyzer.analyze(code, error_message, question)

    def _analyze_python(self, code: str, error: str = "", question: str = "") -> AnalysisFinding:
        return self.python_analyzer.analyze(code, error, question)

    def _analyze_cpp(self, code: str, error: str = "", question: str = "") -> AnalysisFinding:
        return self.cpp_analyzer.analyze(code, error, question)

    def _analyze_javascript(self, code: str, error: str = "", question: str = "") -> AnalysisFinding:
        return self.javascript_analyzer.analyze(code, error, question)

    def _analyze_java(self, code: str, error: str = "", question: str = "") -> AnalysisFinding:
        return self.java_analyzer.analyze(code, error, question)
