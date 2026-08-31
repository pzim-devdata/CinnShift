#!/usr/bin/env python3
"""
themecolorshift.py — AnyThemeColorShifter

Dynamic accent color shifter for Cinnamon desktop themes.
Clones a source theme, detects its accent color and all HSV derivatives,
shifts them to a new target color, and applies the modified theme instantly.

Features:
  - Dynamic derivative discovery (scans CSS + SVG, no hardcoded color lists)
  - Multiplicative HSV scaling (preserves relative brightness ratios)
  - Separate Desktop/Applications sources
  - System theme auto-copy from /usr/share/themes/ or /usr/share/cinnamon/theme/
  - Auto-detection of active themes when no --theme-* specified
  - Clone-only mode (no color argument = just clone)
  - Interactive color picker (--pick, via zenity with tkinter fallback)
  - Random color generation (--random)
  - Color palettes (--palette pale|vibrant|neon|grayscale|dark|soft)
  - Selector-targeted replacement (--selector, --css)
  - Instant CSS reload via toggle-refresh
  - SVG asset recoloring

Usage:
  # Auto-detect current themes and clone only (no color change)
  python themecolorshift.py

  # Auto-detect + shift with a random color
  python themecolorshift.py --random

  # Shift only Applications (GTK)
  python themecolorshift.py --random --theme-app Orchis-Light --variant proton_mix

  # Shift both Desktop and Applications from different sources
  python themecolorshift.py "#6d4aff" --theme-app Orchis-Light --theme-desktop CBlack --variant proton_mix

  # Single source for Desktop + Applications
  python themecolorshift.py --random --theme-source Qogir-Light

  # Apply palette transformation to a provided color
  python themecolorshift.py "#6d4aff" --palette pale --theme-app Orchis-Light

  # Random color within a palette
  python themecolorshift.py --palette neon --random --theme-source Qogir-Light

  # Selector: additionally recolor hover states (uses accent as target)
  python themecolorshift.py --theme-source Qogir-Light --selector hover

  # Selector with color shift: shift accent + recolor hover blocks
  python themecolorshift.py "#6d4aff" --theme-source Qogir-Light --selector hover

  # Selector: dynamic:static combo (hover on buttons only)
  python themecolorshift.py "#6d4aff" --theme-app Orchis-Light --selector hover:button

  # Multiple selectors
  python themecolorshift.py "#6d4aff" --theme-source Qogir-Light --selector hover --selector focus --selector separator

  # Free-form CSS selector
  python themecolorshift.py "#6d4aff" --theme-app Orchis-Light --css ".button:hover"

  # Preview substitutions (--dry-run)
  python themecolorshift.py "#6d4aff" --theme-source Qogir-Light --dry-run

  # Skip theme reload (--no-refresh)
  python themecolorshift.py --random --theme-app Orchis-Light --no-refresh
"""

import sys
import re
import shutil
import colorsys
import argparse
import subprocess
from pathlib import Path
from collections import Counter

# ── Configuration ───────────────────────────────────────────────────
HOME = Path.home()
THEMES_DIR = HOME / ".local" / "share" / "themes"
SYSTEM_CINNAMON_THEME = Path("/usr/share/cinnamon/theme")
SYSTEM_THEMES = Path("/usr/share/themes")
SYSTEM_COPY_PREFIX = "_system_"

GS_CINNAMON = "org.cinnamon.theme"
GS_GTK = "org.cinnamon.desktop.interface"
GS_WM = "org.cinnamon.desktop.wm.preferences"

# ── Neutral colors (excluded from accent detection) ────────────────
NEUTRAL_HEX = {
    "#ffffff", "#fffffe", "#fefefe", "#fdfdfe", "#fafbfc", "#f7f7f7",
    "#f0f3f6", "#f2f2f2", "#f6f6fb", "#fcfcfc", "#fafafc",
    "#000000", "#282a33", "#21232b", "#32343d", "#333641", "#434655",
    "#3e4250", "#51535b", "#464750", "#424656", "#4d5265", "#2c2f39",
    "#464853", "#4a4c59", "#23242a", "#6b6d75", "#85878e", "#5b5f68",
    "#9093a2", "#a3a4a9", "#b2b3b8", "#c4c5c9", "#d3dae3", "#7c7e86",
    "#7c8088", "#898d94", "#e6e6e6", "#e0e0e0", "#e3e4e5", "#d1dae3",
    "#dae2e9", "#eaeef2", "#e1e7ed", "#edf1f4", "#d3e1eb", "#e4edf3",
    "#f6f9fb", "#575a60", "#3f4145", "#a6a6a6", "#d1d3da", "#90949e",
    "#b6b8c0", "#7a7f8b", "#777983", "#e5d6ca",
    "#888888", "#888", "#666666", "#666", "#aaaaaa", "#aaa",
    "#eeeeee", "#eee", "#cccccc", "#ccc", "#444444", "#444",
    "#222222", "#222", "#111111", "#111",
    "#fc4138", "#f04a50", "#f27835", "#f08437", "#f46067", "#d05258",
    "#f68086", "#fd8d88", "#f7ae86", "#ff4d4d", "#ee3239", "#f26267",
    "#f4797e", "#f75d37",
    "#6dcfa7",
    "#9f9792", "#7b736e", "#574f4a", "#463e39", "#342c27",
    "#be916d", "#785336", "#e3cf9c", "#b08952",
    "#83b6ec", "#337fdc", "#cfe1f5", "#7ad9f1", "#0f9ac8", "#caeaf2",
    "#8de6b1", "#29ae74", "#cef8d8", "#b5e98a", "#6ab85b", "#e6f9d7",
    "#f8e359", "#d29d09", "#f9f4e1", "#ffcb62", "#d68400", "#ffead1",
    "#ffa95a", "#ed5b00", "#ffe5c5", "#f78773", "#e62d42", "#f8d2ce",
    "#e973ab", "#e33b6a", "#fac7de", "#cb78d4", "#9945b5", "#e7c2e8",
    "#9e91e8", "#7a59ca", "#d5d2f5", "#c0bfbc", "#6e6d71", "#d8d7d3",
}

