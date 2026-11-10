#!/usr/bin/env python3
"""Print every slide layout in a .pptx, grouped by master.

python-pptx's `Presentation.slide_layouts` only exposes the FIRST master's
layouts. A deck with multiple masters (like the VIB-CCB template, which has
5) hides the rest unless you iterate `prs.slide_masters` yourself. This
script does that, so you always see the full inventory instead of just the
first 4.

Usage:
    python3 list_layouts.py [path/to/deck.pptx]

Defaults to assets/vib-ccb-template.pptx (relative to the skill root) when
no path is given, since that's the deck this skill generates from.
"""
import sys
from pathlib import Path

from pptx import Presentation

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DECK = SKILL_DIR / "assets" / "vib-ccb-template.pptx"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_DECK)
    prs = Presentation(path)

    total = 0
    for m_idx, master in enumerate(prs.slide_masters):
        layouts = list(master.slide_layouts)
        print(f"## Master {m_idx} ({master.name!r}) -- {len(layouts)} layouts")
        for l_idx, layout in enumerate(layouts):
            print(f"  [{m_idx}][{l_idx}] {layout.name}")
        total += len(layouts)
        print()
    print(f"Total layouts across {len(prs.slide_masters)} masters: {total}")


if __name__ == "__main__":
    main()
