---
name: powerpoint-vib
description: >-
  Use whenever a PowerPoint presentation, slide deck, or .pptx file needs to be created or
  generated — for talks, project updates, meeting slides, posters-as-slides, or any "make me a
  deck/slides about X" request. VIB-CCB has a mandatory house style, so ALWAYS build new decks
  from the bundled VIB-CCB template rather than a blank python-pptx presentation, even if the user
  doesn't mention a template, branding, or VIB by name. Also use it when an existing VIB deck
  needs reworking because its figures are too small or unreadable, or its slides carry too much
  text — the skill's figure-first layout rules and audit script apply. Do not use this for editing
  arbitrary existing .pptx files that aren't meant to carry VIB branding.
metadata:
  owner: Luuk Harbers
  status: draft
  tags: [presentations, pptx, vib-branding]
---

# VIB-CCB PowerPoint generation

Generate every new presentation from the VIB-CCB corporate template bundled in this skill, using
python-pptx. Never start a deck from a blank `Presentation()` — the house style (fonts, colors, logo
placement, 137 pre-built layouts) only exists in the template.

## Why a bundled, pre-converted template

The brand template lives as a `.potx` (PowerPoint template) file, and python-pptx cannot open a
`.potx` directly — it raises `ValueError: ... is not a PowerPoint file`. A `.potx` and `.pptx` are the
same OOXML package apart from one content-type string, so this skill ships an **already-converted**
`.pptx` in `assets/`. You never need to touch the original `.potx` or do any conversion — that
was a one-time step (`scripts/potx_to_pptx.py`, kept for re-running if the brand ships an update).

`assets/`, `scripts/` and `references/` below are relative to **this skill's directory** (the folder
that contains this `SKILL.md`, e.g. `~/.claude/skills/powerpoint-vib/`). Resolve it to an absolute
path and use that in generated code — the working directory is wherever the user happens to be,
not here. The examples below call it `SKILL_DIR`.

- **`assets/vib-ccb-template.pptx`** — the blank generation base. All 5 masters / 137 layouts / 7
  themes are intact; every slide has been stripped out. **Always start new decks from a copy of this
  file**, not from `Presentation()`.
- **Reference deck (optional, not bundled)** — the template's original 26 example slides. To keep
  this repo small it is not committed; if you have the official `.potx`, run
  `python3 "$SKILL_DIR/scripts/potx_to_pptx.py" <potx> --reference-out "$TMPDIR/vib-ccb-reference.pptx"`
  and open that when you're unsure what a layout looks like rendered. Without it, use
  `scripts/list_layouts.py` to see which placeholders a layout exposes — don't guess from a name alone.

## The layout-lookup gotcha

`Presentation.slide_layouts` only returns the layouts belonging to the **first** slide master. This
template has 5 masters, so that property alone hides 133 of the 137 layouts. Always reach layouts
through the master:

```python
from pptx import Presentation

import os

SKILL_DIR = os.path.expanduser("~/.claude/skills/powerpoint-vib")  # wherever this SKILL.md lives
# copy or save-elsewhere; never overwrite the bundled original
prs = Presentation(os.path.join(SKILL_DIR, "assets", "vib-ccb-template.pptx"))
layout = prs.slide_masters[MASTER_INDEX].slide_layouts[LAYOUT_INDEX]
slide = prs.slides.add_slide(layout)
```

`references/layouts.md` has the full inventory (all 137, grouped by master) with a table of contents.
Read it before picking a layout — don't guess a name or index.

## Which master to use

Checked against the 26 original example slides: every one of them uses only masters **0, 1, and 4**.
Master 2 has the same layout names as master 1 (likely a dark-theme mirror) and master 3 has generic
default-PowerPoint layout names (Section Header, Two Content, Comparison, Blank, ...) — neither is used
anywhere in the brand's own examples. Unless the user specifically asks for a dark deck or one of those
particular layouts, default to:

- **Master 0** for the opening title slide (`Title Slide - Light 01/02`, or `Dark 01/02` for a dark deck).
- **Master 1** for content slides — this has by far the widest selection (57 layouts: columns, images,
  timelines, highlights, one-column variants) and is what every example content slide actually uses.
- **Master 4** for the closing slide (`End Slide - Light 01/02`, or `Dark 01/02`).

## Figure-first content slides

The failure mode to design against: a wide multi-panel plot dropped into a half-width column, next
to six bullets. At 300 dpi a 4800 × 1500 px figure is 16 in wide; squeezed into a 5.5 in column it
renders at a third of its size and every axis label is gone. The template's boxes make this easy to
do by accident — `One column` gives 11.6 × 5.04 in starting 2.12 in from the top, `Two columns`
only 5.51 × 5.04 in each — so the rules below override the template's default boxes.

**Rules**

1. **One figure per slide by default, two at most.** Two only when both are compact (aspect ratio
   ≤ 1.3, e.g. UMAPs or square heatmaps) so each still gets ≥ 5.5 in of width, or both are wide
   (aspect ≥ 2.5) and stacked with ≥ 2.6 in of height each. Never put a wide figure (aspect > 1.6)
   in a half-width column.
2. **The figure is the slide.** The content canvas is the slide minus 0.87 in side margins, the
   title band (down to ≈ 1.55 in) and the footer (from ≈ 7.0 in): 11.6 × 5.45 in. The figure(s)
   must span ≥ 85 % of that canvas in at least one dimension — a full-width 3:1 figure that is only
   3.6 in tall is fine; a figure floating in the middle at half size is not. Drop the subtitle
   placeholder when it costs figure height.
