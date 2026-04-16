"""S05 End-to-end integration tests — Vietnamese foundation chain.

Verifies that all prior slices (S02–S04) work together when
AUTONOVEL_LANGUAGE=vi: the foundation phase produces Vietnamese world bible,
characters, outline, canon, and honest evaluation scores from a Vietnamese
seed concept.

All API calls are mocked — tests run without ANTHROPIC_API_KEY.

Test categories:
  1. Pipeline file-writing tests (validates T01 fix)
  2. Language instruction wiring tests (validates S02)
  3. Vietnamese text detection tests
  4. Evaluation adaptation tests (validates S03)
  5. State language field test (validates S04)
  6. End-to-end chain test (the main integration test)
"""

import importlib
import json
import os
import re
import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Vietnamese text detection helper
# ---------------------------------------------------------------------------

_VI_CHARS_RE = re.compile(r"[ăâđêôơưĂÂĐÊÔƠƯ]")


def contains_vietnamese(text: str) -> bool:
    """Return True if *text* contains Vietnamese-specific diacritical
    characters (ă, â, đ, ê, ô, ơ, ư and their uppercase forms)."""
    return bool(_VI_CHARS_RE.search(text))


# ===========================================================================
# 1. Pipeline file-writing tests (validates T01 fix)
# ===========================================================================