# ── Selector mappings (dynamic pseudo-classes) ─────────────────────
SELECTOR_DYNAMIC = {
    'hover': [':hover'],
    'active': [':active'],
    'focus': [':focus'],
    'focus-visible': [':focus-visible'],
    'checked': [':checked'],
    'selected': [':selected'],
    'disabled': [':disabled'],
    'insensitive': [':insensitive'],
    'visited': [':visited'],
    'indeterminate': [':indeterminate'],
    'backdrop': [':backdrop'],
    'drop': [':drop('],
    'drag': [':drag'],
}

# ── Selector mappings (static elements) ────────────────────────────
SELECTOR_STATIC = {
    # Window structure
    'headerbar': ['headerbar'],
    'titlebar': ['.titlebar'],
    'decoration': ['decoration'],
    'wm-border': ['.window-frame'],
    'dialog': ['dialog', 'messagedialog'],
    'sidebar': ['sidebar', '.sidebar'],
    'paned': ['paned'],
    'statusbar': ['statusbar'],
    'toolbar': ['toolbar'],
    # Delimiters
    'separator': ['separator'],
    'frame': ['frame'],
    'border': ['border'],
    'infobar': ['infobar'],
    # Controls
    'button': ['button'],
    'entry': ['entry'],
    'switch': ['switch'],
    'checkbox': ['checkbutton'],
    'radio': ['radiobutton'],
    'slider': ['scale slider', 'slider'],
    'progress': ['progressbar'],
    'scrollbar': ['scrollbar'],
    'spinbutton': ['spinbutton'],
    'combobox': ['combobox'],
    # Lists and navigation
    'tabs': ['notebook tab'],
    'treeview': ['treeview'],
    'rows': ['row'],
    'link': ['link', ':link'],
    'spinner': ['spinner'],
    # Overlays
    'tooltip': ['tooltip'],
    'popover': ['popover'],
    'menu': ['menu'],
    'notification': ['notification', '.banner'],
    'osd': ['.osd'],
    # Cinnamon-specific
    'panel': ['#panel'],
    'menu-cin': ['.menu'],
    'calendar-cin': ['calendar'],
    'workspace': ['workspace-switcher'],
    'expo': ['expo'],
    'alt-tab': ['switcher-popup'],
    'desklet': ['.desklet'],
    'window-list': ['window-list'],
    'grouped-list': ['.grouped-window-list'],
}

# ── Color palettes ─────────────────────────────────────────────────
PALETTES = {
    'pale':      {'sat': (0.20, 0.45), 'val': (0.85, 1.0)},
    'vibrant':   {'sat': (0.80, 1.0),  'val': (0.75, 0.95)},
    'neon':      {'sat': (0.90, 1.0),  'val': (0.92, 1.0)},
    'grayscale': {'sat': (0.0,  0.05), 'val': (0.30, 0.80)},
    'dark':      {'sat': (0.55, 0.85), 'val': (0.30, 0.55)},
    'soft':      {'sat': (0.40, 0.65), 'val': (0.70, 0.90)},
}

# ── Color conversion utilities ─────────────────────────────────────

def hex_to_rgb(h):
    """Convert '#rrggbb' to (r, g, b) tuple of ints 0-255."""
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    """Convert (r, g, b) tuple to '#rrggbb' lowercase string."""
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def hex_to_hsv(h):
    """Convert '#rrggbb' to (h, s, v) tuple of floats 0.0-1.0."""
    r, g, b = [c / 255.0 for c in hex_to_rgb(h)]
    return colorsys.rgb_to_hsv(r, g, b)

def hsv_to_hex(h, s, v):
    """Convert (h, s, v) floats to '#rrggbb' lowercase string."""
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return rgb_to_hex(tuple(int(round(c * 255)) for c in (r, g, b)))

# ── Color picker ────────────────────────────────────────────────────

def parse_zenity_output(raw):
    """Parse all possible output formats from zenity --color-selection."""
    raw = raw.strip()
    if not raw:
        return None
    if raw.startswith("#"):
        return raw.lower()
    if raw.startswith("rgb"):
        nums = re.findall(r'[\d.]+', raw)
        if len(nums) >= 3:
            rgb = tuple(int(float(nums[i])) for i in range(3))
            return rgb_to_hex(rgb)
    nums = re.findall(r'[\d.]+', raw)
    if len(nums) >= 3:
        rgb = tuple(int(float(nums[i])) for i in range(3))
        return rgb_to_hex(rgb)
    return None

def pick_color_zenity(default="#6d4aff"):
    """Open zenity color picker. Returns hex string or None (cancelled/absent)."""
    try:
        r = subprocess.run(
            ["zenity", "--color-selection",
             f"--color={default}",
             "--title=Choose accent color"],
            capture_output=True, text=True, check=True
        )
        return parse_zenity_output(r.stdout)
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError:
        return None

