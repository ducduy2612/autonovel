#!/usr/bin/env python3
"""
Generate novel art via Cloudflare Workers AI (Flux 2 Dev).

Uses CLOUDFLARE_API_KEY and CLOUDFLARE_ACCOUNT_ID from .env.
Model: @cf/black-forest-labs/flux-2-dev

Chapter ornaments use atmospheric scenes with characters as compositional
elements (silhouettes, back views, hands) — never faces — for visual
consistency across chapters.

Curation workflow (human-in-the-loop):
  python gen_art.py style                    # Derive visual style from world + voice
  python gen_art.py curate cover --n=4       # Generate 4 cover variants, pick one
  python gen_art.py curate ornament --n=4    # Generate 4 ornament style variants
  python gen_art.py pick cover 2             # Select variant #2 as final
  python gen_art.py pick ornament 3          # Select variant #3 as ornament reference

Batch generation (after picking reference style):
  python gen_art.py ornaments-all            # Generate all chapter scene ornaments
  python gen_art.py scene-break              # Generate scene break decoration
  python gen_art.py curate map --n=3         # Generate 3 map variants (lore-grounded)

Post-processing:
  python gen_art.py vectorize                # Convert ornaments + scene-break to SVG
  python gen_art.py vectorize ornament_ch01  # Vectorize a single image

Full pipeline:
  python gen_art.py all                      # style → curate → batch → vectorize

Safety:
  python gen_art.py archive                  # Zip current art/ to art/archive/<ts>.zip
"""
import os
import sys
import json
import re
import time
import shutil
import argparse
import subprocess
import base64
import zipfile
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env", override=True)

CF_API_KEY = os.environ.get("CLOUDFLARE_API_KEY", "")
CF_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
FLUX_MODEL = "@cf/black-forest-labs/flux-2-dev"

ART_DIR = BASE_DIR / "art"
VARIANTS_DIR = ART_DIR / "variants"
SVG_DIR = ART_DIR / "svg"
STYLE_FILE = ART_DIR / "visual_style.json"
PICKS_FILE = ART_DIR / "picks.json"

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")


# ============================================================
# API HELPERS — Cloudflare Workers AI (Flux 2 Dev)
# ============================================================

# Map aspect ratio labels to pixel dimensions for Flux.
# Flux generates up to ~4 megapixels; keep within reasonable bounds.
# Neuron budget: 10k/day. Pricing is per 512×512 tile per step:
#   18.75 neurons per INPUT tile per step (image edit mode)
#   37.50 neurons per OUTPUT tile per step
# All sizes aligned to multiples of 512 for predictable tile counts.
# Steps reduced from 25 to 12 — still good quality for Flux 2 Dev.
_ART_STEPS = 5

_ASPECT_SIZES = {
    "auto": (512, 512),
    "1:1": (512, 512),      # 1 tile — 37.5n/step
    "2:3": (512, 768),      # 1×1.5 tiles — 56.25n/step
    "3:4": (512, 768),      # same
    "4:3": (512, 512),      # crop later if needed — 1 tile
    "4:1": (512, 256),      # <1 tile — 37.5n/step
    "16:9": (512, 288),     # <1 tile — 37.5n/step
    "9:16": (512, 768),     # 1.5 tiles — 56.25n/step
}

FLUX_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}"
    f"/ai/run/{FLUX_MODEL}"
)


def _resolve_size(aspect_ratio, resolution="1K"):
    """Return (width, height) from an aspect ratio label.

    All base sizes are already aligned to 512px multiples.
    The 'resolution' param is accepted for backward compat but unused.
    """
    base_w, base_h = _ASPECT_SIZES.get(aspect_ratio, (512, 512))
    return base_w, base_h


NEURON_BUDGET_DAILY = int(os.environ.get("AUTONOVEL_NEURON_BUDGET", "10000"))
_neuron_session_used = 0  # track within this process invocation


