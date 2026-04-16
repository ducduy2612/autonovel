"""Tests for evaluate.slop_score() — language gating and return-shape checks."""

import os
import importlib

import pytest

import evaluate as _eval


# ---------------------------------------------------------------------------
# Helpers – reload evaluate after patching AUTONOVEL_LANGUAGE so that
# config.get_language() picks up the new value at call time (get_language
# reads the env var on every call, no reload needed for the config module
# itself, but we reload evaluate to rebind the imported reference cleanly).
# ---------------------------------------------------------------------------

_SAMPLE_EN = (
    "The wizard delved into the tapestry of magic. It was a multifaceted "
    "endeavor that would leverage the synergy of ancient runes.\n\n"
    "Furthermore, the quest was a holistic journey. She couldn't help but "
    "feel a sense of dread wash over her. The air was thick with anticipation.\n\n"
    "He felt a surge of excitement. She felt angry and sad. They felt "
    "nervous and excited all at once. It's important to note that this "
    "was a pivotal moment."
)

_SAMPLE_VI = (
    "Pháp sư đào sâu vào bức tranh thảm ma thuật. Đó là một nỗ lực đa chiều "
    "sẽ tận dụng sự hiệp đồng của các rune cổ đại.\n\n"
    "Hơn nữa, cuộc tìm kiếm là một hành trình toàn diện. Cô ấy không thể "
    "ngừng cảm thấy một luồng lo âu tràn qua. Không khí đặc lại với sự "
    "mong đợi.\n\n"
    "Anh ấy cảm thấy một luồng phấn khích. Cô ấy cảm thấy tức giận và buồn "
    "bã. Họ cảm thấy lo lắng và phấn khích cùng một lúc. Điều quan trọng cần "
    "lưu ý là đây là một khoảnh khắc then chốt."
)


def _slop(text, lang):
    """Call slop_score with AUTONOVEL_LANGUAGE set to *lang*."""
    os.environ["AUTONOVEL_LANGUAGE"] = lang
    importlib.reload(_eval)
    return _eval.slop_score(text)


# Expected keys every slop_score result must contain
_EXPECTED_KEYS = {
    "tier1_hits",
    "tier2_hits",
    "tier2_clusters",
    "tier3_hits",
    "fiction_ai_tells",
    "structural_ai_tics",
    "telling_violations",
    "em_dash_density",
    "sentence_length_cv",
    "transition_opener_ratio",
    "slop_penalty",
    "language",
}


# ===========================================================================
# TestSlopScore
# ===========================================================================