def pick_color_tkinter(default="#6d4aff"):
    """Fallback color picker via tkinter.colorchooser."""
    try:
        import tkinter as tk
        from tkinter import colorchooser
        root = tk.Tk()
        root.withdraw()
        result = colorchooser.askcolor(color=default, title="Choose accent color")
        root.destroy()
        if result and result[1]:
            return result[1].lower()
    except Exception:
        pass
    return None

def pick_color(default="#6d4aff"):
    """Try zenity first (more native on Cinnamon/X11), fall back to tkinter."""
    color = pick_color_zenity(default)
    if color is not None:
        return color
    if not shutil.which("zenity"):
        print("[!] zenity not found, trying tkinter...")
        color = pick_color_tkinter(default)
        if color:
            return color
        print("[!] No color picker available")
    else:
        print("[!] Selection cancelled")
    return None

def random_color():
    """Generate a random pleasant accent color (8 perceptually balanced families)."""
    import random
    base_hues = [0.00, 0.07, 0.11, 0.20, 0.48, 0.60, 0.78, 0.92]
    h = random.choice(base_hues) + random.uniform(-0.015, 0.015)
    h = h % 1.0
    s = random.uniform(0.65, 0.95)
    v = random.uniform(0.75, 1.0)
    return hsv_to_hex(h, s, v)

def random_color_palette(palette_name):
    """Generate a random color within palette constraints."""
    import random
    pal = PALETTES.get(palette_name)
    if not pal:
        return random_color()
    base_hues = [0.00, 0.07, 0.11, 0.20, 0.48, 0.60, 0.78, 0.92]
    h = random.choice(base_hues) + random.uniform(-0.015, 0.015)
    h = h % 1.0
    s = random.uniform(*pal['sat'])
    v = random.uniform(*pal['val'])
    return hsv_to_hex(h, s, v)

def apply_palette(hex_color, palette_name):
    """Transform a color to fit within palette HSV constraints."""
    if palette_name not in PALETTES:
        return hex_color
    pal = PALETTES[palette_name]
    h, s, v = hex_to_hsv(hex_color)
    s = max(pal['sat'][0], min(pal['sat'][1], s))
    v = max(pal['val'][0], min(pal['val'][1], v))
    return hsv_to_hex(h, s, v)

# ── Accent color detection ─────────────────────────────────────────

def detect_accent_color(theme_dir):
    """
    Detect the dominant accent color of a theme.
    Priority: @define-color declarations > most frequent non-neutral, saturated hex.
    """
    css_files = list(theme_dir.rglob("*.css"))
    if not css_files:
        return None

    for css in css_files:
        try:
            content = css.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pattern in (
            r'@define-color\s+selected_bg_color\s+(#[0-9a-fA-F]{6})',
            r'@define-color\s+theme_selected_bg_color\s+(#[0-9a-fA-F]{6})',
            r'@define-color\s+accent_bg_color\s+(#[0-9a-fA-F]{6})',
            r'@define-color\s+window_focus_border_color\s+(#[0-9a-fA-F]{6})',
        ):
            m = re.search(pattern, content)
            if m:
                return m.group(1).lower()

    counter = Counter()
    for css in css_files:
        try:
            content = css.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for match in re.finditer(r'#([0-9a-fA-F]{6})\b', content):
            color = f"#{match.group(1).lower()}"
            if color in NEUTRAL_HEX:
                continue
            h, s, v = hex_to_hsv(color)
            if s < 0.15:
                continue
            counter[color] += 1
    if counter:
        return counter.most_common(1)[0][0]
    return None

# ── Dynamic derivative discovery ───────────────────────────────────

def is_derivative(h, s, v, acc_h, hue_tolerance=0.08, min_v=0.2, max_v=0.99):
    """Determine if an HSV color is a derivative of the accent color."""
    if v < min_v or v > max_v:
        return False
    if s < 0.10:
        return False
    dh = abs(h - acc_h)
    if dh > 0.5:
        dh = 1.0 - dh
    if dh > hue_tolerance:
        return False
    if s > 0.20:
        return True
    if s > 0.10 and v > 0.80:
        return True
    return False

def discover_derivatives(theme_dir, accent_hex, hue_tolerance=0.08):
    """Scan all CSS and SVG files in the theme directory for derivative colors."""
    acc_h, acc_s, acc_v = hex_to_hsv(accent_hex)
    found = set()
    found.add(accent_hex.lower())

    files = list(theme_dir.rglob("*.css")) + list(theme_dir.rglob("*.svg"))
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for match in re.finditer(r'#([0-9a-fA-F]{6})\b', content):
            color = f"#{match.group(1).lower()}"
            if color in NEUTRAL_HEX or color in found:
                continue
            h, s, v = hex_to_hsv(color)
            if is_derivative(h, s, v, acc_h, hue_tolerance):
                found.add(color)
    return found

# ── Replacement palette construction ───────────────────────────────

def build_replacements(source_colors, source_accent, target_accent):
    """Build replacement map using multiplicative HSV scaling."""
    tgt = target_accent.lower()
    src = source_accent.lower()
    t_h, t_s, t_v = hex_to_hsv(tgt)
    s_h, s_s, s_v = hex_to_hsv(src)

    hex_repl = {}
    rgba_map = []

    for sc in source_colors:
        sc = sc.lower()
        d_h, d_s, d_v = hex_to_hsv(sc)

        ratio_s = d_s / s_s if s_s > 0.01 else 1.0
        ratio_v = d_v / s_v if s_v > 0.01 else 1.0

        new_s = max(0.0, min(1.0, ratio_s * t_s))
        new_v = max(0.0, min(1.0, ratio_v * t_v))
        tc = hsv_to_hex(t_h, new_s, new_v)

        hex_repl[sc] = tc
        hex_repl[sc.upper()] = tc.upper()

        sr, sg, sb = hex_to_rgb(sc)
        tr, tg, tb = hex_to_rgb(tc)
        rgba_map.append((sr, sg, sb, tr, tg, tb))

    return hex_repl, rgba_map