class TestPipelineFileWriting:
    """Verify that run_foundation() writes each script's stdout to the
    correct .md file. Uses mocked subprocess to avoid real API calls."""

    def _fake_completed_process(self, stdout: str, returncode: int = 0):
        """Create a fake subprocess.CompletedProcess."""
        return MagicMock(
            returncode=returncode,
            stdout=stdout,
            stderr="",
        )

    def test_world_md_written(self, tmp_path, monkeypatch):
        """gen_world.py stdout is written to world.md."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import run_pipeline as rp
        importlib.reload(rp)

        fake_output = "# World Bible\n\nA fantasy world with bells."
        calls = iter([
            self._fake_completed_process(fake_output),  # gen_world.py
            self._fake_completed_process("# Characters\n\nCass Bellwright."),  # gen_characters
            self._fake_completed_process("# Outline\n\nChapter 1."),  # gen_outline
            self._fake_completed_process("# Foreshadowing"),  # gen_outline_part2
            self._fake_completed_process("# Canon\n\nFact 1."),  # gen_canon
            self._fake_completed_process(""),  # voice_fingerprint (no write expected)
            # Evaluation call
            self._fake_completed_process("overall_score: 8.0\nlore_score: 7.5"),
        ])
        monkeypatch.setattr(rp, "uv_run", lambda *a, **kw: next(calls))
        monkeypatch.setattr(rp, "git_add_commit", lambda *a, **kw: "abc1234")
        monkeypatch.setattr(rp, "git_reset_hard", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "save_state", lambda *a, **kw: None)

        # Override BASE_DIR to tmp_path so files go there
        monkeypatch.setattr(rp, "BASE_DIR", tmp_path)

        state = {
            "phase": "foundation",
            "iteration": 0,
            "foundation_score": 0.0,
            "lore_score": 0.0,
        }
        rp.run_foundation(state)

        world_file = tmp_path / "world.md"
        assert world_file.exists()
        assert fake_output in world_file.read_text()

    def test_characters_md_written(self, tmp_path, monkeypatch):
        """gen_characters.py stdout is written to characters.md."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import run_pipeline as rp
        importlib.reload(rp)

        fake_chars = "# Characters\n\nCass Bellwright, 14 years old."
        calls = iter([
            self._fake_completed_process("# World Bible"),
            self._fake_completed_process(fake_chars),
            self._fake_completed_process("# Outline"),
            self._fake_completed_process("# Foreshadowing"),
            self._fake_completed_process("# Canon"),
            self._fake_completed_process(""),
            self._fake_completed_process("overall_score: 8.0\nlore_score: 7.5"),
        ])
        monkeypatch.setattr(rp, "uv_run", lambda *a, **kw: next(calls))
        monkeypatch.setattr(rp, "git_add_commit", lambda *a, **kw: "abc1234")
        monkeypatch.setattr(rp, "git_reset_hard", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "save_state", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "BASE_DIR", tmp_path)

        rp.run_foundation({"phase": "foundation", "iteration": 0,
                           "foundation_score": 0.0, "lore_score": 0.0})

        chars_file = tmp_path / "characters.md"
        assert chars_file.exists()
        assert fake_chars in chars_file.read_text()

    def test_outline_md_written_and_appended(self, tmp_path, monkeypatch):
        """gen_outline.py writes to outline.md; gen_outline_part2.py appends."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import run_pipeline as rp
        importlib.reload(rp)

        part1 = "# Outline\n\n## Act I\n\n### Ch 1"
        part2 = "### Ch 18\n\n## Foreshadowing Ledger"
        calls = iter([
            self._fake_completed_process("# World"),
            self._fake_completed_process("# Characters"),
            self._fake_completed_process(part1),  # gen_outline.py
            self._fake_completed_process(part2),  # gen_outline_part2.py
            self._fake_completed_process("# Canon"),
            self._fake_completed_process(""),
            self._fake_completed_process("overall_score: 8.0\nlore_score: 7.5"),
        ])
        monkeypatch.setattr(rp, "uv_run", lambda *a, **kw: next(calls))
        monkeypatch.setattr(rp, "git_add_commit", lambda *a, **kw: "abc1234")
        monkeypatch.setattr(rp, "git_reset_hard", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "save_state", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "BASE_DIR", tmp_path)

        rp.run_foundation({"phase": "foundation", "iteration": 0,
                           "foundation_score": 0.0, "lore_score": 0.0})

        outline_file = tmp_path / "outline.md"
        assert outline_file.exists()
        content = outline_file.read_text()
        # Part 1 content should be present
        assert part1 in content
        # Part 2 content should be appended
        assert part2 in content

    def test_canon_md_written(self, tmp_path, monkeypatch):
        """gen_canon.py stdout is written to canon.md."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import run_pipeline as rp
        importlib.reload(rp)

        fake_canon = "# Canon\n\n## Geography\n- Fact 1."
        calls = iter([
            self._fake_completed_process("# World"),
            self._fake_completed_process("# Characters"),
            self._fake_completed_process("# Outline"),
            self._fake_completed_process("# Foreshadowing"),
            self._fake_completed_process(fake_canon),
            self._fake_completed_process(""),
            self._fake_completed_process("overall_score: 8.0\nlore_score: 7.5"),
        ])
        monkeypatch.setattr(rp, "uv_run", lambda *a, **kw: next(calls))
        monkeypatch.setattr(rp, "git_add_commit", lambda *a, **kw: "abc1234")
        monkeypatch.setattr(rp, "git_reset_hard", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "save_state", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "BASE_DIR", tmp_path)

        rp.run_foundation({"phase": "foundation", "iteration": 0,
                           "foundation_score": 0.0, "lore_score": 0.0})

        canon_file = tmp_path / "canon.md"
        assert canon_file.exists()
        assert fake_canon in canon_file.read_text()

    def test_voice_fingerprint_no_planning_doc_write(self, tmp_path, monkeypatch):
        """voice_fingerprint.py is called but doesn't write any planning doc file."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import run_pipeline as rp
        importlib.reload(rp)

        calls = iter([
            self._fake_completed_process("# World"),
            self._fake_completed_process("# Characters"),
            self._fake_completed_process("# Outline"),
            self._fake_completed_process("# Foreshadowing"),
            self._fake_completed_process("# Canon"),
            self._fake_completed_process("voice_fingerprint output"),
            self._fake_completed_process("overall_score: 8.0\nlore_score: 7.5"),
        ])
        monkeypatch.setattr(rp, "uv_run", lambda *a, **kw: next(calls))
        monkeypatch.setattr(rp, "git_add_commit", lambda *a, **kw: "abc1234")
        monkeypatch.setattr(rp, "git_reset_hard", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "save_state", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "BASE_DIR", tmp_path)

        rp.run_foundation({"phase": "foundation", "iteration": 0,
                           "foundation_score": 0.0, "lore_score": 0.0})

        # Voice fingerprint should NOT create any of these planning doc files
        for name in ["voice_fingerprint.md", "voice.md", "fingerprint.md"]:
            assert not (tmp_path / name).exists(), f"Unexpected file: {name}"

    def test_failed_script_does_not_overwrite(self, tmp_path, monkeypatch):
        """A failed script (non-zero returncode) should not overwrite prior output."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import run_pipeline as rp
        importlib.reload(rp)

        # Pre-write world.md with good content
        good_world = "# Good World Bible\n\nExisting content."
        (tmp_path / "world.md").write_text(good_world)

        calls = iter([
            self._fake_completed_process("BAD OUTPUT", returncode=1),  # world fails
            self._fake_completed_process("# Characters"),
            self._fake_completed_process("# Outline"),
            self._fake_completed_process("# Foreshadowing"),
            self._fake_completed_process("# Canon"),
            self._fake_completed_process(""),
            self._fake_completed_process("overall_score: 8.0\nlore_score: 7.5"),
        ])
        monkeypatch.setattr(rp, "uv_run", lambda *a, **kw: next(calls))
        monkeypatch.setattr(rp, "git_add_commit", lambda *a, **kw: "abc1234")
        monkeypatch.setattr(rp, "git_reset_hard", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "save_state", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "BASE_DIR", tmp_path)

        rp.run_foundation({"phase": "foundation", "iteration": 0,
                           "foundation_score": 0.0, "lore_score": 0.0})

        # Good world content should be preserved
        assert (tmp_path / "world.md").read_text() == good_world

    def test_empty_stdout_does_not_overwrite(self, tmp_path, monkeypatch):
        """A script returning empty stdout should not overwrite prior output."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import run_pipeline as rp
        importlib.reload(rp)

        good_world = "# Good World Bible\n\nExisting content."
        (tmp_path / "world.md").write_text(good_world)

        calls = iter([
            self._fake_completed_process(""),  # empty stdout
            self._fake_completed_process("# Characters"),
            self._fake_completed_process("# Outline"),
            self._fake_completed_process("# Foreshadowing"),
            self._fake_completed_process("# Canon"),
            self._fake_completed_process(""),
            self._fake_completed_process("overall_score: 8.0\nlore_score: 7.5"),
        ])
        monkeypatch.setattr(rp, "uv_run", lambda *a, **kw: next(calls))
        monkeypatch.setattr(rp, "git_add_commit", lambda *a, **kw: "abc1234")
        monkeypatch.setattr(rp, "git_reset_hard", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "save_state", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "BASE_DIR", tmp_path)

        rp.run_foundation({"phase": "foundation", "iteration": 0,
                           "foundation_score": 0.0, "lore_score": 0.0})

        assert (tmp_path / "world.md").read_text() == good_world


# ===========================================================================
# 2. Language instruction wiring tests (validates S02)
# ===========================================================================


class TestLanguageInstructionWiring:
    """Verify that each foundation script's call_writer() includes the
    Vietnamese creative-writing instruction when AUTONOVEL_LANGUAGE=vi,
    and excludes it when AUTONOVEL_LANGUAGE=en.

    The scripts use ``config.language_instruction()`` to append the
    language directive to their system prompts.  We test this by
    importing each script's *call_writer* function directly, mocking
    httpx.post to capture the payload, and also ensuring the required
    input files exist for scripts that read them at module level.

    Some scripts (gen_world, gen_characters, gen_outline, gen_canon)
    read files at module import time. We create those files in tmp_path
    and patch BASE_DIR to point there.
    """

    @staticmethod
    def _mock_api_response(text: str = "Generated content here."):
        """Return a mock httpx.Response that looks like a successful Anthropic call."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "content": [{"text": text}],
        }
        return mock_resp

    def _setup_project_files(self, tmp_path):
        """Create all required input files in tmp_path."""
        (tmp_path / "seed.txt").write_text("A Vietnamese fantasy novel about bells.")
        (tmp_path / "voice.md").write_text("# Voice\n\n## Part 2\nVoice definition.")
        (tmp_path / "CRAFT.md").write_text("# Craft\n\nCraft requirements.")
        (tmp_path / "MYSTERY.md").write_text("# Mystery\n\nCentral mystery.")
        (tmp_path / "world.md").write_text("# World Bible\n\nWorld content.")
        (tmp_path / "characters.md").write_text("# Characters\n\nCharacter content.")
        Path("/tmp/outline_output.md").write_text("# Outline Part 1")

    def _capture_call_writer_system_prompt(self, module_name, lang, monkeypatch, tmp_path):
        """Import a script with the given lang, call its call_writer(), and
        return the captured system prompt from the API payload."""
        self._setup_project_files(tmp_path)
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", lang)

        # Patch BASE_DIR in both config and the target module before import
        import config as _cfg
        monkeypatch.setattr(_cfg, "BASE_DIR", tmp_path)

        captured_payload = {}

        def capture_post(url, **kwargs):
            captured_payload.update(kwargs.get("json", {}))
            return self._mock_api_response("Generated content.")

        with patch("httpx.post", side_effect=capture_post):
            mod = importlib.import_module(module_name)
            # Patch BASE_DIR in the imported module
            monkeypatch.setattr(mod, "BASE_DIR", tmp_path)
            importlib.reload(mod)
            mod.call_writer("test prompt")

        return captured_payload.get("system", "")

    # -- gen_world.py system prompt --

    def test_gen_world_vi_instruction_in_system_prompt(self, monkeypatch, tmp_path):
        """gen_world.py system prompt contains Vietnamese instruction when lang=vi."""
        system = self._capture_call_writer_system_prompt(
            "gen_world", "vi", monkeypatch, tmp_path)
        assert "Vietnamese" in system
        assert "literary Vietnamese" in system

    def test_gen_world_en_no_vi_instruction(self, monkeypatch, tmp_path):
        """gen_world.py system prompt does NOT contain Vietnamese instruction when lang=en."""
        system = self._capture_call_writer_system_prompt(
            "gen_world", "en", monkeypatch, tmp_path)
        assert "Vietnamese" not in system

    # -- gen_characters.py system prompt --

    def test_gen_characters_vi_instruction_in_system_prompt(self, monkeypatch, tmp_path):
        """gen_characters.py system prompt contains Vietnamese instruction when lang=vi."""
        system = self._capture_call_writer_system_prompt(
            "gen_characters", "vi", monkeypatch, tmp_path)
        assert "Vietnamese" in system
        assert "literary Vietnamese" in system

    def test_gen_characters_en_no_vi_instruction(self, monkeypatch, tmp_path):
        """gen_characters.py system prompt does NOT contain Vietnamese instruction when lang=en."""
        system = self._capture_call_writer_system_prompt(
            "gen_characters", "en", monkeypatch, tmp_path)
        assert "Vietnamese" not in system

    # -- gen_outline.py system prompt --

    def test_gen_outline_vi_instruction_in_system_prompt(self, monkeypatch, tmp_path):
        """gen_outline.py system prompt contains Vietnamese instruction when lang=vi."""
        system = self._capture_call_writer_system_prompt(
            "gen_outline", "vi", monkeypatch, tmp_path)
        assert "Vietnamese" in system
        assert "literary Vietnamese" in system

    def test_gen_outline_en_no_vi_instruction(self, monkeypatch, tmp_path):
        """gen_outline.py system prompt does NOT contain Vietnamese instruction when lang=en."""
        system = self._capture_call_writer_system_prompt(
            "gen_outline", "en", monkeypatch, tmp_path)
        assert "Vietnamese" not in system

    # -- gen_outline_part2.py system prompt --

    def test_gen_outline_part2_vi_instruction(self, monkeypatch, tmp_path):
        """gen_outline_part2.py system prompt contains Vietnamese instruction when lang=vi."""
        system = self._capture_call_writer_system_prompt(
            "gen_outline_part2", "vi", monkeypatch, tmp_path)
        assert "Vietnamese" in system
        assert "literary Vietnamese" in system

    def test_gen_outline_part2_en_no_vi_instruction(self, monkeypatch, tmp_path):
        """gen_outline_part2.py system prompt does NOT contain Vietnamese when lang=en."""
        system = self._capture_call_writer_system_prompt(
            "gen_outline_part2", "en", monkeypatch, tmp_path)
        assert "Vietnamese" not in system

    # -- gen_canon.py system prompt --

    def test_gen_canon_vi_instruction_in_system_prompt(self, monkeypatch, tmp_path):
        """gen_canon.py system prompt contains Vietnamese instruction when lang=vi."""
        system = self._capture_call_writer_system_prompt(
            "gen_canon", "vi", monkeypatch, tmp_path)
        assert "Vietnamese" in system
        assert "literary Vietnamese" in system

    def test_gen_canon_en_no_vi_instruction(self, monkeypatch, tmp_path):
        """gen_canon.py system prompt does NOT contain Vietnamese when lang=en."""
        system = self._capture_call_writer_system_prompt(
            "gen_canon", "en", monkeypatch, tmp_path)
        assert "Vietnamese" not in system


