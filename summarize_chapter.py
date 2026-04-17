#!/usr/bin/env python3
"""Generate a ~200 word summary of a chapter for downstream context.
Usage: uv run python summarize_chapter.py 1
"""
import sys
from run_pipeline import generate_chapter_summary

ch = int(sys.argv[1])
ok = generate_chapter_summary(ch)
print(f"Chapter {ch} summary: {'saved' if ok else 'skipped (no chapter file)'}")
