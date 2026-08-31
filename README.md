# CinnShift — Instant Accent Color Shifter for Cinnamon & GTK

**CLI tool to recolor any existing Cinnamon/GTK theme in seconds — without deleting it — and switch to the new theme instantly.**

CinnShift is a lightweight Python command-line tool that clones any Cinnamon or GTK theme, detects its dominant accent color and all derived variants (hover, active, borders, disabled states), shifts them to a new target color using HSV scaling, and applies the modified theme instantly via `gsettings`.

No manual CSS editing. No theme rebuild from scratch. Works with any existing theme: Orchis, Qogir, Mint-Y, CBlack, and others.

Repository: [pzim-devdata/CinnShift](https://github.com/pzim-devdata/CinnShift)

---

## Why CinnShift?

There is no native tool to dynamically change accent colors in Cinnamon themes. Existing solutions have limitations:

| Feature | Manual CSS edit | [Oomox](https://github.com/themix-project/oomox) | **CinnShift** |
|---------|:---:|:---:|:---:|
| Modify existing themes | ✓ | ✗ | ✓ |
| Apply to Cinnamon shell | ✓ | ✗ | ✓ |
| Apply to GTK apps | ✓ | ✓ | ✓ |
| Separate App/Desktop targets | ✗ | ✗ | ✓ |
| Custom hex color input | ✗ | ✓ | ✓ |
| Random color generator | ✗ | ✗ | ✓ |
| Color palettes | ✗ | Partial | ✓ |
| Selector-targeted recoloring (hover, focus...) | ✗ | ✗ | ✓ |
| Free-form CSS selector targeting | ✗ | ✗ | ✓ |
| Auto-detect active themes | ✗ | ✗ | ✓ |
| Dry-run preview | ✗ | ✗ | ✓ |
| Original theme untouched | ✗ | ✓ | ✓ |

---

## Visual Comparison

#### BEFORE

![Before Theme](https://raw.githubusercontent.com/pzim-devdata/CinnShift/main/BEFORE.png)

#### AFTER

Applied command: `cinnshift.py --random --theme-app Orchis-Light --theme-desktop cinnamon --variant random`

![After Theme](https://raw.githubusercontent.com/pzim-devdata/CinnShift/main/AFTER.png)

---

## Quick Start

```bash
# Install
mkdir -p ~/.local/bin
curl -o ~/.local/bin/cinnshift.py https://raw.githubusercontent.com/pzim-devdata/CinnShift/main/cinnshift.py
chmod +x ~/.local/bin/cinnshift.py

# Run
cinnshift.py --pick --theme-source Qogir-Light --variant mycolor
```

---

## Dependencies

| Dependency | Required | Purpose |
|------------|:--------:|---------|
| `python3` | Yes | Standard on all Linux distributions |
| `gsettings` | Yes | Bundled with Cinnamon/GNOME |
| `zenity` | No | Interactive color picker (`--pick`) |

```bash
sudo apt install zenity   # Debian/Ubuntu/Mint
```

---

## Exemples

Judicious and aesthetically pleasing commands, with what each one does:

### Everyday use

```bash
# Auto-detect current active themes, generate a random pleasant color,
# shift accent everywhere, and reload live
cinnshift.py --random

# Open a color picker, apply to current active themes only (clone kept)
cinnshift.py --pick

# Shift both GTK apps and the Cinnamon desktop to purple
cinnshift.py "#6d4aff" --theme-app Orchis-Light --theme-desktop cinnamon
```

### Refined selectors (recommended)

```bash
# Balanced recoloring: hover, pressed, checked, selected states
# plus tinted separators. Rich visual impact, nothing obscured.
python cinnshift.py --random \
  --selector hover --selector active --selector checked --selector selected \
  --selector focus --selector separator --palette pale
```

**Effect:** the sweet spot for visible but tasteful recoloring. Interactive states come alive (hover glow, pressed buttons, checked boxes, selected rows, focused entries), separators get a subtle accent tint. Note: `focus` also fills focused text entries (including the Cinnamon menu search box) with the accent color.

```bash
# Minimal footprint
python cinnshift.py --random   --selector hover --selector active --selector checked --selector selected --selector separator
```

**Effect:** same recoloring minus the focus states. Fields (like the Cinnamon menu search entry) keep their original background: recommended if filled entry boxes bother you.

### Full theme recoloring (maximum coverage).

```bash
# Recolor virtually every element of the theme: borders, controls,
# states and shell elements. Avoids backgrounds carriers (tooltip,
# popover, menu, menu-cin, notification, osd, calendar-cin, panel)
# so applet surfaces (calendar@cinnamon.org, Cinnamenu...) stay readable.
python cinnshift.py --random \
  --selector headerbar --selector titlebar --selector decoration --selector wm-border \
  --selector dialog --selector sidebar --selector paned --selector statusbar --selector toolbar \
  --selector separator --selector frame --selector border --selector infobar \
  --selector button --selector entry --selector switch --selector checkbox --selector radio \
  --selector slider --selector progress --selector scrollbar --selector spinbutton --selector combobox \
  --selector tabs --selector treeview --selector rows --selector link --selector spinner \
  --selector workspace --selector expo --selector alt-tab --selector desklet \
  --selector window-list --selector grouped-list \
  --selector hover --selector active --selector focus --selector focus-visible \
  --selector checked --selector selected --selector disabled --selector visited \
  --selector indeterminate --selector backdrop --selector drop --selector drag
```

**Effect:** the deepest recoloring CinnShift can perform: 44 selectors covering window chrome (headerbar, dialogs, sidebars, toolbars), all controls (buttons, entries, switches, sliders...), delimiters, Cinnamon shell elements (workspaces, expo, desklets, window lists) and every interactive state (hover, focus, checked, disabled...). Backgrounds of overlay surfaces are deliberately excluded to preserve text readability in applets.
**Deliberately omitted selectors** (background carriers that would obscure applet content):

| Selector | Reason |
|----------|--------|
| `tooltip` | Full background fill hides tooltip text |
| `popover` | Full popup surface background |
| `menu` | GTK dropdown/menu backgrounds |
| `menu-cin` | Cinnamon start menu background |
| `notification` | Banner full background |
| `osd` | System OSD popup background |
| `calendar-cin` | Calendar widget background |
| `panel` | Entire taskbar background |

### Soft palettes

```bash
# Transform the existing accent of the active theme into a pale (pastel) version
cinnshift.py --palette pale --theme-source Orchis-Light

# Random vivid color on both Desktop and Applications
cinnshift.py --palette vibrant --random --theme-app Orchis-Light --theme-desktop cinnamon

# Neon accent on a dark shell theme
cinnshift.py "#39ff14" --palette neon --theme-desktop cinnamon

# Desaturate a provided color into the grayscale palette
cinnshift.py "#6d4aff" --palette grayscale --theme-app Orchis-Light
```

### Selector-targeted recoloring

Selectors add modifications on top of the normal accent shift: colors found inside matching CSS blocks are also recolored (using the accent color directly, no brightening or darkening).

```bash
# Recolor mouse-hover states with the accent, keep the rest intact
cinnshift.py --theme-app Orchis-Light --selector hover

# Shift accent AND recolor hover + focus + separators
cinnshift.py "#6d4aff" --theme-desktop cinnamon --selector hover --selector focus --selector separator

# Dynamic:static combo: only the hover state of buttons
cinnshift.py "#e66100" --theme-app Orchis-Light --selector hover:button

# Static element alone: repaint all separators with the accent color
cinnshift.py --theme-desktop cinnamon --selector separator
```

### Free-form CSS targeting

```bash
# Target any raw CSS selector directly
cinnshift.py "#6d4aff" --theme-app Orchis-Light --css ".button:hover"
cinnshift.py "#6d4aff" --theme-desktop cinnamon --css "#panel" --css ".window-list-item-box:hover"
```

### Preview and automation

```bash
# Preview substitutions without modifying anything
cinnshift.py "#e66100" --theme-source Qogir-Light --dry-run

# Headless/SSH usage: skip live reload
cinnshift.py --random --theme-app Orchis-Light --no-refresh
```

---

## Arguments

| Argument | Description |
|----------|-------------|
| `color` | Target hex color (e.g. `"#6d4aff"`). Optional: omitted means no accent change |
| `--pick` | Open interactive color picker (zenity) |
| `--random` | Generate a random pleasant color |
| `--palette NAME` | Constrain colors to a palette: `pale`, `vibrant`, `neon`, `grayscale`, `dark`, `soft` |
| `--theme-source NAME` | Use one theme for both Desktop + Applications |
| `--theme-app NAME` | Source theme for Applications (GTK) only |
| `--theme-desktop NAME` | Source theme for Desktop (Cinnamon) only |
| `--variant SUFFIX` | Fixed suffix for the new theme name (default: auto-numbering, see below) |
| `--selector SPEC` | Add selector-targeted replacement. Formats: `hover`, `button`, `hover:button` |
| `--css PATTERN` | Free-form CSS selector (e.g. `--css ".button:hover"`). Repeatable |
| `--dry-run` | Preview substitutions without modifying files |
| `--no-refresh` | Skip live CSS reload (for SSH/headless) |

### Defaults behavior

**Themes:** If no `--theme-source`, `--theme-app`, or `--theme-desktop` is given, CinnShift auto-detects the currently active themes and uses them as sources.

**Colors:** If neither `color`, `--random`, nor `--pick` is given, the script performs **no accent change**: it only clones the theme (or applies selectors using the existing accent). This lets you run `cinnshift.py --selector hover` on an existing theme without touching its main color.

**Palettes:**
- `--palette pale --random`: random color drawn inside the palette constraints
- `cinnshift.py "#6d4aff" --palette pale`: transforms the given color to fit the palette
- `cinnshift.py --palette pale`: transforms the existing accent color of the theme

### Selector grammar

`--selector` accepts three forms. Dynamic (state-based) and static (element-based) filters can be combined:

| Syntax | Meaning |
|--------|---------|
| `--selector hover` | All blocks containing the `:hover` state |
| `--selector button` | All blocks styling buttons (any state) |
| `--selector hover:button` | Hover state **of** buttons only |
| `--css ".button:hover"` | Raw free-form CSS selector |

**Dynamic selectors** (state pseudo-classes): `hover`, `active`, `focus`, `focus-visible`, `checked`, `selected`, `disabled` (alias: `insensitive`), `visited`, `indeterminate`, `backdrop`, `drop`, `drag`.

**Static elements** (structural):

| Category | Names |
|----------|-------|
| Window structure | `headerbar`, `titlebar`, `decoration`, `wm-border`, `dialog`, `sidebar`, `paned`, `statusbar`, `toolbar` |
| Delimiters | `separator`, `frame`, `border`, `infobar` |
| Controls | `button`, `entry`, `switch`, `checkbox`, `radio`, `slider`, `progress`, `scrollbar`, `spinbutton`, `combobox` |
| Lists & navigation | `tabs`, `treeview`, `rows`, `link`, `spinner` |
| Overlays | `tooltip`, `popover`, `menu`, `notification`, `osd` |
| Cinnamon shell | `panel`, `menu-cin`, `calendar-cin`, `workspace`, `expo`, `alt-tab`, `desklet`, `window-list`, `grouped-list` |

**Static elements ignore the neutral-color exclusion list:** gray separators, borders, and window frames get tinted with the accent hue while preserving their original lightness ratio.

**Selector color rule:** colors found inside matched blocks receive the target accent color as-is (no brightening or darkening), so results stay visually perceptible even on very dark themes.

---

## Color Palettes

| Palette | Saturation | Brightness | Character |
|---------|-----------|------------|-----------|
| `pale` | 0.20–0.45 | 0.85–1.00 | Soft pastels |
| `vibrant` | 0.80–1.00 | 0.75–0.95 | Vivid saturated tones |
| `neon` | 0.90–1.00 | 0.92–1.00 | Maximum fluorescent punch |
| `grayscale` | 0.00–0.05 | 0.30–0.80 | Pure grays |
| `dark` | 0.55–0.85 | 0.30–0.55 | Deep muted tones |
| `soft` | 0.40–0.65 | 0.70–0.90 | Balanced moderation |

---

## How It Works

1. **Locate** the source theme (`~/.local/share/themes/`, then `/usr/share/themes/`, then `/usr/share/cinnamon/theme/`)
2. **Detect** the accent color via `@define-color selected_bg_color` or `@define-color window_focus_border_color` (gray colors filtered for accuracy)
3. **Scan** all CSS and SVG files for hue-related derivatives
4. **Shift** all derivatives to the new target color using multiplicative HSV scaling
5. **Clone** the theme, substitute colors in CSS/SVG/gtkrc/metadata files
6. **Apply** via `gsettings` and force CSS reload by toggling themes briefly

The original theme is never modified. A new theme is created and activated.

---

## Theme Naming and Auto-Numbering

Without `--variant`, CinnShift names the derived theme by appending an incrementing number to the source name, avoiding ever-growing names like `theme-custom-custom-custom`:

- First run: `cinnamon` → `cinnamon-1`
- Second run: `cinnamon-1` → `cinnamon-2`
- Next run: `cinnamon-2` → `cinnamon-3`

With `--variant mix`, the suffix is fixed: `Orchis-Light` → `Orchis-Light-mix` (re-running replaces the existing derived theme). The `mix` name keeps hues grounded to the actual color base for harmonious mixes.

---

## Autostart (random color on each boot)

Open **Startup Applications** in the Cinnamon menu, click **Add**, and enter:

**Entry 1 — Applications (GTK):**

- **Name**: `CinnShift`
- **Command**: `/home/YOUR_USERNAME/.local/bin/cinnshift.py --random --theme-app Orchis-Light --variant auto`

**Entry 2 — Desktop (Cinnamon shell):**

- **Name**: `CinnShift-Desktop`
- **Command**: `/home/YOUR_USERNAME/.local/bin/cinnshift.py --random --theme-desktop cinnamon --variant auto`

**Optional: only change color every 3rd day of the month** (limit churn):

**Command**: `python3 -c "import datetime,subprocess,sys; sys.exit(0 if datetime.date.today().day % 3 else 1)" && /home/YOUR_USERNAME/.local/bin/cinnshift.py --random --theme-app Orchis-Light --variant auto`

---

## Important Notes

**Theme cloning:** The original theme is never modified. A new theme is created with the suffix you specify (or an incremented number by default).

**PNG assets:** PNG/raster images (GTK2 checkboxes, switches) are not recolored. Only CSS and SVG files are processed. Some elements may retain original colors if they rely on PNG assets.

**Cinnamon applets:** Some applets (e.g. grouped-window-list) may cache underline colors and not update immediately after a theme color change; re-opening the applet or restarting Cinnamon (`Ctrl+Alt+Esc`) forces the refresh.

---

## Compatibility

Tested on:

| Distribution | DE | Status |
|--------------|----|:------:|
| Debian 13 (Trixie) | Cinnamon 6.x | ✓ |
| Linux Mint 21–22 | Cinnamon 6.x | ✓ |
| Ubuntu 24.04 | Cinnamon (PPA) | ✓ |

Requires a Cinnamon or GNOME-based desktop environment with `gsettings` support.

---

## Contributing

Bug reports, feature requests, and pull requests welcome at [GitHub Issues](https://github.com/pzim-devdata/CinnShift/issues).

---

## License

MIT License
