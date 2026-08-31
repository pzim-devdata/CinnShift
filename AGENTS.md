# AGENTS.md

## Project
CinnShift: Python CLI that clones Cinnamon/GTK themes, detects
the dominant accent color, and shifts all derivatives to a new
color via multiplicative HSV scaling.

## Files
- cinnshift.py: entire tool, single-file script, no dependencies beyond stdlib

## Conventions
- Single file, stdlib only (no pip requirements)
- Comments and docstrings in English
- Selector mappings live in SELECTOR_DYNAMIC and SELECTOR_STATIC dicts
- Palettes defined in PALETTES dict (sat/val tuples)
- Theme cloning never modifies the source theme
- Default theme naming: incremental numbering (-1, -2...), custom via --variant

## Testing
- Always test with --dry-run first
- Test commands must use --theme-app Orchis-Light --theme-desktop cinnamon
- Verify gsettings roundtrip: org.cinnamon.theme name, org.cinnamon.desktop.interface gtk-theme

## Known limitations
- PNG assets not recolored (CSS/SVG only)
- Overlay backgrounds (menu, popover, osd, panel) must not be selector-targeted
 globally: applet text becomes unreadable