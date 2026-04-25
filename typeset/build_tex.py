#!/usr/bin/env python3
"""Build LaTeX source from chapter files and novel metadata."""
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
NOVEL_METADATA_PATH = BASE_DIR / "typeset" / "novel_metadata.yaml"
NOVEL_TEMPLATE_PATH = BASE_DIR / "typeset" / "novel.tex.in"
NOVEL_OUTPUT_PATH = BASE_DIR / "typeset" / "novel.tex"

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

    return "\n".join(lines) + "\n\n"


# ---------------------------------------------------------------------------
# Novel metadata loading (lightweight YAML parse, no PyYAML dependency)
# ---------------------------------------------------------------------------

def _parse_simple_yaml(path: Path) -> dict:
    """Parse the novel_metadata.yaml file for string/list values.

    Handles ``key: value``, ``key: "quoted"``, and ``- item`` list entries
    under a top-level key.  Multi-line strings and nested maps are not
    supported — the file is kept intentionally flat.
    """
    data: dict = {}
    current_key: str | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        # Skip YAML front-matter markers and comments
        if stripped in ("---", "...") or stripped.startswith("#"):
            current_key = None
            continue

        # List item under current key
        if stripped.startswith("- ") and current_key is not None:
            val = stripped[2:].strip().strip('"').strip("'")
            if isinstance(data.get(current_key), list):
                data[current_key].append(val)
            else:
                data[current_key] = [val]
            continue

        # Top-level key: value
        m = re.match(r"^(\w+)\s*:\s*(.*)", stripped)
        if m:
            key, val = m.group(1), m.group(2).strip()
            current_key = key
            if val == "" or val.lower() == "null":
                data[key] = None
            else:
                data[key] = val.strip('"').strip("'")

    return data


def _parse_nested_yaml(path: Path) -> dict:
    """Parse novel_metadata.yaml with one level of nested mapping.

    Returns a dict where top-level keys may map to dicts (for blocks like
    ``copyright:``) or lists (for blocks like ``title_lines:``).
    """
    data: dict = {}
    current_top: str | None = None
    current_sub: str | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped in ("---", "..."):
            current_top = None
            current_sub = None
            continue

        # Comment lines don't reset the current block context
        if stripped.startswith("#"):
            continue

        indented = line != line.lstrip()

        # List item
        if stripped.startswith("- ") and current_top is not None:
            val = stripped[2:].strip()
            # Parse "key: value" list items (title_lines style)
            kv = re.match(r'^(\w+)\s*:\s*"?(.+?)"?$', val)
            if kv:
                if current_top not in data or data[current_top] is None:
                    data[current_top] = []
                if isinstance(data[current_top], list):
                    data[current_top].append({kv.group(1): kv.group(2).strip('"')})
            else:
                if current_top not in data or data[current_top] is None:
                    data[current_top] = []
                if isinstance(data[current_top], list):
                    data[current_top].append(val.strip('"').strip("'"))
            continue

        # Sub-key (one level of indent)
        m_sub = re.match(r"^(\s+)(\w+)\s*:\s*(.*)", line)
        if m_sub and current_top:
            sub_key = m_sub.group(2)
            sub_val = m_sub.group(3).strip()
            current_sub = sub_key
            if current_top not in data or not isinstance(data[current_top], dict):
                data[current_top] = {}
            if sub_val == "" or sub_val.lower() == "null":
                data[current_top][sub_key] = None
            else:
                data[current_top][sub_key] = sub_val.strip('"').strip("'")
            continue

        # Top-level key
        m_top = re.match(r"^(\w+)\s*:\s*(.*)", stripped)
        if m_top:
            current_top = m_top.group(1)
            current_sub = None
            val = m_top.group(2).strip()
            if val == "" or val.lower() == "null":
                data[current_top] = None
            else:
                data[current_top] = val.strip('"').strip("'")

    return data


def load_novel_metadata(path: Path = NOVEL_METADATA_PATH) -> dict:
    """Load and return the novel metadata from YAML."""
    if not path.exists():
        raise FileNotFoundError(
            f"Novel metadata file not found: {path}. "
            "Create typeset/novel_metadata.yaml (see novel_metadata.yaml for schema)."
        )
    return _parse_nested_yaml(path)


def _render_title_page_lines(title_lines: list[dict]) -> str:
    """Render the title page lines from metadata into LaTeX."""
    parts = []
    for entry in title_lines:
        if isinstance(entry, dict):
            for size, text in entry.items():
                if text and text.lower() != "null":
                    escaped = latex_escape(text)
                    parts.append(f"  {{\\{size}\\textsc{{{escaped}}}}}\\\\[0.15in]\n")
        elif isinstance(entry, str) and entry and entry.lower() != "null":
            escaped = latex_escape(entry)
            parts.append(f"  {{\\large\\textsc{{{escaped}}}}}\\\\[0.15in]\n")
    return "".join(parts)


