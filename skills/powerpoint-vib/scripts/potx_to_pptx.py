#!/usr/bin/env python3
"""One-time converter: VIB-CCB .potx template -> .pptx files python-pptx can open.

A .potx (PowerPoint template) and a .pptx (presentation) are the same OOXML
zip package. The only functional difference is one content-type string in
[Content_Types].xml. python-pptx refuses to open a .potx directly (raises
ValueError: "... is not a PowerPoint file"), so this script rewrites that one
string in memory and writes out a real .pptx -- no LibreOffice/unoconv
needed (and none is installed on this HPC anyway), and nothing is re-rendered
so the template is preserved losslessly.

Produces:
  - assets/vib-ccb-template.pptx : the package with every slide removed (all
        5 masters / 137 layouts / 7 themes kept) -- the blank base that
        SKILL.md tells the agent to build generated decks from.
  - optionally, with --reference-out PATH: the template's 26 example slides,
        as-is, so you can see how the brand actually uses its layouts. This is
        ~11 MB and is NOT committed; write it somewhere like $TMPDIR.

Usage (the .potx is not in the repo; get it from VIB's brand resources):

    python3 potx_to_pptx.py path/to/template.potx [--reference-out PATH]
"""
import argparse
import io
import re
import sys
import zipfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS = SKILL_DIR / "assets"
TEMPLATE_OUT = ASSETS / "vib-ccb-template.pptx"


def potx_bytes_to_pptx_zip(raw: bytes) -> zipfile.ZipFile:
    """Return an in-memory zipfile.ZipFile with the content-type swapped."""
    zin = zipfile.ZipFile(io.BytesIO(raw))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                data = data.replace(
                    b"presentationml.template.main+xml",
                    b"presentationml.presentation.main+xml",
                )
            zout.writestr(item, data)
    buf.seek(0)
    return zipfile.ZipFile(buf)


def strip_slides(zin: zipfile.ZipFile) -> bytes:
    """Remove all slides from a converted-pptx zip, keep masters/layouts/themes.

    Slides are referenced from ppt/presentation.xml via <p:sldId> entries,
    each pointing at a relationship id (r:id) in
    ppt/_rels/presentation.xml.rels. To end up with a deck PowerPoint (and
    python-pptx) opens cleanly with zero slides, both sides must be dropped:
    the <p:sldId> list AND the matching slide relationships. Leaving either
    side dangling causes a "needs repair" prompt in PowerPoint.
    """
    pres_xml = zin.read("ppt/presentation.xml").decode("utf-8")
    rels_xml = zin.read("ppt/_rels/presentation.xml.rels").decode("utf-8")

    sld_ids = re.findall(r'<p:sldId[^>]*r:id="([^"]+)"[^/]*/>', pres_xml)
    pres_xml = re.sub(r"<p:sldIdLst>.*?</p:sldIdLst>", "<p:sldIdLst/>", pres_xml, flags=re.S)

    for rid in sld_ids:
        rels_xml = re.sub(rf'<Relationship[^>]*Id="{re.escape(rid)}"[^>]*/>', "", rels_xml)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            name = item.filename
            if re.match(r"ppt/slides/slide\d+\.xml$", name) or re.match(
                r"ppt/slides/_rels/slide\d+\.xml\.rels$", name
            ):
                continue  # drop the slide parts themselves
            if name == "ppt/presentation.xml":
                zout.writestr(item, pres_xml)
            elif name == "ppt/_rels/presentation.xml.rels":
                zout.writestr(item, rels_xml)
            elif name == "[Content_Types].xml":
                data = zin.read(name).decode("utf-8")
                data = re.sub(r'<Override PartName="/ppt/slides/slide\d+\.xml"[^/]*/>', "", data)
                zout.writestr(item, data)
            else:
                zout.writestr(item, zin.read(name))
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("potx", type=Path, help="path to the VIB-CCB .potx template")
    ap.add_argument("--reference-out", type=Path, default=None,
                    help="also write the 26 example slides as a .pptx here (not committed)")
    args = ap.parse_args()
    source = args.potx
    if not source.is_file():
        print(f"ERROR: source template not found: {source}", file=sys.stderr)
        return 1

    print(f"reading {source}")
    raw = source.read_bytes()
    zpptx = potx_bytes_to_pptx_zip(raw)

    if args.reference_out:
        args.reference_out.parent.mkdir(parents=True, exist_ok=True)
        args.reference_out.write_bytes(zpptx.fp.getvalue())
        print(f"wrote {args.reference_out} ({args.reference_out.stat().st_size:,} bytes)")

    blank = strip_slides(zpptx)
    TEMPLATE_OUT.write_bytes(blank)
    print(f"wrote {TEMPLATE_OUT} ({TEMPLATE_OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    sys.exit(main())