def _estimate_neurons(width, height, steps, has_input_images=False):
    """Estimate neuron cost for a single generation call.

    Pricing per step:
      18.75 neurons per INPUT 512x512 tile
      37.50 neurons per OUTPUT 512x512 tile
    Tiles are ceil(dim / 512).
    """
    import math
    out_tiles = math.ceil(width / 512) * math.ceil(height / 512)
    cost_per_step = 37.50 * out_tiles
    if has_input_images:
        in_tiles = math.ceil(width / 512) * math.ceil(height / 512)
        cost_per_step += 18.75 * in_tiles
    return cost_per_step * steps


def _check_budget(cost, label=""):
    """Warn if this operation would exceed the daily neuron budget."""
    global _neuron_session_used
    remaining = NEURON_BUDGET_DAILY - _neuron_session_used
    if cost > remaining:
        print(f"\n  ⚠ BUDGET WARNING: {label} costs ~{cost:,.0f} neurons "
              f"but only {remaining:,} remaining today "
              f"(budget: {NEURON_BUDGET_DAILY:,}, used: {_neuron_session_used:,})")
        return False
    return True


def _spend_neurons(cost):
    """Record neuron spend after a successful API call."""
    global _neuron_session_used
    _neuron_session_used += cost


def _read_image_bytes(img_path):
    """Read raw bytes from a file path, data URI, or URL."""
    if isinstance(img_path, str) and img_path.startswith("data:"):
        _, b64data = img_path.split(",", 1)
        return base64.b64decode(b64data)
    p = Path(img_path)
    if p.exists():
        return p.read_bytes()
    import httpx
    resp = httpx.get(str(img_path), timeout=None, follow_redirects=True)
    resp.raise_for_status()
    return resp.content