# ===========================================================================
# 3. Vietnamese text detection tests
# ===========================================================================


class TestVietnameseDetection:
    """Test the contains_vietnamese() helper function."""

    def test_detects_vietnamese_lower(self):
        """Detects lowercase Vietnamese diacritics."""
        assert contains_vietnamese("Đây là tiếng Việt") is True

    def test_detects_vietnamese_upper(self):
        """Detects uppercase Vietnamese diacritics."""
        assert contains_vietnamese("ĐÂY LÀ TIẾNG VIỆT") is True

    def test_detects_ă(self):
        assert contains_vietnamese("ăn cơm") is True

    def test_detects_â(self):
        assert contains_vietnamese("âm nhạc") is True

    def test_detects_đ(self):
        assert contains_vietnamese("đẹp") is True

    def test_detects_ê(self):
        assert contains_vietnamese("đê") is True

    def test_detects_ô(self):
        assert contains_vietnamese("ông") is True

    def test_detects_ơ(self):
        assert contains_vietnamese("cơm") is True

    def test_detects_ư(self):
        assert contains_vietnamese("tư duy") is True

    def test_english_returns_false(self):
        """English-only text returns False."""
        assert contains_vietnamese("The quick brown fox jumps over the lazy dog.") is False

    def test_empty_string_returns_false(self):
        assert contains_vietnamese("") is False

    def test_ascii_with_acute_returns_false(self):
        """Regular ASCII with common Latin accents (é, à) but no Viet-specific chars."""
        assert contains_vietnamese("café résumé naïve") is False

    def test_mixed_vietnamese_english_returns_true(self):
        """Mixed text with any Vietnamese char returns True."""
        assert contains_vietnamese("Hello đấy là test") is True


