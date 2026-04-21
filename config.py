#!/usr/bin/env python3
"""
Shared configuration module for the autonovel pipeline.

Centralizes all environment variable reading so scripts don't duplicate
load_dotenv() calls and env var names. Import what you need:

    from config import get_language, API_KEY, WRITER_MODEL
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Bootstrap: load .env once at import time
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# API credentials
# ---------------------------------------------------------------------------
API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
GEMINI_KEY: str = os.environ.get("GEMINI_API_KEY", "")
ELEVENLABS_KEY: str = os.environ.get("ELEVENLABS_API_KEY", "")
CF_API_KEY: str = os.environ.get("CLOUDFLARE_API_KEY", "")
CF_ACCOUNT_ID: str = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")

# ---------------------------------------------------------------------------
# Model names
# ---------------------------------------------------------------------------
WRITER_MODEL: str = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
JUDGE_MODEL: str = os.environ.get("AUTONOVEL_JUDGE_MODEL", "claude-sonnet-4-6")
REVIEW_MODEL: str = os.environ.get("AUTONOVEL_REVIEW_MODEL", "claude-opus-4-6")

# ---------------------------------------------------------------------------
# API base URL
# ---------------------------------------------------------------------------
API_BASE: str = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")

# Z.AI Coding Plan endpoint (OpenAI-compatible)
ZAI_CODING_BASE: str = os.environ.get(
    "AUTONOVEL_ZAI_CODING_BASE", "https://api.z.ai/api/coding/paas/v4"
)

# ---------------------------------------------------------------------------
# Timeouts (seconds)
# ---------------------------------------------------------------------------
API_TIMEOUT: int = int(os.environ.get("AUTONOVEL_API_TIMEOUT", "600"))
"""Default timeout for a single LLM API call (httpx request)."""

SUBPROCESS_TIMEOUT: int = int(os.environ.get("AUTONOVEL_SUBPROCESS_TIMEOUT", "600"))
"""Default timeout for pipeline subprocess invocations (uv run python ...)."""

# ---------------------------------------------------------------------------
# Directory constants
# ---------------------------------------------------------------------------
CHAPTERS_DIR: Path = BASE_DIR / "chapters"

# ---------------------------------------------------------------------------
# Language support
# ---------------------------------------------------------------------------
_SUPPORTED_LANGUAGES = {"en", "vi"}


def get_language() -> str:
    """Return the pipeline language code (e.g. ``'en'``, ``'vi'``).

    Reads ``AUTONOVEL_LANGUAGE`` from the environment.  Defaults to
    ``'en'`` for backward compatibility.  Prints a warning to *stderr*
    when the value is not in the supported set so misconfiguration is
    visible in logs.
    """
    lang = os.environ.get("AUTONOVEL_LANGUAGE", "en")
    if lang not in _SUPPORTED_LANGUAGES:
        print(
            f"WARNING: AUTONOVEL_LANGUAGE='{lang}' is not in the supported set "
            f"{sorted(_SUPPORTED_LANGUAGES)}. Defaulting to 'en'.",
            file=sys.stderr,
        )
        return "en"
    return lang


# ---------------------------------------------------------------------------
# Language-aware prompt helpers
# ---------------------------------------------------------------------------

_VI_CREATIVE_INSTRUCTION = (
    "Write all prose, descriptions, dialogue, and narrative in natural, "
    "literary Vietnamese. Use authentic Vietnamese phrasing and idiom — "
    "avoid word-for-word translation from English."
)

_VI_WRITING_INSTRUCTIONS = """\
HƯỚNG DẪN VIẾT VĂN CHƯƠNG TIỂU THUYẾT:

1. Viết NGUYÊN CHƯƠNG, không cắt ngắn, không tóm tắt. Đích ~3.200 từ tiếng Việt.
2. Ngôi thứ ba, biết hạn chế, thì quá khứ, gắn chặt POV của {pov}.
   - "Biết hạn chế": người kể chỉ biết những gì {pov} biết, cảm thấy, nghĩ.
   - Dùng ngôn ngữ tự do gián tiếp: "Hương nhang trầm như thể một lời hứa cũ…"
     thay vì "Anh ấy nghĩ rằng…" hay "Cô ấy cảm thấy…"
