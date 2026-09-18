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

