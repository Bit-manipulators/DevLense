from __future__ import annotations

import base64
import io

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.config import get_settings
from app.main import app
from app.services.ocr_service import OcrService


def _create_sample_base64_image() -> str:
    image = Image.new("RGB", (100, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@pytest.mark.asyncio
async def test_ocr_endpoint_valid_image():
    b64 = _create_sample_base64_image()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/ocr",
            json={"image_base64": b64, "hint_language": "python"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "code" in data
        assert data["detected_language"] in ("python", "javascript", "cpp", "java")
        assert data["confidence"] > 0
        assert "provider" in data


@pytest.mark.asyncio
async def test_ocr_endpoint_data_uri_prefix():
    b64 = _create_sample_base64_image()
    data_uri = f"data:image/png;base64,{b64}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/ocr",
            json={"image_base64": data_uri, "hint_language": "javascript"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "code" in data
        assert data["detected_language"] in ("python", "javascript", "cpp", "java")


@pytest.mark.asyncio
async def test_ocr_endpoint_invalid_base64():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/ocr",
            json={"image_base64": "not-valid-base-64!!!"},
        )
        assert resp.status_code == 400


def test_language_detection_heuristics():
    settings = get_settings()
    service = OcrService(settings)

    # Python
    py_code = "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)"
    lang, conf = service.detect_language(py_code)
    assert lang == "python"
    assert conf >= 0.6

    # C++
    cpp_code = "#include <iostream>\nusing namespace std;\nint main() {\n    cout << 42 << endl;\n    return 0;\n}"
    lang, conf = service.detect_language(cpp_code)
    assert lang == "cpp"
    assert conf >= 0.6

    # JavaScript
    js_code = "const greet = (name) => {\n  console.log(`Hello, ${name}`);\n};\nexport default greet;"
    lang, conf = service.detect_language(js_code)
    assert lang == "javascript"
    assert conf >= 0.6

    # Java
    java_code = "public class Main {\n    public static void main(String[] args) {\n        System.out.println(100);\n    }\n}"
    lang, conf = service.detect_language(java_code)
    assert lang == "java"
    assert conf >= 0.6