# ===========================================================================
# 4. Evaluation adaptation tests (validates S03 in context)
# ===========================================================================


class TestEvaluationAdaptation:
    """Verify that evaluation functions adapt to Vietnamese language mode."""

    def test_slop_score_vi_returns_empty_english_patterns(self, monkeypatch):
        """slop_score() with lang=vi returns empty English pattern lists."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        import evaluate as _eval
        importlib.reload(_eval)

        text = "The wizard delved into the tapestry of magic and synergy."
        result = _eval.slop_score(text)
        assert result["language"] == "vi"
        assert result["tier1_hits"] == []
        assert result["tier2_hits"] == []
        assert result["tier3_hits"] == []
        assert result["fiction_ai_tells"] == []
        assert result["structural_ai_tics"] == []
        assert result["telling_violations"] == 0

    def test_slop_score_en_detects_patterns(self, monkeypatch):
        """slop_score() with lang=en detects English slop patterns."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import evaluate as _eval
        importlib.reload(_eval)

        text = "The wizard delved into the tapestry of magic and synergy."
        result = _eval.slop_score(text)
        assert result["language"] == "en"
        assert len(result["tier1_hits"]) > 0

    def test_get_cross_checks_foundation_vi(self, monkeypatch):
        """_get_cross_checks('FOUNDATION') returns Vietnamese cross-checks when lang=vi."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        import evaluate as _eval
        importlib.reload(_eval)

        checks = _eval._get_cross_checks("FOUNDATION")
        assert "Vietnamese AI clichés" in checks
        assert "CULTURAL SPECIFICITY" in checks
        assert "PROSE NATURALNESS" in checks
        # Should NOT contain English-specific text
        assert "ANTI-SLOP" not in checks

    def test_get_cross_checks_foundation_en(self, monkeypatch):
        """_get_cross_checks('FOUNDATION') returns English cross-checks when lang=en."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import evaluate as _eval
        importlib.reload(_eval)

        checks = _eval._get_cross_checks("FOUNDATION")
        assert "ANTI-SLOP" in checks
        assert "Vietnamese AI clichés" not in checks

    def test_get_cross_checks_chapter_vi(self, monkeypatch):
        """_get_cross_checks('CHAPTER') returns Vietnamese cross-checks when lang=vi."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        import evaluate as _eval
        importlib.reload(_eval)

        checks = _eval._get_cross_checks("CHAPTER")
        assert "VIETNAMESE AI PATTERN CHECK" in checks
        assert "DIALOGUE NATURALNESS" in checks

    def test_get_cross_checks_chapter_en(self, monkeypatch):
        """_get_cross_checks('CHAPTER') returns English cross-checks when lang=en."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import evaluate as _eval
        importlib.reload(_eval)

        checks = _eval._get_cross_checks("CHAPTER")
        assert "DIALOGUE REALISM" in checks
        assert "VIETNAMESE AI PATTERN CHECK" not in checks


