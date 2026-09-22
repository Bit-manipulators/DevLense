from __future__ import annotations

import pytest

from app.languages.registry import LanguageRegistry, UnsupportedLanguageError


def test_language_registry_normalization():
    assert LanguageRegistry.normalize("cpp") == "cpp"
    assert LanguageRegistry.normalize("c++") == "cpp"
    assert LanguageRegistry.normalize("C++") == "cpp"
    assert LanguageRegistry.normalize("c") == "cpp"
    assert LanguageRegistry.normalize("javascript") == "javascript"
    assert LanguageRegistry.normalize("js") == "javascript"
    assert LanguageRegistry.normalize("JS") == "javascript"
    assert LanguageRegistry.normalize("node") == "javascript"
    assert LanguageRegistry.normalize("python") == "python"
    assert LanguageRegistry.normalize("py") == "python"
    assert LanguageRegistry.normalize("java") == "java"
    assert LanguageRegistry.normalize("JAVA") == "java"


def test_language_registry_rejects_unsupported():
    with pytest.raises(UnsupportedLanguageError):
        LanguageRegistry.normalize("rust")

    with pytest.raises(UnsupportedLanguageError):
        LanguageRegistry.normalize("ruby")

    with pytest.raises(UnsupportedLanguageError):
        LanguageRegistry.normalize("")

    assert LanguageRegistry.is_supported("rust") is False
    assert LanguageRegistry.is_supported("cpp") is True


def test_language_config_properties():
    cpp_cfg = LanguageRegistry.get("c++")
    assert cpp_cfg.id == "cpp"
    assert cpp_cfg.is_compiled is True
    assert cpp_cfg.extension == ".cpp"
    assert cpp_cfg.filename == "main.cpp"

    py_cfg = LanguageRegistry.get("py")
    assert py_cfg.id == "python"
    assert py_cfg.is_compiled is False
    assert py_cfg.extension == ".py"


def test_resolve_language_priority():
    # 1. Explicit user selection wins over confirmed and detected
    resolved = LanguageRegistry.resolve_language(
        explicit_language="c++",
        confirmed_language="python",
        detected_language="javascript",
    )
    assert resolved == "cpp"

    # 2. Confirmed detected language wins over auto detected
    resolved2 = LanguageRegistry.resolve_language(
        explicit_language=None,
        confirmed_language="js",
        detected_language="python",
    )
    assert resolved2 == "javascript"

    # 3. Auto detected works when explicit/confirmed are absent
    resolved3 = LanguageRegistry.resolve_language(
        explicit_language=None,
        confirmed_language=None,
        detected_language="python",
    )
    assert resolved3 == "python"

    # 4. Explicit invalid raises error, never silently falls back to python
    with pytest.raises(UnsupportedLanguageError):
        LanguageRegistry.resolve_language(
            explicit_language="brainfuck",
            detected_language="python",
        )
