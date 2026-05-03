#!/usr/bin/env python3
"""Scan manga/chapters/ and generate a LaTeX file for PDF compilation with tectonic.

Usage:
    python build_manga_tex.py                  # all chapters → manga_all.tex
    python build_manga_tex.py --part 1         # split into ~7-chapter parts
    python build_manga_tex.py --chapters 1-7   # explicit range
    python build_manga_tex.py --chapters 8-12  # chapters 8 through 12
    python build_manga_tex.py --part-size 5    # custom part size (default 7)

Output goes to typeset/manga_part{N}.tex (or manga_all.tex for no-part mode).
Then compile: cd typeset && tectonic manga_part1.tex
"""
import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
MANGA_CHAPTERS_DIR = PROJECT_ROOT / "manga" / "chapters"
TYPESET_DIR = PROJECT_ROOT / "typeset"

ROMAN = [
    "", "I", "II", "III", "IV", "V", "VI", "VII",
    "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV",
    "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII",
    "XXIII", "XXIV", "XXV", "XXVI", "XXVII", "XXVIII",
    "XXIX", "XXX",
]


def to_roman(n: int) -> str:
    if 1 <= n < len(ROMAN):
        return ROMAN[n]
    return str(n)


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------
def scan_chapters(directory: Path) -> dict[int, list[Path]]:
    """Return {chapter_num: [sorted panel paths]} from manga/chapters/."""
    chapters: dict[int, list[Path]] = defaultdict(list)
    pattern = re.compile(r"^ch(\d+)_(\d+)\.(png|jpg|jpeg)$", re.IGNORECASE)

    for f in sorted(directory.iterdir()):
        m = pattern.match(f.name)
        if not m:
            continue
        ch_num = int(m.group(1))
        chapters[ch_num].append(f)

    # Sort panels within each chapter
    for ch_num in chapters:
        chapters[ch_num].sort()

    return dict(sorted(chapters.items()))


# ---------------------------------------------------------------------------
# LaTeX generation
# ---------------------------------------------------------------------------
LATEX_HEADER = r"""\documentclass[openany]{book}

% A5 portrait — matches 2:3 manga panel ratio
\usepackage[
  paperwidth=5.83in,
  paperheight=8.27in,
  margin=0pt,
]{geometry}

\usepackage{graphicx}
\usepackage{hyperref}
\hypersetup{
  pdftitle={{{PDF_TITLE}}},
  pdfauthor={Duy Tom},
  pdfsubject={manga},
  hidelinks,
  pdfstartview=Fit,
}
\pagestyle{empty}

\begin{document}
"""

COVER_TEMPLATE = r"""
% === COVER ===
\thispagestyle{empty}
\vspace*{\fill}
\begin{center}
{\fontsize{28}{34}\selectfont\textsc{Những Người Tình}}\\[0.12in]
{\fontsize{14}{18}\selectfont\textsc{của}}\\[0.12in]
{\fontsize{28}{34}\selectfont\textsc{Mưa}}\\[0.3in]
{\small------\quad$\diamond$\quad------}\\[0.4in]
{\Large\textit{{{PART_LABEL}}}}\\[0.15in]
{\small {CHAPTER_RANGE}}\\[0.6in]
{\normalsize\textsc{Manga Edition}}\\[0.5in]
{\large\textsc{Duy Tom}}
\end{center}
\vspace*{\fill}
\clearpage
"""

CHAPTER_DIVIDER = r"""
% --- {roman_label} ---
\newpage
\thispagestyle{empty}
\vspace*{\fill}
\begin{center}
{\Large\textsc{{{roman_label}}}}
\end{center}
\vspace*{\fill}
\clearpage
"""

PANEL_PAGE = r"""
\newpage
\thispagestyle{empty}
\noindent\includegraphics[width=\paperwidth,height=\paperheight]{{{rel_path}}}
\clearpage
"""

COLOPHON = r"""
% === COLOPHON ===
\newpage
\thispagestyle{empty}
\vspace*{\fill}
\begin{center}
{\small--- Hết {part_label} ---}\\[0.3in]
{\small\textit{Những Người Tình của Mưa}}\\[0.1in]
{\small\textsc{Duy Tom}}\\[0.4in]
{\footnotesize Manga panels generated with AI assistance}
\end{center}
\vspace*{\fill}
\end{document}
"""