# ── File substitution ───────────────────────────────────────────────

def replace_in_text(content, hex_repl, rgba_map):
    """Replace hex colors and rgba() values in a text string."""
    for old in sorted(hex_repl.keys(), key=len, reverse=True):
        content = content.replace(old, hex_repl[old])
    for sr, sg, sb, tr, tg, tb in rgba_map:
        content = re.sub(
            rf'rgba\(\s*{sr}\s*,\s*{sg}\s*,\s*{sb}\s*,',
            f'rgba({tr}, {tg}, {tb},',
            content
        )
    return content

def process_file(filepath, hex_repl, rgba_map):
    """Process a single file. Returns True if modified."""
    if not filepath.is_file():
        return False
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    new_content = replace_in_text(content, hex_repl, rgba_map)
    if new_content != content:
        filepath.write_text(new_content, encoding="utf-8")
        return True
    return False

def process_theme_dir(theme_dir, hex_repl, rgba_map):
    """Recursively process all relevant files in a theme directory."""
    modified = []
    for pattern in ("*.css", "*.svg", "gtkrc", "*.rc"):
        for f in theme_dir.rglob(pattern):
            if process_file(f, hex_repl, rgba_map):
                modified.append(str(f.relative_to(theme_dir)))
    idx = theme_dir / "index.theme"
    if idx.is_file():
        content = idx.read_text(encoding="utf-8")
        new = replace_in_text(content, hex_repl, rgba_map)
        if new != content:
            idx.write_text(new, encoding="utf-8")
            modified.append("index.theme")
    meta = theme_dir / "metadata.json"
    if process_file(meta, hex_repl, rgba_map):
        modified.append("metadata.json")
    dock = theme_dir / "plank" / "dock.theme"
    if process_file(dock, hex_repl, rgba_map):
        modified.append("plank/dock.theme")
    return modified

# ── Selector-targeted replacement ──────────────────────────────────

def parse_selector_arg(arg):
    """
    Parse a --selector argument into (dynamic_patterns, static_patterns).
    Formats:
      'hover'              -> ([':hover'], [])
      'button'             -> ([], ['button'])
      'hover:button'       -> ([':hover'], ['button'])
    Returns None on unknown selector name.
    """
    dynamic_patterns = []
    static_patterns = []

    if ':' in arg:
        dyn_str, stat_str = arg.split(':', 1)
        dyn_str = dyn_str.strip()
        stat_str = stat_str.strip()
        if dyn_str in SELECTOR_DYNAMIC:
            dynamic_patterns = list(SELECTOR_DYNAMIC[dyn_str])
        else:
            print(f"[!] Unknown dynamic selector: '{dyn_str}'")
            return None
        if stat_str in SELECTOR_STATIC:
            static_patterns = list(SELECTOR_STATIC[stat_str])
        else:
            print(f"[!] Unknown static selector: '{stat_str}'")
            return None
    else:
        key = arg.strip()
        if key in SELECTOR_DYNAMIC:
            dynamic_patterns = list(SELECTOR_DYNAMIC[key])
        elif key in SELECTOR_STATIC:
            static_patterns = list(SELECTOR_STATIC[key])
        else:
            print(f"[!] Unknown selector: '{key}' (use --css for free-form)")
            return None

    return (dynamic_patterns, static_patterns)

def block_matches(selector_text, dynamic_patterns, static_patterns):
    """Check if a CSS block's selector matches the given dynamic/static patterns."""
    sel_lower = selector_text.lower()
    has_filter = False
    if dynamic_patterns:
        has_filter = True
        if not any(d.lower() in sel_lower for d in dynamic_patterns):
            return False
    if static_patterns:
        has_filter = True
        if not any(s.lower() in sel_lower for s in static_patterns):
            return False
    return has_filter

def compute_selector_replacement(orig_hex, accent_hex, target_hex):
    """
    Compute replacement for a color found in a selector block.
    Uses the target accent color directly, preserving perceptual
    visibility (no lightening/darkening relative to accent).
    """
    return target_hex.lower()