3. Bám ĐÚNG từng beat trong dàn ý, theo đúng thứ tự.
4. Gieo TẤT CẢ các chi tiết tiền hoạ (foreshadowing) được yêu cầu.
5. Chi tiết giác quan cụ thể: {pov} nghe thấy gì, ngửi thấy gì, chạm vào gì.
   - KHÔNG dùng liệt kê ba kiểu "X. Y. Z." hay "X và Y và Z."
   - Kết hợp hai, cắt một, hoặc viết lại thành câu phức.
6. Hiện cảm xúc qua hành động, cử chỉ, chi tiết vật lý — KHÔNG kể cảm xúc.
   - TỐT: "Đầu ngón tay cô run trên mép chén trà."
   - XẤU: "Cô cảm thấy một sự lo âu dâng lên trong lòng."
   - XẤU: "Một cảm giác kỳ lạ xâm chiếm anh."
7. Lời thoại theo đúng cá tính và giọng nói đã định trong characters.md.
   - Nhân vật nói tự nhiên, đôi khi ngập ngừng, ngắt quãng, nói sai.
   - KHÔNG ai nói bằng câu văn trang trọng hoàn hảo.
8. Tuân thủ Part 1 guardrails trong voice.md.
9. TUYỆT ĐỐI KHÔNG dùng các "AI tells" trong tiếng Việt:
   - KHÔNG: "một cảm giác", "không thể không", "mắt mở lớn", "lồng ngực thắt lại",
     "hơi thở nghẹn lại", "trái tim đập thình thịch".
   - Thay thế bằng chi tiết cụ thể hoặc hành động vật lý.
10. Đa dạng độ dài câu. Câu ngắn để tạo nhịp dồn. Câu dài để miêu tả, xây dựng.
    Câu Việt Nam linh hoạt: có thể gộp chủ ngữ, lược đại từ, dùng câu đặc chủ ngữ.
11. Ẩn dụ và so sánh phải mọc từ thế giới của nhân vật — nghề nghiệp, ký ức, môi trường.
    Dùng hình ảnh quen thuộc với độc giả Việt Nam, KHÔNG phải bản dịch từ tiếng Anh.
12. Tin độc giả. KHÔNG giải thích ý nghĩa cảnh. Để cảnh tự lên tiếng.
13. Mở chương bằng một cảnh (in scene), KHÔNG bằng kể (exposition).
    Kết chương bằng một khoảnh khắc, KHÔNG bằng tóm tắt.

CÁC MẪU CẦN TRÁNH:
14. TUYỆT ĐỐI KHÔNG liệt kê ba giác quan liên tiếp.
15. TUYỆT ĐỐI KHÔNG dùng "Anh không [động từ]" hay "Cô không [động từ]"
    quá một lần mỗi chương. Chuyển sang cách diễn đạt tích cực hoặc cắt.
16. TUYỆT ĐỐI KHÔNG dùng "Anh nghĩ về [X]" hay "Cô nghĩ về [X]".
    Thay bằng: suy nghĩ trực tiếp dạng câuFragment, hành động vật lý, hoặc lời thoại.
17. TUYỆT ĐỐI KHÔNG lạm dụng so sánh "như cách [X] [Y]" quá hai lần mỗi chương.
18. KHÔNG giải thích lại cảnh vừa miêu tả. Tin cảnh.
19. Dấu phân cảnh (---) chỉ dùng khi chuyển thời gian/địa điểm thật sự.
    Tối đa 2 mỗi chương.
20. ĐA DẠNG độ dài đoạn văn. Không quá 3 đoạn liên tiếp cùng độ dài.
    Bắt buộc có ít nhất một đoạn 1-2 câu và một đoạn 6+ câu.
21. Kết chương khác mọi chương trước. Tìm kết thúc ĐÚNG cho chương này.
22. Có ít nhất một khoảnh khắc bất ngờ — nhân vật nói sai, cảm xúc đến sớm/trễ,
    chi tiết không theo khuôn mẫu.