# ===========================================================================
# 5. State language field test (validates S04 in context)
# ===========================================================================


class TestStateLanguageField:
    """Verify that default_state() returns language='vi' when
    AUTONOVEL_LANGUAGE=vi."""

    def test_default_state_vi(self, monkeypatch):
        """default_state() with AUTONOVEL_LANGUAGE=vi returns language='vi'."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        import run_pipeline as rp
        importlib.reload(rp)
        state = rp.default_state()
        assert state["language"] == "vi"

    def test_default_state_en(self, monkeypatch):
        """default_state() with AUTONOVEL_LANGUAGE=en returns language='en'."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import run_pipeline as rp
        importlib.reload(rp)
        state = rp.default_state()
        assert state["language"] == "en"

    def test_default_state_has_language_key(self, monkeypatch):
        """default_state() always includes a 'language' key."""
        monkeypatch.delenv("AUTONOVEL_LANGUAGE", raising=False)
        import run_pipeline as rp
        importlib.reload(rp)
        state = rp.default_state()
        assert "language" in state


# ===========================================================================
# 6. End-to-end chain test (the main integration test)
# ===========================================================================


class TestEndToEndVietnameseFoundationChain:
    """Full end-to-end test: mock httpx.post to return fake Vietnamese
    content for each script, call run_foundation() with AUTONOVEL_LANGUAGE=vi,
    and verify all output files exist, are non-empty, and contain Vietnamese
    characters. Also verify state.json has language='vi'."""

    # Fake Vietnamese content for each script
    VI_WORLD = textwrap.dedent("""\
        # Kinh Thánh Thế Giới

        ## Vũ Trụ và Lịch Sử
        Cantamura là một thành phố cổ xưa nằm trong một thung lũng tự nhiên.
        Những tiếng chuông ngân vang khắp nơi, mỗi hồi chuông mang một ý nghĩa.

        ## Hệ Thống Ma Thuật
        Luật Âm Tonal có những quy tắc nghiêm ngặt. Mỗi âm giai có chi phí.
        Mỗi nốt nhạc đều có giới hạn của nó.
    """)

    VI_CHARACTERS = textwrap.dedent("""\
        # Sổ Đăng Ký Nhân Vật

        ## Cass Bellwright (nhân vật chính)
        Một cậu bé 14 tuổi với khả năng nghe thấy những âm thanh ẩn.
        Chồng chất wound/want/need/lie đầy đủ.

        ## Maret Corda (đối thủ)
        Không phải kẻ ác — một người có lợi ích xung đột với Cass.
    """)

    VI_OUTLINE_PART1 = textwrap.dedent("""\
        # Đề Cương Chương

        ## Hồi I

        ### Ch 1: Tiếng Chuông Đầu Tiên
        - **POV:** Cass, ngôi thứ ba hạn chế
        - **Vị trí:** Khu dân cư Bellwright
        - **Cung bậc cảm xúc:** Tò mò → lo âu
    """)

    VI_OUTLINE_PART2 = textwrap.dedent("""\
        ### Ch 18: Đêm Tối Của Linh Hồn

        Cass đối mặt với sự thật về cha mình. Những bí mật được tiết lộ.

        ## Bảng Dự Báo
        | # | Chủ đề | Gieo (Ch) | Thu hoạch (Ch) | Loại |
    """)

    VI_CANON = textwrap.dedent("""\
        # Quy Định Chuẩn

        ## Địa Lý
        - Cantamura nằm trong một thung lũng tự nhiên (world.md)
        - Có ít nhất 5 khu vực chính

        ## Nhân Vật
        - Cass Bellwright, 14 tuổi, có khả năng nghe âm thanh ẩn
        - Eddan Bellwright, cha của Cass, tay run khi nói về quá khứ
    """)

    def _fake_completed_process(self, stdout: str, returncode: int = 0):
        return MagicMock(
            returncode=returncode,
            stdout=stdout,
            stderr="",
        )

    def test_full_vietnamese_foundation_chain(self, tmp_path, monkeypatch):
        """Full foundation chain with AUTONOVEL_LANGUAGE=vi produces Vietnamese
        output files and correct state."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        import run_pipeline as rp
        importlib.reload(rp)

        # Set up mock uv_run that returns Vietnamese content per script
        script_outputs = {
            "gen_world.py": self.VI_WORLD,
            "gen_characters.py": self.VI_CHARACTERS,
            "gen_outline.py": self.VI_OUTLINE_PART1,
            "gen_outline_part2.py": self.VI_OUTLINE_PART2,
            "gen_canon.py": self.VI_CANON,
            "voice_fingerprint.py": "",
        }
        call_count = [0]

        def mock_uv_run(script, timeout=600):
            # Extract script name from the command "uv run python <script>"
            script_name = script.strip().split()[-1] if " " in script else script
            stdout = script_outputs.get(script_name, "")
            call_count[0] += 1
            if "evaluate.py" in script:
                return self._fake_completed_process(
                    "overall_score: 8.0\nlore_score: 7.5")
            return self._fake_completed_process(stdout)

        monkeypatch.setattr(rp, "uv_run", mock_uv_run)
        monkeypatch.setattr(rp, "git_add_commit", lambda *a, **kw: "abc1234")
        monkeypatch.setattr(rp, "git_reset_hard", lambda *a, **kw: None)

        # Override BASE_DIR and STATE_FILE to use tmp_path
        monkeypatch.setattr(rp, "BASE_DIR", tmp_path)
        monkeypatch.setattr(rp, "STATE_FILE", tmp_path / "state.json")

        # Create required directories
        (tmp_path / "chapters").mkdir(exist_ok=True)
        (tmp_path / "briefs").mkdir(exist_ok=True)
        (tmp_path / "edit_logs").mkdir(exist_ok=True)
        (tmp_path / "eval_logs").mkdir(exist_ok=True)

        state = {
            "phase": "foundation",
            "iteration": 0,
            "foundation_score": 0.0,
            "lore_score": 0.0,
            "language": "vi",
        }
        result_state = rp.run_foundation(state)

        # -- Verify all output files exist --
        assert (tmp_path / "world.md").exists(), "world.md not created"
        assert (tmp_path / "characters.md").exists(), "characters.md not created"
        assert (tmp_path / "outline.md").exists(), "outline.md not created"
        assert (tmp_path / "canon.md").exists(), "canon.md not created"

        # -- Verify all output files are non-empty --
        assert (tmp_path / "world.md").stat().st_size > 0
        assert (tmp_path / "characters.md").stat().st_size > 0
        assert (tmp_path / "outline.md").stat().st_size > 0
        assert (tmp_path / "canon.md").stat().st_size > 0

        # -- Verify Vietnamese characters in output files --
        world_text = (tmp_path / "world.md").read_text()
        assert contains_vietnamese(world_text), (
            f"world.md does not contain Vietnamese chars: {world_text[:200]}")

        chars_text = (tmp_path / "characters.md").read_text()
        assert contains_vietnamese(chars_text), (
            f"characters.md does not contain Vietnamese chars: {chars_text[:200]}")

        outline_text = (tmp_path / "outline.md").read_text()
        assert contains_vietnamese(outline_text), (
            f"outline.md does not contain Vietnamese chars: {outline_text[:200]}")

        canon_text = (tmp_path / "canon.md").read_text()
        assert contains_vietnamese(canon_text), (
            f"canon.md does not contain Vietnamese chars: {canon_text[:200]}")

        # -- Verify outline contains both parts --
        assert "Tiếng Chuông Đầu Tiên" in outline_text  # Part 1
        assert "Đêm Tối Của Linh Hồn" in outline_text  # Part 2

        # -- Verify language field preserved in state --
        assert result_state.get("language") == "vi", (
            f"Expected language='vi', got {result_state.get('language')}")

        # -- Verify state was updated correctly --
        assert result_state["foundation_score"] == 8.0
        assert result_state["phase"] == "drafting"

    def test_full_chain_english_no_vietnamese(self, tmp_path, monkeypatch):
        """Full foundation chain with AUTONOVEL_LANGUAGE=en produces output
        without Vietnamese characters."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import run_pipeline as rp
        importlib.reload(rp)

        en_world = "# World Bible\n\nA fantasy world with bells and tonal magic."
        en_chars = "# Characters\n\nCass Bellwright, 14, with a gift for hearing."
        en_outline = "# Outline\n\n## Act I\n\n### Ch 1: The First Bell"
        en_outline2 = "### Ch 18: Dark Night of the Soul"
        en_canon = "# Canon\n\n## Geography\n- Cantamura is in a natural valley."

        script_outputs = {
            "gen_world.py": en_world,
            "gen_characters.py": en_chars,
            "gen_outline.py": en_outline,
            "gen_outline_part2.py": en_outline2,
            "gen_canon.py": en_canon,
            "voice_fingerprint.py": "",
        }

        def mock_uv_run(script, timeout=600):
            script_name = script.strip().split()[-1] if " " in script else script
            if "evaluate.py" in script:
                return self._fake_completed_process(
                    "overall_score: 8.0\nlore_score: 7.5")
            return self._fake_completed_process(
                script_outputs.get(script_name, ""))

        monkeypatch.setattr(rp, "uv_run", mock_uv_run)
        monkeypatch.setattr(rp, "git_add_commit", lambda *a, **kw: "abc1234")
        monkeypatch.setattr(rp, "git_reset_hard", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "BASE_DIR", tmp_path)
        monkeypatch.setattr(rp, "STATE_FILE", tmp_path / "state.json")

        (tmp_path / "chapters").mkdir(exist_ok=True)
        (tmp_path / "briefs").mkdir(exist_ok=True)
        (tmp_path / "edit_logs").mkdir(exist_ok=True)
        (tmp_path / "eval_logs").mkdir(exist_ok=True)

        result_state = rp.run_foundation({
            "phase": "foundation", "iteration": 0,
            "foundation_score": 0.0, "lore_score": 0.0,
            "language": "en",
        })

        # English output should NOT contain Vietnamese-specific chars
        assert not contains_vietnamese(
            (tmp_path / "world.md").read_text())
        assert not contains_vietnamese(
            (tmp_path / "characters.md").read_text())

        # State should preserve language='en'
        assert result_state.get("language") == "en"