def _render_epigraph_lines(epigraph: list[str] | None) -> tuple[str, str]:
    """Render epigraph lines and the full epigraph block.

    Returns (lines_tex, full_block_tex).  If epigraph is empty/None,
    both strings are empty (the epigraph page is omitted entirely).
    """
    if not epigraph:
        return "", ""

    lines = "".join(f"  {latex_escape(l)}\\\\\n" for l in epigraph)
    # Strip the trailing \\
    lines = lines.rstrip("\\\n") + "\\\\[12pt]\n"

    block = (
        "% Epigraph\n\\makeepigraph\n\n"
    )
    return lines, block


def _render_closing_block(closing_line: str | None) -> str:
    """Render the closing end-matter block."""
    if not closing_line:
        return ""
    escaped = latex_escape(closing_line)
    return (
        "\\thispagestyle{empty}\n"
        "\\vspace*{3in}\n"
        "\\begin{center}\n"
        "{\\small------\\quad$\\diamond$\\quad------}\\\\[0.3in]\n"
        f"{{\\small\\textit{{{escaped}}}}}\n"
        "\\end{center}\n"
    )


def generate_novel_tex(
    metadata: dict | None = None,
    lang: str | None = None,
    template_path: Path = NOVEL_TEMPLATE_PATH,
    output_path: Path = NOVEL_OUTPUT_PATH,
) -> Path:
    """Generate ``novel.tex`` from ``novel.tex.in`` template and metadata.

    Reads the ``.in`` template, substitutes ``{{PLACEHOLDER}}`` tokens with
    values from the metadata YAML, and writes the result.
    """
    if metadata is None:
        metadata = load_novel_metadata()
    if lang is None:
        lang = get_language()

    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path}. "
            "Expected typeset/novel.tex.in with {{PLACEHOLDER}} tokens."
        )

    template = template_path.read_text(encoding="utf-8")

    # --- Extract values from metadata ---
    title_lines = metadata.get("title_lines", [])
    if isinstance(title_lines, dict):
        title_lines = [title_lines]

    title_short = metadata.get("title_short", "")
    if isinstance(title_short, list):
        title_short = title_short[0] if title_short else ""

    author = metadata.get("author", "")
    if isinstance(author, list):
        author = author[0] if author else ""

    pdf_subject = metadata.get("pdf_subject", "")
    if isinstance(pdf_subject, list):
        pdf_subject = pdf_subject[0] if pdf_subject else ""

    epigraph = metadata.get("epigraph")
    if isinstance(epigraph, str):
        epigraph = [epigraph] if epigraph else []

    closing_line = metadata.get("closing_line")
    if isinstance(closing_line, list):
        closing_line = closing_line[0] if closing_line else None

    copyright_block = metadata.get("copyright", {})
    if isinstance(copyright_block, str):
        copyright_block = {}

    # --- Render template fragments ---
    title_page_tex = _render_title_page_lines(title_lines)
    epigraph_lines_tex, epigraph_block_tex = _render_epigraph_lines(epigraph)
    closing_block_tex = _render_closing_block(closing_line)

    # Babel package — include only for languages that need it
    if lang == "vi":
        babel = "\\usepackage[vietnamese]{babel}"
    else:
        babel = ""

    # --- Substitute placeholders ---
    result = template
    result = result.replace("{{BABEL_PACKAGE}}", babel)
    result = result.replace("{{TITLE_SHORT_LOWER}}", latex_escape(title_short.lower()))
    result = result.replace("{{TITLE_SHORT}}", latex_escape(title_short))
    result = result.replace("{{AUTHOR}}", latex_escape(author))
    result = result.replace("{{PDF_SUBJECT}}", latex_escape(pdf_subject))
    result = result.replace("{{TITLE_PAGE_LINES}}", title_page_tex)
    result = result.replace("{{EPIGRAPH_LINES}}", epigraph_lines_tex)
    result = result.replace("{{EPIGRAPH_BLOCK}}", epigraph_block_tex)
    result = result.replace("{{CLOSING_BLOCK}}", closing_block_tex)

    # Copyright block
    result = result.replace(
        "{{COPYRIGHT_NOTICE}}",
        latex_escape(copyright_block.get("notice", "")),
    )
    result = result.replace(
        "{{COPYRIGHT_CREATED_BY}}",
        latex_escape(copyright_block.get("created_by", "")),
    )
    result = result.replace(
        "{{COPYRIGHT_URL}}",
        latex_escape(copyright_block.get("url", "")),
    )
    result = result.replace(
        "{{COPYRIGHT_QR_IMAGE}}",
        copyright_block.get("url_qr_image", "../art/qr_bells.png"),
    )
    result = result.replace(
        "{{COPYRIGHT_LOGO_IMAGE}}",
        copyright_block.get("logo_image", "../art/pdf/nous_logo.pdf"),
    )

    output_path.write_text(result, encoding="utf-8")
    return output_path


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
    """Build novel.tex and chapters_content.tex from metadata and chapter markdown."""
    lang = get_language()

    # Generate novel.tex from template + metadata
    tex_path = generate_novel_tex(lang=lang)
    print(f"Wrote {tex_path}")

    # Patch epub metadata language
    patch_epub_metadata()

    # Build chapters_content.tex from chapter markdown files
    chapters_tex = []

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
                f"\\includegraphics[width=1.1in]{{{ornament_file}}}\n"
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
