# Publishing Manga PDF from Chapter PNGs

Compile manga panel images in `manga/chapters/` into print-ready PDFs via `build_manga_tex.py` + Tectonic.

---

## Prerequisites

```bash
# Install tectonic (one-time)
curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh
```

## File Layout

```
manga/
  chapters/
    ch01_1.png          # ch{NN}_{page}.png — 1024×1536 portrait panels
    ch01_2.png
    ...
build_manga_tex.py      # Generates .tex from whatever's in manga/chapters/
typeset/
  manga_part1.tex       # Generated LaTeX
  manga_part1.pdf       # Compiled PDF
```

---

## Usage

All commands run from the project root.

### Everything in one PDF

```bash
python build_manga_tex.py
```

### Specific chapter range

```bash
python build_manga_tex.py --chapters 1-7
python build_manga_tex.py --chapters 8-12
```

### Auto-split into parts

```bash
python build_manga_tex.py --part            # 7 chapters per part (default)
python build_manga_tex.py --part --part-size 5
```

### Custom output name

```bash
python build_manga_tex.py --chapters 1-7 --output manga_part1
```

### Compile

```bash
cd typeset && tectonic manga_part1.tex
```

The script prints the compile commands at the end of each run.

---

## How It Works

1. **Scans** `manga/chapters/` for files matching `ch{NN}_{M}.png`
2. **Groups** by chapter number, sorts panels within each chapter
3. **Generates** LaTeX with:
   - Cover page (title + part label + chapter range)
   - Per-chapter divider page (Roman numerals)
   - Full-bleed panel pages (one image per page, zero margins)
   - Colophon
4. **Tectonic** compiles `.tex` → `.pdf`

No manual editing needed — add or remove PNGs in `manga/chapters/`, re-run the script.

---

## Notes

- **Page size**: A5 (5.83×8.27 in) matches the 2:3 panel aspect ratio
- **Full-bleed**: `margin=0pt` + `width=\paperwidth,height=\paperheight` — panels fill the entire page
- **Warnings**: `Underfull \vbox` on chapter dividers is cosmetic (sparse page)
- **Compression**: Output is ~2.2 MB/panel. For web distribution:
  ```bash
  gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -dNOPAUSE -dBATCH -sOutputFile=compressed.pdf manga_part1.pdf
  ```