# ===========================================================================
# 7. Script execution logging tests
# ===========================================================================


class TestScriptExecutionLogging:
    """Verify that the pipeline logs which script is being tested and
    whether Vietnamese language instruction was found."""

    def test_step_logging_captures_script_names(self, tmp_path, monkeypatch, capsys):
        """run_foundation() logs each foundation script execution via step()."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "vi")
        import run_pipeline as rp
        importlib.reload(rp)

        calls = iter([
            self._fake_completed_process("# World content"),
            self._fake_completed_process("# Characters"),
            self._fake_completed_process("# Outline"),
            self._fake_completed_process("# Foreshadowing"),
            self._fake_completed_process("# Canon"),
            self._fake_completed_process(""),
            self._fake_completed_process("overall_score: 8.0\nlore_score: 7.5"),
        ])
        monkeypatch.setattr(rp, "uv_run", lambda *a, **kw: next(calls))
        monkeypatch.setattr(rp, "git_add_commit", lambda *a, **kw: "abc1234")
        monkeypatch.setattr(rp, "git_reset_hard", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "save_state", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "BASE_DIR", tmp_path)

        rp.run_foundation({"phase": "foundation", "iteration": 0,
                           "foundation_score": 0.0, "lore_score": 0.0})

        captured = capsys.readouterr()
        output = captured.out

        # Verify script names are logged
        assert "gen_world.py" in output or "world" in output.lower()
        assert "gen_characters.py" in output or "characters" in output.lower()
        assert "gen_outline.py" in output or "outline" in output.lower()
        assert "gen_canon.py" in output or "canon" in output.lower()
        assert "voice_fingerprint" in output.lower() or "voice" in output.lower()

    def _fake_completed_process(self, stdout: str, returncode: int = 0):
        return MagicMock(
            returncode=returncode,
            stdout=stdout,
            stderr="",
        )

    def test_file_size_logging(self, tmp_path, monkeypatch, capsys):
        """run_foundation() logs output file path and size for diagnosis."""
        monkeypatch.setenv("AUTONOVEL_LANGUAGE", "en")
        import run_pipeline as rp
        importlib.reload(rp)

        fake_world = "# World Bible\n\n" + "Content line.\n" * 50
        calls = iter([
            self._fake_completed_process(fake_world),
            self._fake_completed_process("# Characters"),
            self._fake_completed_process("# Outline"),
            self._fake_completed_process("# Foreshadowing"),
            self._fake_completed_process("# Canon"),
            self._fake_completed_process(""),
            self._fake_completed_process("overall_score: 8.0\nlore_score: 7.5"),
        ])
        monkeypatch.setattr(rp, "uv_run", lambda *a, **kw: next(calls))
        monkeypatch.setattr(rp, "git_add_commit", lambda *a, **kw: "abc1234")
        monkeypatch.setattr(rp, "git_reset_hard", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "save_state", lambda *a, **kw: None)
        monkeypatch.setattr(rp, "BASE_DIR", tmp_path)

        rp.run_foundation({"phase": "foundation", "iteration": 0,
                           "foundation_score": 0.0, "lore_score": 0.0})

        captured = capsys.readouterr()
        # Should log chars count for world.md
        assert "chars" in captured.out.lower() or "Saved" in captured.out