3. **Pick the layout from the aspect ratio**, not from what the slide "is about":

   | Aspect ratio (w / h) | Placement | Where the text goes |
   |---|---|---|
   | ≥ 1.8 (wide) | full width, 11.6 in | ≤ 3 bullets in a strip below the figure, or none |
   | ≤ 1.3 (tall / square) | full height on one side, ≈ 7.0 × 5.45 in | ≤ 3 bullets in the remaining ≈ 4.3 in column |
   | in between | full width | none — title only |

4. **Text budget: title plus at most 3 bullets, ≤ 12 words each, ≥ 14 pt.** Bullets state the
   takeaway ("POOL25 samples have 2–4× more CNA cells — compare within pools"), not the method.
   Methods, caveats and provenance go in the speaker notes (`slide.notes_slide`), not on the slide.
5. **No text-only content slides** except the title, one optional methods overview (use the
   `Flow/pipeline` or `Chapter Slide` layout rather than bullets), and a closing summary of ≤ 5
   bullets.
6. **Readability floor:** a 300-dpi figure must render at ≥ 45 % of its native size (native inches
   = pixels / 300). If a figure cannot meet that on one slide, split it across slides, crop it, or
   pick a sibling figure — never shrink it further.
7. **Tables:** ≤ 8 columns and ≥ 9 pt. Otherwise drop columns or move the table to a backup slide.
8. **Remove every unused placeholder** so no "click to add text" survives in the output.

**Implementation pattern.** Read the placeholder boxes from the layout, then delete the placeholders
and place the picture in a box computed from the rules above — the template's boxes are too small
by themselves. Scale the picture to fit the box preserving aspect ratio and centre it:

```python
from PIL import Image
from pptx.util import Inches

def fit_picture(slide, path, box):
    left, top, width, height = box
    with Image.open(path) as im:
        ratio = im.width / im.height
    if ratio > width / height:
        w, h = width, int(width / ratio)
    else:
        w, h = int(height * ratio), height
    slide.shapes.add_picture(str(path), int(left + (width - w) / 2), int(top + (height - h) / 2), w, h)

CANVAS = (Inches(0.87), Inches(1.55), Inches(11.6), Inches(5.45))   # full-width figure box
```

**Audit before delivering.** `scripts/audit_slides.py` reports, per slide, the number of pictures,
how far they span the canvas, the word count outside tables, the table column count and the
smallest picture's render scale, and exits 1 when any slide breaks the rules above:

```bash
python3 "$SKILL_DIR/scripts/audit_slides.py" deck.pptx
```

Fix every flagged slide — split it, drop bullets to the notes, or pick a better-shaped figure — and
re-run until it is clean.

## Workflow

1. Copy `assets/vib-ccb-template.pptx` to the output path (or open it and `save()` elsewhere) — never
   edit the bundled copy in place.
2. Look up layouts in `references/layouts.md`, picking by name. When a name is ambiguous, cross-check
   against the reference deck (if you generated one, see above) or inspect its placeholders with
   `scripts/list_layouts.py`.
3. For each slide: `prs.slides.add_slide(layout)`, then fill placeholders via
   `slide.placeholders` (iterate and check `.placeholder_format.idx` / `.name` — layouts vary in which
   placeholders they expose, e.g. title-only vs. title+image+caption).
4. Save with `prs.save(output_path)`.
5. For data figures, follow "Figure-first content slides" above: one figure per slide, sized from
   the aspect ratio, ≤ 3 short bullets. Logos and icons stay in the template's own image placeholders.
6. Run `scripts/audit_slides.py` on the saved deck and fix every slide it flags before handing it over.

## Checks

- `python3 "$SKILL_DIR/scripts/audit_slides.py" deck.pptx` exits 0.
- The deck opens in PowerPoint without a "needs repair" prompt.
- No "Click to add …" placeholder text survives (`audit_slides.py` counts words outside tables;
  also eyeball a rendered PDF if LibreOffice is available).
- Every content slide's figure is legible at projector size — axis labels readable from the back
  of the room.

## Limitations

- The bundled template is the VIB-CCB `.potx` version `0220256` (converted 2026). If
  Communications ship a new template, regenerate (below) — old decks are not updated.
- The example deck is not bundled (size), so rendered previews of layouts need the `.potx`.
- Figure-first rules target data talks; they are deliberately strict and may need relaxing for
  text-heavy formats (teaching slides, admin updates).
- Requires `python-pptx` and `Pillow`. No LibreOffice dependency.

## Regenerating the bundled asset

Only needed if VIB-CCB ships an updated `.potx` (get it from VIB's internal brand / communication
resources; it is not in this repo). Work in a clone of
[bioit-skills](https://github.com/VIB-CCB-BioIT/bioit-skills), not an installed copy.

```bash
cd skills/powerpoint-vib
python3 scripts/potx_to_pptx.py path/to/new-template.potx   # rewrites assets/vib-ccb-template.pptx
python3 scripts/list_layouts.py assets/vib-ccb-template.pptx > "$TMPDIR/layouts.txt"
```

Then update `references/layouts.md` from that output and open a pull request. Do not commit the
`.potx` or a reference deck — each is ~11 MB.
