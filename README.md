# CinnShift — AnyThemeColorShifter for Cinnamon & GTK

**Change the accent color of any existing Cinnamon/GTK theme in seconds.**

CinnShift is a lightweight Python script that clones any Cinnamon or GTK theme, detects its dominant accent color and all derived variants (hover, active, borders, disabled states), shifts them to a new target color using HSV scaling, and applies the modified theme instantly via `gsettings`.

No manual CSS editing. No theme rebuild from scratch. Works with any existing theme: Orchis, Qogir, Mint-Y, CBlack, and others.

---

## Why CinnShift?

There is no native tool to dynamically change accent colors in Cinnamon themes. Existing solutions have limitations:

| Feature | Manual CSS edit | [Oomox](https://github.com/themix-project/oomox) | [DermoDeX](https://github.com/duracell80/DermoDeX) | **CinnShift** |
|---------|:---:|:---:|:---:|:---:|
| Modify existing themes | ✓ | ✗ | ✗ | ✓ |
| Apply to Cinnamon shell | ✓ | ✗ | ✓ | ✓ |
| Apply to GTK apps | ✓ | ✓ | ✗ | ✓ |
| Separate App/Desktop targets | ✗ | ✗ | ✗ | ✓ |
| Custom hex color input | ✗ | ✓ | ✗ | ✓ |
| Random color generator | ✗ | ✗ | ✓ | ✓ |
| Dry-run preview | ✗ | ✗ | ✗ | ✓ |
| Original theme untouched | ✗ | ✓ | ✓ | ✓ |

---

## Visual Comparison

#### BEFORE

![Before Theme](https://raw.githubusercontent.com/pzim-devdata/AnyThemeColorShifter-for-Cinnamon/main/BEFORE.png)

#### AFTER

Applied command: `themecolorshift.py --random --theme-app Orchis-Light --theme-desktop cinnamon --variant random`

![After Theme](https://raw.githubusercontent.com/pzim-devdata/AnyThemeColorShifter-for-Cinnamon/main/AFTER.png)

---

## Quick Start

```bash
# Install
mkdir -p ~/.local/bin
curl -o ~/.local/bin/themecolorshift.py https://raw.githubusercontent.com/pzim-devdata/AnyThemeColorShifter-for-Cinnamon/main/themecolorshift.py
chmod +x ~/.local/bin/themecolorshift.py

# Run
themecolorshift.py --pick --theme-source Qogir-Light --variant mycolor
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

## Usage Examples

```bash
# Pick a color interactively, apply to Desktop + Applications
themecolorshift.py --pick --theme-source Qogir-Light

# Random color on Applications (GTK) only
themecolorshift.py --random --theme-app Orchis-Light --variant random

# Random color on Desktop (Cinnamon) only
themecolorshift.py --random --theme-desktop cinnamon --variant random

# Specific hex color, different themes for Desktop and Applications
themecolorshift.py "#6d4aff" --theme-app Orchis-Light --theme-desktop CBlack --variant mix

# Preview substitutions without applying
themecolorshift.py "#e66100" --theme-source Qogir-Light --dry-run
```

---

## Arguments

| Argument | Description |
|----------|-------------|
| `color` | Target hex color (e.g. `"#6d4aff"`) |
| `--pick` | Open interactive color picker (zenity) |
| `--random` | Generate a random pleasant color |
| `--theme-source NAME` | Use one theme for both Desktop + Applications |
| `--theme-app NAME` | Source theme for Applications (GTK) only |
| `--theme-desktop NAME` | Source theme for Desktop (Cinnamon) only |
| `--variant SUFFIX` | Suffix for the new theme name (default: `-custom`) |
| `--dry-run` | Preview substitutions without modifying files |
| `--no-refresh` | Skip live CSS reload (for SSH/headless) |

At least one of `--theme-source`, `--theme-app`, or `--theme-desktop` is required.  
One of `color`, `--pick`, or `--random` is required.

---

## How It Works

1. **Locate** the source theme (`~/.local/share/themes/`, then `/usr/share/themes/`, then `/usr/share/cinnamon/theme/`)
2. **Detect** the accent color via `@define-color selected_bg_color` or `@define-color window_focus_border_color` (gray colors filtered for accuracy)
3. **Scan** all CSS and SVG files for hue-related derivatives
4. **Shift** all derivatives to the new target color using multiplicative HSV scaling
5. **Clone** the theme, substitute colors in CSS/SVG/gtkrc/metadata files
6. **Apply** via `gsettings` and force CSS reload by toggling themes briefly

The original theme is never modified. A new theme is created with the suffix you specify.

---

## Autostart (random color on each boot)

Open **Startup Applications** in Cinnamon menu, click **Add**, and enter:

**Entry 1 — Applications (GTK):**

- **Name**: `AnyThemeColorShifter`
- **Command**: `/home/YOUR_USERNAME/.local/bin/themecolorshift.py --random --theme-app Orchis-Light --variant auto`

**Entry 2 — Desktop (Cinnamon shell):**

- **Name**: `AnyThemeColorShifter-Desktop`
- **Command**: `/home/YOUR_USERNAME/.local/bin/themecolorshift.py --random --theme-desktop cinnamon --variant auto`

---

## Important Notes

**Theme cloning:** The original theme is never modified. A new theme is created with the suffix you specify. If you omit `--variant`, the suffix defaults to `-custom` (e.g., `Qogir-Light` becomes `Qogir-Light-custom`).

**PNG assets:** PNG/raster images (GTK2 checkboxes, switches) are not recolored. Only CSS and SVG files are processed. Some elements may retain original colors if they rely on PNG assets.

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

Bug reports, feature requests, and pull requests welcome at [GitHub Issues](https://github.com/pzim-devdata/AnyThemeColorShifter-for-Cinnamon/issues).

---

## License

MIT License