class TestSlopScore:
    """Cover language-gating logic in slop_score()."""

    # -- 1. English text, en language: full detection runs ------------------

    def test_english_text_en_language(self, monkeypatch):
        """English sample, AUTONOVEL_LANGUAGE=en → full detection runs."""
        result = _slop(_SAMPLE_EN, "en")
        assert result["language"] == "en"
        # Our sample is loaded with slop words — at least tier1 should fire
        assert len(result["tier1_hits"]) > 0
        # tier2 and tier3 likely non-zero as well
        assert len(result["tier2_hits"]) > 0 or result["tier2_clusters"] > 0 or len(result["tier3_hits"]) > 0
        # slop_penalty should be positive for this loaded sample
        assert result["slop_penalty"] > 0

    # -- 2. English text, vi language: English patterns skipped -------------

    def test_english_text_vi_language(self, monkeypatch):
        """English sample, AUTONOVEL_LANGUAGE=vi → English patterns skipped."""
        result = _slop(_SAMPLE_EN, "vi")
        assert result["language"] == "vi"
        # All English-specific fields should be empty/zero
        assert result["tier1_hits"] == []
        assert result["tier2_hits"] == []
        assert result["tier2_clusters"] == 0
        assert result["tier3_hits"] == []
        assert result["fiction_ai_tells"] == []
        assert result["structural_ai_tics"] == []
        assert result["telling_violations"] == 0
        assert result["transition_opener_ratio"] == 0.0

    # -- 3. Vietnamese text, vi language: agnostic stats computed ----------

    def test_vietnamese_text_vi_language(self, monkeypatch):
        """Vietnamese sample, AUTONOVEL_LANGUAGE=vi → English patterns skipped,
        agnostic stats computed."""
        result = _slop(_SAMPLE_VI, "vi")
        assert result["language"] == "vi"
        # English patterns skipped
        assert result["tier1_hits"] == []
        assert result["tier2_hits"] == []
        # Agnostic stats still computed
        assert isinstance(result["em_dash_density"], float)
        assert isinstance(result["sentence_length_cv"], float)

    # -- 4. Return shape is consistent across languages ---------------------

    def test_return_shape_consistent(self, monkeypatch):
        """Both languages return the same dict keys."""
        en_result = _slop(_SAMPLE_EN, "en")
        vi_result = _slop(_SAMPLE_VI, "vi")
        assert set(en_result.keys()) == _EXPECTED_KEYS
        assert set(vi_result.keys()) == _EXPECTED_KEYS
        assert set(en_result.keys()) == set(vi_result.keys())

    # -- 5. Penalty is agnostic-only for vi ---------------------------------

    def test_penalty_agnostic_only_for_vi(self, monkeypatch):
        """When vi, penalty only reflects em-dash density and sentence-length CV."""
        result = _slop(_SAMPLE_EN, "vi")
        penalty = result["slop_penalty"]
        # Reconstruct the expected penalty from agnostic stats only
        expected = 0.0
        if result["em_dash_density"] > 15:
            expected += min((result["em_dash_density"] - 15) * 0.3, 1.0)
        if result["sentence_length_cv"] < 0.3:
            expected += 1.0
        expected = round(min(expected, 10.0), 2)
        assert penalty == expected

    # -- 6. em_dash_density computed regardless of language -----------------

    def test_em_dash_computed_both_languages(self, monkeypatch):
        """em_dash_density is computed regardless of language."""
        en_result = _slop(_SAMPLE_EN, "en")
        vi_result = _slop(_SAMPLE_EN, "vi")
        # Same text → same em_dash_density
        assert en_result["em_dash_density"] == vi_result["em_dash_density"]
        assert isinstance(en_result["em_dash_density"], float)

    # -- 7. sentence_length_cv computed regardless of language ---------------

    def test_sentence_cv_computed_both_languages(self, monkeypatch):
        """sentence_length_cv is computed regardless of language."""
        en_result = _slop(_SAMPLE_EN, "en")
        vi_result = _slop(_SAMPLE_EN, "vi")
        # Same text → same sentence_length_cv
        assert en_result["sentence_length_cv"] == vi_result["sentence_length_cv"]
        assert isinstance(en_result["sentence_length_cv"], float)


# ---------------------------------------------------------------------------
# Helpers for prompt adaptation tests
# ---------------------------------------------------------------------------

def _build_foundation_prompt(lang):
    """Build the foundation prompt with the given language's cross-checks."""
    os.environ["AUTONOVEL_LANGUAGE"] = lang
    importlib.reload(_eval)
    layers = {
        "voice": "Test voice definition.",
        "world": "Test world bible.",
        "characters": "Test character registry.",
        "outline": "Test outline.",
        "canon": "Test canon.",
    }
    cross_checks = _eval._get_cross_checks("FOUNDATION")
    return _eval.FOUNDATION_PROMPT.format(cross_checks=cross_checks, **layers)


def _build_chapter_prompt(lang):
    """Build the chapter prompt with the given language's cross-checks."""
    os.environ["AUTONOVEL_LANGUAGE"] = lang
    importlib.reload(_eval)
    layers = {
        "voice": "Test voice definition.",
        "world": "Test world bible.",
        "characters": "Test character registry.",
        "canon": "Test canon.",
    }
    cross_checks = _eval._get_cross_checks("CHAPTER")
    return _eval.CHAPTER_PROMPT.format(
        cross_checks=cross_checks,
        chapter_outline="Test outline entry.",
        prev_chapter_tail="Previous chapter text.",
        chapter_text="Chapter text to evaluate.",
        **layers,
    )