def generate_tex(
    chapters: dict[int, list[Path]],
    part_label: str,
    pdf_title: str,
    output_path: Path,
) -> Path:
    """Generate a .tex file from scanned chapters."""
    if not chapters:
        print(f"No chapters to write for {part_label}", file=sys.stderr)
        return output_path

    ch_nums = sorted(chapters.keys())
    first_ch, last_ch = ch_nums[0], ch_nums[-1]
    total_panels = sum(len(v) for v in chapters.values())

    # Chapter range label
    if first_ch == last_ch:
        ch_range = f"Chương {to_roman(first_ch)}"
    else:
        ch_range = f"Chương {to_roman(first_ch)}\\,--\\,{to_roman(last_ch)}"

    lines: list[str] = []

    # Header
    lines.append(LATEX_HEADER.replace("{PDF_TITLE}", pdf_title))

    # Cover
    lines.append(COVER_TEMPLATE.replace("{PART_LABEL}", part_label).replace("{CHAPTER_RANGE}", ch_range))

    # Chapters + panels
    for ch_num in ch_nums:
        roman = f"Chương {to_roman(ch_num)}"
        lines.append(CHAPTER_DIVIDER.replace("{roman_label}", roman))

        for panel_path in chapters[ch_num]:
            # Relative path from typeset/ to manga/chapters/
            rel = Path("..") / panel_path.relative_to(PROJECT_ROOT)
            lines.append(PANEL_PAGE.replace("{rel_path}", str(rel)))

    # Colophon
    lines.append(COLOPHON.replace("{part_label}", part_label))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(lines), encoding="utf-8")

    print(f"  {part_label}: {len(ch_nums)} chapters, {total_panels} panels → {output_path.name}")
    return output_path


# ---------------------------------------------------------------------------
# Splitting into parts
# ---------------------------------------------------------------------------
def split_into_parts(
    chapters: dict[int, list[Path]],
    part_size: int,
) -> list[tuple[str, dict[int, list[Path]]]]:
    """Split chapters into parts of roughly `part_size` chapters each."""
    ch_nums = sorted(chapters.keys())
    parts = []
    for i in range(0, len(ch_nums), part_size):
        chunk = ch_nums[i : i + part_size]
        part_num = i // part_size + 1
        part_chapters = {n: chapters[n] for n in chunk}
        parts.append((f"Phần {part_num}", part_chapters))
    return parts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate LaTeX files from manga/chapters/*.png"
    )
    parser.add_argument(
        "--chapters",
        metavar="START-END",
        help="Chapter range, e.g. 1-7 or 8-12 (default: all)",
    )
    parser.add_argument(
        "--part",
        action="store_true",
        help="Split into ~7-chapter parts (use --part-size to customize)",
    )
    parser.add_argument(
        "--part-size",
        type=int,
        default=7,
        help="Chapters per part when --part is used (default: 7)",
    )
    parser.add_argument(
        "--output",
        metavar="NAME",
        help="Output filename (without .tex). Default: auto from chapter range",
    )
    args = parser.parse_args()

    if not MANGA_CHAPTERS_DIR.exists():
        print(f"Error: {MANGA_CHAPTERS_DIR} not found", file=sys.stderr)
        sys.exit(1)

    chapters = scan_chapters(MANGA_CHAPTERS_DIR)
    if not chapters:
        print("No panel images found in manga/chapters/", file=sys.stderr)
        sys.exit(1)

    all_nums = sorted(chapters.keys())
    print(f"Found {len(all_nums)} chapters ({all_nums[0]}–{all_nums[-1]}), "
          f"{sum(len(v) for v in chapters.values())} panels total")

    # Filter by --chapters range
    if args.chapters:
        parts = args.chapters.split("-")
        start, end = int(parts[0]), int(parts[1])
        chapters = {n: chapters[n] for n in sorted(chapters) if start <= n <= end}
        if not chapters:
            print(f"No chapters found in range {start}–{end}", file=sys.stderr)
            sys.exit(1)

    # Decide how to output
    if args.part:
        parts = split_into_parts(chapters, args.part_size)
    else:
        # Single file
        ch_nums = sorted(chapters.keys())
        label = "Phần 1" if len(ch_nums) == len(all_nums) else None
        if not label:
            first_r = to_roman(ch_nums[0])
            last_r = to_roman(ch_nums[-1])
            label = f"Ch. {first_r}–{last_r}"
        parts = [(label, chapters)]

    print(f"\nGenerating {len(parts)} .tex file(s):\n")

    for idx, (label, ch_map) in enumerate(parts):
        ch_nums = sorted(ch_map.keys())

        # Output filename
        if args.output and len(parts) == 1:
            filename = f"{args.output}.tex"
        elif len(parts) > 1:
            filename = f"manga_part{idx + 1}.tex"
        else:
            filename = f"manga_part1.tex"

        out_path = TYPESET_DIR / filename
        pdf_title = f"Những Người Tình của Mưa — {label} (Manga)"
        generate_tex(ch_map, label, pdf_title, out_path)

    print("\nDone. Compile with:")
    for idx in range(len(parts)):
        name = args.output if args.output and len(parts) == 1 else f"manga_part{idx + 1}"
        print(f"  cd typeset && tectonic {name}.tex")


if __name__ == "__main__":
    main()
