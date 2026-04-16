#!/usr/bin/env python3
"""Build LaTeX source from chapter files."""
import re
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve project root so we can import config regardless of cwd
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from config import get_language, BASE_DIR, CHAPTERS_DIR as CONFIG_CHAPTERS_DIR

CHAPTERS_DIR = str(CONFIG_CHAPTERS_DIR)
OUT_DIR = str(BASE_DIR / "typeset")
EPUB_METADATA_PATH = BASE_DIR / "typeset" / "epub_metadata.yaml"

def latex_escape(t):
    t = t.replace('&', '\\&')
    t = t.replace('%', '\\%')
    t = t.replace('$', '\\$')
    t = t.replace('#', '\\#')
    t = t.replace('_', '\\_')
    return t

def md_to_latex(body):
    result = []
    for line in body.split('\n'):
        s = line.strip()
        if s == '---':
            result.append('\n\\scenebreak\n')
        elif s == '':
            result.append('')
        else:
            s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\\textit{\1}', s)
            s = latex_escape(s)
            s = s.replace('\u2014', '---')
            s = s.replace('\u2013', '--')
            s = s.replace('\u201c', '``')
            s = s.replace('\u201d', "''")
            s = s.replace('\u2018', '`')
            s = s.replace('\u2019', "'")
            s = s.replace('\u2026', '\\ldots{}')
            # Convert straight ASCII quotes to LaTeX open/close
            # " at start of line or after space/punctuation = open (``)
            # " elsewhere = close ('')
            s = re.sub(r'(?<=\s)"(?=\w)', '``', s)    # space then "word
            s = re.sub(r'^"(?=\w)', '``', s)            # line-start "word
            s = re.sub(r'(?<=\w)"(?=[\s.,;:!?\-])', "''", s)  # word" then punct/space
            s = re.sub(r'(?<=\w)"$', "''", s)           # word" at line-end
            s = re.sub(r'(?<=[\.\?\!])"', "''", s)      # punctuation" 
            # Catch any remaining straight quotes (open if after space, close otherwise)
            s = re.sub(r'(?<=\s)"', '``', s)
            s = re.sub(r'"(?=\s)', "''", s)
            s = re.sub(r'^"', '``', s)
            result.append(s)
    return '\n'.join(result)

def make_drop_cap(latex_body):
    """Extract first paragraph and wrap first letter in lettrine."""
    lines = latex_body.split('\n')
    first_para = []
    rest_start = 0
    found = False
    
    for i, l in enumerate(lines):
        if not found and l.strip():
            found = True
        if found:
            if l.strip() == '' or l.strip().startswith('\\scenebreak'):
                rest_start = i
                break
            first_para.append(l)
        else:
            rest_start = i + 1
    
    if not first_para:
        return latex_body
    
    para_text = ' '.join(first_para)
    rest = '\n'.join(lines[rest_start:])
    
    if len(para_text) < 2:
        return latex_body
    
    first_letter = para_text[0]
    after_first = para_text[1:]
    
    # Find the rest of the first word to put in the lettrine second arg
    # e.g. "Cass was awake" -> lettrine{C}{ass} was awake
    space_idx = after_first.find(' ')
    if space_idx > 0:
        word_rest = after_first[:space_idx]
        para_rest = after_first[space_idx:]
    else:
        word_rest = after_first
        para_rest = ""
    
    drop = f"\\lettrine[lines=2, lhang=0.1, nindent=0.2em]{{{first_letter}}}{{{word_rest}}}{para_rest}"
    return drop + '\n\n' + rest

# ---------------------------------------------------------------------------
# Epub metadata language patching
# ---------------------------------------------------------------------------

def patch_epub_metadata(metadata_path: Path = EPUB_METADATA_PATH,
                        lang: str | None = None) -> None:
    """Update the ``lang`` field in *epub_metadata.yaml* to match the
    configured pipeline language.

    Reads the YAML file as plain text (avoids a PyYAML dependency),
    replaces the ``lang:`` line, and writes it back.
    """
    if lang is None:
        lang = get_language()

    if not metadata_path.exists():
        return

    text = metadata_path.read_text(encoding="utf-8")
    new_text = re.sub(r'^lang:\s*\S+', f'lang: {lang}', text, flags=re.MULTILINE)

    if new_text != text:
        metadata_path.write_text(new_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# LaTeX header generation with conditional babel support
# ---------------------------------------------------------------------------

def generate_latex_header(lang: str | None = None) -> str:
    """Return a LaTeX header block for chapters_content.tex.

    When *lang* is ``'vi'``, the header includes
    ``\\usepackage[vietnamese]{babel}`` for proper hyphenation and
    localisation.  For all other languages the header is minimal.
    """
    if lang is None:
        lang = get_language()

    lines = [
        "%% Auto-generated by build_tex.py — do not edit by hand",
        "%% Language: " + lang,
    ]

    if lang == "vi":
        lines.append("\\usepackage[vietnamese]{babel}")

    return "\n".join(lines) + "\n\n"


def discover_chapters() -> list[int]:
    """Return sorted list of chapter numbers from files on disk."""
    import re as _re
    nums = []
    chapters_glob = sorted(Path(CHAPTERS_DIR).glob("ch_*.md"))
    for p in chapters_glob:
        m = _re.match(r"ch_(\d+)", p.name)
        if m:
            nums.append(int(m.group(1)))
    return sorted(nums)


def main():
    """Build chapters_content.tex from chapter markdown files."""
    chapters_tex = []

    # Patch epub metadata language before generating content
    patch_epub_metadata()

    for n in discover_chapters():
        path = os.path.join(CHAPTERS_DIR, f"ch_{n:02d}.md")
        with open(path) as f:
            text = f.read()
        
        lines = text.strip().split('\n')
        title_line = lines[0].lstrip('# ').strip()
        body = '\n'.join(lines[1:]).strip()
        
        if ': ' in title_line:
            label, subtitle = title_line.split(': ', 1)
        else:
            label, subtitle = title_line, ""
        
        chapter_name = subtitle if subtitle else label
        latex_body = md_to_latex(body)
        latex_body = make_drop_cap(latex_body)
        
        # Check for chapter ornament (prefer vector PDF over raster PNG)
        art_base = os.path.dirname(CHAPTERS_DIR)
        pdf_path = os.path.join(art_base, "art", "pdf", f"ornament_ch{n:02d}.pdf")
        png_path = os.path.join(art_base, "art", f"ornament_ch{n:02d}.png")
        ornament_tex = ""
        ornament_file = None
        if os.path.exists(pdf_path):
            ornament_file = pdf_path
        elif os.path.exists(png_path):
            ornament_file = png_path
        if ornament_file:
            ornament_tex = (
                f"\\begin{{center}}\n"
                f"\\includegraphics[width=0.8in]{{{ornament_file}}}\n"
                f"\\end{{center}}\n"
                f"\\vspace{{0.15in}}\n"
            )
        
        chapters_tex.append(f"\\chapter{{{latex_escape(chapter_name)}}}\n\n{ornament_tex}{latex_body}\n")
        print(f"  {n:2d}. {title_line}")

    content = '\n\\clearpage\n\n'.join(chapters_tex)

    header = generate_latex_header()
    with open(os.path.join(OUT_DIR, "chapters_content.tex"), 'w') as f:
        f.write(header + content)

    print(f"\nWrote {len(chapters_tex)} chapters to typeset/chapters_content.tex")


if __name__ == "__main__":
    main()