def process_selectors_in_file(filepath, selector_specs, css_patterns,
                               accent_hex, target_hex, replaced_keys, dry_run=False):
    """
    Process selector-targeted color replacements in a CSS file.
    Only modifies colors within blocks matching the selector criteria.
    Skips colors already replaced by the normal derivative pass.
    Returns (was_modified, substitutions_list).
    """
    if not filepath.is_file():
        return False, []

    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False, []

    replaced_set = set(k.lower() for k in replaced_keys
                       if k.startswith('#') and len(k) == 7)
    substitutions = []
    pattern = re.compile(r'([^{}]+)\{([^{}]*)\}', re.DOTALL)
    modified = False

    def replace_callback(m):
        nonlocal modified
        selector_text = m.group(1)
        body = m.group(2)

        matched = False
        for dyn_pats, stat_pats in selector_specs:
            if block_matches(selector_text, dyn_pats, stat_pats):
                matched = True
                break
        if not matched:
            for css_pat in css_patterns:
                if css_pat.lower() in selector_text.lower():
                    matched = True
                    break
        if not matched:
            return m.group(0)

        new_body = body
        for match in re.finditer(r'#([0-9a-fA-F]{6})\b', body):
            color = f"#{match.group(1).lower()}"
            if color in replaced_set:
                continue
            replacement = compute_selector_replacement(color, accent_hex, target_hex)
            if replacement != color:
                new_body = new_body.replace(match.group(0), replacement)
                new_body = new_body.replace(match.group(0).upper(), replacement.upper())
                substitutions.append((color, replacement, str(filepath.name)))
                modified = True

        # Also handle rgba() in matched blocks
        for match in re.finditer(
            r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,?',
            body
        ):
            sr, sg, sb = int(match.group(1)), int(match.group(2)), int(match.group(3))
            orig_hex = rgb_to_hex((sr, sg, sb))
            if orig_hex in replaced_set:
                continue
            replacement = compute_selector_replacement(orig_hex, accent_hex, target_hex)
            tr, tg, tb = hex_to_rgb(replacement)
            rgba_old = match.group(0)
            rgba_new = re.sub(
                r'\d+\s*,\s*\d+\s*,\s*\d+',
                f'{tr}, {tg}, {tb}',
                rgba_old
            )
            if rgba_new != rgba_old:
                new_body = new_body.replace(rgba_old, rgba_new)
                substitutions.append((orig_hex, replacement, str(filepath.name)))
                modified = True

        if new_body != body:
            return selector_text + "{" + new_body + "}"
        return m.group(0)

    new_content = pattern.sub(replace_callback, content)

    if modified and not dry_run:
        filepath.write_text(new_content, encoding="utf-8")

    return modified, substitutions

def process_selectors_in_dir(theme_dir, selector_specs, css_patterns,
                              accent_hex, target_hex, replaced_keys, dry_run=False):
    """Process selector-targeted replacements across all CSS files in a theme."""
    all_subs = []
    all_modified = []
    for f in theme_dir.rglob("*.css"):
        mod, subs = process_selectors_in_file(
            f, selector_specs, css_patterns,
            accent_hex, target_hex, replaced_keys, dry_run
        )
        if mod:
            all_modified.append(str(f.relative_to(theme_dir)))
            all_subs.extend(subs)
    return all_modified, all_subs

# ── Theme sourcing and cloning ─────────────────────────────────────

def ensure_theme_available(source_name):
    """Locate a theme and make it available in ~/.local/share/themes/."""
    local_dir = THEMES_DIR / source_name
    if local_dir.is_dir():
        return (local_dir, False)

    THEMES_DIR.mkdir(parents=True, exist_ok=True)

    temp_name = f"{SYSTEM_COPY_PREFIX}{source_name}"
    temp_dir = THEMES_DIR / temp_name
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    usr_theme = SYSTEM_THEMES / source_name
    if usr_theme.is_dir():
        print(f"  [INFO] Copying from /usr/share/themes/{source_name}")
        shutil.copytree(usr_theme, temp_dir)
        return (temp_dir, True)

    if source_name == "cinnamon" and SYSTEM_CINNAMON_THEME.is_dir():
        print(f"  [INFO] Copying default Cinnamon theme")
        cinnamon_subdir = temp_dir / "cinnamon"
        shutil.copytree(SYSTEM_CINNAMON_THEME, cinnamon_subdir)
        idx = temp_dir / "index.theme"
        idx.write_text(
            "[X-Cinnamon]\n"
            "Name=cinnamon\n"
            "Type=X-Cinnamon-Theme\n",
            encoding="utf-8"
        )
        return (temp_dir, True)

    return (None, False)

def clone_theme(source_dir, source_name, target_name):
    """Clone a theme directory and update its name in metadata files."""
    target_dir = THEMES_DIR / target_name
    if not source_dir.is_dir():
        print(f"[!] Source theme not found: {source_dir}")
        return None
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_dir, target_dir)

    idx = target_dir / "index.theme"
    if idx.is_file():
        c = idx.read_text(encoding="utf-8")
        c = re.sub(r'^Name\s*=.*$', f"Name={target_name}", c, flags=re.MULTILINE)
        idx.write_text(c, encoding="utf-8")

    meta = target_dir / "metadata.json"
    if meta.is_file():
        c = meta.read_text(encoding="utf-8")
        c = re.sub(r'"name"\s*:\s*"[^"]*"', f'"name": "{target_name}"', c)
        meta.write_text(c, encoding="utf-8")

    return target_dir

# ── gsettings utilities ─────────────────────────────────────────────

def gs_get(schema, key):
    """Get a gsettings value. Returns empty string on failure."""
    try:
        r = subprocess.run(["gsettings", "get", schema, key],
                           capture_output=True, text=True, check=True)
        return r.stdout.strip().strip("'")
    except subprocess.CalledProcessError:
        return ""

def gs_set(schema, key, value):
    """Set a gsettings value with console output."""
    try:
        subprocess.run(["gsettings", "set", schema, key, value], check=True)
        print(f"  [OK] {schema} {key} = '{value}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [!] Failed {schema} {key}: {e}")
        return False

