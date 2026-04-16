"""Tests for the shared config module."""

import os
import sys

import pytest


# ---------------------------------------------------------------------------
# Helper – import config *after* env vars are patched so that module-level
# constants pick up the patched values.  We use importlib.reload() for vars
# that are set at import time.
# ---------------------------------------------------------------------------

import importlib
import config as _cfg


def _reload_config():
    """Force-reload config so module-level constants are re-evaluated."""
    importlib.reload(_cfg)


# ===========================================================================
# get_language() tests
# ===========================================================================


class TestGetLanguage:
    """Cover all branches of config.get_language()."""

    def test_default_is_en(self, monkeypatch):
        """When AUTONOVEL_LANGUAGE is unset, get_language() returns 'en'."""
        monkeypatch.delenv("AUTONOVEL_LANGUAGE", raising=False)
        assert _cfg.get_language() == "en"

    def test_vi_is_supported(self, monkeypatch):
        """When AUTONOVEL_LANGUAGE=vi, get_language() returns 'vi'."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        assert _cfg.get_language() == "vi"

    def test_en_explicit(self, monkeypatch):
        """When AUTONOVEL_LANGUAGE=en, get_language() returns 'en'."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        assert _cfg.get_language() == "en"

    def test_unsupported_falls_back_to_en(self, monkeypatch, capsys):
        """Unsupported language code falls back to 'en' with a stderr warning."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "zz")
        result = _cfg.get_language()
        assert result == "en"
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "zz" in captured.err


# ===========================================================================
# Module-level export tests
# ===========================================================================


class TestExports:
    """Verify all documented names are importable and have correct types."""

    def test_api_key_is_str(self):
        assert isinstance(_cfg.API_KEY, str)

    def test_writer_model_is_str(self):
        assert isinstance(_cfg.WRITER_MODEL, str)

    def test_judge_model_is_str(self):
        assert isinstance(_cfg.JUDGE_MODEL, str)

    def test_review_model_is_str(self):
        assert isinstance(_cfg.REVIEW_MODEL, str)

    def test_api_base_is_str(self):
        assert isinstance(_cfg.API_BASE, str)

    def test_fal_key_is_str(self):
        assert isinstance(_cfg.FAL_KEY, str)

    def test_elevenlabs_key_is_str(self):
        assert isinstance(_cfg.ELEVENLABS_KEY, str)

    def test_base_dir_is_path(self):
        assert isinstance(_cfg.BASE_DIR, _cfg.Path)

    def test_chapters_dir_is_path(self):
        assert isinstance(_cfg.CHAPTERS_DIR, _cfg.Path)

    def test_chapters_dir_inside_base_dir(self):
        assert _cfg.CHAPTERS_DIR.parent == _cfg.BASE_DIR

    def test_base_dir_resolved(self):
        """BASE_DIR should be an absolute, resolved path."""
        assert _cfg.BASE_DIR.is_absolute()
        assert _cfg.BASE_DIR == _cfg.BASE_DIR.resolve()


# ===========================================================================
# Reload-based integration tests (verify env var wiring)
# ===========================================================================


class TestEnvWiring:
    """Check that module-level constants actually read from env vars."""

    def test_writer_model_from_env(self, monkeypatch):
        monkeypatch.setenv("AUTONOVEL_WRITER_MODEL", "test-model-w")
        _reload_config()
        assert _cfg.WRITER_MODEL == "test-model-w"

    def test_judge_model_from_env(self, monkeypatch):
        monkeypatch.setenv("AUTONOVEL_JUDGE_MODEL", "test-model-j")
        _reload_config()
        assert _cfg.JUDGE_MODEL == "test-model-j"

    def test_review_model_from_env(self, monkeypatch):
        monkeypatch.setenv("AUTONOVEL_REVIEW_MODEL", "test-model-r")
        _reload_config()
        assert _cfg.REVIEW_MODEL == "test-model-r"

    def test_api_base_from_env(self, monkeypatch):
        monkeypatch.setenv("AUTONOVEL_API_BASE_URL", "http://localhost:9999")
        _reload_config()
        assert _cfg.API_BASE == "http://localhost:9999"


# ===========================================================================
# language_instruction() and analysis_language_note() tests
# ===========================================================================


class TestLanguageInstruction:
    """Cover language_instruction() and analysis_language_note() helpers."""

    # -- language_instruction --------------------------------------------------

    def test_language_instruction_empty_when_en(self, monkeypatch):
        """language_instruction() returns '' when language is English."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        assert _cfg.language_instruction() == ""

    def test_language_instruction_nonempty_when_vi(self, monkeypatch):
        """language_instruction() returns a non-empty string when lang is vi."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        result = _cfg.language_instruction()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_language_instruction_mentions_vietnamese(self, monkeypatch):
        """language_instruction() text contains 'Vietnamese'."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        assert "Vietnamese" in _cfg.language_instruction()

    # -- analysis_language_note ------------------------------------------------

    def test_analysis_language_note_empty_when_en(self, monkeypatch):
        """analysis_language_note() returns '' when language is English."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        assert _cfg.analysis_language_note() == ""

    def test_analysis_language_note_nonempty_when_vi(self, monkeypatch):
        """analysis_language_note() returns a non-empty string when lang is vi."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        result = _cfg.analysis_language_note()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_analysis_language_note_mentions_vietnamese(self, monkeypatch):
        """analysis_language_note() text contains 'Vietnamese'."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        assert "Vietnamese" in _cfg.analysis_language_note()

    # -- cross-function differentiation ----------------------------------------

    def test_analysis_note_differs_from_instruction(self, monkeypatch):
        """analysis_language_note() and language_instruction() return different text."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        assert _cfg.analysis_language_note() != _cfg.language_instruction()