23. ƯU TIÊN cảnh (scene) hơn kể (summary). Ít nhất 70% chương phải ở trong cảnh.
24. Lời thoại phải giống tiếng nói, KHÔNG giống văn viết.
    Nhân vật đôi khi ngập ngừng, ngắt lời, bỏ lửng, nói hơi sai.

QUY TẮC NGÔN NGỮ TIẾNG VIỆT:
25. Dùng từ thuần Việt hoặc từ Hán Việt đã Việt hóa tự nhiên.
    KHÔNG dùng từ mượn tiếng Anh khi có từ tương đương tiếng Việt.
26. Câu đặc chủ ngữ (topic-comment) là thế mạnh của tiếng Việt — tận dụng:
    "Căn phòng, tối." / "Bóng cây, đổ dài xuống đường."
27. Linh hoạt lược đại từ khi ngữ cảnh rõ: "Đi một mạch đến bến."
28. Dùng "được/bị" cho nghĩa thụ động một cách tự nhiên, không dịch từ bị động tiếng Anh.
29. Tránh câu quá dài nhiễm văn phong Anh (nhiều mệnh đề "that/which").
    Câu tiếng Việt nên ngắn gọn, chủ ngữ rõ, kết nối bằng ngữ cảnh.
30. Ngôn ngữ/xưng hô phù hợp bối cảnh và quan hệ nhân vật:
    anh/chị, thầy, chú, ngài, huynh đệ, ta/mày… theo đúng thế giới truyện."""

_VI_SYSTEM_PROMPT = (
    "Bạn là nhà văn văn học đang viết một chương tiểu thuyết fantasy bằng tiếng Việt. "
    "Bạn viết ngôi thứ ba biết hạn chế, thì quá khứ, gắn chặt một nhân vật POV. "
    "Bạn tuân thủ đúng voice definition. Bạn thực hiện mọi beat trong dàn ý. "
    "Bạn không dùng từ trong danh sách cấm. Bạn hiện cảm xúc, KHÔNG kể. "
    "Văn xuôi của bạn cụ thể, giác quan, đậm chất đời. Ẩn dụ mọc từ trải nghiệm nhân vật. "
    "Bạn đa dạng độ dài câu. Bạn tin độc giả. "
    "Bạn viết NGUYÊN CHƯƠNG — không cắt ngắn, không tóm tắt, không bỏ qua."
)

_VI_ANALYSIS_NOTE = (
    "The text you are analysing is written in Vietnamese. You may respond "
    "in English for analysis and commentary, but you MUST preserve all "
    "quoted Vietnamese prose exactly as written — do not translate or "
    "paraphrase quoted passages."
)


def language_instruction() -> str:
    """Return a creative-writing language instruction when the pipeline
    language is Vietnamese, otherwise an empty string.

    Append the result to the user prompt of any content-generating LLM
    call so the model writes in the target language.
    """
    if get_language() == "vi":
        return _VI_CREATIVE_INSTRUCTION
    return ""


def analysis_language_note() -> str:
    """Return a Vietnamese-awareness note when the pipeline language is
    Vietnamese, otherwise an empty string.

    Intended for evaluation / analysis prompts where the LLM should
    understand Vietnamese text but respond in English, preserving all
    quoted Vietnamese exactly.
    """
    if get_language() == "vi":
        return _VI_ANALYSIS_NOTE
    return ""


def vi_writing_instructions(pov: str = "nhân vật chính") -> str:
    """Return Vietnamese literary writing instructions when the pipeline
    language is Vietnamese, otherwise an empty string.

    The *pov* parameter is interpolated into the instructions so that
    POV-specific guidance reads naturally.  Returns an empty string for
    non-Vietnamese pipelines.
    """
    if get_language() == "vi":
        return _VI_WRITING_INSTRUCTIONS.format(pov=pov)
    return ""


def vi_system_prompt() -> str:
    """Return the Vietnamese-language system prompt when the pipeline
    language is Vietnamese, otherwise an empty string.

    Use this to replace the English system prompt in chapter-drafting
    and revision scripts so the LLM thinks in Vietnamese from the start.
    """
    if get_language() == "vi":
        return _VI_SYSTEM_PROMPT
    return ""