def gs_set_quiet(schema, key, value):
    """Set a gsettings value silently (used during refresh toggle)."""
    try:
        subprocess.run(["gsettings", "set", schema, key, value], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

# ── Theme refresh (force CSS reload) ────────────────────────────────

def refresh_themes(desk_name, app_name, wm_name, do_desktop=True, do_app=True):
    """Force theme CSS reload by toggling to an alternate theme and back."""
    import time
    import random

    available = set()
    if THEMES_DIR.is_dir():
        for d in THEMES_DIR.iterdir():
            if d.is_dir() and not d.name.startswith(SYSTEM_COPY_PREFIX):
                available.add(d.name)
    if SYSTEM_THEMES.is_dir():
        for d in SYSTEM_THEMES.iterdir():
            if d.is_dir():
                available.add(d.name)

    if do_desktop and do_app and desk_name == app_name:
        candidates = available - {desk_name, wm_name}
        if not candidates:
            print("  [!] No alternate theme available for grouped refresh")
            return
        alt = random.choice(sorted(candidates))
        print(f"  [*] Grouped refresh: switching to '{alt}' and back")
        gs_set_quiet(GS_CINNAMON, "name", alt)
        gs_set_quiet(GS_GTK, "gtk-theme", alt)
        gs_set_quiet(GS_WM, "theme", alt)
        time.sleep(0.5)
        gs_set_quiet(GS_CINNAMON, "name", desk_name)
        gs_set_quiet(GS_GTK, "gtk-theme", app_name)
        gs_set_quiet(GS_WM, "theme", wm_name)
        print("  [OK] Desktop + Applications reloaded")
        return

    if do_app:
        candidates = available - {app_name}
        if candidates:
            alt = random.choice(sorted(candidates))
            print(f"  [*] Applications refresh: switching to '{alt}' and back")
            gs_set_quiet(GS_GTK, "gtk-theme", alt)
            time.sleep(0.3)
            gs_set_quiet(GS_GTK, "gtk-theme", app_name)
            print("  [OK] Applications reloaded")
        else:
            print("  [!] No alternate theme for Applications")

    if do_desktop:
        candidates = available - {desk_name, wm_name}
        if candidates:
            alt = random.choice(sorted(candidates))
            print(f"  [*] Desktop refresh: switching to '{alt}' and back")
            gs_set_quiet(GS_CINNAMON, "name", alt)
            gs_set_quiet(GS_WM, "theme", alt)
            time.sleep(0.3)
            gs_set_quiet(GS_CINNAMON, "name", desk_name)
            gs_set_quiet(GS_WM, "theme", wm_name)
            print("  [OK] Desktop reloaded")
        else:
            print("  [!] No alternate theme for Desktop")

# ── Per-theme processing pipeline ───────────────────────────────────

def shift_one_theme(source_name, target_accent, variant_suffix, dry_run=False,
                    selector_specs=None, css_patterns=None, palette=None):
    """
    Full pipeline for one theme.
    If target_accent is None and palette is set: detect accent, apply palette.
    If target_accent is None and no palette: clone only.
    """
    source_dir, is_temp = ensure_theme_available(source_name)
    if not source_dir or not source_dir.is_dir():
        print(f"[!] Theme source not found: {source_name}")
        return None

    try:
        accent = detect_accent_color(source_dir)
        if not accent:
            print(f"[!] Accent not detected for '{source_name}'")
            return None

        # NEW: palette-only mode (no explicit color given)
        if target_accent is None and palette:
            target_accent = apply_palette(accent, palette)
            print(f"  Source: {source_name} (accent {accent})")
            print(f"  Palette '{palette}' applied: {accent} -> {target_accent}")

        # Auto-numbering for default variant, preserve custom variants
        if variant_suffix == "-custom":
            base = strip_trailing_suffix(source_name)
            num = next_available_number(base)
            target_name = f"{base}-{num}"
        else:
            target_name = f"{strip_trailing_suffix(source_name)}{variant_suffix}"

        hex_repl = {}
        rgba_map = []
        target_dir = None

        has_color = target_accent is not None
        has_selectors = bool(selector_specs or css_patterns)

        if not has_color and not has_selectors:
            # Clone only
            print(f"  Source: {source_name} (accent {accent})")
            print(f"  Target: {target_name} (clone only, no color shift)")
            if dry_run:
                print("  [*] Dry-run: would clone without modifications")
                return (target_name, None, {}, [])

            target_dir = clone_theme(source_dir, source_name, target_name)
            if not target_dir:
                return None
            print(f"  Cloned to {target_dir.name}")
            return (target_name, target_dir, {}, [])

        if has_color:
            source_colors = discover_derivatives(source_dir, accent)
            print(f"  Source: {source_name} (accent {accent}, {len(source_colors)} derivatives)")

            hex_repl, rgba_map = build_replacements(source_colors, accent, target_accent)
            print(f"  Target: {target_name} (accent {target_accent})")
            print(f"  {len(hex_repl)} hex substitutions, {len(rgba_map)} rgba patterns")

            if dry_run:
                print("  --- Substitutions ---")
                seen = set()
                for old in sorted(hex_repl.keys()):
                    if old.startswith("#") and len(old) == 7 and old.lower() not in seen:
                        seen.add(old.lower())
                        print(f"    {old} -> {hex_repl[old]}")

        if has_selectors:
            sel_target = target_accent if target_accent else accent
            sel_desc = ", ".join(
                (":".join([
                    ",".join(d or ["-"]),
                    ",".join(s or ["-"])
                ])) for d, s in selector_specs
            )
            if css_patterns:
                sel_desc += f", css=[{', '.join(css_patterns)}]"
            if has_color:
                print(f"  Selectors: {sel_desc} (target: {sel_target})")
            else:
                print(f"  Source: {source_name} (accent {accent})")
                print(f"  Target: {target_name} (selectors only, accent as target)")
                print(f"  Selectors: {sel_desc}")

            if dry_run and not has_color:
                print("  [*] Dry-run: would apply selectors in matched blocks")

        if dry_run:
            return (target_name, None, hex_repl, rgba_map)

        target_dir = clone_theme(source_dir, source_name, target_name)
        if not target_dir:
            return None

        modified = []
        if has_color:
            modified = process_theme_dir(target_dir, hex_repl, rgba_map)
            print(f"  {len(modified)} file(s) modified (color shift)")
            for f in modified[:10]:
                print(f"    - {f}")
            if len(modified) > 10:
                print(f"    ... and {len(modified) - 10} more")

        if has_selectors:
            sel_target = target_accent if target_accent else accent
            sel_modified, sel_subs = process_selectors_in_dir(
                target_dir, selector_specs, css_patterns,
                accent, sel_target, hex_repl, dry_run
            )
            if sel_modified:
                print(f"  {len(sel_modified)} file(s) modified (selectors)")
                for f in sel_modified[:10]:
                    print(f"    - {f}")
                if len(sel_modified) > 10:
                    print(f"    ... and {len(sel_modified) - 10} more")
                print(f"  {len(sel_subs)} selector substitution(s)")
                for old, new, fname in sel_subs[:10]:
                    print(f"    {old} -> {new} ({fname})")
            else:
                print(f"  No selector matches found")

        return (target_name, target_dir, hex_repl, rgba_map)

    finally:
        if is_temp and source_dir.exists():
            shutil.rmtree(source_dir)
            print(f"  [INFO] Temporary copy removed: {source_dir.name}")

# ── Main entry point ────────────────────────────────────────────────

def strip_trailing_suffix(name):
    """Remove trailing -custom or -N suffixes from a theme name."""
    # Strip -custom (possibly stacked)
    while name.endswith("-custom"):
        stripped = name[:-len("-custom")]
        if not stripped:
            break
        name = stripped
    # Strip -N (numeric, possibly stacked)
    while True:
        m = re.match(r'^(.+)-(\d+)$', name)
        if not m:
            break
        name = m.group(1)
    return name

def next_available_number(base_name):
    """Find next available number suffix for base_name in THEMES_DIR."""
    n = 1
    while (THEMES_DIR / f"{base_name}-{n}").exists():
        n += 1
    return n

def main():
    parser = argparse.ArgumentParser(
        description="AnyThemeColorShifter - Change accent color of any Cinnamon/GTK theme."
    )
    parser.add_argument("color", nargs='?', default=None,
                        help='Target color as hex (e.g. "#6d4aff"). '
                             'Omitted if --pick or --random is used. '
                             'If none given: clone only (no color shift).')
    parser.add_argument("--pick", action="store_true",
                        help="Open interactive color picker (zenity)")
    parser.add_argument("--random", action="store_true",
                        help="Generate a random pleasant accent color")
    parser.add_argument("--palette",
                        choices=list(PALETTES.keys()),
                        default=None,
                        help="Apply palette constraints (pale, vibrant, neon, "
                             "grayscale, dark, soft). Combined with --random: "
                             "random within palette. Combined with a hex color: "
                             "transform color to fit palette.")

    src = parser.add_mutually_exclusive_group(required=False)
    src.add_argument("--theme-source",
                     help="Single theme for both Desktop and Applications")
    src.add_argument("--theme-app",
                     help="Source theme for Applications (GTK) only")

    parser.add_argument("--theme-desktop", default=None,
                        help="Source theme for Desktop (Cinnamon). "
                             "If omitted with --theme-app, Desktop stays unchanged. "
                             "If neither --theme-* is given, current active themes are used.")
    parser.add_argument("--variant", default="-custom",
                        help="Suffix for the derived theme name (default: -custom)")
    parser.add_argument("--selector", action="append", default=[],
                        help="Add selector-targeted replacement. "
                             "Formats: 'hover', 'button', 'hover:button'. "
                             "Repeatable for multiple selectors.")
    parser.add_argument("--css", action="append", default=[],
                        help="Free-form CSS selector for targeted replacement. "
                             "Example: --css '.button:hover'. Repeatable.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print substitutions without applying")
    parser.add_argument("--no-refresh", action="store_true",
                        help="Skip theme toggle-refresh (for headless/SSH)")
    args = parser.parse_args()

    # ── Determine target color ───────────────────────────────────
    target = None

    if args.random:
        if args.palette:
            target = random_color_palette(args.palette)
        else:
            target = random_color()
        print(f"[*] Generated color: {target}\n")
    elif args.pick:
        target = pick_color()
        if not target:
            sys.exit(1)
        print(f"[*] Selected color: {target}\n")
    elif args.color:
        target = args.color.lower()
        if not re.match(r'^#[0-9a-fA-F]{6}$', target):
            print("[!] Invalid format. Expected: #RRGGBB")
            sys.exit(1)
        if args.palette:
            target = apply_palette(target, args.palette)
            print(f"[*] Palette '{args.palette}' applied: {target}\n")
        else:
            print(f"[*] Target color: {target}\n")
    else:
        # No explicit color: palette-only mode handled inside shift_one_theme
        if args.palette:
            print(f"[*] Palette '{args.palette}': will transform existing accent\n")
        elif args.selector or args.css:
            print("[*] No color specified: using accent as target for selectors\n")
        else:
            print("[*] No color specified: clone-only mode\n")

    # ── Parse selector specs ─────────────────────────────────────
    selector_specs = []
    css_patterns = list(args.css)

    for sel_arg in args.selector:
        parsed = parse_selector_arg(sel_arg)
        if parsed is None:
            sys.exit(1)
        selector_specs.append(parsed)

    # ── Determine theme sources (auto-detect if none given) ──────
    if not args.theme_source and not args.theme_app and not args.theme_desktop:
        print("[*] No theme specified: detecting current active themes\n")
        current_gtk = gs_get(GS_GTK, "gtk-theme")
        current_cinnamon = gs_get(GS_CINNAMON, "name")

        if current_gtk:
            app_source = current_gtk
            has_app = True
        else:
            app_source = None
            has_app = False
            print("[!] Could not detect current GTK theme")

        if current_cinnamon:
            desktop_source = current_cinnamon
            has_desktop = True
        else:
            desktop_source = None
            has_desktop = False
            print("[!] Could not detect current Cinnamon theme")

        if not has_app and not has_desktop:
            print("[!] No themes detected. Specify --theme-source, --theme-app, or --theme-desktop")
            sys.exit(1)
    elif args.theme_source:
        app_source = args.theme_source
        desktop_source = args.theme_source
        has_desktop = True
        has_app = True
    elif args.theme_app:
        app_source = args.theme_app
        desktop_source = args.theme_desktop
        has_app = True
        has_desktop = desktop_source is not None
    elif args.theme_desktop:
        app_source = None
        desktop_source = args.theme_desktop
        has_app = False
        has_desktop = True
    else:
        print("[!] Invalid configuration")
        sys.exit(1)

    same_source = has_desktop and has_app and (app_source == desktop_source)

    THEMES_DIR.mkdir(parents=True, exist_ok=True)

    header = f"=== AnyThemeColorShifter"
    if target:
        header += f": {target}"
    elif selector_specs or css_patterns:
        header += f": selectors only"
    else:
        header += f": clone only"
    header += " ===\n"
    print(header)

    # ── Process Applications (GTK) ────────────────────────────────
    if has_app:
        print("[Applications / GTK]")
        app_result = shift_one_theme(
            app_source, target, args.variant, args.dry_run,
            selector_specs, css_patterns, palette=args.palette
        )
    else:
        print("[Applications / GTK]")
        print("  (skipped: --theme-app/--theme-source not specified)")
        app_name = gs_get(GS_GTK, "gtk-theme")
        if app_name:
            print(f"  Current theme preserved: {app_name}")
        app_result = (app_name, None, {}, [])

    # ── Process Desktop (Cinnamon) ────────────────────────────────
    if has_desktop:
        print("\n[Desktop / Cinnamon]")
        if same_source:
            print("  (same source: reused)")
            desk_result = app_result
        else:
            desk_result = shift_one_theme(
                desktop_source, target, args.variant, args.dry_run,
                selector_specs, css_patterns, palette=args.palette
            )
    else:
        print("\n[Desktop / Cinnamon]")
        print("  (skipped: --theme-desktop not specified)")
        current_desk = gs_get(GS_CINNAMON, "name")
        if current_desk:
            print(f"  Current theme preserved: {current_desk}")
        desk_result = None

    # ── Abort checks ─────────────────────────────────────────────
    if args.dry_run:
        print("\n[*] Dry-run complete.")
        return

    if has_app and not app_result:
        print("\n[!] Applications failed. Aborting.")
        sys.exit(1)
    if not has_app and not desk_result:
        print("\n[!] No theme modified. Aborting.")
        sys.exit(1)

    # ── Apply gsettings ──────────────────────────────────────────
    print(f"\n[Applying gsettings]")

    if has_app:
        app_name = app_result[0]
        gs_set(GS_GTK, "gtk-theme", app_name)
    else:
        print("  [SKIP] Applications theme not modified")

    if same_source:
        gs_set(GS_CINNAMON, "name", app_name)
        gs_set(GS_WM, "theme", app_name)
    elif has_desktop and desk_result:
        desk_name = desk_result[0]
        gs_set(GS_CINNAMON, "name", desk_name)
        gs_set(GS_WM, "theme", desk_name)
    else:
        print("  [SKIP] Desktop theme not modified")

    # ── Refresh themes ───────────────────────────────────────────
    if not args.no_refresh:
        if same_source:
            final_desk = app_result[0] if has_app else None
            final_wm = final_desk
            refresh_themes(final_desk, final_desk, final_wm,
                           do_desktop=True, do_app=True)
        elif has_app and has_desktop and desk_result:
            final_desk = desk_result[0]
            final_wm = final_desk
            refresh_themes(final_desk, app_result[0], final_wm,
                           do_desktop=True, do_app=True)
        elif has_app:
            final_desk = gs_get(GS_CINNAMON, "name") or app_result[0]
            final_wm = gs_get(GS_WM, "name") or final_desk
            refresh_themes(final_desk, app_result[0], final_wm,
                           do_desktop=False, do_app=True)
        elif has_desktop:
            final_app = gs_get(GS_GTK, "gtk-theme") or ""
            final_desk = desk_result[0]
            final_wm = final_desk
            refresh_themes(final_desk, final_app, final_wm,
                           do_desktop=True, do_app=False)

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n[OK]")
    if has_app:
        print(f"    Applications='{app_name}',", end="")
    if has_desktop and desk_result:
        print(f" Desktop='{desk_result[0]}',", end="")
    if target:
        print(f" Accent={target}")
    elif selector_specs or css_patterns:
        print(f" Selectors applied (accent preserved)")
    else:
        print(f" Cloned (no color change)")
    if not args.no_refresh:
        print("    Theme(s) reloaded live.")
    else:
        print("    Restart apps to see changes.")

if __name__ == "__main__":
    main()