def flux_generate(prompt, resolution="1K", aspect_ratio="auto", seed=None):
    """Generate an image from a text prompt via Cloudflare Flux.

    Returns (data_uri, description).
    """
    import httpx

    width, height = _resolve_size(aspect_ratio, resolution)
    cost = _estimate_neurons(width, height, _ART_STEPS, has_input_images=False)
    _check_budget(cost, f"generate {width}×{height}")
    print(f"    [~{cost:,.0f} neurons, {width}×{height}, {_ART_STEPS} steps]", end="")

    fields = {
        "prompt": (None, prompt),
        "width": (None, str(width)),
        "height": (None, str(height)),
        "steps": (None, str(_ART_STEPS)),
    }
    if seed is not None:
        fields["seed"] = (None, str(seed))

    resp = httpx.post(
        FLUX_URL,
        headers={"Authorization": f"Bearer {CF_API_KEY}"},
        files=fields,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    # Cloudflare wraps in {"success": true, "result": {"image": "<b64>"}}
    image_b64 = data.get("result", {}).get("image") or data.get("image", "")
    if not image_b64:
        errors = data.get("errors", [])
        raise RuntimeError(f"Flux API error: {errors or data}")

    _spend_neurons(cost)
    return f"data:image/png;base64,{image_b64}", ""


def flux_edit(prompt, image_paths, resolution="1K", aspect_ratio="1:1", seed=None):
    """Generate an image using reference image(s) via Flux multi-reference.

    Flux accepts up to 4 input images as input_image_0..input_image_3.
    Each image must be <= 512x512 pixels.
    Returns (data_uri, description).
    """
    import httpx

    width, height = _resolve_size(aspect_ratio, resolution)
    cost = _estimate_neurons(width, height, _ART_STEPS, has_input_images=True)
    _check_budget(cost, f"edit {width}×{height}")
    print(f"    [~{cost:,.0f} neurons, {width}×{height}, {_ART_STEPS} steps, +ref]", end="")

    fields = {
        "prompt": (None, prompt),
        "width": (None, str(width)),
        "height": (None, str(height)),
        "steps": (None, str(_ART_STEPS)),
    }
    if seed is not None:
        fields["seed"] = (None, str(seed))

    for idx, img_path in enumerate(image_paths[:4]):
        img_bytes = _read_image_bytes(img_path)
        fields[f"input_image_{idx}"] = ("reference.png", img_bytes, "image/png")

    resp = httpx.post(
        FLUX_URL,
        headers={"Authorization": f"Bearer {CF_API_KEY}"},
        files=fields,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    image_b64 = data.get("result", {}).get("image") or data.get("image", "")
    if not image_b64:
        errors = data.get("errors", [])
        raise RuntimeError(f"Flux API error: {errors or data}")

    _spend_neurons(cost)
    return f"data:image/png;base64,{image_b64}", ""


def download_image(url_or_data_uri, dest_path):
    """Download an image URL or decode a data URI and save to disk."""
    if url_or_data_uri.startswith("data:"):
        _, b64data = url_or_data_uri.split(",", 1)
        img_bytes = base64.b64decode(b64data)
    else:
        import httpx
        resp = httpx.get(url_or_data_uri, timeout=None, follow_redirects=True)
        resp.raise_for_status()
        img_bytes = resp.content
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(img_bytes)
    return len(img_bytes)


def call_claude(prompt, max_tokens=1500):
    import httpx
    resp = httpx.post(
        f"{ANTHROPIC_BASE}/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": WRITER_MODEL,
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=None,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def load_style():
    if not STYLE_FILE.exists():
        print("No visual style found. Run: gen_art.py style")
        sys.exit(1)
    return json.loads(STYLE_FILE.read_text())


def load_picks():
    if PICKS_FILE.exists():
        return json.loads(PICKS_FILE.read_text())
    return {}


def save_picks(picks):
    PICKS_FILE.write_text(json.dumps(picks, indent=2))


def get_reference_path(art_type):
    """Get the local file path of the picked reference image for a type."""
    picks = load_picks()
    if art_type in picks:
        p = picks[art_type].get("path", "")
        if p and Path(p).exists():
            return p
    return None


# ============================================================
# STYLE
# ============================================================

def cmd_style(args):
    world = (BASE_DIR / "world.md").read_text()[:5000]
    voice = (BASE_DIR / "voice.md").read_text()[:3000]
    title = "Unknown"
    outline = BASE_DIR / "outline.md"
    if outline.exists():
        title = outline.read_text().split("\n")[0].lstrip("# ").strip()

    prompt = f"""You are an art director designing the visual identity for a fantasy novel.

NOVEL TITLE: {title}

WORLD DESCRIPTION (excerpts):
{world}

VOICE/TONE:
{voice}

Define a VISUAL STYLE for all art in this novel. Output valid JSON:

{{
  "art_style": "one sentence describing illustration style",
  "color_palette": "5-7 specific colors",
  "texture": "dominant visual texture",
  "mood": "visual mood",
  "reference_artists": "2-3 real artists whose style approximates this",
  "cover_concept": "specific image for the cover — concrete, no spoilers",
  "ornament_concept": "what chapter ornaments should look like — symbolic, small",
  "scene_break_concept": "what goes between scenes — minimal, horizontal",
  "map_concept": "what the map shows and its style (if applicable)"
}}

JSON only."""

    print("Deriving visual style from world + voice...")
    result = call_claude(prompt)
    text = result.strip()
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    style = json.loads(text)

    ART_DIR.mkdir(exist_ok=True)
    STYLE_FILE.write_text(json.dumps(style, indent=2))

    print(f"\nVisual style saved to {STYLE_FILE}")
    for k, v in style.items():
        print(f"  {k}: {str(v)[:80]}")
    return style


# ============================================================
# CURATE: generate N variants, human picks
# ============================================================

def cmd_curate(args):
    style = load_style()
    art_type = args.art_type
    n = args.n

    VARIANTS_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate fundamentally different art directions via Claude
    from gen_art_directions import generate_directions

    world = ""
    if (BASE_DIR / "world.md").exists():
        world = (BASE_DIR / "world.md").read_text()[:3000]

    print(f"Generating {n} radically different {art_type} directions...")
    directions = generate_directions(art_type, style, n, world)

    # Resolution/aspect per type
    resolutions = {
        "cover": ("1K", "2:3"),
        "ornament": ("1K", "1:1"),
        "map": ("1K", "1:1"),
        "scene-break": ("1K", "4:1"),
    }
    resolution, aspect = resolutions.get(art_type, ("1K", "auto"))

    # Step 2: Generate one image per direction
    directions_log = []
    for i, d in enumerate(directions, 1):
        prompt = d["prompt"]
        # Append universal constraints
        if art_type == "cover":
            prompt += " No text, no title, no lettering. Pure illustration."
        elif art_type in ("ornament", "scene-break"):
            prompt += " White background. No text."

        label = d.get("direction", f"variant_{i}")
        print(f"\n  [{i}/{n}] {label.upper()}: {d.get('concept', '')[:80]}")
        print(f"    Medium: {d.get('medium', 'N/A')}")

        url, desc = flux_generate(prompt, resolution=resolution, aspect_ratio=aspect)
        dest = VARIANTS_DIR / f"{art_type}_{i:02d}.png"
        size = download_image(url, dest)

        # Cache URL and direction info
        picks = load_picks()
        picks[f"variant_{art_type}_{i}"] = {
            "url": url,
            "path": str(dest),
            "direction": label,
            "concept": d.get("concept", ""),
            "medium": d.get("medium", ""),
            "prompt": prompt,
        }
        save_picks(picks)

        directions_log.append({
            "num": i, "direction": label,
            "concept": d.get("concept", ""),
            "medium": d.get("medium", ""),
            "file": dest.name, "size": size,
        })

        print(f"    → {dest.name} ({size:,} bytes)")
        if i < n:
            time.sleep(1)

    # Save directions log for reference
    log_path = VARIANTS_DIR / f"{art_type}_directions.json"
    log_path.write_text(json.dumps(directions_log, indent=2))

    print(f"\n{'='*50}")
    print(f"{n} DIRECTIONS for {art_type}:")
    for d in directions_log:
        print(f"  {d['num']}. [{d['direction'].upper():12s}] {d['concept'][:60]}")
    print(f"\nFiles in: {VARIANTS_DIR}/")
    print(f"Pick one: gen_art.py pick {art_type} <number>")
    print(f"Details:  {log_path}")


def _extract_geography(world_text):
    """Extract location names and spatial relationships from world.md."""
    # Look for district/location names
    locations = []
    for pattern in [
        r'\*\*([^*]+)\*\*\s*[—–-]',  # **Name** — description
        r'###\s+(.+)',  # ### Section headers
    ]:
        for m in re.finditer(pattern, world_text):
            name = m.group(1).strip()
            if len(name) < 40 and not name.startswith("Note"):
                locations.append(name)

    # Also extract named places from text
    for pattern in [r'the ([A-Z][a-z]+ (?:Quarter|District|Tier|Line|Square|Tower|Settlement)s?)']:
        for m in re.finditer(pattern, world_text):
            loc = m.group(1)
            if loc not in locations:
                locations.append(loc)

    if locations:
        return ", ".join(locations[:15])
    return "the main city districts and landmarks described in the world bible"


def cmd_budget(args):
    """Show neuron budget status and cost estimates for each operation."""
    n_chapters = len(sorted(BASE_DIR.glob("chapters/ch_*.md")))
    n_cover = 4  # default --n for cover curate
    n_ornament = 4
    n_map = 3

    # Per-operation costs with current sizes and steps
    cover_cost = _estimate_neurons(512, 768, _ART_STEPS, False)
    ornament_cost = _estimate_neurons(512, 512, _ART_STEPS, False)
    ornament_edit_cost = _estimate_neurons(512, 512, _ART_STEPS, True)
    scene_break_cost = _estimate_neurons(512, 256, _ART_STEPS, False)
    map_cost = _estimate_neurons(512, 512, _ART_STEPS, False)

    total = (
        n_cover * cover_cost +
        n_ornament * ornament_cost +
        n_chapters * ornament_edit_cost +
        scene_break_cost +
        n_map * map_cost
    )

    print(f"Neuron budget: {NEURON_BUDGET_DAILY:,}/day")
    print(f"Session used:  {_neuron_session_used:,}")
    print(f"Remaining:     {NEURON_BUDGET_DAILY - _neuron_session_used:,}\n")

    print(f"Per-operation costs ({_ART_STEPS} steps):")
    print(f"  cover (512×768):           {cover_cost:>8,.0f} neurons")
    print(f"  ornament (512×512):        {ornament_cost:>8,.0f} neurons")
    print(f"  ornament +ref (512×512):   {ornament_edit_cost:>8,.0f} neurons")
    print(f"  scene-break (512×256):     {scene_break_cost:>8,.0f} neurons")
    print(f"  map (512×512):             {map_cost:>8,.0f} neurons")

    print(f"\nFull pipeline estimate ({n_chapters} chapters):")
    print(f"  {n_cover} cover variants:       {n_cover * cover_cost:>8,.0f}")
    print(f"  {n_ornament} ornament variants:   {n_ornament * ornament_cost:>8,.0f}")
    print(f"  {n_chapters} chapter ornaments:   {n_chapters * ornament_edit_cost:>8,.0f}")
    print(f"  1 scene break:          {scene_break_cost:>8,.0f}")
    print(f"  {n_map} map variants:         {n_map * map_cost:>8,.0f}")
    print(f"  {'─'*30}")
    print(f"  TOTAL:                  {total:>8,.0f} neurons")
    print(f"  Days needed:            {total / NEURON_BUDGET_DAILY:.1f} days")


# ============================================================
# PICK: select a variant as the final
# ============================================================

def cmd_pick(args):
    art_type = args.art_type
    number = args.number

    variant_path = VARIANTS_DIR / f"{art_type}_{number:02d}.png"
    if not variant_path.exists():
        print(f"Variant not found: {variant_path}")
        print(f"Available: {sorted(VARIANTS_DIR.glob(f'{art_type}_*.png'))}")
        sys.exit(1)

    # Copy to final location
    if art_type == "cover":
        final = ART_DIR / "cover.png"
    elif art_type == "ornament":
        final = ART_DIR / "ornament_reference.png"
    elif art_type == "map":
        final = ART_DIR / "map.png"
    elif art_type == "scene-break":
        final = ART_DIR / "scene_break.png"
    else:
        final = ART_DIR / f"{art_type}.png"

    shutil.copy2(variant_path, final)

    # Save the pick with its URL for reference
    picks = load_picks()
    variant_key = f"variant_{art_type}_{number}"
    url = picks.get(variant_key, {}).get("url", "")
    picks[art_type] = {"variant": number, "url": url, "path": str(final)}
    save_picks(picks)

    print(f"Selected variant {number} as final {art_type}")
    print(f"  {variant_path} → {final}")
    if art_type == "ornament":
        print(f"\nOrnament reference set. Run: gen_art.py ornaments-all")


# ============================================================
# CHARACTER PROFILES — silhouette-safe descriptors
# ============================================================

# Maps character identifiers to the visual cues that work from behind /
# as silhouette / partial view — NO face details.
_CHARACTER_PATTERNS = [
    # (search_patterns, char_key, silhouette_descriptor)
    (
        ["Cường", "cường"],
        "cuong",
        "A tall gaunt man seen from behind, short uneven hair, pale skin, "
        "long fingers. He touches his left ribcage. Wearing nondescript dark clothes.",
    ),
    (
        ["Kẻ Đuổi", "kẻ đuổi", "Nàng", "nàng"],
        "ke_duoi",
        "A woman glimpsed as a translucent silhouette, long flowing hair, "
        "standing too close. Uncanny stillness. Rendered with slight pixel-edge artifacts.",
    ),
    (
        ["Hạnh", "hạnh"],
        "hanh",
        "A stocky figure seen from behind, short grey hair, metal-framed glasses "
        "in one hand, unbuttoned jacket. Stands at an angle, never straight-on.",
    ),
    (
        ["Giám đốc", "giám đốc"],
        "giam_doc",
        "A still figure in a clean white coat, hair tied back, "
        "holding a clipboard. Perfectly erect posture. No jewelry, no personal markers.",
    ),
    (
        ["Bảo", "bảo"],
        "bao",
        "A wiry figure crouched over electronics, back to viewer, "
        "surrounded by cables and soldering gear. Sleeves rolled up.",
    ),
    (
        ["Người thứ 13", "người thứ 13", "Người Thứ 13"],
        "nguoi_13",
        "A dark shape barely distinguishable from shadow, "
        "standing at the edge of frame. No features, just outline and presence.",
    ),
    (
        ["Tuấn", "tuấn"],
        "tuan",
        "A figure in a white coat sitting at a desk, back to viewer, "
        "reading something intently. Calm stillness.",
    ),
    (
        ["Bà Lành", "bà lành", "Lành", "lành"],
        "ba_lanh",
        "An older woman in neat clothes, seen from behind, "
        "watering a small plant on a windowsill. Gentle posture.",
    ),
]

_CHARACTER_CACHE = None


def _load_character_profiles():
    """Return the character pattern list (cached)."""
    global _CHARACTER_CACHE
    if _CHARACTER_CACHE is None:
        _CHARACTER_CACHE = _CHARACTER_PATTERNS
    return _CHARACTER_CACHE


def _detect_characters_in_chapter(chapter_text, top_n=2):
    """Detect which characters appear in a chapter and return up to top_n.

    Returns list of (char_key, silhouette_descriptor, mention_count) sorted
    by frequency descending.
    """
    profiles = _load_character_profiles()
    hits = []
    for patterns, key, descriptor in profiles:
        count = sum(chapter_text.count(p) for p in patterns)
        if count > 0:
            hits.append((key, descriptor, count))
    hits.sort(key=lambda x: -x[2])
    return hits[:top_n]


def _build_scene_prompt(title, chapter_text, style):
    """Build an atmospheric scene prompt for a chapter ornament.

    Characters are shown as compositional elements — back view, silhouette,
    hands, shadow — never faces or portraits.
    """
    characters = _detect_characters_in_chapter(chapter_text)

    # Build character presence description (silhouette-safe)
    char_desc = ""
    if characters:
        parts = []
        for _key, desc, _count in characters:
            parts.append(desc)
        char_desc = (
            " In the scene: " + " Also nearby: ".join(parts)
            if len(parts) > 1 else " In the scene: " + parts[0]
        )
        char_desc += (
            " IMPORTANT: Show characters from behind, as silhouettes, "
            "or only hands/body — never show faces or front portraits."
        )

    # Build a scene prompt from the chapter context + style
    scene_prompt = (
        f"Atmospheric scene illustration for chapter '{title}'. "
        f"Scene context: a moment of tension and stillness in a confined space "
        f"with dim lighting and digital artifacts."
        f"{char_desc} "
        f"Style: {style['art_style']}. Colors: {style['color_palette']}. "
        f"Texture: {style.get('texture', '')}. Mood: {style.get('mood', '')}. "
        f"Composition: cinematic, off-center subject, negative space. "
        f"Small format. White background. No text. No faces."
    )
    return scene_prompt


# ============================================================
# BATCH ORNAMENTS (scene-based, character-aware)
# ============================================================

def cmd_ornaments_all(args):
    style = load_style()
    ref_path = get_reference_path("ornament")

    chapters = sorted(BASE_DIR.glob("chapters/ch_*.md"))
    print(f"Generating scene-based ornaments for {len(chapters)} chapters...")
    if ref_path:
        print(f"  Using ornament reference for style consistency")
    else:
        print("  WARNING: no ornament reference picked — style may vary")

    for ch_path in chapters:
        num = int(ch_path.stem.split("_")[1])
        # Extract title from first non-blank heading line
        chapter_text = ch_path.read_text()
        title = ""
        for line in chapter_text.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                title = line.lstrip("# ").strip()
                break
        if ": " in title:
            title = title.split(": ", 1)[1]

        prompt = _build_scene_prompt(title, chapter_text, style)

        # Show which characters were detected
        chars = _detect_characters_in_chapter(chapter_text)
        char_names = [c[0] for c in chars] if chars else ["(none)"]
        print(f"  Ch {num}: '{title}' chars={char_names}", end="", flush=True)

        if ref_path:
            url, _ = flux_edit(prompt, [ref_path], resolution="1K", aspect_ratio="1:1")
        else:
            url, _ = flux_generate(prompt, resolution="1K", aspect_ratio="1:1")

        dest = ART_DIR / f"ornament_ch{num:02d}.png"
        size = download_image(url, dest)
        print(f" → {dest.name} ({size:,} bytes)")
        time.sleep(1)


def cmd_scene_break(args):
    style = load_style()
    prompt = (
        f"Minimal decorative scene break. {style['scene_break_concept']}. "
        f"Style: {style['art_style']}. Very simple. White background. No text."
    )
    print("Generating scene break...")
    url, _ = flux_generate(prompt, resolution="1K", aspect_ratio="4:1")
    dest = ART_DIR / "scene_break.png"
    size = download_image(url, dest)
    print(f"  Saved: {dest} ({size:,} bytes)")


# ============================================================
# VECTORIZE: raster → SVG via potrace
# ============================================================

def cmd_vectorize(args):
    target = args.target if args.target else "all"

    # Check potrace is available
    potrace = shutil.which("potrace")
    if not potrace:
        print("ERROR: potrace not found. Install it or add to PATH.")
        sys.exit(1)

    SVG_DIR.mkdir(parents=True, exist_ok=True)

    if target == "all":
        # Vectorize ornaments + scene break (not cover or map)
        files = sorted(ART_DIR.glob("ornament_ch*.png"))
        sb = ART_DIR / "scene_break.png"
        if sb.exists():
            files.append(sb)
    else:
        f = ART_DIR / f"{target}.png"
        if not f.exists():
            print(f"Not found: {f}")
            sys.exit(1)
        files = [f]

    print(f"Vectorizing {len(files)} images...")

    for png_path in files:
        svg_path = SVG_DIR / f"{png_path.stem}.svg"

        try:
            # Step 1: Convert to grayscale PBM using Pillow
            from PIL import Image
            img = Image.open(png_path).convert("L")
            # Threshold to black and white
            bw = img.point(lambda x: 0 if x < 180 else 255, "1")
            pbm_path = png_path.with_suffix(".pbm")
            bw.save(pbm_path)

            # Step 2: Run potrace
            result = subprocess.run(
                [potrace, str(pbm_path), "-s", "-o", str(svg_path),
                 "--turdsize", "4", "--opttolerance", "0.2"],
                capture_output=True, text=True
            )

            # Cleanup temp file
            pbm_path.unlink(missing_ok=True)

            if result.returncode == 0 and svg_path.exists():
                svg_size = svg_path.stat().st_size
                print(f"  {png_path.name} → {svg_path.name} ({svg_size:,} bytes)")
            else:
                print(f"  {png_path.name} → FAILED: {result.stderr[:100]}")

        except Exception as e:
            print(f"  {png_path.name} → ERROR: {e}")

    print(f"\nSVGs saved to {SVG_DIR}/")


# ============================================================
# ALL: full pipeline with human curation points
# ============================================================

def cmd_all(args):
    print("=" * 60)
    print("AUTONOVEL ART PIPELINE (interactive)")
    print("=" * 60)

    print("\n--- Step 0: Archive existing art ---")
    cmd_archive(args)

    print("\n--- Step 1: Visual Style ---")
    if not STYLE_FILE.exists():
        cmd_style(args)
    else:
        print(f"  Using existing style from {STYLE_FILE}")

    print("\n--- Step 2: Generate Cover Variants ---")
    class CurateArgs:
        pass
    ca = CurateArgs()
    ca.art_type = "cover"
    ca.n = 4
    cmd_curate(ca)
    print("\n>>> HUMAN ACTION: Review art/variants/cover_*.png")
    print(">>> Then run: gen_art.py pick cover <number>")
    print(">>> Then re-run: gen_art.py all")
    
    if not get_reference_path("cover"):
        print("\n(Stopping here — pick a cover first)")
        return

    print("\n--- Step 3: Generate Ornament Style Variants ---")
    ca.art_type = "ornament"
    cmd_curate(ca)
    print("\n>>> HUMAN ACTION: Review art/variants/ornament_*.png")
    print(">>> Then run: gen_art.py pick ornament <number>")

    if not get_reference_path("ornament"):
        print("\n(Stopping here — pick an ornament style first)")
        return

    print("\n--- Step 4: Generate All Chapter Ornaments ---")
    cmd_ornaments_all(args)

    print("\n--- Step 5: Scene Break ---")
    cmd_scene_break(args)

    print("\n--- Step 6: Map Variants ---")
    ca.art_type = "map"
    ca.n = 3
    cmd_curate(ca)

    print("\n--- Step 7: Vectorize ---")
    cmd_vectorize(args)

    print("\n" + "=" * 60)
    print("ART PIPELINE COMPLETE")
    print("  Review maps in art/variants/map_*.png")
    print("  Pick one: gen_art.py pick map <number>")
    print("  SVG ornaments in art/svg/")
    print("=" * 60)


# ============================================================
# ARCHIVE: zip current art/ before regenerating
# ============================================================

def cmd_archive(args):
    """Zip the entire art/ directory to art/archive/<timestamp>.zip."""
    if not ART_DIR.exists() or not any(ART_DIR.iterdir()):
        print("Nothing to archive — art/ is empty or missing.")
        return

    archive_dir = ART_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = archive_dir / f"art_{ts}.zip"

    file_count = 0
    total_bytes = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(ART_DIR.rglob("*")):
            # Skip the archive directory itself and test files
            if archive_dir in f.parents or f == archive_dir:
                continue
            if not f.is_file():
                continue
            if f.suffix == ".zip" and f.parent == archive_dir:
                continue
            arcname = f.relative_to(ART_DIR)
            zf.write(f, arcname)
            file_count += 1
            total_bytes += f.stat().st_size

    if file_count == 0:
        zip_path.unlink(missing_ok=True)
        print("Nothing to archive — no files found.")
        return

    zip_size = zip_path.stat().st_size
    print(f"Archived {file_count} files ({total_bytes:,} bytes) → {zip_path} ({zip_size:,} bytes compressed)")
    return str(zip_path)


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Generate novel art via Cloudflare Flux")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("style", help="Derive visual style from world + voice")

    p = sub.add_parser("curate", help="Generate N variants for human selection")
    p.add_argument("art_type", choices=["cover", "ornament", "map", "scene-break"])
    p.add_argument("--n", type=int, default=4, help="Number of variants")

    p = sub.add_parser("pick", help="Select a variant as final")
    p.add_argument("art_type")
    p.add_argument("number", type=int)

    sub.add_parser("ornaments-all", help="Generate ornaments for all chapters")
    sub.add_parser("scene-break", help="Generate scene break decoration")

    p = sub.add_parser("vectorize", help="Convert raster art to SVG")
    p.add_argument("target", nargs="?", default="all", help="Image name or 'all'")

    sub.add_parser("all", help="Full pipeline with human curation points")

    sub.add_parser("archive", help="Zip current art/ to art/archive/<timestamp>.zip")

    sub.add_parser("budget", help="Show neuron budget and cost estimates")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if not CF_API_KEY and args.command not in ("vectorize", "archive", "budget"):
        print("ERROR: CLOUDFLARE_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)
    if not CF_ACCOUNT_ID and args.command not in ("vectorize", "archive", "budget"):
        print("ERROR: CLOUDFLARE_ACCOUNT_ID not set in .env", file=sys.stderr)
        sys.exit(1)

    ART_DIR.mkdir(exist_ok=True)

    commands = {
        "style": cmd_style,
        "curate": cmd_curate,
        "pick": cmd_pick,
        "ornaments-all": cmd_ornaments_all,
        "scene-break": cmd_scene_break,
        "vectorize": cmd_vectorize,
        "all": cmd_all,
        "archive": cmd_archive,
        "budget": cmd_budget,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
