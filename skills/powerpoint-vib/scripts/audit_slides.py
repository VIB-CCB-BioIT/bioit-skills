#!/usr/bin/env python3
"""Audit a generated deck against the figure-first rules in SKILL.md.

    python3 audit_slides.py deck.pptx [--min-span 0.85] [--max-words 60] [--min-scale 0.45] [--max-cols 8]

Per slide it reports the number of pictures, how far their bounding box spans the content canvas
(the slide minus 0.87 in side margins, the title band and the footer) in width and height, the share
of the slide area they cover, the number of words outside tables, and the smallest picture's render
scale (rendered width / native width at the image's dpi, 300 assumed). A slide is flagged when it
has more than two pictures, when the pictures span less than --min-span of the canvas in both
dimensions (a full-width 3:1 figure passes; a figure floating at half size does not), when it
carries more than --max-words words, when a picture renders below --min-scale of its native size,
or when a table has more than --max-cols columns. Title, chapter and end slides pass.
Exits 1 if any slide is flagged, so it can gate a build.
"""
import argparse
import io
import sys

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Emu

try:
    from PIL import Image
except ImportError:  # scale check is skipped without Pillow
    Image = None

EMU_PER_INCH = 914400
MARGIN, TITLE_BAND, FOOTER_BAND = 0.87, 1.55, 0.50   # inches; the template's content canvas


def native_inches(picture):
    """Width of the picture's image at its embedded dpi (300 dpi assumed when absent)."""
    if Image is None:
        return None
    with Image.open(io.BytesIO(picture.image.blob)) as im:
        dpi = im.info.get("dpi", (300, 300))[0] or 300
        return im.width / dpi


def audit(path, min_span, max_words, min_scale, max_cols):
    prs = Presentation(path)
    slide_area = prs.slide_width * prs.slide_height
    canvas_w = prs.slide_width - 2 * MARGIN * EMU_PER_INCH
    canvas_h = prs.slide_height - (TITLE_BAND + FOOTER_BAND) * EMU_PER_INCH
    flagged = 0
    print(f"{'#':>3}  {'pics':>4}  {'w-span':>6}  {'h-span':>6}  {'cover':>6}  {'words':>5}  {'scale':>5}  flags")
    for n, slide in enumerate(prs.slides, 1):
        pics = [s for s in slide.shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE]
        cover = sum(p.width * p.height for p in pics) / slide_area
        wspan = hspan = 0.0
        if pics:
            wspan = (max(p.left + p.width for p in pics) - min(p.left for p in pics)) / canvas_w
            hspan = (max(p.top + p.height for p in pics) - min(p.top for p in pics)) / canvas_h
        words = sum(len(s.text_frame.text.split()) for s in slide.shapes if s.has_text_frame)
        ncols = max((len(s.table.columns) for s in slide.shapes if s.has_table), default=0)
        scale = None
        for p in pics:
            nat = native_inches(p)
            if nat:
                sc = (p.width / EMU_PER_INCH) / nat
                scale = sc if scale is None else min(scale, sc)
        flags = []
        if len(pics) > 2:
            flags.append(f"{len(pics)} pictures (max 2)")
        if pics and max(wspan, hspan) < min_span:
            flags.append(f"pictures span {wspan:.0%} of width, {hspan:.0%} of height (min {min_span:.0%} in one)")
        if ncols > max_cols:
            flags.append(f"table has {ncols} columns (max {max_cols})")
        if words > max_words:
            flags.append(f"{words} words (max {max_words})")
        if scale is not None and scale < min_scale:
            flags.append(f"smallest picture at {scale:.0%} of native size (min {min_scale:.0%})")
        flagged += bool(flags)
        print(f"{n:>3}  {len(pics):>4}  {wspan:>6.0%}  {hspan:>6.0%}  {cover:>6.0%}  {words:>5}  {'' if scale is None else f'{scale:.2f}':>5}  {'; '.join(flags)}")
    print(f"\n{len(prs.slides)} slides, {flagged} flagged")
    return flagged


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx")
    ap.add_argument("--min-span", type=float, default=0.85)
    ap.add_argument("--max-words", type=int, default=60)
    ap.add_argument("--min-scale", type=float, default=0.45)
    ap.add_argument("--max-cols", type=int, default=8)
    a = ap.parse_args()
    sys.exit(1 if audit(a.pptx, a.min_span, a.max_words, a.min_scale, a.max_cols) else 0)


if __name__ == "__main__":
    main()
