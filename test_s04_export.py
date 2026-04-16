"""Tests for S04 — Export and metadata language support.

Covers:
  1. default_state() includes language='en' by default
  2. default_state() with AUTONOVEL_LANGUAGE=vi includes language='vi'
  3. patch_epub_metadata() patches lang correctly for en and vi
"""

import os
import sys
import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so imports work from any cwd
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ===========================================================================
# default_state() language field tests
# ===========================================================================

class TestDefaultStateLanguage:
    """Verify that default_state() propagates the configured language."""

    def test_default_language_is_en(self, monkeypatch):
        """When AUTONOVEL_LANGUAGE is unset, default_state()['language'] == 'en'."""
        monkeypatch.delenv("AUTONOVEL_LANGUAGE", raising=False)
        # Force re-import so the module picks up the patched env
        import importlib
        import run_pipeline as rp
        importlib.reload(rp)
        state = rp.default_state()
        assert state["language"] == "en"

    def test_vi_language_when_env_set(self, monkeypatch):
        """When AUTONOVEL_LANGUAGE=vi, default_state()['language'] == 'vi'."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        import importlib
        import run_pipeline as rp
        importlib.reload(rp)
        state = rp.default_state()
        assert state["language"] == "vi"

    def test_explicit_en_language(self, monkeypatch):
        """When AUTONOVEL_LANGUAGE=en, default_state()['language'] == 'en'."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import importlib
        import run_pipeline as rp
        importlib.reload(rp)
        state = rp.default_state()
        assert state["language"] == "en"

    def test_state_dict_has_language_key(self, monkeypatch):
        """default_state() always includes a 'language' key."""
        monkeypatch.delenv("AUTONOVEL_LANGUAGE", raising=False)
        import importlib
        import run_pipeline as rp
        importlib.reload(rp)
        state = rp.default_state()
        assert "language" in state


# ===========================================================================
# patch_epub_metadata() tests
# ===========================================================================

class TestPatchEpubMetadata:
    """Verify that patch_epub_metadata() correctly patches the lang field."""

    SAMPLE_YAML = textwrap.dedent("""\
        ---
        title: TITLE
        author: AUTHOR
        lang: en
        rights: This is a work of fiction.
        publisher: Publisher Name
        date: 2026
        cover-image: ../art/epub_front_cover.png
        css: epub_style.css
        titlepage: false
        ...
    """)

    def _write_metadata(self, tmp_path: Path, content: str = None) -> Path:
        """Write a sample epub_metadata.yaml to tmp_path and return its path."""
        meta = tmp_path / "epub_metadata.yaml"
        meta.write_text(content or self.SAMPLE_YAML, encoding="utf-8")
        return meta

    def test_patch_to_vi(self, tmp_path):
        """Patching lang to 'vi' updates the file correctly."""
        meta = self._write_metadata(tmp_path)
        import importlib
        import typeset.build_tex as bt
        importlib.reload(bt)
        bt.patch_epub_metadata(meta, lang="vi")

        text = meta.read_text(encoding="utf-8")
        assert "lang: vi" in text
        assert "lang: en" not in text

    def test_patch_to_en(self, tmp_path):
        """Patching lang to 'en' preserves the original value."""
        # Start with a file that has lang: vi
        vi_yaml = self.SAMPLE_YAML.replace("lang: en", "lang: vi")
        meta = self._write_metadata(tmp_path, vi_yaml)
        import importlib
        import typeset.build_tex as bt
        importlib.reload(bt)
        bt.patch_epub_metadata(meta, lang="en")

        text = meta.read_text(encoding="utf-8")
        assert "lang: en" in text
        assert "lang: vi" not in text

    def test_no_change_when_lang_already_correct(self, tmp_path):
        """No write occurs when the lang field already matches."""
        meta = self._write_metadata(tmp_path)
        import importlib
        import typeset.build_tex as bt
        importlib.reload(bt)

        original_mtime = meta.stat().st_mtime
        bt.patch_epub_metadata(meta, lang="en")

        # File content should be identical
        assert meta.read_text(encoding="utf-8") == self.SAMPLE_YAML

    def test_other_fields_preserved(self, tmp_path):
        """Patching lang does not modify other YAML fields."""
        meta = self._write_metadata(tmp_path)
        import importlib
        import typeset.build_tex as bt
        importlib.reload(bt)
        bt.patch_epub_metadata(meta, lang="vi")

        text = meta.read_text(encoding="utf-8")
        assert "title: TITLE" in text
        assert "author: AUTHOR" in text
        assert "rights: This is a work of fiction." in text

    def test_missing_file_does_not_error(self, tmp_path):
        """patch_epub_metadata() silently skips non-existent files."""
        missing = tmp_path / "nonexistent.yaml"
        import importlib
        import typeset.build_tex as bt
        importlib.reload(bt)
        # Should not raise
        bt.patch_epub_metadata(missing, lang="vi")

    def test_patch_uses_get_language_by_default(self, tmp_path, monkeypatch):
        """When lang is not passed, patch_epub_metadata uses get_language()."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        meta = self._write_metadata(tmp_path)
        import importlib
        import typeset.build_tex as bt
        importlib.reload(bt)
        bt.patch_epub_metadata(meta)

        text = meta.read_text(encoding="utf-8")
        assert "lang: vi" in text


# ===========================================================================
# generate_latex_header() / babel injection tests
# ===========================================================================

class TestGenerateLatexHeader:
    """Verify conditional Vietnamese babel injection in the LaTeX header."""

    def test_en_header_has_no_babel(self):
        """When language is 'en', no babel usepackage line appears."""
        import importlib
        import typeset.build_tex as bt
        importlib.reload(bt)

        header = bt.generate_latex_header(lang="en")
        assert "babel" not in header
        assert "%% Language: en" in header

    def test_vi_header_includes_babel(self):
        """When language is 'vi', \\usepackage[vietnamese]{babel} is present."""
        import importlib
        import typeset.build_tex as bt
        importlib.reload(bt)

        header = bt.generate_latex_header(lang="vi")
        assert "\\usepackage[vietnamese]{babel}" in header
        assert "%% Language: vi" in header

    def test_header_is_auto_generated_comment(self):
        """Header starts with an auto-generation comment."""
        import importlib
        import typeset.build_tex as bt
        importlib.reload(bt)

        header = bt.generate_latex_header(lang="en")
        assert "Auto-generated by build_tex.py" in header

    def test_vi_header_from_env(self, monkeypatch):
        """When AUTONOVEL_LANGUAGE=vi and no lang arg passed, babel is injected."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        import importlib
        import typeset.build_tex as bt
        importlib.reload(bt)

        header = bt.generate_latex_header()
        assert "\\usepackage[vietnamese]{babel}" in header

    def test_en_header_from_env(self, monkeypatch):
        """When AUTONOVEL_LANGUAGE=en and no lang arg passed, no babel."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import importlib
        import typeset.build_tex as bt
        importlib.reload(bt)

        header = bt.generate_latex_header()
        assert "babel" not in header
