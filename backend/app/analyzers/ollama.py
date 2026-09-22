from __future__ import annotations

import json
import re

import httpx

from app.analyzers.base import AnalysisFinding, AnalyzerProvider
from app.config import Settings


class OllamaAnalyzer(AnalyzerProvider):
    """Local LLM debugging analyzer powered by Ollama coding models."""

    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model or "qwen2.5-coder:3b"

    async def _resolve_model(self, client: httpx.AsyncClient) -> str:
        if self.model:
            return self.model
        try:
            resp = await client.get(f"{self.base_url}/api/tags", timeout=3.0)
            if resp.status_code == 200:
                tags = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in tags]
                for pref in ("qwen2.5-coder:3b", "qwen2.5-coder:7b", "codellama", "deepseek-coder", "llama3", "mistral"):
                    for m in model_names:
                        if pref in m:
                            return m
                for m in model_names:
                    if "embed" not in m:
                        return m
        except Exception:
            pass
        return "qwen2.5-coder:3b"

    async def analyze(
        self, language: str, code: str, error_message: str = "", question: str = ""
    ) -> AnalysisFinding:
        async with httpx.AsyncClient(timeout=45.0) as client:
            model_to_use = await self._resolve_model(client)
            self.model = model_to_use

            prompt = (
                "You are DevLens AI, an expert compiler engineer, security auditor, and debugging system.\n"
                "Analyze the following source code for syntax errors, logical bugs, edge-case failures, or runtime crashes.\n\n"
                "CRITICAL REQUIREMENTS:\n"
                "1. 'corrected_code' MUST BE THE COMPLETE, VALID, WORKING SOURCE CODE with the bug fixed.\n"
                "2. DO NOT return the original buggy code as corrected_code.\n"
                "3. Preserve all other working parts of the user's program.\n"
                "4. Output MUST be ONLY a single valid JSON object with the following fields:\n"
                "   - summary (string): concise bug summary\n"
                "   - severity (string): 'low' | 'medium' | 'high' | 'critical'\n"
                "   - root_cause (string): exact cause of the fault\n"
                "   - explanation (string): clear explanation of why it fails\n"
                "   - affected_lines (list of ints): 1-based line numbers containing the bug\n"
                "   - suggested_fix (string): concise instruction on how to fix it\n"
                "   - corrected_code (string): the fully corrected code\n"
                "   - debugging_steps (list of strings): recommended verification steps\n"
                "   - confidence (float between 0.0 and 1.0)\n\n"
                f"Language: {language}\n"
                f"Error or compiler diagnostic: {error_message or 'None provided'}\n"
                f"User question: {question or 'Diagnose and fix all issues'}\n"
                f"Source Code:\n{code}\n"
            )

            payload = {
                "model": model_to_use,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            }

            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            content = response.json().get("response", "").strip()

            # Clean markdown code fences if wrapped
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"^```\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                content = json_match.group(0)

            data = json.loads(content)
            if not data.get("corrected_code") or data.get("corrected_code") == code:
                # If model somehow omitted corrected_code, ensure it has a valid value
                data["corrected_code"] = data.get("corrected_code") or code

            return AnalysisFinding.model_validate(data)
