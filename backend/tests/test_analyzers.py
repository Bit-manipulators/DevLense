from __future__ import annotations

import pytest

from app.analyzers.base import AnalyzerProvider
from app.analyzers.rule_based import RuleBasedAnalyzer
from app.services.analysis_service import AnalysisService


@pytest.mark.asyncio
async def test_javascript_null_rule():
    finding = await RuleBasedAnalyzer().analyze(
        "javascript", "const user = null;\nconsole.log(user.name);", "TypeError"
    )
    assert finding.severity == "high"
    assert "optional chaining" in finding.suggested_fix


class BrokenProvider(AnalyzerProvider):
    async def analyze(self, language: str, code: str, error_message: str = "", question: str = ""):
        raise RuntimeError("model offline")


@pytest.mark.asyncio
async def test_provider_failure_falls_back_to_rule_based_analyzer():
    finding = await AnalysisService(BrokenProvider()).analyze("python", "x = 1 / 0")
    assert finding.summary == "Division by zero"
    assert finding.confidence == 0.99


def test_rate_limiter_stale_cleanup():
    from app.utils.rate_limit import InMemoryRateLimiter
    limiter = InMemoryRateLimiter(limit=5, window_seconds=0.01, cleanup_interval_seconds=0.01)
    assert limiter.allow("1.1.1.1") is True
    assert "1.1.1.1" in limiter._hits

    import time
    time.sleep(0.02)
    # Next check after cleanup interval should purge the stale key
    assert limiter.allow("2.2.2.2") is True
    assert "1.1.1.1" not in limiter._hits
    assert "2.2.2.2" in limiter._hits


@pytest.mark.asyncio
async def test_cpp_loop_bound_analysis_and_correction():
    analyzer = RuleBasedAnalyzer()
    cpp_code = "for(int i = 0; i <= n; i++)"
    finding = await analyzer.analyze("cpp", cpp_code)

    assert "Python" not in finding.summary
    assert "syntax error" not in finding.summary.lower()
    assert "loop" in finding.summary.lower()
    assert "i < n" in finding.corrected_code
    assert finding.corrected_code == "for(int i = 0; i < n; i++)"


@pytest.mark.asyncio
async def test_cpp_alias_normalization_and_routing():
    from app.analyzers.factory import AnalyzerFactory

    cpp_analyzer = AnalyzerFactory.get_language_analyzer("c++")
    assert cpp_analyzer.__class__.__name__ == "CppAnalyzer"

    cpp_upper = AnalyzerFactory.get_language_analyzer("CPP")
    assert cpp_upper.__class__.__name__ == "CppAnalyzer"

    js_analyzer = AnalyzerFactory.get_language_analyzer("js")
    assert js_analyzer.__class__.__name__ == "JavaScriptAnalyzer"


@pytest.mark.asyncio
async def test_all_languages_routing_and_no_cross_contamination():
    analyzer = RuleBasedAnalyzer()

    # 1. Python
    py_res = await analyzer.analyze("python", "def test():\n    return 42")
    assert "python" in py_res.root_cause.lower() or py_res.summary != ""

    # 2. C++
    cpp_res = await analyzer.analyze("cpp", "for(int i = 0; i <= n; i++)")
    assert "Python" not in cpp_res.summary
    assert "i < n" in cpp_res.corrected_code

    # 3. JavaScript
    js_res = await analyzer.analyze("javascript", "const x = null; console.log(x.y);")
    assert "optional chaining" in js_res.suggested_fix

    # 4. Java
    java_res = await analyzer.analyze("java", "for (int i = 0; i <= max; i++)")
    assert "i < max" in java_res.corrected_code


