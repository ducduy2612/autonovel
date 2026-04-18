# Art & PDF Guide

## Art Generation

**Budget:** 10,000 neurons/day (Cloudflare free tier).

```bash
# Check cost estimates before generating
python3 gen_art.py budget

# Step 1: Derive visual style from world + voice
python3 gen_art.py style

# Step 2: Generate variants, pick one
python3 gen_art.py curate cover --n=4
python3 gen_art.py pick cover 2

python3 gen_art.py curate ornament --n=4
python3 gen_art.py pick ornament 3

# Step 3: Batch generation (after picking references)
python3 gen_art.py ornaments-all        # one ornament per chapter
python3 gen_art.py scene-break           # decorative scene break
python3 gen_art.py curate map --n=3      # map illustration
python3 gen_art.py pick map 1

# Step 4: Vectorize ornaments to SVG
python3 gen_art.py vectorize

# Or run everything interactively (stops at human pick points)
python3 gen_art.py all
```

### File locations

| File | Purpose |
|---|---|
| `art/visual_style.json` | AI-derived art style (colors, mood, concepts) |
| `art/variants/` | All generated variants before picking |
| `art/cover.png` | Final cover (picked from variants) |
| `art/ornament_reference.png` | Reference style for chapter ornaments |
| `art/ornament_ch01.png` .. `ch24.png` | Per-chapter ornaments |
| `art/scene_break.png` | Scene break decoration |
| `art/map.png` | Map frontispiece (picked from variants) |
| `art/svg/` | Vectorized ornaments (from `vectorize` command) |
| `art/picks.json` | Tracks which variant was picked |

---

## PDF Export

The PDF is built in **two steps**. Never edit `novel.tex` directly — it gets overwritten.

```
novel.tex.in           ← template with {{PLACEHOLDER}} tokens (edit this)
novel_metadata.yaml    ← title, author, copyright, epigraph (edit this)
chapters/ch_*.md       ← chapter content
         ↓
   build_tex.py        ← substitutes metadata + converts markdown → LaTeX
         ↓
novel.tex              ← generated (never hand-edit)
chapters_content.tex   ← generated (never hand-edit)
         ↓
   tectonic            ← compiles LaTeX → PDF
         ↓
typeset/novel.pdf      ← final output
```

### Build commands

```bash
# Step 1: Generate LaTeX from template + chapters
python3 typeset/build_tex.py

# Step 2: Compile to PDF
tectonic typeset/novel.tex

# One-liner
python3 typeset/build_tex.py && tectonic typeset/novel.tex
```

Output: `typeset/novel.pdf`

### When to re-run build_tex.py

- Changed `novel_metadata.yaml` (title, author, copyright, epigraph)
- Changed `novel.tex.in` (layout, fonts, page structure)
- Changed chapter markdown files (`chapters/ch_*.md`)
- Changed art files (cover, ornaments, map, scene break)

### Editing novel_metadata.yaml

This is the **only file you edit** for book-specific metadata. Fields:

```yaml
title_lines:          # Title page display — each line has a LaTeX font size
  - Huge: "First Line"
  - small: "middle word"
  - Huge: "Second Line"

title_short: "Full Title"       # Half-title page, PDF metadata, running headers
author: "Author Name"           # Title page + PDF metadata
pdf_subject: "Genre"            # PDF subject tag

epigraph:                        # One string per line. Empty [] = skip.
  - "Quote line 1"
  - "— Attribution"

closing_line: "Last line of the book"  # Empty = skip

copyright:
  notice: "Copyright notice text"
  created_by: "created by ..."
  url: "https://..."
  url_qr_image: "../art/variants/ornament_03.png"
  logo_image: "../art/variants/ornament_01.png"
```

### PDF page order

1. Cover (full bleed) — `art/cover.png`
2. Half title
3. Title page — from `title_lines`
4. Copyright — from `copyright` block
5. Epigraph — from `epigraph` list (skipped if empty)
6. **Map** — `art/map.png` (skipped if file doesn't exist)
7. Blank verso
8. Chapters (with ornaments + scene breaks)
9. End matter

---

## Quick reference

```bash
# Full art pipeline (interactive — stops for human picks)
python3 gen_art.py all

# Build and export PDF
python3 typeset/build_tex.py && tectonic typeset/novel.tex

# Check neuron budget
python3 gen_art.py budget

# Archive current art before regenerating
python3 gen_art.py archive
```