# ===========================================================================
# TestPromptAdaptation
# ===========================================================================


class TestPromptAdaptation:
    """Cover cross-check language adaptation in FOUNDATION_PROMPT and CHAPTER_PROMPT."""

    # -- 1. Foundation prompt English cross-checks -------------------------

    def test_foundation_prompt_english_cross_checks(self):
        """AUTONOVEL_LANGUAGE=en → foundation cross-checks mention ANTI-SLOP
        and structural formulas."""
        prompt = _build_foundation_prompt("en")
        assert "ANTI-SLOP" in prompt
        assert "structural formulas" in prompt
        # Should NOT contain Vietnamese-specific instructions
        assert "Vietnamese AI clichés" not in prompt

    # -- 2. Foundation prompt Vietnamese cross-checks ----------------------

    def test_foundation_prompt_vietnamese_cross_checks(self):
        """AUTONOVEL_LANGUAGE=vi → foundation cross-checks mention Vietnamese
        AI clichés, cultural specificity, and prose naturalness."""
        prompt = _build_foundation_prompt("vi")
        assert "Vietnamese AI clichés" in prompt
        assert "CULTURAL SPECIFICITY" in prompt
        assert "PROSE NATURALNESS" in prompt
        # Should NOT contain English-specific ANTI-SLOP references
        assert "ANTI-SLOP" not in prompt
        assert "NEGATIVE SPACE" not in prompt

    # -- 3. Chapter prompt English cross-checks ----------------------------

    def test_chapter_prompt_english_cross_checks(self):
        """AUTONOVEL_LANGUAGE=en → chapter cross-checks mention English AI
        patterns (QUOTE TEST, DIALOGUE REALISM, AI PATTERN CHECK)."""
        prompt = _build_chapter_prompt("en")
        assert "QUOTE TEST" in prompt
        assert "DIALOGUE REALISM" in prompt
        assert "AI PATTERN CHECK" in prompt
        assert "EARNED VS GIVEN" in prompt
        # Should NOT contain Vietnamese-specific instructions
        assert "VIETNAMESE AI PATTERN CHECK" not in prompt
        assert "DIALOGUE NATURALNESS" not in prompt

    # -- 4. Chapter prompt Vietnamese cross-checks -------------------------

    def test_chapter_prompt_vietnamese_cross_checks(self):
        """AUTONOVEL_LANGUAGE=vi → chapter cross-checks mention Vietnamese
        prose patterns, dialogue naturalness with particles."""
        prompt = _build_chapter_prompt("vi")
        assert "VIETNAMESE AI PATTERN CHECK" in prompt
        assert "DIALOGUE NATURALNESS" in prompt
        assert "sentence-final particles" in prompt
        assert "pronoun system" in prompt
        # Should NOT contain English-specific AI PATTERN CHECK
        assert "AI PATTERN CHECK" not in prompt or "VIETNAMESE AI PATTERN CHECK" in prompt

    # -- 5. Full novel prompt unchanged across languages --------------------

    def test_full_novel_prompt_unchanged(self):
        """FULL_NOVEL_PROMPT content is identical regardless of language."""
        en_prompt = _build_foundation_prompt("en")  # sets language to en
        en_full = _eval.FULL_NOVEL_PROMPT

        vi_prompt = _build_foundation_prompt("vi")  # sets language to vi
        vi_full = _eval.FULL_NOVEL_PROMPT

        assert en_full == vi_full
        # Also verify FULL_NOVEL_PROMPT has no cross_checks placeholder
        assert "{cross_checks}" not in _eval.FULL_NOVEL_PROMPT
